"""
V42 - ask which number to search before searching, and retry a failed cancel.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v42_ask_which_number_and_cancel_retry.py [--dry-run]

Two corrections from Ubaid, 2026-09-14, on top of V41.

1. ASK FIRST, THEN LOOK UP
   V41 had Aria search {{user_number}} silently and only ask for a number if
   the lookup came back empty. Wrong shape: on an inbound call the caller ID is
   never missing, so the "ask" branch effectively only fired when the caller
   had no booking - by which point she has already told them nothing is there.
   The caller is also never given the chance to say "actually it's under my
   wife's number" up front.
   She now asks ONE question and waits:
       "To find your appointment - should I use the number you're calling from,
        or is it booked under a different one?"
   and searches whichever they choose. No tool call before they answer.

2. A FAILED CANCEL IS RETRIED, NOT SURRENDERED
   On call_e3a032fe0d1d884c5a91ad937d6 one failed cancel_booking ended the
   attempt outright: "I actually couldn't cancel it just now." One transient
   Wix error, or one mistyped booking id, and a caller who asked to cancel
   walks away with the appointment still on the books.
   node-cancel-do now falls to node-cancel-retry-1 and then node-cancel-retry-2
   before node-cancel-failed - three attempts on the same tool. Every attempt
   runs silently (speak_during_execution stays false on all three nodes), so
   the caller hears one pause rather than three announcements.

   Worth knowing why three attempts is not just hope: the retry goes through
   the n8n resolver added the same day, which re-queries the caller's live
   bookings and repairs a garbled id. The retries cover the transient Wix
   failures the resolver cannot; the resolver covers the mistyped ids retrying
   alone would probably just repeat.

Reschedule deliberately NOT given the retry loop here - Ubaid asked for cancel.
Same three-node shape drops in if wanted.
"""

from __future__ import annotations
import argparse
import json
import os
import re
import urllib.request
from pathlib import Path

RETELL_BASE = "https://api.retellai.com"
FLOW_ID = "conversation_flow_bdb1968b28ed"
SNAPSHOT = Path(__file__).parent / "aria_conversation_flow.json"

CANCEL_ATTEMPTS = 3


def api_key() -> str:
    key = os.environ.get("RETELL_API_KEY")
    if key:
        return key
    raw = (Path(__file__).resolve().parents[2] / ".mcp.json").read_text(encoding="utf-8")
    cfg = json.loads(raw[raw.index("{"):])
    blob = json.dumps(cfg["mcpServers"]["retell-sage"])
    match = re.search(r"key_[a-f0-9]+", blob)
    if not match:
        raise SystemExit("No Retell key in the retell-sage MCP server entry.")
    return match.group(0)


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
        raise SystemExit(f"Retell {method} {path} -> {exc.code}: "
                         f"{exc.read().decode('utf-8', 'replace')}") from None


# -----------------------------------------------------------------------------
# 1. Ask which number, then search it.
# -----------------------------------------------------------------------------

V41_OPENER = (
    "Call get_booking IMMEDIATELY, on the number they are calling from - that is "
    "{{user_number}}, and it is almost always the number the appointment is under. "
    "Never open with \"what's the phone number on the appointment?\" You already have "
    "it; asking wastes a turn and makes a caller read ten digits down a phone line for "
    "nothing."
)
ASK_FIRST = (
    "FIRST ask this, and WAIT for the answer - it is the whole turn:\n"
    "    \"To find your appointment - should I use the number you're calling from, or "
    "is it booked under a different one?\"\n"
    "Call no tool until they have answered.\n\n"
    "If they pick the number they are calling from - \"this one\", \"yes\", \"the one "
    "I'm calling from\" - call get_booking on {{user_number}}. If they give a different "
    "number, and they will often just say the digits with nothing else, call get_booking "
    "with that one instead. Either way, search the number they chose, not both."
)

