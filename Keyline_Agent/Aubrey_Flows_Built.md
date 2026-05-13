# Aubrey — Flows Built

Quick checklist of what's wired in `Aubrey_Agent.json` (48 nodes, 3 tools).

## Entry & Routing
- [x] **Opening** — Greets caller by name if recognized, otherwise generic greeting; routes unknown callers to screening.
- [x] **Caregiver topic menu** — Asks "what can I help you with?" and routes to the right flow; skips re-asking if topic already known.
- [x] **Out of scope** — For requests Aubrey can't handle: offers transfer or callback ticket.

## Travel / Mileage
- [x] **Travel request** — Collects all travel fields one-per-turn (name, dates, destination, etc.).
- [x] **Travel submit** — Says "I'm submitting your request now" and triggers the create-ticket function.
- [x] **Travel deny** — Hard-stops requests outside US or more than 30 days out.
- [x] **App offer — travel** — Mentions the caregiver app self-serve option before collecting.

## Incident
- [x] **Incident report** — Collects incident details one-per-turn (client, date, what happened, witnesses).
- [x] **Incident submit** — Delivers wrap-up disclosures + submit acknowledgment in one breath.
- [x] **App offer — incident** — Empathy acknowledgment + offers app-link as self-serve alternative.

## Time / Clock-Out
- [x] **Missed clock-out** — Collects 5 fields for the missed clock-in/out report.
- [x] **MCO submit** — Delivers disclosures + submit acknowledgment together.

## Pay & Payroll
- [x] **Pay stubs — W2** — Directs caller to Square Payroll self-service; no ticket created.
- [x] **Pay stubs — SFC** — Collects name + patient + email; delivers stubs in 1–2 business days.
- [x] **App offer — pay stubs** — Offers app link, then branches to W2 vs SFC if declined.
- [x] **Income letter** — Collects name + patient + email and submits an income-letter ticket.
- [x] **DD security block** — Refuses bank info by phone; offers app link instead.
- [x] **DD hold** — Diagnoses cause of direct-deposit hold and routes appropriately.
- [x] **Pay issue → Payroll** — Empathy + immediate transfer for pay discrepancies, no intake.

## Personal Info
- [x] **Address / contact update** — Collects new address, phone, email and submits a contact-update ticket.

## Health & Care Services
- [x] **Health coach transfer** — Asks for coach's name then transfers.
- [x] **Cancel nurse visit** — Collects callback info + nurse name, submits cancellation ticket.
- [x] **Case manager** — Outside-agency case-manager entry: collects client + caregiver names, then triages.

## Prospect / Intake
- [x] **Prospect intake** — Collects all 16 lead-qualification fields one-per-turn.
- [x] **Prospect submit** — Delivers closing message + creates the prospect ticket in one continuous response.
- [x] **Prospect status check** — Sends app link or offers care-team transfer for status questions.

## Internal
- [x] **Team member request** — Caller asks for someone by name: attempts first-touch resolution before transferring.

## Tickets & SMS
- [x] **Create ticket** — Function node; POSTs to n8n webhook and returns `ticket_id`.
- [x] **Ticket confirmation** — Reads ticket number once on entry; asks if anything else.
- [x] **Ticket status** — Looks up caller's tickets from `{{caller_tickets}}` and answers status questions.
- [x] **Send app link** — Function node; POSTs to n8n SMS webhook to send the app link.
- [x] **Send ticket SMS** — Function node; POSTs to n8n SMS webhook to send ticket details.
- [x] **SMS app link** — Confirms link was sent, asks if anything else needed.

## Transfers
- [x] **Case support** — Generic transfer to case-support team.
- [x] **Care team** — Generic transfer to care-team queue.
- [x] **Alyssa (screening)** — Transfer to Alyssa for phone screening + nurse assessments.
- [x] **Payroll team** — Transfer for pay-discrepancy resolution.
- [x] **Health coach** — Transfer to caller's named health coach.
- [x] **Rochele (onboarding)** — Transfer to onboarding team.
- [x] **Kalil (semi-annual)** — Transfer for semi-annual visit questions.
- [x] **Generic transfer fallback** — Catch-all transfer node.

## Global Handlers (cross-cutting interrupts)
- [x] **Distress** — Acute crisis: empathy + immediate human connect.
- [x] **Fatality** — Condolences only; flags for support team, NO live transfer.
- [x] **FAQ handler** — Answers in-scope FAQs from KB in 1–2 sentences.
- [x] **Topic change** — Caller switches topics mid-flow: drops partial data, re-routes cleanly.
- [x] **Human request** — Caller asks for a human: immediate transfer, no gatekeeping.

## Closing
- [x] **Close call** — Context-aware closing with pending-message check.
- [x] **End call** — Terminates the call.

---

**Validator status:** PASS — 0 errors, 0 warnings.
**Tool URLs:** all 3 tools wired to live n8n webhooks (no placeholders).
