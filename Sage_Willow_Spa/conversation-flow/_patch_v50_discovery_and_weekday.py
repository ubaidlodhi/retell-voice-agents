"""
V50 - offer the options, ask the part of day, and stop guessing weekdays.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v50_discovery_and_weekday.py [--dry-run] [--publish]

Evidence: call_b3ddd8af904ad050d773001c8dd (outbound V06) plus the inbound calls
of the same day. All five live in the SHARED flow, so fixing inbound and
rebuilding outbound fixes both.

1. SHE DID NOT OFFER TO READ THE OPTIONS          (Ubaid)
   Outbound: "Sure. What kind of massage are you looking for?"
   Inbound : "What kind of massage are you looking for? I can go over the
              options if you're not sure."
   Step 1 only said what to do WHEN ASKED, so the offer was luck, not design.
   It is now the required wording for the ask.

2. SHE SKIPPED "MORNING, AFTERNOON OR EVENING?"    (Ubaid)
   Caller gave a day and no time; step 3 says ask the part of day. Instead she
   went to get_slots and answered with one slot per band - "Morning at ten,
   afternoon at one thirty, or evening at six thirty" - which buries the choice
   in three specific times. Step 3 is now an explicit turn of its own that must
   happen before any clock time is spoken.

3. SHE GOT THE WEEKDAY WRONG AND THE CALLER HAD TO CORRECT HER   (found here)
       Aria:  "did you mean Monday, September 30th?"
       Ubaid: "It's not Monday that day."
       Aria:  "Oh, you're right, September 30th is a Wednesday."
   Root cause: the only calendar she has is {{current_calendar_...}}, which
   covers 14 days. The call was on 2026-09-14, so September 30th was off the
   end of it and she worked the weekday out herself - wrong. Arguing with a
   caller about a calendar fact costs more trust than any of the rest of this.
   She may now only state a weekday that the calendar or a tool gave her.

4. SHE KEPT READING THE LIST AFTER HE HAD CHOSEN   (found here)
       Aria:  "No rush. Do you want the morning "
       Ubaid: "10:30."
       Aria:  "at 10, the afternoon at 1:30, or the evening at 6:30?"
       Ubaid: "10:30."
   He answered twice. V39's turn-taking rule covered restarting a clipped turn
   but not resuming one, and node-book-discovery runs at
   interruption_sensitivity 0.5 (deliberately hard to interrupt, so a noisy
   line cannot clip a price list) which makes resuming the default.

5. "$130" IN THE READBACK                          (found here)
   "...at 10:30 AM, for $130." The currency rule says always say "dollars" and
   never "$90"; she had said "one hundred thirty dollars" correctly earlier in
   the same call. Same figures-versus-words family as the phone number.
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


# --- 1. offer the options -----------------------------------------------------
OLD_STEP1 = "1. SERVICE. If they already named one, take it.\n"
NEW_STEP1 = (
    "1. SERVICE. If they already named one, take it.\n"
    "   If they have NOT named one, ask and offer help in the same breath: \"What kind of "
    "massage are you looking for? I can go over the options if you're not sure.\" Never ask "
    "the bare question on its own - someone who does not know the menu has to hear that you "
    "can read it to them.\n"
)

# --- 2. part of day is its own turn -------------------------------------------
OLD_STEP3 = (
    "3. DAY AND TIME. Ask plainly. If they give a day but no time, ask \"morning, "
    "afternoon, or evening?\" - but only offer parts of day that have not already passed "
    "today. After 7:30 PM, suggest tomorrow."
)
NEW_STEP3 = (
    "3. DAY AND TIME. Ask what day they want. Once you have a day but no time, your NEXT "
    "turn is that question and nothing else: \"Do you want to come in the morning, "
    "afternoon, or evening?\" Then WAIT.\n"
    "   Do not skip it and do not answer it for them. Going straight to clock times - "
    "\"morning at ten, afternoon at one thirty, or evening at six thirty\" - is wrong: it "
    "buries their choice in three specific slots instead of letting them pick a part of the "
    "day. Clock times come later, at step 6, after they have chosen one.\n"
    "   Only offer parts of day that have not already passed today. After 7:30 PM, suggest "
    "tomorrow."
)

# --- 3. never guess a weekday -------------------------------------------------
CAL_ANCHOR = "14-day calendar: {{current_calendar_America/Los_Angeles}}\n"
WEEKDAY_RULE = (
    "\nThat calendar is the ONLY thing that tells you which weekday a date falls on, and it "
    "runs out after fourteen days. If the caller names a date that is not in it, do NOT work "
    "the weekday out yourself - you will get it wrong, and being corrected on a calendar "
    "fact by the caller costs you their trust for the rest of the call. Repeat the date back "
    "with no weekday at all - \"September thirtieth, is that right?\" - and let get_slots "
    "tell you the day. Once any tool returns that date, use the weekday the tool gives you "
    "and never your own.\n"
)

# --- 4. stop the list when they pick ------------------------------------------
OLD_TURN = (
    "If a noise or a stray word cuts you off mid-sentence and the caller then answers the "
    "question you were part-way through asking, TAKE THE ANSWER. Do not start that turn "
    "again from the beginning, and never make them give you the same answer twice - they "
    "already said it."
)
NEW_TURN = (
    OLD_TURN + " That applies just as much when you are part-way through reading a list of "
    "options and they pick one: stop the list there, take their pick and move on. Never "
    "carry on reading the remaining options at someone who has already chosen."
)

# --- 5. money as words --------------------------------------------------------
OLD_READBACK_TAIL = (
    "Name the therapist only if the caller specifically asked for one. Do not repeat the "
    "phone number - it is already confirmed."
)
NEW_READBACK_TAIL = (
    "Write the total as words with \"dollars\" on the end - \"one hundred thirty dollars\" - "
    "never as figures with a dollar sign.\n\n"
    + OLD_READBACK_TAIL
)


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    nodes = {n["id"]: n for n in flow["nodes"]}
    disc = nodes["node-book-discovery"]["instruction"]

    for old, new, where in ((OLD_STEP1, NEW_STEP1, "discovery step 1"),
                            (OLD_STEP3, NEW_STEP3, "discovery step 3")):
        if old not in disc["text"]:
            raise SystemExit(f"{where} not found - the instruction changed shape.")
        disc["text"] = disc["text"].replace(old, new, 1)

    gp = flow["global_prompt"]
    if CAL_ANCHOR not in gp:
        raise SystemExit("Calendar line not found in the global prompt.")
    if OLD_TURN not in gp:
        raise SystemExit("Turn-taking block not found in the global prompt.")
    gp = gp.replace(CAL_ANCHOR, CAL_ANCHOR + WEEKDAY_RULE, 1)
    gp = gp.replace(OLD_TURN, NEW_TURN, 1)
    flow["global_prompt"] = gp

    rb = nodes["node-book-readback"]["instruction"]
    if OLD_READBACK_TAIL not in rb["text"]:
        raise SystemExit("Readback tail not found.")
    rb["text"] = rb["text"].replace(OLD_READBACK_TAIL, NEW_READBACK_TAIL, 1)

    # Guards: the V49 phone sample is still the only literal number allowed, and
    # no fabricated weekday may creep into a node prompt.
    allowed = {"+14158923245", "(415) 892-3245", "415-892-3245", "14158923245", "4158923245"}
    phone_like = re.compile(r"\b\d{3}[-. ]\d{3}[-. ]\d{4}\b|\b\d{7,}\b|\(\d{3}\)\s?\d{3}-\d{4}")
    weekday = re.compile(r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b")
    blobs = [(flow["global_prompt"], "global_prompt")]
    blobs += [((n.get("instruction") or {}).get("text", "") or "", n["id"]) for n in flow["nodes"]]
    for blob, label in blobs:
        for hit in phone_like.findall(blob):
            if hit.strip() not in allowed:
                raise SystemExit(f"{label} carries an unsanctioned number: {hit}")
        if label != "global_prompt" and weekday.search(blob):
            raise SystemExit(f"{label} names a weekday: {weekday.search(blob).group(0)}")

    for needle, where in (
        ("I can go over the options if you're not sure", "step 1 offer"),
        ("morning, afternoon, or evening?\" Then WAIT", "step 3 question"),
    ):
        if needle not in disc["text"]:
            raise SystemExit(f"{where} did not land.")
    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true")
    args = ap.parse_args()

    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft flow v{live.get('version')}")
    patched = patch(live)
    print("  1 discovery step 1 : offers to read the options")
    print("  2 discovery step 3 : part-of-day is its own turn, before any clock time")
    print("  3 global prompt    : no weekday beyond the 14-day calendar")
    print("  4 global prompt    : stop the list when they pick")
    print("  5 readback         : total in words, not $figures")
    print(f"  global_prompt {len(live['global_prompt'])} -> {len(patched['global_prompt'])} chars")

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
