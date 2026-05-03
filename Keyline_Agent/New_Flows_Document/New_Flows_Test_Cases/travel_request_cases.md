# Travel Request — AI Test Cases

Test scenarios for Aubrey's Travel Request flow, structured for automated AI simulation.

**Source spec:** `../travel_request.md`
**Flow path (eligible):** `OPENING` → `APP OFFER - TRAVEL` → `TRAVEL REQUEST` → `Create Ticket` → `Ticket Confirmation` → `Close Call`
**Flow path (denied):** `OPENING` → `TRAVEL DENY` → `Close Call`
**Urgency threshold:** less than 5 days from today

---

## TR-A | Over 30 Days — Hard Exit

**Caller persona**
- New caller, no CRM data
- Name: Maria Johnson
- Travel: ~60 days from today
- Polite, brief

**Objective**
Agent denies the request, sends the link, exits cleanly. No travel details collected. No submission confirmation given.

**Dialog**
- **Aubrey:** Of course, I can help with your travel request. May I have your first and last name?
- **Tester:** Maria Johnson.
- **Aubrey:** Is your travel more than 30 days from today?
- **Tester:** Yes, my travel is in two months.
- **Aubrey:** Travel requests can't be submitted more than 30 days in advance. Please use the link I'm sending or give us a call when you are within 10 days of your travel date so we can process it for you.
- **Aubrey:** Is there anything else I can help you with today?
- **Tester:** No, thanks.
- **Aubrey:** [warm close, e.g., "Take care, Maria."]

**Pass criteria**
- 30-day qualification asked before any other field
- Uses phrase "more than 30 days in advance" and references the 10-day window
- `send_app_link` tool fires (or message confirms link sent)
- Routes to TRAVEL DENY → CLOSE CALL

**Must not**
- Ask for address, dates, or care coverage
- Deliver Step 6 language ("Keyline has received...", "Safe travels...")
- Mention international travel as a denial reason
- Ask permission before sending the link
- Trigger Create Ticket

---

## TR-B | Standard Happy Path — Traveling With Patient — Link Not Previously Sent

**Caller persona**
- New caller, no CRM data
- Name: Daniel Reyes
- Travel: 14 days from today, return 21 days from today
- Patient travels with caregiver
- Cooperative, single-field answers

**Objective**
Most common eligible path. Standard link script fires, address collected structured, care coverage suppressed (patient is traveling with caregiver), submission confirmation delivered with ticket number.

**Dialog**
- **Aubrey:** Of course, I can help with your travel request. May I have your first and last name?
- **Tester:** Daniel Reyes.
- **Aubrey:** Is your travel more than 30 days from today?
- **Tester:** No, it's in two weeks.
- **Aubrey:** I'll go ahead and take care of this for you now, and I'm also going to send the link your way so you have it for future requests. It's faster if you ever need this again.
- **Aubrey:** What is your departure date?
- **Tester:** May twelfth.
- **Aubrey:** Can you provide the street address of where you'll be staying?
- **Tester:** 245 Pine Road.
- **Aubrey:** And what city?
- **Tester:** Asheville.
- **Aubrey:** And what state?
- **Tester:** North Carolina.
- **Aubrey:** What is your return date?
- **Tester:** May nineteenth.
- **Aubrey:** Will you be traveling with the patient you care for?
- **Tester:** Yes, she's coming with me.
- **Aubrey:** Let me submit that for you.
- **Aubrey:** I've submitted this for you, and your ticket number is [ticket_id]. Keyline has received your travel request and will review it. Please note your travel request will need to be approved by the state. You should receive a response within 3 business days. Safe travels, and thank you for being a part of the Keyline Home Care family. Is there anything else I can help you with today?
- **Tester:** No, that's all.
- **Aubrey:** [warm close]

**Pass criteria**
- Standard link script fires (not the "we've already sent you" variant)
- Address collected as 3 separate questions: street, city, state
- Departure and return dates both asked
- Care coverage question asked: "Will you be traveling with the patient you care for?"
- Care coverage sub-flow suppressed (no name/relationship/phone for backup caregiver)
- Ticket number read back from `ticket_id` variable
- Step 6 phrases delivered verbatim: "approved by the state", "3 business days", "Safe travels, and thank you for being a part of the Keyline Home Care family"

**Must not**
- Ask permission to send the link
- Combine address into one question
- Fire urgency disclaimer (travel >5 days away)
- Ask for backup caregiver details
- Skip the ticket number readback
- Repeat the link statement after Step 3

---

## TR-C | Within 30 Days — Not Urgent — Not Traveling With Patient — Link Previously Sent

**Caller persona**
- Returning caller, name on file but no CRM trigger
- Name: Maria Johnson
- Travel: 14 days from today, return 21 days from today
- Patient does NOT travel with caregiver — backup caregiver is sister Sandra

