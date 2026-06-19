**Scope:** n8n only (`Book_Appointment`, `Post_Call_Webhook`, `Notification_Dispatcher`)
**Covers:** diagnostic issues 1 through 7
**Companion to:** the master dev doc (full context, all milestones)

---

## Goal of this milestone

A confirmation can never go out unless the write to GHL actually succeeded, and any claim-versus-reality mismatch raises an operator alert so the lead is recovered instead of lost.

This is the milestone that stops the silent booking loss. Everything else (M2, M3) hardens around it.

## The defect this fixes

`Book_Appointment` returns an HTTP 200 even when the booking failed. `GHL - Create Appointment` runs with `continueOnFail`, so a GHL rejection (taken slot, capacity full, bad contactId, 4xx) is swallowed, `Handle Booking Result` returns `success: false` with no `appointment_id`, and `Respond to Retell` sends that body with a 200 status. The post-call pipeline then reads booking status from the tool claim (`tc.success === true`, which is transport-level and always true) instead of from GHL, so the contact gets stamped Booked and the confirmation fires on a claim, not a verified write.

The new single-prompt agent already stores `appointment_id` and `success` from the n8n response, so this work flows straight back to it through the shared `retell-book-appointment` webhook. The booking core work is mostly about proving the write path is solid end to end.

## Architecture principle

n8n and GHL are the source of truth. The agent is treated as an untrusted caller.

1. Booking truth is read back from GHL, never inferred from what the agent reported.
2. Every workflow exit returns one canonical response shape.
3. The operator alert is the one step that can never be skipped, no matter what fails upstream.

Canonical tool response contract, returned on every exit of `Book_Appointment`:

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

## Tasks

**M1.1 Appointment ID as the only success token** (`Book_Appointment`)

- After `GHL - Create Appointment`, extract the id (`id || appointment.id || eventId`).
- Add a read-after-write step: GET the appointment by id and confirm it exists and status is not cancelled.
- Return `success: true` only when that read confirms it. Include `appointment_id` in the response.
- Remove the assumption baked into `continueOnFail`. Keep the node from aborting the run, but route a failed/empty create explicitly to the failure response, never to a success.

**M1.2 Canonical response on every exit** (`Book_Appointment`)

- Standardize the validation-error path, the slot-taken path, and the success path to the exact contract above. Same keys, same shape, every time.

**M1.3 Verification-first ordering** (`Post_Call_Webhook`)

- Move `GHL - Check Appointment` and `Evaluate Booking` to run immediately after `Parse Retell Payload`, before any contact or opportunity write.
- Replace `bookingConfirmed = tc.success === true` entirely. Booking truth comes from the GHL appointments read (`real_booked`), not the tool claim.
- Drop `|| retellCallSuccessful` from the booked condition. The model grading its own call is not evidence.

**M1.4 Confirmation gated on `real_booked`** (`Post_Call_Webhook` to `Notification_Dispatcher`)

- The `booking_confirmation` outcome fires only when `real_booked === true`.
- When `agent_claim === booked` and `real_booked === false`, fire an immediate operator alert carrying the caller's number and summary. This is the lead-recovery net.

**M1.5 Fail loud, not fatal** (`Post_Call_Webhook`)

- Set `onError: continueRegularOutput` on `GHL - Search for Contact`, `GHL - Upsert Contact`, `GHL - Update Existing Contact`, and `GHL - Create Opportunity`.
- Restructure so the verification and operator alert are reached unconditionally, even when an upstream write throws. The alert must be the last thing that cannot be skipped, not the last thing in a fragile chain.
- Review the fifth workflow, `Error Handling`, and fold any relevant findings in here.

---

## Acceptance

Run by injecting JSON payloads into the n8n webhooks to exercise every branch, then confirm with live test calls. All rows must pass.

| Scenario | Expected behavior |
| --- | --- |
| New caller, clean structured address | Contact created, appointment written, verified, confirmation sent |
| Repeat caller | Existing contact updated, appointment written, verified, confirmation sent |
| Capacity-full slot (all nurses booked) | GHL rejects, system reports `capacity_full`, no false confirmation |
| Forced GHL write failure mid-pipeline | Run does not halt, operator alert still fires with caller number |
| Claim booked but no real write | `booking_status_label = Booking Failed`, immediate operator alert, no booking confirmation to caller |

## Dependency note

This milestone is the foundation. M2 (data integrity) and M3 (idempotency, reconciliation) assume the canonical response contract and the verification-first ordering established here.


---

Milestone 2:

## Goal of this milestone

Fix the data-quality defects that make the silent failure intermittent and skew it toward new callers. M1 stops the silent loss; M2 removes the conditions that triggered it in the first place, so fewer bookings ever hit the failure path.

