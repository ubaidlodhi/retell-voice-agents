"""
V57 - a turn without a question leaves the call hanging: end every slot-offer
turn with one, and let the add-ons node say the time back.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v57_no_stall_on_pick.py [--dry-run] [--publish]

DRAFT ONLY by default.

Evidence: call_d54f8542c39dab22344fefd0506 (outbound draft = V15, Ubaid's
test, 2026-09-20 18:43 PT). Every fact on the call was true - menu, $130 for
ninety minutes, Lily's morning genuinely full, noon/one/two really open,
Monday the 21st, booking confirmed in Wix. But:
    Aria:   ...she's free at noon, one, or two. Do any of those work?
    Caller: Uh, yeah, sure.
    Aria:   Noon it is. Let me get that set up.
    (21.5 s of silence)
    Aria:   Just checking in - did you still want that noon spot...?
"Yeah, sure" names no time, so the hand-off edge ("agreed to a specific
time") did not fire; the node then chose noon FOR the caller and ended its
turn with a statement. Transitions are judged on the caller's turns, so with
no question there was nothing to answer, and the call sat until the 20 s
reminder. V52's "say it back - '[Time] it is.' - then move on" can only ever
produce that stall: when the edge does fire the add-ons node speaks first
(call_5a05aadf: "Uh, yes" -> "Did you want to add any enhancements?"), and
when it does not, "[Time] it is." is a dead end.

Fix:
  * discovery: a bare yes to a list of times is not a pick - ask which one,
    never choose for them; a time they name that is open is offered back as
    a question; every turn here ends with a question; no "setting that up".
    Plus transition examples so "Noon." fires and "Yeah, sure." does not.
  * add-ons: opens with the time they just agreed to - "[Time] it is - would
    you like to add any enhancements?" - so the V52 acknowledgement happens
    where it can actually happen.
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
DISCOVERY = "node-book-discovery"
ADDONS = "node-book-addons"


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


OLD_TAIL = (
    "When the caller has agreed to a specific time, say it back in a few words first - \"[Time] it "
    "is.\" - especially if it was a time you had not offered, so they hear that you have it. Then "
    "move on. Never jump to enhancements or the name without that acknowledgement; a caller who has "
    "to ask \"so is that time confirmed?\" was not told. Do not collect their name or phone here."
)
NEW_TAIL = (
    "Every turn in this step ends with a question until the caller has said yes to ONE specific "
    "time - the hand-off to the next step happens on their answer, so a turn that ends in a "
    "statement leaves the call hanging in silence.\n"
    "- \"Yeah\", \"sure\" or \"okay\" to a list of times is NOT a pick. Ask which one: \"Which one - "
    "noon, one, or two?\" Never choose for them.\n"
    "- A time they name that is open in availabilityByDay: offer it back as a question - \"Two "
    "thirty is open - want that one?\"\n"
    "- Never say you are setting anything up, locking anything in or getting anything booked. "
    "Nothing happens in this step but the lookup. Do not collect their name or phone here."
)

OLD_ADDONS_HEAD = "Ask exactly: \"Would you like to add any enhancements?\" then STOP and wait."
NEW_ADDONS_HEAD = (
    "Open with the time the caller just agreed to, then the question, in one breath - \"[Time] it "
    "is - would you like to add any enhancements?\" - then STOP and wait. That is how they hear "
    "the time is theirs; if they had to ask \"so is that confirmed?\" they were not told."
)

OFFER = "Lily's free at noon, one, or two. Do any of those work?"
TRANSITION_EXAMPLES = [
    {"id": "ft-disc-picked-one", "destination_node_id": ADDONS, "transcript": [
        {"role": "agent", "content": OFFER},
        {"role": "user", "content": "Noon."}]},
    {"id": "ft-disc-yes-to-offer", "destination_node_id": ADDONS, "transcript": [
        {"role": "agent", "content": "Ten o'clock tomorrow morning is open. Want to take that?"},
        {"role": "user", "content": "Uh, yes."}]},
    {"id": "ft-disc-named-open-time", "destination_node_id": ADDONS, "transcript": [
        {"role": "agent", "content": "Two thirty is open - want that one?"},
        {"role": "user", "content": "Yes please."}]},
    # stay: no time was picked
    {"id": "ft-disc-vague-yes", "transcript": [
        {"role": "agent", "content": OFFER},
        {"role": "user", "content": "Uh, yeah, sure."}]},
    {"id": "ft-disc-asks-another-day", "transcript": [
        {"role": "agent", "content": OFFER},
        {"role": "user", "content": "What about tomorrow instead?"}]},
]


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    nodes = {n["id"]: n for n in flow["nodes"]}
    disc, addons = nodes[DISCOVERY], nodes[ADDONS]

    t = disc["instruction"]["text"]
    if t.count(OLD_TAIL) != 1:
        raise SystemExit("discovery hand-off paragraph not found exactly once - changed shape.")
    disc["instruction"]["text"] = t.replace(OLD_TAIL, NEW_TAIL)
    if disc.get("finetune_transition_examples"):
        raise SystemExit("discovery already has transition examples - merge by hand.")
    disc["finetune_transition_examples"] = TRANSITION_EXAMPLES

    a = addons["instruction"]["text"]
    if a.count(OLD_ADDONS_HEAD) != 1:
        raise SystemExit("add-ons opening line not found exactly once - changed shape.")
    addons["instruction"]["text"] = a.replace(OLD_ADDONS_HEAD, NEW_ADDONS_HEAD)

    # guards
    d = disc["instruction"]["text"]
    if "[Time] it is." in d or "Then move on" in d:
        raise SystemExit("old hand-off wording survived in discovery")
    if "Which one - noon, one, or two?" not in d or "Never choose for them" not in d:
        raise SystemExit("new hand-off wording missing")
    if "[Time] it is - would you like to add any enhancements?" not in addons["instruction"]["text"]:
        raise SystemExit("add-ons opening missing")
    slot_edge = next(e for e in disc["edges"] if e["id"] == "e-book-slot-picked")
    if slot_edge["destination_node_id"] != ADDONS:
        raise SystemExit("slot-picked edge no longer points at add-ons")
    for ex in TRANSITION_EXAMPLES:
        if ex.get("destination_node_id") not in (None, ADDONS):
            raise SystemExit("transition example points somewhere odd")
    weekday = re.compile(r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b")
    if weekday.search(NEW_TAIL) or weekday.search(NEW_ADDONS_HEAD):
        raise SystemExit("fabricated weekday in a node prompt")
    # earlier work that must survive
    if nodes["node-book-service"]["tool_ids"] != ["get_services"]:
        raise SystemExit("V55 service node changed")
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
    nodes = {n["id"]: n for n in patched["nodes"]}
    print(f"  discovery: {len(nodes[DISCOVERY]['instruction']['text'].split())} words, "
          f"{len(nodes[DISCOVERY]['finetune_transition_examples'])} transition examples")
    print(f"  add-ons opens with: {nodes[ADDONS]['instruction']['text'][:90]!r}")

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
    if NEW_TAIL not in back[DISCOVERY]["instruction"]["text"] \
            or len(back[DISCOVERY].get("finetune_transition_examples", [])) != len(TRANSITION_EXAMPLES) \
            or NEW_ADDONS_HEAD not in back[ADDONS]["instruction"]["text"]:
        raise SystemExit("read-back mismatch after PATCH")
    print(f"PATCHED draft flow v{out.get('version')} (NOT published)")
    if not args.publish:
        print("  Draft only - real callers still get latest_published.")
        return
    request("POST", f"/publish-agent/{AGENT_ID}")
    print("PUBLISHED")


if __name__ == "__main__":
    main()
