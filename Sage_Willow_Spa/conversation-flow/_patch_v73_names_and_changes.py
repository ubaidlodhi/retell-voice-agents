"""
V73 - spelled names are taken from the letters, and a change in the middle of a booking stays in
the booking. DRAFT ONLY.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v73_names_and_changes.py [--dry-run]

Calls reviewed 2026-10-07:
  * call_c33ad230 (inbound v27): "Qatar, h a t t a r" was booked as "Qatar" - the website form
    she filled in a minute earlier says Hattar. call_d92679fd (outbound v17): "Javette, j a,
    v de Victor, e, d de David" was booked as "Javved". The name step already says "take the
    letters", but book_appointment's own field said "exactly as they gave it", and the word the
    transcript showed beside the letters won.
      -> name step + the four name fields of book_appointment: the spelled letters ARE the name,
         whatever word was heard next to them; "v de Victor" / "v as in Victor" is the letter V.
  * call_d18cc6ab (inbound v27): at the phone step the caller said "Yes. Actually, I'd like to
    change it to an hour." The reschedule global node took it as moving an existing appointment,
    ran get_booking with no phone ({} -> "Error getting booking", the same as call_894e4295 on
    2026-10-02), told her "I'm not seeing that booking", then the booking started over and asked
    her name and number again.
      -> reschedule and cancel global nodes: only an appointment they ALREADY HAVE, never the one
         being put together now (condition + negative examples).
      -> add-ons, name and phone steps get an exit to "Booking - Amend" for a change to the
         booking in progress. Amend changes only that, re-checks the agreed time when the length
         changes, keeps everything already collected, and hands back to the name step if the
         name is still missing - otherwise to the readback.
      -> get_booking: phone is required, so the look-up always carries a number.

No --publish flag on purpose. Tools are left on the URLs they have.
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

# ---- 1. names ----------------------------------------------------------------------------
NAME_ANCHOR = ("Join the letters into the word (K-A-U-L is Kaul, B-O-O-K is Book). Letters may come with pauses, "
               "\"as in\" words, or a repeat - take the letters and ignore the rest.")
NAME_ADD = ("\nThe letters ARE the name. When they say a name and then spell it, keep only the letters - the word you "
            "heard is often a mis-hearing of the name (\"Carter, k a r t e r\" is Karter, never Carter). A letter can "
            "come as a word: \"v as in Victor\", \"v de Victor\", \"d for David\" are just V and D.")
OLD_NAME_BACK = "If you come back here after a therapist check, ask only for a name you do not have yet."
NEW_NAME_BACK = ("If you come back here after a therapist check or a change to the booking, ask only for a name you "
                 "do not have yet.")

SPELLED = ("If they spelled it, it is exactly the letters they spelled, joined into one word - even when the "
           "transcript shows a different word next to the letters (\"Carter, k a r t e r\" -> Karter; \"v as in "
           "Victor\" / \"v de Victor\" is the letter V). Only if they never spelled it, the name as heard.")
NAME_FIELDS = {
    "firstName": f"Caller's first name. {SPELLED} Required - never send an empty string.",
    "lastName": f"Caller's last name. {SPELLED} Required - never send an empty string.",
    "guestFirstName": ("Two people at once only: the guest's first name. " + SPELLED + " With the guest's names the "
                       "backend books both appointments at the same time, each with their own therapist - both or "
                       "neither. Never a stand-in like 'Guest' or 'Wife' - if you do not have it, ask for it."),
    "guestLastName": "Two people at once only: the guest's last name. " + SPELLED,
}

# ---- 2. get_booking always carries a number ------------------------------------------------
GET_BOOKING_PHONE = ("Always send it. The number to look the booking up under: the caller's own number, "
                     "{{user_number}}, unless they gave you a different one to look under.")
GET_BOOKING_DESC = ("Look up the caller's existing booking by phone. Always send phone - {{user_number}} unless they "
                    "gave a different number to look under. Trust the server's dayOfWeek.")

# ---- 3. reschedule / cancel only for an appointment they already have ----------------------
RESCHED_CONDITION = (
    "Caller wants to move, change, or reschedule an appointment they ALREADY HAVE - one booked before this call, or "
    "booked and confirmed earlier in this call. NOT a change to the booking you are putting together right now - a "
    "different length, day, time, massage or therapist while you are still asking about enhancements, taking their "
    "name or number, or reading the booking back. That is part of the current booking, not a reschedule.")
CANCEL_CONDITION = (
    "Caller says they want to cancel an appointment they ALREADY HAVE - one booked before this call, or booked and "
    "confirmed earlier in this call. NOT \"cancel that\" or \"scratch that\" about the booking you are still putting "
    "together - wanting something different there is a change to the current booking.")
ASK_PHONE = "Does that number work for the booking?"
RESCHED_NEGATIVES = [
    {"transcript": [{"role": "agent", "content": ASK_PHONE},
                    {"role": "user", "content": "Yes. Actually, I'd like to change it to an hour. Just one hour."}]},
    {"transcript": [{"role": "agent", "content": "Four thirty it is - would you like to add any enhancements?"},
                    {"role": "user", "content": "No - actually, can we move it to five instead?"}]},
    {"transcript": [{"role": "agent", "content": "Can you spell your first name for me?"},
                    {"role": "user", "content": "Wait, can I change it to Friday?"}]},
]
CANCEL_NEGATIVES = [
    {"transcript": [{"role": "agent", "content": "Thanks. And your last name - could you spell that as well?"},
                    {"role": "user", "content": "Actually cancel that - make it ninety minutes instead."}]},
]

# ---- 4. a change mid-booking goes to Amend --------------------------------------------------
CHANGE_PROMPT = ("The caller wants to change something about the booking being put together right now - a different "
                 "massage, length, day or time. Not a therapist request (that has its own exit), and not their name "
                 "or phone number.")
CHANGE_PROMPT_PHONE = ("The caller wants to change something about the booking being put together right now - a "
                       "different massage, length, day, time or therapist. Not their phone number.")
# node -> (new exit, the exit that must stay first, its condition)
CHANGE_EDGES = {
    "node-book-addons": ("e-addons-change", "e-addons-therapist", CHANGE_PROMPT),
    "node-book-name": ("e-name-change", "e-name-therapist", CHANGE_PROMPT),
    "node-book-phone": ("e-phone-change", None, CHANGE_PROMPT_PHONE),
}
PHONE_DONE_ADD = " They did not ask to change anything about the booking in the same answer."
PHONE_CHANGE_EXAMPLE = {
    "id": "ft-phone-change-length",
    "transcript": [{"role": "agent", "content": ASK_PHONE},
                   {"role": "user", "content": "Yes. Actually, I'd like to change it to an hour."}],
    "destination_node_id": "node-book-amend",
}
PHONE_YES_EXAMPLE = {
    "id": "ft-phone-yes",
    "transcript": [{"role": "agent", "content": ASK_PHONE}, {"role": "user", "content": "Yes, that's fine."}],
    "destination_node_id": "node-book-readback",
}

AMEND_TEXT = """The caller wants to change something about the booking you are putting together - while you were asking about enhancements, taking their name or number, or reading it back.

