"""
V66 - fixes from the two-person / couples web tests (2026-09-28). DRAFT ONLY.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v66_test_fixes.py [--dry-run]

No --publish flag on purpose (Ubaid: keep it draft). The draft's tools may be on dev
or prod; they are left where they are.

Tester's findings (Wahaj) and what the calls showed - calls 064644e5, 35e81bfe,
c754d384, f380fe6f on inbound draft v23:
  1. Guest name never asked (all tests). Name -> Phone fired right after the caller's
     own last name; the "ask the guest's too" line inside the name node lost to the
     single-person examples. The tool got "Wife Doe", "Guest Guest", "Guest Doe".
     -> the guest's name is its own step (Booking - Guest Name), reached by its own
        edge; the backend refuses stand-in names ("guest_name_missing") and the
        submit step routes that back to the guest-name step.
  2. Total 215 for Deep Tissue + Swedish, an hour each (right: 175) - twice.
     -> get_slots for two now returns prices.total; the readback reads it.
  3. Challenged on the price, Aria blamed "extras or gratuity" before correcting.
     -> questions node: say you misspoke, never explain a wrong figure away.
  4. "Let me pull that" + "Let me check" back to back: an extra get_services for the
     guest before get_slots. -> not needed any more (prices come with the times).
  5. Enhancements asked twice after "add two people". -> a second person added after
     the enhancements question skips it on the way back.
  6. Couples: no couples room, an unneeded "same one or a different one?", and the
     closing dropped "as a request". -> couples room said up front and in the
     readback, no partner question, closing line reworded around "as a request".
  7. The booking failure itself was a backend race (stale revision on confirm) -
     fixed in n8n (_patch_v66_confirm_retry.py). What it exposed here: after "yes" to
     a callback Aria asked for a time, promised "about an hour", and never sent it.
     -> could-not-complete sends the callback on yes (name already known) and never
        promises a time.
  8. Web calls have no caller ID and Aria read back an invented number
     ("five one five, one five five, five five five five"). -> no caller ID: ask.
"""

from __future__ import annotations
import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _patch_v65_two_guests_request_first as v65  # noqa: E402  (the V65 text this patch replaces)

RETELL_BASE = "https://api.retellai.com"
FLOW_ID = "conversation_flow_bdb1968b28ed"
SNAPSHOT = Path(__file__).parent / "aria_conversation_flow.json"
OK_URLS = {"https://automation.aiemply.com/webhook/retell-wix", "https://automation.aiemply.com/webhook/retell-wix-outbound"}

# ---- 1. the guest's name: its own step -------------------------------------------------------------
GUEST_NODE = {
    "id": "node-book-guest-name",
    "name": "Booking - Guest Name",
    "type": "conversation",
    "skippable": False,
    "instruction": {"type": "prompt", "text": (
        "This booking is for two people at once. You have the caller's name - now get their guest's, the same way.\n\n"
        "Ask: \"And your guest's first name - could you spell that?\" Then WAIT.\n"
        "When they have spelled it: \"And their last name?\" Then WAIT.\n\n"
        "Join the letters into the word (J-A-N-E is Jane). If they say a name instead of spelling it, ask once: "
        "\"Could you spell that for me?\" If they still do not, take it the way it sounds. Do NOT read it back.\n"
        "If they spell both in one breath, take both and skip the second question.\n"
        "Never fill it in yourself - \"Guest\", \"Wife\", \"Partner\" or the caller's own name is not the guest's name.\n"
        "If you are here because the booking came back asking for the guest's name, start with: \"Sorry - I still "
        "need your guest's name.\"")},
    "edges": [
        {"id": "e-guestname-readback", "destination_node_id": "node-book-readback",
         "transition_condition": {"type": "prompt", "prompt": (
             "The guest's first name AND last name have both been given, and the phone number for the booking was "
             "already confirmed earlier in this call.")}},
        {"id": "e-guestname-done", "destination_node_id": "node-book-phone",
         "transition_condition": {"type": "prompt", "prompt": (
             "The guest's first name AND last name have both been given, spelled or said. Never after the first name alone.")}},
    ],
    "finetune_transition_examples": [
        {"id": "ft-guestname-first-only", "transcript": [
            {"role": "agent", "content": "And your guest's first name - could you spell that?"},
            {"role": "user", "content": "J-A-N-E."}]},
        {"id": "ft-guestname-both", "destination_node_id": "node-book-phone", "transcript": [
            {"role": "agent", "content": "And your guest's first name - could you spell that?"},
            {"role": "user", "content": "J-A-N-E."},
            {"role": "agent", "content": "And their last name?"},
            {"role": "user", "content": "R-O-E."}]},
    ],
}
NAME_GUEST_EDGE = {
    "id": "e-name-guest",
    "destination_node_id": "node-book-guest-name",
    "transition_condition": {"type": "prompt", "prompt": (
        "The booking is for two people at once - two appointments side by side, not the Couples Massage - and the "
        "caller has now given their own first AND last name.")},
}
OLD_NAME_DONE_TAIL = (" For two people at once, the guest's first and last name are needed as well - the caller's "
                      "alone is not enough.")
