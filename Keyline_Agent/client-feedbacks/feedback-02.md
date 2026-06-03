# Feedback-02 — Routing Fixes + Two Production Bugs (2026-05-30)

Combines Bernae's routing message (2026-05-30) with two bugs found in [call-issues-01.md](../call-issues/call-issues-01.md).

> **Direction from Stephen:** keep all *existing* numbers as-is. Only wire the new routing Bernae asked for. After we ship, send Keyline a summary of which number is used for which purpose so they can correct anything.

---

## A. Routing — what Bernae asked for

| Caller type | Destination | Number |
|---|---|---|
| Current client or active caregiver | **Case Support** | 678-785-7010 |
| New prospect (looking to enroll) | Collect intake → **live transfer to Eligibility Specialist Dept** after ticket | 678-785-7013 |
| Referred applicant / caregiver — not yet started service, calling for status update | **Care Team** | **470-868-4776** ← new |

### A1. Agent JSON changes (numbers + nodes)

- [ ] **A1.1** Repoint `TRANSFER - CARE TEAM` (`node-transfer-care-team`) from `+16787857013` → **`+14708684776`**. Also adjust the static text to mention Care Team explicitly: *"Let me connect you with our Care Team. Please hold."*
- [ ] **A1.2** Add a **new** transfer node `TRANSFER - ELIGIBILITY SPECIALIST DEPT` at `+16787857013`. Static text: *"Now let me connect you with our Eligibility Specialist team to complete your enrollment. Please hold."* On-failure edge → `node-close-call`. (We are keeping the existing `node-transfer-eligibility` / Alyssa-Screening as a separate node — different purpose, different number `+14702438993`.)

### A2. Flow change — prospect intake gets a live transfer after the ticket

Today: PROSPECT INTAKE → PROSPECT SUBMIT → Create Ticket → Ticket Confirmation → CLOSE CALL. The `Ticket Confirmation` prompt for `call_type == "prospect"` says *"Do NOT transfer the call."*

Per Bernae, after the ticket is created Aubrey must *attempt a live transfer to the Eligibility Specialist Dept*.

- [ ] **A2.1** In `Ticket Confirmation` (`node-1776962211546`), modify the `call_type == "prospect"` branch:
  - Keep ticket-number readback + repeat offer + SMS line.
  - Replace the closer "Per the spec, the team will contact the caller later" with: *"Now, let me connect you with our Eligibility Specialist team to get started. Please hold."*
- [ ] **A2.2** Add a new edge from `Ticket Confirmation` → `TRANSFER - ELIGIBILITY SPECIALIST DEPT` gated on `call_type == "prospect" AND ticket readback complete`. Fires automatically — no "anything else?" needed in the prospect path.
- [ ] **A2.3** Soften the closing in `PROSPECT SUBMIT` (`node-prospect-submit`, Part A) so it doesn't conflict with the live transfer that's coming. Suggested: *"Caregivers deserve real support — we'll start reviewing your case right away, and I'll connect you with our Eligibility team in just a moment."*

### A3. Verification logic on OPENING

- [ ] **A3.1** In `OPENING` (`start-node-aubrey-opening`), under the existing PROSPECT EXCEPTION block, add a clarifying sub-rule: *"For PROSPECTS, first verify whether they are (a) **looking to enroll** (new applicant) → PROSPECT INTAKE, or (b) **already started the referral process but not yet started service, calling for status** → PROSPECT STATUS CHECK."*
- [ ] **A3.2** `PROSPECT STATUS CHECK` already routes "speak with someone" → `node-transfer-care-team`; once A1.1 lands, this goes to 470-868-4776 automatically. Verify via Test 12.
- [ ] **A3.3** Current-client / active-caregiver paths route to `node-transfer-case-support` (7010) via existing flows. No change needed — verify via Test 10.

---

## B. Bug 1 — Aubrey says "Is there anything else?" during ticket creation

**Where seen:** [call-issues-01.md](../call-issues/call-issues-01.md), Call 01, lines 248-251 (right after `create_ticket` returns, before `Send Ticket SMS` fires).

**Root cause (verified):** The global prompt Core Rule says *"Before ending ANY call, you MUST say 'Is there anything else I can help you with today?'"* — and the LLM treats the user's "Thank you" mid-ticket-creation as a call-ending signal. The submit nodes (INCIDENT SUBMIT, MCO SUBMIT, PROSPECT SUBMIT) carry local guards against this, but the `Create Ticket` function node has no prompt of its own, so once we leave the submit node only the global rule applies. The guard never reaches the function-node turn.

This is a **global-prompt scoping bug**. Don't fix by piling more guards on each submit node — fix the rule itself.

