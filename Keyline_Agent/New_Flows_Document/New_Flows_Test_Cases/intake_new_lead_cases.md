# Intake (New Lead) — AI Test Cases

Test scenarios for Aubrey's new-lead intake flow (callers signing up or asking about services), structured for automated AI simulation.

**Source spec:** `../intake_new_lead.md`
**Flow path:** `OPENING` → `PROSPECT INTAKE` → `PROSPECT SUBMIT` → `Create Ticket` → `Ticket Confirmation` → `Close Call` → `End Call`

**Key spec rule:** No live transfer. The team contacts the caller LATER by call or text with next steps.

**Closing message (verbatim, delivered from PROSPECT SUBMIT):**
> "Caregivers deserve real support, and we're going to start reviewing your case right away. You'll receive an update on your eligibility within one business day or sooner. Please be on the lookout for a call or text with next steps."

**Then:** `"I'm submitting your request now."` → tool fires → ticket # read back → `"Is there anything else I can help you with today?"` → close.

---

## IN-01 | Standard Happy Path — Has Medicaid

**Caller persona**
- New caller, no CRM data
- Name: Jennifer Lopez (sounds like a great-granddaughter calling), phone 555-100-2000, email jen@example.com, city Phoenix Arizona
- Family caregiver for her mother (Maria Lopez, DOB unknown)
- Mother HAS Medicaid, no current home care, no one being paid
- Mother needs help with bathing/dressing, has dementia, no autism

**Objective**
Most basic intake path. All 16 fields collected one per turn, expectation-setting closing delivered, ticket created, no transfer.

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** Hi, I'd like to learn about getting paid to care for my mom.
- **Aubrey:** Keyline helps families get paid to care for loved ones at home. May I have your first name?
- **Tester:** Jennifer.
- **Aubrey:** And your last name?
- **Tester:** Lopez.
- **Aubrey:** And your phone number?
- **Tester:** 555-100-2000.
- **Aubrey:** Just to confirm — that's five-five-five, one-zero-zero, two-zero-zero-zero, right?
- **Tester:** Yes.
- **Aubrey:** And your email address?
- **Tester:** jen@example.com.
- **Aubrey:** Let me confirm — that's j-e-n at gmail dot com? *(or natural domain readback)*
- **Tester:** Yes.
- **Aubrey:** What city and state are you calling from?
- **Tester:** Phoenix, Arizona.
- **Aubrey:** Are you the family caregiver?
- **Tester:** Yes.
- **Aubrey:** What is your relationship to the patient?
- **Tester:** She's my mother.
- **Aubrey:** Does the patient have Medicaid?
- **Tester:** Yes.
- **Aubrey:** Is the patient currently receiving home care services?
- **Tester:** No.
- **Aubrey:** Is anyone currently being paid to care for them?
- **Tester:** No.
- **Aubrey:** What's the patient's first name?
- **Tester:** Maria.
- **Aubrey:** And the patient's last name?
- **Tester:** Lopez.
- **Aubrey:** Do you have the patient's date of birth?
- **Tester:** I don't, sorry.
- **Aubrey:** No problem. Does the patient need help with bathing or dressing?
- **Tester:** Yes, she needs help with both.
- **Aubrey:** Does the patient have Alzheimer's or dementia?
- **Tester:** Yes, dementia.
- **Aubrey:** Does the patient have autism or an intellectual or developmental disability?
- **Tester:** No.
- **Aubrey:** *(PROSPECT SUBMIT)* Caregivers deserve real support, and we're going to start reviewing your case right away. You'll receive an update on your eligibility within one business day or sooner. Please be on the lookout for a call or text with next steps. I'm submitting your request now.
- **Aubrey:** *(Create Ticket)* Just a moment please, this will only take a second.
- **Aubrey:** *(Ticket Confirmation)* Your ticket number is [ticket_id]. Is there anything else I can help you with today?
- **Tester:** No, thank you.
- **Aubrey:** *(Close Call)* Thank you for calling Keyline Home Care. Have a great day, Jennifer!

**Pass criteria**
- All 16 fields collected one per turn (no combining)
- Phone read back (3-3-4 digit grouping per global rule)
- Email read back per global rule (gmail spoken naturally for common domains)
- DOB question handled gracefully when caller doesn't have it ("No problem" continuation)
- Closing message delivered verbatim from PROSPECT SUBMIT
- Includes "one business day or sooner" + "call or text with next steps"
- Ticket # read back briefly
- "Is there anything else?" asked before close
- **No live transfer** — call ends with CLOSE CALL, no Eligibility Specialist transfer

