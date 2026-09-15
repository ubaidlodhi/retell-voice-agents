"""
V37 - outcome routing moves onto the function nodes themselves.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v37_function_edges.py [--dry-run] [--publish]

Why V36's branch nodes are being removed
----------------------------------------
V36 put a `branch` after each submit node with equation edges on the tool's
response variable ({{booking_success}} == "true" / "false"). On the very next
real call (call_f5943184d33e8323e48cf257bc3, 2026-09-12) book_appointment
returned {"success": false, ...} and the branch still fell through to Else:

    Transitioning from node node-book-outcome (name: Booking - Outcome)
        to node node-book-outcome-unknown (name: Booking - Outcome Unknown (fallback))

Retell's equation engine does not evaluate variables set by a function node's
response_variables (same symptom reported unresolved on their community forum,
thread 3572). So the branches were dead weight and the six nodes around them
were noise.

What replaces them
------------------
Retell evaluates a function node's own `edges` right after the tool returns,
with the tool result in front of the model and BEFORE any speech. That is the
narrowest possible judgement - "does this JSON say success true or false?" -
and nothing has been said to the caller yet. So:

    submit (function)
      edge  "result shows success true"   -> Confirmed        (success-only wording)
      edge  "result shows success false"  -> Could Not Complete
      else                                -> Could Not Complete (never claim success
                                                                 without evidence)

Removed: node-book-outcome, node-cancel-outcome, node-resched-outcome and the
three "Outcome Unknown (fallback)" conversation nodes. Kept from V36: the
success-only confirm wording, node-cancel-failed, the firstName/lastName tool
descriptions, reschedule_success.
"""

from __future__ import annotations
import argparse
import json
import os
import urllib.request
from pathlib import Path

RETELL_BASE = "https://api.retellai.com"
FLOW_ID = "conversation_flow_bdb1968b28ed"
AGENT_ID = "agent_eceb7448aa1f37e8f436a63a43"
SNAPSHOT = Path(__file__).parent / "aria_conversation_flow.json"


def api_key() -> str:
    key = os.environ.get("RETELL_API_KEY")
    if key:
        return key
    mcp = Path(__file__).resolve().parents[2] / ".mcp.json"
    raw = mcp.read_text(encoding="utf-8")
    cfg = json.loads(raw[raw.index("{"):])
    for arg in cfg["mcpServers"]["retell"]["args"]:
        if arg.startswith("Authorization:Bearer "):
            return arg.split("Bearer ", 1)[1].strip()
    raise SystemExit("No Retell API key found.")


def request(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        f"{RETELL_BASE}{path}", data=data, method=method,
        headers={"Authorization": f"Bearer {api_key()}",
                 "Content-Type": "application/json", "User-Agent": "curl/8.0"})
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"Retell {method} {path} -> {exc.code}: {exc.read().decode('utf-8', 'replace')}") from None


# -----------------------------------------------------------------------------

REMOVE_NODES = {
    "node-book-outcome", "node-book-outcome-unknown",
    "node-cancel-outcome", "node-cancel-outcome-unknown",
    "node-resched-outcome", "node-resched-outcome-unknown",
}

# submit node -> (tool name, confirmed node, failed node)
OUTCOMES = {
    "node-book-submit": ("book_appointment", "node-book-confirm", "node-book-failed"),
    "node-cancel-do": ("cancel_booking", "node-cancel-done", "node-cancel-failed"),
    "node-resched-do": ("reschedule_booking", "node-resched-done", "node-resched-failed"),
}


def prompt_edge(eid: str, dest: str, prompt: str) -> dict:
    return {"id": eid, "destination_node_id": dest,
            "transition_condition": {"type": "prompt", "prompt": prompt}}


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    present = {n["id"] for n in flow["nodes"]}
    missing = REMOVE_NODES - present
    if missing:
        raise SystemExit(f"Expected V36 nodes are missing: {sorted(missing)} - is this the right draft?")
    flow["nodes"] = [n for n in flow["nodes"] if n["id"] not in REMOVE_NODES]
    nodes = {n["id"]: n for n in flow["nodes"]}

    for submit_id, (tool, ok, failed) in OUTCOMES.items():
        n = nodes[submit_id]
        if n["type"] != "function":
            raise SystemExit(f"{submit_id} is not a function node")
        n.pop("always_edge", None)
        short = submit_id.replace("node-", "")
        n["edges"] = [
            prompt_edge(f"e-{short}-ok", ok,
                        f'The {tool} tool result contains "success": true.'),
            prompt_edge(f"e-{short}-failed", failed,
                        f'The {tool} tool result contains "success": false, or an "error", '
                        f"or no result came back."),
        ]
        n["else_edge"] = {"id": f"e-{short}-else", "destination_node_id": failed,
                          "transition_condition": {"type": "prompt", "prompt": "Else"}}

    # ---- sanity --------------------------------------------------------------
    ids = [n["id"] for n in flow["nodes"]]
    assert len(ids) == len(set(ids)), "duplicate node id"
    edge_ids = []
    for n in flow["nodes"]:
        for e in n.get("edges", []):
            edge_ids.append(e["id"])
            assert e["destination_node_id"] in ids, f"dangling {e['id']} -> {e['destination_node_id']}"
        for k in ("always_edge", "skip_response_edge", "else_edge", "edge"):
            if n.get(k):
                edge_ids.append(n[k]["id"])
                assert n[k]["destination_node_id"] in ids, f"dangling {n[k]['id']}"
    dup = {x for x in edge_ids if edge_ids.count(x) > 1}
    assert not dup, f"duplicate edge ids {dup}"
    dead = REMOVE_NODES & {e for n in flow["nodes"] for e in
                           [x["destination_node_id"] for x in n.get("edges", [])]}
    assert not dead, f"edges still point at removed nodes: {dead}"
    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true")
    args = ap.parse_args()

    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft v{live.get('version')} - {len(live['nodes'])} nodes")
    patched = patch(live)
    body = {k: v for k, v in patched.items()
            if k not in ("conversation_flow_id", "version", "last_modification_timestamp", "is_published")}
    print(f"patched   - {len(patched['nodes'])} nodes, "
          f"{sum(1 for n in patched['nodes'] if n['type'] == 'branch')} branch nodes")

    SNAPSHOT.write_text(json.dumps(patched, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"snapshot  -> {SNAPSHOT.name}")
    if args.dry_run:
        print("Dry run - Retell not modified.")
        return

    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    print(f"PATCHED flow v{out.get('version')}")
    if args.publish:
        request("POST", f"/publish-agent/{AGENT_ID}", {})
        vers = request("GET", f"/get-agent-versions/{AGENT_ID}")
        latest = max((v for v in vers if v.get("is_published")), key=lambda v: v["version"])
        print(f"PUBLISHED agent v{latest['version']} -> flow v{latest['response_engine'].get('version')}")


if __name__ == "__main__":
    main()
