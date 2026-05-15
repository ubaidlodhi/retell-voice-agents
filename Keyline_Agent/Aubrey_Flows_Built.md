# Aubrey — Flows Built

**The bold name is the exact node name** — Ctrl+F it in the Retell flow editor to jump straight to that node.

## Entry & Routing
- **OPENING** *(conversation)* — Greets caller by name if recognized, otherwise generic greeting; routes unknown callers via caller-type question.
- **CAREGIVER - TOPIC MENU** *(conversation)* — Asks "what can I help you with?" and routes to the right flow; skips re-asking if topic already known.
- **OUT OF SCOPE** *(conversation)* — For requests Aubrey can't handle: offers transfer or callback ticket.

## Travel / Mileage
- **TRAVEL REQUEST** *(conversation)* — Collects all travel fields one-per-turn (name, dates, destination, etc.).
- **TRAVEL SUBMIT** *(conversation)* — Says "I'm submitting your request now" and triggers the create-ticket function.
- **TRAVEL DENY** *(conversation)* — Hard-stops requests outside US or more than 30 days out.
- **APP OFFER - TRAVEL** *(conversation)* — Mentions the caregiver app self-serve option before collecting.

## Incident
- **INCIDENT REPORT** *(conversation)* — Collects incident details one-per-turn (client, date, what happened, witnesses).
- **INCIDENT SUBMIT** *(conversation)* — Delivers wrap-up disclosures + submit acknowledgment in one breath.
- **APP OFFER - INCIDENT** *(conversation)* — Empathy acknowledgment + offers app-link as self-serve alternative.

## Time / Clock-Out
- **MISSED CLOCK OUT** *(conversation)* — Collects 5 fields for the missed clock-in/out report.
- **MCO SUBMIT** *(conversation)* — Delivers disclosures + submit acknowledgment together.

## Pay & Payroll
- **PAY STUBS - W2** *(conversation)* — Directs caller to Square Payroll self-service; no ticket created.
- **PAY STUBS - SFC** *(conversation)* — Collects name + patient + email; delivers stubs in 1–2 business days.
- **APP OFFER - PAY STUBS** *(conversation)* — Offers app link, then branches to W2 vs SFC if declined.
- **INCOME LETTER** *(conversation)* — Collects name + patient + email and submits an income-letter ticket.
- **DIRECT DEPOSIT - SECURITY BLOCK** *(conversation)* — Refuses bank info by phone; offers app link instead.
- **DD HOLD** *(conversation)* — Diagnoses cause of direct-deposit hold and routes appropriately.
- **PAY ISSUE - TRANSFER** *(conversation)* — Empathy + immediate transfer for pay discrepancies, no intake.

## Personal Info
- **ADDRESS / CONTACT UPDATE** *(conversation)* — Collects new address, phone, email and submits a contact-update ticket.

## Health & Care Services
- **HEALTH COACH TRANSFER** *(conversation)* — Asks for coach's name then transfers.
- **CANCEL NURSE VISIT** *(conversation)* — Collects callback info + nurse name, submits cancellation ticket.
- **CASE MANAGER** *(conversation)* — Outside-agency case-manager entry: collects client + caregiver names, then triages.

## Prospect / Intake
- **PROSPECT INTAKE** *(conversation)* — Collects all 16 lead-qualification fields one-per-turn.
- **PROSPECT SUBMIT** *(conversation)* — Delivers closing message + creates the prospect ticket in one continuous response.
- **PROSPECT STATUS CHECK** *(conversation)* — Sends app link or offers care-team transfer for status questions.

## Internal
- **TEAM MEMBER REQUEST** *(conversation)* — Caller asks for someone by name: attempts first-touch resolution before transferring.

## Tickets & SMS
- **Create Ticket** *(function)* — POSTs to n8n webhook and returns `ticket_id`.
- **Ticket Confirmation** *(conversation)* — Reads ticket number once on entry; asks if anything else.
- **TICKET STATUS** *(conversation)* — Looks up caller's tickets from `{{caller_tickets}}` and answers status questions.
- **Send App Link** *(function)* — POSTs to n8n SMS webhook to send the app link.
- **Send Ticket SMS** *(function)* — POSTs to n8n SMS webhook to send ticket details.
- **SMS APP LINK** *(conversation)* — Confirms link was sent, asks if anything else needed.

## Transfers
- **TRANSFER - CASE SUPPORT** *(transfer_call)* — Transfer to case-support team (active members).
- **TRANSFER - CARE TEAM** *(transfer_call)* — Transfer to care-team queue (new/switching).
- **TRANSFER - ALYSSA (SCREENING)** *(transfer_call)* — Transfer to Alyssa for phone screening + nurse assessments.
- **TRANSFER - PAYROLL TEAM** *(transfer_call)* — Transfer for pay-discrepancy resolution.
- **TRANSFER - HEALTH COACH** *(transfer_call)* — Transfer to caller's named health coach.
- **TRANSFER - ROCHELE (ONBOARDING)** *(transfer_call)* — Transfer to onboarding team / Prospect App help.
- **TRANSFER - KALIL (SEMI-ANNUAL)** *(transfer_call)* — Transfer for semi-annual visit questions.
- **Transfer Call** *(transfer_call)* — Catch-all transfer fallback.

## Global Handlers (cross-cutting interrupts)
- **GLOBAL - DISTRESS** *(conversation)* — Acute crisis: empathy + immediate human connect.
- **GLOBAL - FATALITY** *(conversation)* — Condolences only; flags for support team, NO live transfer.
- **GLOBAL - FAQ HANDLER** *(conversation)* — Answers in-scope FAQs from KB in 1–2 sentences.
- **GLOBAL - TOPIC CHANGE** *(conversation)* — Caller switches topics mid-flow: drops partial data, re-routes cleanly.
- **GLOBAL - HUMAN REQUEST** *(conversation)* — Caller asks for a human: immediate transfer, no gatekeeping.

## Closing
- **CLOSE CALL** *(conversation)* — Context-aware closing with pending-message check.
- **END CALL** *(end)* — Terminates the call.

---

**Node types:** *conversation* = talks/collects · *function* = calls an n8n tool · *transfer_call* = routes to a human · *end* = hangs up.
**Validator status:** PASS — 0 errors, 0 warnings. **Tool URLs:** all 3 wired to live n8n webhooks.
