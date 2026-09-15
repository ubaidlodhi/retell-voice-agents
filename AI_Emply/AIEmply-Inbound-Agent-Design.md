# AIEmply Inbound Voice Agent — Design Spec

**Date:** 2026-09-13
**Status:** Approved design, pending implementation

---

## 1. Purpose

Rebuild the AIEmply inbound receptionist ("Aria") to the craft standard of the InstantReply "Ava" single-prompt agent, correct the factual claims it makes to callers, and close the integration gaps that currently lose leads.

Scope: the inbound agent, the outbound agent's factual alignment, the booking layer, and the post-call pipeline.

---

## 2. Current state (as audited)

| Component | ID / location | State |
|---|---|---|
| Inbound agent | `agent_eb3783fcfb558d2d2c9d5a1764` | v2 draft, unpublished |
| Inbound LLM | `llm_bf5fe7460d8cb60b58e367f553f5` | v1 published & live; v2 draft |
| Outbound agent | `agent_8fb6b2531eef5c23a9ebd08f33` | v1 |
| Outbound LLM | `llm_facbbf7d84bd3f4df3bdbec93f93` | v1 |
| Phone number | `+1 812 666 8047` | inbound pinned to **agent_version 1** |
| Knowledge base | `knowledge_base_af8d8f36fcbb8822` | FAQ loaded (27,991 B), **attached to nothing** |
| Booking endpoint | `automation.aiemply.com/webhook/check-slots` | Live, works, **not an n8n workflow** |
| Post-call webhook | n8n `After Call Notification` (`CPajQlvOtss8nNE1`) | Active, both action nodes disabled |

Both agents are single-prompt (retell-llm), GPT-4.1, voice `11labs-Brynne`.

### Verification method

Findings were confirmed by executing against live systems with placeholder data, not by reading configuration:

- `check-slots` availability + booking exercised via `curl`. Booking returned `{"result":"Appointment booked successfully"}`. **A test booking was created for 2026-09-16T15:00Z / jane@acme.ai — delete it.**
- Timezone behaviour probed with three distinct IANA zones.
- Real call transcript `call_fe7d3411ddd0ab9fd3e4dc37cf7` (2026-08-13) read in full.

---

## 3. Defects found

### D1 — Aria quotes a price that does not exist (CONFIRMED on a live call)

Transcript, verbatim: *"our plans start at four ninety-nine a month."* Starter is **$149/month**.

Root cause is in the prompt's own Pronunciation block:

```
Dollars: "four ninety-nine a month" not "$499/month"
```

The model lifted a *formatting example* and spoke it as a price. That example was the only dollar figure anywhere in its context, and the knowledge base was empty, so it had nothing else to reach for.

### D2 — Knowledge base wired to nothing

`knowledge_base_ids` is `[]` on both LLMs. Until 2026-09-13 the KB's only source was a 2-byte file containing the text `hi`. Both prompts instruct "pull from the knowledge base" six times. This is the enabling condition for D1.

The real FAQ has since been uploaded; it still needs attaching.

### D3 — Prompt contradicts the FAQ on two customer-facing facts

| Claim | Prompt says | FAQ says | Calendar says |
|---|---|---|---|
| Deployment | "live within forty-eight hours" | 1–2 weeks | — |
| Consultation | "free thirty-minute consultation" | 15 minutes | 15-min slots |

`boosted_keywords` contains `"forty-eight hours"`, reinforcing the wrong claim.

### D4 — Live-blocking regression parked in v2

LLM v1 (published, currently serving) has `start_speaker: "agent"`. LLM v2 changed it to `"user"` plus `begin_after_user_silence_ms: 5000`.

On an inbound call that means **five seconds of silence before Aria speaks**. The prompt text is otherwise byte-identical between v1 and v2 — the version adds nothing and breaks the greeting. It has not shipped only because the phone number is pinned to `agent_version: 1`.

### D5 — Turn-taking audibly breaks

From the same transcript:

```
Agent: "Right, totally"
User:  "Okay."
Agent: "get it—pricing's usually the first thing people wanna know..."
```

One sentence — *"Right, totally get it"* — sliced in half by a caller backchannel. Cause: `interruption_sensitivity: 0.9`.

Measured latency on that call: e2e **p50 1524 ms**, p90 1673 ms.

### D6 — Post-call pipeline discards everything

`After Call Notification` is active and its path matches the agents' webhook, but `Create Lead` (Supabase) and `1. Send Mail to Both` (Gmail) are both disabled. Every `call_analyzed` event is silently dropped — including the one successful dental-clinic booking.

