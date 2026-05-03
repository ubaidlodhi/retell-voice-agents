# Incident Report — AI Test Cases

Test scenarios for Aubrey's incident report flow, structured for automated AI simulation.

**Source spec:** `../incident_report.md`
**Flow path:** `OPENING / CAREGIVER MENU` → `APP OFFER - INCIDENT` → `INCIDENT REPORT` → `INCIDENT SUBMIT` → `Create Ticket` → `Ticket Confirmation` → `Close Call`

**Disclosure rules (delivered from INCIDENT SUBMIT based on context):**
- Timeline reminder: only if incident occurred more than 48 hours ago
- Empathy line (always one of three):
  - Still hospitalized → "We wish your loved one a speedy recovery."
  - Discharged and back home → "I'm glad to hear your loved one is back home."
  - Fall with no injuries → "I'm glad to hear no injuries were sustained."
- "I'm submitting your request now." (always closes)

**Mid-flow disclosure (delivered from INCIDENT REPORT Step 5):**
- "Please do not clock in or out while your member is in the hospital. Please call us back once your member has been discharged and is back home receiving care." — only fires when member is still admitted

---

## IR-01 | Fall — No Injuries — Today

**Caller persona**
- New caller, no CRM data
- Name: Maria Johnson
- Phone: 555-100-2000, email: maria@example.com
- Mom fell at home today, no injuries

**Objective**
Most basic fall path. Step 5 entirely skipped (no injuries → no ER/hospital details). Timeline reminder suppressed (today). Empathy = "no injuries". Full address required for falls.

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** My mom had a fall today.
- **Aubrey:** I'm sorry to hear that. I can help you report this. You can also submit incident reports through your caregiver app. Would you like me to send you the link via text?
- **Tester:** No, let's do it on the call.
- **Aubrey:** Okay. May I have your first and last name?
- **Tester:** Maria Johnson.
- **Aubrey:** And your phone number?
- **Tester:** 555-100-2000.
- **Aubrey:** And your email address?
- **Tester:** maria@example.com.
- **Aubrey:** What type of incident is this — was it a fall, an urgent care visit, an emergency room visit, or a hospital admission?
- **Tester:** A fall.
- **Aubrey:** What date did this happen?
- **Tester:** Today.
- **Aubrey:** What time did this happen?
- **Tester:** Around 10 AM.
- **Aubrey:** Where did the fall occur?
- **Tester:** At home.
- **Aubrey:** Where in the home?
- **Tester:** In the bathroom.
- **Aubrey:** How did the fall occur?
- **Tester:** She slipped on a wet floor.
- **Aubrey:** What is the full address of where the incident occurred?
- **Tester:** 123 Maple Street, Phoenix, Arizona.
- **Aubrey:** Were there any injuries?
- **Tester:** No, she's fine.
- **Aubrey:** Can you briefly describe what actually happened?
- **Tester:** She slipped getting out of the shower and landed on her hip, but she's okay.
- **Aubrey:** *(INCIDENT SUBMIT)* I'm glad to hear no injuries were sustained. I'm submitting your request now.
- **Aubrey:** *(Create Ticket)* Just a moment please, this will only take a second.
- **Aubrey:** *(Ticket Confirmation)* I've submitted your request, and your ticket number is [ticket_id]. Thank you for reporting this incident. Our team will review and someone will follow up within one to two business days. Is there anything else I can help you with today?
- **Tester:** No, that's all.
- **Aubrey:** Take care, Maria.

**Pass criteria**
- Caller ID collected first (name → phone → email), one per turn
- Incident type confirmed
- Date and time asked separately
- Fall sub-flow: where in home, how, full address all collected
- "Were there any injuries?" asked
- Step 5 (hospital details) entirely SKIPPED — no injuries
- Description (Step 6) collected
- INCIDENT SUBMIT: timeline reminder SUPPRESSED (today), empathy = "no injuries were sustained"
- Ticket number read back
- "Thank you for reporting this incident" delivered

**Must not**
- Ask about ER, urgent care, hospital name, city, state, admission time, treatments — Step 5 is skipped
- Ask for caller ID after Step 1 (already collected)
- Deliver "speedy recovery" or "back home" empathy
- Deliver the 48-hour timeline reminder (incident is today)
- Deliver the do-not-clock-in instruction (member not hospitalized)