**Objective**
Verify the alternate link script ("we've already sent you") fires, full care coverage sub-flow runs, all 3 backup-caregiver fields collected.

**Dialog**
- **Aubrey:** Of course, I can help with your travel request. May I have your first and last name?
- **Tester:** Maria Johnson.
- **Aubrey:** Is your travel more than 30 days from today?
- **Tester:** No, I'm leaving in two weeks.
- **Aubrey:** It looks like we've already sent you the link. I'll send it again. Using the link will make your request process faster.
- **Aubrey:** What is your departure date?
- **Tester:** May twelfth.
- **Aubrey:** Can you provide the street address of where you'll be staying?
- **Tester:** 123 Maple Street.
- **Aubrey:** And what city?
- **Tester:** Phoenix.
- **Aubrey:** And what state?
- **Tester:** Arizona.
- **Aubrey:** What is your return date?
- **Tester:** May nineteenth.
- **Aubrey:** Will you be traveling with the patient you care for?
- **Tester:** No, I'll be traveling alone.
- **Aubrey:** Who will be caring for the patient while you are away?
- **Tester:** My sister Sandra.
- **Aubrey:** Please provide her first and last name.
- **Tester:** Sandra Johnson.
- **Aubrey:** And her relationship to the patient?
- **Tester:** Sister.
- **Aubrey:** And her phone number?
- **Tester:** 555-234-5678.
- **Aubrey:** Let me submit that for you.
- **Aubrey:** I've submitted this for you, and your ticket number is [ticket_id]. Keyline has received your travel request and will review it. Please note your travel request will need to be approved by the state. You should receive a response within 3 business days. Safe travels, and thank you for being a part of the Keyline Home Care family. Is there anything else I can help you with today?
- **Tester:** No.
- **Aubrey:** [warm close]

**Pass criteria**
- Alternate "we've already sent you" link script fires (not standard variant)
- All 3 backup caregiver fields collected: name, relationship, phone
- Phone read back digit-by-digit grouped 3-3-4 in any confirmation
- Ticket number read back

**Must not**
- Use the standard link script ("I'll go ahead and take care of this for you now...")
- Skip any of the 3 backup caregiver fields
- Combine relationship and name into one question
- Fire urgency disclaimer

---

## TR-D | Urgent Travel (Less Than 5 Days) — Traveling With Patient

**Caller persona**
- New caller, no CRM data
- Name: James Carter
- Travel: 2 days from today, return 9 days from today
- Patient travels with caregiver

**Objective**
Verify urgency disclaimer fires when travel is <5 days away. Care coverage suppressed.

**Dialog**
- **Aubrey:** Of course, I can help with your travel request. May I have your first and last name?
- **Tester:** James Carter.
- **Aubrey:** Is your travel more than 30 days from today?
- **Tester:** No, I'm leaving in two days.
- **Aubrey:** I'll go ahead and take care of this for you now, and I'm also going to send the link your way so you have it for future requests. It's faster if you ever need this again.
- **Aubrey:** What is your departure date?
- **Tester:** [date 2 days from today]
- **Aubrey:** Since your travel is less than 5 days away, we'll do our best to review it quickly, but approval isn't guaranteed as it also requires state review.
- **Aubrey:** Can you provide the street address of where you'll be staying?
- **Tester:** 456 Oak Avenue.
- **Aubrey:** And what city?
- **Tester:** Las Vegas.
- **Aubrey:** And what state?
- **Tester:** Nevada.
- **Aubrey:** What is your return date?
- **Tester:** [date 9 days from today]
- **Aubrey:** Will you be traveling with the patient you care for?
- **Tester:** Yes, the patient is coming with me.
- **Aubrey:** Let me submit that for you.
- **Aubrey:** I've submitted this for you, and your ticket number is [ticket_id]. Keyline has received your travel request and will review it. Please note your travel request will need to be approved by the state. You should receive a response within 3 business days. Safe travels, and thank you for being a part of the Keyline Home Care family. Is there anything else I can help you with today?
- **Tester:** No.
- **Aubrey:** [warm close]

**Pass criteria**
- Urgency disclaimer fires immediately after departure date is given
- Exact phrase: "less than 5 days away", "approval isn't guaranteed", "state review"
- Flow continues after disclaimer (does NOT end the call)
- Care coverage sub-flow suppressed (patient travels with caregiver)
- Submission still completes — disclaimer is informational only

**Must not**
- Stop or end the call after the urgency disclaimer
- Suppress submission confirmation (request is still submitted)
- Ask for backup caregiver details
- Refuse the request based on tight timing

---

## TR-E | Distress Escalation Mid-Travel

