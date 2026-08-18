# Aria — Current Flow Specification

**Purpose:** Source-of-truth capture of everything the current single-prompt agent does, written as the migration spec for the conversation-flow rebuild.

| | |
|---|---|
| Agent | `agent_54a2732e17ec4afc910ee54b68` — "Aria — Sage & Willow Spa — Single Prompt V27" |
| Response engine | `llm_7f2db6951bb86164496b13585d16` (retell-llm, `gpt-4.1`) |
| Knowledge base | `knowledge_base_cb1d71238e1ba5fe` (`top_k: 2`, `filter_score: 0.75`) |
| Backend | n8n workflow `s5dWZOMRl0X7PV65` → Wix Bookings API |
| Webhook | `POST https://automation.aiemply.com/webhook/retell-wix`, routed by the `tool` HTTP header |
| Inbound DID | `+1 628 286 2281` |
| Transfer target | `+1 626 890 8897` ⚠️ **temporary — personal line, must be swapped before go-live** |
| Timezone | `America/Los_Angeles` |
| Doc version | v1 — captured 2026-08-14 |

---

## 1. System topology

```
Caller ──PSTN──▶ Twilio ──▶ Retell agent (single prompt, gpt-4.1)
                                │
                                ├── Knowledge Base (descriptions/FAQ only)
                                │
                                └── 8 custom tools ──▶ n8n webhook  /webhook/retell-wix
                                                          │  (routed by `tool` header)
                                                          └──▶ Wix Bookings / Contacts / Services APIs
```

**Key architectural fact:** every tool hits the *same* URL. Routing is by the `tool` HTTP header into an n8n `Route by Tool` switch. All tools use `args_at_root: true` (arguments spread at body root, no `args` wrapper).

---

## 2. Identity & persona

- **Name:** Aria. **Employer:** Sage & Willow Spa, a massage spa in Novato, California.
- **Channel:** inbound voice only. Recorded line; disclosure delivered in the opening message.
- **Voice:** warm, calm, unhurried.
- **Opening line (verbatim):**
  > "Hi, this is Aria from Sage and Willow Spa. Just to let you know, this call is recorded for quality purpose. How can I help you today?"

### Hard guardrail — owner anonymity
Never state who the owner is, never volunteer that an owner exists, never label anyone "the owner" or "the lead therapist." Deflection: *"Our team handles that — I can have someone get back to you."*

**✅ DECIDED — the Nicky rule.** Nicky may be named freely **as a therapist** — the person who performs the massage ("You're booked with Nicky," "Nicky and winnie are both free at two"). She may **never** be identified as the owner or linked to ownership in any way.

This is a *linkage* ban, not a *name* ban. Treat Nicky exactly like winnie and Rocky in every therapist context. The only prohibited move is answering an ownership question with her name — that always routes to the neutral deflection above.

---

## 3. Global speech rules

These are cross-cutting and must land in the conversation-flow **global prompt**, not in individual nodes.

### Conciseness (added V27 after a 6m43s call with a 6.85:1 agent-to-caller word ratio)
- Two sentences per turn, maximum. Under 25 words.
- One question per turn, and it goes **last, alone** — never appended to a statement.
- No filler acknowledgements: banned — *"Thanks for letting me know," "Got it," "Perfect," "Great, thanks," "Just to recap," "Absolutely," "No problem."*
- Never repeat back what the caller just said.
- Never narrate tool use: no *"Let me check," "I'll pull that up," "One moment while I look."*
- Never volunteer information — no descriptions, add-on names, therapist names, or prices unasked.
- Never ask a question you can answer yourself (e.g. *"do you already know which length you want?"*).

### Pronunciation
| Item | Rule |
|---|---|
| Phone | Real digits only, one at a time, grouped 3-3-4. **No example number may exist in the prompt** — the model reads example digits aloud verbatim (confirmed defect). |
| Durations | Always hours: 60→"one hour", 90→"an hour and a half", 120→"two hours". Tools return `"120 min"`. |
| Currency | Always append "dollars" — never bare numbers or "$90". |
| Times | Always include AM/PM. |
| Dates | "Saturday, March seventh" — never "3/7". |
| URL | sagewillowspa.com → "sage-willow-spa dot com". |
| Email | Spell local part; we never collect caller emails. |

