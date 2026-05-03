"""
Build script for the Sage & Willow Spa Retell conversation-flow agent.

Run:  py -X utf8 _build_agent.py

Outputs: sage_willow_inbound_agent.json
"""

from __future__ import annotations
import json
from pathlib import Path

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------

OUT_PATH = Path(__file__).parent / "sage_willow_inbound_agent.json"
PROMPT_PATH = Path(__file__).parent / "system_prompt.md"
N8N_BASE_URL = "https://automation.aiemply.com/webhook/retell-wix"
SPA_FALLBACK_EMAIL = "sagewillowspa@gmail.com"
SPA_PHONE = "+16286828010"
ESCALATION_EMAIL = "sagewillowspa@gmail.com"

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def edge(eid: str, prompt_text: str, dest: str, examples: list | None = None) -> dict:
    e = {
        "id": eid,
        "transition_condition": {"type": "prompt", "prompt": prompt_text},
        "destination_node_id": dest,
    }
    if examples:
        e["finetune_transition_examples"] = examples
    return e


def equation_edge(eid: str, equations: list[dict], dest: str, op: str = "&&") -> dict:
    return {
        "id": eid,
        "transition_condition": {
            "type": "equation",
            "equations": equations,
            "operator": op,
        },
        "destination_node_id": dest,
    }


def always_edge(eid: str, dest: str) -> dict:
    return {
        "id": eid,
        "transition_condition": {"type": "prompt", "prompt": "Always"},
        "destination_node_id": dest,
    }


def skip_edge(eid: str, dest: str) -> dict:
    return {
        "id": eid,
        "transition_condition": {"type": "prompt", "prompt": "Skip response"},
        "destination_node_id": dest,
    }


def else_edge(eid: str, dest: str) -> dict:
    return {
        "id": eid,
        "transition_condition": {"type": "prompt", "prompt": "Else"},
        "destination_node_id": dest,
    }


# -----------------------------------------------------------------------------
# Tools (wire to n8n production v2 webhook)
# -----------------------------------------------------------------------------

def tool(tool_id, header_name, description, parameters, response_variables=None,
         speak=True, exec_msg="Just a moment please, this will only take a second."):
    t = {
        "tool_id": tool_id,
        "name": tool_id,
        "type": "custom",
        "description": description,
        "method": "POST",
        "url": N8N_BASE_URL,
        "headers": {"tool": header_name},
        "query_params": {},
        "timeout_ms": 120000,
        "parameter_type": "form",
        "args_at_root": True,
        "speak_during_execution": speak,
        "parameters": parameters,
    }
    if speak:
        t["execution_message_description"] = exec_msg
    if response_variables:
        t["response_variables"] = response_variables
    return t


TOOLS = [
    tool(
        "get_services",
        "get-services",
        "Fetch the live list of spa services with their pricing variants and "
        "add-ons. Each service may have a single fixed `price` field OR a "
        "`pricingVariants` array (each variant has {id, duration, price} — for "
        "example: 60-min for $90, 90-min for $130, 120-min for $180). When the "
        "service has pricingVariants, you MUST present the duration options to "
        "the caller, get their pick, and pass the chosen variant.id as variantId "
        "to book_appointment. Each service also has availableAddOns with id, "
        "name, price, duration. Takes no arguments.",
        {"type": "object", "properties": {}, "required": []},
    ),
    tool(
        "get_staff",
        "get-staff",
        "Fetch the live list of therapists. Call only when the caller asks about a "
        "specific therapist by name or wants to choose. Takes no arguments.",
        {"type": "object", "properties": {}, "required": []},
    ),
    tool(
        "get_contact",
        "get-contact",
        "Look up an existing customer contact by phone OR email. Use this when "
        "the caller says they're a returning client. Try phone first (default to "
        "{{user_number}}); if not found, ask for the email they booked under and "
        "try again. When found, the response populates contact_first_name, "
        "contact_last_name, contact_email, contact_phone — use these to skip "
        "re-asking those during booking. Set `found: true` when matched.",
        {
            "type": "object",
            "properties": {
                "phone": {"type": "string", "description": "Caller's phone in E.164 — default to {{user_number}}."},
                "email": {"type": "string", "description": "Email used at the spa, if phone lookup didn't match."},
            },
            "required": [],
        },
        response_variables={
            "contact_found":      "$.found",
            "contact_id":         "$.contact.contactId",
            "contact_first_name": "$.contact.firstName",
            "contact_last_name":  "$.contact.lastName",
            "contact_email":      "$.contact.email",
            "contact_phone":      "$.contact.phone",
        },
    ),
    tool(
        "get_slots",
        "get-slots",
        "Fetch available time slots for a service across a date window. Returns slots "
        "grouped by morning/afternoon/evening, each carrying staffId and scheduleId "
        "(needed for booking). Times are Pacific (10 AM – 8 PM). To keep responses "
        "small, ALWAYS narrow by the caller's preferences before calling: pass "
        "`staffId` if they have a preferred therapist, `timeOfDay` if they have a "
        "preferred part of the day, `earliestFirst: true` if they want the soonest "
        "available, and use `limit` to cap how many slots come back.",
        {
            "type": "object",
            "properties": {
                "serviceId": {"type": "string", "description": "Wix service ID from get_services."},
                "startDate": {"type": "string", "description": "ISO local start, e.g. 2026-05-10 or 2026-05-10T00:00:00."},
                "endDate":   {"type": "string", "description": "ISO local end, e.g. 2026-05-12 or 2026-05-12T23:59:59."},
                "staffId":   {"type": "string", "description": "Optional. Wix staff/resource ID from get_staff. If set, only that therapist's slots are returned. Omit for 'no preference'."},
                "timeOfDay": {
                    "type": "string",
                    "enum": ["morning", "afternoon", "evening", "any"],
                    "description": "Optional. Filter to a part of the day. Morning=10AM–12PM, afternoon=12PM–5PM, evening=5PM–8PM. Use 'any' or omit when caller has no preference.",
                },
                "earliestFirst": {
                    "type": "boolean",
                    "description": "Optional. When true, slots are flattened across days, sorted ascending by start time, and capped to `limit`. Use this when the caller says 'earliest available', 'anytime', 'soonest', 'first opening'.",
                },
                "limit": {
                    "type": "number",
                    "description": "Optional. Max slots to return (default 6). Use 3 for 'earliest available' calls, 6–9 for browsing.",
                },
            },
            "required": ["serviceId", "startDate", "endDate"],
        },
    ),
    tool(
        "book_appointment",
        "book-appointment",
        "Create a booking. Requires the slot's serviceId, staffId, scheduleId, "
        "startDate, endDate, the caller's chosen pricing variantId (from "
        "get_services pricingVariants — the duration the caller picked), plus "
        "contact details. Optional addOnIds array. Email is required by Wix; "
        "if the caller declines to share, fall back to sagewillowspa@gmail.com.",
        {
            "type": "object",
            "properties": {
                "serviceId":  {"type": "string"},
                "variantId":  {"type": "string", "description": "Pricing variant ID from get_services.pricingVariants[].id — represents the duration/price the caller selected (e.g., 60-min vs 90-min vs 120-min)."},
                "staffId":    {"type": "string"},
                "scheduleId": {"type": "string"},
                "startDate":  {"type": "string", "description": "ISO local start of slot."},
                "endDate":    {"type": "string", "description": "ISO local end of slot."},
                "firstName":  {"type": "string"},
                "lastName":   {"type": "string"},
                "email":      {"type": "string", "description": f"Caller's email or fallback {SPA_FALLBACK_EMAIL}."},
                "phone":      {"type": "string", "description": "E.164 phone number."},
                "addOnIds":   {"type": "array", "items": {"type": "string"}, "description": "Optional add-on IDs."},
            },
            "required": ["serviceId", "variantId", "staffId", "scheduleId",
                         "startDate", "endDate", "firstName", "lastName",
                         "email", "phone"],
        },
        response_variables={
            "new_booking_id":      "$.bookingId",
            "booking_confirmed":   "$.confirmed",
            "confirmed_start":     "$.startDate",
            "confirmed_end":       "$.endDate",
            "booking_success":     "$.success",
        },
    ),
    tool(
        "cancel_booking",
        "cancel-booking",
        "Cancel an existing booking by bookingId. Get the bookingId from get_booking first.",
        {
            "type": "object",
            "properties": {"bookingId": {"type": "string"}},
            "required": ["bookingId"],
        },
        response_variables={"cancel_success": "$.success", "cancel_status": "$.status"},
    ),
    tool(
        "reschedule_booking",
        "reschedule-booking",
        "Reschedule an existing booking to a new slot. Requires the original bookingId, "
        "revision, serviceId, scheduleId, staffId, plus the new startDate and endDate.",
        {
            "type": "object",
            "properties": {
                "bookingId":  {"type": "string"},
                "revision":   {"type": "string", "description": "Revision number from get_booking — required by Wix."},
                "serviceId":  {"type": "string"},
                "scheduleId": {"type": "string"},
                "staffId":    {"type": "string"},
                "startDate":  {"type": "string"},
                "endDate":    {"type": "string"},
            },
            "required": ["bookingId", "revision", "serviceId", "scheduleId", "staffId",
                         "startDate", "endDate"],
        },
        response_variables={
            "reschedule_success": "$.success",
            "new_start":          "$.newStartDate",
            "new_end":            "$.newEndDate",
        },
    ),
    tool(
        "get_booking",
        "get-booking",
        "Look up an existing booking by bookingId OR by email. Email is the primary "
        "lookup key — ask the caller for the email address they used to book and read "
        "it back to confirm before calling. Returns up to 5 bookings with bookingId, "
        "revision, serviceId, scheduleId, staffId, startDate, endDate, and contact "
        "details — these populate variables for downstream cancel/reschedule.",
        {
            "type": "object",
            "properties": {
                "bookingId": {"type": "string", "description": "If the caller knows their booking ID."},
                "email":     {"type": "string", "description": "Email address used for the original booking. Read back letter-by-letter for the local part; speak common domains naturally before calling."},
            },
            "required": [],
        },
        response_variables={
            "bookings_count":     "$.count",
            "booking_id":         "$.bookings[0].bookingId",
            "booking_revision":   "$.bookings[0].revision",
            "booking_service_id": "$.bookings[0].serviceId",
            "booking_schedule_id":"$.bookings[0].scheduleId",
            "booking_staff_id":   "$.bookings[0].staffId",
            "booking_start":      "$.bookings[0].startDate",
            "booking_end":        "$.bookings[0].endDate",
            "booking_first_name": "$.bookings[0].firstName",
            "booking_last_name":  "$.bookings[0].lastName",
            "booking_phone":      "$.bookings[0].phone",
        },
    ),
    tool(
        "flag_callback",
        "flag-callback",
        "Send Nicky an email + SMS when the agent cannot answer a question or the caller "
        "insists on a human. Use this instead of warm-transferring (Nicky is in session and "
        "cannot pick up). Always include a short reason summary so she can call back prepared. "
        "NOTE: this route must be added to the n8n workflow before launch.",
        {
            "type": "object",
            "properties": {
                "callerName":   {"type": "string", "description": "Caller's name if known."},
                "callerPhone":  {"type": "string", "description": "Caller's phone (defaults to from_number)."},
                "reason":       {"type": "string", "description": "One-sentence summary of why a callback is needed."},
                "questionDetail":{"type": "string", "description": "The actual question or request, in the caller's words if possible."},
            },
            "required": ["reason"],
        },
        response_variables={"callback_flagged": "$.flagged"},
    ),
]


