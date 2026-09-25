"""
V59 - plainer opening, acknowledge the caller, and never drop a therapist request.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v59_ack_and_therapist.py [--dry-run] [--publish]

DRAFT ONLY by default. --publish also publishes the inbound agent.

1. Opening (Ubaid, 2026-09-25): "Are you looking to book a massage today?"
   -> "Do you want to book a massage?"  (no "today").

2. Acknowledgement (Ubaid: "don't be robotic, acknowledge what the other person
   is saying"). The global prompt's "How you talk" section BANNED it - "No filler
   acknowledgements" and "Never repeat back what the caller just said" - so a
   new section would only contradict an old one. Those two bullets are rewritten
   in place: respond to what they said, deal with an added request first, still
   no canned filler, still no read-back of names or numbers.

3. Therapist (call_022c1ed4c8c8e86462ae2f31686, 2026-09-24 16:55 PT, v18):
       Aria:   4:30 PM is open. Does that work for you?
       Caller: Uh, yes, with Nikki.
       Aria:   Perfect, 4:30 it is. Want to add any enhancements?
       Caller: No, but we want to make sure it's with Nikki.
       Aria:   Can you spell your first name for me?        (caller hangs up)
   get_slots had said 4:30 = winnie only, 5:00 = winnie + Nicky. "yes, with
   Nikki" fired e-book-slot-picked straight into add-ons, and every node after
   discovery (add-ons, name, readback) has no therapist handling and no tools.
   Fix, only for a caller who NAMES someone (nothing changes otherwise):
     * discovery: a yes that adds an unchecked therapist is not a pick; check
       the slot's availableTherapists, confirm or offer a time they are free.
     * add-ons, name: an edge back to discovery for a named therapist, with
       re-entry lines so nothing already answered is asked again.
     * readback -> amend: a therapist correction is an amendment; amend gains
       get_staff; the readback names a therapist only once they were verified.
   The backend already refuses a booking whose requested therapist is not free
   (slot_therapist_resolver: requested-therapist-not-free), so this is about the
   conversation, not about double-booking.
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

GREET, DISC, ADDONS, NAME = "node-greeting", "node-book-discovery", "node-book-addons", "node-book-name"
PHONE, READBACK, AMEND = "node-book-phone", "node-book-readback", "node-book-amend"


def api_key() -> str:
    key = os.environ.get("RETELL_API_KEY")
    if key:
        return key
    raw = (Path(__file__).resolve().parents[2] / ".mcp.json").read_text(encoding="utf-8")
    cfg = json.loads(raw[raw.index("{"):])
    match = re.search(r"key_[a-f0-9]+", json.dumps(cfg["mcpServers"]["retell-sage"]))
    if not match:
        raise SystemExit("No Retell key found (RETELL_API_KEY or .mcp.json retell-sage).")
    return match.group(0)


def request(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(RETELL_BASE + path, data=data, method=method, headers={
        "Authorization": f"Bearer {api_key()}", "Content-Type": "application/json",
        "User-Agent": "curl/8.0"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            text = resp.read().decode()
            return json.loads(text) if text.strip() else {}
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path} -> {e.code}: {e.read().decode()[:600]}")


# --- 1. opening ---------------------------------------------------------------
GREETING_SWAPS = [
    ('open with exactly: "Hi, this is Aria from Sage and Willow Spa. Are you looking to book a massage today?"',
     'open with exactly: "Hi, this is Aria from Sage and Willow Spa. Do you want to book a massage?"'),
    ('-> "Yep, I can hear you - are you looking to book a massage today?"',
     '-> "Yep, I can hear you - do you want to book a massage?"'),
]

# --- 2. acknowledgement -----------------------------------------------------------
OLD_TALK = """- **One question per turn, and it goes last, alone.** Never bolt a question onto the end of a statement - the caller answers the statement and your question lands on top of them.
- **No filler acknowledgements.** Never say "Thanks for letting me know," "Got it," "Perfect," "Great, thanks," "Just to recap," "Absolutely," "No problem." Just answer.
- **Never repeat back what the caller just said.** They know what they said."""

NEW_TALK = """- **One question per turn, and it goes last.** Keep anything before it to a few words, so the caller is not already answering when your question lands.
- **Show you heard them.** Respond to what the caller just said before you move on - a few words that fit it: "Ninety minutes, sure." / "Tomorrow afternoon, okay." / "Oh, sorry to hear that." If they add a request or ask something - a person, a time, a change - deal with that first; never skip past it to your next question. Vary it, keep it short, and don't parrot their whole answer back.
- **No canned filler.** Stock lines that fit anything say nothing: never "Thanks for letting me know," "Just to recap," "Absolutely," "No problem." Names and numbers are never read back unless a step tells you to."""

# --- 3. therapist -----------------------------------------------------------------
OLD_DISC_STEP2 = "Never copy a staffId off a slot they did not ask about."
NEW_DISC_STEP2 = OLD_DISC_STEP2 + """
   - They can name someone at any point - even in the same breath as a yes to a time ("yes, with [Name]"). Before that time is theirs, check it: each slot get_slots returned lists availableTherapists. If that person is listed for the time, confirm it as a question - "[Time] with [Name] is open - want that?" If not, say so and offer a time from the same result where they ARE listed - "[Name]'s not free at [Time], but they are at [Time] - want that instead?" If no time in the result lists them, call get_staff, then get_slots again with their staffId. Never let a time go ahead with a therapist you have not checked."""

OLD_DISC_REENTRY_ANCHOR = "If the caller changes their mind, switch only to a massage they name themselves - never pick one for them."
NEW_DISC_REENTRY = OLD_DISC_REENTRY_ANCHOR + """

