# Knight Law — Inbound Agent Plan (Alice Inbound)

> **Status:** Plan only — no implementation yet.
> **Scope:** Handle *return calls* into Alice. Every caller already exists in **Salesforce + GHL** (they were created in SF as a qualified lead, pushed to GHL, and called outbound). Inbound therefore **never creates a lead** — it **looks up, resumes, re-routes**, and writes back through the *same* post-call → Zapier → Salesforce machinery the outbound flow already uses.

---

## 1. What inbound is (and isn't)

The outbound system is a closed loop:

```
Salesforce (HF Qualified) → Zapier (pre-call) → GHL "01. Outbound" → Retell OUTBOUND call
   → post-call webhook → GHL "Post Retell" → Zapier "02.01 Post Call" → Salesforce update / DocuSign
```

**Inbound is a return call into that same loop.** A person Alice already called (or who was created for outbound) dials back. They may be:

- an **Incomplete** lead who never finished intake, or never answered the outbound call, or
- a **completed** lead (Retainer / Non-Retainer / Bad / Opt-Out) calling again.

Because the lead always pre-exists, the inbound job is: **identify → read their status & prior answers → do the right thing → write back via the existing post-call path.**

### Confirmed business decisions (baked into this plan)

| Decision | Choice |
|---|---|
| **Bad lead calls back** | **Re-check, then close.** Reversible reasons (no-possession / possible misclassification) → Alice re-checks that one point; if it flips, continue intake. Irreversible (vehicle year ≤2019, out-of-state) → polite explanation + callback number, **no transfer**. |
| **Returning Retainer / Non-Retainer** | **Confirm status + warm transfer.** Identify, give a brief status update, warm-transfer to Knight Law (hours-gated). **No re-intake, no re-sending the agreement.** |
| **After hours** (outside Mon–Fri 8a–8p PT) | **Finish/resume intake + book callback.** Save everything, book a callback / take a message. **No live transfer when the team is closed.** |
| **Callback / booking** | Reuse the existing **consultation booking link** (`send_consultation_link`). |
| **Lead creation** | **Never.** Inbound only reads/updates existing contacts. |

---

## 2. Architecture overview

Three components. Two of them reuse existing infrastructure.

```
                          ┌─────────────────────────────────────────────┐
   Caller dials  ───────► │  RETELL inbound number (Alice Inbound)       │
   the inbound #          │                                              │
                          │  (a) Pre-call webhook fires BEFORE pickup ───┼──┐
                          └─────────────────────────────────────────────┘  │
                                                                            ▼
                          ┌──────────────────────────────────────────────────────────┐
                          │  COMPONENT 1 — Pre-Call Lookup Workflow (n8n)             │
                          │  "Knight Law - Pre Call Workflow" (IfnL95bXqblx8SwC)      │
                          │  Webhook → Constant → Get Contact (by phone)             │
                          │   → Pick Contact (0/1/many) → Map Fields                  │
                          │   → Respond: { call_inbound: { dynamic_variables } }      │
                          └───────────────────────────────┬──────────────────────────┘
                                                          │ dynamic variables
                                                          ▼
                          ┌──────────────────────────────────────────────────────────┐
                          │  COMPONENT 2 — Retell "Alice Inbound" conversation flow   │
                          │  Router on lead_status → (resume intake | confirm+xfer |  │
                          │   re-check bad | generic intake) → terminal action        │
                          │  Terminals: warm transfer / book callback / polite close  │
                          └───────────────────────────────┬──────────────────────────┘
                                                          │ post-call webhook (call analysis)
                                                          ▼
                          ┌──────────────────────────────────────────────────────────┐
                          │  COMPONENT 3 — Post-Call Workflow (REUSE existing)        │
                          │  GHL "Post Retell" → branch by Lead Status → Zapier →     │
                          │   Salesforce update / DocuSign                            │
                          │  + 2 new guards: DocuSign idempotency, inbound-source tag │
                          └──────────────────────────────────────────────────────────┘
```

---

## 3. Component 1 — Pre-Call Lookup Workflow

**Workflow:** `Knight Law - Pre Call Workflow` (id `IfnL95bXqblx8SwC`, n8n on heroflow).
**Purpose:** When a call comes in, Retell's **inbound webhook** posts the caller's number here *before Alice speaks*. This workflow looks the caller up in GHL and returns everything Alice needs as **dynamic variables**, so she starts the call already knowing who they are and what's missing.