Keep everything already settled: their name and number if they gave them, and their answer about enhancements. Never ask for any of them again.

Change only the thing they asked about:
- The day or time: call get_slots for the new date and offer what it returns.
- The massage or the length: call get_services with that massage's name and give the new price. Then make sure the agreed time still works for it - call get_slots for the agreed day with the new length and preferredTime set to the agreed time. If requestedTimeAvailable is true, keep the time and say so with the new price, in one line. If not, say so and offer the nearest times it returned.
- A therapist: call get_staff for their staffId, then get_slots for the agreed day with that staffId: if they are free at the agreed time, keep it and say so; if not, offer the nearest times they are free.

For a booking for two people at once, a new time must come from get_slots with guests 2 (plus the guest's massage fields if they differ), so both still have a therapist.

You cannot book. You have no booking tool. Never tell the caller the appointment is booked, set, confirmed or included - once the change is settled, the booking step runs next."""
AMEND_NAME_EDGE = {
    "id": "e-amend-need-name",
    "destination_node_id": "node-book-name",
    "transition_condition": {"type": "prompt", "prompt": (
        "The change is settled and the caller is happy with it, but they have NOT yet given both their first and "
        "last name in this call.")},
}
AMEND_DONE = ("The change is settled and the caller is ready to hear the corrected details - and they have already "
              "given both their first and last name in this call.")


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


def swap(text: str, old: str, new: str, where: str) -> str:
    if new in text:
        return text
    if text.count(old) != 1:
        raise SystemExit(f"{where}: expected one {old[:50]!r} - merge by hand")
    return text.replace(old, new)


def patch(flow: dict) -> tuple[dict, list[str]]:
    flow = json.loads(json.dumps(flow))
    n = {x["id"]: x for x in flow["nodes"]}
    tools = {t["name"]: t for t in flow["tools"]}
    done = []

    # 1. names
    nm = n["node-book-name"]["instruction"]
    new = swap(nm["text"], NAME_ANCHOR, NAME_ANCHOR + NAME_ADD, "name step")
    new = swap(new, OLD_NAME_BACK, NEW_NAME_BACK, "name step")
    if new != nm["text"]:
        nm["text"] = new
        done.append("name step: spelled letters are the name; back after a change asks only what is missing")
    props = tools["book_appointment"]["parameters"]["properties"]
    for field, desc in NAME_FIELDS.items():
        if props[field].get("description") != desc:
            props[field]["description"] = desc
            done.append(f"book_appointment.{field}: spelled letters win")

    # 2. get_booking
    gb = tools["get_booking"]
    if gb["parameters"].get("required") != ["phone"] or gb["parameters"]["properties"]["phone"].get("description") != GET_BOOKING_PHONE:
        gb["parameters"]["properties"]["phone"]["description"] = GET_BOOKING_PHONE
        gb["parameters"]["required"] = ["phone"]
        gb["description"] = GET_BOOKING_DESC
        done.append("get_booking: phone required")

    # 3. global nodes
    for nid, cond, negs in (("node-resched-assistant", RESCHED_CONDITION, RESCHED_NEGATIVES),
                            ("node-cancel-assistant", CANCEL_CONDITION, CANCEL_NEGATIVES)):
        g = n[nid]["global_node_setting"]
        if g.get("condition") != cond:
            g["condition"] = cond
            have = g.setdefault("negative_finetune_examples", [])
            for ex in negs:
                if ex not in have:
                    have.append(json.loads(json.dumps(ex)))
            done.append(f"{nid}: only an appointment they already have (+{len(negs)} negative examples)")

    # 4. change edges -> amend
    for nid, (eid, after, prompt) in CHANGE_EDGES.items():
        edges = n[nid].setdefault("edges", [])
        ids = [e["id"] for e in edges]
        if eid in ids:
            continue
        if after is not None and (not ids or ids[0] != after):
            raise SystemExit(f"{nid}: {after} is not the first exit any more - merge by hand")
        edge = {"id": eid, "destination_node_id": "node-book-amend",
                "transition_condition": {"type": "prompt", "prompt": prompt}}
        edges.insert(1 if after else 0, edge)
        done.append(f"{nid}: exit {eid} -> Booking - Amend")
    ph = n["node-book-phone"]
    pdone = [e for e in ph["edges"] if e["id"] == "e-phone-done"][0]["transition_condition"]
    if PHONE_DONE_ADD not in pdone["prompt"]:
        pdone["prompt"] += PHONE_DONE_ADD
        done.append("phone step: e-phone-done excludes a change in the same answer")
    fte = ph.setdefault("finetune_transition_examples", [])
    for ex in (PHONE_CHANGE_EXAMPLE, PHONE_YES_EXAMPLE):
        if ex["id"] not in [x.get("id") for x in fte]:
            fte.append(json.loads(json.dumps(ex)))
            done.append(f"phone step: example {ex['id']}")

    # 5. amend
    am = n["node-book-amend"]
    if am["instruction"]["text"] != AMEND_TEXT:
        if "The caller wants to change something about the booking they just heard read back." not in am["instruction"]["text"]:
            raise SystemExit("amend instruction is not the one this patch was written against - merge by hand")
        am["instruction"]["text"] = AMEND_TEXT
        done.append("amend: any step of the booking; re-checks the time when the length changes")
    aids = [e["id"] for e in am["edges"]]
    if AMEND_NAME_EDGE["id"] not in aids:
        am["edges"].insert(aids.index("e-amend-done"), json.loads(json.dumps(AMEND_NAME_EDGE)))
        done.append("amend: back to the name step when the name is still missing")
    adone = [e for e in am["edges"] if e["id"] == "e-amend-done"][0]["transition_condition"]
    if adone["prompt"] != AMEND_DONE:
        adone["prompt"] = AMEND_DONE
        done.append("amend: readback only once the name is in")

    # example ids stay unique flow-wide
    ids = [ex.get("id") for x in flow["nodes"] for k in ("finetune_transition_examples", "finetune_conversation_examples")
           for ex in (x.get(k) or []) if ex.get("id")]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        raise SystemExit(f"duplicate example ids: {dup}")
    return flow, done


def verify(out: dict) -> None:
    on = {x["id"]: x for x in out["nodes"]}
    t = {x["name"]: x for x in out["tools"]}
    assert NAME_ADD.strip() in on["node-book-name"]["instruction"]["text"]
    assert t["get_booking"]["parameters"]["required"] == ["phone"]
    assert all(t["book_appointment"]["parameters"]["properties"][f]["description"] == d for f, d in NAME_FIELDS.items())
    assert on["node-resched-assistant"]["global_node_setting"]["condition"] == RESCHED_CONDITION
    assert on["node-cancel-assistant"]["global_node_setting"]["condition"] == CANCEL_CONDITION
    for nid, (eid, after, _) in CHANGE_EDGES.items():
        ids = [e["id"] for e in on[nid]["edges"]]
        assert eid in ids and (after is None or ids[0] == after), nid
    aids = [e["id"] for e in on["node-book-amend"]["edges"]]
    assert aids.index("e-amend-need-name") < aids.index("e-amend-done")
    assert not out.get("is_published")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    if live.get("is_published"):
        raise SystemExit(f"latest flow v{live['version']} is PUBLISHED - make a draft first, never patch the live one")
    patched, done = patch(live)
    print(f"draft flow v{live['version']}:")
    for x in done or ["nothing to do"]:
        print("  " + x)
    if args.dry_run or not done:
        print("Dry run - Retell not modified." if args.dry_run else "Already up to date.")
        return
    body = {k: v for k, v in patched.items()
            if k not in ("conversation_flow_id", "version", "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    verify(out)
    print(f"PATCHED draft flow v{out['version']} - NOT published")


if __name__ == "__main__":
    main()