- [ ] **B1.1** Edit the global prompt Core Rules section. Replace:
  > "Before ending ANY call, you MUST say 'Is there anything else I can help you with today?' and wait for the caller's response. NEVER end the call without this line. Only close after the caller says no or goodbye."

  With:
  > "Before ending ANY call, you MUST say 'Is there anything else I can help you with today?' and wait for the caller's response. NEVER end the call without this line. Only close after the caller says no or goodbye.
  >
  > **Exception — ticket pipeline:** Do NOT say this line while a ticket is being created (between the 'I'm submitting your request now' line and the Ticket Confirmation node reading the ticket number). The ticket isn't done yet. If the caller says 'thank you' or similar during this window, treat it as acknowledgment — stay silent and let the pipeline finish. The 'anything else?' line belongs to Ticket Confirmation (after the ticket number is read) or CLOSE CALL — never to a function node or submit node."

- [ ] **B1.2** Verify the affected submit nodes (INCIDENT SUBMIT, MCO SUBMIT, PROSPECT SUBMIT) still carry their local "stay silent during ticket creation" instruction. Keep those — defense in depth.

---

## C. Bug 2 — PROSPECT INTAKE stuck after Q15 answer

**Where seen:** [call-issues-01.md](../call-issues/call-issues-01.md), Call 02, lines 522-533. User answered the last question at 3:15. Aubrey said "Got it — one moment" at 3:18. Then **11 seconds of silence** until the "Still with me?" reminder fired, and only after the user re-engaged did the transition to PROSPECT SUBMIT happen at 3:34.

**Root cause (verified):** The edge condition on `node-prospect-intake` → `node-prospect-submit` reads:
> *"Caller has just provided an answer to question 16 AND Aubrey has said 'Got it — one moment.'"*

Retell evaluates edges **on user turns**, not on agent turns. So when the user answered Q15, Aubrey hadn't yet said "Got it — one moment" — edge fails. Aubrey then takes her turn and says it — no edge evaluation triggers on agent turns. System sits waiting for the next user turn. The "Got it — one moment" bridge line is dead weight that creates a deadlock.

- [ ] **C1.1** In `node-prospect-intake`, edit the `AFTER LAST FIELD (Q15 ANSWERED)` block. Remove the instruction to say "Got it — one moment." entirely. Replace with: *"After the caller answers Q15, STOP. Do not generate any acknowledgment. The system will transition to PROSPECT SUBMIT immediately — PROSPECT SUBMIT will deliver the closing."*
- [ ] **C1.2** Simplify the edge condition (`e-pi-submit`) on the same node. New text: *"Caller has just provided an answer to question 15 (autism / intellectual or developmental disability). All 15 intake fields are now collected. Transition immediately."* (Also fixes the off-by-one — current prompt says "question 16" but there are 15 questions.)
- [ ] **C1.3** Verify `PROSPECT SUBMIT`'s Part A is the first thing the caller hears after Q15 — that's what makes C1.1 safe. (Part A in current JSON: *"Caregivers deserve real support, and we're going to start reviewing your case right away…"* — yes, it opens with a full sentence, no ack needed.)

---

## D. Test additions (append to [test-plan-2026-05-23.md](test-plan-2026-05-23.md))

- **Test 10 — Active caregiver, asks for live person** → must route to `+16787857010` (Case Support).
- **Test 11 — New prospect, full intake** → after Q15, Aubrey must auto-advance with NO "Still with me?" pause. After ticket readback, Aubrey must say "connecting you with Eligibility" and dial `+16787857013`.
- **Test 12 — Returning prospect status check** → "I applied last week, just checking in." If caller asks for a live person, must dial `+14708684776` (new Care Team).
- **Test 13 — Bug 1 regression** → run any ticket-creating flow (e.g., Test 2 missed clock-out). After "I'm submitting your request now", say "thanks!" during the create_ticket window. Aubrey must NOT respond with "Is there anything else?" — she should stay silent until the ticket number readback in Ticket Confirmation.
- **Test 14 — Bug 2 regression** → run a fresh prospect intake (Test 11). After answering Q15, Aubrey must transition to PROSPECT SUBMIT and start speaking *"Caregivers deserve real support…"* within ~2 seconds. No "Still with me?" pause.

---

## D2. Follow-up fixes from verification workflow (applied 2026-05-30)

After running an adversarial verification workflow on the initial changes, four more issues were found and fixed:

- **H1 — TEAM MEMBER REQUEST edge split.** The `e-tm-eligibility` edge was pointing to `node-transfer-eligibility` (which is actually Alyssa-Screening at +14702438993, not the new Eligibility Specialist Dept). Replaced with two distinct edges: `e-tm-eligibility-dept` → `node-transfer-eligibility-dept` (+16787857013) gated on Eligibility Specialist / enrollment / new application, and `e-tm-alyssa-screening` → `node-transfer-eligibility` (+14702438993) gated on Alyssa / phone screening / nurse assessment. Also updated the in-prompt routing table.
- **H2 — GLOBAL HUMAN REQUEST simplification.** Prompt was verbally promising "let me connect you with our Care Team" for prospects but only had a `skip_response_edge` to Case Support — say/do gap. Stripped the Care Team carve-out. Everyone routed via this node now goes to Case Support uniformly. Prospects in PROSPECT STATUS CHECK still reach Care Team via that node's own `e-ps-xfer` edge.
- **M1 — CAREGIVER MENU switching-providers wording.** Edge prompt said "Route to Care Team for new enrollments and provider changes" — misleading after the Care Team meaning narrowed. Reworded to "Route to Care Team for provider-change requests" only.
- **M2 — Close-call edge collision fix.** Two changes to Ticket Confirmation: (a) reordered edges so `e-tc-prospect-xfer` evaluates *before* the close-call "no thanks" edge; (b) added explicit guard `call_type is NOT "prospect"` to the close-call edge to make the two strictly mutually exclusive. Prevents a prospect's "no thanks" to the repeat-offer from being misread as call-end.

---

## E. Post-ship — number summary for Keyline

After everything lands, send Keyline a one-page rundown like:

| Purpose / department | Current number in agent |
|---|---|
| Case Support (current clients, active caregivers, FC App issues) | 678-785-7010 |
| Eligibility Specialist Dept (post-prospect-intake live transfer) | 678-785-7013 |
| Care Team (referred applicants, status checks, switching providers) | 470-868-4776 |
| Alyssa — Screening / Nurse Assessment | 470-243-8993 |
| Rochele — Prospect App / Onboarding paperwork | 678-785-7013 |
| Kalil — Semi-Annual Visits | 770-658-0034 |
| Payroll Team | 678-785-7010 |
| Health Coach (generic, no name on file) | 678-785-7010 |

Ask Keyline to confirm or correct each row.
