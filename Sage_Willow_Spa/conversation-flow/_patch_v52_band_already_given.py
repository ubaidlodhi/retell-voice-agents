"""
V52 - don't ask for a part of day they just gave you; say the slot back before
moving on.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v52_band_already_given.py [--dry-run] [--publish]

Evidence: call_bed7bde2454d0bbba34f40a3280 (outbound V08, 2026-09-18). A good
call - booking created, the 1:30 PM switch that blew up the call before worked
- with two rough edges, both in the shared discovery node.

1. ASKED FOR WHAT SHE HAD JUST BEEN TOLD
       Aria:  "What day did you want to come in?"
       Ubaid: "Tomorrow."  "Morning."
       Aria:  "Do you want to come in the morning, afternoon, or evening?"
   V50 made the part-of-day question a mandatory turn so it could not be
   skipped. It also could not be skipped when the caller had already answered
   it. Now it is asked only when the part of day is still unknown.

2. MOVED ON WITHOUT SAYING THE SLOT BACK
       Aria:  "1:30 PM is in the afternoon. Want to switch to that instead?"
       Ubaid: "Yes."
       Aria:  "Okay, want to add any enhancements?"
       Ubaid: "So first confirm me that 1:30 is available or not."
   The caller had to ask for a confirmation that should have been volunteered.
   When a time is agreed - especially one outside what was offered - it gets
   said back in a few words before anything else happens.
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


OLD_STEP3_ASK = (
    "Once you have a day but no time, your NEXT turn is that question and nothing else: "
    "\"Do you want to come in the morning, afternoon, or evening?\" Then WAIT.\n"
    "   Do not skip it and do not answer it for them."
)
NEW_STEP3_ASK = (
    "Once you have a day but no time and no part of day, your NEXT turn is that question "
    "and nothing else: \"Do you want to come in the morning, afternoon, or evening?\" Then "
    "WAIT.\n"
    "   If they already told you the part of day - \"tomorrow morning\", or \"tomorrow\" "
    "then \"morning\" - you have your answer: do NOT ask it again, go straight to the "
    "lookup. Asking someone what they just told you sounds like you were not listening.\n"
    "   Otherwise do not skip it and do not answer it for them."
)

OLD_AGREED = "When the caller has agreed to a specific time, move on."
NEW_AGREED = (
    "When the caller has agreed to a specific time, say it back in a few words first - "
    "\"[Time] it is.\" - especially if it was a time you had not offered, so they hear that "
    "you have it. Then move on. Never jump to enhancements or the name without that "
    "acknowledgement; a caller who has to ask \"so is that time confirmed?\" was not told."
)


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    nodes = {n["id"]: n for n in flow["nodes"]}
    disc = nodes["node-book-discovery"]["instruction"]
    text = disc["text"]
    for old, new, where in ((OLD_STEP3_ASK, NEW_STEP3_ASK, "step 3 ask"),
                            (OLD_AGREED, NEW_AGREED, "agreed-time line")):
        if old not in text:
            raise SystemExit(f"{where} not found - the discovery instruction changed shape.")
        text = text.replace(old, new, 1)
    disc["text"] = text

    weekday = re.compile(r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b")
    phone_like = re.compile(r"\b\d{3}[-. ]\d{3}[-. ]\d{4}\b|\b\d{7,}\b")
    if weekday.search(text) or phone_like.search(text):
        raise SystemExit("discovery node carries a fabricated weekday or number")
    # The only literal clock time allowed is the standing "after 7:30 PM, suggest
    # tomorrow" business rule. Nothing this patch adds may introduce another.
    times = re.findall(r"\b\d{1,2}:\d{2}\b", text)
    if times != ["7:30"]:
        raise SystemExit(f"unexpected clock times in the discovery node: {times}")
    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true")
    args = ap.parse_args()

    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft flow v{live.get('version')}")
    patched = patch(live)
    print("  step 3: part-of-day question skipped when already answered")
    print("  agreed time is said back before moving on")

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
    if not args.publish:
        print("  NOTE: not live until published.")
        return

    request("POST", f"/publish-agent/{AGENT_ID}")
    vs = sorted(request("GET", f"/list-agent-versions/{AGENT_ID}")["items"],
                key=lambda v: v["version"], reverse=True)
    pub = max(v["version"] for v in vs if v.get("is_published"))
    agent = request("GET", f"/get-agent/{AGENT_ID}?version={pub}")
    fv = agent["response_engine"]["version"]
    served = request("GET", f"/get-conversation-flow/{FLOW_ID}?version={fv}")
    urls = sorted({t.get("url") for t in served["tools"] if t.get("url")})
    print(f"PUBLISHED -> agent v{pub} (flow v{fv}) is what callers now get")
    print(f"  tools: {urls}")
    if urls != ["https://automation.aiemply.com/webhook/retell-wix"]:
        raise SystemExit("PUBLISHED VERSION IS NOT ON THE PROD BACKEND - fix immediately.")
    print(f"  SOURCE_FLOW_VERSION for the outbound rebuild: {fv}")


if __name__ == "__main__":
    main()