---

## IR-02 | Fall — With Injuries — ER Visit — Yesterday

**Caller persona**
- New caller, no CRM data
- Name: Daniel Reyes, phone 555-200-3000, email daniel@example.com
- Mom fell at home yesterday, had injuries, went to ER, came back home

**Objective**
Fall + injuries → triggers Step 5 ER branch. Hospital details collected. Member discharged. Empathy = "back home". Timeline reminder suppressed (yesterday is within 48 hours).

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** My mom fell yesterday and we had to take her to the ER.
- **Aubrey:** I'm sorry to hear that. I can help you report this. You can also submit incident reports through your caregiver app. Would you like me to send you the link via text?
- **Tester:** No, let's just do it now.
- **Aubrey:** Okay. May I have your first and last name?
- **Tester:** Daniel Reyes.
- **Aubrey:** And your phone number?
- **Tester:** 555-200-3000.
- **Aubrey:** And your email address?
- **Tester:** daniel@example.com.
- **Aubrey:** What type of incident is this — fall, urgent care, ER, or hospital admission?
- **Tester:** It was a fall.
- **Aubrey:** What date did this happen?
- **Tester:** Yesterday.
- **Aubrey:** What time did this happen?
- **Tester:** Around 3 PM.
- **Aubrey:** Where did the fall occur?
- **Tester:** At home.
- **Aubrey:** Where in the home?
- **Tester:** Living room.
- **Aubrey:** How did the fall occur?
- **Tester:** She lost her balance.
- **Aubrey:** What is the full address of where the incident occurred?
- **Tester:** 245 Oak Lane, Tampa, Florida.
- **Aubrey:** Were there any injuries?
- **Tester:** Yes, she hurt her wrist.
- **Aubrey:** Did they go to the emergency room or urgent care?
- **Tester:** ER.
- **Aubrey:** What is the name of the hospital or urgent care facility?
- **Tester:** Tampa General Hospital.
- **Aubrey:** What city?
- **Tester:** Tampa.
- **Aubrey:** What state?
- **Tester:** Florida.
- **Aubrey:** What time were they admitted or seen?
- **Tester:** Around 4 PM.
- **Aubrey:** What was the reason for the admission or visit?
- **Tester:** Suspected wrist fracture.
- **Aubrey:** What treatments are being received?
- **Tester:** They put a cast on and gave her pain medication.
- **Aubrey:** Is your member still admitted, or have they been discharged?
- **Tester:** Discharged. She came home last night.
- **Aubrey:** When did they return home?
- **Tester:** Around 9 PM yesterday.
- **Aubrey:** Can you briefly describe what actually happened?
- **Tester:** She lost her balance walking to the kitchen and fell on her wrist.
- **Aubrey:** *(INCIDENT SUBMIT)* I'm glad to hear your loved one is back home. I'm submitting your request now.
- **Aubrey:** *(Create Ticket)* Just a moment please, this will only take a second.
- **Aubrey:** *(Ticket Confirmation)* I've submitted your request, and your ticket number is [ticket_id]. Thank you for reporting this incident. Our team will review and someone will follow up within one to two business days. Is there anything else I can help you with today?
- **Tester:** No, thanks.
- **Aubrey:** Take care, Daniel.

**Pass criteria**
- Step 5 fires (injuries + ER answer)
- All Step 5 fields collected: facility name, city, state, admission time, reason, treatments, status
- "When did they return home?" follow-up asked because discharged
- Do-not-clock-in instruction NOT delivered (member is home)
- Empathy = "I'm glad to hear your loved one is back home"
- Timeline reminder SUPPRESSED (yesterday is within 48 hours)

**Must not**
- Skip any Step 5 sub-question
- Ask for street address of the ER (city + state only for facilities)
- Deliver the do-not-clock-in instruction (member is home)
- Deliver "speedy recovery" empathy
- Deliver the 48-hour timeline reminder

---

## IR-03 | Hospital Admission — Still Admitted

**Caller persona**
- New caller, no CRM data
- Name: Sarah Kim, phone 555-300-4000, email sarah@example.com
- Member admitted to hospital today, still there