# -----------------------------------------------------------------------------
# Reusable edge sets
# -----------------------------------------------------------------------------

def intent_route_edges(prefix: str) -> list[dict]:
    """Edges that route a freshly-asked 'how can I help' answer to the right flow."""
    return [
        edge(
            f"e-{prefix}-book",
            "Caller wants to book a NEW appointment, schedule a massage, or asks about availability for a future visit.",
            "book-collect",
        ),
        edge(
            f"e-{prefix}-manage",
            "Caller wants to cancel, reschedule, change, or check the status of an EXISTING appointment they already have.",
            "manage-collect",
        ),
        edge(
            f"e-{prefix}-faq",
            "Caller is asking a general question about the spa (hours, location, parking, services offered, prices, gift cards, payment methods, what to expect, prenatal, couples massage, gratuity, insurance, etc.) — NOT trying to book or change an appointment.",
            "faq-handler",
        ),
        edge(
            f"e-{prefix}-callback",
            "Caller has a question Aria genuinely cannot answer, or asks for someone to call them back about something specific.",
            "callback-collect",
        ),
    ]


# -----------------------------------------------------------------------------
# Nodes
# -----------------------------------------------------------------------------

NODES: list[dict] = []


def add(node: dict) -> None:
    NODES.append(node)


# --- Greeting / start ---

add({
    "id": "start",
    "type": "conversation",
    "name": "Greeting + Recording Consent",
    "instruction": {
        "type": "prompt",
        "text": (
            "FIRST TURN ONLY — say warmly, in ONE breath, with a soft natural tone:\n"
            "\"Hi, this is Aria from Sage and Willow Spa. Just to let you know, "
            "this call is recorded for quality purpose. How can I help you today?\"\n\n"
            "AFTER THE FIRST TURN — if the caller's reply is unclear, ambiguous, "
            "off-topic in a way the globals didn't catch, or just doesn't fit any "
            "obvious intent (book / manage / FAQ / callback), DO NOT REPEAT THE "
            "GREETING. Instead, gently re-ask in a SHORT, varied phrasing:\n"
            "  \"Sorry, just to make sure I help you the right way — are you "
            "calling to book, change an appointment, or is there something else "
            "I can help with?\"\n"
            "or:\n"
            "  \"Got it — could you tell me a bit more about what you'd like help "
            "with today?\"\n\n"
            "NEVER repeat the recording-consent disclosure (already said once at "
            "the start). NEVER re-deliver the full greeting verbatim. Use natural, "
            "varied re-prompts so the caller never hears the same line twice."
        ),
    },
    "edges": intent_route_edges("start") + [
        edge(
            "e-start-decline-recording",
            "Caller objected to being recorded, asked us not to record the call, or said 'don't record me'.",
            "recording-decline",
        ),
    ],
    "start_speaker": "agent",
    "display_position": {"x": 100, "y": 100},
})

add({
    "id": "recording-decline",
    "type": "end",
    "name": "Recording Decline (graceful end)",
    "instruction": {
        "type": "prompt",
        "text": (
            "Say warmly:\n"
            "\"Understood. We're required to record for quality, so I'll let you go — "
            "feel free to call back or book online at sage-willow-spa dot com anytime. "
            "Have a great day.\"\n\n"
            "Then end the call."
        ),
    },
    "speak_during_execution": True,
    "display_position": {"x": 100, "y": 350},
})

# --- Booking flow ---