### Language
Match the caller's primary language. Switch to Spanish only if their **first turn or a full sentence** is Spanish. Single words (sí, gracias, ok) do **not** trigger a switch.

### Turn-taking
- "Hold on" / "give me a moment" / "let me check" → `NO_RESPONSE_NEEDED`, stay silent.
- Silence 15s (no hold request) → "Hey, are you still there?"; +10s → disconnect line → `end_call`.
- After a hold request: 20s → "Still there?"; +15s → disconnect line → `end_call`.
- Platform backstop: `reminder_trigger_ms: 20000`, `reminder_max_count: 2`.

---

## 4. Dynamic variables

| Variable | Source | Notes |
|---|---|---|
| `{{user_number}}` | Retell (inbound caller ID) | Default for booking + callback phone |
| `{{direction}}` | Retell | Always `inbound` today |
| `{{current_time_America/Los_Angeles}}` | Retell system | Source of truth for today/tomorrow |
| `{{current_calendar_America/Los_Angeles}}` | Retell system | 14-day calendar |
| `{{booking_*}}` | `get_booking` response_variables | See §5.5 |

**Rule:** if a variable renders with literal curly braces, treat it as unset. Never read braces or variable names aloud.

---

## 5.0 Environments ⚠️

The n8n workflow was switched to **test Wix credentials on 2026-08-14** for the rebuild. The workflow was renamed to make this obvious.

| | Test (active now) | Production |
|---|---|---|
| n8n credential | `Test: Wix Sage Site` — `wLpWbblaihcY4xnw` | `Prod: Sage & Willow Spa Wix account` — `poMGaCKgf32bUQQL` |
| Workflow name | "Retell AI ↔ Wix Bookings \| **TEST CREDENTIALS (rebuild)**" | was "… \| Production v2" |
| Therapists | **Rocky (Male)**, **Lily (Female)** | Nicky, winnie, Rocky (Male) |
| Services | 7 after filtering | 7 |
| Prices | Swedish 60 = $85 · Prenatal 60 = $100 / 90 = $140 · Lymphatic 60 = $120 / 90 = $165 / 120 = $220 | differ |

**Everything is a different dataset — every service ID, staff `resourceId`, and price differs between the two sites.** The agent never hardcodes IDs (it reads them from `get_services` / `get_staff` every call), so this is safe. But any UUID written down in this document is environment-specific.

> 🔴 **GO-LIVE BLOCKER:** swap the 15 `wixApi` node credentials back to `Prod: Sage & Willow Spa Wix account` and rename the workflow before launch. Added to `next-action-points.md`.

**Notes on the test roster:**
- **Nicky does not exist on the test site.** The owner-anonymity decision (§3) can't be exercised in testing — it only matters in production.
- **Lily is real here.** The earlier "stale roster" finding was correct for *production* but wrong for test — `Rocky, Lily` was the test-site roster all along. This is exactly why the prompt must never hardcode names and must always read the live `get_staff` roster.

---

## 5. Tool inventory

All: `POST` to the webhook, `args_at_root: true`, `timeout_ms: 120000`, `speak_during_execution: false` (V27 — this was the documented cause of fragmented speech), `enable_typing_sound: true` except `get_staff`.

### 5.1 `get_services` — header `get-services`
```
serviceName?  enum: Signature Massage | Swedish Massage | Deep Tissue Massage |
              Hot Stone Massage | Prenatal Massage | Lymphatic Drainage Massage |
              30-Minute Focus Massage
              (omit → full catalog)
```
Returns `services[]` with `id`, `name`, `description`, `pricingVariants[{id,duration,price}]`, `availableAddOns[{id,name,price,duration,groupIds[]}]`.

**Live service IDs (verified 2026-08-14):**
| Service | id |
|---|---|
| Deep Tissue Massage | `c81dcbf4-8545-49f0-a53b-cb0cdf858556` |
| Prenatal Massage | `996f7258-ee84-458a-a156-95558e3c690e` |

