# Aubrey — Test Plan for feedback-02 Fixes

Created 2026-05-30. Covers everything we changed for [feedback-02.md](feedback-02.md) — Bernae's routing changes (2026-05-30) and the two production bugs from [call-issues-01.md](../call-issues/call-issues-01.md).

Run each test as a Retell web/test call. Most are 1–3 minutes.

---

## Setup

- The agent under test is `Aubrey_Agent.json` (current branch).
- For tests that verify transfer numbers, keep a tab open on your outbound carrier logs (or the Retell call dashboard) so you can confirm the *actual dialed number*, not just what Aubrey said.
- For the prospect tests, you'll need to actually go through the full 15-question intake — there's no shortcut.
- Caller-lookup is on phone (production). Web test calls have no `from_number`, so Aubrey treats you as **unrecognized** unless noted otherwise. That's fine for all tests below except Test 11.

---

## Test 1 — Bug 1 regression: no premature "anything else?" during ticket creation

**Goal:** confirm the global-prompt ticket-pipeline exception works. Aubrey must stay silent during `create_ticket` even if the caller says "thank you."

**Caller script:**
1. "Hi, I forgot to clock out yesterday."
2. (When asked) "Caregiver."
3. "Marcus Bell."
4. (Patient name) "Dorothy Hale."
5. (Date) "Yesterday afternoon, around 3 PM."
6. (Reason) "My phone died."
7. *(Aubrey says: "I'm submitting your request now."* — and you hear the typing/processing sound from `create_ticket`.)*
8. **Mid-create, say: "Thanks!"**

**PASS if:**
- ✅ Aubrey does **NOT** respond with "Is there anything else I can help you with today?" during the `create_ticket` tool run
- ✅ Aubrey stays silent through `create_ticket` → `Send Ticket SMS` → until Ticket Confirmation reads the ticket number
- ✅ "Is there anything else?" appears only AFTER the ticket-number readback

**FAIL signal:** Aubrey speaking ANY closing-like phrase ("Is there anything else?", "Have a great day", "Thank you for calling") between *"I'm submitting your request now"* and the ticket-number readback.

---

## Test 2 — Bug 2 regression: PROSPECT INTAKE auto-advances after Q15

**Goal:** confirm the PROSPECT INTAKE → PROSPECT SUBMIT transition fires immediately on the user's Q15 answer, with no "Still with me?" reminder.

