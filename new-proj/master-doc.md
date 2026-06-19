## 1. Context and goal

Bookings fail silently. The caller hears "you're all set" and the confirmation sends, but no appointment is written and no contact is created. It is intermittent and skews to new callers. Root cause: every layer verifies that the HTTP call completed, not that the appointment actually wrote to GHL. The full diagnostic is in the proposal; this doc is the build plan.

The goal of the engagement: **a confirmation can never go out unless the write to GHL actually succeeded**, and any claim-versus-reality mismatch raises an operator alert so the lead is recovered instead of lost.

### 1.1 The failure has two layers, only one is confirmed

The silent failure is a chain, and the two halves live in different systems. They must be diagnosed separately.

**Layer A, the n8n side (confirmed).** `Book_Appointment` returns an HTTP 200 even when the booking failed. `GHL - Create Appointment` runs with `continueOnFail`, so a GHL rejection (taken slot, capacity full, bad contactId, 4xx) is swallowed, `Handle Booking Result` returns `success: false` with no `appointment_id`, and `Respond to Retell` sends that body with a 200 status. This is confirmed from the workflow logic: a failed booking is delivered to the agent as a 200 response carrying `success: false`. The n8n hardening in M1 fixes this half directly.

**Layer B, the Retell side (largely addressed on the new agent, one check remaining).** Whether the caller hears "you're all set" depends on how the agent handles the tool response. The old Monolith agent was the likely source of the false confirmation, advancing on tool completion rather than reading `success`. The new single-prompt agent already stores `appointment_id` and `success` from the n8n response, so it consumes the verified-write outputs directly. One check remains: storing `success` is not the same as gating the spoken confirmation on it. Confirm the new agent only speaks the confirmation when `success === true`, not merely that it records the value. This is a verification on the agent, not n8n work. See Section 4.1.

**Conclusion:** the n8n fix removes the silent-loss damage (via verified write plus operator alert) regardless of the agent. With the new agent storing `appointment_id` and `success`, the remaining agent-side risk is narrow: confirm the spoken confirmation is gated on `success`, not just stored.

---

## 2. Agent situation: single-prompt standard, shared webhook

The agent migration is confirmed. The old Conversation Flow agent (the "Monolith," ~78 nodes) is being retired. Every client runs on the new single-prompt agent going forward.

**The key fact: the webhook is shared.** The new single-prompt agent's `book_appointment` function calls the same n8n webhook (`retell-book-appointment`) as before. So the booking contract is stable across the migration, and every fix made in n8n carries over to the new agent automatically with no rework. The work is durable by construction.

**Our work is entirely in n8n and GHL. We do not build in Retell.** The new agent already stores `appointment_id` and `success` returned by the n8n workflow, so the agent side already consumes the verified-write outputs. Any remaining agent-side requirement is delivered as the integration contract in Section 4 to whoever owns the agent; we do not implement it.

**What this means for where we build:**

- All build work is in n8n and GHL. The shared webhook means it applies to the new agent immediately.
- The verified-write logic lives in the same n8n workflow the new agent already calls, so it is hardened in place.
- Because the new agent stores `appointment_id` and `success`, the booking core work is mostly about proving the write path is solid end to end, not introducing new plumbing on the agent side.

---

## 3. Architecture principle

n8n and GHL are the source of truth and the enforcement layer. The agent is treated as an untrusted caller. Concretely:

1. Booking truth is read back from GHL, never inferred from what the agent reported.
2. Every workflow exit returns one canonical response shape so the agent can branch on it identically, regardless of agent build.
3. The operator alert is the one step that can never be skipped, no matter what fails upstream.

The canonical tool response contract, returned on every exit of `Book_Appointment`:

```json
{
  "success": true,
  "appointment_id": "abc123",
  "response": "Appointment confirmed for ... A confirmation text will be sent shortly."
}
```

```json
{
  "success": false,
  "reason": "slot_taken | booking_failed | invalid_input | capacity_full",
  "response": "<exact words the agent should speak, then re-collect>"
}
```