**Must not**
- Combine multiple fields into one question
- Skip any of the 16 fields
- Stop or block when caller says "no Medicaid" — continue regardless
- Transfer the caller to Eligibility Specialist (not in spec)
- Repeat the closing expectation message in Ticket Confirmation
- Speak the literal "{{caller_name}}" template

---

## IN-02 | No Medicaid Path — Flow Continues Anyway

**Caller persona**
- New caller, no CRM data
- Name: Robert Tan, phone 555-300-4000, email robert@example.com, Seattle Washington
- Caring for his elderly father, no Medicaid
- Father has Alzheimer's, no autism, needs bathing help

**Objective**
Verifies §7 flow logic — caller answers "No" to Medicaid, intake continues without stopping.

**Dialog (abbreviated for brevity — same shape as IN-01 through Q8)**
- ... [Steps 1-7: caller info + caregiver ID collected] ...
- **Aubrey:** Does the patient have Medicaid?
- **Tester:** No, he doesn't have Medicaid.
- **Aubrey:** Is the patient currently receiving home care services?
- **Tester:** No.
- ... [continues through Q10-16 normally] ...
- **Aubrey:** *(PROSPECT SUBMIT — closing message + submit)*
- **Aubrey:** *(Create Ticket → Ticket Confirmation)* Your ticket number is [ticket_id]. Is there anything else I can help you with today?
- **Tester:** No, thank you.
- **Aubrey:** Thank you for calling Keyline Home Care. Have a great day, Robert!

**Pass criteria**
- After "No" to Medicaid, agent asks Q9 (currently receiving home care services?) without pause or redirect
- Flow continues through all remaining questions
- Closing message + ticket creation happens normally
- No "well unfortunately we can't help you" language

**Must not**
- End the call early when caller says "No Medicaid"
- Skip questions 9-16 because Medicaid is "No"
- Tell the caller they don't qualify (eligibility is determined by the team, not Aubrey)
- Refer to Medicaid as a hard requirement on the call

---

## IN-03 | DOB Provided — Patient Has Autism

**Caller persona**
- New caller, no CRM data
- Name: Anita Patel, phone 555-500-6000, email anita@example.com, Houston Texas
- Caregiver for her brother (David Patel, DOB March 15, 1990)
- Has Medicaid, currently receiving services informally, no one paid yet
- David has autism (developmental disability), needs help with dressing

**Objective**
Verifies the DOB collection branch (when caller has the date) and the §6 condition questions for autism/IDD path.

**Dialog (key turns)**
- ... [Steps 1-7: caller info + relationship "brother"] ...
- **Aubrey:** Does the patient have Medicaid?
- **Tester:** Yes.
- **Aubrey:** Is the patient currently receiving home care services?
- **Tester:** Yes, I'm taking care of him myself but informally.
- **Aubrey:** Is anyone currently being paid to care for them?
- **Tester:** No, not yet.
- **Aubrey:** What's the patient's first name?
- **Tester:** David.
- **Aubrey:** And the patient's last name?
- **Tester:** Patel.
- **Aubrey:** Do you have the patient's date of birth?
- **Tester:** Yes, March fifteenth, nineteen ninety.
- **Aubrey:** Got it. Does the patient need help with bathing or dressing?
- **Tester:** Yes, dressing mainly.
- **Aubrey:** Does the patient have Alzheimer's or dementia?
- **Tester:** No.
- **Aubrey:** Does the patient have autism or an intellectual or developmental disability?
- **Tester:** Yes, he has autism.
- **Aubrey:** *(PROSPECT SUBMIT — closing message + submit)*
- **Aubrey:** *(Ticket Confirmation)* Your ticket number is [ticket_id]. Is there anything else I can help you with today?

**Pass criteria**
- DOB collected when caller offers it ("March fifteenth, nineteen ninety")
- All 3 condition questions asked (bathing/dressing, dementia, autism)
- Each condition question answered separately
- Closing message + ticket created normally

**Must not**
- Skip the bathing/dressing question because caller mentioned autism
- Skip the dementia question
- Combine condition questions into one
- Refuse intake based on patient already receiving informal care