**Objective**
Hospital admission with member still admitted. Triggers do-not-clock-in instruction (delivered ONCE in Step 5). Empathy = "speedy recovery". No fall path.

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** My mom was admitted to the hospital today.
- **Aubrey:** I'm sorry to hear that. I can help you report this. You can also submit incident reports through your caregiver app. Would you like me to send you the link via text?
- **Tester:** No, on the call please.
- **Aubrey:** Okay. May I have your first and last name?
- **Tester:** Sarah Kim.
- **Aubrey:** And your phone number?
- **Tester:** 555-300-4000.
- **Aubrey:** And your email address?
- **Tester:** sarah@example.com.
- **Aubrey:** What type of incident is this — fall, urgent care, ER, or hospital admission?
- **Tester:** Hospital admission.
- **Aubrey:** What date did this happen?
- **Tester:** Today.
- **Aubrey:** What time did this happen?
- **Tester:** This morning, around 8 AM.
- **Aubrey:** What is the name of the hospital?
- **Tester:** St. Mary's Medical Center.
- **Aubrey:** What city?
- **Tester:** Reno.
- **Aubrey:** What state?
- **Tester:** Nevada.
- **Aubrey:** What time were they admitted?
- **Tester:** Around 9 AM.
- **Aubrey:** What was the reason for the admission?
- **Tester:** She had trouble breathing.
- **Aubrey:** What treatments are being received?
- **Tester:** They have her on oxygen and running tests.
- **Aubrey:** Is your member still admitted, or have they been discharged?
- **Tester:** Still admitted.
- **Aubrey:** Please do not clock in or out while your member is in the hospital. Please call us back once your member has been discharged and is back home receiving care.
- **Aubrey:** Can you briefly describe what actually happened?
- **Tester:** She woke up short of breath and we called 911. They admitted her for observation.
- **Aubrey:** *(INCIDENT SUBMIT)* We wish your loved one a speedy recovery. I'm submitting your request now.
- **Aubrey:** *(Create Ticket)* Just a moment please, this will only take a second.
- **Aubrey:** *(Ticket Confirmation)* I've submitted your request, and your ticket number is [ticket_id]. Thank you for reporting this incident. Our team will review and someone will follow up within one to two business days. Is there anything else I can help you with today?
- **Tester:** No, thanks.
- **Aubrey:** Take care, Sarah.

**Pass criteria**
- No fall sub-flow (no "where in the home", no "how", no full address)
- All Step 5 fields collected: hospital name, city, state, admission time, reason, treatments, status
- Do-not-clock-in instruction delivered ONCE after status confirmed
- Empathy = "speedy recovery"
- Timeline reminder SUPPRESSED (today)

**Must not**
- Ask "where in the home" or "how did it occur" (this is not a fall)
- Ask for street address of the hospital (name, city, state only)
- Deliver "back home" empathy (member is still admitted)
- Deliver the do-not-clock-in instruction more than once
- Include the do-not-clock-in instruction inside a summary

---

## IR-04 | Hospital Admission — Discharged and Home

**Caller persona**
- New caller, no CRM data
- Name: James Carter, phone 555-400-5000, email james@example.com
- Father admitted yesterday, discharged this morning, back home

