"""
V70 - fixes from the 2026-10-01 web tests. DRAFT ONLY.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v70_recording_and_callback.py [--dry-run]

1. Recording (call_4bc3790c): the tester read "This call may be recorded... press 1..."
   and Aria answered it twice with "Sorry, I missed that - what can I help you with?".
   V69 put the recording rule in the global prompt, but the greeting node's own list of
   openers has "You did not catch it, or it was just noise -> 'Sorry, I missed that'",
   and the node wins. -> the greeting's list now names a recording first (stay quiet,
   NO_RESPONSE_NEEDED, a stop sequence Retell honours), plus one worked example.
2. Callback never sent (call_55f2a92d): after a booking the caller asked for a callback
   about the new-client deal. Aria already had the name (from the booking), so never
   asked it; e-message-send waits for "the caller's name ... collected", and the
   caller's "Uh, no. That's all." to "anything else you want them to cover?" fired
   e-message-cancel ("changed their mind") -> Close, no flag_callback. -> the name may
   come from earlier in the call; "no / that's all" to "anything else?" means send;
   two examples on the node.

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

GREET_ANCHOR = "- You did not catch it, or it was just noise -> \"Sorry, I missed that - what can I help you with?\""
GREET_NEW = ("- A recorded or automated message, not a person - \"this call may be recorded,\" \"press 1 for...,\" "
             "\"please stay on the line,\" a voicemail greeting, a recorded pitch -> reply NO_RESPONSE_NEEDED and stay "
             "quiet until it has finished. It is NOT something you missed: never answer it with \"Sorry, I missed "
             "that.\" When a real person speaks, answer them.\n")
GREET_EXAMPLE = {"id": "fc-greet-recording", "transcript": [
    {"role": "agent", "content": "Hi, this is Aria from Sage and Willow Spa. Do you want to book a massage?"},
    {"role": "user", "content": "Thank you for calling. This call may be recorded for quality and training purposes."},
    {"role": "agent", "content": "NO_RESPONSE_NEEDED"},
    {"role": "user", "content": "For sales, press 1. For support, press 2. Please stay on the line."},
    {"role": "agent", "content": "NO_RESPONSE_NEEDED"},
    {"role": "user", "content": "Hi, sorry about that. Do you have anything open tomorrow?"},
    {"role": "agent", "content": "Sure - let's find you a time."},
]}

SEND_PROMPT = ("The caller has said what they want passed on, and their name is known - given in this step or "
               "anywhere earlier in the call (for example while booking). A \"no\" or \"that's all\" in answer to "
               "\"anything else?\" means the message is complete - send it.")
CANCEL_PROMPT = ("The caller says they no longer want a message passed on or a call back at all (\"never mind, "
                 "don't bother\"). NOT a \"no\" or \"that's all\" answering \"anything else?\" - that means the "
                 "message is ready to send.")
MSG_EXAMPLES = [
    {"id": "ft-msg-thats-all-send", "destination_node_id": "node-handoff-callback", "transcript": [
        {"role": "agent", "content": "Okay, I'll have them call you about the new client deal. Anything else you want them to cover?"},
        {"role": "user", "content": "Uh, no. That's all."}]},
    {"id": "ft-msg-never-mind", "destination_node_id": "node-close", "transcript": [
        {"role": "agent", "content": "Sure - what should I pass on to the team?"},
        {"role": "user", "content": "Actually never mind, I'll just call back another time."}]},
]


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


def patch(flow: dict) -> tuple[dict, list[str]]:
    flow = json.loads(json.dumps(flow))
    n = {x["id"]: x for x in flow["nodes"]}
    done = []

    g = n["node-greeting"]
    text = g["instruction"]["text"]
    if GREET_NEW not in text:
        if text.count(GREET_ANCHOR) != 1:
            raise SystemExit("greeting: the 'Sorry, I missed that' line is not where expected - merge by hand")
        g["instruction"]["text"] = text.replace(GREET_ANCHOR, GREET_NEW + GREET_ANCHOR)
        done.append("greeting: recording -> stay quiet, before the 'missed that' line")
    ex = g.setdefault("finetune_conversation_examples", [])
    if not any(e["id"] == GREET_EXAMPLE["id"] for e in ex):
        ex.append(GREET_EXAMPLE)
        done.append("greeting: recording example")

    m = n["node-message-collect"]
    edges = {e["id"]: e for e in m["edges"]}
    if edges["e-message-send"]["destination_node_id"] != "node-handoff-callback" or \
            edges["e-message-cancel"]["destination_node_id"] != "node-close":
        raise SystemExit("message node edges changed - merge by hand")
    for eid, prompt in (("e-message-send", SEND_PROMPT), ("e-message-cancel", CANCEL_PROMPT)):
        if edges[eid]["transition_condition"].get("prompt") != prompt:
            edges[eid]["transition_condition"] = {"type": "prompt", "prompt": prompt}
            done.append(f"message: {eid} reworded")
    tex = m.setdefault("finetune_transition_examples", [])
    for e in MSG_EXAMPLES:
        if not any(x["id"] == e["id"] for x in tex):
            tex.append(e)
            done.append(f"message: example {e['id']}")
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
    for d in done or ["nothing to do"]:
        print("  " + d)
    if args.dry_run or not done:
        print("Dry run - Retell not modified." if args.dry_run else "Already up to date.")
        return
    body = {k: v for k, v in patched.items()
            if k not in ("conversation_flow_id", "version", "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    on = {x["id"]: x for x in out["nodes"]}
    assert GREET_NEW in on["node-greeting"]["instruction"]["text"]
    assert any(e["id"] == GREET_EXAMPLE["id"] for e in on["node-greeting"].get("finetune_conversation_examples", []))
    assert len(on["node-message-collect"].get("finetune_transition_examples", [])) >= 2
    assert not out.get("is_published")
    print(f"PATCHED draft flow v{out['version']} - NOT published")


if __name__ == "__main__":
    main()