NEW_NAME_DONE_TAIL = (" Only for a booking for one person, or the Couples Massage - for two people at once the "
                      "guest's name comes next, in its own step.")
NAME_ENTRY = ("\nIf you come here straight after the caller agreed a time for two people, open with the time: "
              "\"[Time] it is for both of you. Can you spell your first name for me?\"")
NAME_EXAMPLE = {"id": "ft-name-pair-caller-done", "destination_node_id": "node-book-guest-name",
                "transcript": v65._PAIR_NAME_LEAD}

# ---- 2 + 4 + 5. discovery ----------------------------------------------------------------------------
OLD_DISC_CALL = ("call get_slots with guests 2, and add guestServiceName and guestDurationInMinutes when the guest's "
                 "massage or length is different.")
NEW_DISC_CALL = ("call get_slots with guests 2, and add guestServiceName and guestDurationInMinutes when the guest's "
                 "massage or length is different. Do not call get_services for the guest's massage first - get_slots "
                 "needs only its name, and returns both prices and the total (prices.total).")
SKIP_ADDONS_EDGE = {
    "id": "e-disc-pair-skip-addons",
    "destination_node_id": "node-book-name",
    "transition_condition": {"type": "prompt", "prompt": (
        "The caller has agreed to a specific time for two people at once, AND the enhancements question was already "
        "asked earlier in this call - before the second person was added.")},
}
SLOT_PICKED_ADD = (" Not when a second person was added after the enhancements question had already been asked - "
                   "that goes straight on to the names.")

# ---- 6. couples ---------------------------------------------------------------------------------------
OLD_SL_COUPLES = ("COUPLES MASSAGE: one massage, for the caller only. Mention we have a dedicated couples room. You may "
                  "ask ONCE \"any preference for your partner's massage?\" - whatever they say, acknowledge in three "
                  "words and remember it for the notes.")
NEW_SL_COUPLES = ("COUPLES MASSAGE: one booking, in the caller's name - two people side by side in our couples room. "
                  "The first time it comes up, say so: \"Lovely - we have a dedicated couples room for that.\" Do not "
                  "ask whether the partner wants the same or something different - it is the same for both. If they "
                  "volunteer something about their partner's massage, keep it for the notes.")

# ---- 2 + 6. readback ----------------------------------------------------------------------------------
RB_NEW = ("\n\nFor two people at once, read both in one sentence and name the guest: \"So that's a [Service] for "
          "[Duration] for you and a [Guest's service] for [Guest's duration] for [Guest's first name], side by side on "
          "[Day of the week/Date] at [Time], [Total] dollars - sound good?\" When both are the same: \"two [Service]s "
          "for [Duration] for you and [Guest's first name], side by side on ...\". [Total] is prices.total from the "
          "get_slots result for two, plus any add-ons - never add the massages up yourself. If you do not have the "
          "guest's first and last name yet, do not read back: ask for them first.\n"
          "For the Couples Massage: \"So that's a Couples Massage for [Duration] in our couples room, [Day of the "
          "week/Date] at [Time], [Total] dollars ...\" Its price already covers both people - never double it.\n"
          "If get_services marked the massage \"byRequest\": true, end with: \"... [Total] dollars - that one's by "
          "request, so the team will confirm it with you. Sound good?\"")
OLD_RB_TOTAL = "The total is the price get_services gave for the length they chose"
NEW_RB_TOTAL = "For one person, the total is the price get_services gave for the length they chose"

# ---- 1. submit -> back to the guest's name --------------------------------------------------------------
SUBMIT_GUEST_EDGE = {
    "id": "e-book-submit-guestname",
    "destination_node_id": "node-book-guest-name",
    "transition_condition": {"type": "prompt", "prompt": (
        "The book_appointment tool result contains \"guest_name_missing\" - nothing was booked and the guest's name "
        "is still needed.")},
}

