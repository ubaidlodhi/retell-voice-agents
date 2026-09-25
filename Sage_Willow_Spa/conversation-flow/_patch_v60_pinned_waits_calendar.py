"""
V60 - two latent booking bugs found by the V59 mocked simulations, plus a
tighter acknowledgement line. Applied on top of V59, published together with it.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v60_pinned_waits_calendar.py [--dry-run] [--publish]

1. "You're all set" BEFORE the booking came back. The four function nodes that
   speak while their tool runs (book, cancel, reschedule, callback) have
   speak_during_execution: true but no node instruction, so the model improvises
   the wait line - and sometimes improvises a confirmation. Real call
   call_1e5741361f5c5f5b262fad8d3eb (2026-09-20, outbound v5): "You're all set."
   -> book_appointment -> result. Two of three V59 simulations did the same. If
   the tool had failed, the caller would already have been told it was done.
   Fix: pin each node's wait line as static text - the same line its tool
   already declares, so nothing new is said, it is just no longer improvised.

2. Dates past the 14-day calendar refused. The Caller Context says the calendar
   "runs out after fourteen days"; in simulation Aria read that as a booking
   limit ("October eighth isn't in my booking calendar yet") and sent the
   caller away. The paragraph already says to let get_slots find the day; one
   sentence makes explicit that it is not a limit.

3. Acknowledgement wording (V59): "Thanks for letting me know the date and
   time" still came out. The acknowledgement should pick up the detail itself,
   not thank them for it.
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
SPEAKING_FUNCTION_NODES = ("node-book-submit", "node-cancel-do", "node-resched-do", "node-handoff-callback")


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
        raise SystemExit(f"{method} {path} -> {e.code}: {e.read().decode()[:600]}")


OLD_CAL = "and it runs out after fourteen days."
NEW_CAL = ("and it runs out after fourteen days. It is NOT a booking limit - a date past it can still be "
           "booked; look it up like any other.")

OLD_ACK = """- **Show you heard them.** Respond to what the caller just said before you move on - a few words that fit it: "Ninety minutes, sure." / "Tomorrow afternoon, okay." / "Oh, sorry to hear that." """
NEW_ACK = """- **Show you heard them.** Respond to what the caller just said before you move on - a few words that pick up the detail itself, not a thank-you for it: "Ninety minutes, sure." / "Tomorrow afternoon, okay." / "Oh, sorry to hear that." """


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    nodes = {n["id"]: n for n in flow["nodes"]}
    tools = {t["tool_id"]: t for t in flow["tools"]}

    gp = flow["global_prompt"]
    if gp.count(OLD_CAL) != 1:
        raise SystemExit("calendar sentence changed shape")
    if gp.count(OLD_ACK) != 1:
        raise SystemExit("V59 acknowledgement bullet not found - is V59 on the draft?")
    flow["global_prompt"] = gp.replace(OLD_CAL, NEW_CAL).replace(OLD_ACK, NEW_ACK)

    pinned = {}
    for nid in SPEAKING_FUNCTION_NODES:
        n = nodes[nid]
        if n.get("type") != "function" or not n.get("speak_during_execution"):
            raise SystemExit(f"{nid} is not a speaking function node any more")
        if n.get("instruction"):
            raise SystemExit(f"{nid} already has an instruction - merge by hand")
        tool = tools[n["tool_id"]]
        line = tool.get("execution_message_description")
        if tool.get("execution_message_type") != "static_text" or not line:
            raise SystemExit(f"{nid}: its tool has no static wait line to pin")
        if re.search(r"\b(set|booked|done|confirmed|all set)\b", line, re.I) and "now" not in line:
            raise SystemExit(f"{nid}: wait line {line!r} reads like a confirmation")
        n["instruction"] = {"type": "static_text", "text": line}
        pinned[nid] = line

    # guards: V59 still intact
    if "Do you want to book a massage?" not in nodes["node-greeting"]["instruction"]["text"]:
        raise SystemExit("V59 opening gone")
    if [e["id"] for e in nodes["node-book-addons"]["edges"]][0] != "e-addons-therapist":
        raise SystemExit("V59 add-ons therapist edge gone")
    if sorted({t["url"] for t in flow["tools"]}) != [PROD_URL]:
        raise SystemExit("inbound tools are not all on the PROD backend")
    flow["_pinned"] = pinned
    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true")
    args = ap.parse_args()

    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft flow v{live.get('version')}")
    patched = patch(live)
    pinned = patched.pop("_pinned")
    for nid, line in pinned.items():
        print(f"  pinned {nid:24} -> {line!r}")
    SNAPSHOT.write_text(json.dumps(patched, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.dry_run:
        print("Dry run - Retell not modified.")
        return

    body = {k: v for k, v in patched.items()
            if k not in ("conversation_flow_id", "version", "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    back = {n["id"]: n for n in out["nodes"]}
    for nid, line in pinned.items():
        got = back[nid].get("instruction") or {}
        if got.get("type") != "static_text" or got.get("text") != line:
            raise SystemExit(f"{nid}: pinned line did not survive the PATCH (got {got})")
    if NEW_CAL not in out["global_prompt"] or NEW_ACK not in out["global_prompt"]:
        raise SystemExit("global prompt read-back mismatch")
    print(f"PATCHED draft flow v{out.get('version')}")
    if not args.publish:
        print("  Draft only - real callers still get latest_published.")
        return
    request("POST", f"/publish-agent/{AGENT_ID}")
    vs = request("GET", f"/get-agent-versions/{AGENT_ID}")
    vs = vs.get("items", vs) if isinstance(vs, dict) else vs
    pub = max(v["version"] for v in vs if v.get("is_published"))
    pa = request("GET", f"/get-agent/{AGENT_ID}?version={pub}")
    pf = request("GET", f"/get-conversation-flow/{FLOW_ID}?version={pa['response_engine']['version']}")
    pn = {n["id"]: n for n in pf["nodes"]}
    ok = (all((pn[nid].get("instruction") or {}).get("text") == line for nid, line in pinned.items())
          and "Do you want to book a massage?" in pn["node-greeting"]["instruction"]["text"]
          and sorted({t["url"] for t in pf["tools"]}) == [PROD_URL])
    print(f"PUBLISHED inbound agent v{pub} -> flow v{pf['version']}; V59+V60 + prod tools verified={ok}")
    if not ok:
        raise SystemExit("published version is not what was intended")


if __name__ == "__main__":
    main()