If you are back here because the caller asked for a particular therapist after a time was agreed, do not start over: check that time for that person (step 2) and go from there."""

OLD_SLOT_PICKED = "The caller has agreed to a specific appointment time that get_slots returned."
NEW_SLOT_PICKED = ("The caller has agreed to a specific appointment time that get_slots returned. If they named a "
                   "therapist, that person must already have been confirmed free at that time - a yes that adds a "
                   "therapist you have not checked (\"yes, with [Name]\") is NOT agreement yet.")

OFFER = "Four thirty is open. Does that work for you?"
DISC_EXAMPLES = [
    {"id": "ft-disc-yes-plus-therapist", "transcript": [
        {"role": "agent", "content": OFFER},
        {"role": "user", "content": "Uh, yes, with Lily."}]},
    {"id": "ft-disc-therapist-confirmed", "destination_node_id": ADDONS, "transcript": [
        {"role": "agent", "content": "Four thirty with Lily is open - want that?"},
        {"role": "user", "content": "Yes please."}]},
    {"id": "ft-disc-yes-anyone", "destination_node_id": ADDONS, "transcript": [
        {"role": "agent", "content": OFFER},
        {"role": "user", "content": "Yes, anyone's fine."}]},
]

# A therapist request that shows up after the time was agreed.
THERAPIST_EDGE_PROMPT = ("The caller asks for a specific therapist by name, or insists the appointment be with a "
                         "particular person, and that person has not already been confirmed free at the agreed time. "
                         "Never fires when the caller has not named anyone.")

OLD_ADDONS_DONE = "The add-on question has been settled - they picked one, declined, or there were none to offer."
NEW_ADDONS_DONE = (OLD_ADDONS_DONE[:-1] + " - and they did not ask for a specific therapist in the same answer.")
ADDONS_TAIL = """

If they asked for a therapist, say the name with the time: "[Time] with [Name] it is - would you like to add any enhancements?"
If you are back here after the time or therapist was re-checked and they already answered the enhancements question, do not ask it fresh - confirm and check their answer still stands, as one question: "[Time] with [Name] it is - and still no enhancements?\""""
ADDONS_Q = "Four thirty it is - would you like to add any enhancements?"
ADDONS_EXAMPLES = [
    {"id": "ft-addons-therapist", "destination_node_id": DISC, "transcript": [
        {"role": "agent", "content": ADDONS_Q},
        {"role": "user", "content": "No, but we want to make sure it's with Lily."}]},
    {"id": "ft-addons-declined", "destination_node_id": NAME, "transcript": [
        {"role": "agent", "content": ADDONS_Q},
        {"role": "user", "content": "No thanks."}]},
    {"id": "ft-addons-asks-what", "transcript": [
        {"role": "agent", "content": ADDONS_Q},
        {"role": "user", "content": "What are those?"}]},
]

OLD_NAME_DONE = ("The caller has given BOTH a first name and a last name, spelled or said. "
                 "Never after the first name alone.")
NEW_NAME_DONE = OLD_NAME_DONE + " Names they gave earlier in the call count."
NAME_TAIL = """
If you come back here after a therapist check, ask only for a name you do not have yet. If you already have both: "I've still got your name from before - all good to carry on?\""""
NAME_EXAMPLE = {"id": "ft-name-therapist", "destination_node_id": DISC, "transcript": [
    {"role": "agent", "content": "Can you spell your first name for me?"},
    {"role": "user", "content": "Sure, but first - it has to be with Lily."}]}

OLD_READBACK_THERAPIST = "Name the therapist only if the caller specifically asked for one."
NEW_READBACK_THERAPIST = ("Name the therapist only if the caller specifically asked for one and get_slots "
                          "showed them free at that time.")
OLD_READBACK_FIX = ("The caller asked for something DIFFERENT from what was just read back - a different service, "
                    "a different day, or a different time. They are correcting it, not agreeing to it.")