add({
    "id": "book-collect",
    "type": "conversation",
    "name": "Book — Collect Preliminary",
    "instruction": {
        "type": "prompt",
        "text": (
            "Goal: collect THREE pieces of information ONE PER TURN, acknowledging "
            "each before moving on. Do not stack questions. DO NOT ask for the "
            "caller's name here — name handling happens later in the booking "
            "subagent (it's looked up automatically for returning clients, only "
            "asked for new clients who couldn't be found).\n\n"
            "1. Whether they're a NEW client or have visited Sage and Willow Spa "
            "   BEFORE. Ask warmly: \"Have you been to Sage and Willow Spa before, "
            "   or is this your first visit?\"\n"
            "2. What kind of massage they're interested in — Signature, Swedish, "
            "   Deep Tissue, Hot Stone, Prenatal, Lymphatic Drainage, or "
            "   thirty-minute Focus. If they're not sure, briefly describe a few "
            "   in one sentence each and let them pick.\n"
            "3. Their preferred day and a rough time window. Ask conversationally — "
            "   for example, \"What day were you thinking, and roughly what time?\" — "
            "   and accept whatever phrasing they use.\n\n"
            "Q3 STYLE RULE: do NOT read example phrases aloud (no \"like 'Saturday "
            "afternoon' or 'tomorrow around three PM'\"). Just ask the question plainly.\n\n"
            "Q3 \"EARLIEST AVAILABLE\" BYPASS: if the caller answers Q3 with any of:\n"
            "  - \"earliest available\" / \"soonest\" / \"asap\" / \"as soon as possible\"\n"
            "  - \"today\" / \"today if possible\" / \"whatever's open today\"\n"
            "  - \"whenever you have time\" / \"any time\" / \"open to anything\"\n"
            "TREAT Q3 AS COMPLETE — do not ask for a specific day or time-of-day. "
            "The book-subagent will handle the search appropriately (with "
            "earliestFirst: true starting from today). Acknowledge briefly "
            "(\"Got it, I'll find the soonest available\") and proceed.\n\n"
            "After all three are collected, say EXACTLY:\n"
            "\"Got it — let me check what we have.\"\n"
            "Then stop. The system handles the next step.\n\n"
            "GUARDRAILS:\n"
            "- One question per turn.\n"
            "- Don't ask for the caller's NAME here — book-subagent handles it.\n"
            "- Don't ask for phone or email here — those come after we pick a slot.\n"
            "- Never read brackets [ ] aloud.\n"
            "- Don't deliver any closing line — that's not your job here."
        ),
    },
    "edges": [
        equation_edge(
            "e-book-collect-already-booked",
            [{"left": "{{new_booking_id}}", "operator": "exists"}],
            "post-task",
        ),
        edge(
            "e-book-collect-done",
            "Aria has just said \"Got it — let me check what we have.\" OR all three fields "
            "(new/returning, service interest, preferred day/time OR an "
            "earliest-available bypass) have been collected.",
            "book-subagent",
            examples=[
                {"id": "fe-bcoll-done-1", "destination_node_id": "book-subagent",
                 "transcript": [
                    {"role": "user", "content": "Monday around 10 AM"},
                    {"role": "agent", "content": "Got it — let me check what we have."}]},
                {"id": "fe-bcoll-done-2", "destination_node_id": "book-subagent",
                 "transcript": [
                    {"role": "user", "content": "Earliest available"},
                    {"role": "agent", "content": "Got it, I'll find the soonest available."}]},
                {"id": "fe-bcoll-done-3", "destination_node_id": "book-subagent",
                 "transcript": [
                    {"role": "user", "content": "Today if possible"},
                    {"role": "agent", "content": "Got it — let me check what we have."}]},
                {"id": "fe-bcoll-done-4", "destination_node_id": "book-subagent",
                 "transcript": [
                    {"role": "agent", "content": "Got it — let me check what we have."},
                    {"role": "user", "content": "Sounds good"}]},
            ],
        ),
        edge(
            "e-book-collect-cancel",
            "Caller changed their mind and said they don't want to book after all.",
            "post-task",
        ),
    ],
    "display_position": {"x": 500, "y": 100},
})

