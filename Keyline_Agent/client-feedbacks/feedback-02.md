# Feedback-02 — Routing Fixes (Bernae, 2026-05-30)

> Client message: current clients/active caregivers + prospects (new vs. status-check) are getting transferred to the wrong department. New canonical routing below.

## Canonical routing (per Bernae)

| Caller type | Destination | Number |
|---|---|---|
| Current client or active caregiver | **Case Support** | 678-785-7010 |
| New prospect (looking to enroll) | Collect info → live-transfer to **Eligibility Specialist Dept** after ticket | 678-785-7013 |
| Referred applicant / caregiver — not yet started service, calling for status update | **Care Team** | **470-868-4776** ← new |

---

## Todo list

### A. Phone number corrections (agent JSON)

- [ ] **A1.** Rename node `TRANSFER - CARE TEAM` (`id: node-transfer-care-team`) → repoint number from `+16787857013` to **`+14708684776`** (Care Team's real number per Bernae). Update the `instruction.text` to mention Care Team explicitly.
- [ ] **A2.** Add new transfer node **`TRANSFER - ELIGIBILITY SPECIALIST`** with number `+16787857013`. Static message: *"Let me connect you with our Eligibility Specialist team to complete your enrollment. Please hold."*
  - On-failure edge → `node-close-call`.
- [ ] **A3.** Decide on `TRANSFER - ROCHELE (ONBOARDING)` — currently also uses `+16787857013`. Either (a) keep as a separate node and tell client we're now sending both prospect-app-issue + post-intake calls to the same Eligibility number, or (b) collapse Rochele into the new Eligibility Specialist node. **Open question for client.**
- [ ] **A4.** `TRANSFER - ALYSSA (SCREENING)` stays at `+14702438993` — that's for nurse phone-screenings/assessments, separate from Bernae's three buckets.

### B. Flow change — new prospect intake gets a live transfer after ticket

Current behavior (verified in `node-1776962211546` Ticket Confirmation, the `call_type == "prospect"` branch):
> "Do NOT transfer the call. Per the spec, the team will contact the caller later by call or text."

New behavior per Bernae: collect info → create ticket → **attempt live transfer to Eligibility Specialist**. Only fall back to "they'll follow up" if the transfer fails.

- [ ] **B1.** Edit `Ticket Confirmation` node prompt — for `call_type == "prospect"`:
  - Read ticket number + SMS line (keep as-is)
  - After repeat offer, **replace** the "they'll contact you" closer with: *"Now, let me connect you with our Eligibility Specialist team to get started. Please hold."*
  - Then route to the new `TRANSFER - ELIGIBILITY SPECIALIST` node.
- [ ] **B2.** Add a new edge from Ticket Confirmation → `TRANSFER - ELIGIBILITY SPECIALIST` gated on `call_type == "prospect"`. (Fires automatically — no caller answer needed.)
- [ ] **B3.** Update `PROSPECT SUBMIT` (`node-prospect-submit`) Part A wording — current line *"You'll receive an update on your eligibility within one business day or sooner"* should be softened to leave room for the live transfer that's coming. Suggestion: *"We'll start reviewing your case right away — and I'll try to connect you with our Eligibility team in just a moment to get you started."*

### C. Routing-decision tightening (OPENING + status check)

Per Bernae, Aubrey should *verify* caller type before transferring. The OPENING node already asks the caregiver/client/case-manager question for unrecognized callers, but the prospect distinction needs a clearer split.

- [ ] **C1.** Edit `OPENING` (`start-node-aubrey-opening`) prompt — under the existing PROSPECT EXCEPTION block, add a second clarifier:
  > For PROSPECTS: first verify whether they are (a) **looking to enroll** (new applicant) → route to PROSPECT INTAKE, or (b) **already started the referral process but not yet started service, calling for status** → route to PROSPECT STATUS CHECK.
- [ ] **C2.** `PROSPECT STATUS CHECK` (`node-prospect-status-check`) already routes "speak with someone" → `node-transfer-care-team`. After fix A1 this will go to the correct Care Team number (470-868-4776) — verify in test call.
- [ ] **C3.** Active-caregiver / current-client → Case Support is already correct via the existing topic flows (most create tickets; explicit transfers route to `node-transfer-case-support` = 7010). No change needed beyond verifying via test.

### D. Reference + memory updates

- [ ] **D1.** Update memory `reference_keyline_monday_columns.md` (or create a new `reference_keyline_transfer_numbers.md`) with the canonical 7010 / 7013 / 470-868-4776 mapping so future sessions don't repeat the routing mix-up.
- [ ] **D2.** Save this feedback-02.md alongside feedback-01.md for client handoff.

---

## Test additions (append to test-plan-2026-05-23.md)

- **Test 10 — Active caregiver requests live person** → must transfer to **678-785-7010** (Case Support). Verify caller-ID phone matches the dialed transfer.
- **Test 11 — New prospect intake (full)** → after ticket creation, Aubrey says *"connecting you with Eligibility"* and transfers to **678-785-7013**. Confirm the message + the actual dialed number.
- **Test 12 — Returning prospect status check** → "I applied last week, just checking in." → Aubrey routes to PROSPECT STATUS CHECK → if caller asks for live person, transfers to **470-868-4776** (Care Team).

---

## Open questions for client

1. **Rochele (Onboarding) node** — currently transfers prospect-app issues to 678-785-7013. Is that still the right number for Rochele specifically, or should Rochele be folded into the Eligibility Specialist team?
2. **Care Team scope** — your message mentions Care Team handles "referred applicants/caregivers not yet started services, calling for status update." Should the existing case-manager-routing-to-Care-Team paths ("in process of starting" / "switch providers") also go to 470-868-4776, or is that a different Care Team?
