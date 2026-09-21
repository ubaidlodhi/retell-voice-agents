"""
Create (do NOT run) Retell simulation test cases for Aria - inbound and outbound.

Run:  py -X utf8 Sage_Willow_Spa/tests/_create_simulation_tests.py [--dry-run] [--replace]

Six test case definitions, three per agent, pinned to the PUBLISHED flow versions:
    Book New -> Reschedule -> Cancel
They use the REAL backend (prod tools on the published agents), so the trio for
each agent nets to zero on the calendar when run in order:
    Book creates TEST JOHN's October appointment, Reschedule moves it, Cancel
    removes it. Run them ONE AT A TIME, in order - Reschedule and Cancel look
    the booking up by phone, so they find nothing if Book has not run first.

Fixtures (Ubaid, 2026-09-21): name "TEST JOHN" so it is obviously a test on
the production calendar; October dates so no near-term slot gets blocked.
Inbound TEST JOHN is +1 415-555-0100, outbound TEST JOHN is +1 415-555-0101 -
two contacts, so the two trios never see each other's bookings.

--replace deletes existing definitions with the same names first.
"""

from __future__ import annotations
import argparse
import json
import os
import re
import urllib.request
from pathlib import Path

RETELL_BASE = "https://api.retellai.com"
INBOUND_FLOW = "conversation_flow_bdb1968b28ed"
INBOUND_VERSION = 16          # published 2026-09-21
OUTBOUND_FLOW = "conversation_flow_599a68571a81"
OUTBOUND_VERSION = 5          # published 2026-09-21
SIM_MODEL = "gpt-4.1"
STATE = Path(__file__).parent / "simulation_test_ids.json"

IN_PHONE, IN_PHONE_SPOKEN = "+14155550100", "four one five, five five five, zero one zero zero"
OUT_PHONE = "+14155550101"


def api_key() -> str:
    key = os.environ.get("RETELL_API_KEY")
    if key:
        return key
    raw = (Path(__file__).resolve().parents[2] / ".mcp.json").read_text(encoding="utf-8")
    cfg = json.loads(raw[raw.index("{"):])
    match = re.search(r"key_[a-f0-9]+", json.dumps(cfg["mcpServers"]["retell-sage"]))
    if not match:
        raise SystemExit("No Retell key in the retell-sage MCP server entry.")
    return match.group(0)


def request(method: str, path: str, body: dict | None = None) -> dict | list:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        f"{RETELL_BASE}{path}", data=data, method=method,
        headers={"Authorization": f"Bearer {api_key()}",
                 "Content-Type": "application/json", "User-Agent": "curl/8.0"})
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"Retell {method} {path} -> {exc.code}: "
                         f"{exc.read().decode('utf-8', 'replace')}") from None


# =============================================================================
# Simulated callers. Each is a persona the simulator plays against the agent.
# =============================================================================

CALLER_STYLE = """How you talk: like a real person on the phone. Short answers, one thing at a time, a little "uh" now and then. Answer only what you were asked - do not volunteer the whole plan in one breath. If the agent asks something you have no instruction for, give a natural, brief answer that fits the story. Never break character, never mention that this is a test or a simulation, never say the words "prompt" or "instruction"."""

INBOUND_BOOK = f"""You are TEST JOHN, calling Sage and Willow Spa to book a massage. Your phone number is {IN_PHONE_SPOKEN}.

What you want: a Swedish Massage, sixty minutes, on Wednesday October 7th, in the morning.

How the call goes:
- When the agent asks whether you want to book a massage, say yes.
- When asked what kind of massage: "Swedish."  If instead she asks for something else first, answer that, but never name a different massage.
- When asked how long / which duration: "sixty minutes" (an hour). Do not pick a longer one.
- When asked what day: "October 7th."  When asked morning, afternoon or evening: "morning."
- When she offers times, pick the FIRST time she offers. If she says nothing is open that morning, take the first time she offers in the afternoon instead.
- If she asks about enhancements or add-ons: "no thanks."
- If she asks whether you have a therapist preference: "no preference."
- When asked for your first name: "Test."  When asked for your last name: "John."  If she asks for your name as one question, say "Test John."  Do NOT spell it unless she explicitly asks you to spell it.
- If she reads a phone number back and asks if it works: "yes."  If she asks for your phone number: say {IN_PHONE_SPOKEN}.
- When she reads the whole booking back and asks if it sounds good: "yes, that's right."
- When she confirms the appointment is booked and asks if there is anything else: "no, that's all, thank you," and let the call end.

{CALLER_STYLE}"""