V41_NOT_FOUND = (
    "ONLY if that lookup comes back with nothing do you ask for a number, and say why: "
    "\"I'm not seeing anything under the number you're calling from - is it booked under "
    "a different one?\" When they give you one - and they will often just say the digits "
    "with nothing else - call get_booking AGAIN with that number. Keep the details you "
    "read out strictly to what the tool returned; if you cannot see a real booking, do "
    "not invent one."
)
NEW_NOT_FOUND = (
    "If nothing comes back under the number you searched, say so plainly and ask whether "
    "it might be under another one - then call get_booking AGAIN with whatever they give "
    "you. Keep the details you read out strictly to what the tool returned; if you cannot "
    "see a real booking, do not invent one."
)

LOOKUP_NODES = ("node-status-assistant", "node-cancel-assistant", "node-resched-assistant")

# -----------------------------------------------------------------------------
# 2. Three attempts at the cancel before giving up.
# -----------------------------------------------------------------------------

OK_PROMPT = 'The cancel_booking tool result contains "success": true.'
FAIL_PROMPT = ('The cancel_booking tool result contains "success": false, or an "error", '
               'or no result came back.')

V41_CANCEL_FAILED = (
    "The cancellation did not go through. Say plainly that you couldn't cancel it just "
    "now - no jargon, no error codes - and offer to have someone from the spa call them "
    "back to sort it.\n\n"
    "If they say yes and the booking you looked up already carried a first and last "
    "name, use that name - do not ask for it again. Ask only when you genuinely do not "
    "have one."
)
NEW_CANCEL_FAILED = (
    "The cancellation still has not gone through after several tries. Say you're having "
    "trouble cancelling it on your end - no jargon, no error codes, and do not list the "
    "attempts - and offer to have someone from the spa call them back to sort it.\n\n"
    "If they say yes and the booking you looked up already carried a first and last "
    "name, use that name - do not ask for it again. Ask only when you genuinely do not "
    "have one."
)