## Why these matter (new-caller skew)

Existing callers arrive with clean prefilled data and clean phone numbers, so they pass validation and take the safe update path. New callers' data comes from live speech, so a comma-less address fails the parser and an imperfect phone fails normalization. Both push the call onto the fragile path. These four fixes close that gap.

## Canonical response contract (from M1, reused here)

When any of these fixes needs to reject input, it returns the same shape M1 established:

```json
{ "success": false, "reason": "invalid_input", "response": "<words the agent should speak, then re-collect>" }
```

---

## Tasks

**M2.1 Empty-query search guard** (`Post_Call_Webhook`)

- Never call `GHL - Search for Contact` with `query: ""`. If `caller_phone` is empty, skip the search and route to the new-contact path or the alert path. An empty query can return an arbitrary contact and write call data onto the wrong person's record.
- Audit existing contacts for prior wrong-record writes caused by this.

**M2.2 Address parser hardening** (`Book_Appointment`)

- Harden the fallback parser so comma-less speech input like `698 NE 1st Ave Miami FL 33132` parses correctly: extract ZIP (first 5-digit group), then the 2-letter state immediately before it, then split the remainder into street and city with token heuristics.
- If a valid 5-digit ZIP and a city cannot be derived, return the canonical `invalid_input` response so the agent re-collects, rather than guessing.
- Structured fields from the agent (master doc, Section 4 item 3) are the real fix; this parser is the safety net for any malformed input.

**M2.3 Shared phone normalization** (`Book_Appointment` + `Post_Call_Webhook`)

- Use one identical `normalizeUSPhone()` in both workflows.
- In `Book_Appointment`, if the phone normalizes to empty, return the canonical re-collect response instead of proceeding.

**M2.4 DST-safe timezones** (`Calendar_Check` + `Book_Appointment` same-day slots)

- Replace the hardcoded `04:00` offsets used to build day-boundary timestamps. Use luxon (available in n8n code nodes) with the `America/New_York` zone so the offset is correct year-round. The current code shifts everything by an hour once DST ends in November.

---

## Acceptance

Run by injecting JSON payloads into the n8n webhooks to exercise every branch, then confirm with live test calls. All rows must pass.

| Scenario | Expected behavior |
| --- | --- |
| Anonymous caller ID | No empty-query search, no wrong-record write, handled gracefully, operator alerted if booking attempted |
| Comma-less spoken address | Parser recovers a valid address, or agent re-collects; never a silent 200 fail |
| International / malformed phone | Normalizes to empty, agent re-confirms; no failed silent upsert, no halted run |
| Same-day slot request after DST change (simulate November) | Day-boundary timestamps are correct, no one-hour shift |


---

Milestone 3:

## Goal of this milestone

Make the system secure and self-monitoring. After M1 and M2, bookings are verified and the failure paths are closed. M3 secures the credentials, prevents duplicate bookings under Round Robin, and adds a daily check so any future discrepancy surfaces the next morning instead of never.

---

## Tasks

**M3.1 Credential cleanup** (all four workflows)

- Move the GHL API key, base URL, location id, calendar id, pipeline and stage ids, and custom field ids out of the code nodes into n8n credentials (HTTP Header Auth) and a single shared config, or environment variables.
- **Rotate the GHL token.** It has lived in exported JSON that has been shared around, so rotation is the responsible step, not optional. Do this early in the milestone.

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

## Round Robin: what GHL owns vs what we own

The live calendar is a GHL Round Robin with multi-nurse concurrency. Capacity equals assigned staff (3 nurses means 3 bookings in the same slot, the 4th rejected).

**GHL handles natively, we do not rebuild:** per-slot capacity, nurse assignment and load balancing, capacity-aware free-slots output, and the over-capacity rejection itself.

**Our code must respect that correct behavior:**

- Idempotency keys on the call, so a retry cannot ride spare capacity onto a second nurse (M3.2).
- Reconciliation treats different-nurse same-slot bookings as valid (M3.3).
- The verified-write path (built in M1) correctly handles GHL's capacity-full rejection: report `capacity_full`, do not confirm.

---

## Acceptance

Run by injecting JSON payloads into the n8n webhooks, then confirm with live test calls.

| Scenario | Expected behavior |
| --- | --- |
| All credentials moved and token rotated | No secrets in any code node; workflows run on credentials/env vars; old token revoked |
| Retry / duplicate `call_id` | No second appointment, no second nurse, original `appointment_id` returned |
| Two different callers, same slot, different nurses | Both booked, reconciliation treats as valid, neither flagged |
| Contact marked Booked with no real appointment | Reconciliation flags it in the daily digest to the operator |