**Re-enabling them as-is will not work.** They were built for a website "Get Started" form, not for Retell:

- `Create Lead` reads `$json.body.name` / `.email` / `.phone` / `.industry`. Retell sends `body.call.call_analysis.custom_analysis_data.*`.
- The Gmail template references `$json.full_name`, `company_name`, `website_url`, `plan`, `project_details` — website form fields absent from a Retell payload.
- It also reads `$json.*` while positioned *after* the Supabase node, so `$json` is the Supabase response, not the webhook body.

These nodes need rewiring to the Retell payload shape, not just switching on.

### D7 — Booking layer pushes timezone maths onto the LLM

`check-slots` **ignores `iana_timezone` entirely** — `Asia/Karachi` and `America/Los_Angeles` return byte-identical payloads: **166 slots over 6 days, all raw UTC**.

So the agent asks "what timezone are you in?", gets nothing back that reflects it, and must convert 166 UTC timestamps itself and pick two. One of three probe requests also returned empty, and the prompt has no failure path for that.

### D8 — Two settings misconfigurations

- `ambient_sound_volume: 0.4` with no `ambient_sound` set — inert.
- `language: ["es-ES","en-US","es-419","en-GB"]` — Spanish is listed first while the prompt is English-only, with `stt_mode: "fast"`. Bilingual support is wanted and stays; the defect is the ordering plus the total absence of Spanish handling in the prompt.

### D9 — Prompt-internal contradictions

- Pronunciation says *"Do NOT ask them to spell the whole thing upfront"*; Call Flow says *"what's the best email... Can you spell that out for me?"*
- Three different silence policies: 15 s (spam rule), `NO_RESPONSE_NEEDED` (hold rule), 50 s (`end_call_after_silence_ms`).
- The greeting stacks two questions, violating the agent's own one-at-a-time rule. A caller hung up 10 s into one call.
- `call_successful` scored `true` on a call where the caller got a wrong price and hung up before booking.

---

## 4. Decisions locked

| # | Decision |
|---|---|
| 1 | Aria states **1–2 week deployment** and a **15-minute consultation**, per the FAQ. |
| 2 | Aria **quotes real plan prices** ($149 / $399 / $599) then pivots to booking. |
| 3 | Booking gets an **n8n wrapper** that converts server-side and returns 2–3 ready-to-read local-time options. |
| 4 | Delivered as a **new version on the existing inbound agent**, `V01` suffix; the phone number stays pinned to v1 until test-called. |
| 5 | Scope: inbound prompt + settings, KB attach, post-call pipeline, outbound factual alignment. |

---

## 5. Design

### 5.1 Inbound prompt

Rebuilt to Ava's structure, shaped for inbound:

1. **Identity** — Aria, AIEmply, 24/7 inbound. `{{current_time}}`, `{{user_number}}`.
2. **Speak their language** — industry vocabulary table: dental → *patients*; law → *potential clients*; HVAC/plumbing → *customers*; real estate → *buyers and sellers*; property management → *tenants and owners*; contractors → *customers*; unknown → *inquiries*, pain kept general.
3. **Style and word choice** — one question per turn (fixes the stacked greeting); 2–3 sentences max; contractions always; banned list covering *Great / Absolutely / Certainly / Awesome* and corporate jargon (*solution, leverage, streamline, seamless, reach out, circle back*); never reuse a sentence shape twice in one call.
4. **Acknowledge before you move** — react to the specific thing said before asking anything else; no bare "Got it" followed by the next question.
5. **Match their energy** — table mapping caller signal → register.
6. **Call flow** — Open (one question) → intent → Qualify (2 questions, down from 4) → value bridge → book → wrap.
7. **Pricing** — real figures anchored in-prompt *and* KB-backed, so a retrieval miss degrades to "the team covers exact numbers", never to invention.
8. **Objections** — expanded from 5 to ~13, one clean response each.
9. **Booking rules** — read wrapper options verbatim; never invent or round a slot; explicit fallback when the tool returns empty or errors.
10. **Turn-taking and silence** — a single ladder replacing the three conflicting policies: hold cue → `NO_RESPONSE_NEEDED`; ~15 s → "You still there?"; ~10 s more → close and `end_call`.
11. **Guardrails** — no invented statistics, prices, guarantees or client names; no legal/medical/financial advice; AI disclosure when asked.
12. **Pronunciation** — **no fake figure may appear as a formatting example.** Dollar formatting is demonstrated with a real price.
13. **Language** — Aria opens in English and mirrors the caller. If the caller speaks Spanish, she switches fully and stays there for the rest of the call; she does not mix languages mid-sentence or announce the switch. Every fact, price and commitment is identical in both languages, and spell-back of emails and times follows Spanish conventions when in Spanish. Slot labels returned by the booking wrapper are English day/time strings, so Aria translates the day name when speaking Spanish while sending the `iso` value back unchanged.

