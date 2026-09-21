"""
Build the Sage & Willow Spa OUTBOUND voice agent.

Run:  py -X utf8 outbound/_build_outbound_agent.py [--dry-run] [--prod] [--publish]

  default   tools -> DEV backend (test Wix site), agent left as a draft
  --prod    tools -> PRODUCTION backend (the client's real Wix calendar)
  --publish publish the agent after updating it, so `latest_published` moves

Why this is a transform and not a copy
--------------------------------------
The outbound agent is the live INBOUND conversation flow with a small,
declared set of differences. Rather than fork 60KB of JSON and let the two
drift, this script pulls the inbound flow from the Retell API every run and
re-applies the patch set below. Fix something on inbound, re-run this, and the
fix ports over.

What differs from inbound
-------------------------
1. Tool URLs point at the DEV backend (`/webhook/retell-wix-outbound`,
   test Wix credentials) so an outbound test call can never write to the
   client's real calendar - unless built with --prod, which keeps the
   inbound (production) URLs. Went live with --prod --publish on 2026-09-19.
2. {{user_number}} is the SPA's caller ID on an outbound call, not the lead's
   number. Every reference is rewired to {{lead_phone}} from the web form.
3. The greeting becomes an outbound opening: identity check, reason for the
   call, permission to continue.
4. Five new nodes for failure modes inbound never had - wrong person, bad
   time, not interested, doesn't remember the form, voicemail.
5. Phone is never collected - it is the number we dialled. Name is skipped when
   the lead supplied it (website form) and asked once when it is unknown
   (missed-call callbacks) - a branch node decides, not the model.
6. Closing line stops saying "thank you for calling."

Everything else - booking discovery, add-ons, readback, submit, cancel,
reschedule, status, FAQ, transfer, callback, and every escalation - is carried
over untouched.
"""

from __future__ import annotations
import argparse
import json
import os
import re
import urllib.request
from pathlib import Path

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------

RETELL_BASE = "https://api.retellai.com"

# Source of truth: the live inbound agent's flow.
SOURCE_FLOW_ID = "conversation_flow_bdb1968b28ed"
SOURCE_FLOW_VERSION = 18  # PUBLISHED 2026-09-22: V38-V58 (spelled names), 30 s silence
SOURCE_AGENT_ID = "agent_eceb7448aa1f37e8f436a63a43"

# Dev backend built by _build_outbound_backend_workflow.py (n8n yfbpUaEzZQghelh3).
OUTBOUND_WEBHOOK = "https://automation.aiemply.com/webhook/retell-wix-outbound"
# Post-call events (call_analyzed) -> the n8n workflow that sends Aria's recap
# e-mail; the same webhook the inbound agent already reports to.
POST_CALL_WEBHOOK = "https://automation.aiemply.com/webhook/sage-willow-post-call"
INBOUND_WEBHOOK = "https://automation.aiemply.com/webhook/retell-wix"

KNOWLEDGE_BASE_ID = "knowledge_base_cb1d71238e1ba5fe"  # "SPA Business Context"

SPA_CALLER_ID = "{{user_number}}"   # inbound: the caller. Outbound: the SPA's own line.
LEAD_PHONE = "{{lead_phone}}"       # the number we dialled

# Tools whose JSON schema mentions the caller's number and must be rewired.
PHONE_DEFAULT_TOOLS = 4  # book_appointment, get_booking, cancel_booking, reschedule_booking

# The three lookup flows (status / cancel / reschedule) search the caller's own
# number first. On inbound that is whoever dialled us; on outbound it is the
# lead we rang, and the inbound wording - "the number they are calling from",
# "they rang us from it" - is simply false. V44 gave all three the same block,
# so one replacement fixes all three.
OLD_LOOKUP_STEP = (
    "Call get_booking IMMEDIATELY on the number they are calling from, {{user_number}}. "
    "Do not ask them for a number first - they rang us from it, it is nearly always the "
    "one they booked with, and looking it up takes less time than asking.\n"
    "   If, and only if, that comes back with nothing, ask for the other one and say why: "
    "\"I'm not seeing an appointment under the number you're calling from - is there a "
    "different number you booked with?\" Then call get_booking AGAIN with whatever they "
    "give you; they will often just say the digits with nothing else."
)
NEW_LOOKUP_STEP = (
    "Call get_booking IMMEDIATELY on {{lead_phone}} - the number we rang them on. "
    "Do not ask them for a number first; it is nearly always the one they booked with, "
    "and looking it up takes less time than asking.\n"
    "   If, and only if, that comes back with nothing, ask for the other one and say why: "
    "\"I'm not seeing an appointment under this number - is there a different one you "
    "booked with?\" Then call get_booking AGAIN with whatever they give you; they will "
    "often just say the digits with nothing else."
)
LOOKUP_NODES = ("node-status-assistant", "node-cancel-assistant", "node-resched-assistant")

# Number the voicemail message asks people to ring back - the Retell DID, so a
# callback lands on the inbound Aria agent.
CALLBACK_NUMBER_SPOKEN = "six two eight, two eight six, two two eight one"

# Bump on every meaningful build so the client knows which revision they tested.
AGENT_VERSION = "V19"

# A silent line ends after this long (Ubaid, 2026-09-22, after Nicky's "no need
# to wait almost 3 mins"): 89 s let call_b004eecd sit for 149 s. First 50 s,
# then 30 s the same day. Set here on purpose rather than inherited, so a
# dashboard edit on inbound cannot drift it.
END_CALL_AFTER_SILENCE_MS = 30000
# Ubaid renamed the agent in the dashboard on 2026-09-19; keep his name and
# carry the build version on the flow name instead.
AGENT_NAME = "Aria - Sage & Willow Spa - Outbound Agent"
FLOW_NAME = f"Aria - Sage & Willow Spa - Outbound {AGENT_VERSION}"

OUT_DIR = Path(__file__).parent
FLOW_SNAPSHOT = OUT_DIR / "outbound_conversation_flow.json"
AGENT_SNAPSHOT = OUT_DIR / "outbound_agent.json"
STATE_PATH = OUT_DIR / "_deployed_ids.json"


