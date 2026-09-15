"""
V36 - outcomes are decided by the tool result, not by the LLM.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v36_outcome_branches.py [--dry-run] [--publish]

Why
---
Outbound test call call_1bafa906b4b96ea7a30bcfd1403 (2026-09-12): book_appointment
returned {"success": false, "error": "firstName is required; lastName is
required"}. The "Booking - Confirmed" node was a conversation node told "if
booking_success is true say you're all set, if it failed say you're having
trouble" - and the model said "You're all set for Sunday at 10:30". Same
failure class as the fabricated bookings before: a talk node deciding an
outcome it should only be reporting.

What changes
------------
For each mutating tool (book / cancel / reschedule) the submit function node
now feeds a `branch` node that routes on the tool's response variable:

    submit --always--> outcome (branch)
                         {{x_success}} == "true"  -> Confirmed   (success-only wording)
                         {{x_success}} == "false" -> Could Not Complete
                         else                     -> Outcome Unknown (fallback = old behaviour)

The "Unknown" fallback exists so that, if the response variable ever fails to
populate, the call degrades to today's behaviour instead of telling a booked
caller their booking failed. Check the public log of the next real call: if it
never visits an "Outcome Unknown" node, the variables work and those nodes can
be deleted in a later patch.

Also:
  * book_appointment.firstName / lastName gain descriptions (they had none) -
    the same call passed neither even though the caller spelled J-O-H-N T-E-S-T.
  * reschedule_booking gains `reschedule_success: $.success` so its branch can
    key off the same always-present field the other two use.
  * "Cancel - Could Not Complete" node added (cancel had no failure path).
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

def eq_edge(eid: str, dest: str, var: str, value: str) -> dict:
    return {"id": eid, "destination_node_id": dest,
            "transition_condition": {"type": "equation", "operator": "&&",
                                     "equations": [{"left": f"{{{{{var}}}}}", "operator": "==", "right": value}]}}


def prompt_edge(eid: str, dest: str, prompt: str) -> dict:
    return {"id": eid, "destination_node_id": dest,
            "transition_condition": {"type": "prompt", "prompt": prompt}}


def branch(nid: str, name: str, var: str, ok: str, failed: str, unknown: str, pos: dict) -> dict:
    return {
        "id": nid, "name": name, "type": "branch", "display_position": pos,
        "edges": [
            eq_edge(f"e-{nid}-ok", ok, var, "true"),
            eq_edge(f"e-{nid}-failed", failed, var, "false"),
        ],
        "else_edge": {"id": f"e-{nid}-else", "destination_node_id": unknown,
                      "transition_condition": {"type": "prompt", "prompt": "Else"}},
    }


def conv(nid: str, name: str, text: str, edges: list, pos: dict) -> dict:
    return {"id": nid, "name": name, "type": "conversation", "display_position": pos,
            "instruction": {"type": "prompt", "text": text}, "edges": edges}


BOOK_CONFIRMED = (
    'The booking went through. Say ONE short line - "You\'re all set for Tuesday at two PM." Nothing else: '
    "do not repeat the service, price, phone, or booking ID. Then ask \"Anything else I can help with?\""
)
BOOK_UNKNOWN = (
    "The booking tool has returned but its result is not clear. Look at what it actually said. "
    'If it plainly succeeded, say ONE short line - "You\'re all set for Tuesday at two PM." - then ask "Anything else I can help with?" '
    "If it did not plainly succeed, you have NOT booked anything: never say all set, never say confirmed. "
    'Say "I\'m having trouble finalizing that" and offer to have someone from the spa call them back.'
)
CANCEL_CONFIRMED = 'The cancellation went through. One short line: "All set - that\'s cancelled." Then ask "Anything else I can help with?"'
CANCEL_FAILED = (
    "The cancellation did not go through. Say plainly that you couldn't cancel it just now - no jargon, no error codes - "
    "and offer to have someone from the spa call them back to sort it. If they say yes, ask for their name."
)
CANCEL_UNKNOWN = (
    "The cancel tool has returned but its result is not clear. Look at what it actually said. "
    'If it plainly succeeded: "All set - that\'s cancelled." then ask "Anything else I can help with?" '
    "If it did not plainly succeed, nothing has been cancelled: never say it is cancelled. "
    "Say you're having trouble with it and offer to have someone call them back."
)
RESCHED_CONFIRMED = 'The move went through. One short line with the new day and time only - "You\'re moved to Friday at one PM." Then ask "Anything else I can help with?"'
RESCHED_UNKNOWN = (
    "The reschedule tool has returned but its result is not clear. Look at what it actually said. "
    'If it plainly succeeded, give the new day and time in one line - "You\'re moved to Friday at one PM." - then ask "Anything else I can help with?" '
    "If it did not plainly succeed, nothing has moved: never say it is moved. "
    "Say you couldn't move it and offer to have someone call them back."
)


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    nodes = {n["id"]: n for n in flow["nodes"]}
    tools = {t["name"]: t for t in flow["tools"]}

    # ---- tools ---------------------------------------------------------------
    props = tools["book_appointment"]["parameters"]["properties"]
    props["firstName"]["description"] = (
        "Caller's first name exactly as they gave it on this call. If they spelled it letter by letter, "
        "join the letters into the word (J-O-H-N -> John). Required - never send an empty string."
    )
    props["lastName"]["description"] = (
        "Caller's last name exactly as they gave it on this call, spelled letters joined into the word "
        "(T-E-S-T -> Test). Required - never send an empty string."
    )
    rv = tools["reschedule_booking"].setdefault("response_variables", {})
    rv["reschedule_success"] = "$.success"

    # ---- booking -------------------------------------------------------------
    pos = nodes["node-book-confirm"].get("display_position", {"x": 0, "y": 0})
    nodes["node-book-submit"]["always_edge"]["destination_node_id"] = "node-book-outcome"
    nodes["node-book-confirm"]["instruction"] = {"type": "prompt", "text": BOOK_CONFIRMED}
    nodes["node-book-confirm"]["edges"] = [e for e in nodes["node-book-confirm"]["edges"] if e["id"] != "e-confirm-failed"]
    unknown_edges = [
        prompt_edge("e-bookunk-done", "node-close", "The caller has nothing else they need."),
        prompt_edge("e-bookunk-more", "node-greeting", "The caller wants something else - another booking, or a change."),
        prompt_edge("e-bookunk-callback", "node-handoff-callback", "The booking did not succeed and the caller wants someone to call them back."),
        prompt_edge("e-bookunk-retry", "node-book-discovery", "The booking did not succeed and the caller wants to try a different time instead."),
    ]
    flow["nodes"].append(branch("node-book-outcome", "Booking - Outcome", "booking_success",
                                "node-book-confirm", "node-book-failed", "node-book-outcome-unknown",
                                {"x": pos["x"] - 250, "y": pos["y"]}))
    flow["nodes"].append(conv("node-book-outcome-unknown", "Booking - Outcome Unknown (fallback)", BOOK_UNKNOWN,
                              unknown_edges, {"x": pos["x"], "y": pos["y"] + 260}))

    # ---- cancel --------------------------------------------------------------
    pos = nodes["node-cancel-done"].get("display_position", {"x": 0, "y": 0})
    nodes["node-cancel-do"]["always_edge"]["destination_node_id"] = "node-cancel-outcome"
    nodes["node-cancel-done"]["instruction"] = {"type": "prompt", "text": CANCEL_CONFIRMED}
    flow["nodes"].append(branch("node-cancel-outcome", "Cancel - Outcome", "cancel_success",
                                "node-cancel-done", "node-cancel-failed", "node-cancel-outcome-unknown",
                                {"x": pos["x"] - 250, "y": pos["y"]}))
    flow["nodes"].append(conv("node-cancel-failed", "Cancel - Could Not Complete", CANCEL_FAILED, [
        prompt_edge("e-cancelfail-callback", "node-handoff-callback", "The caller wants a callback."),
        prompt_edge("e-cancelfail-done", "node-close", "The caller does not want to go further."),
    ], {"x": pos["x"], "y": pos["y"] + 260}))
    flow["nodes"].append(conv("node-cancel-outcome-unknown", "Cancel - Outcome Unknown (fallback)", CANCEL_UNKNOWN, [
        prompt_edge("e-cancelunk-done", "node-close", "The caller has nothing else."),
        prompt_edge("e-cancelunk-more", "node-greeting", "The caller wants something else."),
        prompt_edge("e-cancelunk-callback", "node-handoff-callback", "The cancellation did not succeed and the caller wants a callback."),
    ], {"x": pos["x"], "y": pos["y"] + 520}))

    # ---- reschedule ----------------------------------------------------------
    pos = nodes["node-resched-done"].get("display_position", {"x": 0, "y": 0})
    nodes["node-resched-do"]["always_edge"]["destination_node_id"] = "node-resched-outcome"
    nodes["node-resched-done"]["instruction"] = {"type": "prompt", "text": RESCHED_CONFIRMED}
    nodes["node-resched-done"]["edges"] = [e for e in nodes["node-resched-done"]["edges"] if e["id"] != "e-rescheddone-failed"]
    flow["nodes"].append(branch("node-resched-outcome", "Reschedule - Outcome", "reschedule_success",
                                "node-resched-done", "node-resched-failed", "node-resched-outcome-unknown",
                                {"x": pos["x"] - 250, "y": pos["y"]}))
    flow["nodes"].append(conv("node-resched-outcome-unknown", "Reschedule - Outcome Unknown (fallback)", RESCHED_UNKNOWN, [
        prompt_edge("e-reschedunk-done", "node-close", "The caller has nothing else."),
        prompt_edge("e-reschedunk-more", "node-greeting", "The caller wants something else."),
        prompt_edge("e-reschedunk-callback", "node-handoff-callback", "The reschedule did not succeed and the caller wants a callback."),
    ], {"x": pos["x"], "y": pos["y"] + 260}))

    # ---- sanity --------------------------------------------------------------
    ids = [n["id"] for n in flow["nodes"]]
    assert len(ids) == len(set(ids)), "duplicate node id"
    edge_ids = []
    for n in flow["nodes"]:
        for e in n.get("edges", []):
            edge_ids.append(e["id"])
        for k in ("always_edge", "skip_response_edge", "else_edge"):
            if n.get(k):
                edge_ids.append(n[k]["id"])
    dup = {x for x in edge_ids if edge_ids.count(x) > 1}
    assert not dup, f"duplicate edge ids {dup}"
    for n in flow["nodes"]:
        for e in n.get("edges", []) + [n[k] for k in ("always_edge", "skip_response_edge", "else_edge") if n.get(k)]:
            assert e["destination_node_id"] in ids, f"dangling {e['id']} -> {e['destination_node_id']}"
    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true", help="publish the agent after patching")
    args = ap.parse_args()

    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft v{live.get('version')} - {len(live['nodes'])} nodes")
    patched = patch(live)
    body = {k: v for k, v in patched.items()
            if k not in ("conversation_flow_id", "version", "last_modification_timestamp", "is_published")}
    print(f"patched   - {len(patched['nodes'])} nodes "
          f"({sum(1 for n in patched['nodes'] if n['type'] == 'branch')} branch)")

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
        pub = [v for v in vers if v.get("is_published")]
        latest = max(pub, key=lambda v: v["version"])
        print(f"PUBLISHED agent v{latest['version']} -> flow v{latest['response_engine'].get('version')}")


if __name__ == "__main__":
    main()