**Caller script (timed — watch the clock between turns):**
1. "Hi, I want to sign up to get paid to take care of my mom."
2. "John Doe." (first name + last name)
3. (Phone confirm) "Yes, that's correct."
4. (City and state) "Atlanta, Georgia."
5. (Family caregiver?) "Yes."
6. (Relationship?) "Son."
7. (Medicaid?) "Yes, she has Medicaid."
8. (Receiving home care?) "No."
9. (Anyone being paid?) "No."
10. (Patient first name) "Grace."
11. (Patient last name) "Williams."
12. (DOB) "I'm not sure, sorry."
13. (Bathing/dressing help?) "Yes, she does."
14. (Alzheimer's/dementia?) "No."
15. (Autism/IDD?) — **"No, thankfully not."**

**PASS if:**
- ✅ Time between your Q15 answer and Aubrey's next utterance is **< 3 seconds**
- ✅ Aubrey's next utterance is the PROSPECT SUBMIT opener: *"Caregivers deserve real support, and we're going to start reviewing your case right away. I'll connect you with our Eligibility team in just a moment so we can keep things moving."*
- ✅ Aubrey does **NOT** say "Got it — one moment" or any acknowledgment after Q15
- ✅ "Still with me?" or "Take your time" reminder does **NOT** fire

**FAIL signal:** Any silence > 5 seconds, or any "Still with me?" prompt, or Aubrey saying "Got it" / "one moment" / "thank you" after Q15.

---

## Test 3 — New prospect: full intake → live transfer to Eligibility Dept

**Goal:** end-to-end test of the prospect post-ticket live transfer (A2).

**Caller script:** identical to Test 2 above, but keep going past Q15 through ticket readback.

After Test 2's PASS criteria are met, continue:
- *(Aubrey runs `create_ticket` and `Send Ticket SMS`.)*
- *(Ticket Confirmation: "Your ticket number is [digits]. Take a moment to write that down... You'll also get a text. Would you like me to repeat it?")*
- **You say: "No thanks."**

**PASS if:**
- ✅ Aubrey does **NOT** ask "Is there anything else I can help you with today?"
- ✅ Aubrey does **NOT** say "Thank you for calling, have a great day"
- ✅ Aubrey speaks: *"Now, let me connect you with our Eligibility Specialist team to get started. Please hold."*
- ✅ Dialed number on the outbound transfer is **`+1 678-785-7013`** (Eligibility Specialist Dept)

**FAIL signals:**
- Aubrey closing the call instead of transferring
- Dialed number is something other than `+16787857013`
- Aubrey saying she's connecting to "Case Support" or "Care Team" instead of Eligibility

---

## Test 4 — Returning applicant status check → Care Team

**Goal:** confirm the new Care Team number `+1 470-868-4776` is dialed for "I applied, just checking in" callers.

**Caller script:**
1. "Hi, I submitted my application last week. Just checking on the status."
2. *(Aubrey may offer the app link.)* "No, can I talk to someone?"
3. *(If asked anything else, give brief answers.)*

**PASS if:**
- ✅ Aubrey routes through **PROSPECT STATUS CHECK** (you'll hear the "you can check status through the Keyline app" prompt)
- ✅ When you ask for a person, Aubrey says: *"Let me connect you with our Care Team. Please hold."*
- ✅ Dialed number is **`+1 470-868-4776`**

**FAIL signals:**
- Aubrey routing to PROSPECT INTAKE instead (would mean OPENING didn't split correctly)
- Dialed number is `+16787857013` (old Care Team number — confirms the repoint didn't land)

---

## Test 5 — OPENING prospect-split clarifier fires on ambiguous intent

**Goal:** confirm the new PROSPECT VERIFICATION clarifier in OPENING asks the right disambiguating question.

**Caller script:**
1. "Hi, I'm calling about Keyline." *(deliberately vague)*
2. *(If Aubrey asks the caregiver/client/case-manager question)* "I'm a prospect."
3. *(Aubrey should ask the new clarifier:)* — **Wait and listen for the prompt:**
   > *"Just to make sure I get you to the right place — are you looking to enroll for the first time, or are you checking on the status of an application you already started?"*
4. Answer: "I'm looking to enroll."

**PASS if:**
- ✅ Aubrey asks the clarifier question (or a near-paraphrase) before routing
- ✅ After you answer "enroll", Aubrey routes to **PROSPECT INTAKE** (you'll hear "Keyline helps families get paid to care for loved ones at home" and the first-name question)

**Variant 5b** — same caller, but answer "I'm checking on the status of an application I submitted":
- ✅ Aubrey routes to **PROSPECT STATUS CHECK** instead

**Variant 5c** — caller is unambiguous from the start: *"I want to sign up to get paid to care for my mom."*
- ✅ Aubrey does **NOT** ask the clarifier — routes directly to PROSPECT INTAKE

---

## Test 6 — Caller asks for "the Eligibility Specialist" by name → Eligibility Dept

**Goal:** confirm the H1 fix routes Eligibility-Specialist requests to the Dept (not Alyssa).

**Caller script:**
1. "Hi, I'd like to speak with someone on the Eligibility Specialist team."
2. *(Aubrey may collect a few fields first — name, phone, state, status. Answer briefly.)*
3. *(When asked the purpose)* "I have an enrollment question only they can answer."
4. *(If Aubrey offers to help first)* "No, I really need to speak with them directly."

**PASS if:**
- ✅ Aubrey routes to **TRANSFER - ELIGIBILITY SPECIALIST DEPT**
- ✅ Dialed number is **`+1 678-785-7013`**

**FAIL signal:** Dialed number is `+1 470-243-8993` (that's Alyssa-Screening — pre-fix behavior).

---

## Test 7 — Caller asks for Alyssa / phone screening → Alyssa-Screening

**Goal:** confirm the H1 fix still routes phone-screening / nurse-assessment requests to Alyssa (not the new Eligibility Dept).

**Caller script:**
1. "Hi, I need to speak with Alyssa about my phone screening."
2. *(Aubrey collects fields; answer briefly.)*
3. *(Purpose)* "I want to reschedule my phone screening appointment."

**PASS if:**
- ✅ Aubrey routes to **TRANSFER - ALYSSA (SCREENING)**
- ✅ Dialed number is **`+1 470-243-8993`**

**FAIL signal:** Dialed number is `+1 678-785-7013` — would mean the disambiguation collapsed and screening got merged into the Dept route.

---

## Test 8 — GLOBAL HUMAN REQUEST → Case Support uniformly

**Goal:** confirm H2 closes the say/do gap. Aubrey should never promise "Care Team" from this node, and everyone goes to Case Support.

**Caller script (scenario A — active caregiver):**
1. "Hi, I forgot to clock out yesterday."
2. (Identification) "Caregiver."
3. **(After Aubrey starts collecting)** "Actually, I want to talk to a real person."

**PASS if:**
- ✅ Aubrey says: *"Of course — let me connect you with someone from our team right now. Please hold."* (generic — NOT "Care Team")
- ✅ Dialed number is **`+1 678-785-7010`** (Case Support)

**Variant 8b — prospect mid-intake:**
1. "I want to sign up to take care of my dad."
2. *(After 2-3 intake questions)* "Hold on, can I just talk to a person instead?"

**PASS if:**
- ✅ Same line — Aubrey says "someone from our team" (not Care Team)
- ✅ Dialed number is **`+1 678-785-7010`** (Case Support — the global node only reaches Case Support; prospects in mid-intake do NOT get routed to Care Team)

**FAIL signal:** Aubrey verbally saying "let me connect you with our Care Team" — that's the old prompt leaking through.

---

## Test 9 — Caregiver wants to switch providers → Care Team

**Goal:** confirm M1's tightened edge wording still fires correctly and routes to Care Team.

**Caller script:**
1. "Hi, I'm a caregiver and my client wants to switch to a different provider."
2. (Identification) "Caregiver."
3. *(If Aubrey asks anything else)* "Yeah, we want to move our service to a new provider."

**PASS if:**
- ✅ Aubrey routes to TRANSFER - CARE TEAM
- ✅ Dialed number is **`+1 470-868-4776`**

**FAIL signal:** Aubrey routing the caller into PROSPECT INTAKE instead (would mean the edge condition is too narrow / the LLM is misreading "switch" as "enroll fresh").

---

## Test 10 — Close-call vs prospect-xfer collision regression

**Goal:** confirm M2's mutual-exclusion fix. A prospect saying "no thanks" to the ticket-repeat offer must trigger the live transfer, NOT a hang-up.

**Caller script:** run a full prospect intake (use Test 3's script through ticket creation). Then at the ticket-readback:
- *(Aubrey: "Your ticket number is [digits]. Take a moment to write that down... Would you like me to repeat it?")*
- **You say: "No, thanks."**

**PASS if:**
- ✅ Aubrey does **NOT** say "Thank you for calling Keyline Home Care. Have a great day!"
- ✅ Aubrey does **NOT** hang up
- ✅ Aubrey speaks: *"Now, let me connect you with our Eligibility Specialist team to get started. Please hold."*
- ✅ Dialed number is **`+1 678-785-7013`**

**FAIL signal:** Aubrey closing the call after "no thanks" — that's the close-call edge firing instead of the prospect-xfer edge.

---

## Test 11 — Returning caller patient confirmation (regression from earlier work)

**Goal:** double-check that the returning-caller flow still works after all the routing edits.

**Pre-req:** run Test 1 first to seed a caller-board row for this phone with **Caller Patient Name = Dorothy Hale**.

**Caller script (from the same number used in Test 1):**
1. "Hi, I missed my clock-in this morning."

**PASS if:**
- ✅ Aubrey greets with "welcome back" or recognized greeting
- ✅ Aubrey **confirms** the patient: *"Just to confirm, you're caring for Dorothy Hale, right?"* — does **not** re-ask the patient name from scratch

---

## Quick-reference scorecard

| # | Test | Verifies | Expected dialed number |
|---|------|----------|------------------------|
| 1 | Mid-ticket "thanks" | Bug 1 fix (global prompt exception) | n/a (no transfer) |
| 2 | PROSPECT INTAKE Q15 auto-advance | Bug 2 fix (edge condition + Got-it removal) | n/a |
| 3 | New prospect → live transfer | A2 (prospect post-ticket flow) | `+16787857013` |
| 4 | Returning applicant status check | A1.1 (Care Team repoint) | `+14708684776` |
| 5 | OPENING prospect-split clarifier | A3.1 (prospect verification) | n/a (routing only) |
| 6 | "Eligibility Specialist" request | H1 (split eligibility edge) | `+16787857013` |
| 7 | "Alyssa" / phone screening request | H1 (split eligibility edge) | `+14702438993` |
| 8 | Mid-flow "talk to a real person" | H2 (GLOBAL HUMAN REQUEST) | `+16787857010` |
| 9 | Caregiver switching providers | M1 (switching-providers wording) | `+14708684776` |
| 10 | Prospect "no thanks" after ticket | M2 (close-call vs xfer collision) | `+16787857013` |
| 11 | Returning caller — patient confirm | Regression — earlier work still intact | n/a |

---

## What to capture per test

For each test, jot down:
- ✅ / ❌ for each PASS criterion
- The actual dialed number (from Retell logs / outbound carrier)
- Any unexpected behavior (extra questions, weird pauses, wrong wording)
- Audio recording link if available (so we can diff against the script later)

If any test fails, capture the **full Retell transcript** of that call so we can trace which node/edge misfired.
