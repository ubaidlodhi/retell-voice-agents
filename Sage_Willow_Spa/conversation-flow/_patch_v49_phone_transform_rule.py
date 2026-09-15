"""
V49 - Ubaid's phone rule, verbatim: show the transformation, not the shape.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v49_phone_transform_rule.py [--dry-run] [--publish]

V48/V48b described the target format abstractly - "[digit] [digit] [digit], ..."
- on the theory that a worked example would get read aloud as a real number.
It did not work. call_1215d55783d79608312e3f34ab1 ran on published v8 with that
rule in place and still produced:

    Agent: "Sure, it's 253-268-1856. What did you need today?"

So the abstract slot was not enough here, and Ubaid supplied the wording he
wants instead:

    Transform input formats (like +14158923245 or (415) 892-3245) into
    spaced-out text. Pronounce it as:
    "four one five - eight nine two - three two four five"

That is an input -> output example, which is a different thing from a bare
shape: it shows the model what to DO with the value it holds, not just what the
answer should look like. Adopted as written, including the hyphen-separated
groups.

The one thing added on top is a line marking those digits as a FORMAT sample and
not a number to say. That is not hedging the instruction - it is the guard the
$499 and "Tuesday at 2 PM" incidents earned, and 415-892-3245 is a plausible
enough number that a caller could not tell it was wrong. The build still fails
on any other literal number anywhere in the flow, Ubaid's own number included.

Note the failing line came from a node other than node-book-phone, so the global
prompt rule is the load-bearing one; both are updated.
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

# The only literal digits allowed to exist in this flow: Ubaid's format sample.
SAMPLE_FORMS = (
    "+14158923245", "(415) 892-3245", "415-892-3245",
    # \b in the scanner starts after the "+", so the bare run has to be listed too.
    "14158923245", "4158923245",
)
FORBIDDEN = ("253", "268", "1856")  # Ubaid's real line must never appear


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

NEW_PHONE_RULE = (
    "- **Phone numbers** - TRANSFORM the input format into spaced-out text before you say "
    "it. Whatever form the number arrives in - +14158923245, (415) 892-3245, 415-892-3245 "
    "- you write and pronounce it as:\n"
    "      \"four one five - eight nine two - three two four five\"\n"
    "  Digit words, one per digit, three groups, hyphens between the groups. NEVER write "
    "the figures. A group written as figures is read aloud as \"four hundred fifteen\", "
    "which is not a phone number, and the caller has to ask you to say it again.\n"
    "  Those digits are a FORMAT example and nothing else - never say that number on a "
    "call. The only number you may say aloud is the live value of {{user_number}} or one "
    "the caller just gave you. If you cannot see real digits, ask."
)

NEW_PHONE_NODE = (
    "Read {{user_number}} back and ask if that number works for the booking.\n\n"
    "Transform it into spaced-out text first. Whatever form it arrives in - +14158923245 "
    "or (415) 892-3245 - you say it as:\n"
    "    \"four one five - eight nine two - three two four five\"\n"
    "Digit words, three groups, hyphens between the groups. Never say the figures.\n\n"
    "That example is a FORMAT, not a number to say. Say only the real digits of "
    "{{user_number}} - never one from these instructions, never one from memory. If they "
    "ask you to repeat it, say the SAME digits again, the same way.\n\n"
    "If they want a different number, take it. We never ask for an email."
)

RULE_START = "- **Phone numbers** -"
RULE_END = "\n- **Durations**"

PHONE_LIKE = re.compile(r"\b\d{3}[-. ]\d{3}[-. ]\d{4}\b|\b\d{7,}\b|\(\d{3}\)\s?\d{3}-\d{4}")


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    nodes = {n["id"]: n for n in flow["nodes"]}

    gp = flow["global_prompt"]
    start = gp.find(RULE_START)
    end = gp.find(RULE_END, start)
    if start < 0 or end < 0:
        raise SystemExit("Could not locate the phone bullet between its neighbours.")
    flow["global_prompt"] = gp[:start] + NEW_PHONE_RULE + gp[end:]

    nodes["node-book-phone"]["instruction"] = {"type": "prompt", "text": NEW_PHONE_NODE}

    # Every literal number in the flow must be part of the sanctioned sample.
    texts = [(flow["global_prompt"], "global_prompt")]
    texts += [((n.get("instruction") or {}).get("text", "") or "", n["id"]) for n in flow["nodes"]]
    texts += [(json.dumps(t, ensure_ascii=False), f"tool:{t['name']}") for t in flow["tools"]]
    for blob, label in texts:
        for hit in PHONE_LIKE.findall(blob):
            if hit.strip() not in SAMPLE_FORMS:
                raise SystemExit(f"{label} carries an unsanctioned literal number: {hit}")
        for piece in FORBIDDEN:
            if re.search(rf"\b{piece}\b", blob):
                raise SystemExit(f"{label} contains a fragment of the real test line: {piece}")

    for blob, label in (("four one five - eight nine two - three two four five", "spoken sample"),
                        ("TRANSFORM the input format", "transform instruction")):
        if blob not in flow["global_prompt"]:
            raise SystemExit(f"global_prompt lost the {label}.")
    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true")
    args = ap.parse_args()

    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft flow v{live.get('version')}")
    patched = patch(live)
    print("  phone rule: input->output transform, hyphenated digit words")
    print("  only literal digits in the flow: the 415 format sample")
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
    ok = "four one five - eight nine two - three two four five" in served["global_prompt"]
    print(f"PUBLISHED -> agent v{pub} (flow v{fv}) is what callers now get")
    print(f"  tools: {urls}")
    print(f"  transform rule live: {'yes' if ok else 'NO'}")
    if urls != ["https://automation.aiemply.com/webhook/retell-wix"]:
        raise SystemExit("PUBLISHED VERSION IS NOT ON THE PROD BACKEND - fix immediately.")


if __name__ == "__main__":
    main()
