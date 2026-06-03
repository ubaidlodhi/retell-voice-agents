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
        "Live spa service catalog. Returns services[] with id, name, description, "
        "plus EITHER `price` (fixed) OR `pricingVariants[{id, duration, price}]` "
        "(per-duration pricing — caller picks one duration, pass that variant.id "
        "as variantId to book_appointment). Each service may have "
        "`availableAddOns[{id, name, price, duration, groupIds[]}]`. No arguments.",
        {"type": "object", "properties": {}, "required": []},
    ),
    tool(
        "get_staff",
        "get-staff",
        "Live therapist roster. Returns staff[] with id, resourceId, name, email. "
        "Use `resourceId` as the staffId for get_slots and book_appointment. "
        "Names may include gender in parens (e.g. \"Lily (Female)\"). No arguments.",
        {"type": "object", "properties": {}, "required": []},
    ),
    tool(
        "get_contact",
        "get-contact",
        "Look up a returning customer by phone or email. Try phone first "
        "(defaults to {{user_number}}); if not found, ask for the email they "
        "booked under and call again. When found, populates contact_first_name, "
        "contact_last_name, contact_email, contact_phone — use these to skip "
        "re-asking during booking.",
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
        "Available time slots for a service. Pacific time, 10 AM – 8 PM. ALWAYS "
        "narrow by caller prefs before calling: `staffId` for a specific "
        "therapist (smallest response), `timeOfDay` for part-of-day, "
        "`earliestFirst:true` for soonest, `limit` to cap count. Response varies "
        "by `mode`: 'grouped' = `availabilityByDay[date].{morning,afternoon,"
        "evening}[]`; 'earliest_first' = flat `slots[]`. Each slot has "
        "startDate, endDate, scheduleId, plus `availableTherapists` array of "
        "`{name, staffId}` (names from Wix, may include gender). Use the chosen "
        "entry's staffId for book_appointment when caller picks a specific "
        "therapist; omit staffId for 'no preference' (Wix auto-assigns).",
        {
            "type": "object",
            "properties": {
                "serviceId": {"type": "string", "description": "Wix service ID from get_services."},
                "startDate": {"type": "string", "description": "ISO local start, e.g. 2026-05-10 or 2026-05-10T00:00:00."},
                "endDate":   {"type": "string", "description": "ISO local end, e.g. 2026-05-12 or 2026-05-12T23:59:59."},
                "durationInMinutes": {"type": "number", "description": "Required. The chosen session length in minutes (60 / 90 / 120 / 30 / 45). For NEW bookings, use the pricingVariants[].duration the caller picked (parse from strings like '60 min'). For RESCHEDULES, use {{booking_duration_min}}."},
                "staffId":   {"type": "string", "description": "Optional. resourceId from get_staff to filter to one therapist."},
                "timeOfDay": {
                    "type": "string",
                    "enum": ["morning", "afternoon", "evening", "any"],
                    "description": "Optional. morning=10AM-12PM, afternoon=12PM-5PM, evening=5PM-8PM.",
                },
                "earliestFirst": {
                    "type": "boolean",
                    "description": "Optional. True for 'earliest/soonest/anytime' — flattens, sorts ascending, capped at `limit`.",
                },
                "limit": {
                    "type": "number",
                    "description": "Optional. Max slots (default 6, 3 if earliestFirst).",
                },
            },
            "required": ["serviceId", "startDate", "endDate", "durationInMinutes"],
        },
    ),
    tool(
        "book_appointment",
        "book-appointment",
        "Create a booking. REQUIRED: serviceId, variantId (the chosen "
        "pricingVariants[].id from get_services), scheduleId, startDate, "
        "endDate, firstName, lastName, email, phone. Email is mandatory — "
        "Wix uses it for the confirmation AND it's the only key for "
        "reschedule/cancel lookups. NEVER pass a synthesized, default, or "
        "spa-owned email. OPTIONAL: `staffId` — pass when caller picked a "
        "specific therapist, OMIT for 'no preference' (Wix auto-assigns); "
        "`addOns` — array of `{id, groupId}` objects, both required per "
        "entry, use groupIds[0] from the SAME service get_services returned.",
        {
            "type": "object",
            "properties": {
                "serviceId":  {"type": "string"},
                "variantId":  {"type": "string", "description": "pricingVariants[].id from get_services for the chosen duration."},
                "staffId":    {"type": "string", "description": "Optional. Pass for specific therapist; omit for 'no preference'."},
                "scheduleId": {"type": "string"},
                "startDate":  {"type": "string", "description": "ISO local start."},
                "endDate":    {"type": "string", "description": "ISO local end."},
                "firstName":  {"type": "string"},
                "lastName":   {"type": "string"},
                "email":      {"type": "string"},
                "phone":      {"type": "string", "description": "E.164."},
                "addOns":     {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id":      {"type": "string"},
                            "groupId": {"type": "string", "description": "Use groupIds[0] from the same service."},
                        },
                        "required": ["id", "groupId"],
                    },
                    "description": "Optional. Each entry requires id + groupId only.",
                },
            },
            "required": ["serviceId", "variantId", "scheduleId",
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
        "Cancel an existing booking. REQUIRED: bookingId AND revision — Wix "
        "V2 cancellation rejects requests without the revision number. Get "
        "both from get_booking first ({{booking_id}} and {{booking_revision}}).",
        {
            "type": "object",
            "properties": {
                "bookingId": {"type": "string"},
                "revision":  {"type": "string", "description": "Revision number from get_booking — required by Wix."},
            },
            "required": ["bookingId", "revision"],
        },
        response_variables={
            "cancel_success_flag": "$.cancelFlag",
            "cancel_success":      "$.success",
            "cancel_status":       "$.status",
        },
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
            "reschedule_success_flag": "$.rescheduleFlag",
            "reschedule_success":      "$.success",
            "new_start":               "$.newStartDate",
            "new_end":                 "$.newEndDate",
            "new_day_of_week":         "$.newDayOfWeek",
        },
    ),
    tool(
        "get_booking",
        "get-booking",
        "Look up an existing booking by email (primary) or bookingId. Ask the "
        "caller for the email they booked under, read it back to confirm, then "
        "call. Returns up to 5 bookings with bookingId, revision, serviceId, "
        "scheduleId, staffId, startDate, endDate, plus contact fields — these "
        "populate variables for downstream cancel/reschedule.",
        {
            "type": "object",
            "properties": {
                "bookingId": {"type": "string", "description": "If the caller knows their booking ID."},
                "email":     {"type": "string", "description": "Email address used for the original booking. Read back letter-by-letter for the local part; speak common domains naturally before calling."},
            },
            "required": [],
        },
        response_variables={
            "lookup_found_flag":      "$.foundFlag",
            "bookings_count":         "$.count",
            "booking_id":             "$.bookings[0].bookingId",
            "booking_revision":       "$.bookings[0].revision",
            "booking_service_id":     "$.bookings[0].serviceId",
            "booking_service_name":   "$.bookings[0].serviceName",
            "booking_schedule_id":    "$.bookings[0].scheduleId",
            "booking_staff_id":       "$.bookings[0].staffId",
            "booking_staff_name":     "$.bookings[0].staffName",
            "booking_start":          "$.bookings[0].startDate",
            "booking_end":            "$.bookings[0].endDate",
            "booking_day_of_week":    "$.bookings[0].dayOfWeek",
            "booking_duration_min":   "$.bookings[0].durationMinutes",
            "booking_within_24h_flag":"$.bookings[0].withinCancellationWindowFlag",
            "booking_first_name":     "$.bookings[0].firstName",
            "booking_last_name":      "$.bookings[0].lastName",
            "booking_phone":          "$.bookings[0].phone",
        },
    ),
    tool(
        "flag_callback",
        "flag-callback",
        "Send Nicky an email when the agent can't answer or the caller insists "
        "on a human. Use this instead of warm-transferring (Nicky is in session "
        "and can't pick up). Always include a short reason summary so she can "
        "call back prepared.",
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
            "FIRST TURN ONLY — warmly, in ONE breath:\n"
            "\"Hi, this is Aria from Sage and Willow Spa. Just to let you know, "
            "this call is recorded for quality purpose. How can I help you "
            "today?\"\n\n"
            "If the caller's reply doesn't fit an obvious intent (book / "
            "manage / FAQ / callback), do NOT repeat the greeting or recording "
            "disclosure. Re-prompt SHORT and varied — e.g. \"Sorry, just to "
            "make sure — are you calling to book, change an appointment, or "
            "something else?\""
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
    "name": "Book — Service Question",
    "instruction": {
        "type": "prompt",
        "text": (
            "Ask the caller which type of massage they're interested in. Read the "
            "menu in ONE breath:\n\n"
            "\"What type of massage are you interested in? We offer Signature, "
            "Swedish, Deep Tissue, Hot Stone, Prenatal, Lymphatic Drainage, and a "
            "thirty-minute Focus session. If you're not sure, I can describe a few "
            "for you.\"\n\n"
            "If the caller asks for descriptions, give a one-sentence description "
            "of two or three relevant options based on what they hint at (stress, "
            "back pain, pregnancy, etc.) and let them pick.\n\n"
            "DO NOT call any tool here. DO NOT ask about date, add-ons, name, "
            "returning vs new, or anything else — that all happens after they "
            "name a service."
        ),
    },
    "edges": [
        equation_edge(
            "e-book-collect-already-booked",
            [{"left": "{{new_booking_id}}", "operator": "exists"}],
            "post-task",
        ),
        edge(
            "e-book-collect-picked",
            "Caller has named a specific service (Swedish, Deep Tissue, Hot Stone, "
            "Signature, Prenatal, Lymphatic Drainage, Focus, Couples, or any other "
            "spa service from the menu).",
            "book-services-fetch",
        ),
        edge(
            "e-book-collect-cancel",
            "Caller changed their mind and no longer wants to book.",
            "post-task",
        ),
    ],
    "display_position": {"x": 500, "y": 100},
})