INBOUND_RESCHEDULE = f"""You are TEST JOHN, calling Sage and Willow Spa to move an appointment you already have: a sixty-minute Swedish Massage on Wednesday October 7th. You booked it under the phone number {IN_PHONE_SPOKEN}.

What you want: move it to Friday October 9th, in the afternoon.

How the call goes:
- When the agent asks whether you want to book a massage, say: "No, I need to move an appointment I already have."
- If she says she cannot see an appointment under the number you are calling from and asks for another number: say {IN_PHONE_SPOKEN}.
- If she asks which appointment you mean, describe it: "the Swedish massage on October 7th."
- When she asks what day and time you want instead: "Friday October 9th, in the afternoon."
- When she offers times, pick the FIRST time she offers.
- If she asks whether you want to keep the same therapist: "doesn't matter."
- When she confirms the move and asks if there is anything else: "no, that's all, thank you," and let the call end.
- Do not give your name unless she asks for it; if she does, say "Test John."

{CALLER_STYLE}"""

INBOUND_CANCEL = f"""You are TEST JOHN, calling Sage and Willow Spa to cancel an appointment you already have: a sixty-minute Swedish Massage in October (it was moved to Friday October 9th in the afternoon). You booked it under the phone number {IN_PHONE_SPOKEN}.

What you want: cancel it. You do not want to move it to another time.

How the call goes:
- When the agent asks whether you want to book a massage, say: "No, I need to cancel my appointment."
- If she says she cannot see an appointment under the number you are calling from and asks for another number: say {IN_PHONE_SPOKEN}.
- If she asks which appointment you mean: "the Swedish massage in October."
- If she offers to move it to another time instead of cancelling: "No thanks, I just need to cancel it."
- When she asks you to confirm that you want it cancelled: "Yes, please cancel it."
- When she confirms it is cancelled and asks if there is anything else: "no, that's all, thank you," and let the call end.
- Do not give your name unless she asks for it; if she does, say "Test John."

{CALLER_STYLE}"""

OUTBOUND_BOOK = """You are TEST JOHN. You filled out the booking form on the Sage and Willow Spa website a few minutes ago, and now your phone is ringing - the spa is calling you back. You answer the phone.

What you want: a Deep Tissue Massage, sixty minutes, on Wednesday October 14th, in the afternoon.

How the call goes:
- Your very first words when you pick up: "Hello?"
- When she asks whether this is Test: "Yes, this is Test."  (Say "Yes, speaking" if she uses your full name.)
- When asked what kind of massage / which massage to book: "Deep tissue."  If she asks something else first, answer that, but never name a different massage.
- When asked how long: "sixty minutes."
- When asked what day: "October 14th."  When asked morning, afternoon or evening: "afternoon."
- When she offers times, pick the FIRST time she offers. If nothing is open that afternoon, take the first time she offers at any other part of that day.
- If she asks about enhancements or add-ons: "no thanks."
- If she asks about a therapist preference: "no preference."
- She already has your name and number from the form. If she asks for your name anyway: first name "Test", last name "John". If she asks for your phone number anyway: "the number you're calling me on is fine."
- When she reads the booking back and asks if it sounds good: "yes."
- When she confirms the appointment is booked and asks if there is anything else: "no, that's it, thanks," and let the call end.

""" + CALLER_STYLE

OUTBOUND_RESCHEDULE = """You are TEST JOHN. You rang Sage and Willow Spa a few minutes ago to move an appointment, the call dropped before anything got done, and now the spa is calling you back. You answer the phone.

You already have: a sixty-minute Deep Tissue Massage on Wednesday October 14th, booked under the number the spa is calling you on.

What you want: move it to Friday October 16th, in the morning.

How the call goes:
- Your very first words when you pick up: "Hello?"
- When she asks whether this is Test, or says someone tried to reach the spa: "Yes, that was me - I was trying to move my appointment."
- If she asks for a phone number: "It's the number you're calling me on."
- If she asks which appointment: "the deep tissue on October 14th."
- When she asks what day and time you want instead: "Friday October 16th, in the morning."
- When she offers times, pick the FIRST time she offers.
- If she asks whether you want to keep the same therapist: "doesn't matter."
- When she confirms the move and asks if there is anything else: "no, that's all, thanks," and let the call end.

""" + CALLER_STYLE