---

## 4. Retell integration contract (guidance for the Single-Prompt team)

We do not build in Retell. This is the contract plus guidance we deliver to whoever owns the single-prompt agent, so it works correctly against the hardened n8n backend. The new agent already stores `appointment_id` and `success` from the n8n response, so item 1 may already be satisfied (confirm via Section 4.1). The rest should be stated plainly in the system prompt, since a single-prompt agent reasons in one prompt rather than explicit flow nodes.

1. **Branch on the result body, not tool completion.** The agent must only move to the confirmation state when the tool response has `success === true`. Tool completion (HTTP 200) is not success.
2. **On `success === false`, speak `response` verbatim and re-collect.** Do not confirm. Do not end the call as booked.
3. **Collect address as four separate fields**, not one spoken string: `address1`, `city`, `state`, `postal_code`. This removes the single biggest source of new-caller failures.
4. **Re-confirm the phone number** when the system reports it could not be normalized.
5. **Pass `call_id` into the booking tool** so n8n can dedupe retries (Section 7, M3).

n8n hardens its own fallback parsing and normalization regardless, so the system degrades gracefully if the new agent does not yet send clean structured fields. The contract is the durable fix; the parser is the safety net.

### 4.1 Retell verification task: confirm the confirmation is gated on success

The new single-prompt agent already stores `appointment_id` and `success` from the n8n response. The one thing left to confirm is that it gates the spoken confirmation on `success === true`, rather than storing the value and confirming anyway. This is a quick diagnostic on the agent, not a build, and any fix found goes into the integration contract (Section 4) for whoever owns the agent.

Test procedure:

1. Force `Book_Appointment` to return `success: false` for a test call. Two reliable ways: book a slot that is already taken or at full capacity, or submit an address that fails the validation gate. The workflow responds 200 with `success: false` and no `appointment_id`.
2. Run a call through the single-prompt agent that triggers that booking.
3. Observe what the agent says when the tool returns `success: false`:
    - If it still speaks a confirmation, the agent is storing `success` but not gating on it. Flag for the contract: the spoken confirmation must be conditioned on `success === true`.
    - If it correctly declines to confirm and re-prompts, the gating is already correct and no agent change is needed.
4. Cross-check one real production call where the caller heard the confirmation but GHL has no appointment: read its Retell transcript and tool-response log to see the `success` value the agent received and what it said next.

Outcome: a clear yes/no on whether the spoken confirmation is gated on verified success, recorded in Section 9.

---

## 5. Build plan

Workflows in scope: `Book_Appointment`, `Post_Call_Webhook`, `Calendar_Check`, `Notification_Dispatcher`. A fifth workflow, `Error Handling`, is also in scope and needs review before kickoff; fold any relevant findings into M1.5 (fail loud, not fatal).

### Milestone 1: Verified-write booking core (n8n)

Covers diagnostic issues 1 through 7.

**M1.1 Appointment ID as the only success token** (`Book_Appointment`)

- After `GHL - Create Appointment`, extract the id (`id || appointment.id || eventId`).
- Add a read-after-write step: GET the appointment by id and confirm it exists and status is not cancelled.
- Return `success: true` only when that read confirms it. Include `appointment_id` in the response.
- Remove the assumption baked into `continueOnFail`. Keep the node from aborting the run, but route a failed/empty create explicitly to the failure response, never to a success.

**M1.2 Canonical response on every exit** (`Book_Appointment`)

- Standardize the validation-error path, the slot-taken path, and the success path to the exact contract in Section 3. Same keys, same shape, every time.

**M1.3 Verification-first ordering** (`Post_Call_Webhook`)

- Move `GHL - Check Appointment` and `Evaluate Booking` to run immediately after `Parse Retell Payload`, before any contact or opportunity write.
- Replace `bookingConfirmed = tc.success === true` entirely. Booking truth comes from the GHL appointments read (`real_booked`), not the tool claim.
- Drop `|| retellCallSuccessful` from the booked condition. The model grading its own call is not evidence.