add({
    "id": "book-subagent",
    "type": "subagent",
    "name": "Book — Tool-Driven Booking",
    "instruction": {
        "type": "prompt",
        "text": (
            "You're helping the caller book a massage at Sage & Willow Spa. Use the "
            "attached tools fluidly — narrate naturally between calls. Speak times in "
            "natural form (\"three thirty PM\"), prices naturally (\"one hundred thirty "
            "dollars\"), and durations naturally (\"ninety minutes\"). Pacific time only "
            "(ten AM to eight PM, every day except Christmas Day and Thanksgiving Day).\n\n"
            "Sequence:\n\n"
            "STEP 0 — Contact lookup (returning clients only).\n"
            "  This step ONLY runs if the caller said in book-collect that they've "
            "  visited before. SKIP entirely for new clients.\n"
            "  a) Call get_contact with phone={{user_number}}. Don't announce — "
            "     this is a quiet lookup.\n"
            "  b) If contact_found is true after that call, greet the caller by "
            "     first name to confirm: \"Welcome back, {{contact_first_name}}! \" "
            "     and proceed. The contact's first/last name, email, and phone are "
            "     now stored — DO NOT re-ask for any of those later in STEP 5.\n"
            "  c) If contact_found is false, ask for the email they used at the "
            "     spa: \"No worries — what email did you use when you booked "
            "     before? I'll find your file.\" Then call get_contact again with "
            "     that email.\n"
            "    - If found this time, greet by first name as in (b).\n"
            "    - If still not found, treat the caller as new for this booking — "
            "      apologize briefly (\"Hmm, I'm not finding you in the system, "
            "      but no problem — we'll get you set up\") and proceed. You'll "
            "      need to collect first/last name + email manually in STEP 5.\n"
            "  Do NOT skip new-client cases through this step. Do NOT make a "
            "  returning caller repeat their name, email, or phone if get_contact "
            "  found them.\n\n"
            "STEP 1 — Confirm service + pick a duration variant.\n"
            "  Call get_services. Look up the service the caller picked.\n"
            "  - If the service has a single fixed `price` (no pricingVariants), "
            "    confirm in one sentence: \"Got it — that's [price] for [duration].\"\n"
            "  - If the service has `pricingVariants` (an array of {id, duration, "
            "    price} options), READ THE OPTIONS to the caller naturally and "
            "    ask which one they want. Example for Deep Tissue:\n"
            "      \"Deep Tissue comes in three lengths — sixty minutes for "
            "      ninety dollars, ninety minutes for one hundred thirty "
            "      dollars, or two hours for one hundred eighty dollars. "
            "      Which would you like?\"\n"
            "    Capture the pricingVariants[].id of the option they pick — "
            "    you'll pass it as variantId to book_appointment in STEP 6.\n"
            "  Do NOT mention add-ons here. STOP after confirming service + variant.\n\n"
            "STEP 2 — Gather slot preferences (BEFORE calling get_slots).\n"
            "  Ask these in order, ONE PER TURN, to narrow the search. Each answer "
            "  becomes a get_slots argument:\n"
            "    a) Therapist preference: \"Any preference on therapist, or no preference?\"\n"
            "       - If they name someone → call get_staff to resolve the staffId for that "
            "         person; you'll pass it to get_slots.\n"
            "       - If \"no preference\" / \"whoever's available\" → omit staffId.\n"
            "    b) Time-of-day preference: \"Morning, afternoon, or evening work better — "
            "       or do you want the earliest available?\"\n"
            "       - \"morning\" / \"afternoon\" / \"evening\" → pass that as timeOfDay.\n"
            "       - \"earliest\" / \"anytime\" / \"soonest\" / \"first available\" → pass "
            "         earliestFirst: true and limit: 3 (skip the time-of-day filter).\n"
            "       - If they're flexible → pass timeOfDay: \"any\" with limit: 6.\n\n"
            "STEP 3 — Fetch and offer slots.\n"
            "  Call get_slots with serviceId, a 3–5 day window around the caller's "
            "  preferred day, plus the preference filters from Step 2. Read back two or "
            "  three viable times naturally; let the caller pick.\n"
            "  - If get_slots returns nothing in the requested filter, widen ONCE: drop "
            "    timeOfDay (or staffId) and re-call. If still empty, offer a callback via "
            "    flag_callback.\n"
            "  - If the caller asked for a specific therapist who has no availability, say "
            "    so plainly and ask if any therapist is okay; if yes, re-call without "
            "    staffId.\n\n"
            "STEP 4 — Confirm slot + add-ons.\n"
            "  Confirm the picked slot. Then ask if they'd like any add-ons.\n\n"
            "STEP 5 — Collect contact info (CONDITIONAL based on STEP 0).\n"
            "  IF the contact lookup in STEP 0 succeeded ({{contact_found}} is "
            "  true), DO NOT ask for first name, last name, email, or phone. "
            "  You already have all of them as variables. Just confirm in ONE "
            "  short sentence:\n"
            "    \"I have you on file as {{contact_first_name}} "
            "    {{contact_last_name}}, with email {{contact_email}} and phone "
            "    [read {{contact_phone}} grouped 3-3-4]. Use those for the "
            "    booking, or want to update something?\"\n"
            "  - If they say yes/use those: skip ahead to STEP 6.\n"
            "  - If they want to update one field, ask only for that field, "
            "    confirm, and proceed.\n\n"
            "  IF the contact lookup in STEP 0 failed OR the caller is new "
            "  (contact_found is false or unset), collect manually ONE PER TURN:\n"
            "    a) First and last name (only if not already known from "
            "       earlier in the call).\n"
            "    b) Phone number — default to {{user_number}}; confirm it's "
            "       the best one. Read back grouped 3-3-4.\n"
            "    c) Email — ASK PLAINLY: \"What's the best email for the booking?\"\n"
            "       Do NOT pre-offer a \"spa email on file\" as an option. That is "
            "       a SILENT internal fallback only — never present it as a choice.\n"
            "       Read back to confirm: spell the LOCAL part letter by letter, "
            "       common domains spoken naturally (\"at gmail dot com\").\n"
            f"       ONLY if the caller refuses to share, quietly use {SPA_FALLBACK_EMAIL} "
            "       without reading it aloud (\"no problem, we'll keep email off "
            "       the booking\").\n\n"
            "STEP 6 — Final readback + book.\n"
            "  Read back the FULL booking once: service, duration (in minutes), "
            "  day and date, time, therapist name, total price (base + add-ons), "
            "  contact info. Mention the cancellation policy ONCE here: \"We ask "
            "  for twenty-four hours' notice for cancellations.\" Then ask them "
            "  to confirm. After they say yes, call book_appointment with these "
            "  required fields:\n"
            "    - serviceId (from STEP 1's get_services)\n"
            "    - variantId (the pricingVariants[].id the caller picked — REQUIRED)\n"
            "    - staffId, scheduleId, startDate, endDate (from STEP 3's get_slots)\n"
            "    - firstName, lastName, email, phone (from STEP 0 lookup OR STEP 5 collection)\n"
            "    - addOnIds (optional array, from STEP 4)\n"
            "  WITHOUT variantId the booking will be rejected — never skip it.\n\n"
            "If something fails or the caller wants a human, call flag_callback with a "
            "short reason and end this branch.\n\n"
            "INLINE FAQ HANDLING (important): if the caller asks a brief spa-related "
            "question mid-flow — location, hours, parking, payment methods, gratuity, "
            "what to wear, intake forms, pet policy, cancellation policy, late-arrival "
            "rules, etc. — answer in 1–2 sentences using the attached knowledge base, "
            "THEN return immediately to where the booking left off. Do NOT route to "
            "the FAQ handler. Do NOT abandon the booking. Do NOT make the caller "
            "repeat anything they already gave you.\n"
            "Off-topic, non-spa questions are handled by the global off-topic redirect "
            "automatically — don't engage with them.\n\n"
            "When book_appointment returns success, stop talking and let the next node "
            "deliver the confirmation. Do not read the bookingId aloud."
        ),
    },
    "tool_ids": ["get_contact", "get_services", "get_staff", "get_slots", "book_appointment", "flag_callback"],
    "edges": [
        equation_edge(
            "e-book-subagent-success",
            [{"left": "{{new_booking_id}}", "operator": "exists"}],
            "book-success",
        ),
        edge(
            "e-book-subagent-callback",
            "Booking attempt failed, no slots are available in any reasonable window, "
            "OR the caller specifically asked to have someone call them back about booking.",
            "callback-collect",
        ),
        edge(
            "e-book-subagent-walkaway",
            "Caller decided not to book after seeing options or prices and is wrapping up.",
            "post-task",
        ),
    ],
    "display_position": {"x": 900, "y": 100},
})

add({
    "id": "book-success",
    "type": "conversation",
    "name": "Book — Confirmation Line",
    "instruction": {
        "type": "prompt",
        "text": (
            "Say ONE short line confirming the booking, using only the values from the "
            "successful book_appointment call. Keep it natural and warm — no list, no "
            "long readback (you already read it back once before submitting).\n\n"
            "Example shape: \"Perfect — you're all set for the [service] on [day, date] "
            "at [time]. We'll see you then.\"\n\n"
            "Substitute real values; if any field is missing, omit it cleanly. Never "
            "fabricate. Do not read out the booking ID. Do not repeat the cancellation "
            "policy — you already mentioned it during readback."
        ),
    },
    "edges": [],
    "skip_response_edge": skip_edge("e-book-success-skip", "post-task"),
    "display_position": {"x": 1300, "y": 100},
})

# --- Manage existing booking flow ---

add({
    "id": "manage-collect",
    "type": "conversation",
    "name": "Manage — Collect Lookup",
    "instruction": {
        "type": "prompt",
        "text": (
            "Caller wants to cancel, reschedule, or check an existing booking. Goal: "
            "get the email address the booking was made under so we can look it up.\n\n"
            "Say:\n"
            "\"Sure — I can help with that. What email address did you use when you "
            "booked?\"\n\n"
            "When they give it, READ IT BACK to confirm:\n"
            "- Spell the LOCAL part (before the @) letter by letter, with phonetic "
            "  alphabet on any ambiguous letter (\"M as in Mike, A as in Alpha\").\n"
            "- For common domains (gmail dot com, yahoo dot com, outlook dot com, "
            "  hotmail dot com, icloud dot com, aol dot com), speak the domain "
            "  naturally — do NOT spell it letter by letter.\n"
            "- For uncommon domains, spell the whole address.\n\n"
            "After they confirm the email is right, say:\n"
            "\"Got it — let me pull that up.\"\n\n"
            "GUARDRAILS:\n"
            "- Do not ask for phone here — email is the lookup key.\n"
            "- Don't ask for name; get_booking returns contact details.\n"
            "- Don't ask for booking ID unless the caller volunteers one."
        ),
    },
    "edges": [
        edge(
            "e-manage-collect-ready",
            "The caller has confirmed their email address is correct, OR "
            "Aria has just said \"Got it — let me pull that up.\"",
            "manage-fetch",
        ),
    ],
    "display_position": {"x": 500, "y": 400},
})

add({
    "id": "manage-fetch",
    "type": "function",
    "name": "Manage — Fetch Booking",
    "tool_id": "get_booking",
    "tool_type": "local",
    "wait_for_result": True,
    "edges": [],
    "always_edge": always_edge("e-manage-fetch-after", "manage-router"),
    "display_position": {"x": 900, "y": 400},
})

