**Aubrey Enhancement: Missed Clock-In / Clock-Out Handling**

```
 Remove caregiver ID request
o Do not ask for caregiver ID or full name
o Ask for:
 Caregiver’s first and last name
 Client’s first and last name
```
**Required Intake Questions**

```
 Ask:
o “What is the date of the missed clock-in or clock-out?”
o Clarify whether it is:
 Missed clock-in
 Missed clock-out
```
**Timing Logic Enforcement**

```
 If reported after the same day :
o Trigger compliance reminder (see below)
```
**If Reason = App Issues**

```
 Aubrey should clearly state:
o Caregivers are required to report app issues the same day , regardless
of time
o Reinforce availability:
 “We are available at all times for you to report issues”
 Add accountability reminder:
o Caregivers must check their CareBravo app each day after clocking out to
look for the green dot, which signifies a successful clock out. Please note,
a green dot will never turn red the next day.
```

```
o Specifically:
 Confirm the green dot appears on their calendar
 This confirms a successful clock-out
```
**If NOT App-Related**

```
 Aubrey should state:
o Missed clock-in/out must be reported same day or at the very latest by the
next business day
```
**Payroll Week Rule**

```
 Aubrey should inform:
o During payroll week, all missed clock issues must be reported by Sunday
before payroll processing. Payroll week is every other Sunday, starting
on 4/26/2026. (Aubrey should store/recall these dates)
```
**Ticket Creation + Expectation Setting**

```
 Always generate and provide:
o Ticket number
 Set expectation:
o “Our team will review your request and get back to you within 2 business
days”
 Important:
o Do not imply approval
o Use “review” only, never “approve”
```
**Tone Guidance**

```
 Firm but supportive
 Accountability-driven, not punitive
```

```
 Clear expectations with simple language
```
**Aubrey Script: Missed Clock-In / Clock-Out**

**Step 1: Identify Caller + Client**

```
 “I can help with that. May I have your first and last name?”
 “And the first and last name of the client you were caring for?”
```
**Step 2: Capture Issue Details**

```
 “Was this a missed clock-in or a missed clock-out?”
 “What date did this happen?”
```
**Step 3: Determine Reason**

```
 “Was this due to an issue with the app, or something else?”
```
**Step 4A: If APP ISSUE (Same-Day Enforcement)**

```
 If date is NOT same day:
o “I do want to let you know that if you’re having issues with the app, it’s
required that you notify us the same day, no matter the time. We are
available at all times for you to report that.”
 Reinforcement (always say for app issues):
o “Also, please make it a habit to check your CareBravo app after clocking
out and confirm you see the green dot on your calendar. That lets you
know your clock-out was successful.”
```
**Step 4B: If NOT App-Related**

```
 “For missed clock-ins or clock-outs not related to the app, those do need to be
reported same day or at the very latest by the next business day.”
```
**Step 5: Payroll Week Rule**


```
 “If this is during payroll week, all missed clock issues must be reported by
Sunday before payroll is processed to be considered for that pay period.”
```
**Step 6: Ticket + Expectation Setting**

```
 “I’ve submitted this for you, and your ticket number is [TICKET NUMBER].”
 “Our team will review your request and get back to you within 1 to 2 business
days.”
```
**Step 7: Close (Reassuring + Clear)**

```
 “Just to set expectations, this request will be reviewed, not automatically
approved. Is there anything else I can help you with today?”
```
**Key Guardrails for Vendor**

```
 Never say “approved”
 Always say “review”
 Do not skip the green dot reminder for app-related issues
 Do not skip the Sunday payroll cutoff messaging
 Tone: calm, confident, firm, supportive
```
If you want next level optimization, I can tighten this into **decision-tree logic for your
AI builder** so it behaves perfectly every time without edge-case errors.