# ---- 6. request closing ---------------------------------------------------------------------------------
OLD_REQ_LINE = ("    \"I've sent that to the team as a request for [Day of the week/Date] at [Time] - they'll confirm it with "
                "you. Anything else I can help with?\"")
NEW_REQ_LINE = ("    \"That's sent to the team as a request for [Day of the week/Date] at [Time] - they'll confirm it "
                "with you. Anything else I can help with?\"\n\n"
                "The words \"as a request\" are the point of the line - never leave them out.")

# ---- 7. could not complete ---------------------------------------------------------------------------------
OLD_FAILED = ("Tell them plainly you're having trouble finalizing it - no jargon, no error codes. Offer to have someone "
              "from the spa call them back. If they say yes, ask for their name.")
NEW_FAILED = ("Tell them plainly you're having trouble finalizing it - no jargon, no error codes - and offer a callback: "
              "\"I'm having trouble finishing that booking. Want me to have the team call you to set it up?\"\n"
              "If they say yes and you already have their name from earlier in the call, that is all you need - the "
              "request goes to the team next; do not ask anything else. Only if you do not have their name, ask for it.\n"
              "Never promise when they will call, and never say it has been passed on before it has.")
OLD_BF_CALLBACK = "The caller wants someone to call them back."
NEW_BF_CALLBACK = ("The caller said yes to a callback, or asked for one, and their name is known - given earlier in "
                   "this call or just now.")

# ---- 3. questions node ----------------------------------------------------------------------------------------
FAQ_ANCHOR = "\n\nKeep it short. Do not re-introduce yourself"
FAQ_ADD = ("\n\nIf a price or total you gave earlier in this call was wrong, say so plainly - \"Sorry, I misspoke - "
           "it's [correct total] dollars.\" - and never explain the difference away with extras, gratuity or anything else.")

# ---- 8. no caller ID ---------------------------------------------------------------------------------------------
PHONE_ANCHOR = "\n\nIf they want a different number, take it."
PHONE_ADD = ("\n\nIf {{user_number}} is empty or shows curly braces - there is no caller ID - do not read anything "
             "back. Ask: \"What's the best number for the booking?\" Never make one up.")

# ---- tools ---------------------------------------------------------------------------------------------------------
GUESTS_DESC_ADD = " It also returns prices for both and their total (prices.total) - quote that total."
GFN_DESC_ADD = " Never a stand-in like 'Guest' or 'Wife' - if you do not have it, ask for it."


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


def once(text: str, old: str, new: str, where: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"{where}: expected one match for {old[:60]!r}, found {text.count(old)}")
    return text.replace(old, new)