**Caller persona**
- New caller, no CRM data
- Name: Linda Hayes
- Starts a travel request but breaks down mid-flow

**Objective**
Verify the GLOBAL - DISTRESS node fires from inside TRAVEL REQUEST and routes to live transfer. Travel intake is abandoned.

**Dialog**
- **Aubrey:** Of course, I can help with your travel request. May I have your first and last name?
- **Tester:** Linda Hayes.
- **Aubrey:** Is your travel more than 30 days from today?
- **Tester:** No, it's in a couple weeks.
- **Aubrey:** I'll go ahead and take care of this for you now, and I'm also going to send the link your way so you have it for future requests. It's faster if you ever need this again.
- **Aubrey:** What is your departure date?
- **Tester:** I'm sorry, I just — I can't deal with this right now, I'm really overwhelmed.
- **Aubrey:** I'm so sorry you're going through this. I want to make sure you get the right support right away.
- **Aubrey:** I'm going to connect you with someone from our team now. Please hold.
- **[Live transfer to Care Team]**

**Pass criteria**
- GLOBAL - DISTRESS triggers on emotional distress signal
- Empathetic acknowledgment delivered before transfer
- Live transfer to Care Team executes (cold transfer)
- Travel intake is fully abandoned — no further data collection

**Must not**
- Continue collecting travel details after distress is detected
- Ask intake questions to "finish" what was started
- Try to resolve the issue itself
- Fire Create Ticket for travel
- Confuse this for fatality (fatality is callback-only, no live transfer)

---

## TR-F | Returning Caller — CRM Name Pre-Filled

**Caller persona**
- Returning caller
- CRM injected: `caller_name = "Sarah Mills"`, `is_returning_caller = "true"`
- Travel: 21 days from today, return 28 days from today
- Patient travels with caregiver

**Objective**
Verify the agent confirms the pre-filled name instead of asking again, and the flow proceeds normally.

**Dialog**
- **Aubrey:** Hi Sarah, welcome back. How can I support you today?
- **Tester:** I need to submit a travel request.
- **Aubrey:** Of course, I can help with your travel request. Just to confirm — that's Sarah Mills, right?
- **Tester:** Yes, that's me.
- **Aubrey:** Is your travel more than 30 days from today?
- **Tester:** No, three weeks from now.
- **Aubrey:** I'll go ahead and take care of this for you now, and I'm also going to send the link your way so you have it for future requests. It's faster if you ever need this again.
- **Aubrey:** What is your departure date?
- **Tester:** [date 21 days from today]
- **Aubrey:** Can you provide the street address of where you'll be staying?
- **Tester:** 88 Elm Court.
- **Aubrey:** And what city?
- **Tester:** Tampa.
- **Aubrey:** And what state?
- **Tester:** Florida.
- **Aubrey:** What is your return date?
- **Tester:** [date 28 days from today]
- **Aubrey:** Will you be traveling with the patient you care for?
- **Tester:** Yes.
- **Aubrey:** Let me submit that for you.
- **Aubrey:** I've submitted this for you, and your ticket number is [ticket_id]. Keyline has received your travel request and will review it. Please note your travel request will need to be approved by the state. You should receive a response within 3 business days. Safe travels, and thank you for being a part of the Keyline Home Care family. Is there anything else I can help you with today?
- **Tester:** No.
- **Aubrey:** [warm close]

**Pass criteria**
- Agent greeting uses caller name from CRM ("Hi Sarah, welcome back")
- Confirms name once instead of asking fresh
- Does not ask name again later in the flow
- Flow proceeds identically to TR-B otherwise

**Must not**
- Ask "May I have your first and last name?" when CRM has it
- Ask for caller phone or email (TRAVEL REQUEST does not collect those)
- Ask for caller state (explicitly suppressed in this flow)
- Re-ask the name if caller corrects pronunciation only

---

## Coverage Summary

| Case | 30-Day | Urgency | Link Variant | Patient Travels With | Returning Caller | Tests |
|------|--------|---------|--------------|----------------------|------------------|-------|
| TR-A | >30 (deny) | n/a | sent on exit | n/a | no | Hard-exit guardrails |
| TR-B | within | not urgent | standard | yes | no | Standard happy path |
| TR-C | within | not urgent | previously sent | no | no | Backup caregiver sub-flow |
| TR-D | within | <5 days | standard | yes | no | Urgency disclaimer |
| TR-E | within | n/a | n/a | n/a | no | Distress escalation (global) |
| TR-F | within | not urgent | standard | yes | yes | CRM-injected name confirmation |

**Out of scope for this file** (covered in shared global-flow tests): fatality escalation, human-request transfer, FAQ interruption, topic-change mid-flow.
