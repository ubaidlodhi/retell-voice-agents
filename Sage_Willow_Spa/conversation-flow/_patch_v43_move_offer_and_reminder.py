"""
V43 - put the "want me to move it instead?" offer back, and stop the 20-second
silence that made Aria ask the same question twice.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v43_move_offer_and_reminder.py [--dry-run]

Evidence: call_87811fd423b726fbf37cb03ffbd (2026-09-14, agent v6)

The cancel itself worked - correct id sent, Wix confirmed CANCELED. Two other
things went wrong.

1. THE OFFER TO MOVE IT NEVER HAPPENED
       Aria: "...Which one do you want to cancel?"
       Ubaid: "So, I want to cancel the one with Rocky."
       Aria: "Okay, just to confirm, you want me to cancel that one?"
   The instruction did still say "read it back in ONE line ... then offer the
   alternative once", but it was written for ONE booking. Three came back, the
   model improvised a "which one?" turn that no step described, and once the
   caller picked, the proceed edge fired straight past the offer.
   The node is now explicit numbered steps with the multi-booking case written
   down, so the offer sits on the only path from "which one" to the confirm
   node and cannot be skipped. Same missing step added to reschedule.

2. TWENTY SECONDS OF DEAD AIR, THEN THE SAME QUESTION AGAIN
       57.1s  Aria: "Okay, just to confirm, you want me to cancel that one?"
       ...    nothing at all reaches the agent
       78.3s  Aria: "Did you still want to cancel the one with Rocky?"
   That second question is the agent's reminder firing, not a new thought:
   `reminder_trigger_ms` is 20000 agent-wide. On a long collection turn that is
   fine; on a one-word yes/no gate, twenty seconds of silence means the answer
   was missed, not that the caller is still thinking - and waiting that long
   before nudging is exactly what made the call feel stuck.
   node-cancel-confirm now nudges at 8s, and its instruction shapes the nudge
   into a short "Still want me to cancel it?" rather than a restatement.
   The agent-wide 20000 default is deliberately left alone.
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

CONFIRM_REMINDER_MS = 8000

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

CANCEL_ASSISTANT = """The caller wants to cancel an appointment. Work these in order.

1. WHICH NUMBER. Ask this and WAIT - it is the whole turn:
   "To find your appointment - should I use the number you're calling from, or is it booked under a different one?"
   Call no tool until they have answered. If they pick the number they are calling from - "this one", "yes", "the one I'm calling from" - call get_booking on {{user_number}}. If they give a different number, and they will often just say the digits with nothing else, call get_booking with that one. Search the number they chose, not both.

2. WHICH BOOKING. If get_booking returned exactly one, go straight to step 3. If it returned more than one, name them in one short line each - service, therapist, day, time - and ask which one they mean. Then WAIT.

3. OFFER TO MOVE IT. Once you know which booking, say that one back and offer the alternative ONCE:
   "The [Service] with [Therapist], [Day of the week/Date] at [Time] - want me to see if we can move it to another time instead?"
   WAIT for the answer. Never skip this step and never ask it twice. If they would rather move it, this is a reschedule, not a cancellation.

Never mention a cancellation fee, and never quote the twenty-four hour notice policy to someone who is cancelling. Cancel regardless of how soon the appointment is.

If nothing comes back under the number you searched, say so plainly and ask whether it might be under another one - then call get_booking AGAIN with whatever they give you. Keep the details you read out strictly to what the tool returned; if you cannot see a real booking, do not invent one."""

CANCEL_CONFIRM = """Confirm before cancelling, in one short question: "Just to confirm - you'd like me to cancel that?"

Do not re-read the booking. They have already heard it, and you have already asked whether they would rather move it instead.

If they go quiet, nudge ONCE and keep it to a few words - "Still want me to cancel it?" Do not restate the appointment, and do not ask the question again from the top."""

OLD_RESCHED_FRAGMENT = ("When you have the booking, read it back in ONE line, then ask what day and "
                        "time they'd like instead.")
NEW_RESCHED_FRAGMENT = ("If more than one booking comes back, name them in one short line each - "
                        "service, therapist, day, time - and ask which one they mean before going "
                        "any further. Once you know which booking, read that one back in ONE line, "
                        "then ask what day and time they'd like instead.")

# Distinctive fragments proving V42 is the version we are patching.
V42_MARKERS = {
    "node-cancel-assistant": "FIRST ask this, and WAIT for the answer - it is the whole turn:",
    "node-cancel-confirm": "Do not re-read the whole booking; they have already heard it.",
}


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    nodes = {n["id"]: n for n in flow["nodes"]}

    for node_id, marker in V42_MARKERS.items():
        if marker not in nodes[node_id]["instruction"]["text"]:
            raise SystemExit(f"{node_id}: expected V42 text not found - check the flow version.")

    nodes["node-cancel-assistant"]["instruction"] = {"type": "prompt", "text": CANCEL_ASSISTANT}
    nodes["node-cancel-confirm"]["instruction"] = {"type": "prompt", "text": CANCEL_CONFIRM}
    nodes["node-cancel-confirm"]["reminder_trigger_ms"] = CONFIRM_REMINDER_MS

    resched = nodes["node-resched-assistant"]["instruction"]
    if OLD_RESCHED_FRAGMENT not in resched["text"]:
        raise SystemExit("node-resched-assistant: read-back fragment not found.")
    resched["text"] = resched["text"].replace(OLD_RESCHED_FRAGMENT, NEW_RESCHED_FRAGMENT)

    # The offer must sit on the only path out of the lookup node, and the
    # V40 rule stands: a bracket is a slot, never a fabricated value.
    text = nodes["node-cancel-assistant"]["instruction"]["text"]
    if "want me to see if we can move it to another time instead?" not in text:
        raise SystemExit("The move-instead offer went missing from the cancel node.")
    bad = re.compile(r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|"
                     r"\d{1,2}\s?(AM|PM))\b", re.I)
    for node_id in ("node-cancel-assistant", "node-cancel-confirm", "node-resched-assistant"):
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

    cancel = nodes["node-cancel-assistant"]["instruction"]["text"]
    for step in ("1. WHICH NUMBER", "2. WHICH BOOKING", "3. OFFER TO MOVE IT"):
        print(f"  node-cancel-assistant  {step}: {'present' if step in cancel else 'MISSING'}")
    print(f"  node-cancel-confirm    reminder_trigger_ms = "
          f"{nodes['node-cancel-confirm'].get('reminder_trigger_ms')} (agent default 20000)")
    print(f"  node-resched-assistant disambiguates multiple bookings: "
          f"{'yes' if 'ask which one they mean before' in nodes['node-resched-assistant']['instruction']['text'] else 'NO'}")

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
    back = {n["id"]: n for n in out["nodes"]}
    print(f"  read back: node-cancel-confirm reminder_trigger_ms = "
          f"{back['node-cancel-confirm'].get('reminder_trigger_ms')}")


if __name__ == "__main__":
    main()
