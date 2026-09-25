"""
V63 - reschedule looks the booking up before asking anything; an explicit yes to
cancelling is not asked twice.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v63_resched_lookup_cancel_once.py [--dry-run] [--publish]

Evidence (Ubaid's test line, 2026-09-24, inbound v20):

1. call_d394be70b9b190f7299615b83e3 - reschedule
       Caller: Uh, no, but I want to reschedule my one.
       Aria:   Okay, you want to move your appointment. Let me pull that up.
               What day and time were you looking to move to?
       Caller: So, uh, did you. Find my appointment?        <- only now get_booking
   The node already says "Call get_booking IMMEDIATELY"; the model acknowledged
   first (V59 "show you heard them") and then asked the node's LATER question.
   Prose, because it is the first slip and the identical lookup text in the cancel
   node worked in the same session. If it recurs: move the lookup into a function
   node in front of the subagent.
   The V44 lookup block itself is left byte-for-byte alone - the outbound builder
   string-replaces it (OLD_LOOKUP_STEP) and aborts if it changes.

2. call_9ad002f455238066aae3479e5d4 - cancel
       Aria:   ...Did you want to cancel the Saturday one?
       Caller: Uh, yes.
       Aria:   Okay, just to confirm, you want me to cancel that one?   <- asked twice
   Every path went lookup -> Cancel - Confirm -> Cancel - Submit. Now an explicit
   yes to cancelling a specific booking goes straight to Cancel - Submit; a bare
   "no" to "want me to move it instead?" still gets the one confirm question,
   because "no" alone does not say "cancel".
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

RESCHED, CANCEL, CANCEL_CONFIRM, CANCEL_DO = ("node-resched-assistant", "node-cancel-assistant",
                                              "node-cancel-confirm", "node-cancel-do")

OLD_RESCHED_HEAD = "The caller wants to move an existing appointment.\n\n"
NEW_RESCHED_HEAD = ("The caller wants to move an existing appointment.\n\n"
                    "Your FIRST action here is the get_booking call - before you say anything and before any question. "
                    "Its own wait line covers the pause, so do not acknowledge first and do not ask what time they want; "
                    "the next thing the caller hears from you is their booking.\n\n")
OLD_RESCHED_ORDER = "Once you know which booking, read that one back in ONE line, then ask what day and time they'd like instead."
NEW_RESCHED_ORDER = (OLD_RESCHED_ORDER + " Never ask for the new day or time before you have read their booking back.")

DIRECT_EDGE = {
    "id": "e-cancel-direct",
    "destination_node_id": CANCEL_DO,
    "transition_condition": {"type": "prompt", "prompt": (
        "The caller has just said an explicit yes to CANCELLING one specific booking - \"yes\" to \"do you want to "
        "cancel the Saturday one?\", or \"no, just cancel it\". A bare \"no\" to moving it is NOT this.")},
}
MOVE_Q = "The Signature Massage with Lily, Saturday at six - want me to see if we can move it to another time instead?"
CANCEL_EXAMPLES = [
    {"id": "ft-cancel-yes-to-cancel", "destination_node_id": CANCEL_DO, "transcript": [
        {"role": "agent", "content": "I see two appointments, Thursday at four thirty and Saturday at six. Did you want to cancel the Saturday one?"},
        {"role": "user", "content": "Uh, yes."}]},
    {"id": "ft-cancel-just-cancel", "destination_node_id": CANCEL_DO, "transcript": [
        {"role": "agent", "content": MOVE_Q},
        {"role": "user", "content": "No, just cancel it."}]},
    {"id": "ft-cancel-bare-no", "destination_node_id": CANCEL_CONFIRM, "transcript": [
        {"role": "agent", "content": MOVE_Q},
        {"role": "user", "content": "No."}]},
    {"id": "ft-cancel-which-one", "transcript": [
        {"role": "agent", "content": "I see two appointments, Thursday at four thirty and Saturday at six. Which one did you mean?"},
        {"role": "user", "content": "The Saturday one."}]},
]
OLD_PROCEED = "A booking was found and the caller still wants to cancel it rather than move it."
NEW_PROCEED = (OLD_PROCEED + " Use this when they turned down moving it without saying \"cancel\" in so many words.")


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


# The V44 block the outbound builder rewrites - must survive untouched.
V44_LOOKUP = "Call get_booking IMMEDIATELY on the number they are calling from, {{user_number}}."


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    n = {x["id"]: x for x in flow["nodes"]}

    r = n[RESCHED]["instruction"]
    before_v44 = r["text"].count(V44_LOOKUP)
    r["text"] = once(r["text"], OLD_RESCHED_HEAD, NEW_RESCHED_HEAD, RESCHED)
    r["text"] = once(r["text"], OLD_RESCHED_ORDER, NEW_RESCHED_ORDER, RESCHED)
    if before_v44 != 1 or r["text"].count(V44_LOOKUP) != 1:
        raise SystemExit("the V44 lookup block moved - the outbound builder depends on it")

    c = n[CANCEL]
    ids = [e["id"] for e in c["edges"]]
    if ids != ["e-cancel-proceed", "e-cancel-resched", "e-cancel-keep"]:
        raise SystemExit(f"cancel edges changed shape: {ids}")
    proceed = c["edges"][0]["transition_condition"]
    if proceed.get("prompt") != OLD_PROCEED:
        raise SystemExit("e-cancel-proceed wording changed")
    proceed["prompt"] = NEW_PROCEED
    c["edges"] = [DIRECT_EDGE] + c["edges"]
    if c.get("finetune_transition_examples"):
        raise SystemExit("cancel lookup already has examples - merge by hand")
    c["finetune_transition_examples"] = CANCEL_EXAMPLES

    # guards
    if n[CANCEL_DO]["type"] != "function" or (n[CANCEL_DO].get("instruction") or {}).get("text") != "Cancelling that now.":
        raise SystemExit("cancel submit node is not the pinned function node")
    for ex in CANCEL_EXAMPLES:
        if ex.get("destination_node_id") and ex["destination_node_id"] not in n:
            raise SystemExit(f"example {ex['id']} points nowhere")
    if "to that time with that therapist" not in n["node-book-discovery"]["instruction"]["text"]:
        raise SystemExit("V62 gone")
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
    print(f"draft flow v{live['version']}: reschedule looks up first; explicit cancel goes straight through")
    if args.dry_run:
        print("Dry run - Retell not modified.")
        return
    body = {k: v for k, v in patched.items()
            if k not in ("conversation_flow_id", "version", "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    on = {x["id"]: x for x in out["nodes"]}
    assert NEW_RESCHED_HEAD in on[RESCHED]["instruction"]["text"] and on[CANCEL]["edges"][0]["id"] == "e-cancel-direct"
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
    ok = (NEW_RESCHED_HEAD in pn[RESCHED]["instruction"]["text"] and pn[CANCEL]["edges"][0]["id"] == "e-cancel-direct"
          and len(pn[CANCEL].get("finetune_transition_examples", [])) == 4
          and sorted({t["url"] for t in pf["tools"]}) == [PROD_URL])
    print(f"PUBLISHED inbound agent v{pub} -> flow v{pf['version']}; V63 + prod tools verified={ok}")
    if not ok:
        raise SystemExit("published version is not what was intended")


if __name__ == "__main__":
    main()