**Objective**
Hospital admission, member already home. Step 5 collects details + asks "When did they return home?". Do-not-clock-in instruction NOT delivered. Empathy = "back home".

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** My dad was admitted to the hospital yesterday but he's home now.
- **Aubrey:** I'm sorry to hear that. I can help you report this. You can also submit incident reports through your caregiver app. Would you like me to send you the link via text?
- **Tester:** No, let's do this now.
- **Aubrey:** Okay. May I have your first and last name?
- **Tester:** James Carter.
- **Aubrey:** And your phone number?
- **Tester:** 555-400-5000.
- **Aubrey:** And your email address?
- **Tester:** james@example.com.
- **Aubrey:** What type of incident is this — fall, urgent care, ER, or hospital admission?
- **Tester:** Hospital admission.
- **Aubrey:** What date did this happen?
- **Tester:** Yesterday.
- **Aubrey:** What time did this happen?
- **Tester:** Around 6 PM.
- **Aubrey:** What is the name of the hospital?
- **Tester:** Mercy General.
- **Aubrey:** What city?
- **Tester:** Sacramento.
- **Aubrey:** What state?
- **Tester:** California.
- **Aubrey:** What time were they admitted?
- **Tester:** Around 7 PM.
- **Aubrey:** What was the reason for the admission?
- **Tester:** Chest pain.
- **Aubrey:** What treatments are being received?
- **Tester:** They ran tests and ruled out a cardiac event. Gave him medication.
- **Aubrey:** Is your member still admitted, or have they been discharged?
- **Tester:** Discharged this morning.
- **Aubrey:** When did they return home?
- **Tester:** Around 11 AM today.
- **Aubrey:** Can you briefly describe what actually happened?
- **Tester:** He had chest pain in the evening so we took him in. They observed him overnight and sent him home this morning.
- **Aubrey:** *(INCIDENT SUBMIT)* I'm glad to hear your loved one is back home. I'm submitting your request now.
- **Aubrey:** *(Create Ticket)* Just a moment please, this will only take a second.
- **Aubrey:** *(Ticket Confirmation)* I've submitted your request, and your ticket number is [ticket_id]. Thank you for reporting this incident. Our team will review and someone will follow up within one to two business days. Is there anything else I can help you with today?
- **Tester:** No, thanks.
- **Aubrey:** Take care, James.

**Pass criteria**
- Step 5 status answer = "Discharged" → follow-up "When did they return home?" asked
- Do-not-clock-in instruction NOT delivered (member is home)
- Empathy = "back home"
- Timeline reminder SUPPRESSED (yesterday)

**Must not**
- Deliver the do-not-clock-in instruction (member is home)
- Skip the "When did they return home?" follow-up
- Deliver "speedy recovery" empathy

---

## IR-05 | Urgent Care Visit — Today

**Caller persona**
- New caller, no CRM data
- Name: Linda Hayes, phone 555-500-6000, email linda@example.com
- Mom went to urgent care today, came home

**Objective**
Urgent care visit (not a fall, not ER, not hospital admission). Step 5 fires for facility details. No fall sub-flow. Empathy = "back home".

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** I had to take my mom to urgent care today.
- **Aubrey:** I'm sorry to hear that. Would you like me to send you the link to submit it through the caregiver app?
- **Tester:** No, on the call please.
- **Aubrey:** Okay. May I have your first and last name?
- **Tester:** Linda Hayes.
- **Aubrey:** And your phone number?
- **Tester:** 555-500-6000.
- **Aubrey:** And your email address?
- **Tester:** linda@example.com.
- **Aubrey:** What type of incident is this — fall, urgent care, ER, or hospital admission?
- **Tester:** Urgent care visit.
- **Aubrey:** What date did this happen?
- **Tester:** Today.
- **Aubrey:** What time did this happen?
- **Tester:** Around 2 PM.
- **Aubrey:** What is the name of the urgent care facility?
- **Tester:** QuickCare Clinic.
- **Aubrey:** What city?
- **Tester:** Austin.
- **Aubrey:** What state?
- **Tester:** Texas.
- **Aubrey:** What time were they seen?
- **Tester:** Around 2:30 PM.
- **Aubrey:** What was the reason for the visit?
- **Tester:** A persistent cough.
- **Aubrey:** What treatments are being received?
- **Tester:** They prescribed antibiotics.
- **Aubrey:** Is your member still admitted, or have they been discharged?
- **Tester:** Discharged. She's home now.
- **Aubrey:** When did they return home?
- **Tester:** About an hour ago.
- **Aubrey:** Can you briefly describe what actually happened?
- **Tester:** She'd been coughing for a few days, getting worse, so I took her in.
- **Aubrey:** *(INCIDENT SUBMIT)* I'm glad to hear your loved one is back home. I'm submitting your request now.
- **Aubrey:** *(Create Ticket)* Just a moment please, this will only take a second.
- **Aubrey:** *(Ticket Confirmation)* I've submitted your request, and your ticket number is [ticket_id]. Thank you for reporting this incident. Our team will review and someone will follow up within one to two business days. Is there anything else I can help you with today?
- **Tester:** No.
- **Aubrey:** Take care, Linda.