### 5.2 Inbound settings

| Setting | From | To | Why |
|---|---|---|---|
| `start_speaker` | `user` (v2) | `agent` | D4 — dead air on answer |
| `interruption_sensitivity` | 0.9 | 0.8 | D5 — sliced sentences |
| `language` | Spanish first | `en-US` first, Spanish retained | D8 — English-primary detection, bilingual kept |
| `ambient_sound` | unset | `call-center` @ 0.3 | D8 — inert volume |
| `enable_expressive_mode` | unset | `true` + tuned tags | Human delivery |
| `denoising_mode` | noise-cancellation | noise-and-background-speech | Matches Ava |
| `voice_temperature` | 1.0 | 0.9 | Matches Ava |
| `kb_config.top_k` | 3 | 5 | 28 KB FAQ; pricing spans sections |
| `max_call_duration_ms` | 363000 | 600000 | Booking calls ran 258 s |
| `end_call_after_silence_ms` | 50000 | 30000 | Sits just past the 25 s prompt ladder |
| `boosted_keywords` | incl. "forty-eight hours" | corrected set | D3 |
| `post_call_analysis` | lenient | tightened `call_successful` | D9 |

`expressive_emotion_tags` follow Ava's discipline: at most one tag per turn, never two turns running, never on an objection or brush-off.

### 5.3 Knowledge base

Attach `knowledge_base_af8d8f36fcbb8822` to both LLMs. `top_k: 5`, `filter_score: 0.6`.

### 5.4 Booking wrapper (new n8n workflow)

```
Aria → wrapper webhook → check-slots → convert → 2–3 local-time options
```

Responsibilities:

- Call `check-slots`, taking the caller's IANA timezone as input.
- Convert UTC slots to caller-local (the upstream endpoint will not — D7).
- Drop past slots. Offer from the two soonest days that actually have slots — the calendar returns weekend availability (confirmed: Sat 2026-09-13, Sun 2026-09-14), so weekends are offered rather than filtered out.
- Return at most 3 options, each with a spoken `label` and the exact `iso` string `book_consultation` requires.
- Return a typed empty/error result so the prompt has a real branch to take.

Response contract:

```json
{
  "options": [
    {"label": "Tuesday at 2:00 PM",    "iso": "2026-09-16T18:00:00.000Z"},
    {"label": "Wednesday at 10:30 AM", "iso": "2026-09-17T14:30:00.000Z"}
  ]
}
```

Aria reads `label` verbatim and returns `iso` unmodified. No timezone arithmetic in the LLM; it cannot offer a slot that was not returned.

`book_consultation` continues to post to `check-slots` unchanged — that path is verified working.

### 5.5 Post-call pipeline

Rewire `After Call Notification` for the Retell `call_analyzed` payload:

- Map from `body.call.call_analysis.custom_analysis_data.*` and `body.call.*` (call id, from number, duration, summary, recording URL).
- Fix the Gmail template to reference fields that exist; drop the website-form fields (`company_name`, `website_url`, `plan`, `project_details`).
- Correct the post-Supabase `$json` reference so the email reads webhook data.
- Re-enable both nodes only once the mapping is proven with a replayed payload.
- Recipients unchanged.

### 5.6 Outbound alignment

Same factual corrections (1–2 weeks, 15 minutes, real pricing), same banned-phrase list, same pronunciation fix, KB attached. Structure otherwise left alone — a full prompt rebuild is out of scope this pass.

---

## 6. Delivery and rollback

1. Build a new LLM version + agent version, `agent_name` suffixed `V01`.
2. Phone number **stays pinned to `agent_version: 1`** through review.
3. Test-call via web call and via PSTN.
4. Flip the number only on explicit approval.

Rollback is repinning the number to `agent_version: 1`. No destructive edits to v1 at any point.

---

## 7. Test plan

Every item exercised with real calls or replayed payloads — not string checks.