NEW_READBACK_FIX = ("The caller asked for something DIFFERENT from what was just read back - a different service, "
                    "a different day, a different time, or a specific therapist who was not part of it. They are "
                    "correcting it, not agreeing to it.")
READBACK_LINE = "So that's a Signature Massage for one hour, Thursday October eighth at four thirty, ninety dollars - sound good?"
READBACK_EXAMPLES = [
    {"id": "ft-readback-add-therapist", "destination_node_id": AMEND, "transcript": [
        {"role": "agent", "content": READBACK_LINE},
        {"role": "user", "content": "Yes, but with Lily."}]},
    {"id": "ft-readback-yes-restating", "destination_node_id": "node-book-submit", "transcript": [
        {"role": "agent", "content": READBACK_LINE.replace("at four thirty,", "at five with Lily,")},
        {"role": "user", "content": "Yes, with Lily, perfect."}]},
]

OLD_AMEND = "If it is the service or the length, call get_services and give the new price."
NEW_AMEND = OLD_AMEND + (" If it is a therapist, call get_staff for their staffId, then get_slots for the agreed day "
                         "with that staffId: if they are free at the agreed time, keep it and say so; if not, offer the "
                         "nearest times they are free.")


def replace_once(text: str, old: str, new: str, where: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"{where}: expected exactly one match, found {text.count(old)} for {old[:70]!r}")
    return text.replace(old, new)