def retry_node(index: int, next_on_fail: str, position: dict) -> dict:
    """One more silent attempt at cancel_booking, same args as the attempt before."""
    node_id = f"node-cancel-retry-{index}"
    short = f"retry{index}"
    return {
        "id": node_id,
        "name": f"Cancel - Retry {index}",
        "type": "function",
        "tool_type": "local",
        "tool_id": "cancel_booking",
        "wait_for_result": True,
        # Silent: the caller should hear one pause, not one announcement per attempt.
        "speak_during_execution": False,
        "enable_typing_sound": True,
        "skippable": False,
        "display_position": position,
        "edges": [
            {"id": f"e-cancel-{short}-ok",
             "destination_node_id": "node-cancel-done",
             "transition_condition": {"type": "prompt", "prompt": OK_PROMPT}},
            {"id": f"e-cancel-{short}-failed",
             "destination_node_id": next_on_fail,
             "transition_condition": {"type": "prompt", "prompt": FAIL_PROMPT}},
        ],
        "else_edge": {
            "id": f"e-cancel-{short}-else",
            "destination_node_id": next_on_fail,
            "transition_condition": {"type": "prompt", "prompt": "Else"},
        },
    }


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    nodes = {n["id"]: n for n in flow["nodes"]}

    # --- 1. ask, then look up -------------------------------------------------
    for node_id in LOOKUP_NODES:
        text = nodes[node_id]["instruction"]["text"]
        if V41_OPENER not in text:
            raise SystemExit(f"{node_id}: V41 opener not found - rerun V41 first.")
        if V41_NOT_FOUND not in text:
            raise SystemExit(f"{node_id}: V41 not-found paragraph not found.")
        text = text.replace(V41_OPENER, ASK_FIRST, 1)
        text = text.replace(V41_NOT_FOUND, NEW_NOT_FOUND)
        nodes[node_id]["instruction"]["text"] = text

    # --- 2. retry the cancel --------------------------------------------------
    base = nodes["node-cancel-do"]["display_position"]
    retries = CANCEL_ATTEMPTS - 1
    for i in range(1, retries + 1):
        node_id = f"node-cancel-retry-{i}"
        if node_id in nodes:
            raise SystemExit(f"{node_id} already exists - V42 has already been applied.")
        next_on_fail = (f"node-cancel-retry-{i + 1}" if i < retries else "node-cancel-failed")
        node = retry_node(i, next_on_fail, {"x": base["x"] + 260 * i, "y": base["y"] + 220})
        flow["nodes"].append(node)
        nodes[node_id] = node

    # The first attempt now falls into the retry chain instead of straight to failed.
    do = nodes["node-cancel-do"]
    for edge in do["edges"]:
        if edge["destination_node_id"] == "node-cancel-failed":
            edge["destination_node_id"] = "node-cancel-retry-1"
    if do["else_edge"]["destination_node_id"] == "node-cancel-failed":
        do["else_edge"]["destination_node_id"] = "node-cancel-retry-1"

    failed = nodes["node-cancel-failed"]["instruction"]
    if failed["text"].strip() != V41_CANCEL_FAILED:
        raise SystemExit("node-cancel-failed text has changed shape.")
    failed["text"] = NEW_CANCEL_FAILED

    # --- guards ---------------------------------------------------------------
    seen: set[str] = set()
    ids = {n["id"] for n in flow["nodes"]}
    for node in flow["nodes"]:
        for edge in list(node.get("edges", [])) + [e for e in (node.get("else_edge"),
                                                               node.get("always_edge"),
                                                               node.get("skip_response_edge"))
                                                   if e]:
            if edge["id"] in seen:
                raise SystemExit(f"Duplicate edge id: {edge['id']}")
            seen.add(edge["id"])
            if edge["destination_node_id"] not in ids:
                raise SystemExit(f"{edge['id']} points at missing node "
                                 f"{edge['destination_node_id']}")

    # Exactly one path may still end at "could not cancel", and it must be the last retry.
    enders = [n["id"] for n in flow["nodes"]
              for e in list(n.get("edges", [])) + [x for x in (n.get("else_edge"),) if x]
              if e["destination_node_id"] == "node-cancel-failed"]
    if set(enders) != {f"node-cancel-retry-{retries}"}:
        raise SystemExit(f"node-cancel-failed reached from {sorted(set(enders))}, "
                         f"expected only the last retry.")
    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft flow v{live.get('version')} - {len(live['nodes'])} nodes")
    patched = patch(live)
    nodes = {n["id"]: n for n in patched["nodes"]}

    print(f"  nodes {len(live['nodes'])} -> {len(patched['nodes'])}")
    for node_id in LOOKUP_NODES:
        text = nodes[node_id]["instruction"]["text"]
        print(f"  {node_id:24s} asks before searching: "
              f"{'yes' if 'FIRST ask this, and WAIT' in text else 'NO'}")
    chain = ["node-cancel-do"] + [f"node-cancel-retry-{i}" for i in range(1, CANCEL_ATTEMPTS)]
    for node_id in chain:
        n = nodes[node_id]
        fail = next(e["destination_node_id"] for e in n["edges"]
                    if e["id"].endswith("-failed"))
        print(f"  {node_id:24s} tool={n['tool_id']} speaks={n['speak_during_execution']} "
              f"on failure -> {fail}")

    SNAPSHOT.write_text(json.dumps(patched, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"snapshot -> {SNAPSHOT.name}")
    if args.dry_run:
        print("Dry run - Retell not modified.")
        return

    body = {k: v for k, v in patched.items()
            if k not in ("conversation_flow_id", "version",
                         "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    print(f"PATCHED draft flow v{out.get('version')} (NOT published) - "
          f"{len(out['nodes'])} nodes")
    back = {n["id"] for n in out["nodes"]}
    print(f"  read back: retry nodes present = "
          f"{sorted(n for n in back if n.startswith('node-cancel-retry'))}")


if __name__ == "__main__":
    main()