**M1.4 Confirmation gated on `real_booked`** (`Post_Call_Webhook` to `Notification_Dispatcher`)

- The `booking_confirmation` outcome fires only when `real_booked === true`.
- When `agent_claim === booked` and `real_booked === false`, fire an immediate operator alert carrying the caller's number and summary. This is the lead-recovery net that protects the two-week gap.

**M1.5 Fail loud, not fatal** (`Post_Call_Webhook`)

- Set `onError: continueRegularOutput` on `GHL - Search for Contact`, `GHL - Upsert Contact`, `GHL - Update Existing Contact`, and `GHL - Create Opportunity`.
- Restructure so the verification and operator alert are reached unconditionally, even when an upstream write throws. The alert must be the last thing that cannot be skipped, not the last thing in a fragile chain.

**M1 acceptance:** see the test matrix in Section 8.

### Milestone 2: Data integrity (n8n)

Covers diagnostic issues 8, 9, 10, 11.

**M2.1 Empty-query search guard** (`Post_Call_Webhook`)

- Never call `GHL - Search for Contact` with `query: ""`. If `caller_phone` is empty, skip the search and route to the new-contact path or the alert path. An empty query can return an arbitrary contact and write call data onto the wrong person's record.
- Audit existing contacts for prior wrong-record writes caused by this.

**M2.2 Address parser hardening** (`Book_Appointment`)

- Harden the fallback parser so comma-less speech input like `698 NE 1st Ave Miami FL 33132` parses correctly: extract ZIP (first 5-digit group), then the 2-letter state immediately before it, then split the remainder into street and city with token heuristics.
- If a valid 5-digit ZIP and a city cannot be derived, return the canonical `invalid_input` response so the agent re-collects, rather than guessing.
- Structured fields from the agent (Section 4, item 3) are the real fix; this parser is the safety net for the gap and for any malformed input afterward.

**M2.3 Shared phone normalization** (`Book_Appointment` + `Post_Call_Webhook`)

- Use one identical `normalizeUSPhone()` in both workflows.
- In `Book_Appointment`, if the phone normalizes to empty, return the canonical re-collect response instead of proceeding.

**M2.4 DST-safe timezones** (`Calendar_Check` + `Book_Appointment` same-day slots)

- Replace the hardcoded `04:00` offsets used to build day-boundary timestamps. Use luxon (available in n8n code nodes) with the `America/New_York` zone so the offset is correct year-round. The current code shifts everything by an hour once DST ends in November.

### Milestone 3: Credential cleanup and observability (n8n + GHL)

Covers diagnostic issue 13 plus the two scoped improvements (idempotency, reconciliation), both built Round-Robin aware.

**M3.1 Credential cleanup** (all four workflows)

- Move the GHL API key, base URL, location id, calendar id, pipeline and stage ids, and custom field ids out of the code nodes into n8n credentials (HTTP Header Auth) and a single shared config, or environment variables.
- **Rotate the GHL token.** It has lived in exported JSON, so rotation is the responsible step, not optional.

**M3.2 Idempotency, keyed on the call** (`Book_Appointment`)

- Dedupe on `call_id`, never on the slot.
- Before creating, check whether an appointment already carries this `call_id` (store it in a custom field or as a title token). If it does, return that existing `appointment_id` and do not create a second.
- This is the specific thing GHL cannot do for us: GHL has no concept that two webhook hits came from the same phone call, so without this a retry would load-balance the same caller onto a second nurse.

**M3.3 Daily reconciliation, Round-Robin aware** (new scheduled workflow)

- Once per day, list contacts marked Booked in the last 24 hours and confirm each has a real, non-cancelled GHL appointment on the expected date.
- Treat multiple bookings in the same slot across different nurses as valid by design. Never flag legitimate concurrency.
- Flag only true discrepancies: a contact marked Booked with no real appointment, or an orphaned appointment with no matching contact.
- Output a digest to the operator (email or SMS).