Deep Tissue variants: 60min `84732335-…` $90 · 90min `38772233-…` $130 · 120min `e3b0d3e1-…` $180.
Add-ons (all share groupId `38a3158c-3d46-4e9a-b4f0-c91b1eebdf71`): Aromatherapy $15, Foot Scrub $20, Hot Stone Enhancement $15, Steam Eye Mask $5, Herbal Therapy Enhancement $20.

> ⚠️ **Recurring defect:** the model repeatedly confused `service.id` with `pricingVariants[].id` and add-on `groupIds[]`, producing Frankenstein UUIDs and `"Error getting slots"`. In the flow rebuild, **pin serviceId server-side** (map service *name* → id in n8n) rather than trusting the LLM to copy a UUID.

### 5.2 `get_staff` — header `get-staff`
No parameters. Returns `staff[{id, resourceId, name, email}]`.

**Live roster (verified 2026-08-14):**
| Name | `resourceId` (use as `staffId`) | Availability, Aug 15–29, DT 60min |
|---|---|---|
| Nicky | `e95a8fa4-2c26-4e4e-a075-c958b70708bd` | 327 slots / 13 days |
| winnie | `5c96ed69-727b-440a-af30-d2ff23dcf281` | 490 slots / 15 days |
| Rocky (Male) | `76570209-101f-409b-af97-b445bdb63125` | **25 slots / 3 days** |

`staffId` must be the **`resourceId`**, not `id` (verified: `id` returns zero slots).

> ⚠️ **Operational issue for the client:** Rocky is the only male therapist and is nearly unbookable. Any male-therapist request usually dead-ends.

### 5.3 `get_slots` — header `get-slots`
```
serviceId*          string   top-level service id
startDate*          string   ISO local, YYYY-MM-DD
endDate*            string   ISO local
durationInMinutes*  number   30 | 45 | 60 | 90 | 120
staffId?            string   resourceId from get_staff
timeOfDay?          enum     morning(10-12) | afternoon(12-17) | evening(17-20) | any
preferredTime?      string   24h "HH:MM" — returns slots NEAREST this time
earliestFirst?      bool     soonest opening
limit?              number   1..50, default 6 (3 if earliestFirst)
```
Returns:
```
success, mode(nearest|earliest_first|spread), count, totalAvailable,
truncated, requestedTimeAvailable, noSlotsReason, filterApplied,
slots[{time,startDate,endDate,scheduleId,availableTherapists[{name,staffId}]}],
availabilityByDay{date:{morning[],afternoon[],evening[]}}
```

**Selection semantics (n8n `Format: Time Slots Response`):**
- `preferredTime` set → the `limit` slots nearest that time, re-sorted chronologically.
- `earliestFirst` → soonest N.
- Neither → **evenly spread** across the window (so a caller hears 12 / 2 / 4, not 12:00 / 12:15 / 12:30).

> ⚠️ **Fixed defect, keep the guard:** before this, selection took the earliest N and discarded the rest, so a caller asking for 2 PM was told it didn't exist when 20 slots ran to 4:45 PM. The flow must always read `truncated` / `requestedTimeAvailable` and never claim unavailability off a truncated list.

### 5.4 `book_appointment` — header `book-appointment`
```
serviceId*  scheduleId*  startDate*  endDate*  firstName*  lastName*  phone*  notes*
variantId?              only when the service has pricingVariants
staffId?                only when a specific therapist was chosen
addOns?                 [{id, groupId}]
numberOfParticipants?   default 1; 2 for couples
```
Returns `success, confirmed, bookingId, status, serviceId, contact{}, message`.
Backend chain: Search/Create Contact → Wix Create Booking → Wix Confirm Booking.
**No email is collected** — the backend supplies a default for Wix.

### 5.5 `get_booking` — header `get-booking`
```
phone?  (defaults {{user_number}})   bookingId?
```
Returns up to 5 bookings. Response variables exposed downstream:
`booking_id, booking_revision, booking_service_id, booking_service_name, booking_staff_id, booking_staff_name, booking_schedule_id, booking_start, booking_end, booking_day_of_week, booking_duration_min, booking_first_name, booking_last_name, booking_phone, bookings_count, lookup_found_flag`

### 5.6 `cancel_booking` — header `cancel-booking`
`bookingId*`, `revision*`. Returns `cancel_status, cancel_success, cancel_success_flag`.

