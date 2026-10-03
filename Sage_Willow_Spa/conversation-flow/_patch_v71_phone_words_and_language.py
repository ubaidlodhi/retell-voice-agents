"""
V71 - phone number read as single digits every time, and no language switch on a
mis-heard fragment. DRAFT ONLY.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v71_phone_words_and_language.py [--dry-run]

1. Phone number (call_5a700f3f, 2026-10-01): Aria wrote "does 253-268-1856 work?" and the
   voice read the figures as numbers ("eighteen fifty-six"). The phone node already says
   "digit words, never the figures" and usually gets it right - usually is the problem.
   -> a code node in front of the phone step turns {{user_number}} into the words to say
      ("two five three, two six eight, one eight five six") as {{caller_number_spoken}};
      the phone step reads that string back word for word. No figures to mis-read. If the
      code ever fails, the step falls back to today's instructions.
2. Language (call_8c47b948, live, 2026-10-01): the caller said "um", the transcriber wrote
   "嗯", and Aria answered in Chinese; the caller hung up. Ubaid took Chinese off the
   agent's languages; the rule in the prompt only spoke about Spanish single words.
   -> English unless the caller clearly speaks Spanish (a full sentence, or asks for it);
      a fragment, filler or text in any other language is a mis-hearing.

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
PHONE = "node-book-phone"
SAY = "node-book-phone-say"

CODE = """// {{user_number}} as the words to say: "two five three, two six eight, one eight five six".
const d = String(dv.user_number || '').replace(/[^0-9]/g, '');
const ten = (d.length === 11 && d[0] === '1') ? d.slice(1) : d;
if (ten.length !== 10) return { spoken: '' };
const W = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine'];
const say = (s) => s.split('').map((c) => W[Number(c)]).join(' ');
return { spoken: say(ten.slice(0, 3)) + ', ' + say(ten.slice(3, 6)) + ', ' + say(ten.slice(6)) };"""

SAY_NODE = {
    "id": SAY, "type": "code", "name": "Booking - Phone Number Words",
    "code": CODE, "wait_for_result": True, "speak_during_execution": False,
    "response_variables": {"caller_number_spoken": "spoken"},
    "edges": [],
    "else_edge": {"id": "e-phone-say-done", "destination_node_id": PHONE,
                  "transition_condition": {"type": "prompt", "prompt": "Else"}},
}

OLD_HEAD = "Read {{user_number}} back and ask if that number works for the booking.\n\nTransform it into spaced-out text first."
NEW_HEAD = ("Read the caller's number back and ask if that number works for the booking. Say it exactly as "
            "written here, word for word: \"{{caller_number_spoken}}\". Those are already the words to say - "
            "never turn them into figures.\n\nOnly if that is empty or shows curly braces, use {{user_number}}: "
            "transform it into spaced-out text first.")

OLD_LANG = ("Match the caller's primary language. Switch to Spanish only if their first turn or a full sentence "
            "is Spanish. Single words (si, gracias, ok) do NOT trigger a switch.")
NEW_LANG = ("Speak English. Switch to Spanish only when the caller clearly speaks it - a full, sensible sentence "
            "in Spanish, or they ask for Spanish. A single word, a filler sound, a garbled fragment, or text in "
            "any other language (si, ok, gracias, 嗯) is a mis-hearing: stay in English, and if you did not "
            "understand, ask again in English. Never answer in any language other than English or Spanish.")


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

    if SAY not in n:
        pos = n[PHONE].get("display_position", {"x": 0, "y": 0})
        node = json.loads(json.dumps(SAY_NODE))
        node["display_position"] = {"x": pos["x"] - 300, "y": pos["y"] + 260}
        flow["nodes"].append(node)
        moved = 0
        for x in flow["nodes"]:
            if x["id"] == SAY:
                continue
            for e in x.get("edges", []):
                if e["destination_node_id"] == PHONE:
                    e["destination_node_id"] = SAY
                    moved += 1
            for k in ("skip_response_edge", "always_edge", "else_edge"):
                if x.get(k) and x[k]["destination_node_id"] == PHONE:
                    x[k]["destination_node_id"] = SAY
                    moved += 1
            for ex in x.get("finetune_transition_examples", []):
                if ex.get("destination_node_id") == PHONE:
                    ex["destination_node_id"] = SAY
        if moved == 0:
            raise SystemExit("nothing led into the phone step - check by hand")
        done.append(f"code node {SAY} in front of the phone step ({moved} edges moved)")

    ph = n[PHONE]["instruction"]
    if NEW_HEAD not in ph["text"]:
        if ph["text"].count(OLD_HEAD) != 1:
            raise SystemExit("phone step text is not as expected - merge by hand")
        ph["text"] = ph["text"].replace(OLD_HEAD, NEW_HEAD)
        done.append("phone step reads {{caller_number_spoken}} word for word")

    g = flow["global_prompt"]
    if NEW_LANG not in g:
        if g.count(OLD_LANG) != 1:
            raise SystemExit("global prompt: language rule is not as expected - merge by hand")
        flow["global_prompt"] = g.replace(OLD_LANG, NEW_LANG)
        done.append("global prompt: language rule")
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
    assert on[SAY]["type"] == "code" and on[SAY].get("response_variables") == {"caller_number_spoken": "spoken"}, on.get(SAY)
    assert on[SAY]["else_edge"]["destination_node_id"] == PHONE
    assert NEW_LANG in out["global_prompt"] and NEW_HEAD in on[PHONE]["instruction"]["text"]
    assert not any(e["destination_node_id"] == PHONE for x in out["nodes"] if x["id"] != SAY for e in x.get("edges", []))
    assert not out.get("is_published")
    print(f"PATCHED draft flow v{out['version']} - NOT published")


if __name__ == "__main__":
    main()
