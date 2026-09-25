"""
V62 - after a therapist check, ASK (don't announce); read the phone number without the +1.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v62_therapist_question_phone_digits.py [--dry-run] [--publish]

Evidence: call_38cf8b90b659e674fc591c42e1b (Ubaid's test line, 2026-09-24 18:19 PT, inbound v19).

1. Silence after a therapist request.
       Aria:   4:30 PM is open. Does that work for you?
       Caller: Uh, yes.  /  With Niki.        (-> add-ons -> back to discovery, correct)
       Aria:   Okay, 4:30 with Nicky it is.   (statement)
       ... 23.6 s of silence ...
       Aria:   Just checking, did you still want 4:30 with Nicky?
   Nicky WAS free at 4:30 and the booking went through with her - the check
   worked. But the turn ended in a statement, and discovery only hands off on
   the caller's next turn. The "every turn ends with a question" rule is lifted
   once the caller "has said yes to ONE specific time" - and they had - so the
   model treated itself as exempt. Close that loophole in both places.

2. Phone read-back: +12532681856 was read as "one two five, three two six,
   eight one eight five six" - the country code read out and the groups
   shifted. The node's format example never says to drop the +1.
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
AGENT_ID = "agent_eceb7448aa1f37e8f436a63a43"
SNAPSHOT = Path(__file__).parent / "aria_conversation_flow.json"
PROD_URL = "https://automation.aiemply.com/webhook/retell-wix"

OLD_CONFIRM = 'If that person is listed for the time, confirm it as a question - "[Time] with [Name] is open - want that?"'
NEW_CONFIRM = ('If that person is listed for the time, confirm it as a question - "[Time] with [Name] is open - want that?" - '
               'even when they already said yes to the time. Announcing it ("[Time] with [Name] it is.") and stopping leaves '
               'the call in silence.')
OLD_HANDOFF = "Every turn in this step ends with a question until the caller has said yes to ONE specific time"
NEW_HANDOFF = ("Every turn in this step ends with a question until the caller has said yes to ONE specific time - "
               "and, if they named a therapist, to that time with that therapist")
OLD_PHONE = "Digit words, three groups, hyphens between the groups. Never say the figures."
NEW_PHONE = ("Digit words, three groups, hyphens between the groups. Never say the figures. The leading +1 is the "
             "country code - never say it. What you say is exactly the last ten digits, grouped three, three, four.")


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
    with urllib.request.urlopen(req, timeout=120) as resp:
        text = resp.read().decode()
        return json.loads(text) if text.strip() else {}


def once(text: str, old: str, new: str, where: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"{where}: expected one match for {old[:60]!r}, found {text.count(old)}")
    return text.replace(old, new)


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    n = {x["id"]: x for x in flow["nodes"]}
    d = n["node-book-discovery"]["instruction"]
    d["text"] = once(d["text"], OLD_CONFIRM, NEW_CONFIRM, "discovery")
    d["text"] = once(d["text"], OLD_HANDOFF, NEW_HANDOFF, "discovery")
    p = n["node-book-phone"]["instruction"]
    p["text"] = once(p["text"], OLD_PHONE, NEW_PHONE, "phone")
    # the phone example digits must still be a FORMAT, and nothing earlier may have gone
    if "Do you want to book a massage?" not in n["node-greeting"]["instruction"]["text"]:
        raise SystemExit("V59 opening gone")
    if (n["node-book-submit"].get("instruction") or {}).get("type") != "static_text":
        raise SystemExit("V60 pinned wait line gone")
    if "re-checking the time or the therapist never changes it" not in n["node-book-readback"]["instruction"]["text"]:
        raise SystemExit("V61 price rule gone")
    if sorted({t["url"] for t in flow["tools"]}) != [PROD_URL]:
        raise SystemExit("tools not all on PROD")
    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true")
    args = ap.parse_args()
    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    patched = patch(live)
    SNAPSHOT.write_text(json.dumps(patched, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"draft flow v{live['version']}: discovery asks after a therapist check; phone drops the +1")
    if args.dry_run:
        print("Dry run - Retell not modified.")
        return
    body = {k: v for k, v in patched.items()
            if k not in ("conversation_flow_id", "version", "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    on = {x["id"]: x for x in out["nodes"]}
    assert NEW_CONFIRM in on["node-book-discovery"]["instruction"]["text"] and NEW_PHONE in on["node-book-phone"]["instruction"]["text"]
    print(f"PATCHED draft flow v{out['version']}")
    if not args.publish:
        return
    request("POST", f"/publish-agent/{AGENT_ID}")
    vs = request("GET", f"/get-agent-versions/{AGENT_ID}")
    vs = vs.get("items", vs) if isinstance(vs, dict) else vs
    pub = max(v["version"] for v in vs if v.get("is_published"))
    pa = request("GET", f"/get-agent/{AGENT_ID}?version={pub}")
    pf = request("GET", f"/get-conversation-flow/{FLOW_ID}?version={pa['response_engine']['version']}")
    pn = {x["id"]: x for x in pf["nodes"]}
    ok = (NEW_CONFIRM in pn["node-book-discovery"]["instruction"]["text"] and NEW_HANDOFF in pn["node-book-discovery"]["instruction"]["text"]
          and NEW_PHONE in pn["node-book-phone"]["instruction"]["text"] and sorted({t["url"] for t in pf["tools"]}) == [PROD_URL])
    print(f"PUBLISHED inbound agent v{pub} -> flow v{pf['version']}; V62 + prod tools verified={ok}")
    if not ok:
        raise SystemExit("published version is not what was intended")


if __name__ == "__main__":
    main()