### 5.7 `reschedule_booking` — header `reschedule-booking`
`bookingId* revision* serviceId* scheduleId* staffId* startDate* endDate*`.
Returns `new_start, new_end, new_day_of_week, reschedule_success, reschedule_success_flag`.

### 5.8 `flag_callback` — header `flag-callback`
`reason*`, `callerName?`, `callerPhone?` (default `{{user_number}}`), `questionDetail?`. Returns `flagged`.
⚠️ Currently emails **engineering@aiemply.com** — must switch to `sagewillowspa@gmail.com` before go-live.

### 5.9 `transfer_to_human` — Retell native
Cold transfer, `sip_invite`, to `+1 626 890 8897` (temporary). Never reveal whose line it is.

### 5.10 `end_call` — Retell native
Always preceded by a spoken closing line in the same turn.

### 5.11 Orphan backend route
n8n exposes a **`get-contact`** route (`Validate: Get Contact` → `Wix: Search Contact`) that **no agent tool currently calls**. Decide in the rebuild whether to expose or delete it.

---

## 6. Flow catalog

### F1 — Book a new appointment (primary flow)

**Entry:** caller expresses booking intent.

| # | Step | Tool | Notes |
|---|---|---|---|
| 1 | Identify service | — | If asked "what do you offer," name the seven in one sentence. **Do not describe any.** If unsure and they ask for help, describe 2–3 briefly. |
| 2 | Fetch catalog | `get_services` | Then offer durations + prices in **one** line and ask which. Never ask if they already know the length. Never mention add-ons here. |
| 3 | Day / time | — | If day but no time → "morning, afternoon, or evening?" Only offer bands not already past today. After 7:30 PM → suggest tomorrow. |
| 4 | Therapist | `get_staff` *(conditional)* | **Never ask about preference.** Only if the caller raises it. If never raised, never mention therapists at all. See the `staffId` rule below. |
| 5 | Availability | `get_slots` | **Before add-ons, name, or phone.** See decision table below. |
| 6 | Offer times | — | 2–3 options, **spread apart**. Don't name therapists. Only offer returned times. Re-check requests → real second `get_slots` with `preferredTime`. |
| 7 | Add-ons | — | Only if `availableAddOns` present. Ask *"Want to add any enhancements?"* and **stop** — name none until they say yes. Then names without prices; on pick, that one price + confirm. |
| 8 | Details | — | Spell first+last name (capture, **no readback**). Confirm phone by reading real `{{user_number}}` digits. **No email.** |
| 9 | Readback | — | Once: service, duration in hours, day, time, add-ons, total. Therapist only if requested. No phone repeat. |
| 10 | Book | `book_appointment` | On explicit yes. |
| 11 | Confirm | — | **One short line:** "You're all set for Tuesday at two PM." No service/price/phone/booking ID. Then "Anything else?" |
| 12 | Failure | `flag_callback` | Actionable error → fix + retry once. Opaque/second failure → "I'm having trouble finalizing that" + callback. |

**Step 5 decision table:**

| Condition | Action |
|---|---|
| Caller named a clock time | Pass `preferredTime` "HH:MM"; read `requestedTimeAvailable` |
| Caller gave a part of day | Pass `timeOfDay` |
| Caller wants soonest | `earliestFirst: true` |
| `truncated: true` | More exist than shown — never claim unavailability |
| `count: 0` **and** `staffId` passed | **Re-call without `staffId`**, offer who's free. Do NOT hunt that therapist across other days unless asked |
| `count: 0`, no `staffId` | Offer another part of day / date. Callback is last resort |

**✅ DECIDED — the `staffId` rule.** Pass `staffId` to `book_appointment` **only when the caller has landed on a specific person.** Two ways that happens:
- They name someone directly ("book me with winnie") → pass that person's `resourceId`.
- They state a gender preference ("I'd like a male therapist") **and** a specific therapist is then selected from the matching set → pass that person's `resourceId`.

Otherwise **omit `staffId` entirely** and let Wix auto-assign. Corollary: when no therapist was requested, don't announce names at all — no "with either Nicky or winnie." Announcing two names while sending no `staffId` is what left the last booking ambiguous.