add({
    "id": "manage-router",
    "type": "branch",
    "name": "Manage — Found vs Not Found",
    "edges": [
        # Robust "found" check: bookings_count must exist AND be non-zero AND non-empty.
        # Earlier we relied on {{booking_id}} exists, but production calls showed that
        # equation failing even when the lookup returned a booking. bookings_count is
        # always set by the n8n format-response (to "0" or "N"), so it's the safer key.
        equation_edge(
            "e-manage-router-found",
            [
                {"left": "{{bookings_count}}", "operator": "exists"},
                {"left": "{{bookings_count}}", "operator": "!=", "right": "0"},
                {"left": "{{bookings_count}}", "operator": "!=", "right": ""},
            ],
            "manage-action-prompt",
            op="&&",
        ),
    ],
    "else_edge": else_edge("e-manage-router-not-found", "manage-not-found"),
    "display_position": {"x": 1300, "y": 400},
})

add({
    "id": "manage-not-found",
    "type": "conversation",
    "name": "Manage — Not Found",
    "instruction": {
        "type": "prompt",
        "text": (
            "Say:\n"
            "\"Hmm, I'm not finding any active appointments under that email. Want me "
            "to book you something new, or is there anything else I can help with?\"\n\n"
            "Don't suggest the caller's email is wrong or misspelled — be diplomatic. "
            "It's possible the booking was made with a different address."
        ),
    },
    "edges": [
        edge("e-manage-nf-book", "Caller wants to book a new appointment.", "book-collect"),
        edge("e-manage-nf-faq", "Caller has a general question instead.", "faq-handler"),
        edge(
            "e-manage-nf-no",
            "Caller said no, that's all, goodbye, or otherwise indicated they're done.",
            "close-call",
        ),
    ],
    "display_position": {"x": 1300, "y": 650},
})

add({
    "id": "manage-action-prompt",
    "type": "conversation",
    "name": "Manage — Action Prompt",
    "instruction": {
        "type": "prompt",
        "text": (
            "Read back the existing booking found, then ask what they want to do.\n\n"
            "Say something like:\n"
            "\"Okay — I see your booking on [day and date] at [time]. What would you "
            "like to do — cancel, reschedule, or something else?\"\n\n"
            "Use the values from {{booking_start}} for date/time. Speak the date "
            "naturally (e.g., \"Saturday, May ninth at three PM\"). Don't read the "
            "raw ISO timestamp aloud. Don't read the booking ID aloud."
        ),
    },
    "edges": [
        edge(
            "e-manage-action-cancel",
            "Caller wants to CANCEL the appointment.",
            "cancel-confirm",
        ),
        edge(
            "e-manage-action-reschedule",
            "Caller wants to RESCHEDULE, move, or change the time of the appointment.",
            "reschedule-subagent",
        ),
        edge(
            "e-manage-action-info",
            "Caller just wanted to confirm the details and isn't changing anything.",
            "post-task",
        ),
    ],
    "display_position": {"x": 1700, "y": 400},
})

# --- Cancel ---

add({
    "id": "cancel-confirm",
    "type": "conversation",
    "name": "Cancel — Confirm Intent",
    "instruction": {
        "type": "prompt",
        "text": (
            "Confirm the cancellation explicitly before submitting.\n\n"
            "Say:\n"
            "\"Just to confirm — you'd like me to cancel the appointment on [day, date] "
            "at [time]? Heads up, we ask for twenty-four hours' notice as a courtesy — "
            "should I go ahead?\"\n\n"
            "Use the booking's start date/time from variables. If they say yes, move on. "
            "If they hesitate or change their mind, route to reschedule or back out."
        ),
    },
    "edges": [
        edge(
            "e-cancel-yes",
            "Caller has explicitly confirmed they want to cancel — said yes, please cancel, "
            "go ahead, or similar firm affirmation after Aria asked \"should I go ahead?\".",
            "cancel-execute",
            examples=[
                {"id": "fe-cancel-yes-1", "destination_node_id": "cancel-execute",
                 "transcript": [{"role": "agent", "content": "...should I go ahead?"},
                                {"role": "user", "content": "Yes please."}]},
                {"id": "fe-cancel-yes-2", "destination_node_id": "cancel-execute",
                 "transcript": [{"role": "agent", "content": "...should I go ahead?"},
                                {"role": "user", "content": "Yeah, go ahead and cancel it."}]},
            ],
        ),
        edge(
            "e-cancel-reschedule-instead",
            "Caller decided to reschedule instead of canceling.",
            "reschedule-subagent",
        ),
        edge(
            "e-cancel-back-out",
            "Caller decided to keep the booking after all and is not canceling.",
            "post-task",
            examples=[
                {"id": "fe-cancel-back-1", "destination_node_id": "post-task",
                 "transcript": [{"role": "agent", "content": "...should I go ahead?"},
                                {"role": "user", "content": "Actually no, leave it."}]},
            ],
        ),
    ],
    "display_position": {"x": 2100, "y": 250},
})

add({
    "id": "cancel-execute",
    "type": "function",
    "name": "Cancel — Execute",
    "tool_id": "cancel_booking",
    "tool_type": "local",
    "wait_for_result": True,
    "edges": [],
    "always_edge": always_edge("e-cancel-execute-after", "cancel-success"),
    "display_position": {"x": 2500, "y": 250},
})

add({
    "id": "cancel-success",
    "type": "conversation",
    "name": "Cancel — Success",
    "instruction": {
        "type": "prompt",
        "text": (
            "Say ONE short line:\n"
            "\"All set — your appointment is canceled. Anything else I can help with?\"\n\n"
            "If cancel_success returned false, say instead:\n"
            "\"Hmm, looks like that didn't go through on my end. I'll have someone reach "
            "out to make sure it's handled. Anything else?\"\n\n"
            "Then route based on what the caller says next."
        ),
    },
    "edges": [
        edge(
            "e-cancel-success-no",
            "Caller said no, that's all, goodbye, or similar.",
            "close-call",
        ),
        edge(
            "e-cancel-success-book",
            "Caller wants to book a new appointment.",
            "book-collect",
        ),
        edge(
            "e-cancel-success-manage",
            "Caller wants to manage another existing booking.",
            "manage-collect",
        ),
        edge(
            "e-cancel-success-faq",
            "Caller has another general question.",
            "faq-handler",
        ),
    ],
    "display_position": {"x": 2900, "y": 250},
})

# --- Reschedule ---

