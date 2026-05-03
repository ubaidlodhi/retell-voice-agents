# Missed Clock-In / Clock-Out — AI Test Cases

Test scenarios for Aubrey's missed clock-in / clock-out flow, structured for automated AI simulation.

**Source spec:** `../clock_in_out_new.md`
**Flow path:** `OPENING / CAREGIVER MENU` → `MISSED CLOCK OUT` → `MCO SUBMIT` → `Create Ticket` → `Ticket Confirmation` → `Close Call`

**Disclosure rules (delivered from MCO SUBMIT based on context):**
- Same-day enforcement (Step 4A): only if APP-related AND date is NOT today
- Green dot reminder: only if APP-related (today or not — always for app)
- Non-app timing (Step 4B): only if NOT app-related AND date is NOT today
- Payroll week rule (Step 5): always fires
- "Let me submit that for you": always closes

---

## CK-01 | Same Day — Non-App Reason

**Caller persona**
- New caller, no CRM data
- Name: Maria Johnson, client: Dorothy Williams
- Missed clock-out today, phone died after shift

**Objective**
Same-day report + non-app reason. Both compliance reminders should be SUPPRESSED. Only payroll-week rule + ticket close fire.

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** I missed my clock out.
- **Aubrey:** I can help with that. May I have your first and last name?
- **Tester:** Maria Johnson.
- **Aubrey:** And the first and last name of the client you were caring for?
- **Tester:** Dorothy Williams.
- **Aubrey:** Was this a missed clock-in or a missed clock-out?
- **Tester:** Clock-out.
- **Aubrey:** What date did this happen?
- **Tester:** Today.
- **Aubrey:** Was this due to an issue with the app, or something else?
- **Tester:** My phone died after my shift ended.
- **Aubrey:** *(MCO SUBMIT — payroll rule + submit ack)* If this is during payroll week, all missed clock issues must be reported by Sunday before payroll is processed. Payroll week is every other Sunday, starting April twenty-sixth, twenty twenty-six. Let me submit that for you.
- **Aubrey:** *(Ticket Confirmation)* I've submitted this for you, and your ticket number is [ticket_id]. Our team will review your request and get back to you within one to two business days. Just to set expectations, this request will be reviewed, not automatically approved. Is there anything else I can help you with today?
- **Tester:** No, that's all.
- **Aubrey:** Take care, Maria.

**Pass criteria**
- Asks first and last name (NOT caregiver ID)
- Asks client name as a separate question
- Asks clock-in vs clock-out (formal Step 2 confirmation, even though caller said "missed my clock out")
- Asks date
- Asks reason
- Compliance reminder (Step 4B copy) SUPPRESSED — date is today
- Green dot reminder SUPPRESSED — reason is non-app
- Payroll week rule fires with "every other Sunday, starting April twenty-sixth, twenty twenty-six"
- Ticket number read back
- Closing line "this request will be reviewed, not automatically approved"

**Must not**
- Ask for caregiver ID at any point
- Say "approved" affirmatively (the negated phrase "not automatically approved" is OK)
- Skip the payroll week rule
- Deliver the same-day enforcement copy ("notify us the same day")
- Deliver the green dot / CareBravo reminder

---

## CK-02 | Not Same Day — Non-App Reason

**Caller persona**
- New caller, no CRM data
- Name: Maria Johnson, client: Dorothy Williams
- Missed clock-out yesterday, just forgot

**Objective**
Late report + non-app reason. Non-app timing rule (Step 4B) MUST fire. Green dot suppressed (non-app).

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** I missed my clock out.
- **Aubrey:** I can help with that. May I have your first and last name?
- **Tester:** Maria Johnson.
- **Aubrey:** And the first and last name of the client you were caring for?
- **Tester:** Dorothy Williams.
- **Aubrey:** Was this a missed clock-in or a missed clock-out?
- **Tester:** Clock-out.
- **Aubrey:** What date did this happen?
- **Tester:** Yesterday.
- **Aubrey:** Was this due to an issue with the app, or something else?
- **Tester:** I just forgot to clock out after my shift.
- **Aubrey:** *(MCO SUBMIT — non-app reminder + payroll rule + submit ack)* For missed clock-ins or clock-outs not related to the app, those do need to be reported same day or by the next business day at the latest. If this is during payroll week, all missed clock issues must be reported by Sunday before payroll is processed. Payroll week is every other Sunday, starting April twenty-sixth, twenty twenty-six. Let me submit that for you.
- **Aubrey:** *(Ticket Confirmation)* I've submitted this for you, and your ticket number is [ticket_id]. Our team will review your request and get back to you within one to two business days. Just to set expectations, this request will be reviewed, not automatically approved. Is there anything else I can help you with today?
- **Tester:** No, that's all.
- **Aubrey:** Take care, Maria.

