"""
Build script for the Sage & Willow Spa SINGLE-PROMPT Retell agent.

Run:  py -X utf8 _build_single_prompt_agent.py

Outputs: aria_single_prompt.json

Notes
-----
- This is the single-prompt (retell-llm) variant of the agent. It runs the
  whole call from one prompt (system_prompt_single.md) and exposes the tools
  inline — no node graph. Created because the conversation-flow version was
  too rigid for the spa receptionist use case (caller pricing questions got
  stuck inside collection nodes).
- Tools wire to the SAME n8n webhook used by the conversation-flow agent
  (https://automation.aiemply.com/webhook/retell-wix) — the n8n "Parse Retell
  Payload" node accepts either args-at-root or nested-args shape and reads
  the tool name from the `tool` header. No n8n changes needed.
- Voice + post-call analysis fields mirror the conversation-flow agent so the
  client's existing pipelines keep working.
"""

from __future__ import annotations
import json
from pathlib import Path

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------

OUT_PATH = Path(__file__).parent / "aria_single_prompt.json"
PROMPT_PATH = Path(__file__).parent / "system_prompt_single.md"
N8N_BASE_URL = "https://automation.aiemply.com/webhook/retell-wix"
EXEC_MSG = "Just a moment please, this will only take a second."


# -----------------------------------------------------------------------------
# Tool helper
# -----------------------------------------------------------------------------

def tool(name, header, description, parameters, response_variables=None):
    t = {
        "type": "custom",
        "name": name,
        "description": description,
        "method": "POST",
        "url": N8N_BASE_URL,
        "headers": {"tool": header},
        "timeout_ms": 120000,
        "speak_during_execution": True,
        "speak_after_execution": True,
        "execution_message_type": "static_text",
        "execution_message_description": EXEC_MSG,
        "parameters": parameters,
    }
    if response_variables:
        t["response_variables"] = response_variables
    return t


# -----------------------------------------------------------------------------
# Tools (same 9 webhook tools as the conversation-flow agent + built-in end_call)
# -----------------------------------------------------------------------------