add({
    "id": "reschedule-subagent",
    "type": "subagent",
    "name": "Reschedule — Tool-Driven",
    "instruction": {
        "type": "prompt",
        "text": (
            "You're rescheduling an existing booking. The original booking details are "
            "already loaded as variables: {{booking_id}}, {{booking_revision}}, "
            "{{booking_service_id}}, {{booking_schedule_id}}, {{booking_staff_id}}.\n\n"
            "Sequence:\n\n"
            "STEP 1 — Get new-day preference.\n"
            "  Ask: \"What day were you thinking of moving it to?\" Get a target day or rough "
            "  range.\n\n"
            "STEP 2 — Get time-of-day preference (BEFORE calling get_slots).\n"
            "  Ask: \"Morning, afternoon, or evening work better — or do you want the "
            "  earliest available?\"\n"
            "    - \"morning\" / \"afternoon\" / \"evening\" → pass timeOfDay to get_slots.\n"
            "    - \"earliest\" / \"anytime\" / \"soonest\" → pass earliestFirst: true, "
            "      limit: 3.\n"
            "    - flexible → pass timeOfDay: \"any\", limit: 6.\n\n"
            "  THERAPIST RULE — read this carefully:\n"
            "  - DEFAULT: keep the same therapist as the original booking. Pass "
            "    staffId={{booking_staff_id}} on every get_slots call. The caller has "
            "    already seen this therapist; reschedule continuity matters.\n"
            "  - DO NOT call get_staff. Do NOT ask the caller \"who was your previous "
            "    therapist?\" — we already know from {{booking_staff_id}}.\n"
            "  - If the caller says \"same therapist as before\" / \"the one I had\" / "
            "    similar continuity language, that is the DEFAULT — proceed silently.\n"
            "  - ONLY omit staffId if the caller EXPLICITLY says they want a different "
            "    therapist (\"someone else\", \"a different person\") or says \"anyone is fine\".\n\n"
            "STEP 3 — Fetch and offer.\n"
            "  Call get_slots with serviceId={{booking_service_id}}, a 3–5 day window "
            "  around the new preferred day, plus the filters from Step 2. Read back two "
            "  or three viable times; let the caller pick.\n"
            "  - If empty under the filters, widen ONCE (drop staffId, then drop timeOfDay) "
            "    before giving up.\n\n"
            "STEP 4 — Confirm new slot.\n"
            "  Say: \"To confirm — moving you to [new day, date] at [new time]. Sound good?\"\n\n"
            "STEP 5 — Submit.\n"
            "  After they confirm, call reschedule_booking with the new slot's "
            "  serviceId, scheduleId, staffId, startDate, endDate, plus the original "
            "  bookingId={{booking_id}} and revision={{booking_revision}}.\n\n"
            "If reschedule_booking returns failure, apologize and call flag_callback so "
            "Nicky can sort it out manually.\n\n"
            "Pacific time, ten AM to eight PM only. Speak times naturally. Do not read "
            "out IDs or revision numbers."
        ),
    },
    "tool_ids": ["get_slots", "reschedule_booking", "flag_callback"],
    "edges": [
        equation_edge(
            "e-reschedule-success",
            [{"left": "{{reschedule_success}}", "operator": "==", "right": "true"}],
            "reschedule-success",
        ),
        edge(
            "e-reschedule-callback",
            "Reschedule attempt failed, no slots are available, OR the caller wants help "
            "from a human.",
            "callback-collect",
        ),
        edge(
            "e-reschedule-walkaway",
            "Caller decided not to reschedule after seeing options.",
            "post-task",
        ),
    ],
    "display_position": {"x": 2100, "y": 550},
})

add({
    "id": "reschedule-success",
    "type": "conversation",
    "name": "Reschedule — Success Line",
    "instruction": {
        "type": "prompt",
        "text": (
            "Say ONE short line confirming the new time, using {{new_start}}.\n\n"
            "Example: \"Done — you're now booked for [new day, date] at [new time].\"\n\n"
            "Speak the date and time naturally. Do not read out IDs."
        ),
    },
    "edges": [],
    "skip_response_edge": skip_edge("e-reschedule-success-skip", "post-task"),
    "display_position": {"x": 2500, "y": 550},
})

# --- FAQ / Info ---

add({
    "id": "faq-handler",
    "type": "subagent",
    "name": "FAQ / Info Handler",
    "instruction": {
        "type": "prompt",
        "text": (
            "You're answering a general question about Sage & Willow Spa. Use the "
            "attached knowledge base for FAQs (hours, location, parking, gift cards, "
            "payment methods, prenatal eligibility, late arrival, gratuity, insurance, "
            "etc.) and the get_services tool when the caller asks about specific "
            "service details, prices, durations, or add-ons.\n\n"
            "Answer in 1–2 sentences, conversationally. Don't read service lists or "
            "prices like a menu — pick the relevant ones for the caller's question.\n\n"
            "If the question isn't answered by the KB or get_services and you're not "
            "confident, do NOT guess. Offer a callback: \"That's a good question — "
            "let me have someone reach out so you get the right answer.\"\n\n"
            "After answering, ask: \"Anything else I can help with?\"\n\n"
            "Hours reminder: ten AM to eight PM Pacific, every day except Christmas Day "
            "and Thanksgiving Day. Address: four hundred Rowland Boulevard, Novato, "
            "California. Phone: six two eight, six eight two, eight zero one zero. "
            "Cancellation policy: twenty-four hours' notice. Walk-ins accepted "
            "depending on availability."
        ),
    },
    "tool_ids": ["get_services", "get_staff", "flag_callback"],
    "edges": [
        edge(
            "e-faq-book",
            "Caller wants to book an appointment after their question was answered.",
            "book-collect",
        ),
        edge(
            "e-faq-manage",
            "Caller wants to cancel, reschedule, or check an existing appointment.",
            "manage-collect",
        ),
        edge(
            "e-faq-callback",
            "Aria couldn't answer confidently and offered a callback that the caller accepted.",
            "callback-collect",
        ),
        edge(
            "e-faq-done",
            "Caller indicated they're done — said no, that's all, thanks, goodbye, or similar.",
            "close-call",
        ),
    ],
    "display_position": {"x": 500, "y": 700},
})

# --- Callback capture ---

add({
    "id": "callback-collect",
    "type": "conversation",
    "name": "Callback — Collect",
    "instruction": {
        "type": "prompt",
        "text": (
            "Goal: collect the info needed to flag a callback for Nicky. ONE QUESTION PER TURN.\n\n"
            "1. Caller's name (if not already known from earlier in the call).\n"
            "2. Best phone number — default to the number they're calling from "
            f"   ({{{{user_number}}}}); only re-ask if they want a different number. "
            "   Read back grouped 3-3-4.\n"
            "3. A one-sentence summary of what they need help with.\n\n"
            "After all three are collected, say EXACTLY:\n"
            "\"Got it — I'll have her reach out as soon as she's free.\"\n"
            "Then stop. The system flags the callback.\n\n"
            "GUARDRAILS:\n"
            "- One question per turn.\n"
            "- Confirm any uncommon name with phonetic alphabet.\n"
            "- Don't promise a specific call-back time — Nicky calls back when she's out of session."
        ),
    },
    "edges": [
        equation_edge(
            "e-callback-collect-already",
            [{"left": "{{callback_flagged}}", "operator": "exists"}],
            "post-task",
        ),
        edge(
            "e-callback-collect-done",
            "Aria has just said \"Got it — I'll have her reach out as soon as she's free.\" "
            "OR all three callback fields (name, phone, reason) are collected.",
            "callback-flag",
        ),
        edge(
            "e-callback-collect-cancel",
            "Caller changed their mind and no longer wants a callback.",
            "post-task",
        ),
    ],
    "display_position": {"x": 500, "y": 1000},
})

add({
    "id": "callback-flag",
    "type": "function",
    "name": "Callback — Flag",
    "tool_id": "flag_callback",
    "tool_type": "local",
    "wait_for_result": True,
    "edges": [],
    "always_edge": always_edge("e-callback-flag-after", "callback-success"),
    "display_position": {"x": 900, "y": 1000},
})

add({
    "id": "callback-success",
    "type": "conversation",
    "name": "Callback — Success Line",
    "instruction": {
        "type": "prompt",
        "text": (
            "Say ONE short line:\n"
            "\"You're all set — she'll call you back. Anything else I can help with in the meantime?\"\n\n"
            "Be warm but brief."
        ),
    },
    "edges": [
        edge(
            "e-callback-success-no",
            "Caller said no, that's all, thanks, or similar.",
            "close-call",
        ),
        edge(
            "e-callback-success-faq",
            "Caller has another question.",
            "faq-handler",
        ),
        edge(
            "e-callback-success-book",
            "Caller wants to book an appointment.",
            "book-collect",
        ),
    ],
    "display_position": {"x": 1300, "y": 1000},
})

# --- Post-task menu ---