def api_key() -> str:
    """Retell key from the environment, falling back to the repo's .mcp.json.

    Never inline the key here - this file is committed.
    """
    key = os.environ.get("RETELL_API_KEY")
    if key:
        return key
    # Read the key from the `retell-sage` MCP entry specifically. .mcp.json also
    # holds keys for retell-aiemply and retell-impleko, which are DIFFERENT
    # workspaces with no Sage & Willow agents in them - a blind grep, or the old
    # lookup of a bare `retell` server that no longer exists, picks the wrong one
    # and every call silently returns nothing.
    mcp = Path(__file__).resolve().parents[2] / ".mcp.json"
    if mcp.exists():
        raw = mcp.read_text(encoding="utf-8")
        cfg = json.loads(raw[raw.index("{"):])
        entry = cfg.get("mcpServers", {}).get("retell-sage")
        if entry:
            match = re.search(r"key_[a-f0-9]+", json.dumps(entry))
            if match:
                return match.group(0)
    raise SystemExit(
        "No Retell API key. Set RETELL_API_KEY, or configure the `retell-sage` "
        "MCP server in .mcp.json."
    )


def request(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        f"{RETELL_BASE}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {api_key()}",
            "Content-Type": "application/json",
            "User-Agent": "curl/8.0",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            # publish-agent answers 200 with an empty body.
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise SystemExit(f"Retell API {method} {path} -> {exc.code}: {detail}") from None


# =============================================================================
# 1. Global prompt patches
# =============================================================================

OLD_CALLER_CONTEXT = """## Caller Context

Caller phone: {{user_number}}
Call direction: {{direction}}"""

NEW_CALL_CONTEXT = """## Call Context

OUTBOUND call - you placed it. lead_source is "{{lead_source}}":
- website_form: they filled out the booking form on our website and asked us to get in touch. They have never spoken to us.
- missed_call: they rang the spa a little earlier and the call ended before anything got done. You are returning it. What they seemed to want, if known: {{inbound_intent}}

Lead name: {{lead_first_name}} {{lead_last_name}}
Lead phone: {{lead_phone}}
When: {{lead_submitted_at}}
"""

# Kept to what the exit nodes do not already enforce. The old eight-bullet
# version cost ~380 tokens on every turn and mostly restated the wrong-person /
# bad-time / not-interested nodes and their edge conditions.
OUTBOUND_ETIQUETTE = """## You rang them

- You interrupted their day: get to the point inside two sentences, and take the first clear no as a no - one short acknowledgement, then let them go.
- Never ask for anything you already have. You have their number; if the name came through, you have that too.
- Match what happened: a website_form lead never rang us; a missed_call lead never filled out a form. They booked, paid and agreed to nothing before this call.
- The number this call dials FROM is the spa's own line. The only number that belongs to this lead is {{lead_phone}}.

"""

ANCHOR_BEFORE_ETIQUETTE = "## Never claim something is done"

OLD_PHONE_PRONUNCIATION = (
    "The only number you may say aloud is the live value of {{user_number}} or "
    "one the caller just gave you."
)
NEW_PHONE_PRONUNCIATION = (
    "The only number you may say aloud is the live value of {{lead_phone}} or "
    "one the lead just gave you."
)


def patch_global_prompt(prompt: str) -> str:
    if OLD_CALLER_CONTEXT not in prompt:
        raise SystemExit("Caller Context block not found - inbound prompt changed shape.")
    prompt = prompt.replace(OLD_CALLER_CONTEXT, NEW_CALL_CONTEXT)

    if OLD_PHONE_PRONUNCIATION not in prompt:
        raise SystemExit("Phone pronunciation line not found - inbound prompt changed shape.")
    prompt = prompt.replace(OLD_PHONE_PRONUNCIATION, NEW_PHONE_PRONUNCIATION)

    if ANCHOR_BEFORE_ETIQUETTE not in prompt:
        raise SystemExit("Etiquette anchor not found - inbound prompt changed shape.")
    prompt = prompt.replace(ANCHOR_BEFORE_ETIQUETTE, OUTBOUND_ETIQUETTE + ANCHOR_BEFORE_ETIQUETTE, 1)

    # Identity line: inbound says "This is a live, recorded phone call."
    prompt = prompt.replace(
        "This is a live, recorded phone call.",
        "This is a live, recorded phone call that YOU placed.",
    )
    return prompt


# =============================================================================
# 2. Node instruction rewrites (id -> new instruction text)
# =============================================================================

# The NAMED opener. Only reachable through node-out-gate when lead_name_known
# is exactly "yes", so {{lead_first_name}} is guaranteed to hold a real name
# here. On call_bf1fba1444d077c131bf9411e1f the agent opened with
# "Hi, is this {{lead_first_name}}?" - braces and all - because the call was
# placed without dynamic variables and the old single opener left it to the
# model to notice. It did not. A branch node now decides; the model never sees
# an opener it is not allowed to say.
# A machine answered. Nicky (2026-09-22): "give waiting time, let answering
# finish speaking". On both real voicemail calls (call_1b82ff9f, call_8f22bdb3)
# the greeting's first "Hi," was taken as the callee and Aria opened over the
# recording, restarting two or three times, before Retell's voicemail
# detection left the message. The opener is judged on what was heard, so the
# rule lives in both opener nodes: a recording gets silence, not an opener.
RECORDING_RULE = """A RECORDING IS NOT A PERSON. If what you hear sounds like a machine - a phone number read out, "you've reached", "not available", "can't take your call", "leave a message", "at the tone", a beep - do NOT open. Reply NO_RESPONSE_NEEDED and stay quiet, and keep doing so while the recording runs; the voicemail step takes over on its own. A recording is not echo either: if one cut you off, stay quiet rather than starting the opener again. Only a live person gets the opener."""

OPENING_NAMED = """The reason for this call is lead_source = "{{lead_source}}" (see Call Context). A missed_call lead never filled out a form, and a website_form lead never rang us - never mix those up.

THEY SPEAK FIRST - "Hello?", a name, a grunt, anything. Whatever it is, your FIRST turn is the opener below. A first "Hello?" is them answering the phone, not asking if you can hear them.

""" + RECORDING_RULE + """

FIRST TURN ONLY - open with exactly: "Hi, is this {{lead_first_name}}?" then STOP. No second sentence, no stacked question. You are checking you have the right person before you say anything else.

Once they confirm it is them, ONE turn, then straight to the question. You have not introduced yourself yet, so do it now:
- website_form: "Hi {{lead_first_name}}, this is Aria from Sage and Willow Spa - you filled out our booking form. Which massage can I book for you?"
- missed_call: "Hi {{lead_first_name}}, this is Aria from Sage and Willow Spa - looks like we got cut off a moment ago. What can I help you with?"
- lead_source is anything else: "Hi {{lead_first_name}}, this is Aria from Sage and Willow Spa - you reached out to us. What can I help you with?"
On a missed_call lead, if {{inbound_intent}} says they were booking, end with "Which massage can I book for you?" instead of "What can I help you with?"
Never read a variable name or curly braces aloud.

You are NOT asking permission first - they reached out to us, so get to the point. But a bad time or a not-interested still wins over the question: let them go.

After that you have introduced yourself. NEVER say either line again, in whole or in part.

Handle here and wait - do not route:
- "Hello?" / "Can you hear me?" AFTER you have opened -> "Yep, I can hear you - is this {{lead_first_name}}?"
- "Who is this?" -> website_form: "It's Aria from Sage and Willow Spa - you filled out our booking form." missed_call: "It's Aria from Sage and Willow Spa - you rang us a little earlier."
- "Is this a robot?" -> "I'm Aria, the virtual receptionist at Sage and Willow Spa - happy to help." Then carry on.
- They name a massage straight away -> take it and move on.
- missed_call lead says they never called -> "No problem at all - sorry to bother you. Take care." and end the call.

Route as soon as you know where this is going. Do not answer spa questions or list services here."""

# The UNNAMED opener. Reached when lead_name_known is anything but "yes" -
# including when the dynamic variables never arrived at all, in which case
# every {{...}} in the context renders as literal braces and lead_source is
# unusable too. Nothing in this node depends on the name.
OPENING_UNNAMED = """The reason for this call is lead_source = "{{lead_source}}" (see Call Context). A missed_call lead never filled out a form, and a website_form lead never rang us - never mix those up. If lead_source is neither of those, or shows curly braces, treat the reason as unknown and use the "unknown" line wherever there is a choice.

You do NOT have this person's name. Never guess one, never ask for one here, and never say the words "lead" or "first name".

THEY SPEAK FIRST - "Hello?", a name, a grunt, anything. Whatever it is, your FIRST turn is the opener below. A first "Hello?" is them answering the phone, not asking if you can hear them.

""" + RECORDING_RULE + """

FIRST TURN ONLY - open with exactly ONE of these, then STOP. No second sentence, no stacked question.
- website_form: "Hi, this is Aria from Sage and Willow Spa - am I speaking with the person who filled out our booking form?"
- missed_call: "Hi, this is Aria from Sage and Willow Spa - did someone at this number just try to reach us?"
- unknown: "Hi, this is Aria from Sage and Willow Spa - am I speaking with the person who reached out to us?"

Once they confirm it is them, ONE turn, then straight to the question. You have ALREADY introduced yourself - do NOT say your name or the spa again:
- website_form: "Great - which massage can I book for you?"
- missed_call: "Sorry about that - what can I help you with?"
- unknown: "Great - what can I help you with?"
On a missed_call lead, if {{inbound_intent}} says they were booking, end with "Which massage can I book for you?" instead of "What can I help you with?"
Never read a variable name or curly braces aloud.

You are NOT asking permission first - they reached out to us, so get to the point. But a bad time or a not-interested still wins over the question: let them go.

After that you have introduced yourself. NEVER say the opener again, in whole or in part.

Handle here and wait - do not route:
- "Hello?" / "Can you hear me?" AFTER you have opened -> "Yep, I can hear you." then the opener question again, once.
- "Who is this?" -> website_form: "It's Aria from Sage and Willow Spa - you filled out our booking form." missed_call: "It's Aria from Sage and Willow Spa - you rang us a little earlier." unknown: "It's Aria from Sage and Willow Spa - you reached out to us."
- "Is this a robot?" -> "I'm Aria, the virtual receptionist at Sage and Willow Spa - happy to help." Then carry on.
- They name a massage straight away -> take it and move on.
- missed_call lead says they never called -> "No problem at all - sorry to bother you. Take care." and end the call.

Route as soon as you know where this is going. Do not answer spa questions or list services here."""

WRONG_PERSON = """Say: "Sorry about that - looks like I've got the wrong number. Have a good one."

Then nothing. This person did not ask us to call.

Do NOT explain what the spa is. Do NOT ask who you are speaking to. Do NOT ask for the right number. Do NOT offer them a massage, a booking, a callback, or the website. Do not try to salvage the call."""

BAD_TIME = """They are the right person but this is a bad moment. Ask once when a better time to reach them would be, then take whatever they give you.

"day after tomorrow", "after five", "evenings", "just try me tomorrow" - all fine. Do not push for an exact hour and do not ask a second question.

Do not try to book anything now. Do not squeeze in a price or a service before letting them go."""

NOT_INTERESTED = """Say: "No problem at all - sorry to have bothered you. Take care."

One line, then nothing.

Do NOT ask why. Do NOT offer a discount, a different day, a different service, or a callback. Do NOT mention the website. Do NOT ask to keep them on the list.

If they asked to be taken off the list or told you not to call again, say instead: "Understood - I'll make sure we don't call again. Take care." """

NO_FORM_RECALL = """They do not remember reaching out, or they are wary this is a sales call. Say it once, calmly, in one sentence, matching lead_source = "{{lead_source}}":
- website_form: they filled out the booking form on sage-willow-spa dot com asking us to call about a massage appointment.
- missed_call: someone rang the spa from this number at {{lead_submitted_at}} and the call dropped before we could help, so you are just returning it.

Say it ONCE. Do not argue, do not repeat it, and do not read their details back to prove it - that makes it worse, not better.

If someone else in the household may have filled it out or made the call, offer to ring back rather than pressing on.

If they still do not want the call after that one explanation, let them go."""

VOICEMAIL_FALLBACK = f"""You have reached an answering machine, not a person. Leave this message and nothing else:

"Hi {{{{lead_first_name}}}}, this is Aria from Sage and Willow Spa getting back to you. Give us a call at {CALLBACK_NUMBER_SPOKEN} and we'll get you scheduled. Thanks!"

Do not wait for a reply. Do not ask a question. Do not say anything after that message.

If {{{{lead_first_name}}}} is empty or renders with literal curly braces, open with "Hi, this is Aria from Sage and Willow Spa" instead."""

# Name: the inbound node's text is inherited as-is (V58: spell the first name,
# then spell the last name, no read-back - Ubaid, 2026-09-22, after
# call_d1fc46c0 booked "Book Kaul" for a caller who said first Kaul, last
# Book). Outbound only prepends this line; build_flow refuses a source node
# that does not ask for the spelling.
BOOK_NAME_OUTBOUND_HEAD = "You do not have this lead's name yet.\n\n"
BOOK_NAME_MUST_HAVE = ("Can you spell your first name for me?",
                       "could you spell that as well?",
                       "Do NOT read either name back")

BOOK_NAME_GATE_NAME = "Booking - Name Known?"


CLOSE_OUTBOUND = """Say exactly: "Thanks for your time. Take care."

Nothing after it - no summary, no extra offer. Never say "thank you for calling" - you rang them."""

RECORDING_DECLINE_OUTBOUND = """Say: "Understood - I'll let you go. You can book any time at sage-willow-spa dot com. Have a great day."

Then nothing. You rang them, so there is nothing to negotiate here - do not explain the recording policy and do not ask them to reconsider."""

INSTRUCTION_REWRITES = {
    "node-greeting": OPENING_NAMED,
    "node-close": CLOSE_OUTBOUND,
    "node-global-recording-decline": RECORDING_DECLINE_OUTBOUND,
}

# Display-name changes so the Retell canvas reads as an outbound flow.
NAME_REWRITES = {
    "node-greeting": "Outbound Opening (name known)",
    "node-book-name": "Booking - Name (ask)",
}


# =============================================================================
# 3. New nodes
# =============================================================================

def prompt_edge(edge_id: str, dest: str, prompt: str) -> dict:
    return {
        "id": edge_id,
        "destination_node_id": dest,
        "transition_condition": {"type": "prompt", "prompt": prompt},
    }


def skip_to(edge_id: str, dest: str) -> dict:
    return {
        "id": edge_id,
        "destination_node_id": dest,
        "transition_condition": {"type": "prompt", "prompt": "Skip response"},
    }


NEW_NODES = [
    {
        "id": "node-out-wrong-person",
        "name": "Outbound - Wrong Person",
        "type": "conversation",
        "display_position": {"x": 700, "y": -900},
        "instruction": {"type": "prompt", "text": WRONG_PERSON},
        "edges": [],
        "skip_response_edge": skip_to("e-wrongperson-hangup", "node-hangup"),
        # Reached only through the opener's own edge (e-out-wrong). "Wrong
        # number" is an opening-phase objection; carrying it as a global node
        # put its condition and six examples into every routing pass.
    },
    {
        "id": "node-out-bad-time",
        "name": "Outbound - Bad Time",
        "type": "conversation",
        "display_position": {"x": 700, "y": -500},
        "instruction": {"type": "prompt", "text": BAD_TIME},
        "edges": [
            prompt_edge(
                "e-badtime-callback", "node-handoff-callback",
                "The lead has given a day or time to call back, or said to just try again whenever.",
            ),
            prompt_edge(
                "e-badtime-no", "node-out-not-interested",
                "The lead says not to call back at all.",
            ),
            prompt_edge(
                "e-badtime-continue", "node-book-service",
                "The lead changes their mind and wants to carry on with booking now.",
            ),
        ],
        "global_node_setting": {
            "condition": (
                "The lead is the right person but says this is a bad time - they are busy, "
                "driving, at work, with someone, or ask to be called back later."
            ),
            "cool_down": 2,
            "positive_finetune_examples": [
                {"transcript": [{"role": "user", "content": "I'm driving right now"}]},
                {"transcript": [{"role": "user", "content": "Can you call me back later?"}]},
                {"transcript": [{"role": "user", "content": "Now's not a great time"}]},
            ],
            "negative_finetune_examples": [
                {"transcript": [{"role": "user", "content": "Hold on one second"}]},
            ],
        },
    },
    {
        "id": "node-out-not-interested",
        "name": "Outbound - Not Interested",
        "type": "conversation",
        "display_position": {"x": 700, "y": -100},
        "instruction": {"type": "prompt", "text": NOT_INTERESTED},
        "edges": [],
        "skip_response_edge": skip_to("e-notinterested-hangup", "node-hangup"),
        "global_node_setting": {
            "condition": (
                "The lead says they are not interested, have changed their mind, already "
                "booked somewhere else, or asks not to be contacted again. Fires on a clear "
                "refusal of the call itself - not on declining one service, one add-on, or "
                "one time slot."
            ),
            "cool_down": 1,
            "positive_finetune_examples": [
                {"transcript": [{"role": "user", "content": "I'm not interested, thanks"}]},
                {"transcript": [{"role": "user", "content": "Take me off your list"}]},
                {"transcript": [{"role": "user", "content": "I already booked somewhere else"}]},
                {"transcript": [{"role": "user", "content": "Please don't call me again"}]},
            ],
            "negative_finetune_examples": [
                {"transcript": [{"role": "user", "content": "No thanks, no add-ons"}]},
            ],
        },
    },
    {
        "id": "node-out-no-form-recall",
        "name": "Outbound - Doesn't Recall Reaching Out",
        "type": "conversation",
        "display_position": {"x": 700, "y": 300},
        "instruction": {"type": "prompt", "text": NO_FORM_RECALL},
        "edges": [
            prompt_edge(
                "e-noform-book", "node-book-service",
                "The lead accepts the explanation and wants to talk about booking.",
            ),
            prompt_edge(
                "e-noform-drop", "node-out-not-interested",
                "The lead still does not want the call after the one explanation.",
            ),
            prompt_edge(
                "e-noform-later", "node-out-bad-time",
                "Someone else in the household may have filled it out, or the lead wants us to try again later.",
            ),
        ],
        # Reached only through the opener's own edge (e-out-noform), for the
        # same reason as wrong-person above.
    },
    {
        "id": "node-out-voicemail",
        "name": "Outbound - Voicemail",
        "type": "conversation",
        "display_position": {"x": 700, "y": 700},
        "instruction": {"type": "prompt", "text": VOICEMAIL_FALLBACK},
        "edges": [],
        "skip_response_edge": skip_to("e-voicemail-hangup", "node-hangup"),
        "global_node_setting": {
            "condition": (
                "The other end is an answering machine or voicemail, not a live person - a "
                "recorded greeting, an automated 'leave a message after the tone', a beep, or "
                "a carrier message. Never fires while an actual person is replying to you."
            ),
            "cool_down": 1,
            "positive_finetune_examples": [
                {"transcript": [{"role": "user", "content": "Please leave your message after the tone"}]},
                {"transcript": [{"role": "user", "content": "You have reached the voicemail of 415 555 0142"}]},
            ],
            "negative_finetune_examples": [
                {"transcript": [{"role": "user", "content": "Hello?"}]},
                {"transcript": [{"role": "user", "content": "Yes this is she"}]},
            ],
        },
    },
]


# Extra edges out of the opening node, on top of the inbound ones it keeps.
OPENING_EDGES = [
    prompt_edge(
        "e-out-wrong", "node-out-wrong-person",
        "The person who answered is not the lead we asked for, or says we have the wrong number.",
    ),
    prompt_edge(
        "e-out-badtime", "node-out-bad-time",
        "The lead is the right person but says now is a bad time or asks to be called back later.",
    ),
    prompt_edge(
        "e-out-notinterested", "node-out-not-interested",
        "The lead says they are not interested, changed their mind, or asks not to be called again.",
    ),
    prompt_edge(
        "e-out-noform", "node-out-no-form-recall",
        "The lead does not remember filling out a form or calling us, asks how we got their number, or suspects a scam.",
    ),
]


# =============================================================================
# 4. Flow transform
# =============================================================================

def build_flow(source: dict, target_webhook: str) -> dict:
    flow = json.loads(json.dumps(source))  # deep copy
    for key in ("conversation_flow_id", "version", "last_modification_timestamp", "is_published"):
        flow.pop(key, None)

    flow["global_prompt"] = patch_global_prompt(flow["global_prompt"])

    # Tools -> the chosen backend, and the phone defaults baked into their JSON schemas
    # move off the spa's caller ID. book_appointment.phone and get_booking.phone
    # both default to {{user_number}} on inbound; left alone, outbound would file
    # every booking against the spa's own number.
    swapped = 0
    rewired_defaults = 0
    for tool in flow.get("tools", []):
        if tool.get("url") == INBOUND_WEBHOOK:
            tool["url"] = target_webhook
            swapped += 1
        raw = json.dumps(tool, ensure_ascii=False)
        if "{{user_number}}" in raw:
            rewired = raw.replace("{{user_number}}", "{{lead_phone}}")
            tool.clear()
            tool.update(json.loads(rewired))
            rewired_defaults += 1
    if swapped != 8:
        raise SystemExit(f"Expected to repoint 8 tools, repointed {swapped}. The source "
                         f"inbound flow's tools are not all on {INBOUND_WEBHOOK} - refusing to "
                         f"build from a draft that is itself pointed at dev.")
    # book_appointment.phone and get_booking.phone have always defaulted to the
    # caller's number. V41 added a required `phone` to cancel_booking and
    # reschedule_booking too, so the n8n resolver can check the bookingId the
    # model sent against that caller's live bookings - which makes four.
    if rewired_defaults != PHONE_DEFAULT_TOOLS:
        raise SystemExit(
            f"Expected {PHONE_DEFAULT_TOOLS} tools with a {{{{user_number}}}} phone "
            f"reference (book_appointment, get_booking, cancel_booking, "
            f"reschedule_booking), found {rewired_defaults}."
        )

    nodes = {n["id"]: n for n in flow["nodes"]}

    for node_id, text in INSTRUCTION_REWRITES.items():
        if node_id not in nodes:
            raise SystemExit(f"Node {node_id} missing from inbound flow.")
        nodes[node_id]["instruction"] = {"type": "prompt", "text": text}
    for node_id, name in NAME_REWRITES.items():
        nodes[node_id]["name"] = name

    # The opening keeps its inbound routing and gains the outbound exits.
    nodes["node-greeting"]["edges"] = OPENING_EDGES + nodes["node-greeting"]["edges"]

    # Twin of the opening for leads whose name we do not have. Same edges, one
    # row down on the canvas; edge ids get a "u-" prefix so they stay unique.
    unnamed = json.loads(json.dumps(nodes["node-greeting"]))
    unnamed["id"] = "node-greeting-unnamed"
    unnamed["name"] = "Outbound Opening (name unknown)"
    unnamed["instruction"] = {"type": "prompt", "text": OPENING_UNNAMED}
    pos = unnamed.get("display_position", {"x": 0, "y": 0})
    unnamed["display_position"] = {"x": pos["x"], "y": pos["y"] + 320}
    for e in unnamed["edges"]:
        e["id"] = "u-" + e["id"]
    for k in ("skip_response_edge", "always_edge", "else_edge"):
        if unnamed.get(k):
            unnamed[k]["id"] = "u-" + unnamed[k]["id"]
    flow["nodes"].append(unnamed)
    nodes["node-greeting-unnamed"] = unnamed

    # The gate. `exists` is TRUE for an empty string, and a variable that never
    # arrived renders as literal braces - so only an exact "yes", which the
    # trigger workflow sets on purpose, reaches the named opener. Everything
    # else, including a call placed with no dynamic variables at all, goes to
    # the unnamed one. The model never sees an opener it is not allowed to say.
    gate = {
        "id": "node-out-gate",
        "name": "Outbound - Name Known?",
        "type": "branch",
        "display_position": {"x": pos["x"] - 300, "y": pos["y"] + 160},
        "edges": [{
            "id": "e-outgate-named",
            "destination_node_id": "node-greeting",
            "transition_condition": {"type": "equation", "operator": "&&", "equations": [
                {"left": "{{lead_name_known}}", "operator": "==", "right": "yes"},
            ]},
        }],
        "else_edge": {"id": "e-outgate-unnamed", "destination_node_id": "node-greeting-unnamed",
                      "transition_condition": {"type": "prompt", "prompt": "Else"}},
    }
    flow["nodes"].append(gate)
    nodes["node-out-gate"] = gate
    flow["start_node_id"] = "node-out-gate"

    # The CALLEE speaks first. Inbound is agent-first because the caller is
    # waiting for a greeting; outbound is the reverse - the person picking up
    # says "Hello?" and only then does Aria open. With agent-first she started
    # at ~1.2s, before anyone had said hello (call_4ec71f5e: her "Hi, this is
    # Aria" collided with "Hello? Yes, I'm here", the model took that as a
    # confirmation and skipped straight to "what can I help you with?" - the
    # person hung up without ever hearing why we rang). A 1s
    # begin_message_delay was the old mitigation and was not enough.
    flow["start_speaker"] = "user"
    # They picked up and said nothing: open after a short beat rather than the
    # inbound flow's 6s (that is for a caller who dialled and is waiting).
    flow["begin_after_user_silence_ms"] = 4000
    for gid in ("node-greeting", "node-greeting-unnamed"):
        nodes[gid].pop("reminder_trigger_ms", None)
        nodes[gid].pop("reminder_max_count", None)

    # node-handoff-done inherits an edge back to the greeting ("wants something
    # else"). Send that through the gate too, so a mid-call return never
    # re-reads an opener that may not apply.
    for n in flow["nodes"]:
        if n["id"] == "node-out-gate":
            continue
        for e in n.get("edges", []):
            if e["destination_node_id"] == "node-greeting":
                e["destination_node_id"] = "node-out-gate"

    # Phone: on an outbound call it is always the number we dialled, so the inbound
    # "Booking - Phone" node is removed outright. A node told to "say nothing" is
    # the classic Retell failure - the model has to produce a turn, so it invents
    # one (call_f5943184: "you're all set... male or female therapist?" came from
    # exactly that node). No node, no babble.
    flow["nodes"] = [n for n in flow["nodes"] if n["id"] != "node-book-phone"]
    nodes.pop("node-book-phone")
    for n in flow["nodes"]:
        for e in n.get("edges", []):
            if e["destination_node_id"] == "node-book-phone":
                e["destination_node_id"] = "node-book-readback"
        for k in ("skip_response_edge", "always_edge", "else_edge"):
            if n.get(k) and n[k]["destination_node_id"] == "node-book-phone":
                n[k]["destination_node_id"] = "node-book-readback"
        # V58 gave the name node transition examples that name their target.
        for ex in n.get("finetune_transition_examples", []):
            if ex.get("destination_node_id") == "node-book-phone":
                ex["destination_node_id"] = "node-book-readback"

    # Name node: inbound's V58 wording plus the outbound first line.
    name_text = nodes["node-book-name"]["instruction"]["text"]
    for must in BOOK_NAME_MUST_HAVE:
        if must not in name_text:
            raise SystemExit(f"node-book-name does not ask for the spelling ({must!r} missing) - "
                             f"inbound V58 not in the source flow?")
    nodes["node-book-name"]["instruction"]["text"] = BOOK_NAME_OUTBOUND_HEAD + name_text

    # Name: known on a website_form lead, usually unknown on a missed_call lead.
    # The trigger workflow sends lead_name_known = "yes" | "no"; a branch keys off
    # that string. (Retell's `exists` is true for an EMPTY string, which is how
    # V04 skipped the name question and sent firstName "" to the tool.) Else -> ask.
    for n in flow["nodes"]:
        for e in n.get("edges", []):
            if e["destination_node_id"] == "node-book-name":
                e["destination_node_id"] = "node-book-name-gate"
    nodes["node-book-name"].pop("skip_response_edge", None)
    name_pos = nodes["node-book-name"].get("display_position", {"x": 0, "y": 0})
    flow["nodes"].append({
        "id": "node-book-name-gate",
        "name": BOOK_NAME_GATE_NAME,
        "type": "branch",
        "display_position": {"x": name_pos["x"] - 250, "y": name_pos["y"]},
        "edges": [{
            "id": "e-namegate-known",
            "destination_node_id": "node-book-readback",
            "transition_condition": {"type": "equation", "operator": "&&", "equations": [
                {"left": "{{lead_name_known}}", "operator": "==", "right": "yes"},
            ]},
        }],
        "else_edge": {"id": "e-namegate-ask", "destination_node_id": "node-book-name",
                      "transition_condition": {"type": "prompt", "prompt": "Else"}},
    })

    # The tool must be told where the name comes from on an outbound call.
    for tool in flow["tools"]:
        if tool["name"] == "book_appointment":
            props = tool["parameters"]["properties"]
            props["firstName"]["description"] = (
                "The lead's first name. Use the Lead name from the call context when it was given there; "
                "otherwise exactly the first name they gave on this call, spelled letters joined into the word "
                "(J-O-H-N -> John). Required - never send an empty string."
            )
            props["lastName"]["description"] = (
                "The lead's last name. Use the Lead name from the call context when it was given there; "
                "otherwise exactly the last name they gave on this call, spelled letters joined into the word "
                "(T-E-S-T -> Test). Required - never send an empty string."
            )

    # Status / cancel / reschedule all open by looking the caller up on their own
    # number. Outbound has to say WHOSE number that is, and must not claim they
    # rang us - on a website_form lead they never did.
    for node_id in LOOKUP_NODES:
        text = nodes[node_id]["instruction"]["text"]
        if OLD_LOOKUP_STEP not in text:
            raise SystemExit(
                f"{node_id}: the V44 lookup block is not where it was. The inbound flow "
                f"changed shape - re-read it before rebuilding outbound."
            )
        nodes[node_id]["instruction"]["text"] = text.replace(OLD_LOOKUP_STEP, NEW_LOOKUP_STEP)

    # The lead's number, never the spa's caller ID, goes on a callback.
    msg = nodes["node-message-collect"]["instruction"]
    if "{{user_number}}" not in msg["text"]:
        raise SystemExit("node-message-collect no longer references {{user_number}}.")
    msg["text"] = msg["text"].replace(
        "Their number is {{user_number}} unless they give you a different one.",
        "Their number is {{lead_phone}} - the number we rang them on - unless they give you a different one. Never use the number this call is dialling from; that is the spa's own line.",
    )

    flow["nodes"].extend(NEW_NODES)

    if "{{lead_first_name}}" in OPENING_UNNAMED:
        raise SystemExit("OPENING_UNNAMED references {{lead_first_name}}.")
    if flow["start_node_id"] != "node-out-gate":
        raise SystemExit("start_node_id is not the name gate.")
    if flow.get("start_speaker") != "user":
        raise SystemExit("Outbound must be user-first - the callee says hello before Aria opens.")
    for gid in ("node-greeting", "node-greeting-unnamed"):
        if "your FIRST turn is the opener below" not in nodes[gid]["instruction"]["text"]:
            raise SystemExit(f"{gid} lost the user-first opener note.")
        # V54: the opener cannot be talked over. Line echo (the callee's device
        # playing Aria back ~1 s late) is a copy of whatever she says, so any
        # sensitivity above 0 lets it cut her off; nobody real interrupts a
        # four-second opener. Inherited from the inbound greeting node - abort
        # rather than ship an opener that echo can chop.
        if nodes[gid].get("interruption_sensitivity") != 0:
            raise SystemExit(f"{gid} is interruptible - inbound V54 not in the source flow?")
    if "plays your own voice back to you" not in flow["global_prompt"]:
        raise SystemExit("Turn-taking echo rule (inbound V54) missing from the global prompt.")
    # V55: the massage is chosen in a node that cannot look up times. Every
    # "wants to book" edge must land there, never on discovery directly -
    # call_5a05aadf booked a Swedish nobody asked for when discovery owned
    # both the question and get_slots.
    svc = nodes.get("node-book-service")
    if not svc or svc.get("tool_ids") != ["get_services"] or "global_node_setting" not in svc:
        raise SystemExit("node-book-service missing or reshaped - inbound V55 not in the source flow?")
    if "global_node_setting" in nodes["node-book-discovery"]:
        raise SystemExit("discovery still carries the new-booking trigger")
    # V56: a length answer gets the menu read back in the same turn, never the
    # same question again (call_b316291d looped "what kind of massage?" x3).
    if "We have [every name it returned]" not in svc["instruction"]["text"] or "I can list them" in svc["instruction"]["text"]:
        raise SystemExit("service node lost the V56 list-on-non-answer rule")
    # V57: discovery ends every turn with a question and never says "[Time] it
    # is." as a dead end; the add-ons node says the time back instead.
    if "Never choose for them" not in nodes["node-book-discovery"]["instruction"]["text"]             or "[Time] it is - would you like to add any enhancements?" not in nodes["node-book-addons"]["instruction"]["text"]:
        raise SystemExit("V57 hand-off wording missing from the source flow")
    # V58: both openers refuse to talk over a recording, the name node asks for
    # both spellings, and nothing still points at the removed phone node.
    for gid in ("node-greeting", "node-greeting-unnamed"):
        if RECORDING_RULE not in nodes[gid]["instruction"]["text"]:
            raise SystemExit(f"{gid} lost the recording rule")
    if not nodes["node-book-name"]["instruction"]["text"].startswith(BOOK_NAME_OUTBOUND_HEAD):
        raise SystemExit("name node lost its outbound first line")
    if "Do NOT ask them to spell it" in nodes["node-book-name"]["instruction"]["text"]:
        raise SystemExit("name node still carries the V53 no-spelling wording")
    dangling = [(n["id"], ex.get("id")) for n in flow["nodes"]
                for ex in n.get("finetune_transition_examples", [])
                if ex.get("destination_node_id") and ex["destination_node_id"] not in nodes]
    if dangling:
        raise SystemExit(f"transition examples point at nodes that do not exist: {dangling}")
    direct = [e["id"] for n in flow["nodes"] for e in n.get("edges", [])
              if e["destination_node_id"] == "node-book-discovery" and e["id"] not in ("e-service-chosen", "e-bookfail-retry")]
    if direct:
        raise SystemExit(f"edges start a booking at discovery, bypassing the service node: {direct}")
    strays = [n["id"] for n in flow["nodes"] if n["id"] != "node-out-gate"
              for e in n.get("edges", []) + [x for x in (n.get("else_edge"),) if x]
              if e["destination_node_id"] == "node-greeting"]
    if strays:
        raise SystemExit(f"Nodes route to the named opener without the gate: {strays}")

    flow["knowledge_base_ids"] = [KNOWLEDGE_BASE_ID]


    # Every {{user_number}} that survives anywhere - node, tool schema, or global
    # prompt - is a bug: on an outbound call it resolves to the spa's own line.
    if "{{user_number}}" in json.dumps(flow, ensure_ascii=False):
        offenders = [n["id"] for n in flow["nodes"]
                     if "{{user_number}}" in json.dumps(n, ensure_ascii=False)]
        offenders += [t["name"] for t in flow["tools"]
                      if "{{user_number}}" in json.dumps(t, ensure_ascii=False)]
        if "{{user_number}}" in flow["global_prompt"]:
            offenders.append("global_prompt")
        raise SystemExit(f"Still references the spa's own caller ID: {offenders}")

    return flow


# =============================================================================
# 5. Agent config
# =============================================================================

OUTBOUND_ANALYSIS_FIELDS = [
    {
        "name": "reached_lead",
        "type": "enum",
        "choices": ["lead", "wrong_person", "voicemail", "no_answer", "unclear"],
        "description": "Who or what actually picked up the phone.",
    },
    {
        "name": "outbound_outcome",
        "type": "enum",
        "choices": [
            "booked", "callback_scheduled", "not_interested", "wrong_number",
            "voicemail_left", "do_not_call", "transferred", "other",
        ],
        "description": "How the outbound attempt ended.",
    },
    {
        "name": "do_not_call",
        "type": "boolean",
        "description": "True only if the lead explicitly asked not to be contacted again.",
    },
    {
        "name": "callback_window",
        "type": "string",
        "description": "When the lead asked to be called back, in their own words. Empty if they did not ask.",
    },
]

VOICEMAIL_MESSAGE = (
    "Hi {{lead_first_name}}, this is Aria from Sage and Willow Spa getting back to "
    f"you. Give us a call at {CALLBACK_NUMBER_SPOKEN} and we'll get you scheduled. Thanks!"
)


def build_agent(source_agent: dict, flow_id: str, flow_version: int) -> dict:
    carry = [
        "language", "voice_id", "fallback_voice_ids", "voice_temperature",
        "voice_speed", "volume", "enable_expressive_mode", "expressive_emotion_tags",
        "enable_backchannel", "reminder_trigger_ms", "reminder_max_count",
        "max_call_duration_ms", "interruption_sensitivity", "responsiveness",
        "enable_dynamic_responsiveness", "ring_duration_ms", "stt_mode",
        "allow_user_dtmf", "user_dtmf_options", "denoising_mode",
        "data_storage_setting", "opt_in_signed_url", "end_call_after_silence_ms",
        "post_call_analysis_model", "pii_config", "handbook_config",
    ]
    agent = {k: source_agent[k] for k in carry if k in source_agent}
    agent["agent_name"] = AGENT_NAME
    agent["response_engine"] = {
        "type": "conversation-flow",
        "conversation_flow_id": flow_id,
        "version": flow_version,
    }
    # Latency over letter-perfect transcription (Ubaid, 2026-09-20): names and
    # numbers are no longer spelled back, so the accuracy mode's extra ~200ms
    # per turn buys little. Inbound stays on its own setting until he says so.
    agent["stt_mode"] = "fast"
    agent["end_call_after_silence_ms"] = END_CALL_AFTER_SILENCE_MS
    # Aria's post-call recap e-mail (2026-09-21). call_analyzed is the one event
    # that carries the summary and the analysis fields the e-mail is built from.
    agent["webhook_url"] = POST_CALL_WEBHOOK
    agent["webhook_events"] = ["call_analyzed"]
    agent["voicemail_option"] = {
        "action": {"type": "static_text", "text": VOICEMAIL_MESSAGE}
    }
    agent["post_call_analysis_data"] = (
        source_agent.get("post_call_analysis_data", []) + OUTBOUND_ANALYSIS_FIELDS
    )
    return agent


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Write snapshots but do not touch Retell.")
    ap.add_argument("--prod", action="store_true",
                    help="Point the tools at the PRODUCTION backend (real Wix calendar).")
    ap.add_argument("--publish", action="store_true",
                    help="Publish the agent after updating it.")
    args = ap.parse_args()
    target_webhook = INBOUND_WEBHOOK if args.prod else OUTBOUND_WEBHOOK
    backend_label = "PRODUCTION (client's real Wix calendar)" if args.prod else "DEV (test Wix credentials)"

    print(f"Fetching inbound flow {SOURCE_FLOW_ID} v{SOURCE_FLOW_VERSION} ...")
    source_flow = request("GET", f"/get-conversation-flow/{SOURCE_FLOW_ID}?version={SOURCE_FLOW_VERSION}")
    print(f"  {len(source_flow['nodes'])} nodes, {len(source_flow['tools'])} tools")

    flow = build_flow(source_flow, target_webhook)
    FLOW_SNAPSHOT.write_text(json.dumps(flow, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  built outbound flow: {len(flow['nodes'])} nodes -> {FLOW_SNAPSHOT.name}")

    source_agent = request("GET", f"/get-agent/{SOURCE_AGENT_ID}")

    if args.dry_run:
        agent = build_agent(source_agent, "DRY_RUN", 0)
        AGENT_SNAPSHOT.write_text(json.dumps(agent, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  built agent config -> {AGENT_SNAPSHOT.name}")
        print("Dry run - Retell not modified.")
        return

    state = json.loads(STATE_PATH.read_text(encoding="utf-8")) if STATE_PATH.exists() else {}

    if state.get("conversation_flow_id"):
        created_flow = request(
            "PATCH", f"/update-conversation-flow/{state['conversation_flow_id']}", flow
        )
        print(f"Updated flow {created_flow['conversation_flow_id']} v{created_flow['version']}")
    else:
        created_flow = request("POST", "/create-conversation-flow", flow)
        print(f"Created flow {created_flow['conversation_flow_id']} v{created_flow['version']}")

    agent = build_agent(
        source_agent, created_flow["conversation_flow_id"], created_flow["version"]
    )
    AGENT_SNAPSHOT.write_text(json.dumps(agent, indent=2, ensure_ascii=False), encoding="utf-8")

    if state.get("agent_id"):
        created_agent = request("PATCH", f"/update-agent/{state['agent_id']}", agent)
        print(f"Updated agent {created_agent['agent_id']} v{created_agent['version']}")
    else:
        created_agent = request("POST", "/create-agent", agent)
        print(f"Created agent {created_agent['agent_id']}")

    STATE_PATH.write_text(json.dumps({
        "conversation_flow_id": created_flow["conversation_flow_id"],
        "conversation_flow_version": created_flow["version"],
        "agent_id": created_agent["agent_id"],
        "agent_version": created_agent.get("version"),
        "flow_name": FLOW_NAME,
        "agent_name": AGENT_NAME,
    }, indent=2), encoding="utf-8")

    print(f"  agent_id: {created_agent['agent_id']}")
    print(f"  backend:  {target_webhook}  {backend_label}")

    if not args.publish:
        print("  NOT published. The trigger workflow decides which version it dials.")
        return

    request("POST", f"/publish-agent/{created_agent['agent_id']}")
    versions = sorted(request("GET", f"/list-agent-versions/{created_agent['agent_id']}")["items"],
                      key=lambda v: v["version"], reverse=True)
    pub = max(v["version"] for v in versions if v.get("is_published"))
    served_agent = request("GET", f"/get-agent/{created_agent['agent_id']}?version={pub}")
    served_flow = request("GET", f"/get-conversation-flow/{served_agent['response_engine']['conversation_flow_id']}"
                                 f"?version={served_agent['response_engine']['version']}")
    served_urls = sorted({t.get("url") for t in served_flow["tools"] if t.get("url")})
    print(f"  PUBLISHED -> agent v{pub} ({served_agent['agent_name']})")
    print(f"  published version's tools: {served_urls}")
    if served_urls != [target_webhook]:
        raise SystemExit("PUBLISHED VERSION IS NOT ON THE INTENDED BACKEND - fix immediately.")


if __name__ == "__main__":
    main()
