"""
V44 - look the appointment up on the caller's own number straight away; ask for
a different number only when that finds nothing.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v44_lookup_first_ask_on_miss.py [--dry-run]

Ubaid, 2026-09-14: "if someone says I want to reschedule, I want to cancel -
for the appointment lookup we should immediately look for the appointment using
the phone number the caller is calling from. And if we return no appointments,
then we should ask: I didn't see an appointment using the number you're calling
from, is there a different number you used while booking? So it will be a less
frictionable call."

So step 1 stops being a question. V42 had Aria ask which number to search
before searching anything; that is a whole extra turn on every status, cancel
and reschedule call, and the honest answer is that the caller's own number is
right nearly every time. The question now only gets asked in the case where it
carries information - when the lookup came back empty - and it says why it is
being asked, which is what makes it land as helpful rather than bureaucratic.

Everything V43 added stays: the numbered steps, the "which booking?" step when
several come back, the "want me to move it instead?" offer before cancelling,
and the 8-second nudge on node-cancel-confirm.
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
# The lookup step, written once and shared by all three flows.
# -----------------------------------------------------------------------------

FIND_IT = (
    "Call get_booking IMMEDIATELY on the number they are calling from, {{user_number}}. "
    "Do not ask them for a number first - they rang us from it, it is nearly always the "
    "one they booked with, and looking it up takes less time than asking.\n"
    "   If, and only if, that comes back with nothing, ask for the other one and say why: "
    "\"I'm not seeing an appointment under the number you're calling from - is there a "
    "different number you booked with?\" Then call get_booking AGAIN with whatever they "
    "give you; they will often just say the digits with nothing else."
)

# What V42/V43 left in each node, to be replaced.
V42_ASK_FIRST = (
    "FIRST ask this, and WAIT for the answer - it is the whole turn:\n"
    "    \"To find your appointment - should I use the number you're calling from, or is "
    "it booked under a different one?\"\n"
    "Call no tool until they have answered.\n\n"
    "If they pick the number they are calling from - \"this one\", \"yes\", \"the one I'm "
    "calling from\" - call get_booking on {{user_number}}. If they give a different number, "
    "and they will often just say the digits with nothing else, call get_booking with that "
    "one instead. Either way, search the number they chose, not both."
)

V43_CANCEL_STEP_1 = (
    "1. WHICH NUMBER. Ask this and WAIT - it is the whole turn:\n"
    "   \"To find your appointment - should I use the number you're calling from, or is it "
    "booked under a different one?\"\n"
    "   Call no tool until they have answered. If they pick the number they are calling "
    "from - \"this one\", \"yes\", \"the one I'm calling from\" - call get_booking on "
    "{{user_number}}. If they give a different number, and they will often just say the "
    "digits with nothing else, call get_booking with that one. Search the number they "
    "chose, not both."
)
NEW_CANCEL_STEP_1 = "1. FIND IT. " + FIND_IT

# The trailing "nothing came back" paragraph is now handled inside the lookup
# step, so all that is left to say here is: never invent a booking.
V43_TRAILING = (
    "If nothing comes back under the number you searched, say so plainly and ask whether "
    "it might be under another one - then call get_booking AGAIN with whatever they give "
    "you. Keep the details you read out strictly to what the tool returned; if you cannot "
    "see a real booking, do not invent one."
)
NEW_TRAILING = ("Keep the details you read out strictly to what the tool returned; if you "
                "cannot see a real booking, do not invent one.")

LOOKUP_NODES = ("node-status-assistant", "node-cancel-assistant", "node-resched-assistant")


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    nodes = {n["id"]: n for n in flow["nodes"]}

    cancel = nodes["node-cancel-assistant"]["instruction"]
    if V43_CANCEL_STEP_1 not in cancel["text"]:
        raise SystemExit("node-cancel-assistant: V43 step 1 not found - check flow version.")
    cancel["text"] = cancel["text"].replace(V43_CANCEL_STEP_1, NEW_CANCEL_STEP_1)

    for node_id in ("node-status-assistant", "node-resched-assistant"):
        text = nodes[node_id]["instruction"]["text"]
        if V42_ASK_FIRST not in text:
            raise SystemExit(f"{node_id}: V42 ask-first block not found - check flow version.")
        nodes[node_id]["instruction"]["text"] = text.replace(V42_ASK_FIRST, FIND_IT)

    for node_id in LOOKUP_NODES:
        text = nodes[node_id]["instruction"]["text"]
        if V43_TRAILING not in text:
            raise SystemExit(f"{node_id}: trailing not-found paragraph not found.")
        nodes[node_id]["instruction"]["text"] = text.replace(V43_TRAILING, NEW_TRAILING)

    # --- guards ---------------------------------------------------------------
    for node_id in LOOKUP_NODES:
        text = nodes[node_id]["instruction"]["text"]
        if "should I use the number you're calling from" in text:
            raise SystemExit(f"{node_id} still asks which number before looking anything up.")
        if "Call get_booking IMMEDIATELY" not in text:
            raise SystemExit(f"{node_id} lost the immediate lookup.")
        if "is there a different number you booked with?" not in text:
            raise SystemExit(f"{node_id} lost the ask-on-miss wording.")

    # V43's cancel steps must survive intact.
    cancel_text = nodes["node-cancel-assistant"]["instruction"]["text"]
    for step in ("1. FIND IT.", "2. WHICH BOOKING.", "3. OFFER TO MOVE IT."):
        if step not in cancel_text:
            raise SystemExit(f"node-cancel-assistant lost step: {step}")
    if "want me to see if we can move it to another time instead?" not in cancel_text:
        raise SystemExit("The move-instead offer went missing from the cancel node.")
    if nodes["node-cancel-confirm"].get("reminder_trigger_ms") != 8000:
        raise SystemExit("node-cancel-confirm lost its 8s reminder override.")

    # V40 rule still stands: brackets are slots, never fabricated values.
    bad = re.compile(r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|"
                     r"\d{1,2}\s?(AM|PM))\b", re.I)
    for node_id in LOOKUP_NODES:
        hit = bad.search(nodes[node_id]["instruction"]["text"])
        if hit:
            raise SystemExit(f"{node_id} carries a fabricated day/time: {hit.group(0)}")
    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft flow v{live.get('version')} - {len(live['nodes'])} nodes")
    patched = patch(live)
    nodes = {n["id"]: n for n in patched["nodes"]}

    for node_id in LOOKUP_NODES:
        text = nodes[node_id]["instruction"]["text"]
        print(f"  {node_id:24s} looks up first: yes | asks only on a miss: yes | "
              f"{len(text)} chars")
    print(f"  node-cancel-confirm      reminder_trigger_ms = "
          f"{nodes['node-cancel-confirm'].get('reminder_trigger_ms')}")

    SNAPSHOT.write_text(json.dumps(patched, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"snapshot -> {SNAPSHOT.name}")
    if args.dry_run:
        print("Dry run - Retell not modified.")
        return

    body = {k: v for k, v in patched.items()
            if k not in ("conversation_flow_id", "version",
                         "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    print(f"PATCHED draft flow v{out.get('version')} (NOT published)")


if __name__ == "__main__":
    main()
