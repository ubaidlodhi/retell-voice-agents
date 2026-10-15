"""
V77 - a full day is "fully booked", never "closed"; "trouble finishing" only after a real error; no
silence in the time step. DRAFT ONLY.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v77_full_day_and_wording.py [--dry-run]

Calls 2026-10-07..09 (inbound v29):
  * call_bffcab7c, call_e3d02f48: get_slots returned nothing for the rest of the day
    (totalAvailableAllBands 0) and Aria said "Looks like we're actually closed today" - the spa is open
    until 8. Then only "What day works?"; the second caller hung up.
      -> Discovery: say "fully booked", never "closed", and look up the next day straight away.
  * call_88121ba3, call_bffcab7c, call_17652e99, call_6a4c88df: the caller turned the times down and
    "Booking - Could Not Complete" said "I'm having trouble finishing that booking" - it sounds like
    the system broke when nothing did.
      -> that line only when book_appointment returned an error; otherwise "No problem".
  * call_bffcab7c: "Yesterday. Thank you." -> NO_RESPONSE_NEEDED in Discovery (public log 22:11:16)
    -> 24 s of silence. The V74 global rule did not hold at the step itself.
      -> Discovery: every caller turn gets a reply; an answer that makes no sense gets a question.

No --publish flag on purpose.
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

FULL_OLD = "Only when totalAvailableAllBands is 0 do you suggest another date."
FULL_NEW = ("When totalAvailableAllBands is 0 the day is fully booked: say \"We're fully booked [today/that day]\" - "
            "never \"closed\"; the spa is open, the day is just full. Then, before asking anything, call get_slots "
            "for the next day and offer what it returns: \"...but tomorrow I have [Time], [Time], or [Time] - would "
            "one of those work?\"")

REPLY_ANCHOR = "If they named only a day, go on from step 1."
REPLY_ADD = (" Every caller turn here gets a reply - never NO_RESPONSE_NEEDED unless they asked you to hold on. If an "
             "answer makes no sense (\"yesterday\" for a booking, a stray \"thank you\"), ask what they meant.")

FAIL_OLD = ("Tell them plainly you're having trouble finalizing it - no jargon, no error codes - and offer a callback: "
            "\"I'm having trouble finishing that booking. Want me to have the team call you to set it up?\"")
FAIL_NEW = ("If book_appointment returned an error in this call, tell them plainly - no jargon, no error codes - and "
            "offer a callback: \"I'm having trouble finishing that booking. Want me to have the team call you to set "
            "it up?\" Otherwise nothing broke - no time suited them, or they stopped - so never say you had trouble: "
            "\"No problem - want me to have the team call you to find a time that works?\"")


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


def swap(text: str, old: str, new: str, where: str) -> str:
    if new in text:
        return text
    if text.count(old) != 1:
        raise SystemExit(f"{where}: expected one {old[:50]!r} - merge by hand")
    return text.replace(old, new)


def patch(flow: dict) -> tuple[dict, list[str]]:
    flow = json.loads(json.dumps(flow))
    n = {x["id"]: x for x in flow["nodes"]}
    done = []
    d = n["node-book-discovery"]["instruction"]
    new = swap(d["text"], FULL_OLD, FULL_NEW, "discovery")
    if new != d["text"]:
        d["text"] = new
        done.append("discovery: a full day is 'fully booked', then the next day is looked up")
    new = swap(d["text"], REPLY_ANCHOR, REPLY_ANCHOR + REPLY_ADD, "discovery")
    if new != d["text"]:
        d["text"] = new
        done.append("discovery: every caller turn gets a reply")
    fl = n["node-book-failed"]["instruction"]
    new = swap(fl["text"], FAIL_OLD, FAIL_NEW, "could not complete")
    if new != fl["text"]:
        fl["text"] = new
        done.append("could not complete: 'trouble finishing' only after a booking error")
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
    assert FULL_NEW in on["node-book-discovery"]["instruction"]["text"]
    assert REPLY_ADD in on["node-book-discovery"]["instruction"]["text"]
    assert FAIL_NEW in on["node-book-failed"]["instruction"]["text"]
    assert not out.get("is_published")
    print(f"PATCHED draft flow v{out['version']} - NOT published")


if __name__ == "__main__":
    main()