### Flow (planned)

1. **Webhook** *(exists)* — receives Retell's inbound payload (caller `from_number`).
2. **Constant** *(exists)* — `location_id`, `api_version`.
3. **Get Contact** *(exists)* — `GET /contacts/?locationId&query={from_number}`.
4. **Pick Contact** *(new)* — resolve **0 / 1 / many** (see edge cases). Match on **last-10-digits**, prefer the record that has a `Lead Status` and/or `Salesforce Record ID`, else most recently updated.
5. **Map Fields** *(new)* — build a lookup from the contact's `customFields[]` array (which only contains fields that *have* a value), normalize Yes/No → the values the agent/classifier expect, and assemble the dynamic-variable contract (§6).
6. **Respond to Webhook** *(new)* — return the Retell inbound shape:
   ```
   { "call_inbound": { "dynamic_variables": { …§6… } } }
   ```

### Output contract → Retell

The response feeds §6 dynamic variables into Alice. If lookup fails or times out, return `contact_found="false"` and empty fields so Alice degrades gracefully to a generic intake (§8).

---

## 4. Component 2 — Retell "Alice Inbound" conversation flow

A **new front-end router** that **reuses the existing outbound intake nodes** (same classify code node, same make enum, same one-at-a-time contact confirmation, same voice + EN/ES settings). Build a dedicated *inbound* flow because the entry logic differs; share the qualification block.

### 4.1 Top-level router (on `lead_status`)

| `lead_status` | Alice's behavior | Terminal |
|---|---|---|
| **Incomplete Lead** | Greet by name, "we spoke earlier — let's pick up where we left off." **Resume** intake, skipping already-filled fields, ask only what's missing → re-classify | Route by new status ↓ |
| **Retainer Lead** | Greet by name, confirm the file is with the team, answer a brief FAQ. **No re-intake, no re-send.** | **Warm transfer** (hours-gated) |
| **Non-Retainer Lead** | Greet by name, confirm next step (consultation), brief FAQ. **No re-intake.** | **Warm transfer** (hours-gated) |
| **Bad Lead** | Look at `bad_lead_reason`. **Reversible** (`not_in_possession`, ambiguous/misclass) → re-check that one point; if it flips, continue intake. **Irreversible** (`vehicle_year`, out-of-state) → explain, give callback #. | Re-route if flipped; else polite close |
| **Opt-Out Consent** | Caller initiated, so handle politely; re-engage **only if they ask**; otherwise respect opt-out and close | Close (re-engage only on request) |
| **(blank / not found)** | Greet generically, run the **full** intake from scratch | Route by status |

### 4.2 Resume logic ("memory retention")

The intake questions map 1:1 to GHL custom fields (§6). On resume, each question node carries a **guard**:

> *If the field's dynamic variable is already set → quick-confirm or skip. If empty → ask.*

- Alice opens with a short recap: *"Last time you told us it's a 2021 BMW X5, bought in California — I just need a couple more details."*
- The **deterministic classify code node** runs on whatever is present (the same node the outbound C3 fix touched — it disqualifies on possession before requiring a year, etc.).
- **Corrections allowed:** if the caller changes a prior answer, the new value wins and re-classification re-runs.

**Design choice to confirm:** quick-confirm the **vehicle + CA** on resume (safer) but silently trust the rest (less friction). Defaulting to that unless told otherwise.

### 4.3 Terminal actions