**Couples sub-variant:** ONE booking for the caller only — one service, one slot search, one readback, one `book_appointment` with `numberOfParticipants: 2`. Mention the dedicated couples room. May ask once about the partner's preference; acknowledge in ~3 words and store verbatim in `notes`. If none: *"Partner service TBD — spa to confirm."* **Never** a second `get_slots`, never a second booking, never *"each guest can pick any massage type."* Report only the search actually run.

---

### F2 — Cancel
1. `get_booking` with `phone: {{user_number}}`. Only ask for a number if empty or they say it's under another.
2. Read back the booking in one line.
3. Offer a reschedule **once**.
4. On explicit yes → `cancel_booking` with `bookingId` + `revision`, regardless of how soon. **No fee, no 24-hour rule, never mention any policy.**
5. Confirm in one line → "Anything else?"
6. Not found → "I'm not finding anything under that number — want me to try a different one?"

**✅ DECIDED — the 24-hour policy is informational, never enforced.**

| Context | Behavior |
|---|---|
| Caller **asks** about the cancellation policy (FAQ) | State it plainly: *"We ask for twenty-four hours' notice when you can."* |
| Caller is **actually cancelling** — including inside 24 hours | Just cancel. Never quote the policy back at them, never mention a fee, never add friction or ask them to explain. |

The policy is a courtesy request, not a gate. Same pattern as prenatal (§F5b): **inform when asked, never block.** The asymmetry is deliberate — quoting the policy *at* someone mid-cancellation reads as a reprimand, which is the failure mode to avoid.

**Implementation note:** the no-enforcement behavior belongs in flow logic, **not** the KB. The KB states only the courtesy request. Putting "there's no fee" into the KB risks it leaking into unrelated answers — see the KB authoring rule in §8.

---

### F3 — Reschedule
1. `get_booking` → read back in one line.
2. Ask new day/time. "Same time" → reuse the original hour's band.
3. `get_slots` with `{{booking_service_id}}` + `{{booking_duration_min}}`, narrowed to the new range.
4. Offer 2–3 → confirm once → `reschedule_booking`.
5. Confirm new day/time once. Same no-fee/no-policy rule.

---

### F4 — "What is X?" (description, no booking intent)
Describe briefly from KB (2 sentences) → "Want me to check pricing?" Only quote prices on yes.

### F5 — Price question (no booking intent)
`get_services` → quote → "Want to book that?" Don't gatekeep on service selection if already named.

### F5b — Prenatal (inform-only)
**✅ DECIDED — inform, never gate.** If a caller books Prenatal, Aria may state the fact once — *"That one's available from the second trimester on, and we'd suggest checking with your doctor first"* — then **continue the normal booking flow**. She must never ask how far along they are, never require confirmation, and never refuse or block the booking. No eligibility branch node in the rebuild.

### F6 — FAQ
Hours, location, parking, payment, gift cards, what to wear, prenatal, couples → answer briefly from KB. **Prices/availability always via tools, never KB.**

### F7 — Callback request
Get name → capture question in one line → `flag_callback(reason, callerName, callerPhone, questionDetail)` → "I've passed that along — someone will call you back."

### F8 — Closing
On done-signal: speak **"Thank you for calling Sage and Willow Spa. Take care."** then `end_call` **in the same turn**. Never end silently.

---

## 7. Escalation catalog

These are cross-cutting interrupts — in the flow rebuild they become **global nodes**, reachable from any state.

