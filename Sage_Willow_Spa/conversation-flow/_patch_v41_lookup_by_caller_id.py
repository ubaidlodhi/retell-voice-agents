"""
V41 - look the caller up on the number they are calling from, and stop a
garbled booking id from killing a cancellation.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v41_lookup_by_caller_id.py [--dry-run]

Evidence: call_e3a032fe0d1d884c5a91ad937d6 (2026-09-14, agent v6)

1. THE CALLER WAS ASKED FOR A NUMBER WE ALREADY HAD
   Aria:  "What's the phone number on the appointment?"
   Ubaid: "So it is the one I'm calling from."
   get_booking was then called with exactly {{user_number}} - the number Aria
   had the whole time. A wasted turn on every status, cancel and reschedule
   call, and it invites the caller to recite ten digits down a phone line for
   no reason. The three lookup nodes now search the caller's own number FIRST
   and only ask for a different one when nothing comes back.

2. THE CANCELLATION FAILED ON A MISTYPED BOOKING ID          (the real bug)
   get_booking returned    79f6638b-c4c9-4bc0-bc80-c074547fac9a
   cancel_booking was sent 79f6638b-c4c9-4bc0-bc074547fac9a   <- "bc80-" gone
   Wix: "bookingId is not a valid GUID". Aria said she couldn't cancel and
   flagged a callback; the appointment stayed on the books.

   The id was read off a three-booking JSON blob fifty seconds and four turns
   earlier. Copying 36 hex characters across that gap is not something an LLM
   does reliably and no prompt wording fixes it, so the repair is server-side:
   n8n now re-queries the caller's own bookings and matches the id it was sent
   against them (exact, then unique leading block, then nearest edit distance
   with a clear margin), and takes the revision from Wix rather than from the
   model. See "Resolve: Booking Id (Cancel)" / "(Reschedule)" in n8n
   yfbpUaEzZQghelh3.

   That resolver needs the phone number the booking was found under, so
   cancel_booking and reschedule_booking now take a required `phone`.

3. ARIA ASKED FOR A NAME SHE HAD ALREADY BEEN GIVEN
   The booking she had just read out carried firstName "John", lastName "Doe",
   and she still asked "What's your name?" before flagging the callback.
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
# 1. Look them up on the number they are calling from.
# -----------------------------------------------------------------------------

# The reschedule node words it as "Call get_booking first."; the other two just
# "Call get_booking." Match each exactly so a silent no-op is impossible.
OLD_OPENERS = {
    "node-status-assistant": "Call get_booking.",
    "node-cancel-assistant": "Call get_booking.",
    "node-resched-assistant": "Call get_booking first.",
}
NEW_OPENER = (
    "Call get_booking IMMEDIATELY, on the number they are calling from - that is "
    "{{user_number}}, and it is almost always the number the appointment is under. "
    "Never open with \"what's the phone number on the appointment?\" You already have "
    "it; asking wastes a turn and makes a caller read ten digits down a phone line for "
    "nothing."
)

OLD_NOT_FOUND = (
    "If nothing is found, say so plainly and ask whether they'd like you to try a "
    "different number. When they give you one - and they will often just say the digits "
    "with nothing else - call get_booking AGAIN with that number. Keep the details you "
    "read out strictly to what the tool returned; if you cannot see a real booking, do "
    "not invent one."
)
NEW_NOT_FOUND = (
    "ONLY if that lookup comes back with nothing do you ask for a number, and say why: "
    "\"I'm not seeing anything under the number you're calling from - is it booked under "
    "a different one?\" When they give you one - and they will often just say the digits "
    "with nothing else - call get_booking AGAIN with that number. Keep the details you "
    "read out strictly to what the tool returned; if you cannot see a real booking, do "
    "not invent one."
)

# -----------------------------------------------------------------------------
# 2. A name you were already given is not a question.
# -----------------------------------------------------------------------------

OLD_CANCEL_FAILED = (
    "The cancellation did not go through. Say plainly that you couldn't cancel it just "
    "now - no jargon, no error codes - and offer to have someone from the spa call them "
    "back to sort it. If they say yes, ask for their name."
)
NEW_CANCEL_FAILED = (
    "The cancellation did not go through. Say plainly that you couldn't cancel it just "
    "now - no jargon, no error codes - and offer to have someone from the spa call them "
    "back to sort it.\n\n"
    "If they say yes and the booking you looked up already carried a first and last "
    "name, use that name - do not ask for it again. Ask only when you genuinely do not "
    "have one."
)

# -----------------------------------------------------------------------------
# 3. Both write tools now carry the phone, so the backend can verify the id.
# -----------------------------------------------------------------------------

PHONE_PARAM = {
    "type": "string",
    "description": ("The number this booking was found under - the same one get_booking "
                    "was called with, normally {{user_number}}. Always send it."),
}

CANCEL_DESC = ("Cancel a booking. Only after an explicit yes. Send the bookingId and "
               "revision from get_booking plus the phone they were found under - the "
               "server re-checks the id against that caller's live bookings before "
               "cancelling anything.")
RESCHED_DESC = ("Move a booking to a new time. Only after the caller confirms the new "
                "slot. Send the original bookingId, revision and serviceId, the phone "
                "they were found under, and the new scheduleId, startDate and endDate. "
                "startDate and endDate must be the time the caller actually agreed to, "
                "copied exactly - never a nearby slot. The server re-checks the bookingId "
                "against that caller's live bookings before moving anything.")

LOOKUP_NODES = ("node-status-assistant", "node-cancel-assistant", "node-resched-assistant")


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    nodes = {n["id"]: n for n in flow["nodes"]}

    for node_id in LOOKUP_NODES:
        text = nodes[node_id]["instruction"]["text"]
        opener = OLD_OPENERS[node_id]
        if opener not in text:
            raise SystemExit(f"{node_id}: opener {opener!r} not found.")
        if OLD_NOT_FOUND not in text:
            raise SystemExit(f"{node_id}: not-found paragraph not found.")
        text = text.replace(opener, NEW_OPENER, 1)
        text = text.replace(OLD_NOT_FOUND, NEW_NOT_FOUND)
        nodes[node_id]["instruction"]["text"] = text

    failed = nodes["node-cancel-failed"]["instruction"]
    if failed["text"].strip() != OLD_CANCEL_FAILED:
        raise SystemExit("node-cancel-failed text has changed shape.")
    failed["text"] = NEW_CANCEL_FAILED

    tools = {t["name"]: t for t in flow["tools"]}
    for name, desc in (("cancel_booking", CANCEL_DESC), ("reschedule_booking", RESCHED_DESC)):
        tool = tools[name]
        tool["description"] = desc
        tool["parameters"]["properties"]["phone"] = dict(PHONE_PARAM)
        required = tool["parameters"].setdefault("required", [])
        if "phone" not in required:
            required.append("phone")

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
        print(f"  {node_id:24s} opens on caller ID: "
              f"{'yes' if 'IMMEDIATELY' in text else 'NO'}, "
              f"asks only on miss: {'yes' if 'ONLY if that lookup' in text else 'NO'}")
    tools = {t["name"]: t for t in patched["tools"]}
    for name in ("cancel_booking", "reschedule_booking"):
        print(f"  {name:24s} required={tools[name]['parameters']['required']}")

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

    back_tools = {t["name"]: t for t in out["tools"]}
    for name in ("cancel_booking", "reschedule_booking"):
        props = back_tools[name]["parameters"]["properties"]
        print(f"  read back: {name} phone param = {'present' if 'phone' in props else 'MISSING'}")


if __name__ == "__main__":
    main()