- **Warm transfer** → Knight Law intake (number TBD — placeholder `+1XXXXXXXXXX`). **Hours gate:** Mon–Fri 8a–8p PT only.
  - Transfer **fails** (no answer / busy) → fall back to booking a callback (don't dead-end).
- **Book callback** → reuse `send_consultation_link` (the existing booking-link function). Used after-hours and as the transfer-fail fallback.
- **Polite close** → for irreversible bad leads / opt-outs: courteous explanation + callback number `(310) 552-2250`, then `end_call`.

### 4.4 Reused settings

Same voice, same English/Spanish auto-switch, same FAQ "answer-then-revert" global, same human-request global as the outbound conversation-flow agent. Inbound `start_speaker = agent` (Alice greets first). **Outbound-only post-call analysis** stays; inbound adds its own post-call webhook (Component 3).

---

## 5. Component 3 — Post-Call Workflow (reuse + guards)

**Reuse the existing GHL "Post Retell" workflow** (find_contact → update fields → branch by Lead Status → Zapier `02.01 Post Call` → Salesforce update / DocuSign). It is already status-driven, so a completed inbound intake flows through unchanged. **Two guards to add:**

1. **DocuSign / retainer idempotency** — a returning **Retainer** re-entering the retainer branch would **re-send the fee agreement** and recreate the "won" opportunity. Guard: skip the retainer Zapier webhook + DocuSign if the lead is **already** "HF Retainer Sent" (or `Lead Status` already Retainer on entry and nothing changed). Confirm-status-and-transfer should **not** trigger a second envelope.
2. **Inbound source tag** — tag inbound-completed contacts (e.g. `voice-inbound`) separately from outbound `voice`, for reporting and to distinguish call direction.

Everything else (Incomplete → follow-up workflow, Non-Retainer EN/ES follow-up + opportunity, Bad → lost opportunity + DND, Opt-Out → remove-from-all) is inherited as-is.

---

## 6. Field map & dynamic-variable contract

GHL custom fields (`model: contact`, location `vHHnJlFVorkeBvqgaqqA`). The pre-call workflow reads these by **ID** out of `contact.customFields[]` and exposes them as dynamic variables; the post-call workflow writes the same fields back.

| Custom field ID | GHL field name | → Dynamic variable | Notes |
|---|---|---|---|
| `KXtfUXZAiVchURizdzxW` | Lead Status | `lead_status` | Router key. Values: Incomplete / Retainer / Non-Retainer / Bad Lead / Opt-Out Consent |
| `Iw4Gtrz6t4It6itTdWY4` | Lead Language | `lead_language` | English / Spanish — seeds greeting |
| `Nut24vIH6AHbXoKyhX9M` | Salesforce Record ID | `salesforce_record_id` | Needed so post-call updates the right SF lead |
| `xcRLpJKMV7rBAylI41Ph` | Bad Lead Reason | `bad_lead_reason` | Drives reversible-vs-irreversible re-check |
| `iC8F774s9S7zzpWJzy4s` | Are you having issues with your vehicle? | `having_issues` | |
| `8hrW19JucZMrvkaInbdq` | Purchased/leased from a CA dealership? | `ca_purchase` | |
| `psMc0nlcBlb4jrgtyT6t` | Still in possession of the vehicle? | `in_possession` | **Normalize** Yes/No → the boolean the classifier expects |
| `Xy9KVmiPlkh1udw4n5Je` | Year of the vehicle | `vehicle_year` | |
| `gswt6GWEUgPVhuveoZBS` | Vehicle's make | `vehicle_make` | Aligns with existing agent `dv.vehicle_make` |
| `QEnIM80S2QQuftwM1XuF` | Model of the vehicle | `vehicle_model` | |
| `ulAGG4Jq1Kp9JnRU3h5v` | New or used? | `purchase_new_used` | |
| `BA8l2mqhsLsYcJBQjMT6` | Certified pre-owned (CPO)? | `is_cpo` | |
| `HAOzCiaJ9mUASuHuoESO` | Purchase Condition | `purchase_condition` | Combined new/used/CPO summary |
| `TRZwb9rqTG1eNhiDt6AH` | Visited a dealership for repair? | `dealership_repair` | |
| `QN83VkI4y67Iokp4maRp` | Owner / signed the sales contract? | `is_owner` | |
| `ivMJsGAleiefhcTwS9gE` | conversation_summary | `prior_summary` | Context for Alice's recap (LARGE_TEXT) |
| `1YS4xhy9VWZwvx0TcnbO` | Transcript of the Call | *(optional)* `prior_transcript` | Heavy; pass a trimmed summary instead if size is an issue |
| `uAAqJPf48BMiZcydoKQs` | Number of Calls Made | *(optional)* `num_calls_made` | |

**Standard (non-custom) fields:** `caller_name` ← `contactName`/`firstName`+`lastName`, `caller_phone` ← `phone`, `caller_email` ← `email`, `contact_id` ← `id`.

**Plumbing variable:** `contact_found` (`"true"`/`"false"`) — tells Alice whether to greet by name or fall to generic intake.

> **Important:** `customFields[]` only includes fields that have a value, so any mapping must default missing IDs to empty — never assume a field is present.

---

## 7. Lead-status decision matrix (end-to-end)

| Status in | Re-intake? | Re-classify? | Transfer? | Writes back via post-call |
|---|---|---|---|---|
| Incomplete | Resume (missing only) | Yes | If terminal = Ret/Non-Ret (hours) | New terminal status → SF + (DocuSign if newly Retainer) |
| Retainer | No | No | **Yes** (hours) | **No new DocuSign** (idempotency guard) |
| Non-Retainer | No | No | **Yes** (hours) | No status regression |
| Bad — reversible | Re-check 1 point | If flips | Only if it flips to Ret/Non-Ret | New status if flipped |
| Bad — irreversible | No | No | **No** | No change (already Bad/lost) |
| Opt-Out | Only if asked | — | Only if re-engaged | Respect opt-out; no auto re-add |
| Blank / not found | Full | Yes | Per terminal | Per terminal status |

---

## 8. Edge cases & handling

**Identity / lookup**
- **Phone doesn't match the record** (different/spouse's phone, withheld caller-ID, formatting). The "always in SF" guarantee covers *existence*, not *that they call from the stored number*. → **Not-found path:** ask name / number on file, or fall to generic intake. Match on **last-10-digits**, not exact E.164.
- **Anonymous / withheld caller-ID** → empty `from_number` → not-found path.
- **Multiple contacts on one phone** (dupes) → Pick Contact prefers the record with a `Lead Status` / `Salesforce Record ID` / most recent.