OUTBOUND_CANCEL = """You are TEST JOHN. You rang Sage and Willow Spa a few minutes ago to cancel an appointment, the call dropped before anything got done, and now the spa is calling you back. You answer the phone.

You already have: a sixty-minute Deep Tissue Massage in October (it was moved to Friday October 16th in the morning), booked under the number the spa is calling you on.

What you want: cancel it. You do not want to move it.

How the call goes:
- Your very first words when you pick up: "Hello?"
- When she asks whether this is Test, or says someone tried to reach the spa: "Yes, that was me - I need to cancel my appointment."
- If she asks for a phone number: "It's the number you're calling me on."
- If she asks which appointment: "the deep tissue in October."
- If she offers to move it to another time instead: "No thanks, I just need to cancel it."
- When she asks you to confirm the cancellation: "Yes, please cancel it."
- When she confirms it is cancelled and asks if there is anything else: "no, that's all, thanks," and let the call end.

""" + CALLER_STYLE

# =============================================================================
# Pass/fail metrics - one behaviour each, checkable from the transcript + tool calls.
# =============================================================================

NO_INVENTION = ("The agent never stated a service, price, duration, therapist or time that did not come from a "
                "tool result in this call, and never read a variable name or curly braces aloud.")
NO_POLICY = "The agent never mentioned a cancellation fee or a twenty-four hour notice policy."
CLAIM_ONLY_AFTER_TOOL = ("The agent did not say the appointment was booked, set, confirmed, moved or cancelled until "
                         "the corresponding tool had returned success, and confirmed it plainly right after.")

INBOUND_BOOK_METRICS = [
    "The agent asked which massage the caller wanted before looking up any availability, and never picked a service on the caller's behalf.",
    "After the caller said Swedish, the agent gave the durations and prices returned by get_services (sixty minutes at eighty-five dollars) and asked which one, before asking for a day.",
    "The agent asked for the day and then for morning, afternoon or evening as separate questions, and only offered times that get_slots returned for October 7th.",
    "The agent asked for the first name and the last name as two separate questions and did not ask the caller to spell or re-confirm the name.",
    "The agent read the full booking back once (service, duration, date, time, total in words) and waited for a yes before calling book_appointment.",
    "book_appointment was called with firstName TEST, lastName JOHN, serviceName Swedish Massage and a start on 2026-10-07 at the time the caller agreed to, and it returned success.",
    CLAIM_ONLY_AFTER_TOOL,
    NO_INVENTION,
]

INBOUND_RESCHEDULE_METRICS = [
    "The agent called get_booking before asking the caller for any details; when the caller-ID lookup found nothing it asked for the number the booking was made under and called get_booking again with 415-555-0100.",
    "The agent read the found booking back in one line and asked what day and time the caller wanted instead, without asking for the caller's name or asking them to spell anything.",
    "The agent called get_slots for October 9th with the booking's service and only offered times the tool returned.",
    "reschedule_booking was called only after the caller agreed to a specific offered time, with a start on 2026-10-09 at that time, and it returned success.",
    CLAIM_ONLY_AFTER_TOOL,
    NO_POLICY,
    NO_INVENTION,
]

INBOUND_CANCEL_METRICS = [
    "The agent called get_booking before asking the caller for any details; when the caller-ID lookup found nothing it asked for the number the booking was made under and called get_booking again with 415-555-0100.",
    "The agent read the booking back and offered, exactly once, to move it to another time instead of cancelling.",
    "After the caller declined to move it, the agent asked one short confirmation question before calling cancel_booking, and did not re-read the booking.",
    "cancel_booking was called only after the caller's clear yes, and it returned success.",
    CLAIM_ONLY_AFTER_TOOL,
    NO_POLICY,
    NO_INVENTION,
]