---

## IN-04 | Switching from Another Provider — Currently Being Paid

**Caller persona**
- New caller, no CRM data
- Name: Marcus Lee, phone 555-700-8000, email marcus@example.com, Atlanta Georgia
- Caring for his wife (Helen Lee, DOB 1965)
- Has Medicaid, currently receiving services through another provider, currently being paid by that provider
- Wife has dementia, needs help with bathing AND dressing, no autism

**Objective**
Verifies the path where caller is "switching providers" — already paid by another agency. Flow should continue normally.

**Dialog (key turns)**
- ... [Steps 1-7] ...
- **Aubrey:** Does the patient have Medicaid?
- **Tester:** Yes.
- **Aubrey:** Is the patient currently receiving home care services?
- **Tester:** Yes, through another agency. We want to switch.
- **Aubrey:** Is anyone currently being paid to care for them?
- **Tester:** Yes, I'm being paid by the other agency right now.
- **Aubrey:** What's the patient's first name?
- ... [continues normally through condition questions] ...
- **Aubrey:** *(PROSPECT SUBMIT)* Caregivers deserve real support, and we're going to start reviewing your case right away. You'll receive an update on your eligibility within one business day or sooner. Please be on the lookout for a call or text with next steps. I'm submitting your request now.
- **Aubrey:** *(Ticket Confirmation)* Your ticket number is [ticket_id]. Is there anything else I can help you with today?

**Pass criteria**
- Continues normally when caller says "Yes" to currently receiving services + "Yes" to currently being paid
- No "you can't switch" or "you're not eligible" language
- Closing + ticket as normal

**Must not**
- Block the intake because caller is currently with another provider
- Comment on whether they can switch — that's the team's job to evaluate

---

## IN-05 | Distress Escalation Mid-Flow

**Caller persona**
- New caller, no CRM data
- Name: Carmen Rivera
- Calling to enroll, breaks down emotionally mid-collection (overwhelmed)

**Objective**
Verify GLOBAL - DISTRESS fires from inside PROSPECT INTAKE and routes to live transfer. Intake is abandoned.

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** Hi, I'm trying to figure out how to get paid for caring for my dad.
- **Aubrey:** Keyline helps families get paid to care for loved ones at home. May I have your first name?
- **Tester:** Carmen.
- **Aubrey:** And your last name?
- **Tester:** Rivera.
- **Aubrey:** And your phone number?
- **Tester:** I'm sorry, this is just so much. I don't know what to do, I can't keep doing this alone.
- **Aubrey:** *(GLOBAL - DISTRESS)* I'm so sorry you're going through this. I want to make sure you get the right support right away.
- **Aubrey:** I'm going to connect you with someone from our team now. Please hold.
- **[Live transfer to Care Team]**

**Pass criteria**
- GLOBAL - DISTRESS triggers on emotional distress signal
- Empathetic acknowledgment delivered before transfer
- Live transfer to Care Team executes
- Intake fully abandoned — no Create Ticket fires for prospect

**Must not**
- Continue collecting fields after distress is detected
- Try to explain the program in detail (caller needs human support, not info)
- Confuse this for fatality (fatality is callback-only, no live transfer)

---

## IN-06 | Returning Caller — CRM Pre-Filled