add({
    "id": "post-task",
    "type": "conversation",
    "name": "Post-Task Menu",
    "instruction": {
        "type": "prompt",
        "text": (
            "Say ONE short line:\n"
            "\"Anything else I can help you with today?\"\n\n"
            "If you've ALREADY asked this same question in the immediately previous "
            "turn (caller is responding to it now), DO NOT repeat — instead say a "
            "brief acknowledgment like \"Sounds good.\" or \"Got it.\" and let the "
            "edges route based on the caller's response. NEVER stay silent or "
            "respond NO_RESPONSE_NEEDED here."
        ),
    },
    "edges": intent_route_edges("post") + [
        edge(
            "e-post-no",
            "Caller said no, that's all, nothing else, thanks, goodbye, bye, or any "
            "other clear indicator they're done with the call.",
            "close-call",
            examples=[
                {"id": "fe-post-bye-1", "destination_node_id": "close-call",
                 "transcript": [{"role": "agent", "content": "Anything else I can help you with today?"},
                                {"role": "user", "content": "No thanks, that's all."}]},
                {"id": "fe-post-bye-2", "destination_node_id": "close-call",
                 "transcript": [{"role": "agent", "content": "Anything else I can help you with today?"},
                                {"role": "user", "content": "Bye bye"}]},
                {"id": "fe-post-bye-3", "destination_node_id": "close-call",
                 "transcript": [{"role": "agent", "content": "Anything else I can help you with today?"},
                                {"role": "user", "content": "I'm good, thanks"}]},
            ],
        ),
    ],
    "display_position": {"x": 1700, "y": 850},
})

# --- Close ---

add({
    "id": "close-call",
    "type": "end",
    "name": "Close Call",
    "instruction": {
        "type": "prompt",
        "text": (
            "Say ONE short, GENERIC closing — works for every exit path (booking, "
            "FAQ, decline, spam, off-topic, etc.):\n"
            "  \"Thanks for calling Sage and Willow Spa. Take care.\"\n\n"
            "If you delivered any farewell line in the immediately previous turn "
            "(e.g., \"Take care!\", \"Have a great day\", \"You're all set\"), say "
            "just the short form and end:\n"
            "  \"Take care.\"\n\n"
            "RULES:\n"
            "- NEVER say \"we look forward to seeing you\" — it presumes a future "
            "  visit, wrong for declines / spam / info-only calls.\n"
            "- NEVER reference a specific booking by date, time, or service in the "
            "  closing — that was already done at book-success.\n"
            "- NEVER repeat the recording-consent line.\n"
            "- ALWAYS brief — one short sentence, then end the call."
        ),
    },
    "speak_during_execution": True,
    "display_position": {"x": 2100, "y": 850},
})

# -----------------------------------------------------------------------------
# Global Nodes
# -----------------------------------------------------------------------------

add({
    "id": "g-emergency",
    "type": "conversation",
    "name": "GLOBAL — Medical Emergency",
    "instruction": {
        "type": "prompt",
        "text": (
            "Say ONE calm, clear line:\n"
            "\"If this is a medical emergency, please hang up and call nine-one-one "
            "right away.\"\n\n"
            "Then stop. Do not engage further. Do not offer to book or take a callback."
        ),
    },
    "edges": [],
    "skip_response_edge": skip_edge("e-g-emergency-skip", "close-call"),
    "global_node_setting": {
        "condition": (
            "When the caller reports a medical emergency, says someone is unconscious, "
            "having a heart attack, can't breathe, is bleeding heavily, or otherwise "
            "describes an active life-threatening situation."
        ),
    },
    "display_position": {"x": 100, "y": 1300},
})

add({
    "id": "g-crisis",
    "type": "conversation",
    "name": "GLOBAL — Crisis / Distress",
    "instruction": {
        "type": "prompt",
        "text": (
            "Say ONE warm, calm line:\n"
            "\"I hear you. If you're in crisis or having thoughts of harming yourself, "
            "please contact the nine-eight-eight Suicide and Crisis Lifeline by dialing "
            "nine-eight-eight — they're there for you twenty-four seven.\"\n\n"
            "Then stop. Do not push to book or transfer. Do not engage further."
        ),
    },
    "edges": [],
    "skip_response_edge": skip_edge("e-g-crisis-skip", "close-call"),
    "global_node_setting": {
        "condition": (
            "When the caller expresses acute emotional distress, mentions self-harm, "
            "suicidal thoughts, or says they cannot continue living."
        ),
    },
    "display_position": {"x": 500, "y": 1300},
})

add({
    "id": "g-spam",
    "type": "conversation",
    "name": "GLOBAL — Spam / Solicitation",
    "instruction": {
        "type": "prompt",
        "text": (
            "Say ONE polite, firm line and end:\n"
            "\"Thanks, but we're not interested in any marketing or sales offers. "
            "Have a good day.\"\n\n"
            "Do not engage further. Do not let them pivot."
        ),
    },
    "edges": [],
    "skip_response_edge": skip_edge("e-g-spam-skip", "close-call"),
    "global_node_setting": {
        "condition": (
            "When the caller is selling something to the spa, pitching marketing, SEO, "
            "lead generation, business loans, credit card processing, payroll services, "
            "Google listing services, web design, or running a survey or robocall — i.e., "
            "anyone trying to sell TO us, not a customer."
        ),
    },
    "display_position": {"x": 900, "y": 1300},
})

add({
    "id": "g-inappropriate",
    "type": "conversation",
    "name": "GLOBAL — Inappropriate Request",
    "instruction": {
        "type": "prompt",
        "text": (
            "Say ONE professional, neutral line — do NOT moralize or lecture:\n"
            "\"We're a professional massage spa and only provide therapeutic and "
            "relaxation massage services. Is there anything else I can help you with?\"\n\n"
            "Then route based on what they say next. If they push back, repeat the line "
            "once and then politely end the call."
        ),
    },
    "edges": [
        edge(
            "e-g-inappropriate-book",
            "Caller dropped the inappropriate line and now wants to book a legitimate appointment.",
            "book-collect",
        ),
        edge(
            "e-g-inappropriate-end",
            "Caller pressed again on the inappropriate request, said no, hung up energy, "
            "or otherwise didn't pivot to a legitimate need.",
            "close-call",
        ),
    ],
    "global_node_setting": {
        "condition": (
            "When the caller explicitly asks for \"full service\", \"happy ending\", "
            "sexual services, \"latina girls\", \"asian girls\" in a sexual context, or "
            "uses any euphemism for non-therapeutic services."
        ),
    },
    "display_position": {"x": 1300, "y": 1300},
})

add({
    "id": "g-off-topic",
    "type": "conversation",
    "name": "GLOBAL — Off-Topic Redirect",
    "instruction": {
        "type": "prompt",
        "text": (
            "Say ONE short, friendly line redirecting:\n"
            "\"I'm here to help with bookings and questions about Sage & Willow Spa. Is "
            "there anything spa-related I can help with?\"\n\n"
            "Do not engage with the off-topic content. Do not give an opinion."
        ),
    },
    "edges": intent_route_edges("g-ot") + [
        edge(
            "e-g-ot-no",
            "Caller said no, indicated they don't have a spa-related need, or wants to "
            "wrap up.",
            "close-call",
        ),
    ],
    "global_node_setting": {
        "condition": (
            "FIRES when the caller asks Aria for content that is NOT spa business — "
            "specifically:\n"
            "  - Politics, news, weather, jokes, opinions, life advice, philosophy.\n"
            "  - AI capabilities or how the AI works.\n"
            "  - Math problems, trivia, general knowledge questions.\n"
            "  - Help with unrelated products, services, or other businesses.\n"
            "  - General chitchat with no spa-related intent.\n"
            "  - PERSONAL or ROMANTIC interest in staff (asking for a therapist's "
            "    phone number, social media, address, schedule outside work, dating, "
            "    relationship status, or any non-professional contact).\n"
            "  - Any request for staff personal information beyond their first name.\n"
            "\n"
            "DOES NOT FIRE on any legitimate spa question, INCLUDING:\n"
            "  location / address / 'where are you located', hours, parking, services "
            "  offered, prices, durations, gift cards, payment methods, gratuity, "
            "  insurance, prenatal eligibility, walk-ins, late arrivals, what to wear, "
            "  intake forms, receipts, packages, couples massage, therapist preferences "
            "  during booking, pet/animal policy, cancellation policy, things to know "
            "  before arriving, or anything else about the spa as a business.\n"
            "\n"
            "When in doubt about whether something is spa-related, DO NOT FIRE — let "
            "the current flow's KB handle it inline. This global is the LAST RESORT, "
            "not the first."
        ),
    },
    "display_position": {"x": 1700, "y": 1300},
})