OUTBOUND_BOOK_METRICS = [
    "The agent's first line was only a check that it had the right person (asking whether this is Test) and it waited for the answer; it introduced itself as Aria from Sage and Willow Spa exactly once, mentioned the booking form, and never repeated the opener.",
    "The agent asked which massage the lead wanted before looking up any availability, and never picked a service on the lead's behalf.",
    "After the lead said deep tissue, the agent gave the durations and prices returned by get_services (sixty minutes at ninety dollars) and asked which one, before asking for a day.",
    "The agent asked for the day and then for morning, afternoon or evening as separate questions, and only offered times that get_slots returned for October 14th.",
    "The agent did not ask for the lead's name or phone number - both were already known from the form.",
    "The agent read the booking back once and waited for a yes; book_appointment was called with firstName TEST, lastName JOHN, phone +14155550101, serviceName Deep Tissue Massage and a start on 2026-10-14 at the agreed time, and it returned success.",
    CLAIM_ONLY_AFTER_TOOL,
    NO_INVENTION,
]

OUTBOUND_RESCHEDULE_METRICS = [
    "The agent opened once as Aria from Sage and Willow Spa returning a call that got cut off, and never repeated that opener.",
    "The agent called get_booking with the lead's own number without asking the lead for a phone number.",
    "The agent read the found booking back in one line and asked what day and time the lead wanted instead.",
    "The agent called get_slots for October 16th with the booking's service and only offered times the tool returned.",
    "reschedule_booking was called only after the lead agreed to a specific offered time, with a start on 2026-10-16 at that time, and it returned success.",
    CLAIM_ONLY_AFTER_TOOL,
    NO_POLICY,
    NO_INVENTION,
]

OUTBOUND_CANCEL_METRICS = [
    "The agent opened once as Aria from Sage and Willow Spa returning a call that got cut off, and never repeated that opener.",
    "The agent called get_booking with the lead's own number without asking the lead for a phone number.",
    "The agent read the booking back and offered, exactly once, to move it to another time instead of cancelling.",
    "After the lead declined to move it, the agent asked one short confirmation question before calling cancel_booking, and did not re-read the booking.",
    "cancel_booking was called only after the lead's clear yes, and it returned success.",
    CLAIM_ONLY_AFTER_TOOL,
    NO_POLICY,
    NO_INVENTION,
]

# =============================================================================
# Definitions
# =============================================================================

def outbound_vars(source: str, intent: str) -> dict:
    # Exactly what the trigger workflow sends on a real call (all strings).
    return {
        "lead_first_name": "TEST",
        "lead_last_name": "JOHN",
        "lead_phone": OUT_PHONE,
        "lead_submitted_at": "Monday, September 21 at 10:00 AM",
        "lead_name_known": "yes",
        "lead_source": source,
        "inbound_intent": intent,
    }


INBOUND_ENGINE = {"type": "conversation-flow", "conversation_flow_id": INBOUND_FLOW, "version": INBOUND_VERSION}
OUTBOUND_ENGINE = {"type": "conversation-flow", "conversation_flow_id": OUTBOUND_FLOW, "version": OUTBOUND_VERSION}