CUSTOM_TOOLS = [
    tool(
        "get_services",
        "get-services",
        "Live service catalog with IDs, durations, prices, and add-ons. Call "
        "before quoting any price, before get_slots, and before book_appointment.",
        {"type": "object", "properties": {}, "required": []},
    ),
    tool(
        "get_staff",
        "get-staff",
        "Live therapist roster. Call when caller asks about specific therapists. "
        "Use the returned `resourceId` as `staffId` downstream.",
        {"type": "object", "properties": {}, "required": []},
    ),
    tool(
        "get_contact",
        "get-contact",
        "Returning-client lookup. Call when caller says they've been here before. "
        "Try phone first (defaults to {{user_number}}); fall back to email if not found.",
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
        "Available time slots. Narrow with staffId, timeOfDay, earliestFirst, "
        "or limit when the caller's request implies it. Returns slots with "
        "startDate, endDate, scheduleId, and availableTherapists[{name, staffId}]. "
        "Use the chosen entry's staffId for book_appointment; omit if caller has "
        "no preference (Wix auto-assigns).",
        {
            "type": "object",
            "properties": {
                "serviceId": {"type": "string", "description": "Wix service ID from get_services."},
                "startDate": {"type": "string", "description": "ISO local start, e.g. 2026-05-10."},
                "endDate":   {"type": "string", "description": "ISO local end, e.g. 2026-05-12."},
                "durationInMinutes": {
                    "type": "number",
                    "description": "Required. Session length: 60, 90, 120, 30, or 45. New bookings: the duration caller picked. Reschedules: {{booking_duration_min}}.",
                },
                "staffId":   {"type": "string", "description": "Optional. resourceId from get_staff."},
                "timeOfDay": {
                    "type": "string",
                    "enum": ["morning", "afternoon", "evening", "any"],
                    "description": "Optional. morning=10AM-12PM, afternoon=12PM-5PM, evening=5PM-8PM.",
                },
                "earliestFirst": {"type": "boolean", "description": "Optional. True when caller wants the soonest opening."},
                "limit":         {"type": "number",  "description": "Optional. Max slots (default 6, 3 if earliestFirst)."},
            },
            "required": ["serviceId", "startDate", "endDate", "durationInMinutes"],
        },
    ),
    tool(
        "book_appointment",
        "book-appointment",
        "Create a booking. Only call after caller has confirmed slot + name + "
        "email + phone. Email is mandatory — Wix uses it for the confirmation "
        "AND as the only lookup key for future cancel/reschedule. Never substitute "
        "a spa-owned email; offer a callback if caller declines. Pass addOns only "
        "if get_services returned them for this service.",
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
                "addOns": {
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
            "required": ["serviceId", "variantId", "scheduleId", "startDate",
                         "endDate", "firstName", "lastName", "email", "phone"],
        },
        response_variables={
            "new_booking_id":    "$.bookingId",
            "booking_confirmed": "$.confirmed",
            "confirmed_start":   "$.startDate",
            "confirmed_end":     "$.endDate",
            "booking_success":   "$.success",
        },
    ),
    tool(
        "get_booking",
        "get-booking",
        "Look up an existing booking by email. Confirm the email letter-by-letter "
        "before calling. Returns up to 5 bookings with bookingId, revision, "
        "dayOfWeek, serviceName, staffName, durationMinutes, "
        "withinCancellationWindowFlag. Trust the server's dayOfWeek.",
        {
            "type": "object",
            "properties": {
                "bookingId": {"type": "string", "description": "If the caller knows their booking ID."},
                "email":     {"type": "string", "description": "Email used for the original booking."},
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
        "cancel_booking",
        "cancel-booking",
        "Cancel a booking. Needs bookingId and revision from get_booking. Only "
        "call after explicit caller confirmation.",
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
        "Reschedule a booking. Needs original bookingId/revision/serviceId plus "
        "new scheduleId, staffId, startDate, endDate from get_slots.",
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
            "required": ["bookingId", "revision", "serviceId", "scheduleId",
                         "staffId", "startDate", "endDate"],
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
        "flag_callback",
        "flag-callback",
        "Email Nicky a callback request. Use when caller insists on a human, has "
        "a question you can't answer, or a tool failed. Always include callerName "
        "— ask the caller's name first if you don't have it.",
        {
            "type": "object",
            "properties": {
                "callerName":    {"type": "string", "description": "Caller's name — ASK if you don't have it before calling."},
                "callerPhone":   {"type": "string", "description": "Caller's phone — default to {{user_number}}."},
                "reason":        {"type": "string", "description": "One-sentence summary of why a callback is needed."},
                "questionDetail":{"type": "string", "description": "The actual question or request, in the caller's words if possible."},
            },
            "required": ["reason"],
        },
        response_variables={"callback_flagged": "$.flagged"},
    ),
]


END_CALL_TOOL = {
    "name": "end_call",
    "type": "end_call",
    "description": "End the call gracefully after the closing line. Use when the "
                   "caller says goodbye, when emergency / crisis / spam / "
                   "recording-decline triggers, or after a silence timeout.",
    "speak_during_execution": False,
    "speak_after_execution": False,
}


# -----------------------------------------------------------------------------
# Post-call analysis (mirrors the conversation-flow agent — 10 fields)
# -----------------------------------------------------------------------------

POST_CALL_ANALYSIS = [
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
    {"name": "booking_id",         "type": "string",  "description": "Wix bookingId if a booking was created on this call."},
    {"name": "callback_required",  "type": "boolean", "description": "True if a callback was flagged for Nicky."},
    {"name": "callback_reason",    "type": "string",  "description": "Short reason for the callback if one was flagged."},
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
    {"name": "spam_call",            "type": "boolean", "description": "Was this call identified as spam, marketing, or solicitation?"},
    {"name": "inappropriate_request","type": "boolean", "description": "Did the caller request 'full service' / 'happy ending' / sexual services?"},
    {"name": "tool_failure",         "type": "boolean", "description": "Did any Wix tool call fail (slot lookup, booking creation, etc.)?"},
]


# -----------------------------------------------------------------------------
# Agent
# -----------------------------------------------------------------------------

GENERAL_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")

AGENT = {
    "agent_id": "",
    "channel": "voice",
    "agent_name": "Aria — Sage & Willow Spa — Single Prompt V1",
    "language": ["en-US", "es-ES", "en-IN", "es-419", "en-GB", "en-AU"],
    # Mirror conversation-flow agent voice + perf settings so it sounds the same.
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
    "post_call_analysis_data": POST_CALL_ANALYSIS,
    "response_engine": {
        "type": "retell-llm",
        "llm_id": "",
        "version": 0,
    },
    "retellLlmData": {
        "llm_id": "",
        "version": 0,
        "model": "gpt-4.1",
        "general_prompt": GENERAL_PROMPT,
        "general_tools": CUSTOM_TOOLS + [END_CALL_TOOL],
        "start_speaker": "agent",
        "begin_message": "Hi, this is Aria from Sage and Willow Spa. Just to let you know, this call is recorded for quality purpose. How can I help you today?",
        "default_dynamic_variables": {},
        "knowledge_base_ids": [],
        "kb_config": {
            "top_k": 3,
            "filter_score": 0.6,
        },
    },
}


def main():
    OUT_PATH.write_text(
        json.dumps(AGENT, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Wrote {OUT_PATH}")
    print(f"  Prompt size: {len(GENERAL_PROMPT)} chars / {len(GENERAL_PROMPT.split())} words")
    print(f"  Tools: {len(CUSTOM_TOOLS) + 1} ({len(CUSTOM_TOOLS)} custom + 1 end_call)")
    print(f"  Post-call analysis fields: {len(POST_CALL_ANALYSIS)}")


if __name__ == "__main__":
    main()