def edge(node: dict, edge_id: str) -> dict:
    for e in node.get("edges", []):
        if e["id"] == edge_id:
            return e
    raise SystemExit(f"{node['id']}: edge {edge_id} missing")


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    nodes = {n["id"]: n for n in flow["nodes"]}

    # 1. opening
    g = nodes[GREET]["instruction"]
    for old, new in GREETING_SWAPS:
        g["text"] = replace_once(g["text"], old, new, GREET)

    # 2. acknowledgement - rewrite the bullets that forbade it
    flow["global_prompt"] = replace_once(flow["global_prompt"], OLD_TALK, NEW_TALK, "global_prompt")

    # 3a. discovery
    d = nodes[DISC]
    d["instruction"]["text"] = replace_once(d["instruction"]["text"], OLD_DISC_STEP2, NEW_DISC_STEP2, DISC)
    d["instruction"]["text"] = replace_once(d["instruction"]["text"], OLD_DISC_REENTRY_ANCHOR, NEW_DISC_REENTRY, DISC)
    sp = edge(d, "e-book-slot-picked")["transition_condition"]
    if sp.get("prompt") != OLD_SLOT_PICKED:
        raise SystemExit("e-book-slot-picked changed shape")
    sp["prompt"] = NEW_SLOT_PICKED
    have = {ex["id"] for ex in d.get("finetune_transition_examples", [])}
    if have & {ex["id"] for ex in DISC_EXAMPLES}:
        raise SystemExit("discovery already has V59 examples")
    d["finetune_transition_examples"] = d.get("finetune_transition_examples", []) + DISC_EXAMPLES

    # 3b. add-ons: therapist edge FIRST, then the tightened done-edge
    a = nodes[ADDONS]
    done = edge(a, "e-addons-done")
    if done["transition_condition"].get("prompt") != OLD_ADDONS_DONE or len(a["edges"]) != 1:
        raise SystemExit("add-ons edges changed shape")
    done["transition_condition"]["prompt"] = NEW_ADDONS_DONE
    a["edges"] = [{"id": "e-addons-therapist", "destination_node_id": DISC,
                   "transition_condition": {"type": "prompt", "prompt": THERAPIST_EDGE_PROMPT}}] + a["edges"]
    a["instruction"]["text"] = a["instruction"]["text"].rstrip() + ADDONS_TAIL
    if a.get("finetune_transition_examples"):
        raise SystemExit("add-ons already has examples - merge by hand")
    a["finetune_transition_examples"] = ADDONS_EXAMPLES

    # 3c. name: therapist edge first, names from earlier count, re-entry line
    n = nodes[NAME]
    nd = edge(n, "e-name-done")
    if nd["transition_condition"].get("prompt") != OLD_NAME_DONE or len(n["edges"]) != 1:
        raise SystemExit("name edges changed shape")
    nd["transition_condition"]["prompt"] = NEW_NAME_DONE
    n["edges"] = [{"id": "e-name-therapist", "destination_node_id": DISC,
                   "transition_condition": {"type": "prompt", "prompt": THERAPIST_EDGE_PROMPT}}] + n["edges"]
    n["instruction"]["text"] = n["instruction"]["text"].rstrip() + NAME_TAIL
    n["finetune_transition_examples"] = n.get("finetune_transition_examples", []) + [NAME_EXAMPLE]

    # 3d. readback -> amend for a therapist; readback names only a verified one
    r = nodes[READBACK]
    r["instruction"]["text"] = replace_once(r["instruction"]["text"], OLD_READBACK_THERAPIST, NEW_READBACK_THERAPIST, READBACK)
    fix = edge(r, "e-readback-fix")["transition_condition"]
    if fix.get("prompt") != OLD_READBACK_FIX:
        raise SystemExit("e-readback-fix changed shape")
    fix["prompt"] = NEW_READBACK_FIX
    if r.get("finetune_transition_examples"):
        raise SystemExit("readback already has examples - merge by hand")
    r["finetune_transition_examples"] = READBACK_EXAMPLES

    # 3e. amend handles a therapist, and can look one up
    m = nodes[AMEND]
    m["instruction"]["text"] = replace_once(m["instruction"]["text"], OLD_AMEND, NEW_AMEND, AMEND)
    if "get_staff" not in m["tool_ids"]:
        m["tool_ids"] = m["tool_ids"] + ["get_staff"]

    # ---- guards ----------------------------------------------------------------
    gt = nodes[GREET]["instruction"]["text"]
    if "book a massage today" in gt or gt.count("Do you want to book a massage?") != 1:
        raise SystemExit("opening line not swapped cleanly")
    if "Never repeat back what the caller just said" in flow["global_prompt"] or "No filler acknowledgements" in flow["global_prompt"]:
        raise SystemExit("an old anti-acknowledgement bullet survived")
    if "Tomorrow afternoon works" in flow["global_prompt"]:
        raise SystemExit("acknowledgement example implies availability")
    for nid in (ADDONS, NAME):
        ids = [e["id"] for e in nodes[nid]["edges"]]
        if not ids[0].endswith("-therapist"):
            raise SystemExit(f"{nid}: therapist edge is not first")
    tool_ids = {t["tool_id"] for t in flow["tools"]}
    if not set(m["tool_ids"]) <= tool_ids:
        raise SystemExit("amend references a tool that does not exist")
    all_ids = [x["id"] for nn in flow["nodes"] for x in nn.get("finetune_transition_examples", []) or []]
    if len(all_ids) != len(set(all_ids)):
        raise SystemExit("duplicate transition example id")
    for nn in flow["nodes"]:
        for ex in nn.get("finetune_transition_examples", []) or []:
            if ex.get("destination_node_id") and ex["destination_node_id"] not in nodes:
                raise SystemExit(f"{nn['id']}: example {ex['id']} points nowhere")
    for text_ in (NEW_DISC_STEP2, ADDONS_TAIL, NAME_TAIL, NEW_TALK, NEW_AMEND):
        if re.search(r"[–—]", text_):
            raise SystemExit("long dash in new text")
        if re.search(r"\b(Nicky|winnie|Winnie|Nikki)\b", text_):
            raise SystemExit("a real staff name in node/global text - use [Name]")
    # earlier work that must survive
    if nodes[GREET].get("interruption_sensitivity") != 0 or "plays your own voice back to you" not in flow["global_prompt"]:
        raise SystemExit("V54 echo protection gone")
    if nodes["node-book-service"]["tool_ids"] != ["get_services"]:
        raise SystemExit("V55 service node changed")
    if "Never choose for them" not in nodes[DISC]["instruction"]["text"]:
        raise SystemExit("V57 wording gone")
    if "Can you spell your first name for me?" not in nodes[NAME]["instruction"]["text"]:
        raise SystemExit("V58 spelling wording gone")
    if flow.get("start_speaker") != "user" or flow.get("begin_after_user_silence_ms") != 6000:
        raise SystemExit("start_speaker/user + 6000ms dashboard edit is not intact")
    if sorted({t["url"] for t in flow["tools"]}) != [PROD_URL]:
        raise SystemExit("inbound tools are not all on the PROD backend")
    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true")
    args = ap.parse_args()

    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft flow v{live.get('version')} - {len(live['nodes'])} nodes, global prompt "
          f"{len(live['global_prompt'].split())} words")
    patched = patch(live)
    print(f"  global prompt now {len(patched['global_prompt'].split())} words")
    SNAPSHOT.write_text(json.dumps(patched, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"snapshot -> {SNAPSHOT.name}")
    if args.dry_run:
        print("Dry run - Retell not modified.")
        return

    body = {k: v for k, v in patched.items()
            if k not in ("conversation_flow_id", "version", "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    strip = lambda f: json.dumps({k: f[k] for k in ("nodes", "global_prompt", "tools")}, sort_keys=True)
    if strip(out) != strip(patched):
        raise SystemExit("read-back mismatch after PATCH")
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
    ok = strip(pf) == strip(patched) and sorted({t["url"] for t in pf["tools"]}) == [PROD_URL]
    print(f"PUBLISHED inbound agent v{pub} -> flow v{pf['version']}; content + prod tools verified={ok}")
    if not ok:
        raise SystemExit("published version is not what was intended")


if __name__ == "__main__":
    main()