---

## 6. Round Robin: what GHL owns vs what we own

The live calendar is a GHL Round Robin with multi-nurse concurrency. Capacity equals assigned staff (3 nurses means 3 bookings in the same slot, the 4th rejected).

**GHL handles natively, we do not rebuild:** per-slot capacity, nurse assignment and load balancing, capacity-aware free-slots output, and the over-capacity rejection itself.

**Our code must respect that correct behavior:**

- Idempotency keys on the call, so a retry cannot ride spare capacity onto a second nurse (M3.2).
- Reconciliation treats different-nurse same-slot bookings as valid (M3.3).
- The verified-write path correctly handles GHL's capacity-full rejection: report `capacity_full`, speak the re-collect response, do not confirm. The "slot conflict" acceptance test is really a capacity-full rejection test.

---

## 7. Baseline and before/after deliverable

Baseline protocol:

1. Download all workflows on day one and snapshot the current n8n `versionId` of each as the frozen baseline.
2. Build against that baseline. Document every change so there is never ambiguity about who touched what.
3. Deliver a before/after comparison of the workflows at the end.

Note on sequencing: if a prior contractor's change is still mid-flight, confirm whether the shared workflows are the final baseline or whether another edit is still landing before snapshotting.

Frozen baseline versionIds (fill on kickoff):

| Workflow | versionId at baseline |
| --- | --- |
| Book_Appointment |  |
| Post_Call_Webhook |  |
| Calendar_Check |  |
| Notification_Dispatcher |  |
| Error Handling |  |

---

## 8. Test and acceptance matrix

Testing method: each scenario is run by injecting JSON payloads into the n8n webhooks, exercising every branch without needing a live phone call. Each milestone is only checked off once its scenarios pass this way; live test calls confirm end to end. Testing is done manually.

Run as live test calls. M1 acceptance requires all rows pass.

| Scenario | Expected behavior |
| --- | --- |
| New caller, clean structured address | Contact created, appointment written, verified, confirmation sent |
| Repeat caller | Existing contact updated, appointment written, verified, confirmation sent |
| Anonymous caller ID | No empty-query search, no wrong-record write, handled gracefully, operator alerted if booking attempted |
| Comma-less spoken address | Parser recovers a valid address, or agent re-collects; never a silent 200 fail |
| International / malformed phone | Normalizes to empty, agent re-confirms; no failed silent upsert, no halted run |
| Capacity-full slot (all nurses booked) | GHL rejects, system reports `capacity_full`, agent re-collects, no false confirmation |
| Retry / duplicate `call_id` | No second appointment, no second nurse, original `appointment_id` returned |
| Forced GHL write failure mid-pipeline | Run does not halt, operator alert still fires with caller number |
| Claim booked but no real write | `booking_status_label = Booking Failed`, immediate operator alert, no booking confirmation to caller |

---

## 9. Decision and change log

| Date | Decision / change | Notes |
| --- | --- | --- |
| Set | Production agent: single-prompt standard; Monolith retired | New agent's `book_appointment` calls the same `retell-book-appointment` webhook, so n8n work carries over automatically. We do not build in Retell. |
| Set | Cleared to start n8n hardening | Credential cleanup, reconciliation, idempotency, contact-handling, verified-write all greenlit |
| Pending | Confirm baseline is final (no other in-flight edit) | Snapshot versionIds once confirmed |
| Pending | Verify the new agent gates spoken confirmation on `success` | New agent stores `appointment_id` and `success`; confirm it speaks confirmation only on `success === true`, not merely stores it (Section 4.1) |
|  | Frozen baseline captured | versionIds recorded in Section 7 |
|  |  |  |

---

## 10. Out of scope

This engagement covers the issues in the diagnostic plus the hardening above. Anything unrelated surfaced while in the system gets flagged to Jabari with a recommendation, but the fix is a separate scoped item with his sign-off. No work done without it.