add({
    "id": "g-intent-switch",
    "type": "conversation",
    "name": "GLOBAL — Intent Switch (Mid-Flow Pivot)",
    "instruction": {
        "type": "prompt",
        "text": (
            "The caller has just pivoted to a DIFFERENT request than the flow they "
            "were in. Acknowledge briefly with ONE short, warm line — pick one:\n"
            "  \"Sure, no problem — let me help with that.\"\n"
            "  \"Of course — let me handle that instead.\"\n\n"
            "Then immediately route based on the NEW intent (the one they just "
            "expressed). Do NOT ask them to repeat themselves. Do NOT continue "
            "the previous flow."
        ),
    },
    "edges": intent_route_edges("g-intent"),
    "global_node_setting": {
        "condition": (
            "When the caller pivots to a CLEARLY DIFFERENT primary intent than the "
            "current flow is handling. Examples that FIRE this global:\n"
            "  - In booking flow, says \"actually I want to reschedule my existing one\" "
            "    or \"never mind, I want to cancel\".\n"
            "  - In manage flow, says \"forget it, I want to book new\".\n"
            "  - In booking flow, says \"I just have a quick question first\" "
            "    (FAQ pivot).\n"
            "Does NOT fire on:\n"
            "  - Natural follow-ups within the same flow (changing the time during "
            "    booking, removing an add-on, picking a different therapist).\n"
            "  - Brief affirmations or clarifications.\n"
            "  - The caller asking a one-off question they expect Aria to answer "
            "    quickly and return to the flow."
        ),
    },
    "display_position": {"x": 558, "y": 6500},
})

add({
    "id": "g-human",
    "type": "conversation",
    "name": "GLOBAL — Human Request",
    "instruction": {
        "type": "prompt",
        "text": (
            "Say ONE warm line:\n"
            "\"Of course — let me grab your details and I'll have someone reach out as "
            "soon as they can.\"\n\n"
            "Do NOT promise to transfer the call. Do NOT say \"hold on while I connect "
            "you.\" Nicky is in session and can't pick up the call — that's why it rolled "
            "over to you."
        ),
    },
    "edges": [],
    "skip_response_edge": skip_edge("e-g-human-skip", "callback-collect"),
    "global_node_setting": {
        "condition": (
            "When the caller has explicitly asked to speak to a person, manager, owner, "
            "human, real receptionist, or representative — AND has insisted after Aria "
            "offered to help directly. Does NOT fire on the first request — only when "
            "the caller is firm about needing a human."
        ),
    },
    "display_position": {"x": 2100, "y": 1300},
})


# -----------------------------------------------------------------------------
# Top-level agent doc
# -----------------------------------------------------------------------------

GLOBAL_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")

AGENT = {
    "agent_id": "",
    "channel": "voice",
    "agent_name": "Aria — Sage & Willow Spa - V05",
    "language": ["en-US", "es-ES", "en-IN", "es-419", "en-GB", "en-AU"],
    "voice_id": "11labs-Brynne",
    "voice_temperature": 0.7,
    "voice_speed": 0.9,
    "max_call_duration_ms": 1800000,
    "interruption_sensitivity": 0.9,
    "responsiveness": 1.0,
    "begin_message_delay_ms": 800,
    "ring_duration_ms": 30000,
    "normalize_for_speech": True,
    "stt_mode": "accurate",
    "denoising_mode": "noise-and-background-speech-cancellation",
    "data_storage_setting": "everything",
    "post_call_analysis_model": "gpt-4.1",
    "is_published": False,
    "handbook_config": {
        "echo_verification": False,
        "speech_normalization": True,
        "default_personality": False,
        "scope_boundaries": True,
        "natural_filler_words": True,
        "nato_phonetic_alphabet": True,
        "high_empathy": True,
        "ai_disclosure": False,
        "smart_matching": True,
    },
    "post_call_analysis_data": [
        {
            "name": "caller_intent",
            "type": "enum",
            "choices": [
                "new_booking", "cancel", "reschedule", "status_check",
                "faq_general", "faq_pricing", "callback_request",
                "spam", "inappropriate", "off_topic", "emergency", "crisis", "other",
            ],
            "description": "Primary purpose of the call.",
        },
        {
            "name": "resolution_status",
            "type": "enum",
            "choices": [
                "booking_created", "booking_canceled", "booking_rescheduled",
                "info_provided", "callback_flagged",
                "spam_declined", "inappropriate_deflected",
                "abandoned", "other",
            ],
            "description": "What actually happened on the call.",
        },
        {
            "name": "booking_id",
            "type": "string",
            "description": "Wix bookingId if a booking was created on this call.",
        },
        {
            "name": "service_booked",
            "type": "string",
            "description": "Service name if a booking was created or rescheduled.",
        },
        {
            "name": "appointment_datetime",
            "type": "string",
            "description": "Local appointment date and time in natural language if booked or rescheduled.",
        },
        {
            "name": "callback_required",
            "type": "boolean",
            "description": "True if a callback was flagged for Nicky.",
        },
        {
            "name": "callback_reason",
            "type": "string",
            "description": "Short reason for the callback if one was flagged.",
        },
        {
            "name": "caller_sentiment",
            "type": "enum",
            "choices": ["positive", "neutral", "frustrated", "angry"],
            "description": "Overall caller sentiment by end of call.",
        },
        {
            "name": "is_returning_client",
            "type": "boolean",
            "description": "Did the caller indicate they are a returning client?",
        },
        {
            "name": "language_used",
            "type": "enum",
            "choices": ["english", "spanish", "mixed"],
            "description": "Primary language of the conversation.",
        },
        {
            "name": "recording_consent_acknowledged",
            "type": "boolean",
            "description": "Did the agent deliver the recording-consent line at the start of the call?",
        },
        {
            "name": "spam_call",
            "type": "boolean",
            "description": "Was this call identified as spam, marketing, or solicitation?",
        },
        {
            "name": "inappropriate_request",
            "type": "boolean",
            "description": "Did the caller request 'full service' / 'happy ending' / sexual services?",
        },
        {
            "name": "tool_failure",
            "type": "boolean",
            "description": "Did any Wix tool call fail (slot lookup, booking creation, etc.)?",
        },
        {
            "name": "call_summary",
            "type": "string",
            "description": "Two-sentence summary of what happened on the call.",
        },
    ],
    "response_engine": {
        "type": "conversation-flow",
        "version": 1,
        "conversation_flow_id": "",
    },
    "conversationFlow": {
        "conversation_flow_id": "",
        "version": 1,
        "global_prompt": GLOBAL_PROMPT,
        "start_node_id": "start",
        "start_speaker": "agent",
        "model_choice": {"type": "cascading", "model": "gpt-4.1"},
        "knowledge_base_ids": [],
        "knowledge_base_settings": {
            "_comment": "Attach the three KB docs (business_facts.md, faqs.md, service_descriptions.md) "
                        "after creating them in Retell. Add their IDs to knowledge_base_ids above.",
        },
        "tools": TOOLS,
        "nodes": NODES,
    },
}

# -----------------------------------------------------------------------------
# Write
# -----------------------------------------------------------------------------

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(AGENT, f, indent=2, ensure_ascii=False)

print(f"Wrote {OUT_PATH}")
print(f"Nodes: {len(NODES)}")
print(f"Tools: {len(TOOLS)}")
print(f"Global nodes: {sum(1 for n in NODES if 'global_node_setting' in n)}")
