"""
V51 - "check again" means a fresh lookup; a part of day is never empty until the
census says so; the day comes before the part of day.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v51_recheck_means_lookup.py [--dry-run] [--publish]

Evidence: call_bf1fba1444d077c131bf9411e1f (outbound V07, 2026-09-19), which
ended with the caller swearing at the agent and hanging up.

    get_slots  timeOfDay: morning  -> 10, 10:30, 11, 11:30      (t=120s)
    Caller: "12:30."
    Aria:   "12:30 isn't an option."
    Caller: "Check again."
    Aria:   "The latest morning spot is 11:30. 12:30 isn't open."        <- no tool call
    Caller: "...you just have to check that time"
    Aria:   "12:30 isn't open tomorrow ... there's nothing in the afternoon."  <- never looked
    Caller: "Use the tool and check. For tomorrow's afternoon."
    get_slots  timeOfDay: afternoon -> 12:00, 12:30, 1:00 ...    (t=202s)
    Aria:   "You're right, 12:30 is open tomorrow."

Two layers failed.

BACKEND (fixed the same day in both n8n workflows, "Format: Time Slots
Response"): the timeOfDay filter ran BEFORE the census, so availabilityByDay for
a morning lookup held only mornings and was stamped complete. The prompt says -
correctly, that is the field's whole job - to treat it as the complete picture.
So the agent was telling the truth as far as it could see. The census is now
built from the whole day; timeOfDay only narrows what is read out first. A time
the caller names is now either in availabilityByDay or genuinely not open.

PROMPT (this patch):
  1. "Check again", "are you sure", "look again", any push-back on a time being
     unavailable -> call get_slots AGAIN with preferredTime, every time, before
     answering. The old text said this once, softly, at the end of step 6, and
     the model answered two re-checks from memory. It is now its own rule.
  2. Never say a part of the day has nothing in it unless availabilityByDay for
     that part is actually empty. "There's nothing in the afternoon" was
     invented for a band the agent had never seen.
  3. Step 3 got ahead of itself: "What day do you want to come in?" - "Mm-hmm."
     - "Morning, afternoon, or evening?" A grunt is not a day. Ask for the day
     again; the part-of-day question waits until there is one.
  4. count: 0 no longer means the day is empty. The response now carries
     totalAvailableAllBands and the other bands in the census - offer from
     those before suggesting another date.
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


# --- step 3: the day comes first ---------------------------------------------
OLD_STEP3_HEAD = (
    "3. DAY AND TIME. Ask what day they want. Once you have a day but no time, your NEXT "
    "turn is that question and nothing else:"
)
NEW_STEP3_HEAD = (
    "3. DAY AND TIME. Ask what day they want. If what comes back is not a day - \"mm-hmm\", "
    "\"yeah\", a question, silence - ask for the day again; do not move on without one. "
    "Once you have a day but no time, your NEXT turn is that question and nothing else:"
)

# --- step 5: the census is the whole day; re-check means a real lookup --------
OLD_STEP5_BLOCK = (
    "   - If count is 0 with no staffId, offer a different part of day or a different date.\n"
    "   - availabilityByDay is the COMPLETE list of open times; slots is only a sample. "
    "Before telling anyone a time or a part of day is unavailable, check availabilityByDay. "
    "Answer follow-ups like \"anything else that morning?\" from it - do not re-run get_slots "
    "for that.\n"
    "   - If the caller names a time you did not offer, look it up in availabilityByDay. If "
    "it is there, use it. If it genuinely is not, say so and offer the closest real times. "
    "NEVER quietly book a different time than the one they asked for."
)
NEW_STEP5_BLOCK = (
    "   - availabilityByDay is the COMPLETE list of open times for the WHOLE day - every "
    "part of it, no matter which timeOfDay you passed. slots is only the sample you read "
    "aloud first. Before telling anyone a time or a part of day is unavailable, check "
    "availabilityByDay. Answer follow-ups like \"anything else that morning?\" from it.\n"
    "   - If count is 0, the day is NOT empty - look at availabilityByDay and "
    "totalAvailableAllBands and offer what is open in the other parts of the day. Only "
    "when totalAvailableAllBands is 0 do you suggest another date.\n"
    "   - NEVER say a part of the day has nothing in it unless availabilityByDay shows that "
    "part empty. Saying \"there's nothing in the afternoon\" about an afternoon you have not "
    "looked at is a lie, and callers catch it.\n"
    "   - If the caller names a time you did not offer, look it up in availabilityByDay. If "
    "it is there, use it - no need to search again. If it is not there, it is not open: say "
    "so and offer the closest real times. NEVER quietly book a different time than the one "
    "they asked for.\n"
    "   - RE-CHECK RULE. If the caller says \"check again\", \"are you sure\", \"look again\", "
    "\"double-check\", or pushes back at all on a time being unavailable, you call get_slots "
    "AGAIN - with preferredTime set to the time they want and no timeOfDay - BEFORE you "
    "answer. Every time, no exceptions, even if you are certain. Never answer a re-check "
    "from an earlier result; the caller asked you to look, so look."
)

# The old soft version at the end of step 6 is superseded; keep the rest of 6.
OLD_STEP6_TAIL = (
    " If they ask you to re-check a specific time, actually call get_slots again with "
    "preferredTime - do not answer from the earlier result."
)
NEW_STEP6_TAIL = " A re-check request is covered by the RE-CHECK RULE in step 5."


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    nodes = {n["id"]: n for n in flow["nodes"]}
    disc = nodes["node-book-discovery"]["instruction"]
    text = disc["text"]
    for old, new, where in ((OLD_STEP3_HEAD, NEW_STEP3_HEAD, "step 3 head"),
                            (OLD_STEP5_BLOCK, NEW_STEP5_BLOCK, "step 5 block"),
                            (OLD_STEP6_TAIL, NEW_STEP6_TAIL, "step 6 tail")):
        if old not in text:
            raise SystemExit(f"{where} not found - the discovery instruction changed shape.")
        text = text.replace(old, new, 1)
    disc["text"] = text

    for needle, where in (("RE-CHECK RULE.", "re-check rule"),
                          ("for the WHOLE day - every part of it", "whole-day census"),
                          ("NEVER say a part of the day has nothing in it", "no invented empty band"),
                          ("do not move on without one", "day before part-of-day")):
        if needle not in text:
            raise SystemExit(f"{where} did not land.")

    weekday = re.compile(r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b")
    phone_like = re.compile(r"\b\d{3}[-. ]\d{3}[-. ]\d{4}\b|\b\d{7,}\b")
    if weekday.search(text):
        raise SystemExit("discovery node names a weekday")
    if phone_like.search(text):
        raise SystemExit("discovery node carries a phone-like number")
    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true")
    args = ap.parse_args()

    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft flow v{live.get('version')}")
    patched = patch(live)
    print("  step 3: a grunt is not a day - ask again before the part-of-day question")
    print("  step 5: census is the whole day; count 0 != empty day; no invented empty band")
    print("  step 5: RE-CHECK RULE - push-back => get_slots again with preferredTime, always")

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