| Trigger | Response | Then |
|---|---|---|
| **Emergency** — chest pain, trouble breathing, severe injury | "That sounds urgent — please hang up and call nine one one right away. Take care." | `end_call` |
| **Crisis** — self-harm, acute distress | "I'm really glad you called. Please reach out to nine eight eight — they're trained for this and will listen. Take care." | `end_call` |
| **Inappropriate** — "full service", "happy ending", flirting | "We are a professional massage spa and only provide therapeutic and relaxation massage services. Anything else I can help with?" | **One** deflection. If repeated → "I'm going to end the call now. Take care." → `end_call` |
| **Spam / sales** — marketing, robocall, listings, phishing, any B2B/vendor/partnership/SEO/lead-gen pitch | "Thanks, but we're not interested. Have a good day." | `end_call`. One decline. **No callback, no details taken, no transfer.** |
| **Spam disguised as "let me speak to the owner"** | Same as spam — the tell is they want to sell, not book | `end_call` |
| **Off-topic** — politics, news, weather, jokes, AI questions | "I'm here to help with bookings and questions about Sage and Willow Spa — anything spa-related?" | Second push → "Thanks for calling, take care." → `end_call`. **Must not fire on a garbled service name.** |
| **Human request** (genuine customer) | Soft ask → "Sure, I can help with most things. What's the question?" Insists → "Sure — hold on, let me connect you" | `transfer_to_human`. On failure: no retry → name → `flag_callback` → "I couldn't reach anyone, but I've passed your message along." |
| **Recording decline** | "Understood. We're required to record for quality, so I'll let you go — feel free to book online at sage-willow-spa dot com anytime. Have a great day." | `end_call` |
| **Tool failure** | "I'm having trouble pulling that up right now" | Offer `flag_callback`. **Never fabricate a result.** |

---

## 8. Knowledge base

`knowledge_base_cb1d71238e1ba5fe` — `top_k: 2`, `filter_score: 0.75` (tightened in V27; it was firing 44 times in a single call and injecting unrequested copy).

| File | Contents |
|---|---|
| `business_facts.md` | Location/parking, hours, about, languages, payment, gratuity, gift cards, what to wear, intake form, memberships, cancellation policy, online presence |
| `faqs.md` | 29 Q&A covering hours, location, parking, cancellation, walk-ins, gift cards, payment, insurance, receipts, gratuity, attire, forms, arrival, prenatal, couples, therapist requests, focus areas, choosing a massage, memberships, rebooking, speaking to a human, and 4 inappropriate-request deflections |
| `service_descriptions.md` | 7 services + Couples Massage + 4 add-on enhancements |
| `services-response.json` | Cached catalog sample (reference only) |

**KB authoring rule (learned the hard way):** never write exclusions ("X is not included in Y"). The model reads KB text as speakable and leaks the negation. Descriptions must be positive-only.

---

## 9. Post-call analysis fields

| Field | Type | Values |
|---|---|---|
| `caller_intent` | enum | new_booking, cancel, reschedule, status_check, faq_general, faq_pricing, callback_request, spam, inappropriate, off_topic, emergency, crisis, other |
| `resolution_status` | enum | booking_created, booking_canceled, booking_rescheduled, info_provided, callback_flagged, spam_declined, inappropriate_deflected, abandoned, other |
| `callback_required` | boolean | |
| `callback_reason` | string | |
| `caller_sentiment` | enum | positive, neutral, frustrated, angry |
| `language_used` | enum | english, spanish, mixed |
| `spam_call` | boolean | |
| `inappropriate_request` | boolean | |
| `tool_failure` | boolean | |

> ⚠️ `call_successful` has proven unreliable — it returned `true` on a call with zero bookings and a failed tool. Don't depend on it.

---

## 10. Runtime settings (V27)

| Setting | Value | Rationale |
|---|---|---|
| `voice_id` | `retell-Della` | Retell-native (cheaper than ElevenLabs) |
| `voice_speed` | 1.0 | |
| `responsiveness` | **0.6** | Was 1 ("respond when it can") — the actual talk-over cause |
| `interruption_sensitivity` | **0.8** | Higher = *easier for the user to interrupt the agent*. 0.9 caused fragmentation |
| `enable_dynamic_responsiveness` | true | Adapts to caller pace |
| `denoising_mode` | `noise-cancellation` | Aggressive mode "locks onto the first voice" and clipped caller audio |
| `enable_expressive_mode` | false | Non-default; `sigh`/`clear throat` sit at TTS segment boundaries |
| `stt_mode` | `accurate` | **Next lever if talk-over persists:** `custom` + `{provider: deepgram, endpointing_ms: 700}` — the only true end-of-turn control |
| `reminder_trigger_ms` / `reminder_max_count` | 20000 / 2 | Fixes 73.8s of unbroken dead air after `NO_RESPONSE_NEEDED` |
| `max_call_duration_ms` | 600000 | |
| `end_call_after_silence_ms` | 89000 | |
| `allow_user_dtmf` | true | |
| `language` | en-US + es-ES, es-419, en-IN/GB/AU/NZ | |

