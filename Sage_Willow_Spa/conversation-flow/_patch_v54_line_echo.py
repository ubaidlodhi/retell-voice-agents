"""
V54 - the line plays Aria's own voice back; she must not answer herself.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v54_line_echo.py [--dry-run] [--publish]

DRAFT ONLY by default (Ubaid's sequencing: draft + dev first, he tests, then
publish).

Evidence: call_b004eecd765b2feed08836f06a3 (inbound v15, 2026-09-20, real
caller via the Mint/T-Mobile forward). The caller channel of the multichannel
recording carries the agent's own greeting 0.9 s late at about -10 dB (cross-
correlation peak at 0.88-0.90 s; that channel is silent before Aria speaks).
Transcribed as the caller: "Hi, this is Ari" and then "Dr. Manuela" - a garble
of "Sage and Willow". Result: the greeting was cut at "from Sage and Willow",
Aria answered the garble with "Sure, what can I help you with?", the caller
never got a proper opening and never spoke; 150 s to inactivity.

Same thing on call_b32ae2e91d1ab8a86217186f62b (09-03, "Hi, this is Arna" at
0.8 s, greeting cut, caller gone at 9 s) - the lead we later rang back.

Two of 39 recent inbound calls. Both on the greeting, never later: network
echo cancellers need a few seconds to converge, so the opening is where the
echo lives. Meanwhile real callers do not barge into the greeting at all
(0 of 39 - the "overlaps" are people answering in the last 0.3 s of the
question).

Fix, two parts:
1. Greeting node: interruption_sensitivity 0. The echo is a copy of whatever
   Aria says, for as long as she says it, so any sensitivity above 0 lets a
   long enough burst cut her off. The greeting is 4.5 s and nobody real
   interrupts it. What the caller says during it is still transcribed and
   answered right after.
2. Global Turn-taking rule: a "caller" turn that is her own words - her name,
   her introduction, her question asked back - is echo. Reply
   NO_RESPONSE_NEEDED (the same silent turn the hold-on rule already uses;
   verified silent on calls 3010cd9 / c203c97), unless it cut her off, in
   which case say the sentence again. Anything that could be an answer is the
   caller.
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


# The hold-on paragraph the rule slots in after. Exact text, so the patch
# refuses to run if the Turn-taking section has changed shape.
HOLD_ON_PARAGRAPH = (
    'If the caller says "hold on," "give me a moment," "let me check," or "one second" - '
    "reply NO_RESPONSE_NEEDED and stay quiet. Do not say \"okay\" or \"take your time.\""
)

ECHO_RULE = (
    "Sometimes the line plays your own voice back to you about a second late, and it lands "
    "as the caller's turn: your last sentence, or a chopped or garbled piece of it, sometimes "
    "mangled into other words or a name. You can tell because it is something only you would "
    "say - your own name, your introduction, your own question asked back at you. That is not "
    "the caller and it is not the caller repeating you; the whole burst is echo, including any "
    "odd word or name tacked onto it. Reply NO_RESPONSE_NEEDED and wait, exactly as for "
    "\"hold on\". If it cut you off mid-sentence, say that sentence again from the start "
    "instead. Anything that could be an answer to your question - a massage, a time, a yes or "
    "a no - is the caller: take it."
)

GREETING_NODE = "node-greeting"


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    nodes = {n["id"]: n for n in flow["nodes"]}

    # 2. the rule
    gp = flow["global_prompt"]
    if ECHO_RULE in gp:
        print("  echo rule already present - leaving the prompt as is")
    else:
        if gp.count(HOLD_ON_PARAGRAPH) != 1:
            raise SystemExit("Turn-taking hold-on paragraph not found exactly once - prompt changed shape.")
        gp = gp.replace(HOLD_ON_PARAGRAPH, HOLD_ON_PARAGRAPH + "\n\n" + ECHO_RULE, 1)
        flow["global_prompt"] = gp

    # 1. the greeting cannot be talked over
    greet = nodes[GREETING_NODE]
    if greet["type"] != "conversation":
        raise SystemExit(f"{GREETING_NODE} is a {greet['type']} node, expected conversation.")
    greet["interruption_sensitivity"] = 0

    # guards
    tt = flow["global_prompt"][flow["global_prompt"].index("## Turn-taking"):]
    tt = tt[:tt.find("\n## ")] if "\n## " in tt else tt
    if tt.count("NO_RESPONSE_NEEDED") != 2:
        raise SystemExit("Turn-taking should mention NO_RESPONSE_NEEDED exactly twice (hold-on + echo).")
    if len(ECHO_RULE.split()) > 140:
        raise SystemExit("echo rule is too long for an every-turn prompt")
    if re.search(r"\b(Manuela|Arna)\b", flow["global_prompt"]):
        raise SystemExit("a transcript garble leaked into the prompt")
    if nodes[GREETING_NODE].get("interruption_sensitivity") != 0:
        raise SystemExit("greeting interruption_sensitivity did not stick")
    # Dashboard edits that must survive.
    if flow.get("start_speaker") != "user" or flow.get("begin_after_user_silence_ms") != 6000:
        raise SystemExit("Ubaid's start_speaker/user + 6000ms dashboard edit is not intact.")
    # V53 must still be there - this patch stacks on it.
    if "is NOT a service" not in nodes["node-book-discovery"]["instruction"]["text"]:
        raise SystemExit("V53 service gate missing - patching the wrong version?")
    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true")
    args = ap.parse_args()

    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft flow v{live.get('version')} - {len(live['nodes'])} nodes")
    patched = patch(live)
    nodes = {n["id"]: n for n in patched["nodes"]}
    print(f"  greeting interruption_sensitivity: {nodes[GREETING_NODE].get('interruption_sensitivity')}")
    print(f"  global prompt: {len(live['global_prompt'])} -> {len(patched['global_prompt'])} chars")

    SNAPSHOT.write_text(json.dumps(patched, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"snapshot -> {SNAPSHOT.name}")
    if args.dry_run:
        print("Dry run - Retell not modified.")
        return

    body = {k: v for k, v in patched.items()
            if k not in ("conversation_flow_id", "version",
                         "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    back = {n["id"]: n for n in out["nodes"]}
    if back[GREETING_NODE].get("interruption_sensitivity") != 0 or ECHO_RULE not in out["global_prompt"]:
        raise SystemExit("read-back mismatch after PATCH")
    print(f"PATCHED draft flow v{out.get('version')} (NOT published)")
    if not args.publish:
        print("  Draft only - real callers still get latest_published.")
        return
    request("POST", f"/publish-agent/{AGENT_ID}")
    print("PUBLISHED")


if __name__ == "__main__":
    main()
