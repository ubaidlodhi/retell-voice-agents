"""
V48 - write phone numbers as digit WORDS again, so the voice says them one at a
time instead of reading "253-268-1856" as three large numbers.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v48_phone_digits_as_words.py [--dry-run]

Ubaid, 2026-09-14, on call_82cbc2946548410bb682c677e76 (published v6):
"the way its repeating number is not what I wanted, it should be a proper way,
like before."

    Aria: "Is 253-268-1856 the right number for this booking?"
    Ubaid: "Uh, can you repeat that?"
    Aria: "Sure, it's 253-268-1856. Is that the right number?"

Older versions wrote the digits out as words and sounded right:

    v0  "And is your phone number two five three, two six eight, one eight five six?"
    v5  "...is two five three, two six eight, one eight five six - sound good?"
    v8  "...six two six, eight nine zero, eight eight nine seven. Is that okay?"

The rule said "read the real digits one at a time, grouped three-three-four".
That describes the SPEECH, not the text to write, so the model wrote the digit
form and left the grouping to TTS - which instead reads 253 as "two hundred
fifty-three". The instruction was never wrong, it was just aimed at the wrong
layer.

Same failure class as the confirm line in V39/V40: the prompt used to carry a
worked example, the example was removed because the model read it aloud as
fact, and with no shape left to copy the model improvised a worse one. V40's
answer was a bracketed slot - the shape with nothing fabricated in it - so that
is what the phone rule gets too. A real sample number here would be read out on
a live call sooner or later; see [[feedback-no-fake-numbers-in-prompt-examples]].
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


# -----------------------------------------------------------------------------

OLD_PHONE_RULE = (
    "- **Phone numbers** - read the real digits one at a time, grouped three-three-four "
    "with short pauses. The only number you may say aloud is the live value of "
    "{{user_number}} or one the caller just gave you. There is no example number in these "
    "instructions to copy. If you cannot see real digits, ask."
)
NEW_PHONE_RULE = (
    "- **Phone numbers** - WRITE the digits out as words, one per digit, in three groups "
    "separated by commas. The shape is:\n"
    "      \"[digit] [digit] [digit], [digit] [digit] [digit], [digit] [digit] [digit] [digit]\"\n"
    "  so a number starting 2-5-3 is written \"two five three, ...\" and never \"253\". "
    "Digit form makes the voice say \"two hundred fifty-three\", which is not a phone "
    "number and forces the caller to ask you to repeat it. Never write the number with "
    "hyphens, brackets or spaces between figures - words only.\n"
    "  The only number you may say aloud is the live value of {{user_number}} or one the "
    "caller just gave you. There is no example number in these instructions to copy - the "
    "brackets above are slots, not digits. If you cannot see real digits, ask."
)

OLD_PHONE_NODE = (
    "Read back the real digits of {{user_number}}, grouped three-three-four, and ask if "
    "that number works for the booking. Say only that number - never one from these "
    "instructions, never one from memory.\n\n"
    "If they want a different number, take it. We never ask for an email."
)
NEW_PHONE_NODE = (
    "Read {{user_number}} back and ask if that number works for the booking.\n\n"
    "Write every digit as a word, in three groups: \"[digit] [digit] [digit], [digit] "
    "[digit] [digit], [digit] [digit] [digit] [digit]\". Never write it as figures - "
    "\"253-268-1856\" comes out of the voice as \"two hundred fifty-three\" and the caller "
    "has to ask you to say it again.\n\n"
    "Say only that number - never one from these instructions, never one from memory. If "
    "they ask you to repeat it, say the SAME digits again, the same way.\n\n"
    "If they want a different number, take it. We never ask for an email."
)


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    nodes = {n["id"]: n for n in flow["nodes"]}

    if OLD_PHONE_RULE not in flow["global_prompt"]:
        raise SystemExit("Phone pronunciation bullet not found in the global prompt.")
    flow["global_prompt"] = flow["global_prompt"].replace(OLD_PHONE_RULE, NEW_PHONE_RULE)

    node = nodes["node-book-phone"]["instruction"]
    if node["text"].strip() != OLD_PHONE_NODE:
        raise SystemExit("node-book-phone text has changed shape.")
    node["text"] = NEW_PHONE_NODE

    # No literal phone number may appear anywhere - a sample number in a prompt
    # gets spoken on a live call eventually. Brackets are slots, digits are not.
    digits = re.compile(r"\b\d{3}[-. ]\d{3}[-. ]\d{4}\b|\b\d{7,}\b")
    for blob, label in ([(flow["global_prompt"], "global_prompt")] +
                        [(n.get("instruction", {}).get("text", "") or "", n["id"])
                         for n in flow["nodes"]]):
        hit = digits.search(blob)
        if hit and hit.group(0) != "253-268-1856":  # only ever as the counter-example
            raise SystemExit(f"{label} carries a literal phone number: {hit.group(0)}")
    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true",
                    help="publish afterwards so live callers actually get the fix")
    args = ap.parse_args()

    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft flow v{live.get('version')} - {len(live['nodes'])} nodes")
    patched = patch(live)
    nodes = {n["id"]: n for n in patched["nodes"]}
    print("  global prompt phone rule: words + bracketed slot")
    print("  node-book-phone         : words + bracketed slot")
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
        print("  NOTE: the number serves latest_published, so this has NOT reached "
              "callers. Re-run with --publish.")
        return

    request("POST", f"/publish-agent/{AGENT_ID}")
    vs = sorted(request("GET", f"/list-agent-versions/{AGENT_ID}")["items"],
                key=lambda v: v["version"], reverse=True)
    pub = max(v["version"] for v in vs if v.get("is_published"))
    agent = request("GET", f"/get-agent/{AGENT_ID}?version={pub}")
    fv = agent["response_engine"]["version"]
    served = request("GET", f"/get-conversation-flow/{FLOW_ID}?version={fv}")
    urls = sorted({t.get("url") for t in served["tools"] if t.get("url")})
    served_node = next(n for n in served["nodes"] if n["id"] == "node-book-phone")
    print(f"PUBLISHED -> agent v{pub} (flow v{fv}) is what callers now get")
    print(f"  tools: {urls}")
    print(f"  phone node carries the fix: "
          f"{'yes' if 'as a word' in served_node['instruction']['text'] else 'NO'}")
    if urls != ["https://automation.aiemply.com/webhook/retell-wix"]:
        raise SystemExit("PUBLISHED VERSION IS NOT ON THE PROD BACKEND - fix immediately.")


if __name__ == "__main__":
    main()