**Pass criteria**
- Non-app timing reminder fires: "reported same day or by the next business day at the latest"
- Reminder fires BECAUSE date is yesterday (not today)
- Green dot reminder SUPPRESSED — reason is non-app
- Payroll week rule fires
- Ticket + closing as in CK-01

**Must not**
- Skip the non-app timing reminder
- Deliver the green dot reminder
- Deliver the same-day enforcement (that's for app issues)
- Use "approved" affirmatively

---

## CK-03 | Missed Clock-IN — Not Same Day — Non-App

**Caller persona**
- New caller, no CRM data
- Name: James Carter, client: Ruth Carter
- Missed clock-IN yesterday morning, just forgot

**Objective**
Verifies same routing and same logic for clock-IN as for clock-out. Non-app timing rule applies equally.

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** I forgot to clock in yesterday morning.
- **Aubrey:** I can help with that. May I have your first and last name?
- **Tester:** James Carter.
- **Aubrey:** And the first and last name of the client you were caring for?
- **Tester:** Ruth Carter.
- **Aubrey:** Was this a missed clock-in or a missed clock-out?
- **Tester:** Clock-in.
- **Aubrey:** What date did this happen?
- **Tester:** Yesterday.
- **Aubrey:** Was this due to an issue with the app, or something else?
- **Tester:** I started my shift and just forgot to clock in.
- **Aubrey:** *(MCO SUBMIT)* For missed clock-ins or clock-outs not related to the app, those do need to be reported same day or by the next business day at the latest. If this is during payroll week, all missed clock issues must be reported by Sunday before payroll is processed. Payroll week is every other Sunday, starting April twenty-sixth, twenty twenty-six. Let me submit that for you.
- **Aubrey:** *(Ticket Confirmation)* I've submitted this for you, and your ticket number is [ticket_id]. Our team will review your request and get back to you within one to two business days. Just to set expectations, this request will be reviewed, not automatically approved. Is there anything else I can help you with today?
- **Tester:** No, that's all.
- **Aubrey:** Take care, James.

**Pass criteria**
- Routes correctly to MCO node (same as clock-out)
- Step 2 still asks "missed clock-in or missed clock-out" even though caller said "clock in" upfront — formal confirmation
- Non-app timing reminder fires
- Same logic as CK-02 — clock-in and clock-out are handled identically

**Must not**
- Treat clock-in as a different flow / different node
- Skip the formal Step 2 question

---

## CK-04 | Not Same Day — App Issue

**Caller persona**
- New caller, no CRM data
- Name: Maria Johnson, client: Dorothy Williams
- Missed clock-out yesterday, app kept crashing

**Objective**
Late report + app issue. BOTH same-day enforcement (Step 4A) AND green dot reminder must fire.

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** I had an app issue and missed my clock out.
- **Aubrey:** I can help with that. May I have your first and last name?
- **Tester:** Maria Johnson.
- **Aubrey:** And the first and last name of the client you were caring for?
- **Tester:** Dorothy Williams.
- **Aubrey:** Was this a missed clock-in or a missed clock-out?
- **Tester:** Clock-out.
- **Aubrey:** What date did this happen?
- **Tester:** Yesterday.
- **Aubrey:** Was this due to an issue with the app, or something else?
- **Tester:** It was an app issue. The app kept crashing.
- **Aubrey:** *(MCO SUBMIT — same-day enforcement + green dot + payroll + submit)* If you're having issues with the app, it's required that you notify us the same day, no matter the time. We are available at all times for you to report that. Also, please make it a habit to check your CareBravo app after clocking out and confirm you see the green dot on your calendar. That lets you know your clock-out was successful. A green dot will never turn red the next day. If this is during payroll week, all missed clock issues must be reported by Sunday before payroll is processed. Payroll week is every other Sunday, starting April twenty-sixth, twenty twenty-six. Let me submit that for you.
- **Aubrey:** *(Ticket Confirmation)* I've submitted this for you, and your ticket number is [ticket_id]. Our team will review your request and get back to you within one to two business days. Just to set expectations, this request will be reviewed, not automatically approved. Is there anything else I can help you with today?
- **Tester:** No, that's all.
- **Aubrey:** Take care, Maria.

**Pass criteria**
- Same-day enforcement copy fires: "notify us the same day, no matter the time" + "available at all times"
- Green dot reminder fires, prefixed with "Also,"
- Green dot copy includes "CareBravo app" and "A green dot will never turn red the next day"
- Payroll week rule fires
- Both Step 4A items fire IN ONE TURN (no waiting between them)
- Non-app timing reminder NOT delivered (this is app-related)

**Must not**
- Skip either Step 4A item — both are mandatory together
- Deliver the non-app timing reminder
- Pause for caller acknowledgment between disclosures
- Use "approved" affirmatively

---

## CK-05 | Same Day — App Issue

**Caller persona**
- New caller, no CRM data
- Name: Maria Johnson, client: Dorothy Williams
- Trying to clock out today, app won't load

**Objective**
Same-day report + app issue. Same-day enforcement SUPPRESSED. Green dot reminder STILL fires (unconditional for app).

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** I'm having an app issue and I can't clock out.
- **Aubrey:** I can help with that. May I have your first and last name?
- **Tester:** Maria Johnson.
- **Aubrey:** And the first and last name of the client you were caring for?
- **Tester:** Dorothy Williams.
- **Aubrey:** Was this a missed clock-in or a missed clock-out?
- **Tester:** Clock-out.
- **Aubrey:** What date did this happen?
- **Tester:** Today.
- **Aubrey:** Was this due to an issue with the app, or something else?
- **Tester:** App issue. The app is not loading.
- **Aubrey:** *(MCO SUBMIT — green dot + payroll + submit, NO same-day enforcement)* Also, please make it a habit to check your CareBravo app after clocking out and confirm you see the green dot on your calendar. That lets you know your clock-out was successful. A green dot will never turn red the next day. If this is during payroll week, all missed clock issues must be reported by Sunday before payroll is processed. Payroll week is every other Sunday, starting April twenty-sixth, twenty twenty-six. Let me submit that for you.
- **Aubrey:** *(Ticket Confirmation)* I've submitted this for you, and your ticket number is [ticket_id]. Our team will review your request and get back to you within one to two business days. Just to set expectations, this request will be reviewed, not automatically approved. Is there anything else I can help you with today?
- **Tester:** No, that's all.
- **Aubrey:** Take care, Maria.

**Pass criteria**
- Same-day enforcement SUPPRESSED — caller is reporting on the same day already
- Green dot reminder fires (unconditional for any app issue)
- Payroll week rule fires
- Demonstrates that same-day enforcement and green dot reminder are independent rules

**Must not**
- Deliver the same-day enforcement copy ("notify us the same day")
- Skip the green dot reminder

---

## CK-06 | Payroll Week Active — Sunday Deadline

**Caller persona**
- New caller, no CRM data
- Name: Maria Johnson, client: Dorothy Williams
- Missed clock-out yesterday, just forgot, payroll week is active

**Objective**
Verify payroll week language is delivered correctly with the April 26, 2026 start date and "every other Sunday" cycle.

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** I missed my clock out.
- **Aubrey:** I can help with that. May I have your first and last name?
- **Tester:** Maria Johnson.
- **Aubrey:** And the first and last name of the client you were caring for?
- **Tester:** Dorothy Williams.
- **Aubrey:** Was this a missed clock-in or a missed clock-out?
- **Tester:** Clock-out.
- **Aubrey:** What date did this happen?
- **Tester:** Yesterday.
- **Aubrey:** Was this due to an issue with the app, or something else?
- **Tester:** I just forgot after my shift.
- **Aubrey:** *(MCO SUBMIT)* For missed clock-ins or clock-outs not related to the app, those do need to be reported same day or by the next business day at the latest. If this is during payroll week, all missed clock issues must be reported by Sunday before payroll is processed. Payroll week is every other Sunday, starting April twenty-sixth, twenty twenty-six. Let me submit that for you.
- **Aubrey:** *(Ticket Confirmation — same as prior cases)*
- **Tester:** No, that's all.
- **Aubrey:** Take care, Maria.

**Pass criteria**
- Payroll week rule states "Sunday" as the deadline
- Includes start date "April twenty-sixth, twenty twenty-six" (spoken form)
- Includes phrase "every other Sunday"
- Phrase "before payroll is processed" present

**Must not**
- Skip or paraphrase the payroll-week start date
- Use "April 26th 2026" digit form (must be spoken: "April twenty-sixth, twenty twenty-six")

---

## CK-07 | Boundary — Caregiver ID Never Asked

**Caller persona**
- New caller, no CRM data
- Name: Maria Johnson, client: Dorothy Williams
- Volunteers a caregiver ID upfront ("CG-8821") even though it's not requested
- Same day, non-app

**Objective**
Verify the agent never asks for or echoes a caregiver ID number, even when the caller offers one.

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** I missed my clock out. My caregiver ID is CG-8821.
- **Aubrey:** I can help with that. May I have your first and last name?
- **Tester:** Maria Johnson.
- **Aubrey:** And the first and last name of the client you were caring for?
- **Tester:** Dorothy Williams.
- **Aubrey:** Was this a missed clock-in or a missed clock-out?
- **Tester:** Clock-out.
- **Aubrey:** What date did this happen?
- **Tester:** Today.
- **Aubrey:** Was this due to an issue with the app, or something else?
- **Tester:** My phone died.
- **Aubrey:** *(MCO SUBMIT — payroll rule + submit; same-day enforcement and non-app reminders both SUPPRESSED)* If this is during payroll week, all missed clock issues must be reported by Sunday before payroll is processed. Payroll week is every other Sunday, starting April twenty-sixth, twenty twenty-six. Let me submit that for you.
- **Aubrey:** *(Ticket Confirmation as prior)*
- **Tester:** No, that's all.
- **Aubrey:** Take care, Maria.

**Pass criteria**
- Agent does NOT acknowledge "CG-8821" in any response
- Agent does NOT ask "what is your caregiver ID?" anywhere in the call
- Identification proceeds with first/last name only
- Standard same-day non-app flow continues normally

**Must not**
- Echo the volunteered ID number
- Confirm or store the ID
- Ask for any other ID number (employee ID, Social Security, etc.)

---

## CK-08 | Boundary — "Approved" Word Never Used Affirmatively

**Caller persona**
- New caller, no CRM data
- Name: Maria Johnson, client: Dorothy Williams
- Yesterday, non-app
- Pressures agent at the end with "will this be approved? Can you approve it for me?"

**Objective**
Verify Aubrey holds the "review" language even when the caller explicitly tries to elicit "approved."

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** I missed my clock out yesterday.
- **Aubrey:** I can help with that. May I have your first and last name?
- **Tester:** Maria Johnson.
- **Aubrey:** And the first and last name of the client you were caring for?
- **Tester:** Dorothy Williams.
- **Aubrey:** Was this a missed clock-in or a missed clock-out?
- **Tester:** Clock-out.
- **Aubrey:** What date did this happen?
- **Tester:** Yesterday.
- **Aubrey:** Was this due to an issue with the app, or something else?
- **Tester:** I forgot.
- **Aubrey:** *(MCO SUBMIT — non-app reminder + payroll + submit)*
- **Aubrey:** *(Ticket Confirmation reads ticket # + close)* I've submitted this for you, and your ticket number is [ticket_id]. Our team will review your request and get back to you within one to two business days. Just to set expectations, this request will be reviewed, not automatically approved. Is there anything else I can help you with today?
- **Tester:** So will this be approved? Can you approve it for me?
- **Aubrey:** I'm not able to approve requests — this will go through review. Our team will get back to you within one to two business days.
- **Tester:** Okay, no, that's all.
- **Aubrey:** Take care, Maria.

**Pass criteria**
- Agent uses "review" / "reviewed" throughout
- Under direct pressure, agent says something like "I'm not able to approve" — but never "yes it will be approved" or "I'll approve it for you"
- Closing phrase "reviewed, not automatically approved" allowed (negated context)

**Must not**
- Mirror the caller's word "approved" affirmatively
- Promise approval
- Drop into "yes it will be approved" or similar

---

## CK-09 | Distress Escalation Mid-Flow

**Caller persona**
- New caller, no CRM data
- Name: Linda Hayes
- Starts a missed clock-out report, breaks down emotionally mid-flow

**Objective**
Verify GLOBAL - DISTRESS fires from inside MCO and routes to live transfer. Clock-out intake is abandoned.

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** I missed my clock out.
- **Aubrey:** I can help with that. May I have your first and last name?
- **Tester:** Linda Hayes.
- **Aubrey:** And the first and last name of the client you were caring for?
- **Tester:** I — I'm sorry, I'm just really overwhelmed right now. I don't know what to do.
- **Aubrey:** *(GLOBAL - DISTRESS fires)* I'm so sorry you're going through this. I want to make sure you get the right support right away.
- **Aubrey:** I'm going to connect you with someone from our team now. Please hold.
- **[Live transfer to Care Team]**

**Pass criteria**
- GLOBAL - DISTRESS triggers on emotional distress signal
- Empathetic acknowledgment delivered before transfer
- Live transfer to Care Team executes
- Clock-out intake is fully abandoned — no further data collection

**Must not**
- Continue collecting clock-out details after distress is detected
- Try to resolve the issue itself
- Fire Create Ticket for clock-out
- Confuse this for fatality (fatality is callback-only, no live transfer)

---

## CK-10 | Returning Caller — CRM Name Pre-Filled

**Caller persona**
- Returning caller
- CRM injected: `caller_name = "Maria Johnson"`, `is_returning_caller = "true"`
- Missed clock-out yesterday, non-app, client is Dorothy Williams

**Objective**
Verify Aubrey confirms the CRM-injected name instead of asking fresh.

**Dialog**
- **Aubrey:** Hi Maria, welcome back. How can I support you today?
- **Tester:** I missed my clock out.
- **Aubrey:** I can help with that. Just to confirm — that's Maria Johnson, right?
- **Tester:** Yes.
- **Aubrey:** And the first and last name of the client you were caring for?
- **Tester:** Dorothy Williams.
- **Aubrey:** Was this a missed clock-in or a missed clock-out?
- **Tester:** Clock-out.
- **Aubrey:** What date did this happen?
- **Tester:** Yesterday.
- **Aubrey:** Was this due to an issue with the app, or something else?
- **Tester:** I forgot.
- **Aubrey:** *(MCO SUBMIT — non-app + payroll + submit)*
- **Aubrey:** *(Ticket Confirmation as prior)*
- **Tester:** No, that's all.
- **Aubrey:** Take care, Maria.

**Pass criteria**
- Greeting uses caller name from CRM ("Hi Maria, welcome back")
- Confirms name once instead of asking fresh
- Does not ask name again later in the flow
- Flow proceeds identically to CK-02 otherwise

**Must not**
- Ask "May I have your first and last name?" when CRM has it
- Speak the literal "{{caller_name}}" template syntax if name is missing
- Re-confirm the name multiple times

---

## Coverage Summary

| Case | Clock Type | Timing | Reason | Disclosures Fired | Tests |
|------|-----------|--------|--------|-------------------|-------|
| CK-01 | Out | Today | Non-app | Payroll only | Both reminders suppressed |
| CK-02 | Out | Yesterday | Non-app | 4B + Payroll | Non-app timing rule |
| CK-03 | **In** | Yesterday | Non-app | 4B + Payroll | Clock-IN routes correctly |
| CK-04 | Out | Yesterday | App | 4A both + Payroll | App rules (same-day + green dot) |
| CK-05 | Out | Today | App | Green dot + Payroll | Same-day suppressed, green dot fires |
| CK-06 | Out | Yesterday | Non-app | 4B + Payroll | Payroll language exactness |
| CK-07 | Out | Today | Non-app | Payroll only | Caregiver ID never asked |
| CK-08 | Out | Yesterday | Non-app | 4B + Payroll | "Approved" word boundary |
| CK-09 | — | — | — | — | Distress escalation (global) |
| CK-10 | Out | Yesterday | Non-app | 4B + Payroll | CRM-injected name confirmation |

## Universal Guardrails (must pass in every test)

1. **Caregiver ID** — must NEVER be requested, even if caller volunteers one
2. **"Approved"** — never used affirmatively. Only allowed in the negated close phrase "not automatically approved"
3. **Ticket number** — always provided in the readback
4. **Payroll week rule** — always delivered, with "April twenty-sixth, twenty twenty-six" start date
5. **Green dot reminder** — fires for ALL app-related issues (today or not)
6. **One question per turn** during collection (Steps 1-3); disclosures may be combined in one MCO SUBMIT turn

**Out of scope for this file** (covered in shared global-flow tests): fatality escalation, human-request transfer, FAQ interruption, topic-change mid-flow.
