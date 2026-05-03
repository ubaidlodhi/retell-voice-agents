# Sage & Willow Spa — Build Deliverables

> **Source documents reviewed**
> - [client-discovery-call-transcript.md](client-discovery-call-transcript.md)
> - [AIEmply_Sage & Willow Spa_Onboarding_Sheet.xlsx](AIEmply_Sage%20%26%20Willow%20Spa_Onboarding_Sheet.xlsx)
> - [Retell AI ↔ Wix Bookings _ Production v2.json](Retell%20AI%20%E2%86%94%20Wix%20Bookings%20_%20Production%20v2.json)
>
> **Plan:** Starter AI Employee — $149/mo (100 included minutes, $0.30/min overage)
> **Build target:** Single Retell AI inbound voice agent (Aria) routing to the production n8n Wix Bookings webhook.
> **Voice:** Iniga-Yang Adult Female (confirmed by client via email, 2026-04-24).

---

## 1. Client snapshot

| Field | Value |
|---|---|
| Business | Sage & Willow Spa |
| Owner | Chen Ma (Nicky) |
| Address | 400 Rowland Blvd, Novato, CA 94947 (intersection of Rowland & Novato Blvd) |
| Service area | Novato + surrounding Marin County |
| Business phone | +1 628-682-8010 (forwards from spa landline → Nicky's mobile) |
| Carrier | AT&T |
| Hours | 7 days/week, 10:00 AM – 8:00 PM (PT, Novato CA) |
| Closed | Christmas Day, Thanksgiving Day |
| Staffing | 1 full-time therapist (Nicky) + 2 part-time |
| Booking platform | Wix Bookings (already integrated via n8n workflow) |
| Website | https://www.sagewillowspa.com |
| Booking URL | https://www.sagewillowspa.com/reservation |
| Instagram | instagram.com/sagewillow2025 |
| Escalation / dashboard email | sagewillowspa@gmail.com |
| Languages | English (primary), Spanish (secondary, bilingual) |

---

## 2. What the client wants — scope of the agent

From the discovery call, Nicky has three concrete goals (in priority order):

1. **Catch missed calls while she is in session.** The spa landline rings her personal mobile; during a massage she cannot pick up. Currently averaging 5–9 calls/day, ~⅓ are spam.
2. **Book appointments directly into the Wix calendar.** She explicitly does *not* want "send the link" behaviour — the AI must complete the booking on the call.
3. **Filter spam and advertising calls** so she stops losing 10 minutes per junk call.

Two operational requirements layered on top:
- **Ring routing:** call rings Nicky's number first; after **3–4 rings unanswered**, the carrier/forwarding rule sends the call to the Retell agent. (Forwarding rule is configured outside Retell — we just receive whatever the carrier hands us.)
- **No live human transfer.** If AI cannot answer a question, it must **NOT** warm-transfer back to Nicky (she's the reason the call rolled over in the first place). Instead it must capture the question + caller details and **flag her by SMS + email** so she can call back. This was explicit in the call.

### In scope (Phase 1 — this build)

- Inbound voice agent "**Aria**" (female, soft / calm / warm voice — confirmed in call)
- Greeting + recording-consent disclosure (CA two-party consent)
- Spam / solicitation deflection
- "Full-service / happy-ending" deflection (professional redirect)
- Service info Q&A backed by live Wix data + KB
- Direct appointment booking, cancellation, reschedule, lookup (via existing n8n Wix workflow)
- Bilingual EN/ES handling
- FAQ knowledge base (parking, hours, payments, gift cards, prenatal, etc.)
- Unanswered-question capture → email/SMS flag to Nicky
- Post-call analysis fields (intent, booking outcome, lead capture, spam classification, escalation flag)
- HIPAA-aware handling (do not push medical detail beyond what is needed for booking; do not store/recite back conditions unnecessarily)

### Out of scope (Phase 2 — future build)

- Outbound promotion/marketing campaigns to existing client list (mentioned by Ubaid as Phase 2 once Phase 1 is live)
- CRM sync (no CRM today; contacts log to AIEmply dashboard only)
- Live warm-transfer to Nicky during business hours

---

## 3. Conversation surface (call flow at a glance)

```
INBOUND (after carrier forwards on no-answer)
   │
   ├─ Greeting + recording-consent disclosure (CA)
   │
   ├─ Intent classification
   │     ├─ Spam / sales / solicitation     → polite decline + end
   │     ├─ Inappropriate ("full service")  → professional redirect + end
   │     ├─ Booking (new appointment)       → BOOKING FLOW
   │     ├─ Manage existing booking         → LOOKUP → cancel / reschedule
   │     ├─ Service / pricing / hours / FAQ → KB or get-services tool
   │     ├─ Emergency (medical)             → "Please call 911" + end
   │     └─ Complex / unknown query         → CALLBACK CAPTURE
   │
   └─ Closing line + end
```

### 3.1 Booking flow — required slots

Per onboarding sheet section 4 + section 6 qualification questions:

1. Name (first + last) — *required*
2. Best phone number — *required* (default to caller ID if they confirm)
3. Email — *optional but strongly preferred* (needed for Wix `book-appointment`)
4. Service type — *required* (validate against `get-services`)
5. Duration option (60 / 90 / 120 min) — *required*
6. New or returning client — *required*
7. Health conditions / injuries / allergies — *optional*, ask but do not force
8. Preferred date + time — *required* (validate against `get-slots`)
9. Add-ons / enhancements — *required ask*, optional answer
10. How they heard about us — *optional* (post-call analysis field)

> **Email handling:** the n8n `book-appointment` validator marks `email` as required, but qualification lists it optional. Resolution (decided): ask for email; if the caller declines, fall back to **`sagewillowspa@gmail.com`** so the Wix call still succeeds. The confirmation lands in Nicky's inbox and she has the caller's phone number to follow up. No synthesized/fake addresses.

### 3.2 Hard policy lines (must be enforced in prompt, not KB)

| Trigger | Behaviour |
|---|---|
| "Full service" / "happy ending" / similar | "We are a professional massage spa and only provide therapeutic and relaxation massage services." Then offer to book a legitimate service or end the call. Do **not** moralize. |
| Marketing / sales pitch | "We're not interested in marketing offers — thank you, have a good day." End. |
| Robocall / silence / DTMF tones | End call. |
| Caller asks for specific gender/ethnicity therapist | Acknowledge preference, do not promise; check with `get-staff` and offer what is available. (See onboarding Q34.) |
| Medical emergency mentioned | "If this is a medical emergency, please hang up and call 911 immediately." End. |
| Question AI cannot answer | Take name + callback number + brief description, fire callback-capture tool, promise Nicky will call back. |
| Cancellation < 24 hr | State 24-hr policy, still allow cancel via tool, log it. |
| No-show / "what if I don't show up?" | Communicate the 24-hr cancellation policy; no fee is charged. (Nicky follows up personally with no-shows.) |

### 3.3 After-hours behaviour

The spa is open 10 AM – 8 PM 7 days/week, so "after-hours" only fires outside that window or on Christmas/Thanksgiving. After-hours script (from onboarding sheet 1):

> "Thank you for calling. We're currently closed, but we'd love to take care of you. You can book your appointment anytime online, or I can help you schedule now. What day were you looking for?"

The booking tool works 24/7, so we can take the booking on the call regardless of hours.

---

## 4. Token-efficient knowledge architecture

The whole point: **don't dump everything into the system prompt.** Split content by *how often it's needed* and *whether it changes*.

### 4.1 SYSTEM PROMPT (small, always loaded)

Goes in the Retell agent prompt because it governs every turn:

- Identity: name (Aria), role, brand voice keywords (healing / calming / welcoming / restorative / natural)
- Persona: soft, calm, warm, conversational — never robotic, never salesy
- Language rule: respond in the language the caller uses; switch fluidly EN ↔ ES
- Greeting line, closing line, recording-consent line
- Hard policy lines from §3.2 (spam, full-service deflection, emergency, no warm transfer)
- Booking-flow slot list + the 24-hr cancellation policy line
- Tool usage rules (when to call which tool, how to read the response)
- Output style: short sentences, one question at a time, confirm before booking
- Privacy: don't read back health info unprompted; do not store SSN/payment card data

**Approximate prompt budget: ~1,500–2,000 tokens.** Anything that doesn't change conversation behaviour goes elsewhere.

### 4.2 RETELL KNOWLEDGEBASE (RAG — fires only when relevant)

Goes in KB because it's long, mostly static, and only needed when the caller asks. The agent retrieves a chunk only on FAQ-style turns, so we don't pay tokens for it on every turn.

**KB document 1 — `business_facts.md`**
- Address, parking, directions
- Full hours including holiday closures
- About / mission / unique selling points
- Service-area description (Novato + Marin County)
- Years in business, staffing summary
- Languages spoken
- Payment methods, gratuity policy, gift cards, insurance stance

**KB document 2 — `faqs.md`**
The 28 Q&A pairs from onboarding tab 7, lightly cleaned. Resolved per client email thread (2026-04-24 → 2026-04-25):
- Q23 (specific therapist request): *"Yes, you can request a preference. We'll do our best to accommodate based on availability."*
- Q28 (how early to arrive): *"We recommend arriving 5–10 minutes early so you have time to settle in."*
- Q29 (receipts): *"Yes, we can email or print a receipt after your session."*
- Q30 (book next session): *"Absolutely — your therapist can help you schedule your next visit before you leave."*
- No-show: communicate 24-hr cancellation policy only — no fee.

Coverage areas:
- Hours, location, parking
- Cancellation / no-show / rescheduling
- Walk-ins
- Gift cards, payment, gratuity, insurance, receipts
- Prenatal eligibility, intake forms, what to wear/bring
- Memberships / packages (currently "contact us")
- Late arrival policy, "how early should I arrive"
- Couples massage availability
- Therapist preference handling
- Service-choice guidance ("which massage should I choose?")
- "Full service" rejection variants (×3)
- Therapist gender/ethnicity request handling

**KB document 3 — `service_descriptions.md`**
Long-form 1–3 sentence descriptions of the 7 services + 4 add-ons (already in onboarding tab 5). Used when a caller asks "what's the difference between Swedish and Deep Tissue?" — the description is too long for the prompt but small for RAG.

**KB document 4 (optional) — `website_scrape.md`**
One-time scrape of:
- `sagewillowspa.com` (home / about)
- `sagewillowspa.com/reservation` (booking page copy, if it has anything we don't already have)
- `sagewillowspa.com/services` (any service detail beyond the sheet)
Worthwhile only if the live site has descriptive copy not already in the sheet. Re-scrape quarterly.

### 4.3 LIVE TOOL CALLS (always fresh, never in prompt or KB)

Anything that changes (prices, slots, staffing, booking status) must come from the n8n webhook — never hardcoded:

| Need | Tool |
|---|---|
| "What services do you offer?" / "How much is X?" / "What add-ons?" | `get-services` |
| "Who's available?" / "Can I book with [name]?" | `get-staff` |
| "Do you have anything Saturday afternoon?" | `get-slots` |
| New booking | `book-appointment` |
| "Can you cancel my appointment?" | `get-booking` → `cancel-booking` |
| "Can I move my appointment to Friday?" | `get-booking` → `get-slots` → `reschedule-booking` |
| "Did my booking go through?" / "When's my appointment?" | `get-booking` |

> The n8n side already enforces required-arg validation (see section 5). We let it return validation errors; the agent reads them and asks the caller for the missing piece.

---

## 5. Tools the agent will call (n8n webhook contract)

All seven tools post to the **same** n8n webhook — `POST /webhook/retell-wix` — and are routed by the `tool` HTTP header. Body is the standard Retell tool-call payload (`{ args, call }`).

| Tool name (header) | Required args | Optional args | Returns on success |
|---|---|---|---|
| `get-services` | — | — | `{ success, count, services: [{id, name, description, type, durationMinutes, defaultCapacity, onlineBookingEnabled, price, currency, paymentOptions, availableAddOns}] }` |
| `get-staff` | — | — | `{ success, count, staff: [{id, resourceId, name, email}] }` |
| `get-slots` | `serviceId`, `startDate`, `endDate` (ISO-local; date-only is auto-padded) | — | `{ success, availabilityByDay: { "YYYY-MM-DD": { morning[], afternoon[], evening[] } } }` — each slot carries `staffId` + `scheduleId` for booking |
| `book-appointment` | `serviceId`, `staffId`, `scheduleId`, `startDate`, `endDate`, `firstName`, `lastName`, `email`, `phone` | `addOnIds[]` | `{ success, confirmed, bookingId, status, startDate, endDate, contact, message }` |
| `cancel-booking` | `bookingId` | — | `{ success, message, bookingId, status }` |
| `reschedule-booking` | `bookingId`, `revision`, `serviceId`, `scheduleId`, `staffId`, `startDate`, `endDate` | — | `{ success, message, bookingId, newStartDate, newEndDate, status }` |
| `get-booking` | one of: `bookingId` *or* `phone` (auto-falls-back to caller ID `from_number`) | — | `{ success, count, bookings: [{bookingId, status, revision, serviceId, scheduleId, staffId, startDate, endDate, firstName, lastName, phone, email}] }` |

**Critical chaining rules to bake into the prompt:**
- Booking requires running `get-services` (to resolve serviceId) and `get-slots` (which gives `staffId` + `scheduleId`) **before** `book-appointment`. Do not invent these IDs.
- Reschedule requires `get-booking` first (to capture the **revision number** — Wix rejects reschedule without it) and then `get-slots` for the new time.
- Time zone is **America/Los_Angeles**; the n8n side already converts and filters slots to 10 AM – 8 PM local. The agent should speak local times only.

### 5.1 Tool we still need to add (NOT in current n8n workflow)

`flag-callback` — when AI cannot answer or caller wants a human:

- Args: `callerName`, `callerPhone`, `reason`, `transcriptSnippet`
- Behaviour: send email to `sagewillowspa@gmail.com` + SMS to `+1 628-682-8010` summarizing the unanswered question
- Implementation note: add as a new branch in the existing n8n workflow (or as a separate webhook). Simplest path: extend the same `Route by Tool` switch with a new `flag-callback` route → Gmail node + Twilio SMS node.

---

## 6. Compliance & safety

| Item | Plan |
|---|---|
| HIPAA | Sheet marks "applicable." Practical posture: do not require, store, or repeat back protected health info. Ask about injuries/conditions only as part of the booking intake; transmit them to Wix only if the booking note field accepts it; do not echo back. |
| CA two-party recording consent | Required. Announce at start of every call. (The onboarding sheet's filled value was a copy-paste error; we authored our own short line — see below.) |
| Approved consent line | *"Just to let you know, this call is recorded for quality. How can I help you today?"* Plays once, right after the greeting. |
| Emergency | "If this is a medical emergency, please hang up and call 911 immediately." End the call. Do not engage. |
| Crisis / distressed caller | *"If you're in crisis or having thoughts of harming yourself, please contact the 988 Suicide and Crisis Lifeline by dialing 988. They're available 24/7."* Then end the call gently. |
| Data retention | Transcripts + recordings live in AIEmply dashboard per standard plan. |

---

## 7. Decisions & defaults (no remaining client blockers)

### Resolved per client email thread (2026-04-24 → 2026-04-25)

- ✅ **Voice selection** — Iniga-Yang Adult Female confirmed.
- ✅ **No-show policy** — *no fee.* Aria simply communicates the 24-hr cancellation policy when booking. Nicky personally follows up with no-shows after the fact.
- ✅ **Q23 — "Can I request a specific therapist?"** Answer: *"Yes, you can request a preference. We'll do our best to accommodate based on availability."*
- ✅ **Q28 — "How early should I arrive?"** Answer: *"We recommend arriving 5–10 minutes early so you have time to settle in."*
- ✅ **Q29 — "Can I get a receipt?"** Answer: *"Yes, we can email or print a receipt after your session."*
- ✅ **Q30 — "Can I book my next appointment after my session?"** Answer: *"Absolutely — your therapist can help you schedule your next visit before you leave."*

> Client guidance on FAQ wording: *"Some of the questions and answers I added are because I used to receive calls and customers asked, so I recorded whatever I remembered, just in case, so that AI will have knowledge to answer."* → We have authority to refine wording for these FAQs as long as the substance is preserved.

### Resolved per internal direction (build-team owns these — no need to ping client)

- ✅ **Recording-consent line** — short, natural, satisfies CA Penal Code §632 notification:
  > *"Just to let you know, this call is recorded for quality. How can I help you today?"*
  Plays once at the start, immediately after the greeting. If the caller objects, end the call politely.
- ✅ **Wix API credentials** — build team uses our own automation/sandbox credentials during the build & test phase. Swap to client's Wix credentials at go-live; no client action needed pre-approval.
- ✅ **Email-required handling for `book-appointment`** — when caller does not provide an email, fall back to **`sagewillowspa@gmail.com`** (Nicky's business email). Wix accepts the booking, the confirmation lands in her inbox, and she has the caller's phone number to follow up. No fake placeholder addresses.
- ✅ **Topics to avoid / scope** — Aria is a *Sage & Willow Spa receptionist*, full stop. If the caller asks anything off-topic (general chitchat, unrelated product questions, advice outside spa services), gently redirect: *"I'm here to help with bookings and questions about Sage & Willow Spa — is there anything spa-related I can help you with?"* Don't engage with politics, news, opinions, jokes, or other off-brand topics.
- ✅ **Do-not-book rules** — defer to whatever the Wix calendar already enforces (same-day cutoffs, therapist availability, capacity). The agent reads `get-slots`; if a slot isn't returned as bookable, it isn't offered. No additional rules layered on top.
- ✅ **Crisis / distressed caller protocol** — default: *"If you're in crisis or having thoughts of harming yourself, please contact the 988 Suicide and Crisis Lifeline by dialing 988. They're available 24/7."* Then end the call gently. Do not engage further.
- ✅ **Packages / memberships** — fetched live from `get-services` and add-ons (`get-services` returns each service's `availableAddOns`). Whatever Wix has is what Aria offers. FAQ Q16 ("contact us") becomes a fallback only if the caller asks for something not in the catalog.
- ⏭ **AT&T conditional call forwarding** — post-approval step. Configured at carrier-side once Nicky signs off on the Retell agent.

---

## 8. Build sequence (proposed)

1. **Block launch items resolved with client** (§7).
2. **Set up Retell agent shell** — voice selection (female, soft/warm — Nicky already approved a sample on the call), greeting, language (`multi`), recording-consent disclosure, post-call analysis fields.
3. **Add 7 Retell custom tools** mapped to the n8n webhook routes per §5.
4. **Add `flag-callback` tool** + n8n route (§5.1).
5. **Author system prompt** — boundaries from §3, §4.1, §6.
6. **Build KB documents** (§4.2) and attach to the agent.
7. **Internal test pass** — golden paths: book / cancel / reschedule / FAQ / spam / inappropriate / Spanish caller / unanswered question.
8. **Hand off to client (Nicky) for testing** — per discovery call: "after the training period we will hand it to you for testing."
9. **Iterate on weekly audit feedback** — promised in the call.
10. **Provision Retell phone number, configure AT&T conditional-forward**, go live.

---

## 9. Files in this folder

| File | Purpose |
|---|---|
| `client-discovery-call-transcript.md` | Source — Nicky's discovery call, captures intent + tone preferences |
| `AIEmply_Sage & Willow Spa_Onboarding_Sheet.xlsx` | Source — structured onboarding answers |
| `Retell AI ↔ Wix Bookings _ Production v2.json` | Source — n8n workflow, exposes 7 tool routes |
| `sage_willow_inbound_agent.json` | (empty) Will hold the Retell agent export once built |
| `Sage_Willow_Deliverables.md` | This document |
| `kb/business_facts.md` | KB doc 1 — location, hours, payment, gift cards, gratuity, languages, etc. |
| `kb/faqs.md` | KB doc 2 — 28 Q&A pairs (with the 4 client-resolved answers baked in) |
| `kb/service_descriptions.md` | KB doc 3 — prose descriptions of 7 services + 4 add-ons (no prices — those come from `get_services`) |
| `system_prompt.md` | The agent's system prompt (mirror of what's embedded in the agent JSON) |
| `flow_map_and_tests.md` | Flow diagram + 24 test scenarios + pre-launch action items |
| `sage_willow_inbound_agent.json` | Importable Retell agent — 27 nodes, 8 tools, 15 post-call fields |
| `_build_agent.py` / `_modify_n8n_workflow.py` | Idempotent build scripts (re-runnable to regenerate the agent JSON or update the n8n workflow) |