def edge(node: dict, eid: str) -> dict:
    hits = [e for e in node["edges"] if e["id"] == eid]
    if len(hits) != 1:
        raise SystemExit(f"{node['id']}: edge {eid} missing")
    return hits[0]


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    n = {x["id"]: x for x in flow["nodes"]}
    if "node-book-guest-name" in n:
        raise SystemExit("V66 already applied")
    if "node-book-requested" not in n:
        raise SystemExit("V65 not in this draft")

    # 1. guest name step
    g = json.loads(json.dumps(GUEST_NODE))
    pos = n["node-book-name"].get("display_position") or {"x": 0, "y": 0}
    g["display_position"] = {"x": pos["x"] + 300, "y": pos["y"] + 420}
    flow["nodes"].append(g)
    nm = n["node-book-name"]
    nm["instruction"]["text"] = once(nm["instruction"]["text"], v65.NAME_TWO, NAME_ENTRY, "name (V65 line)")
    if [e["id"] for e in nm["edges"]] != ["e-name-therapist", "e-name-done"]:
        raise SystemExit("name edges changed shape")
    nm["edges"].insert(1, NAME_GUEST_EDGE)            # the therapist edge stays first (outbound builder checks it)
    nd = edge(nm, "e-name-done")["transition_condition"]
    nd["prompt"] = once(nd["prompt"], OLD_NAME_DONE_TAIL, NEW_NAME_DONE_TAIL, "e-name-done")
    ex = nm["finetune_transition_examples"]
    before = len(ex)
    nm["finetune_transition_examples"] = [e for e in ex if e["id"] not in ("ft-name-pair-caller-only", "ft-name-pair-guest-done")]
    if len(nm["finetune_transition_examples"]) != before - 2:
        raise SystemExit("V65 name examples not found")
    nm["finetune_transition_examples"].append(NAME_EXAMPLE)

    # 2, 4, 5. discovery
    d = n["node-book-discovery"]
    d["instruction"]["text"] = once(d["instruction"]["text"], OLD_DISC_CALL, NEW_DISC_CALL, "discovery")
    sp = edge(d, "e-book-slot-picked")["transition_condition"]
    sp["prompt"] += SLOT_PICKED_ADD
    d["edges"].insert(0, SKIP_ADDONS_EDGE)

    # 6. couples + readback
    s = n["node-book-service"]
    s["instruction"]["text"] = once(s["instruction"]["text"], OLD_SL_COUPLES, NEW_SL_COUPLES, "service couples")
    rb = n["node-book-readback"]
    rb["instruction"]["text"] = once(rb["instruction"]["text"], v65.RB_TWO, RB_NEW, "readback (V65 block)")
    rb["instruction"]["text"] = once(rb["instruction"]["text"], OLD_RB_TOTAL, NEW_RB_TOTAL, "readback total")

    # 1. submit -> guest name
    sb = n["node-book-submit"]
    if [e["id"] for e in sb["edges"]] != ["e-book-submit-requested", "e-book-submit-ok", "e-book-submit-failed"]:
        raise SystemExit("submit edges changed shape")
    sb["edges"].insert(1, SUBMIT_GUEST_EDGE)

    # 6. request closing
    rq = n["node-book-requested"]["instruction"]
    rq["text"] = once(rq["text"], OLD_REQ_LINE, NEW_REQ_LINE, "requested")

    # 7. could not complete
    f = n["node-book-failed"]
    if f["instruction"]["text"] != OLD_FAILED:
        raise SystemExit("could-not-complete text changed - merge by hand")
    f["instruction"]["text"] = NEW_FAILED
    bc = edge(f, "e-bookfail-callback")["transition_condition"]
    if bc["prompt"] != OLD_BF_CALLBACK:
        raise SystemExit("e-bookfail-callback wording changed")
    bc["prompt"] = NEW_BF_CALLBACK

    # 3. questions; 8. phone
    q = n["node-global-faq"]["instruction"]
    q["text"] = once(q["text"], FAQ_ANCHOR, FAQ_ADD + FAQ_ANCHOR, "questions")
    p = n["node-book-phone"]["instruction"]
    p["text"] = once(p["text"], PHONE_ANCHOR, PHONE_ADD + PHONE_ANCHOR, "phone")

    # tools
    t = {x["name"]: x for x in flow["tools"]}
    t["get_slots"]["parameters"]["properties"]["guests"]["description"] += GUESTS_DESC_ADD
    t["book_appointment"]["parameters"]["properties"]["guestFirstName"]["description"] += GFN_DESC_ADD

    # guards
    long = [x["name"] for x in flow["tools"] if len(x.get("description", "")) > 1024]
    if long:
        raise SystemExit(f"tool description over 1024 characters: {long}")
    ids = [x["id"] for x in flow["nodes"]]
    all_edges = [e["id"] for x in flow["nodes"] for e in x.get("edges", [])]
    if len(ids) != len(set(ids)) or len(all_edges) != len(set(all_edges)):
        raise SystemExit("duplicate node or edge id")
    real = set(ids)
    for x in flow["nodes"]:
        for e in x.get("edges", []):
            if e["destination_node_id"] not in real:
                raise SystemExit(f"{e['id']} points nowhere")
        for e2 in x.get("finetune_transition_examples", []):
            if e2.get("destination_node_id") and e2["destination_node_id"] not in real:
                raise SystemExit(f"example {e2['id']} points nowhere")
    if "You are an AI, not a person." not in flow["global_prompt"]:
        raise SystemExit("V64 gone")
    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    urls = {x["url"] for x in live["tools"]}
    if len(urls) != 1 or not urls <= OK_URLS:
        raise SystemExit(f"unexpected tool URLs: {urls}")
    patched = patch(live)
    SNAPSHOT.write_text(json.dumps(patched, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"draft flow v{live['version']}: V66 test fixes ({len(patched['nodes'])} nodes), tools on {urls.pop()}")
    if args.dry_run:
        print("Dry run - Retell not modified.")
        return
    body = {k: v for k, v in patched.items()
            if k not in ("conversation_flow_id", "version", "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    on = {x["id"]: x for x in out["nodes"]}
    assert "node-book-guest-name" in on and on["node-book-name"]["edges"][1]["id"] == "e-name-guest"
    print(f"PATCHED draft flow v{out['version']} - NOT published")


if __name__ == "__main__":
    main()