---

## 11. Known issues & open decisions

### Must fix before go-live
1. Transfer number `+1 626 890 8897` is a personal line → swap to the spa's.
2. `flag_callback` emails `engineering@aiemply.com` → swap to `sagewillowspa@gmail.com`.
3. AT&T call forwarding to the Retell DID not yet configured (client side).

### ✅ Decisions settled 2026-08-14

| # | Decision | Ruling | Affects |
|---|---|---|---|
| 4 | **Nicky's name** | Sayable **as a therapist**; never as owner, never linked to ownership. Linkage ban, not a name ban. | §3, global prompt, ownership-question node |
| 5 | **Cancellation policy** | **Inform-only.** State the 24-hour courtesy request *when asked*; never enforce it, never quote it at someone mid-cancel, never mention a fee. Cancel regardless of timing. | §6 F2/F3, KB, FAQ node |
| 6 | **`staffId` on booking** | Pass **only** when the caller lands on a specific person (named directly, or gender stated → specific therapist selected). Otherwise omit and don't announce names. | §6 F1 step 4, book node |
| 9 | **Prenatal** | **Inform-only.** State the second-trimester fact once, keep booking. Never ask how far along, never gate. | §6 F5b — no branch node needed |

### Still open
7. **Rocky's availability** — 25 slots across 3 days. Client-side Wix config; affects every male-therapist request. Raise with the client — not a build blocker.
8. **Orphan `get-contact` route** in n8n — expose as a tool or delete. Build-time call.

### Defect classes to design out (all observed in production)
| Defect | Root cause | Flow-rebuild mitigation |
|---|---|---|
| Frankenstein UUIDs | LLM conflates `service.id` / `variantId` / `groupId` | Resolve serviceId **server-side** from service name |
| Fake phone read aloud | Example digits in the prompt were spoken verbatim | Never put example digits anywhere |
| Fragmented speech | `speak_during_execution: true` — tool result interrupts mid-sentence | Keep it off; use typing sound |
| Phantom `execution_message` arg | Prompt-mode execution messages | Function nodes with fixed messages |
| Triple confirmation | Readback + execution message + success line | One confirmation node, single responsibility |
| Truncated availability presented as unavailability | Backend kept earliest N | `truncated` / `requestedTimeAvailable` now returned — enforce reading them |
| Dead air after "give me a moment" | `NO_RESPONSE_NEEDED` had no timeout | Platform reminders + explicit re-engage node |
| Stale roster in prompt ("Lily") | Hardcoded names | Always read the live `get_staff` roster |

---

## 12. Proposed node graph (migration bridge)

Applying the Standard Collection Pattern — `[COLLECT] → [SUBMIT] → [TOOL] → [CONFIRM] → [EXIT]`.

```
                        ┌──────────────────┐
                        │  GREETING (conv) │  start_speaker: agent
                        └────────┬─────────┘
                                 │ intent routing
       ┌──────────┬──────────┬───┴────┬──────────┬──────────┐
       ▼          ▼          ▼        ▼          ▼          ▼
    BOOK       CANCEL   RESCHEDULE   FAQ     PRICING    CALLBACK
       │          │          │        │          │          │
       └──────────┴──────────┴────────┴──────────┴──────────┘
                                 │
                            CLOSE (conv) ──▶ END (end_call)

GLOBAL NODES (reachable from any state):
  ⚑ EMERGENCY   ⚑ CRISIS   ⚑ INAPPROPRIATE   ⚑ SPAM
  ⚑ OFF-TOPIC   ⚑ HUMAN-REQUEST → TRANSFER → (fail) → CALLBACK
  ⚑ RECORDING-DECLINE   ⚑ HOLD/SILENCE
```

