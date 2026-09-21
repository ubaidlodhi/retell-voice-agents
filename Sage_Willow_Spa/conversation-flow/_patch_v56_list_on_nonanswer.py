"""
V56 - a length is not a massage: acknowledge it and READ THE MENU, once, in one turn.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v56_list_on_nonanswer.py [--dry-run] [--publish]

DRAFT ONLY by default.

Evidence: call_b316291d0f4fceea3bb7f4607ab (outbound draft, Ubaid's test right
after V55). The gate held - no invented Swedish - but:
    Aria:   What kind of massage are you looking for? I can go over the options...
    Caller: Um, 90 minutes.
    Aria:   Okay. What kind of massage did you want? I can go over the options...
    Caller: Uh, 90 minutes.
    Aria:   Okay, what kind of massage? I can go over the options if you want.
    Caller: Yeah, I mean 90-minute massage.
    Aria:   Okay. What kind of massage did you want? I can go over the options...
He hung up. V55's rule said "ask again: 'Sure - and which massage did you
want? I can list them.'" and she did exactly that, forever, never calling
get_services because nobody had asked what we offer.

Ubaid: "if someone is saying length it should tell me 'okay sure, a 90
minutes, but which massage option' - then tell the options as well: Swedish,
Deep Tissue...". So: any answer that is not a massage name -> keep the detail,
fetch the catalog, and put the names in front of them in the same turn. The
offer to list is for the first ask only; the same question is never asked
twice without the names.
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
SERVICE_NODE = "node-book-service"


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


OLD_RULE = (
    "THE RULE OF THIS STEP: the caller names the massage - you never do. A length (\"ninety "
    "minutes\"), a time (\"ten AM\"), a day, a therapist's name or \"whatever you recommend\" is NOT "
    "a massage. If that is what you get, keep the detail for later and ask again: \"Sure - and which "
    "massage did you want? I can list them.\" There is no default massage - not Swedish, not anything "
    "- and nothing moves forward until they have said one from the menu. Booking a massage the "
    "caller never chose is the one mistake the readback cannot reliably catch."
)
NEW_RULE = (
    "THE RULE OF THIS STEP: the caller names the massage - you never do. A length (\"ninety "
    "minutes\"), a time (\"ten AM\"), a day, a therapist's name or \"whatever you recommend\" is NOT "
    "a massage. When that is what you get, do NOT simply ask again. Keep the detail, call "
    "get_services with no serviceName, and put the menu in front of them in that same turn: "
    "\"Sure, ninety minutes. Which massage did you want? We have [every name it returned].\" "
    "The offer to go over the options is for your first ask only - the same question is never "
    "asked twice without the names. There is no default massage - not Swedish, not anything - and "
    "nothing moves forward until they have picked one from the menu. Booking a massage the caller "
    "never chose is the one mistake the readback cannot reliably catch."
)

OLD_LIST_LINE = (
    "   If they ask what you offer, or you need to list anything: call get_services with NO "
    "serviceName - that returns the menu - then say the names it returned in ONE short sentence, "
    "all of them, exactly as named."
)
NEW_LIST_LINE = (
    "   If they ask what you offer, are unsure, or answered with anything other than a massage "
    "name: call get_services with NO serviceName - that returns the menu - then say the names it "
    "returned in ONE short sentence, all of them, exactly as named."
)

# One worked example of the turn, so the shape is unambiguous: keep the
# length, fetch the menu, say the names the tool returned, ask. The names in
# the example are two real services; the rule says to read whatever the tool
# returns today, and the example shows exactly that (they appear in the tool
# result first).
ASK = "What kind of massage are you looking for? I can go over the options if you're not sure."
CONVERSATION_EXAMPLES = [
    {"id": "fc-svc-length-then-menu", "transcript": [
        {"role": "agent", "content": ASK},
        {"role": "user", "content": "Um, ninety minutes."},
        {"role": "tool_call_invocation", "tool_call_id": "ex-1", "name": "get_services", "arguments": "{}"},
        {"role": "tool_call_result", "tool_call_id": "ex-1",
         "content": "{\"success\":true,\"catalog\":true,\"services\":[{\"name\":\"Swedish Massage\"},{\"name\":\"Deep Tissue Massage\"}]}"},
        {"role": "agent", "content": "Sure, ninety minutes. Which massage did you want? We have Swedish and Deep Tissue."},
        {"role": "user", "content": "Deep tissue."},
        {"role": "tool_call_invocation", "tool_call_id": "ex-2", "name": "get_services", "arguments": "{\"serviceName\":\"Deep Tissue Massage\"}"},
    ]},
]


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    nodes = {n["id"]: n for n in flow["nodes"]}
    if SERVICE_NODE not in nodes:
        raise SystemExit("node-book-service missing - apply V55 first.")
    svc = nodes[SERVICE_NODE]
    text = svc["instruction"]["text"]
    for old, new, what in ((OLD_RULE, NEW_RULE, "rule paragraph"), (OLD_LIST_LINE, NEW_LIST_LINE, "list line")):
        if text.count(old) != 1:
            raise SystemExit(f"{what} not found exactly once - service node changed shape.")
        text = text.replace(old, new)
    svc["instruction"]["text"] = text
    svc["finetune_conversation_examples"] = CONVERSATION_EXAMPLES

    # guards
    if "and ask again:" in text or "I can list them" in text:
        raise SystemExit("the loop instruction survived")
    if text.count("We have [every name it returned]") != 1:
        raise SystemExit("listing line missing")
    if re.search(r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b", text):
        raise SystemExit("fabricated weekday in the service node")
    if svc["tool_ids"] != ["get_services"]:
        raise SystemExit("service node tools changed")
    if len(text.split()) > 560:
        raise SystemExit("service instruction is getting long")
    if flow.get("start_speaker") != "user" or flow.get("begin_after_user_silence_ms") != 6000:
        raise SystemExit("Ubaid's start_speaker/user + 6000ms dashboard edit is not intact.")
    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true")
    args = ap.parse_args()

    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft flow v{live.get('version')} - {len(live['nodes'])} nodes")
    patched = patch(live)
    svc = next(n for n in patched["nodes"] if n["id"] == SERVICE_NODE)
    print(f"  service node instruction: {len(svc['instruction']['text'].split())} words")

    SNAPSHOT.write_text(json.dumps(patched, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"snapshot -> {SNAPSHOT.name}")
    if args.dry_run:
        print("Dry run - Retell not modified.")
        return

    body = {k: v for k, v in patched.items()
            if k not in ("conversation_flow_id", "version",
                         "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    back = next(n for n in out["nodes"] if n["id"] == SERVICE_NODE)
    if NEW_RULE not in back["instruction"]["text"] or len(back.get("finetune_conversation_examples", [])) != 1:
        raise SystemExit("read-back mismatch after PATCH")
    print(f"PATCHED draft flow v{out.get('version')} (NOT published)")
    if not args.publish:
        print("  Draft only - real callers still get latest_published.")
        return
    request("POST", f"/publish-agent/{AGENT_ID}")
    print("PUBLISHED")


if __name__ == "__main__":
    main()
