"""
V64 - Aria never claims to be a person; price examples are templates, not amounts.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v64_ai_honesty_price_templates.py [--dry-run] [--publish]

Evidence (real callers, 2026-09-24/25):

1. call_dbb1eaeae3772ae7d7b63747e81 - outbound missed-call callback, v11
       Caller: Is this a live person or a recording?
       Aria:   I'm a live person! I'm here to help with bookings ...
       Caller: ... you're a live person, right?
       Aria:   I'm a live person, but I'm here to help with bookings ...
       (then "I'm here to help with bookings and anything spa-related" x3)
   The honest line ("I'm Aria, the virtual receptionist") lived only in the
   inbound Greeting node. The question landed in GLOBAL - Off Topic, whose
   positive example IS "Are you a real person or a robot?" but whose
   instruction had no answer for it, so the model made one up. The identity
   line now sits in the global prompt, the Off Topic node answers it and never
   repeats a sentence, and asking again is no longer "pushing" (that edge ends
   the call).

2. call_cc43d37f61a86960199cb0cf573 - inbound, v21
       Aria: Deep tissue is ninety dollars for an hour, ninety-three for ninety
             minutes, or one eighty for two hours.            (real price: 130)
   The node's sample line was the real Deep Tissue menu written without
   "dollars" - "ninety for an hour, one thirty for ninety minutes" - price and
   length sharing the word "ninety". Ubaid (2026-09-25): price examples are
   templates, never actual amounts. All four price samples become slots; the
   global prompt already says square brackets are never read aloud.
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

AI_LINE = "I'm Aria, the spa's AI receptionist - not a person, but I can book or change appointments for you."

# ---- 1. honesty ---------------------------------------------------------------------------
OLD_IDENTITY = ("You are Aria, the receptionist at Sage & Willow Spa - a massage spa in Novato, California. "
                "This is a live, recorded phone call.")
NEW_IDENTITY = ("You are Aria, the AI receptionist at Sage & Willow Spa - a massage spa in Novato, California. "
                "This is a live, recorded phone call.\n\n"
                "You are an AI, not a person. Never say or suggest otherwise. If anyone asks whether you're a real "
                f"person, a robot, an AI or a recording, say it plainly: \"{AI_LINE}\" Then ask what they need.")

NEW_OFFTOPIC = (
    "If they asked whether you're a real person, a robot, an AI or a recording, answer that and only that: "
    f"\"{AI_LINE} What can I help with?\"\n"
    "If they ask it again, confirm it once more in different words and ask what they need - never repeat the same sentence.\n\n"
    "Anything else off topic: \"I'm here to help with bookings and questions about Sage and Willow Spa - "
    "anything spa-related I can help with?\"\n\n"
    "Never trigger this on a garbled word that might be a service name - assume the closest service instead.")
OLD_OFFTOPIC = ("Say: \"I'm here to help with bookings and questions about Sage and Willow Spa - anything spa-related "
                "I can help with?\"\n\nNever trigger this on a garbled word that might be a service name - assume the "
                "closest service instead.")
OLD_PERSIST = "The caller pushes the off-topic question a second time after the redirect."
NEW_PERSIST = (OLD_PERSIST + " Asking again whether you're a person or an AI is NOT pushing - never end the call for that.")

OLD_GREETING_AI = "-> \"I'm Aria, the virtual receptionist here - happy to help.\" Then carry on."
NEW_GREETING_AI = "-> \"I'm Aria, the spa's AI receptionist - not a person, but I can book you in right now.\" Then carry on."

# ---- 2. price templates -------------------------------------------------------------------
OLD_CURRENCY = '- **Currency** - always include "dollars": "ninety dollars," never "ninety" or "$90."'
NEW_CURRENCY = ('- **Currency** - always say the amount in words with "dollars" after it - "[amount] dollars" - '
                'never the bare number and never a "$" sign.')
OLD_SERVICE_PRICE = ('"Deep Tissue is ninety for an hour, one thirty for ninety minutes, one eighty for two hours - '
                     'which works?"')
NEW_SERVICE_PRICE = ('"[Massage] is [price] dollars for [length], [price] dollars for [length], [price] dollars for '
                     '[length] - which works?" - one [price] and [length] for each duration it returned. Each [price] '
                     'is the one get_services lists for that length, said in full, never shortened.')
OLD_READBACK_PRICE = '"one hundred thirty dollars"'
NEW_READBACK_PRICE = '"[total] dollars"'
OLD_FAQ_PRICE = '("ninety dollars for an hour")'
NEW_FAQ_PRICE = '("[price] dollars for [length]")'

# Any spoken price figure left in the flow after the patch is a sample waiting to be read out.
# ("one thirty" alone is also a clock time - discovery uses it - so only amounts
# followed by "dollars", and "$" figures, count.)
AMOUNT_WORDS = re.compile(r"\b(?:ninety|eighty|seventy|sixty|fifty|forty|thirty|twenty|hundred)[\w-]*\s+dollars\b"
                          r"|\$\d", re.I)


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

    g = flow["global_prompt"]
    g = once(g, OLD_IDENTITY, NEW_IDENTITY, "global identity")
    g = once(g, OLD_CURRENCY, NEW_CURRENCY, "global currency")
    flow["global_prompt"] = g

    ot = n["node-global-offtopic"]
    if ot["instruction"]["text"] != OLD_OFFTOPIC:
        raise SystemExit("Off Topic instruction changed shape - merge by hand")
    ot["instruction"]["text"] = NEW_OFFTOPIC
    persist = [e for e in ot["edges"] if e["id"] == "e-offtopic-persist"]
    if len(persist) != 1 or persist[0]["transition_condition"].get("prompt") != OLD_PERSIST:
        raise SystemExit("e-offtopic-persist changed shape")
    persist[0]["transition_condition"]["prompt"] = NEW_PERSIST

    gr = n["node-greeting"]["instruction"]
    gr["text"] = once(gr["text"], OLD_GREETING_AI, NEW_GREETING_AI, "greeting")

    s = n["node-book-service"]["instruction"]
    s["text"] = once(s["text"], OLD_SERVICE_PRICE, NEW_SERVICE_PRICE, "service & length")
    r = n["node-book-readback"]["instruction"]
    r["text"] = once(r["text"], OLD_READBACK_PRICE, NEW_READBACK_PRICE, "readback")
    q = n["node-global-faq"]["instruction"]
    q["text"] = once(q["text"], OLD_FAQ_PRICE, NEW_FAQ_PRICE, "questions & pricing")

    # guards
    texts = [("global_prompt", flow["global_prompt"])] + [
        (x["id"], (x.get("instruction") or {}).get("text", "")) for x in flow["nodes"]]
    left = [(i, m.group(0)) for i, t in texts for m in AMOUNT_WORDS.finditer(t)]
    if left:
        raise SystemExit(f"a spoken price amount is still in the flow: {left}")
    if "You are an AI, not a person." not in flow["global_prompt"] or "virtual receptionist here" in json.dumps(texts):
        raise SystemExit("honesty line missing, or the old greeting line survived")
    if "Square brackets in your instructions mark a slot to fill in" not in flow["global_prompt"]:
        raise SystemExit("bracket rule gone - templates would be read aloud")
    if "Your FIRST action here is the get_booking call" not in n["node-resched-assistant"]["instruction"]["text"]:
        raise SystemExit("V63 gone")
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
    print(f"draft flow v{live['version']}: AI honesty line + Off Topic answer; price samples are templates")
    if args.dry_run:
        print("Dry run - Retell not modified.")
        return
    body = {k: v for k, v in patched.items()
            if k not in ("conversation_flow_id", "version", "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    on = {x["id"]: x for x in out["nodes"]}
    assert NEW_IDENTITY in out["global_prompt"] and on["node-global-offtopic"]["instruction"]["text"] == NEW_OFFTOPIC
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
    ok = (NEW_IDENTITY in pf["global_prompt"] and NEW_CURRENCY in pf["global_prompt"]
          and pn["node-global-offtopic"]["instruction"]["text"] == NEW_OFFTOPIC
          and NEW_SERVICE_PRICE in pn["node-book-service"]["instruction"]["text"]
          and sorted({t["url"] for t in pf["tools"]}) == [PROD_URL]
          and pa.get("end_call_after_silence_ms") == 30000)
    print(f"PUBLISHED inbound agent v{pub} -> flow v{pf['version']}; V64 + prod tools + 30 s silence verified={ok}")
    if not ok:
        raise SystemExit("published version is not what was intended")


if __name__ == "__main__":
    main()