**Resume correctness**
- **Yes/No normalization** — stored answers are text ("Yes"/"No"); the classifier expects booleans/specific values. Normalize in Map Fields.
- **Partial vehicle** (make but no year) — handled by the deterministic classifier (possession disqualification fires before the year requirement; reprompt only when a year is genuinely needed).
- **Caller changes a prior answer** — new value wins; re-classify.

**Returning completed leads**
- **Duplicate DocuSign / opportunity** on a returning Retainer → idempotency guard (§5).
- **Non-Retainer with new qualifying facts** (e.g. now confirms they're the owner) → allow a re-qualify branch rather than locking them.

**Transfers**
- **After-hours** (outside Mon–Fri 8a–8p PT) → no live transfer → finish/resume intake + book callback.
- **Transfer fails** (no answer/busy) → fall back to callback booking.
- **Transfer destination** still TBD (placeholder).

**Reliability**
- **Pre-call webhook latency/timeout** → Alice must start even if variables don't arrive → generic intake fallback (consistent with the existing caller-lookup latency design).
- **Language mismatch** — stored `lead_language` seeds the greeting; live detection (ES auto-switch) wins if the caller speaks the other language.

**Privacy**
- Phone match ≠ identity proof. Before sharing case specifics with a **Retainer**, a light name confirmation is prudent (low-sensitivity domain, but worth a beat). Family-member-on-behalf is possible.

---

## 9. Open items / placeholders (need from client)

1. **Warm-transfer number + department(s)** for Knight Law intake — currently placeholder `+1XXXXXXXXXX` (only the callback line `(310) 552-2250` is known). *(Client will share later.)*
2. **Resume confirmation depth** — confirm vehicle + CA on resume vs. trust all? (Defaulting to confirm-vehicle+CA.)
3. **Inbound number** — which Retell phone number is the inbound line, and is the inbound webhook to be pointed at Component 1.
4. **DocuSign idempotency rule** — confirm the exact "already sent" signal to gate on (SF `HF Retainer Sent` vs. GHL Lead Status on entry).

---

## 10. Build sequence (when approved)

1. **Component 1** — finish the pre-call lookup workflow: Pick Contact + Map Fields + Respond-to-Webhook (dynamic-variable contract §6). Robust phone match + not-found path.
2. **Component 2** — build "Alice Inbound" conversation flow: status router, resume guards on reused intake nodes, terminals (transfer hours-gate / book callback / close). Version-suffixed JSON for import.
3. **Component 3** — add the two post-call guards (DocuSign idempotency, inbound tag) to the existing workflow.
4. **Test** — Retell simulation cases per status (incomplete-resume, returning-retainer-transfer, bad-reversible-flip, bad-irreversible-close, after-hours-callback, phone-not-found).

---

*Reference data: `custom-fields-schema.json` (field IDs), `contact-output.json` (sample lookup), `outbound-pre-call-workflows.md` + `outbound-post-call-workflows.md` (existing loop this plugs into).*
