"""
V74 - no silent turns while a booking is being made. DRAFT ONLY.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v74_no_silent_turns.py [--dry-run]

call_d18cc6ab (inbound v27, 2026-10-06) had two 21-second silences, each ended only by Retell's
reminder line:
  1. 110 s - 131 s. After the wrong jump to reschedule (fixed in V73) the caller was dropped back in
     "Booking - Service & Length" with the massage, the day and the time already said. That step
     asked the day and the time again, then made a bare statement - "Okay, I'll get you booked for a
     one-hour deep tissue massage at 6 PM today." - and waited. Its exit is judged on the caller's
     next turn, and the caller was waiting for Aria. Reminder: "Just checking in - want me to finish
     booking that?"
  2. 136 s - 157 s. On "Yes, please" the call moved to "Booking - Discovery", whose model returned
     NO_RESPONSE_NEEDED (public log 00:38:57.471) - the stay-quiet signal meant for "hold on", a
     recording or our own echo. Nothing was said and no time was looked up. Reminder: "Are you
     still there?"
  -> Service & Length: never promises a booking or confirms a time; when the day/time were already
     given it asks to check them, as a question.
  -> Discovery: arriving with a day and time already named, its first action is get_slots for it,
     then the time offered back as a question. It never answers with silence.
  -> Turn-taking (global): NO_RESPONSE_NEEDED only for "hold on", a recording or the echo - never
     when the caller has answered or is waiting on Aria.

No --publish flag on purpose. Tools are left where they are.
"""

from __future__ import annotations
import argparse
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

RETELL_BASE = "https://api.retellai.com"
FLOW_ID = "conversation_flow_bdb1968b28ed"

SVC_OLD = ("Once the massage and the length are both settled, ask what day they want to come in - \"What day works "
           "for you?\" - and stop there. No morning-or-afternoon question, no name, no number: you have no "
           "availability tool and no booking tool in this step.")
SVC_ADD = ("\nIf they already told you the day, or the day and the time, do not ask for them again - check them "
           "instead, as a question: \"[Length] [massage], [day] at [time] - shall I check that's open?\" Never say "
           "you will book it, get it booked or set it up, and never confirm a time: you cannot see times here. "
           "Every turn in this step ends with a question - a statement leaves the caller waiting in silence.")

DISC_ANCHOR = ("If you are back here because the caller asked for a particular therapist after a time was agreed, "
               "do not start over: check that time for that person (step 2) and go from there.")
DISC_ADD = ("\n\nWhen you arrive here, you always answer - never with silence. If the caller already named a day and "
            "a time earlier in the call, your FIRST action is get_slots for that day with preferredTime set to that "
            "time - before you say anything - then offer it back as a question: \"[Time] is open - want that "
            "one?\" (or, if it is not open, the nearest times). If they named only a day, go on from step 1.")

TURN_ANCHOR = "Do not say \"okay\" or \"take your time.\""
TURN_ADD = (" NO_RESPONSE_NEEDED is only for these three cases - \"hold on\", a recording, your own echo. When the "
            "caller has answered you or is waiting on you - a yes, a time, \"go ahead\", \"finish booking it\" - "
            "you always reply.")


def api_key() -> str:
    key = os.environ.get("RETELL_API_KEY")
    if key:
        return key
    raw = (Path(__file__).resolve().parents[2] / ".mcp.json").read_text(encoding="utf-8")
    cfg = json.loads(raw[raw.index("{"):])
    return re.search(r"key_[a-f0-9]+", json.dumps(cfg["mcpServers"]["retell-sage"])).group(0)


def request(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(RETELL_BASE + path, data=data, method=method, headers={
        "Authorization": f"Bearer {api_key()}", "Content-Type": "application/json", "User-Agent": "curl/8.0"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            text = resp.read().decode()
            return json.loads(text) if text.strip() else {}
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Retell {method} {path} -> {e.code}: {e.read().decode()[:600]}")


def add_after(text: str, anchor: str, addition: str, where: str) -> str:
    if addition in text:
        return text
    if text.count(anchor) != 1:
        raise SystemExit(f"{where}: expected one {anchor[:50]!r} - merge by hand")
    return text.replace(anchor, anchor + addition)


def patch(flow: dict) -> tuple[dict, list[str]]:
    flow = json.loads(json.dumps(flow))
    n = {x["id"]: x for x in flow["nodes"]}
    done = []
    for nid, anchor, addition, label in (
            ("node-book-service", SVC_OLD, SVC_ADD, "service & length: day/time already given -> a question, never a promise"),
            ("node-book-discovery", DISC_ANCHOR, DISC_ADD, "discovery: arriving with a time -> get_slots first, never silence")):
        ins = n[nid]["instruction"]
        new = add_after(ins["text"], anchor, addition, nid)
        if new != ins["text"]:
            ins["text"] = new
            done.append(label)
    new = add_after(flow["global_prompt"], TURN_ANCHOR, TURN_ADD, "global prompt")
    if new != flow["global_prompt"]:
        flow["global_prompt"] = new
        done.append("turn-taking: NO_RESPONSE_NEEDED only for hold on / recording / echo")
    return flow, done


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    if live.get("is_published"):
        raise SystemExit(f"latest flow v{live['version']} is PUBLISHED - make a draft first, never patch the live one")
    patched, done = patch(live)
    print(f"draft flow v{live['version']}:")
    for x in done or ["nothing to do"]:
        print("  " + x)
    if args.dry_run or not done:
        print("Dry run - Retell not modified." if args.dry_run else "Already up to date.")
        return
    body = {k: v for k, v in patched.items()
            if k not in ("conversation_flow_id", "version", "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    on = {x["id"]: x for x in out["nodes"]}
    assert SVC_ADD in on["node-book-service"]["instruction"]["text"]
    assert DISC_ADD in on["node-book-discovery"]["instruction"]["text"]
    assert TURN_ADD in out["global_prompt"]
    assert not out.get("is_published")
    print(f"PATCHED draft flow v{out['version']} - NOT published")


if __name__ == "__main__":
    main()
