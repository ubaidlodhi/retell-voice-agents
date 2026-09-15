# Dental Practice Agent Template

Single-prompt Retell agent for a dental front desk. Built from the Sage & Willow
sample, so it carries the same full settings surface: 62 of 62 agent fields and
21 of 21 LLM fields populated, validated against the live `createAgent` and
`createRetellLLM` schemas.

## Files

- `Sample Agent - Dental.json` — importable Retell agent.
- `dental_prompt.md` — the same prompt as a standalone editable file.

## Before go live: replace all 28 placeholders

Most of them live in one block, the `# Practice Facts` section near the top of
the prompt. Edit that block first, then sweep the rest.

### Identity
- `[PRACTICE NAME]`
- `[AGENT NAME]`
- `[CITY]`, `[STATE]`, `[ZIP]`
- `[PRACTICE ADDRESS]`
- `[PRACTICE WEBSITE]` and `[PRACTICE WEBSITE SPOKEN]` (how it should be read aloud)
- `[PARKING DETAIL]`

### People
- `[PROVIDER 1]`, `[PROVIDER 2]`
- `[HYGIENIST 1]`, `[HYGIENIST 2]`

### Schedule
- `[OPENING TIME]`, `[CLOSING TIME]`
- `[OPEN DAYS]`, `[CLOSED DAYS]`, `[HOLIDAY CLOSURES]`
- `[TIMEZONE]` — see the warning below
- `[AFTER HOURS INSTRUCTION]`

### Booking
- `[NEW PATIENT EXAM TYPE]` — the exact catalog name for a new patient visit
- `[EMERGENCY SLOT TYPE]` — the exact catalog name for a same-day urgent visit
- `[APPOINTMENT TYPE]` — used only in readback examples
- `[NEW PATIENT FORM INSTRUCTION]`

### Policy
- `[CANCELLATION NOTICE WINDOW]`
- `[LATE CANCEL FEE POLICY]`

### Other
- `[SECOND LANGUAGE]` — or delete the bilingual paragraph in `# Brand Voice`
- `[PRACTICE TRANSFER NUMBER IN E164]` — in `retellLlmData.default_dynamic_variables.transfer_number`

## Two placeholders that break things if you miss them

1. `[TIMEZONE]` appears inside dynamic variables: `{{current_time_[TIMEZONE]}}`
   and `{{current_calendar_[TIMEZONE]}}`. Retell needs a literal IANA zone, so
   these do not resolve until you substitute. Replace with the zone name only,
   for example `{{current_time_America/New_York}}`. Also set the agent-level
   `timezone` field to the same value.

2. `transfer_number` must become a real E.164 string, for example
   `+15551234567`. The `transfer_to_human` tool points at `{{transfer_number}}`
   rather than a hardcoded number, so this is the only place to change it.
   Retell rejects a literal placeholder in `transfer_destination.number` at
   import time, but accepts the dynamic variable, which is why it is wired this
   way. An unreplaced value fails at transfer time instead of import time.

## Import gotcha: fallback voices

`fallback_voice_ids` must come from a different TTS provider than `voice_id`.
Retell rejects the import with "Cannot have main voice and fallback voices from
the same provider." The main voice here is `11labs-Brynne`, so the fallbacks are
the same Brynne character on three other providers: `cartesia-Brynne`,
`minimax-Brynne`, `inworld-Brynne`. If you change the main voice, change these
too.

## Verified

Both this template and the spa sample were round-tripped through the live API
(`POST /create-retell-llm` then `POST /create-agent`, both 201, probe objects
deleted). All settings survive the trip: 8 webhook events, 15 post-call fields,
21 boosted keywords, 4 pronunciation entries, 9 handbook presets, 7 guardrail
topics, 9 PII categories.

## Webhook endpoints to build

All eight custom tools POST to the placeholder `https://example.com/webhook/retell-dental`
and route on the `tool` header. Replace `example.com` with your automation host
before go live; a placeholder URL imports fine but every tool call fails at
runtime until it points somewhere real.

| Tool | Header value |
|---|---|
| `get_appointment_types` | `get-appointment-types` |
| `get_providers` | `get-providers` |
| `get_slots` | `get-slots` |
| `book_appointment` | `book-appointment` |
| `get_appointment` | `get-appointment` |
| `cancel_appointment` | `cancel-appointment` |
| `reschedule_appointment` | `reschedule-appointment` |
| `flag_callback` | `flag-callback` |

All use `args_at_root: true`, so arguments arrive at the top level of the body,
not nested under a `call` object.

Agent-level `webhook_url` is the placeholder
`https://example.com/webhook/retell-dental-events` for the eight call lifecycle
events. Same rule: swap the host before go live.

## Scope

Insurance is deliberately out of scope. There is no verification tool and the
prompt never asks for a carrier or member ID. Any cost, coverage, bill or claim
question routes to a billing callback via `flag_callback`.

## Prompt size

3,364 tokens (o200k_base), under Retell's ~3,500-token base-rate line. The
first draft was 5,108; the cut came from merging tool discipline into the tool
list, collapsing escalations into one section, folding records requests into
Patient Privacy, and tightening every flow to one line per step.

## Compliance design notes

Three prompt sections carry the risk in a dental agent, and each has a matching
post-call analysis field so you can audit them per call:

| Prompt section | Audit field |
|---|---|
| `# Clinical Boundaries` | `clinical_boundary_held` |
| `# Flow: Cost Questions` | `no_cost_quoted` |
| `# Patient Privacy` | `identity_verified_before_disclosure` |

Filter call history on any of these coming back false to find the calls worth
listening to.

`# Flow: Emergency Triage` runs before any booking flow whenever pain,
swelling, bleeding or trauma comes up. Step one screens for red flags that need
911 or an ER, not a dental chair. It triages urgency only and never names a
condition. `emergency_triage_result` records how each one resolved.

## What is deliberately absent from the prompt

Ten Agent Handbook presets are enabled in `handbook_config`, and the prompt does
not restate any of them:

`conversational_personality`, `natural_filler_words`, `high_empathy`,
`echo_verification`, `nato_phonetic_alphabet`, `speech_normalization`,
`smart_matching`, `ai_disclosure`, `scope_boundaries`.

So there is no pronunciation section, no personality section, no "one question
per turn" rule and no generic "do not fabricate" rule in the prompt. Turning a
preset off means writing its guidance back into the prompt by hand.

The one deliberate conflict is `# Capturing the Patient's Name`, which overrides
`echo_verification` for names only. It is labeled as an override in the prompt.

## Formatting rules this template follows

No asterisks, no em dashes, no en dashes, no smart quotes, anywhere in the
prompt or in any tool description. Headings are markdown hashes only. Keep it
that way when you edit, since these characters get read aloud or mangled by TTS.
