# Industry Patterns

Vertical-specific conversation flows, objection scripts, and compliance notes. Use these to tailor the **Conversation Flow**, **Objection Handling**, and **Guardrails** sections for a specific business. They're starting points — always adapt to the client's actual offer and rules.

> **Compliance disclaimer:** the compliance notes below are general orientation, not legal advice. Voice-AI calling is regulated (TCPA, recording-consent laws, HIPAA, FDCPA, state-specific rules) and the requirements depend on jurisdiction and use case. Tell the client to confirm mandatory disclosures with their own counsel, and put any required verbatim language in the prompt exactly as given.

## Table of contents
- [Real Estate](#real-estate)
- [Healthcare](#healthcare)
- [Insurance](#insurance)
- [Home Services](#home-services)
- [Financial Services](#financial-services)
- [SaaS / Tech](#saas--tech)
- [Debt Collection](#debt-collection)
- [Retail / E-Commerce](#retail--e-commerce)
- [Cross-vertical patterns](#cross-vertical-patterns)

---

## Real Estate

**Common agents:** buyer/seller lead follow-up, showing scheduling, listing inquiries.

**Flow (outbound buyer lead):** Opening (reference the property/inquiry) → Discovery (timeline, budget range, pre-approved?, areas of interest) → Core Task (book a showing or a call with the agent via `check_availability`/`book_appointment`) → Wrap-Up (confirm, offer to text details).

**Vertical objections:**
- "I already have an agent." → "Totally understand — I'm not trying to step on any toes. Want me to just send the listing details so you have them?"
- "I'm just browsing." → "No pressure at all. What kind of place are you keeping an eye out for, just so I can flag anything that fits?"
- "What's the price?" (when unlisted) → don't guess; offer to have the agent follow up or pull it from the KB if available.

**Compliance:** honor Do-Not-Call and opt-out immediately; many states require recording disclosure. Don't promise financing terms.

## Healthcare

**Common agents:** appointment scheduling, reminders/confirmations, insurance verification intake, new-patient registration.

**Flow (inbound scheduling):** Greeting → identify caller (and CRM lookup via `{{user_number}}`) → reason for visit → `check_availability` → confirm slot + provider → `book_appointment` → Wrap-Up (what to bring, arrival time).

**Vertical objections / sensitive moments:**
- Caller describes an emergency → do **not** triage; "If this is a medical emergency, please hang up and dial 911." Otherwise route to a nurse line / human.
- Caller asks for medical advice → decline and defer to the provider.

**Compliance:** HIPAA — minimize PHI spoken aloud, confirm identity before sharing any record details, follow the client's exact verification script. Enable **Scope Boundaries**; avoid **Natural Filler Words** (too casual for clinical contexts). Use **Echo Verification** for names/DOB.

## Insurance

**Common agents:** quote collection, first-notice-of-loss / claims intake, policy renewal reminders.

**Flow (quote intake):** Opening → Discovery (coverage type, basic risk details, current carrier, renewal date) → Core Task (capture details via `extract_dynamic_variables` or a custom function, or book an agent callback) → Wrap-Up.

**Vertical objections:**
- "I'm happy with my current insurer." → "Makes sense — most folks just want to know if they're overpaying. Mind if I grab a couple details to check?"
- "How much will it cost?" → don't fabricate a quote; explain a licensed agent finalizes pricing.

**Compliance:** insurance quoting/binding is licensed activity — the agent collects info and routes to a licensed human; it must not quote binding prices or give coverage advice. Recording disclosure as required.

## Home Services

**Common agents:** estimate booking, dispatch/scheduling, post-job follow-up (HVAC, plumbing, roofing, cleaning, pest, etc.).

**Flow (inbound estimate):** Greeting → service needed + urgency → address/service area check → `check_availability` for a tech window → `book_appointment` → Wrap-Up (window, what to expect). For emergencies (burst pipe, no heat), prioritize and offer the soonest slot or transfer to dispatch.

**Vertical objections:**
- "How much will it cost?" → give a ballpark only if it's in the KB; otherwise "The tech will give you an exact quote on-site, and the estimate's free."
- "Can someone come today?" → check soonest availability; be honest about windows.

**Compliance:** lightest of the verticals — mainly accurate scheduling and not over-promising arrival times or prices.

## Financial Services

**Common agents:** loan/pre-qualification, payment reminders, application follow-up.

**Flow (loan pre-qual):** Opening → Discovery (loan purpose, rough amount, employment, ballpark credit band) → Core Task (score against criteria; book a loan officer or hand off) → Wrap-Up.

**Vertical objections:**
- "Will this affect my credit?" → answer accurately only if you know (soft vs hard pull); otherwise defer to a human, don't guess.
- "What rate can I get?" → don't fabricate rates; a licensed officer finalizes.

**Compliance:** heavy — fair-lending rules, no specific financial advice, no fabricated rates/terms. Collect, don't decide. Enable **Scope Boundaries** and **Structured Output** for clean data capture. Recording disclosure as required.

## SaaS / Tech

**Common agents:** demo booking, inbound MQL qualification, onboarding/activation nudges, trial follow-up.

**Flow (outbound demo booking):** Opening (reference their signup/download) → Discovery (role, team size, the problem they're solving, current tool) → Core Task (book a demo via `check_availability`/`book_appointment`, or `agent_transfer` to an SDR) → Wrap-Up (calendar invite, send recap SMS).

**Vertical objections:**
- "Just send me pricing." → "Happy to — and a quick 15-minute demo usually saves people money since pricing depends on your setup. Want me to grab a time?"
- "We're already using [competitor]." → acknowledge, find the gap, position the demo around it.

**Compliance:** B2B and lightest-touch; still honor opt-out and DNC. Casual tone and **Natural Filler Words** are usually fine here.

## Debt Collection

**Common agents:** payment reminders, arrangement setup, right-party contact.

**Flow:** Opening → **right-party verification** (confirm you're speaking to the correct person *before* discussing any debt) → mini-Miranda disclosure → reason for call → Core Task (arrangement / payment via secure handoff) → Wrap-Up.

**Compliance (heaviest — FDCPA and state law):**
- **Mini-Miranda**, included verbatim as the client provides, e.g.: *"This is an attempt to collect a debt, and any information obtained will be used for that purpose."* On later contacts, the abbreviated form may apply — follow the client's script exactly.
- **Right-party contact:** never disclose the debt to anyone but the debtor; verify identity first. If it's the wrong party or a third party, do not reveal the nature of the call.
- Honor cease-communication and dispute requests immediately (route to a human).
- No threats, no calls outside permitted hours, recording disclosure as required.
- Put **every** required phrase in the prompt verbatim; do not paraphrase compliance language. This vertical's guardrails are stricter than its sales goals — when in tension, compliance wins. If the script has many mandatory branches, this is a strong candidate for `retell-conversation-flow` instead.

## Retail / E-Commerce

**Common agents:** order status, returns/exchanges, simple support, post-purchase upsell.

**Flow (inbound order status):** Greeting → identify order (order number or `{{user_number}}` lookup via custom function) → read status back (with pronunciation rules) → resolve or escalate → optional soft upsell → Wrap-Up.

**Vertical objections:**
- "Where's my order?!" (frustrated) → empathy first ("I'm sorry it's running late, let me check right now"), then the lookup.
- Return outside policy → state the policy from the KB; offer the best available alternative; don't invent exceptions.

**Compliance:** light; accurate status (don't guess delivery dates), clean handling of refunds via the right tool/transfer.

---

## Cross-vertical patterns

- **Reminder / confirmation calls** (any vertical): keep it short — verify identity → state the appointment/payment/event with full pronunciation → confirm, reschedule, or cancel → close. Don't over-talk; these are 30–60 second calls.
- **Survey / feedback calls:** one question at a time, capture with `extract_dynamic_variables`, never argue with the answer, thank and close.
- **Emotionally charged verticals** (healthcare, collections, complaints): lead with the High Empathy preset, slow the responsiveness setting, and put the empathy-before-action rule front and center.
- **Any regulated vertical:** prefer **Scope Boundaries** + KB over free-form answers, enable **Structured Output**, and surface every mandatory disclosure verbatim in the prompt rather than letting the LLM phrase it.