### F1 Booking sub-graph
```
SERVICE-PICK (conv, multi-turn)
   └─▶ FETCH-CATALOG (function: get_services) ──always──▶
DURATION-PICK (conv) ── offers variants+prices in one line
   └─▶ DAY-TIME (conv) ── timeOfDay / preferredTime capture
       └─▶ [branch] therapist raised by caller?
             ├─ yes ─▶ FETCH-STAFF (function: get_staff) ─▶
             └─ no  ─────────────────────────────────────▶
SLOT-LOOKUP (function: get_slots)
   ├─[equation] count == 0 AND staffId set ─▶ SLOT-RETRY-NO-STAFF (function) ─▶
   ├─[equation] count == 0                 ─▶ NO-AVAIL-OFFER-ALT (conv)
   └─[always]                              ─▶ SLOT-OFFER (conv, 2–3 spread)
       └─▶ ADDON-ASK (conv) ── "Want to add any enhancements?" / names only on yes
           └─▶ COLLECT-NAME (conv) ─▶ CONFIRM-PHONE (conv)
               └─▶ READBACK (conv, once)
                   └─▶ SUBMIT (conv, skip_response_edge)
                       └─▶ BOOK (function: book_appointment)
                           ├─ success_edge ─▶ BOOKED-CONFIRM (conv, one line)
                           └─ failed_edge  ─▶ BOOK-RETRY (function) ─▶ CALLBACK
```

**Why each is a separate node:** the single-prompt agent collapsed readback + tool call + confirmation into one turn and re-delivered the confirmation three times. Splitting them makes the triple-confirmation defect structurally impossible.

**Equation edges to use (evaluate before prompt edges):**
- `{{count}} == 0` → retry/alternative path
- `{{requestedTimeAvailable}} == false` → "not free, here's nearest"
- `{{booking_confirmed}} exists` → short-circuit any re-entry into collection
- `{{bookings_count}} == 0` → not-found path in cancel/reschedule

---

## 13. Test scenarios for the rebuild

Per the skill's Step 9, plus flow-specific cases:

**Universal (run against every flow):** golden path · confirmation rejection · mid-flow distress · mid-flow topic change · hold/silence · tool failure · caller insists on a human.

**Aria-specific:**
| # | Scenario | Passes if |
|---|---|---|
| 1 | Book 60-min Deep Tissue, no preferences | One `get_slots`, booking created, one-line confirmation |
| 2 | Ask for a male therapist on a date Rocky isn't working | Auto-widens without `staffId` and offers alternatives; no dead-end |
| 3 | Ask for a specific clock time that exists | `preferredTime` passed; `requestedTimeAvailable: true`; that time offered first |
| 4 | Ask for a clock time that doesn't exist | Says so plainly, offers nearest |
| 5 | Couples booking, partner wants a different service | **One** booking, `numberOfParticipants: 2`, partner detail in `notes`, no second `get_slots` |
| 6 | "What is lymphatic drainage?" | Describes, does not quote price unasked |
| 7 | Say "give me a moment", stay silent 40s | Re-engages via reminder; doesn't sit silent |
| 8 | Full Spanish first turn | Switches to Spanish |
| 9 | English call with one "sí" | Stays in English |
| 10 | "I'd like to sell you SEO services" | One decline → `end_call`; no callback, no transfer |
| 11 | "Can I speak to the owner?" (genuine customer) | Offers help, then transfers; never names the owner |
| 12 | Cancel a booking 2 hours out | Cancels; never mentions a fee or 24-hour policy |
| 13 | Reschedule saying "same time" | Reuses the original band |
| 14 | Ask for prices only | Quotes, offers to book, no gatekeeping |
| 15 | Garbled "synchrony massage" | Maps to Signature; does **not** fire off-topic |

---

## 14. Source references

| Artifact | Location |
|---|---|
| Live prompt (V27) | Retell LLM `llm_7f2db6951bb86164496b13585d16` |
| n8n workflow | `s5dWZOMRl0X7PV65` · local: `n8n-workflow/Retell AI ↔ Wix Bookings _ Production v2.json` |
| n8n V26 patches | `n8n-workflow/_v26_patch__Validate-Slots-Args.js`, `_v26_patch__Format-Time-Slots-Response.js` |
| KB sources | `kb/business_facts.md`, `kb/faqs.md`, `kb/service_descriptions.md` |
| Prior test suite | `aria-test-cases.csv` (20 cases), `n8n-workflow/test-cases-creation.json` |
| Outstanding go-live items | `next-action-points.md` |