**Pass criteria**
- No fall sub-flow (no "where in the home", no "how", no full incident address)
- Step 5 collected: name, city, state, admission/seen time, reason, treatments, status
- Empathy = "back home"

**Must not**
- Ask fall-specific questions (this isn't a fall)
- Ask for street address of urgent care (name, city, state only)

---

## IR-06 | Late Report (>48 Hours) — Timeline Reminder Fires

**Caller persona**
- New caller, no CRM data
- Name: Maria Johnson
- Mom fell 4 days ago at home, no injuries — caller is reporting late

**Objective**
Verify the 48-hour timeline reminder fires when incident occurred more than 48 hours ago.

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** My mom fell about four days ago. I forgot to report it.
- **Aubrey:** I'm sorry to hear that. Would you like me to send the app link to report it there?
- **Tester:** No, let's do it now.
- **Aubrey:** Okay. May I have your first and last name?
- **Tester:** Maria Johnson.
- **Aubrey:** And your phone number?
- **Tester:** 555-100-2000.
- **Aubrey:** And your email address?
- **Tester:** maria@example.com.
- **Aubrey:** What type of incident is this — fall, urgent care, ER, or hospital admission?
- **Tester:** A fall.
- **Aubrey:** What date did this happen?
- **Tester:** April twenty-fifth.
- **Aubrey:** What time did this happen?
- **Tester:** Late afternoon, around 5 PM.
- **Aubrey:** Where did the fall occur?
- **Tester:** At home, in the kitchen.
- **Aubrey:** How did the fall occur?
- **Tester:** She tripped over a rug.
- **Aubrey:** What is the full address of where the incident occurred?
- **Tester:** 123 Maple Street, Phoenix, Arizona.
- **Aubrey:** Were there any injuries?
- **Tester:** No, she was okay.
- **Aubrey:** Can you briefly describe what actually happened?
- **Tester:** She tripped over a rug and landed on her side. She got up on her own and seemed fine.
- **Aubrey:** *(INCIDENT SUBMIT)* For future reference, please report incidents within 24 to 48 hours so we can support you promptly. I'm glad to hear no injuries were sustained. I'm submitting your request now.
- **Aubrey:** *(Create Ticket)* Just a moment please, this will only take a second.
- **Aubrey:** *(Ticket Confirmation)* I've submitted your request, and your ticket number is [ticket_id]. Thank you for reporting this incident. Our team will review and someone will follow up within one to two business days. Is there anything else I can help you with today?
- **Tester:** No, thanks.
- **Aubrey:** Take care, Maria.

**Pass criteria**
- Timeline reminder FIRES — exact phrase: "For future reference, please report incidents within 24 to 48 hours so we can support you promptly."
- Reminder is delivered AFTER description (not at the start of the call)
- Reminder + empathy + submit line all delivered in ONE INCIDENT SUBMIT turn
- Step 5 still skipped (no injuries)

**Must not**
- Deliver the timeline reminder at the start of the call
- Skip the timeline reminder (incident is >48 hours old)
- Deliver the reminder twice

---

## IR-07 | Distress Escalation Mid-Flow

**Caller persona**
- New caller, no CRM data
- Name: Linda Hayes
- Reports a fall, breaks down emotionally mid-flow

**Objective**
Verify GLOBAL - DISTRESS fires from inside INCIDENT REPORT and routes to live transfer. Incident intake is abandoned.

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** My mom fell.
- **Aubrey:** I'm sorry to hear that. Would you like me to send the app link?
- **Tester:** No.
- **Aubrey:** Okay. May I have your first and last name?
- **Tester:** Linda Hayes.
- **Aubrey:** And your phone number?
- **Tester:** I — I can't do this right now. I'm so overwhelmed, I don't know what to do.
- **Aubrey:** *(GLOBAL - DISTRESS)* I'm so sorry you're going through this. I want to make sure you get the right support right away.
- **Aubrey:** I'm going to connect you with someone from our team now. Please hold.
- **[Live transfer to Care Team]**

**Pass criteria**
- GLOBAL - DISTRESS triggers on emotional distress signal
- Empathetic acknowledgment delivered before transfer
- Live transfer to Care Team executes
- Incident intake fully abandoned — no Create Ticket fires for incident

**Must not**
- Continue collecting incident details after distress is detected
- Try to resolve the issue itself
- Fire Create Ticket for incident
- Confuse this for fatality (fatality is callback-only, no live transfer)

---

## IR-08 | Returning Caller — CRM Pre-Filled

**Caller persona**
- Returning caller
- CRM injected: `caller_name = "Maria Johnson"`, `caller_email = "maria@example.com"`, `is_returning_caller = "true"`
- Mom had urgent care visit yesterday, came home

**Objective**
Verify Aubrey confirms CRM-injected fields instead of asking fresh. Phone still asked because not in CRM.

**Dialog**
- **Aubrey:** Hi Maria, welcome back. How can I support you today?
- **Tester:** My mom went to urgent care yesterday.
- **Aubrey:** I'm sorry to hear that. Would you like me to send the link to use the app?
- **Tester:** No, just do it on the call.
- **Aubrey:** Okay. Just to confirm — that's Maria Johnson, right?
- **Tester:** Yes.
- **Aubrey:** And the best phone number to reach you?
- **Tester:** 555-100-2000.
- **Aubrey:** I've got your email as maria@example.com — should I use that?
- **Tester:** Yes.
- **Aubrey:** What type of incident is this — fall, urgent care, ER, or hospital admission?
- **Tester:** Urgent care.
- **Aubrey:** *(continues with Step 3 onward — same as IR-05 from this point)*

**Pass criteria**
- Greeting uses caller name from CRM ("Hi Maria, welcome back")
- Confirms name once (does not re-ask)
- Confirms email from CRM (does not re-ask)
- Phone still asked (not in CRM)
- Flow proceeds normally from Step 2 onward

**Must not**
- Ask "May I have your first and last name?" when CRM has it
- Ask for email fresh when CRM has it
- Speak the literal "{{caller_name}}" template syntax
- Re-confirm the name multiple times

---

## Coverage Summary

| Case | Type | Timing | Outcome | Step 5 Fires? | Disclosures |
|------|------|--------|---------|---------------|-------------|
| IR-01 | Fall | Today | No injuries | No | "no injuries" empathy |
| IR-02 | Fall | Yesterday | Injuries → ER → home | Yes (ER details) | "back home" empathy |
| IR-03 | Hospital | Today | Still admitted | Yes (full) | Don't-clock-in + "speedy recovery" |
| IR-04 | Hospital | Yesterday | Discharged & home | Yes (full + return time) | "back home" empathy |
| IR-05 | Urgent care | Today | Discharged & home | Yes (full + return time) | "back home" empathy |
| IR-06 | Fall | 4 days ago | No injuries | No | Timeline reminder + "no injuries" |
| IR-07 | — | — | — | — | Distress escalation (global) |
| IR-08 | Urgent care | Yesterday | Discharged & home | Yes | CRM-injected name + email confirmation |

## Universal Guardrails (must pass in every test)

1. **Caller ID first** — name → phone → email collected before any incident details. No exceptions.
2. **Incident type classified** — must be one of: fall, urgent care, ER, hospital admission.
3. **Date and time as separate questions** — never combined.
4. **Fall path requires full address**; hospital/ER/urgent-care path uses **name + city + state only** (no street).
5. **Admission time** in Step 5 is separate from incident time in Step 3 — both required.
6. **Don't-clock-in instruction** delivered ONCE if member is still admitted, NEVER if discharged.
7. **Description (Step 6)** is mandatory — no exceptions.
8. **Timeline reminder** fires when incident is more than 48 hours ago, always after description.
9. **Empathy line** — exactly one of three (speedy recovery / back home / no injuries), delivered in INCIDENT SUBMIT.
10. **"Thank you for reporting this incident"** — delivered in Ticket Confirmation, not from INCIDENT REPORT or INCIDENT SUBMIT.
11. **Ticket number** — always provided in the readback.
12. **One question per turn** during collection (Steps 1-6); disclosures may be combined in one INCIDENT SUBMIT turn.

**Out of scope for this file** (covered in shared global-flow tests): fatality escalation, human-request transfer, FAQ interruption, topic-change mid-flow.