**Caller persona**
- Returning caller (called once before, didn't complete intake)
- CRM injected: `caller_name = "Diane Chen"`, `caller_email = "diane@example.com"`, `is_returning_caller = "true"`
- Calling back to complete the application
- Phone, city/state, all patient/condition info still need to be collected

**Objective**
Verify Aubrey confirms CRM-injected fields instead of asking fresh, then collects the rest.

**Dialog (key turns)**
- **Aubrey:** Hi Diane, welcome back. How can I support you today?
- **Tester:** Hi, I called yesterday to start an application but didn't finish.
- **Aubrey:** Keyline helps families get paid to care for loved ones at home. Just to confirm — that's Diane Chen, right?
- **Tester:** Yes.
- **Aubrey:** And the best phone number to reach you?
- **Tester:** 555-200-3000.
- **Aubrey:** I've got your email as diane@example.com — should I use that?
- **Tester:** Yes.
- **Aubrey:** What city and state are you calling from?
- **Tester:** Boston, Massachusetts.
- *(continues with steps 6-16 normally)*
- **Aubrey:** *(PROSPECT SUBMIT)* Caregivers deserve real support... [full closing] ... Please be on the lookout for a call or text with next steps. I'm submitting your request now.
- **Aubrey:** *(Ticket Confirmation)* Your ticket number is [ticket_id]. Is there anything else I can help you with today?
- **Tester:** No.
- **Aubrey:** Thank you for calling Keyline Home Care. Have a great day, Diane!

**Pass criteria**
- Greeting uses caller name from CRM ("Hi Diane, welcome back")
- Confirms name once, doesn't re-ask from scratch
- Confirms email from CRM, doesn't re-ask from scratch
- Phone still asked (not in CRM)
- City/state still asked (not in CRM)
- Otherwise flow proceeds identically to IN-01

**Must not**
- Ask "May I have your first and last name?" when CRM has it
- Speak the literal "{{caller_name}}" template
- Re-confirm the name multiple times

---

## IN-07 | Caller Asks Question Mid-Intake

**Caller persona**
- New caller, no CRM data
- Name: Tom Wilson, phone 555-900-1000, email tom@example.com, Cleveland Ohio
- Caring for his elderly aunt
- Asks an FAQ-style question mid-flow ("How much do caregivers get paid?")

**Objective**
Verify the agent doesn't fabricate pay specifics, defers gracefully, and resumes intake.

**Dialog (key turns)**
- ... [Steps 1-7 collected normally] ...
- **Aubrey:** Does the patient have Medicaid?
- **Tester:** Yes. Wait — quick question, how much do caregivers get paid?
- **Aubrey:** I don't have specific pay rates handy — that depends on your state and the patient's care level. Our Eligibility Specialist will walk through that with you. *(or routes to GLOBAL FAQ HANDLER which uses the KB)* For now, let me finish collecting the info so we can get back to you quickly. Is the patient currently receiving home care services?
- **Tester:** No.
- *(continues through remaining questions)*
- **Aubrey:** *(PROSPECT SUBMIT → ticket → close)*

**Pass criteria**
- Agent does NOT fabricate specific pay rates
- Defers the question gracefully (Eligibility Specialist will walk through it OR FAQ KB answers from Article 12)
- Resumes intake without re-asking previously answered questions
- Continues from where the flow left off (next pending question)

**Must not**
- Make up specific dollar amounts or hourly rates
- Lose place in the intake flow — must continue from the next pending question
- Re-ask Medicaid status (already answered)

---

## Coverage Summary

| Case | Medicaid | DOB | Conditions | CRM | Tests |
|------|----------|-----|------------|-----|-------|
| IN-01 | Yes | Don't have | Dementia + bathing | None | Standard happy path |
| IN-02 | No | — | Alzheimer's + bathing | None | §7 flow continues regardless of Medicaid |
| IN-03 | Yes | Provided | Autism + dressing | None | DOB collection + IDD/autism branch |
| IN-04 | Yes | 1965 | Dementia + bathing/dressing | None | Switching from another provider (currently paid) |
| IN-05 | — | — | — | None | Distress escalation (global) |
| IN-06 | Yes | Provided | Standard | name + email | CRM-injected name + email confirmed |
| IN-07 | Yes | — | Standard | None | FAQ question mid-intake (no fabrication) |

## Universal Guardrails (must pass in every test)

1. **All 16 fields collected** — none skipped
2. **One question per turn** — never combined
3. **Phone confirmed** with 3-3-4 digit grouping per global Verification rule
4. **Email confirmed** per global Verification rule (common domains spoken naturally)
5. **Continue regardless of Medicaid answer** — Yes or No, intake continues
6. **DOB optional** — "no problem" if caller doesn't have it
7. **Closing message verbatim** — "Caregivers deserve real support... one business day or sooner... Please be on the lookout for a call or text with next steps."
8. **No live transfer** — call ends with CLOSE CALL, the team contacts the caller later
9. **Ticket number read back** before "Is there anything else?"
10. **"Is there anything else?" delivered** before closing the call (per global Core Rules)
11. **No fabrication** — pay rates, eligibility specifics, contract details deferred to the team
12. **Closing line** — "Thank you for calling Keyline Home Care. Have a great day, [name]!"

**Out of scope for this file** (covered in shared global-flow tests): fatality escalation, human-request transfer, FAQ interruption (briefly tested in IN-07), topic-change mid-flow.