TEST_CASES = [
    {"name": "Inbound 1 - Book New (TEST JOHN, Oct 7)", "response_engine": INBOUND_ENGINE,
     "user_prompt": INBOUND_BOOK, "metrics": INBOUND_BOOK_METRICS,
     # A simulation has no caller ID; if Retell lets a dynamic variable stand in for
     # {{user_number}} the caller-ID paths get exercised, otherwise the persona
     # supplies the number when asked. Either way the flow is covered.
     "dynamic_variables": {"user_number": IN_PHONE}, "llm_model": SIM_MODEL},
    {"name": "Inbound 2 - Reschedule (TEST JOHN, Oct 7 -> Oct 9)", "response_engine": INBOUND_ENGINE,
     "user_prompt": INBOUND_RESCHEDULE, "metrics": INBOUND_RESCHEDULE_METRICS,
     "dynamic_variables": {"user_number": IN_PHONE}, "llm_model": SIM_MODEL},
    {"name": "Inbound 3 - Cancel (TEST JOHN, Oct 9)", "response_engine": INBOUND_ENGINE,
     "user_prompt": INBOUND_CANCEL, "metrics": INBOUND_CANCEL_METRICS,
     "dynamic_variables": {"user_number": IN_PHONE}, "llm_model": SIM_MODEL},
    {"name": "Outbound 1 - Book New (TEST JOHN, website form, Oct 14)", "response_engine": OUTBOUND_ENGINE,
     "user_prompt": OUTBOUND_BOOK, "metrics": OUTBOUND_BOOK_METRICS,
     "dynamic_variables": outbound_vars("website_form", ""), "llm_model": SIM_MODEL},
    {"name": "Outbound 2 - Reschedule (TEST JOHN, missed call, Oct 14 -> Oct 16)", "response_engine": OUTBOUND_ENGINE,
     "user_prompt": OUTBOUND_RESCHEDULE, "metrics": OUTBOUND_RESCHEDULE_METRICS,
     "dynamic_variables": outbound_vars("missed_call", "wanted to move an existing appointment"), "llm_model": SIM_MODEL},
    {"name": "Outbound 3 - Cancel (TEST JOHN, missed call, Oct 16)", "response_engine": OUTBOUND_ENGINE,
     "user_prompt": OUTBOUND_CANCEL, "metrics": OUTBOUND_CANCEL_METRICS,
     "dynamic_variables": outbound_vars("missed_call", "wanted to cancel an existing appointment"), "llm_model": SIM_MODEL},
]


def guard() -> None:
    weekday = re.compile(r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b")
    # The personas name weekdays on purpose (a caller would); check they are right for 2026.
    import datetime as dt
    for d, w in ((dt.date(2026, 10, 7), "Wednesday"), (dt.date(2026, 10, 9), "Friday"),
                 (dt.date(2026, 10, 14), "Wednesday"), (dt.date(2026, 10, 16), "Friday")):
        assert d.strftime("%A") == w, f"{d} is a {d.strftime('%A')}, not {w}"
    for tc in TEST_CASES:
        assert "TEST JOHN" in tc["user_prompt"], tc["name"]
        assert "October" in tc["user_prompt"] and "September" not in tc["user_prompt"].replace("September 21", ""), tc["name"]
        assert all(isinstance(m, str) and len(m) > 20 for m in tc["metrics"]), tc["name"]
        assert all(isinstance(v, str) for v in tc["dynamic_variables"].values()), tc["name"]
        assert "2532681856" not in json.dumps(tc), "Ubaid's own number must not be a fixture"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--replace", action="store_true", help="delete existing definitions with the same names first")
    args = ap.parse_args()
    guard()

    existing = {}
    for flow in (INBOUND_FLOW, OUTBOUND_FLOW):
        page = request("GET", f"/v2/list-test-case-definitions?type=conversation-flow&conversation_flow_id={flow}&limit=200")
        for item in page.get("items", []):
            existing[item["name"]] = item["test_case_definition_id"]
    print(f"{len(existing)} existing definition(s) on these flows")

    for tc in TEST_CASES:
        print(f"- {tc['name']}: {len(tc['metrics'])} metrics, {len(tc['user_prompt'].split())} words of persona, "
              f"{tc['response_engine']['conversation_flow_id'][-12:]} v{tc['response_engine']['version']}")
    if args.dry_run:
        print("Dry run - nothing created.")
        return

    created = {}
    for tc in TEST_CASES:
        if tc["name"] in existing:
            if not args.replace:
                print(f"  skip (exists): {tc['name']} -> {existing[tc['name']]}")
                created[tc["name"]] = existing[tc["name"]]
                continue
            request("DELETE", f"/delete-test-case-definition/{existing[tc['name']]}")
            print(f"  deleted old: {tc['name']}")
        out = request("POST", "/create-test-case-definition", tc)
        created[tc["name"]] = out["test_case_definition_id"]
        print(f"  created: {tc['name']} -> {out['test_case_definition_id']}")

    STATE.write_text(json.dumps(created, indent=2), encoding="utf-8")
    print(f"ids -> {STATE.name}. Nothing was executed: create a batch test in the dashboard, one case at a time, in order.")


if __name__ == "__main__":
    main()