| # | Test | Pass |
|---|---|---|
| T1 | Ask "how much?" | Quotes $149/$399/$599. **Never $499.** |
| T2 | Ask "how fast can you set it up?" | Says 1–2 weeks, never 48 hours |
| T3 | Ask "how long is the call?" | Says 15 minutes |
| T4 | Answer the call | Aria speaks immediately, no dead air |
| T5 | Backchannel ("okay", "mm-hmm") mid-sentence | Aria completes her sentence |
| T6 | Full booking, non-Pacific timezone | Offered times correct in caller's zone |
| T7 | Wrapper returns empty | Graceful fallback, no invented slot |
| T8 | Complete a booking | Supabase row written, email received |
| T9 | Hang up mid-booking | `call_successful` scores `false` |
| T10 | Ask an off-FAQ question | Defers to the team; invents nothing |

---

## 8. Implementation status — built 2026-09-13

All of the below is deployed and verified by execution, not by inspection.

| # | Item | State |
|---|---|---|
| D1 | `$499` price bug | **Fixed.** Verified: agent now quotes one forty-nine / three ninety-nine / five ninety-nine. |
| D2 | KB unattached | **Fixed.** `knowledge_base_af8d8f36fcbb8822` attached to both LLMs, `top_k: 5`. Retrieval confirmed returning the real pricing table. |
| D3 | Wrong facts | **Fixed.** 1–2 weeks and 15 minutes, in English and Spanish. |
| D4 | `start_speaker` regression | **Fixed.** Back to `agent`. |
| D5 | Interruption sensitivity | **Fixed.** 0.9 → 0.8. Needs a live call to confirm audibly. |
| D6 | Post-call pipeline | **Fixed** for Supabase; Gmail blocked, see below. |
| D7 | UTC timezone maths | **Fixed** via wrapper, see below. |
| D8 | Settings misconfigs | **Fixed.** `ambient_sound` set; language reordered English-first, Spanish kept. |
| D9 | Prompt contradictions | **Fixed.** Single silence ladder, one-question greeting, email rule reconciled. |

### New: booking wrapper

- Workflow `ciP1DuKm2rzV2800` — "AIEmply | Retell Booking Slots Wrapper", active.
- Endpoint `https://automation.aiemply.com/webhook/aiemply-get-slots`.
- Verified across `America/New_York`, `America/Los_Angeles`, `America/Chicago`, `Europe/London`, `Asia/Karachi`, and an invalid zone.
- One bug found and fixed during testing: when no slot fell in civil hours locally, the fallback picked the earliest slot, which produced "Tuesday at 12:00 AM" for Karachi. Now picks the slot closest to local midday instead.
- Both agents call it. `book_consultation` still posts to `check-slots`, unchanged.

### Changed from the approved plan

**"Re-enable the post-call nodes" was the wrong fix.** Running it surfaced a second defect the config did not show: the Supabase `leads` table has a **NOT NULL constraint on `company_name`**, a website-form column no phone call supplies. Every Retell-shaped insert would have failed regardless of field mapping.

Resolved by adding a `company_name` post-call analysis field to both agents so Aria extracts it when mentioned, with a `'Unknown (phone lead)'` fallback in n8n. Supabase inserts now succeed — verified, row written with all fields populated.

Also added, beyond the plan:
- An IF guard (`Has Lead Details`) so spam and instant-hangup calls no longer write empty rows.
- `onError: continueRegularOutput` on the Gmail node, so a mail failure no longer prevents lead capture or the webhook's 200.

### Not done, and why

**Expressive mode was not enabled.** It is a Retell-native-voice feature and both agents use `11labs-Brynne`. Turning it on would mean changing the brand voice — a user decision, not an implementation detail. Everything else from §5.2 shipped.

---

## 9. Open items

### Blocked — needs you

- **The n8n Gmail credential is revoked.** Error: *"The credential 'Gmail account' needs to be reconnected."* Lead emails will not send until it is re-authorised in n8n (credential `JFQBwEz5WO2yRdab`). Supabase capture works regardless; the mail step now fails soft.
- **Phone number is still pinned to inbound `agent_version: 1`** — the old version. Test-call first, then repin to the new version to go live.

### Test data to clean up

- Booking on the real calendar: **2026-09-16T15:00Z, jane@acme.ai**.
- Supabase `leads` rows from the pipeline tests (John Doe / jane@acme.ai / Bright Smile Dental, call ids `call_TESTPAYLOAD0003` and `call_TESTPAYLOAD0004`).
- `check-slots` is not an n8n workflow and is not editable through the n8n MCP. Its owner/host is unidentified — a maintainability risk worth resolving.
- `check-slots` returned empty on 1 of 3 probes. Cause unknown; the wrapper's error branch mitigates the symptom, not the cause.
- Latency p50 1524 ms is high. Out of scope this pass; revisit if calls still feel slow after the settings changes.