# Deterministic get_services call — NOT left to the subagent's discretion.
# Earlier the subagent (LLM decides whether to call tools) skipped
# get_services because the Knowledge Base already gave it descriptions,
# prices, and durations — but the KB has NO machine IDs, so the agent
# fabricated a serviceId for get_slots and the call failed. A function
# node always executes its tool on entry: by the time book-subagent
# starts, the real catalog (serviceId, variantId, pricingVariants,
# availableAddOns) is guaranteed to be in context.
add({
    "id": "book-services-fetch",
    "type": "function",
    "name": "Book — Fetch Service Catalog",
    "tool_id": "get_services",
    "tool_type": "local",
    "wait_for_result": True,
    "edges": [],
    "always_edge": always_edge("e-book-services-fetch-after", "book-subagent"),
    "display_position": {"x": 700, "y": 100},
})

add({
    "id": "book-subagent",
    "type": "subagent",
    "name": "Book — Tool-Driven Booking",
    "instruction": {
        "type": "prompt",
        "text": (
            "Handle a NEW booking. Caller just named a service. Pacific time, "
            "open 10 AM–8 PM daily (closed Christmas + Thanksgiving).\n\n"
            "DATA SOURCE RULE (critical):\n"
            "  get_services has ALREADY been called — its result (the full "
            "catalog with real serviceId, variantId, pricingVariants, "
            "availableAddOns) is in your context. Use ONLY those values. "
            "The Knowledge Base has service descriptions for ANSWERING "
            "QUESTIONS only — it has NO IDs. NEVER pull serviceId, "
            "variantId, scheduleId, prices-to-book, or add-ons from the KB "
            "or from memory. NEVER fabricate an ID — if a required ID isn't "
            "in the get_services result, you cannot proceed; offer a "
            "callback instead. (Only re-call get_services if its result is "
            "genuinely not in your context.)\n\n"
            "STEP 1 — Service + variant.\n"
            "  Find the named service in the get_services result.\n"
            "  • Has `pricingVariants` → read durations in ONE sentence (e.g. "
            "\"Swedish comes in three lengths — one hour for ninety dollars, an "
            "hour and a half for one hundred forty, or two hours for two hundred. "
            "Which would you like?\"). Capture chosen variant.id as variantId.\n"
            "  • Single `price` → confirm: \"Got it — that's [price] for "
            "[duration].\"\n"
            "  No add-ons here.\n\n"
            "STEP 2 — Add-on offer (one soft turn).\n"
            "  HARD RULE: if this service's `availableAddOns` is missing, "
            "empty, or absent — SKIP this step entirely. Do NOT mention "
            "add-ons, do NOT ask \"any add-ons?\", do NOT name examples. "
            "NEVER invent or recall add-ons from memory (no aromatherapy / "
            "hot towel / CBD / etc.) — every name and price MUST come from "
            "the current get_services response. Fabricated add-ons break "
            "book_appointment.\n"
            "  When `availableAddOns` IS present: read each entry's actual "
            "`name` and `price` from the array, framed as additions (never "
            "\"we offer\"). Example shape only — substitute real values: "
            "\"Would you like to add [name] for [price], or [name] for "
            "[price] — or skip add-ons?\"\n"
            "  Capture each chosen add-on as `{id, groupId}`. groupId = "
            "groupIds[0] from this service's availableAddOns (same id has "
            "different groupIds per service — never mix). One re-prompt "
            "max, then move on.\n\n"
            "STEP 3 — Availability + slot pick.\n"
            "  Ask ONE PER TURN, in this order:\n"
            "    a) THERAPIST: \"Any preference on therapist — male, female, or "
            "no preference?\"\n"
            "       - Name (\"Lily\") → get_staff to resolve staffId, pass to "
            "get_slots.\n"
            "       - Gender, ONE match → use that staffId.\n"
            "       - Gender, MULTIPLE matches → ask which by name.\n"
            "       - No preference → omit staffId entirely.\n"
            "    b) DAY: \"What day were you thinking?\"\n"
            "    c) TIME OF DAY (only if more narrowing needed): "
            "\"Morning, afternoon, or evening — or earliest available?\" → pass "
            "timeOfDay, or earliestFirst:true + limit:3.\n\n"
            "  Call get_slots. ALWAYS pass durationInMinutes — the duration "
            "the caller chose in STEP 1 (parse from pricingVariants[].duration "
            "like \"60 min\" → 60, or from the service's single duration if "
            "no variants). REQUIRED by Wix.\n"
            "  DATE WINDOW:\n"
            "    • Specific day → startDate = endDate = that day.\n"
            "    • \"Earliest\" with no day → today + 5 days, earliestFirst:true.\n"
            "    • Range (\"this weekend\") → 3–5 day window.\n"
            "  Each slot has `dayOfWeek`, `localDate`, `time`, and "
            "`availableTherapists: [{name, staffId}]`. ALWAYS use the slot's "
            "`dayOfWeek` field for the weekday — never compute it yourself. "
            "Read back two or three times:\n"
            "    • Empty → read time only.\n"
            "    • One entry → mention by name (\"ten thirty AM with Lily\").\n"
            "    • Multiple → offer the times, then ask preference once "
            "(\"I have ten thirty AM, eleven AM, or eleven thirty AM. We have "
            "Rocky and Lily working — any preference?\").\n"
            "  Empty result → widen ONCE (drop staffId, then timeOfDay). Still "
            "empty → offer flag_callback.\n\n"
            "  When caller picks a slot AND a specific therapist (by name or "
            "gender-resolved), capture that entry's staffId from "
            "availableTherapists for STEP 5. \"No preference\" → omit staffId; "
            "Wix auto-assigns.\n\n"
            "STEP 4 — Contact.\n"
            "  Ask: \"Have you been to Sage and Willow Spa before, or is this "
            "your first visit?\"\n"
            "  RETURNING → silently call get_contact with phone={{user_number}}.\n"
            "    • Found → \"Great, I found your record on file — "
            "{{contact_first_name}} {{contact_last_name}}, email "
            "{{contact_email}}. Use that for the booking?\" (jump to PHONE on "
            "yes; update only the field they want to change otherwise).\n"
            "    • Not found → DON'T mention it; fall through to NEW.\n"
            "  NEW (or not-found): one per turn — first+last name, then "
            "email. Email is REQUIRED (Wix sends the confirmation there and "
            "we look up by email for any future changes — phone lookup isn't "
            "supported). If caller hesitates, say so briefly and re-ask. If "
            "they truly refuse, route to a callback instead of inventing or "
            "using a spa-owned address.\n"
            "  PHONE (always): \"Can we use the number you're calling from, or "
            "another preferred number?\" Default to {{user_number}}.\n\n"
            "STEP 5 — Readback + book (MANDATORY).\n"
            "  Read in one breath: service + duration, day/date/time, therapist "
            "(if any), add-ons (or \"no add-ons\"), total price, email, phone, "
            "and one-time policy line \"We ask for twenty-four hours' notice if "
            "you need to cancel or reschedule.\" Then ask: \"Should I go ahead "
            "and book it?\"\n"
            "  WAIT for explicit yes. Then call book_appointment. variantId is "
            "REQUIRED — never skip. Pass staffId only when caller picked a "
            "specific therapist; omit for no-preference. Pass addOns as the "
            "captured array from STEP 2.\n\n"
            "GENERAL\n"
            "Failure or caller wants a human → call flag_callback.\n"
            "Inline FAQ (location, hours, parking, what to wear) → answer in 1–2 "
            "sentences from KB, then return to where you were. Don't make caller "
            "repeat anything.\n"
            "On book_appointment success → stop talking, next node delivers "
            "confirmation. Never read the bookingId."
        ),
    },
    "tool_ids": ["get_contact", "get_services", "get_staff", "get_slots", "book_appointment", "flag_callback"],
    "edges": [
        # Prompt-based, NOT equation. Retell's equation evaluation of
        # response_variables ({{new_booking_id}}) right after a tool call is
        # unreliable — the variable isn't loaded into the equation context
        # yet, so the edge silently never fires and the subagent gets stuck
        # free-form chatting instead of transitioning to book-success. The
        # subagent's LLM DOES have the tool result in its context window, so
        # a prompt edge matches it correctly. Same fix as reschedule-subagent.
        edge(
            "e-book-subagent-success",
            "The book_appointment tool just returned success — the booking "
            "was created (the result has a bookingId and success/confirmed "
            "is true).",
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
            "Caller wants to cancel, reschedule, or check an existing booking. "
            "Get the email used at booking — that's our lookup key.\n\n"
            "TURN 1: \"Sure — I can help with that. What email did you use "
            "when you booked?\"\n"
            "TURN 2: read the email back per the global email pronunciation "
            "rules and ask \"Did I get that right?\" — then WAIT for the "
            "caller's reply. On explicit yes, transition silently (don't say "
            "\"let me pull that up\" — the lookup tool plays a filler line "
            "on its own). On no/correction, re-ask the email once.\n\n"
            "Don't ask for phone, name, or booking ID."
        ),
    },
    "edges": [
        edge(
            "e-manage-collect-ready",
            "The caller has explicitly confirmed their email address is "
            "correct (\"yes\", \"that's right\", \"correct\", \"yep\"). "
            "Does NOT fire on the caller's first reply (the email itself) "
            "— Aria must read it back and the caller must confirm.",
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
    "always_edge": always_edge("e-manage-fetch-after", "manage-result"),
    "display_position": {"x": 900, "y": 400},
})

# Merged "router + action prompt + not-found" into ONE node. Earlier we had
# three separate conversation nodes each speaking one short line — every split
# forced a dead-air caller turn ("Got it — I found your booking." → wait → ...).
# This node handles ALL three lookup outcomes in a single first turn, reading
# the booking descriptor AND asking the action together when a single booking
# is found.
add({
    "id": "manage-result",
    "type": "conversation",
    "name": "Manage — Result + Action",
    "instruction": {
        "type": "prompt",
        "text": (
            "ONE turn — never a separate \"I found your booking\" line.\n\n"
            "Branch by {{lookup_found_flag}} and {{bookings_count}}:\n\n"
            "• NOT FOUND ({{lookup_found_flag}} != \"yes\"):\n"
            "  \"Hmm, I'm not finding any upcoming appointments under that "
            "email. Want me to book you something new, or is there anything "
            "else I can help with?\"\n"
            "  (Don't suggest the caller's email is wrong — be diplomatic.)\n\n"
            "• ONE BOOKING ({{bookings_count}} == \"1\"):\n"
            "  Read the FULL descriptor + ask the action in ONE breath. Use "
            "{{booking_duration_min}}, {{booking_service_name}}, "
            "{{booking_staff_name}}, {{booking_day_of_week}}, and the "
            "calendar date/time from {{booking_start}}. NEVER compute the "
            "weekday — always use dayOfWeek. Drop the \"with X\" if staff "
            "name is empty.\n"
            "  - If caller stated their action earlier (cancel/reschedule) → "
            "CONFIRM: \"Got it — your {{booking_duration_min}}-minute "
            "{{booking_service_name}} with {{booking_staff_name}} on "
            "{{booking_day_of_week}}, [date] at [time]. Just to confirm, "
            "you'd like to [cancel | reschedule] this appointment?\"\n"
            "  - Otherwise ASK: \"Got it — your [descriptor]. Would you like "
            "to cancel, reschedule, or just check details?\"\n\n"
            "• MULTIPLE BOOKINGS ({{bookings_count}} != \"1\" AND not zero):\n"
            "  TURN 1 — list each with descriptor (use each booking's "
            "dayOfWeek), ask which. e.g. \"I see two — your one-hour Deep "
            "Tissue with Rocky on Friday, May fifteenth at ten AM, and your "
            "Swedish with Lily on Monday, May eighteenth at one PM. Which "
            "one?\"\n"
            "  TURN 2 (after caller picks) — confirm the picked one + ask "
            "action: \"Got it — your [picked descriptor]. Cancel or "
            "reschedule?\"\n\n"
            "Phrase as a DESCRIPTOR (\"your Friday appointment\"), never "
            "\"reschedule your appointment on Friday\" (sounds like moving "
            "TO Friday). NEVER read booking IDs."
        ),
    },
    "edges": [
        # 1-booking and multi-booking selection outcomes
        edge(
            "e-manage-cancel",
            "Caller wants to CANCEL the (selected) appointment.",
            "cancel-reason",
        ),
        edge(
            "e-manage-reschedule",
            "Caller wants to RESCHEDULE, move, or change the time of the (selected) appointment.",
            "reschedule-subagent",
        ),
        edge(
            "e-manage-info",
            "Caller just wanted to confirm details and isn't changing anything.",
            "post-task",
        ),
        # Not-found outcomes
        edge(
            "e-manage-nf-book",
            "After being told no booking was found, caller wants to book a new appointment.",
            "book-collect",
        ),
        edge(
            "e-manage-nf-faq",
            "After being told no booking was found, caller has a general question instead.",
            "faq-handler",
        ),
        edge(
            "e-manage-nf-no",
            "After being told no booking was found, caller said no, that's all, goodbye, or otherwise indicated they're done.",
            "close-call",
        ),
    ],
    "display_position": {"x": 1300, "y": 400},
})

# --- Cancel ---

add({
    "id": "cancel-reason",
    "type": "conversation",
    "name": "Cancel — Ask Reason + Offer Reschedule",
    "instruction": {
        "type": "prompt",
        "text": (
            "TWO-TURN flow — DO NOT transition after only Turn 1.\n\n"
            "TURN 1 (first time here) — ask the reason AND signal the "
            "reschedule off-ramp upfront so the caller knows it's an option:\n"
            "  \"Got it — mind if I ask what came up? If it's a timing thing "
            "I might be able to move it instead.\"\n\n"
            "TURN 2 (after caller answers) — based on their reason, ALWAYS "
            "give them a binary choice. Pick ONE phrasing:\n"
            "  • TIMING reason (busy, conflict, work, family, urgent, that "
            "day, can't make it, schedule, kids, travel, etc.):\n"
            "    \"Sounds like a timing thing — want me to find another "
            "time, or are you set on canceling?\"\n"
            "  • FIRM reason (sick, illness, injured, no longer want it):\n"
            "    \"Totally understand. Just to confirm, go ahead and cancel?\"\n"
            "  • VAGUE / no reason given (\"personal\", \"just need to\"):\n"
            "    \"No problem. Would you rather reschedule, or cancel?\"\n\n"
            "DO NOT transition until the caller answers Turn 2. Capture the "
            "reason internally for the within-24h callback note. NEVER skip "
            "Turn 2 — the caller MUST hear an explicit reschedule-vs-cancel "
            "choice before we proceed."
        ),
    },
    "edges": [
        edge(
            "e-cancel-reason-reschedule",
            "After Aria explicitly offered to find another time / reschedule, "
            "the caller agreed — e.g. \"yes\", \"reschedule\", \"find another "
            "time\", \"move it\", \"sure let's try\". Does NOT fire merely "
            "because the caller stated a timing reason without yet hearing "
            "the offer.",
            "reschedule-subagent",
            examples=[
                {"id": "fe-cancel-reschedule-1", "destination_node_id": "reschedule-subagent",
                 "transcript": [
                     {"role": "agent", "content": "Sounds like a timing thing — want me to find another time, or are you set on canceling?"},
                     {"role": "user", "content": "yeah let's try another time"},
                 ]},
                {"id": "fe-cancel-reschedule-2", "destination_node_id": "reschedule-subagent",
                 "transcript": [
                     {"role": "agent", "content": "No problem. Would you rather reschedule, or cancel?"},
                     {"role": "user", "content": "reschedule please"},
                 ]},
            ],
        ),
        edge(
            "e-cancel-reason-walkaway",
            "Caller changed their mind and wants to keep the booking as-is "
            "(\"never mind\", \"actually keep it\", \"forget it\").",
            "post-task",
        ),
        edge(
            "e-cancel-reason-proceed",
            "After Aria explicitly offered the reschedule-vs-cancel choice "
            "(Turn 2), the caller chose to cancel — \"cancel\", \"go ahead "
            "and cancel\", \"I'm set on canceling\", \"yes cancel\". Does "
            "NOT fire on the caller's FIRST reply (a stated reason); the "
            "agent must complete Turn 2 first.",
            "cancel-policy-router",
            examples=[
                {"id": "fe-cancel-proceed-1", "destination_node_id": "cancel-policy-router",
                 "transcript": [
                     {"role": "agent", "content": "Sounds like a timing thing — want me to find another time, or are you set on canceling?"},
                     {"role": "user", "content": "no just cancel it"},
                 ]},
                {"id": "fe-cancel-proceed-2", "destination_node_id": "cancel-policy-router",
                 "transcript": [
                     {"role": "agent", "content": "Totally understand. Just to confirm, go ahead and cancel?"},
                     {"role": "user", "content": "yes please"},
                 ]},
            ],
        ),
    ],
    "display_position": {"x": 2100, "y": 100},
})

add({
    # Silent branch — no speech, no dead air. Routes directly on the
    # server-computed within-24h flag from get_booking.
    "id": "cancel-policy-router",
    "type": "branch",
    "name": "Cancel — 24-Hour Policy Router",
    "edges": [
        equation_edge(
            "e-cancel-policy-within",
            [{"left": "{{booking_within_24h_flag}}", "operator": "==", "right": "yes"}],
            "cancel-within-window",
        ),
    ],
    "else_edge": else_edge("e-cancel-policy-outside", "cancel-confirm"),
    "display_position": {"x": 2100, "y": 250},
})

add({
    "id": "cancel-within-window",
    "type": "subagent",
    "name": "Cancel — Within 24h (auto-callback)",
    "instruction": {
        "type": "prompt",
        "text": (
            "The booking is within twenty-four hours of starting, so we don't "
            "process the cancellation directly. Two things this turn:\n\n"
            "1. Say warmly: \"I've noted this and someone from the team will "
            "reach out about options. Anything else I can help with?\"\n\n"
            "2. In the same turn, call flag_callback with:\n"
            "   • reason: \"Within-24h cancellation request\"\n"
            "   • callerName: {{booking_first_name}} {{booking_last_name}}\n"
            "   • callerPhone: {{user_number}}\n"
            "   • questionDetail: a one-line summary including the caller's "
            "stated cancellation reason (from the prior turn) AND the booking "
            "details — {{booking_service_name}}, {{booking_start}}, "
            "staff: {{booking_staff_name}}, bookingId: {{booking_id}}."
        ),
    },
    "tool_ids": ["flag_callback"],
    # This node asks "anything else?" itself, so it must OWN the routing —
    # route directly to close-call / flows like cancel-success does. Routing
    # into post-task here caused a hung call: post-task would see the question
    # was already asked, say "Got it", then wait for a caller turn that never
    # comes (the caller already answered).
    "edges": [
        edge(
            "e-cancel-within-no",
            "Caller said no, that's all, thanks, goodbye, or otherwise "
            "indicated they're done with the call.",
            "close-call",
        ),
        edge(
            "e-cancel-within-book",
            "Caller wants to book a new appointment.",
            "book-collect",
        ),
        edge(
            "e-cancel-within-manage",
            "Caller wants to manage another existing booking.",
            "manage-collect",
        ),
        edge(
            "e-cancel-within-faq",
            "Caller has another general question.",
            "faq-handler",
        ),
    ],
    "display_position": {"x": 2500, "y": 100},
})

add({
    "id": "cancel-confirm",
    "type": "conversation",
    "name": "Cancel — Confirm (>24h)",
    "instruction": {
        "type": "prompt",
        "text": (
            "Confirm the cancellation in ONE short line. Use enriched booking "
            "details for clarity:\n"
            "  \"Just to confirm — cancel your "
            "{{booking_duration_min}}-minute {{booking_service_name}} with "
            "{{booking_staff_name}} on {{booking_day_of_week}}, "
            "[calendar date] at [time]? Sure?\"\n\n"
            "Use {{booking_day_of_week}} for the weekday (never compute it). "
            "Calendar date + time come from {{booking_start}}. If staff name "
            "is empty, drop that phrase. Yes → proceed; hesitation / "
            "reschedule → route accordingly."
        ),
    },
    "edges": [
        edge(
            "e-cancel-yes",
            "Caller has explicitly confirmed cancellation — yes, go ahead, "
            "please cancel, or similar firm affirmation.",
            "cancel-execute",
        ),
        edge(
            "e-cancel-reschedule-instead",
            "Caller decided to reschedule instead of canceling.",
            "reschedule-subagent",
        ),
        edge(
            "e-cancel-back-out",
            "Caller decided to keep the booking after all.",
            "post-task",
        ),
    ],
    "display_position": {"x": 2500, "y": 250},
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
            "Check {{cancel_success_flag}}:\n"
            "• \"yes\" → \"All set — your appointment is canceled. Anything else I can help with?\"\n"
            "• anything else → \"Hmm, that didn't go through on my end. I'll have someone reach out. Anything else?\"\n\n"
            "The flag is the source of truth — don't default to the success line."
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
            "Reschedule an existing booking. Use {{booking_id}}, "
            "{{booking_revision}}, {{booking_service_id}}, {{booking_schedule_id}}, "
            "{{booking_staff_id}}. For multi-booking lookups where caller picked "
            "a non-most-recent one, pull THAT booking's fields from get_booking "
            "context (variables default to most-recent).\n\n"
            "STAFFID RULE: must be a 36-char GUID from the booking's `staffId` "
            "field. NEVER use scheduleId/serviceId. If the selected booking has "
            "no staffId (any-resource booking), OMIT staffId entirely from "
            "get_slots and reschedule_booking.\n\n"
            "STEP 1 — Ask: \"What day were you thinking of moving it to?\" "
            "Parse the caller's reply for BOTH the day and (if given) an "
            "exact time. Capture:\n"
            "  • dayTarget — the day they named.\n"
            "  • timeTarget — exact time IF the caller said one (\"one PM\", "
            "\"three thirty\") OR said \"same time\" / \"same as my current\" "
            "(then use the H:MM from {{booking_start}}). Otherwise null.\n\n"
            "STEP 2 — Time-of-day question. SKIP this step entirely if "
            "timeTarget is set. Otherwise ask: \"Morning, afternoon, or "
            "evening — or earliest available?\" Map to timeOfDay, or "
            "earliestFirst:true + limit:3.\n"
            "  Therapist: default to {{booking_staff_id}} for continuity "
            "(don't ask, don't call get_staff). Only drop staffId if caller "
            "explicitly asks for a different person or says \"anyone\".\n\n"
            "STEP 3 — Call get_slots with serviceId={{booking_service_id}}, "
            "durationInMinutes={{booking_duration_min}}, + filters. "
            "durationInMinutes is REQUIRED — Wix uses it to return slots of "
            "the right length. DATE WINDOW: specific day → startDate = "
            "endDate = that day.\n"
            "  Reading slots back:\n"
            "  • timeTarget set (caller asked for an exact time):\n"
            "    - Find the slot in the response whose `time` matches "
            "timeTarget. If present → confirm JUST that slot: \"Good news — "
            "Lily has [time] open on [day]. Want me to move it there?\" "
            "DO NOT mention other times.\n"
            "    - If exact time not available → say so and offer the single "
            "closest open time: \"Hmm, [time] isn't open — the closest is "
            "[closest]. Want that, or pick a different time?\"\n"
            "  • timeTarget NOT set (caller gave time-of-day only):\n"
            "    Read back two or three options as before; let caller pick.\n"
            "  Empty result → widen ONCE (drop staffId, then timeOfDay).\n\n"
            "STEP 4 — Confirm: \"To confirm — moving you to [new day, date] "
            "at [new time]. Sound good?\"\n\n"
            "STEP 5 — On yes, call reschedule_booking with the new slot's "
            "serviceId, scheduleId, staffId, startDate, endDate + original "
            "bookingId={{booking_id}}, revision={{booking_revision}}.\n\n"
            "Failure → call flag_callback. Pacific time, 10 AM–8 PM only."
        ),
    },
    "tool_ids": ["get_slots", "reschedule_booking", "flag_callback"],
    "edges": [
        # Prompt-based instead of equation: Retell's branch/equation evaluation
        # of response_variables right after a tool call is unreliable. The
        # subagent's LLM has the tool result in its context window though, so
        # a prompt edge can match it correctly.
        edge(
            "e-reschedule-success",
            "The reschedule_booking tool just returned success — the booking "
            "was successfully moved to the new slot (rescheduleFlag is \"yes\").",
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
            "Say ONE short line confirming the new time, using "
            "{{new_day_of_week}} for the weekday and {{new_start}} for the "
            "date and time. NEVER compute the weekday yourself.\n\n"
            "Example: \"Done — you're now booked for {{new_day_of_week}}, "
            "[calendar date] at [time].\"\n\n"
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
            "Answer a general spa question using the attached knowledge base "
            "(hours, location, parking, gift cards, payments, prenatal, late "
            "arrival, gratuity, insurance, walk-ins, cancellation policy) and "
            "get_services for service-specific details (prices, durations, "
            "add-ons).\n\n"
            "Answer in 1–2 sentences. Don't read prices/services like a menu — "
            "just the relevant ones.\n"
            "If the answer isn't in KB or get_services and you're not "
            "confident, DON'T guess — offer a callback: \"That's a good "
            "question — let me have someone reach out so you get the right "
            "answer.\"\n"
            "After answering: \"Anything else I can help with?\""
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
            "Collect callback info ONE QUESTION PER TURN:\n"
            "1. Caller's name (skip if known from earlier).\n"
            "2. Best phone — default to {{user_number}}, confirm; only re-ask "
            "if they want a different number.\n"
            "3. One-sentence summary of what they need help with.\n\n"
            "After all three: \"Got it — I'll have her reach out as soon as "
            "she's free.\" Then stop.\n"
            "Don't promise a specific call-back time — Nicky calls when she's "
            "out of session."
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
            "NEVER stay silent or respond NO_RESPONSE_NEEDED here — always "
            "ask the line so the caller has a clear prompt to respond to."
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
    "agent_name": "Aria — Sage & Willow Spa - V26",
    "language": ["en-US", "es-ES", "en-IN", "es-419", "en-GB", "en-AU"],
    # voice_id / voice_speed / post_call_analysis_model below were changed by
    # the client in the Retell dashboard — synced here so rebuilds don't revert.
    "voice_id": "custom_voice_573dab78e535ca398ccb542f7e",
    "voice_temperature": 0.7,
    "voice_speed": 1,
    "max_call_duration_ms": 1800000,
    "interruption_sensitivity": 0.9,
    "responsiveness": 1,
    "begin_message_delay_ms": 800,
    "ring_duration_ms": 30000,
    "normalize_for_speech": True,
    "stt_mode": "accurate",
    "denoising_mode": "noise-and-background-speech-cancellation",
    "data_storage_setting": "everything",
    "post_call_analysis_model": "gpt-4.1-mini",
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
            "name": "language_used",
            "type": "enum",
            "choices": ["english", "spanish", "mixed"],
            "description": "Primary language of the conversation.",
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
# Enable the typing-sound UX cue on every tool-calling node — function nodes
# (deterministic tool calls) and subagent nodes (LLM-woven tool calls). The
# sound plays while the tool executes so the caller hears "the system is
# working" rather than dead silence. Safe to apply uniformly: nodes that
# don't actually invoke a tool will just ignore it.
for _n in NODES:
    if _n["type"] in ("function", "subagent"):
        _n["enable_typing_sound"] = True

# -----------------------------------------------------------------------------
# Write
# -----------------------------------------------------------------------------

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(AGENT, f, indent=2, ensure_ascii=False)

print(f"Wrote {OUT_PATH}")
print(f"Nodes: {len(NODES)}")
print(f"Tools: {len(TOOLS)}")
print(f"Global nodes: {sum(1 for n in NODES if 'global_node_setting' in n)}")
