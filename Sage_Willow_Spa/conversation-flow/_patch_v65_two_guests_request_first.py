"""
V65 - two people at once (two appointments, two therapists) and request-first services.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v65_two_guests_request_first.py [--dry-run]

DRAFT ONLY. Ubaid (2026-09-27): "fix this but NOT publish it". There is no
--publish flag on purpose; publishing is a separate, deliberate step.

What Nicky confirmed (2026-09-27, reply "YES"):
  1. Two people at once -> Aria only offers times when two therapists are
     available together and books both guests at the same time, each with their
     own therapist, under the caller's and the guest's names.
  2. Each guest can choose their own massage and length.
  3. Nothing works for two -> no back-to-back; Aria takes a request and the spa
     calls them back.
  4. Services set to "request first" in Wix come to Nicky for approval, and Aria
     tells the caller the team will confirm it.

Evidence: call_cc43d37f61a86960199cb0cf573 (2026-09-25) - "Add 2 people" at the
enhancements question; Aria booked one Deep Tissue at noon on the only therapist
free, with a note, and quoted the price for two.

Backend (n8n, _patch_pair_booking_and_approval.py): get_slots with guests 2
returns only paired times; book_appointment with guest names books both or
neither; request-first services come back "status": "PENDING".
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
SNAPSHOT = Path(__file__).parent / "aria_conversation_flow.json"
PROD_URL = "https://automation.aiemply.com/webhook/retell-wix"

# ---- Service & Length ----------------------------------------------------------------------------
SL_ANCHOR = "\n\nOnce the massage and the length are both settled, ask what day they want to come in"
SL_TWO = ("\n\nTWO PEOPLE AT ONCE: if they want massages for themselves and someone else at the same time - "
          "\"me and my wife\", \"for two of us\" - and did not ask for the Couples Massage by name, that is two "
          "appointments side by side, each with their own therapist. Ask once: \"Same massage and length for both of "
          "you?\" If not, find out the guest's massage and length the same way as the caller's, with its price. Keep "
          "track of who gets which.\n"
          "If you are back here because a second person came up after a time was picked, do not start over: ask only "
          "\"Same massage and length for your guest?\" and settle the guest's.")
OLD_SL_CHOSEN_TAIL = "and the agent naming one on the caller's behalf does not count."
NEW_SL_CHOSEN_TAIL = (OLD_SL_CHOSEN_TAIL + " For two people at once, the guest's massage and length must be settled "
                      "too - \"same for both\" settles it.")

# ---- Discovery -----------------------------------------------------------------------------------
DISC_ANCHOR = "\n\nEvery turn in this step ends with a question until the caller has said yes to ONE specific time"
DISC_TWO = ("\n\nTWO PEOPLE AT ONCE (two appointments side by side - not the Couples Massage): call get_slots with "
            "guests 2, and add guestServiceName and guestDurationInMinutes when the guest's massage or length is "
            "different. Offer only times it returns - each one has two therapists available together. If you are back "
            "here because a second person was added after a time was agreed, check that same time first (preferredTime). "
            "Never offer back-to-back times. If nothing works for them, say: \"I don't have two therapists available "
            "together for that. I can have the team call you to set it up - would that work?\" If yes, ask what name "
            "to give the team if you do not have it yet.")
PAIR_REQUEST_EDGE = {
    "id": "e-disc-pair-request",
    "destination_node_id": "node-handoff-callback",
    "transition_condition": {"type": "prompt", "prompt": (
        "The booking is for two people at once, no time with two therapists available together works for them, and "
        "the caller has said yes to the team calling them back to set it up - and has given their name for it.")},
}
OLD_GIVEUP = "No workable time could be found, or the caller does not want to continue booking."
NEW_GIVEUP = (OLD_GIVEUP + " Not a two-person booking the caller wants the team to call them back about - that has "
              "its own path.")

# ---- Add-ons -------------------------------------------------------------------------------------
ADDONS_ANCHOR = "\n\nIf get_services returned no add-ons for this service"
ADDONS_TWO = ("\n\nFor two people at once, ask once for both: \"[Time] it is for both of you - would either of you like "
              "to add any enhancements?\" Keep track of whose is whose.")
SECOND_GUEST_ADDONS = {
    "id": "e-addons-second-guest",
    "destination_node_id": "node-book-service",
    "transition_condition": {"type": "prompt", "prompt": (
        "The caller wants a second person at the same time - \"add two people\", \"and one for my wife\", \"for both "
        "of us\" - and the booking so far is for one person.")},
}
OLD_ADDONS_DONE = ("The add-on question has been settled - they picked one, declined, or there were none to offer - "
                   "and they did not ask for a specific therapist in the same answer.")
NEW_ADDONS_DONE = (OLD_ADDONS_DONE[:-1] + ", and did not add a second person.")
ADDONS_EXAMPLE = {"id": "ft-addons-second-guest", "destination_node_id": "node-book-service", "transcript": [
    {"role": "agent", "content": "Four thirty it is - would you like to add any enhancements?"},
    {"role": "user", "content": "Add two people."}]}

# ---- Name ----------------------------------------------------------------------------------------
NAME_ANCHOR = "\nIf you come back here after a therapist check"
NAME_TWO = ("\nFor two people at once, once you have the caller's first and last name, ask for the guest's the same "
            "way: \"And your guest's first name - could you spell that?\" then \"And their last name?\" Same rules - no "
            "read-back.")
OLD_NAME_DONE = ("The caller has given BOTH a first name and a last name, spelled or said. Never after the first name "
                 "alone. Names they gave earlier in the call count.")
NEW_NAME_DONE = (OLD_NAME_DONE + " For two people at once, the guest's first and last name are needed as well - the "
                 "caller's alone is not enough.")
_PAIR_NAME_LEAD = [
    {"role": "agent", "content": "Four thirty it is for both of you - would either of you like to add any enhancements?"},
    {"role": "user", "content": "No thanks."},
    {"role": "agent", "content": "Can you spell your first name for me?"},
    {"role": "user", "content": "J-O-H-N."},
    {"role": "agent", "content": "Thanks. And your last name - could you spell that as well?"},
    {"role": "user", "content": "D-O-E."}]
NAME_EXAMPLES = [
    {"id": "ft-name-pair-caller-only", "transcript": _PAIR_NAME_LEAD},
    {"id": "ft-name-pair-guest-done", "destination_node_id": "node-book-phone", "transcript": _PAIR_NAME_LEAD + [
        {"role": "agent", "content": "And your guest's first name - could you spell that?"},
        {"role": "user", "content": "J-A-N-E."},
        {"role": "agent", "content": "And their last name?"},
        {"role": "user", "content": "R-O-E."}]},
]

# ---- Readback ------------------------------------------------------------------------------------
RB_ANCHOR = "\n\nThe total is the price get_services gave for the length they chose"
RB_TWO = ("\n\nFor two people at once, read both in one sentence: \"So that's a [Service] for [Duration] for you and a "
          "[Guest's service] for [Guest's duration] for [Guest's first name], side by side on [Day of the week/Date] at "
          "[Time], [Total] dollars - sound good?\" When both are the same: \"two [Service]s for [Duration], side by side "
          "on ...\". The total is both massages plus any add-ons.\n"
          "If get_services marked the massage \"byRequest\": true, end with: \"... [Total] dollars - that one's by "
          "request, so the team will confirm it with you. Sound good?\"")
SECOND_GUEST_READBACK = {
    "id": "e-readback-second-guest",
    "destination_node_id": "node-book-service",
    "transition_condition": {"type": "prompt", "prompt": (
        "The caller wants to add a second person at the same time, and what was read back was for one person.")},
}

# ---- Amend ---------------------------------------------------------------------------------------
AMEND_ANCHOR = "\n\nYou cannot book. You have no booking tool."
AMEND_TWO = ("\n\nFor a booking for two people at once, a new time must come from get_slots with guests 2 (plus the "
             "guest's massage fields if they differ), so both still have a therapist.")

# ---- Submit -> Requested / Confirmed -------------------------------------------------------------
REQUESTED_EDGE = {
    "id": "e-book-submit-requested",
    "destination_node_id": "node-book-requested",
    "transition_condition": {"type": "prompt", "prompt": (
        "The book_appointment tool result contains \"status\": \"PENDING\" - a request the spa still has to approve.")},
}
OLD_SUBMIT_OK = "The book_appointment tool result contains \"success\": true."
NEW_SUBMIT_OK = ("The book_appointment tool result contains \"success\": true and does NOT say \"status\": "
                 "\"PENDING\".")
REQUESTED_NODE = {
    "id": "node-book-requested",
    "name": "Booking - Requested",
    "type": "conversation",
    "skippable": False,
    "instruction": {"type": "prompt", "text": (
        "The booking was sent as a REQUEST - the spa still has to approve it, so it is NOT confirmed. Say ONE short "
        "line, exactly this shape:\n\n"
        "    \"I've sent that to the team as a request for [Day of the week/Date] at [Time] - they'll confirm it with "
        "you. Anything else I can help with?\"\n\n"
        "Fill both slots from the booking the tool just returned. Never say \"you're all set\", \"booked\" or "
        "\"confirmed\". If they ask when they will hear, say the team will be in touch to confirm it.")},
    "edges": [
        {"id": "e-requested-done", "destination_node_id": "node-close",
         "transition_condition": {"type": "prompt", "prompt": "The caller has nothing else they need."}},
        {"id": "e-requested-more", "destination_node_id": "node-greeting",
         "transition_condition": {"type": "prompt", "prompt": "The caller wants something else - another booking, or a change."}},
    ],
}
CONFIRM_ANCHOR = "\n\nIf the caller asks you to repeat it"
CONFIRM_TWO = ("\n\nFor two people at once: \"You're both all set for [Day of the week/Date] at [Time]. Anything else "
               "I can help with?\"")

# ---- tools ---------------------------------------------------------------------------------------
SLOT_PARAMS = {
    # The guidance lives here, not in the tool description: that is capped at 1024 characters.
    "guests": {"type": "number", "description": (
        "2 when two people want massages at the same time, each with their own therapist (not the Couples Massage). "
        "Omit for one person. Every time then returned - in slots and availabilityByDay - has two different "
        "therapists available together; guestEndDate is when the guest's massage ends. If none come back, never "
        "offer back-to-back times.")},
    "guestServiceName": {"type": "string", "description": (
        "With guests 2, only when the guest's massage is different: the massage the guest chose, by name.")},
    "guestServiceId": {"type": "string", "description": (
        "With guests 2: top-level id from get_services for the guest's massage, when it differs.")},
    "guestDurationInMinutes": {"type": "number", "description": "With guests 2, only when the guest's length is different."},
}
BOOK_PARAMS = {
    "guestFirstName": {"type": "string", "description": (
        "Two people at once only: the guest's first name as spelled on this call. With the guest's names the backend "
        "books both appointments at the same time, each with their own therapist - both or neither.")},
    "guestLastName": {"type": "string", "description": "Two people at once only: the guest's last name as spelled on this call."},
    "guestServiceName": {"type": "string", "description": "Two people at once, only when the guest's massage is different."},
    "guestServiceId": {"type": "string", "description": "Two people at once: top-level id for the guest's massage, when it differs."},
    "guestDurationInMinutes": {"type": "number", "description": "Two people at once, only when the guest's length is different."},
    "guestAddOns": {"type": "array", "description": (
        "Two people at once: add-ons the guest chose, from get_services for the guest's massage. Each needs id and groupId."),
        "items": {"type": "object", "required": ["id", "groupId"],
                  "properties": {"id": {"type": "string"}, "groupId": {"type": "string"}}}},
}
NEW_PARTICIPANTS_DESC = ("2 only for the Couples Massage booked by name. For two people booking two massages, send the "
                         "guest fields instead.")
BOOK_DESC_ADD = (" For two people at once, add guestFirstName and guestLastName (and the guest's massage fields if they "
                 "differ) - one call books both. A result with \"status\": \"PENDING\" is a request the spa still has "
                 "to approve, not a confirmed booking.")
SERVICES_DESC_ADD = (" A service with \"byRequest\": true is booked by request - the spa approves it before it is "
                     "confirmed.")


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


def insert_before(text: str, anchor: str, add: str, where: str) -> str:
    return once(text, anchor, add + anchor, where)


def edge(node: dict, eid: str) -> dict:
    hits = [e for e in node["edges"] if e["id"] == eid]
    if len(hits) != 1:
        raise SystemExit(f"{node['id']}: edge {eid} missing")
    return hits[0]


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    n = {x["id"]: x for x in flow["nodes"]}
    if "node-book-requested" in n:
        raise SystemExit("V65 already applied")

    s = n["node-book-service"]
    s["instruction"]["text"] = insert_before(s["instruction"]["text"], SL_ANCHOR, SL_TWO, "service")
    e = edge(s, "e-service-chosen")["transition_condition"]
    e["prompt"] = once(e["prompt"], OLD_SL_CHOSEN_TAIL, NEW_SL_CHOSEN_TAIL, "e-service-chosen")

    d = n["node-book-discovery"]
    d["instruction"]["text"] = insert_before(d["instruction"]["text"], DISC_ANCHOR, DISC_TWO, "discovery")
    if [x["id"] for x in d["edges"]] != ["e-book-slot-picked", "e-book-giveup"]:
        raise SystemExit("discovery edges changed shape")
    d["edges"].insert(1, PAIR_REQUEST_EDGE)
    g = edge(d, "e-book-giveup")["transition_condition"]
    if g["prompt"] != OLD_GIVEUP:
        raise SystemExit("e-book-giveup wording changed")
    g["prompt"] = NEW_GIVEUP

    a = n["node-book-addons"]
    a["instruction"]["text"] = insert_before(a["instruction"]["text"], ADDONS_ANCHOR, ADDONS_TWO, "add-ons")
    if [x["id"] for x in a["edges"]] != ["e-addons-therapist", "e-addons-done"]:
        raise SystemExit("add-ons edges changed shape")
    a["edges"].insert(1, SECOND_GUEST_ADDONS)   # the therapist edge stays first (outbound builder checks it)
    ad = edge(a, "e-addons-done")["transition_condition"]
    if ad["prompt"] != OLD_ADDONS_DONE:
        raise SystemExit("e-addons-done wording changed")
    ad["prompt"] = NEW_ADDONS_DONE
    a["finetune_transition_examples"].append(ADDONS_EXAMPLE)

    nm = n["node-book-name"]
    nm["instruction"]["text"] = insert_before(nm["instruction"]["text"], NAME_ANCHOR, NAME_TWO, "name")
    nd = edge(nm, "e-name-done")["transition_condition"]
    if nd["prompt"] != OLD_NAME_DONE:
        raise SystemExit("e-name-done wording changed")
    nd["prompt"] = NEW_NAME_DONE
    nm["finetune_transition_examples"] += NAME_EXAMPLES

    rb = n["node-book-readback"]
    rb["instruction"]["text"] = insert_before(rb["instruction"]["text"], RB_ANCHOR, RB_TWO, "readback")
    if [x["id"] for x in rb["edges"]] != ["e-readback-yes", "e-readback-fix"]:
        raise SystemExit("readback edges changed shape")
    rb["edges"].insert(1, SECOND_GUEST_READBACK)

    am = n["node-book-amend"]
    am["instruction"]["text"] = insert_before(am["instruction"]["text"], AMEND_ANCHOR, AMEND_TWO, "amend")

    sb = n["node-book-submit"]
    if [x["id"] for x in sb["edges"]] != ["e-book-submit-ok", "e-book-submit-failed"]:
        raise SystemExit("submit edges changed shape")
    ok = edge(sb, "e-book-submit-ok")["transition_condition"]
    if ok["prompt"] != OLD_SUBMIT_OK:
        raise SystemExit("e-book-submit-ok wording changed")
    ok["prompt"] = NEW_SUBMIT_OK
    sb["edges"].insert(0, REQUESTED_EDGE)

    req = json.loads(json.dumps(REQUESTED_NODE))
    pos = n["node-book-confirm"].get("display_position") or {"x": 0, "y": 0}
    req["display_position"] = {"x": pos["x"], "y": pos["y"] + 420}
    flow["nodes"].append(req)
    c = n["node-book-confirm"]["instruction"]
    c["text"] = insert_before(c["text"], CONFIRM_ANCHOR, CONFIRM_TWO, "confirmed")

    tools = {t["name"]: t for t in flow["tools"]}
    gs = tools["get_slots"]
    if set(SLOT_PARAMS) & set(gs["parameters"]["properties"]):
        raise SystemExit("get_slots already has guest params")
    gs["parameters"]["properties"].update(SLOT_PARAMS)
    bk = tools["book_appointment"]
    if set(BOOK_PARAMS) & set(bk["parameters"]["properties"]):
        raise SystemExit("book_appointment already has guest params")
    bk["parameters"]["properties"].update(BOOK_PARAMS)
    bk["parameters"]["properties"]["numberOfParticipants"]["description"] = NEW_PARTICIPANTS_DESC
    bk["description"] += BOOK_DESC_ADD
    tools["get_services"]["description"] += SERVICES_DESC_ADD

    # guards
    long = [t["name"] for t in flow["tools"] if len(t.get("description", "")) > 1024]
    if long:
        raise SystemExit(f"tool description over Retell's 1024-character cap: {long}")
    ids = [x["id"] for x in flow["nodes"]]
    all_edges = [e["id"] for x in flow["nodes"] for e in x.get("edges", [])]
    if len(ids) != len(set(ids)) or len(all_edges) != len(set(all_edges)):
        raise SystemExit("duplicate node or edge id")
    real = set(ids)
    for x in flow["nodes"]:
        for e in x.get("edges", []):
            if e["destination_node_id"] not in real:
                raise SystemExit(f"{e['id']} points nowhere")
        for ex in x.get("finetune_transition_examples", []):
            if ex.get("destination_node_id") and ex["destination_node_id"] not in real:
                raise SystemExit(f"example {ex['id']} points nowhere")
    if "You are an AI, not a person." not in flow["global_prompt"]:
        raise SystemExit("V64 gone")
    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    if sorted({t["url"] for t in live["tools"]}) != [PROD_URL]:
        raise SystemExit("draft tools are not on PROD - patch first, then switch the draft to dev for testing")
    patched = patch(live)
    SNAPSHOT.write_text(json.dumps(patched, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"draft flow v{live['version']}: two guests + request-first ({len(patched['nodes'])} nodes)")
    if args.dry_run:
        print("Dry run - Retell not modified.")
        return
    body = {k: v for k, v in patched.items()
            if k not in ("conversation_flow_id", "version", "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    on = {x["id"]: x for x in out["nodes"]}
    assert "node-book-requested" in on and on["node-book-submit"]["edges"][0]["id"] == "e-book-submit-requested"
    assert "guests" in {t["name"]: t for t in out["tools"]}["get_slots"]["parameters"]["properties"]
    print(f"PATCHED draft flow v{out['version']} - NOT published")


if __name__ == "__main__":
    main()
