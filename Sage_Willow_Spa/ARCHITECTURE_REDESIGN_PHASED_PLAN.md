# Aria + n8n + Wix Bookings — Architectural Review & Phased Redesign Plan

> **Scope:** Sage & Willow Spa voice-agent stack (Retell single-prompt agent "Aria" → n8n "Retell AI ↔ Wix Bookings | Production v2" → Wix Bookings REST API).
> **Goal:** Eliminate the failure modes where the AI sends incorrect / hallucinated Wix identifiers, by moving booking intelligence from the agent into the backend.
> **Status:** Proposal — phased, each phase independently shippable.

---

## Table of contents

1. [Current architecture](#1-current-architecture-what-is-actually-happening)
2. [Failure modes you're hitting (and why)](#2-failure-modes-youre-hitting-and-why)
3. [The redesign — stateless, no tokens, no cache](#3-the-redesign--thin-agent--fat-backend-with-opaque-tokens)
4. [Wix-side hardening (independent of agent redesign)](#4-wix-side-hardening-independent-of-agent-redesign)
5. [Phased implementation plan](#5-phased-implementation-plan)
6. [Risk callouts](#6-risk-callouts)
7. [Summary — what this buys you](#7-summary--what-this-buys-you)
8. [Validation appendix — plan vs. current files](#8-validation-appendix--plan-vs-current-files)
9. [Sources](#sources)

---

## 1. Current architecture (what is actually happening)

```
┌────────┐    tool call    ┌─────────────────┐    REST    ┌──────────┐
│  Aria  │ ──────────────► │ n8n (Prod v2)   │ ─────────► │ Wix v2   │
│ (LLM)  │ ◄────────────── │ Switch+Validate │ ◄───────── │  APIs    │
└────────┘   tool result   └─────────────────┘            └──────────┘
```

### What the agent currently owns

- Service / variant disambiguation (matches caller phrase → catalog item, picks `variantId` by duration)
- Slot disambiguation (echoes back the exact `scheduleId`, `startDate`, `endDate` from `get_slots`)
- Therapist disambiguation (echoes `staffId` from the slot's `availableTherapists`)
- Add-on plumbing (passes `{id, groupId}` per add-on)
- Conditional shape rules ("omit `variantId` if no `pricingVariants`")
- Multi-turn ID memory (UUIDs returned from one tool must survive verbatim into the next tool call, possibly turns later)

### What n8n currently owns

- Header-based tool routing (the `Route by Tool` Switch node fans out to 9 tool sub-flows by reading the `tool` HTTP header)
- Argument validation per tool (separate `Validate: …` Code nodes)
- Wix REST calls
- Contact upsert (search-then-create)
- Response formatting (slim down Wix payloads before returning to agent)

### Why this is the root cause of the failures

This is a **fat-agent / thin-backend** split. The agent is asked to behave like a deterministic transport layer for 36-character UUIDs and strict ISO-8601 strings across multiple conversational turns. LLMs are bad at that — that is the entire problem.

---

## 2. Failure modes you're hitting (and why)

### 2.1 LLM ID-handling failures (the dummy / mangled values)

LLMs are unreliable at echoing 36-char UUIDs and complex compound structures across multiple turns. Concretely in the current tool set:

| Field the agent must echo | Source | Observed failure |
|---|---|---|
| `serviceId` | `get_services` | Truncation, hallucination |
| `variantId` | `get_services` (nested under `pricingVariants`) | Picked from wrong service; passed when service has none; omitted when required |
| `scheduleId` | `get_slots` | Stale (older slot from same call), mangled |
| `staffId` (booking) | `get_slots.availableTherapists[].staffId` | Mismatched to chosen therapist; sometimes the *name* is sent in this field |
| `startDate` / `endDate` | `get_slots` | Format drift (`T15:0:0.000`), timezone-stripping accidents |
| `addOns[].id` + `groupId` | `get_services.availableAddOns[]` | `groupIds` is an array but the schema expects one `groupId` — agent has to pick element 0 |
| `bookingId` + `revision` | `get_booking` | Revision sometimes a number, sometimes a string in tool args |

The agent's prompt has 20+ rules dedicated to compensating for this ("Only pass documented parameters", "pass `variantId` only when service has `pricingVariants`", "Trust the server's `dayOfWeek`"). **Every such rule is a load-bearing prayer.**

### 2.2 Wix-specific traps your current pipeline doesn't defend against

From the official Wix Bookings docs (sources listed at the end of this document):

1. **Race condition between `time-slots` query and `bookings/create` is officially documented.** Wix recommends "always call Time Slots V2 immediately before Create Booking, and pass the full `availabilityEntries.slot` object verbatim." Your current code reconstructs the slot from scattered fields the agent threaded through the conversation — this is *exactly* what Wix tells you not to do.
2. **Slot availability is policy-based, not a hold.** `bookable: true` doesn't reserve anything. Two parallel callers can both book the same slot; Wix sets `doubleBooked: true` on one and requires manual cleanup.
3. **`Confirm Booking` does NOT re-validate availability.** So if a stale slot slips through `Create Booking`, you'll happily confirm a conflict.
4. **`flowControlSettings.withoutPayment` is not in the current public schema** — your workflow uses it (`Wix: Create Booking` node). It may still work today but is undocumented and could break silently.
5. **No `Idempotency-Key` support on Wix v2.** A retry on a transient 5xx may create duplicate bookings.
6. **Resource type IDs and locationIds are per-site, but hardcoded in your workflow** (`1cd44cf8-756f-41c3-bd90-3e2ffcaf1155` and `a345d3c7-2a89-4816-ad3a-277ea40730a7` appear in multiple places). Spa-portable code can't ship like this.
7. **428 Failed Precondition has 12 distinct error codes** behind it. The workflow currently treats every Wix error the same ("Error booking service") and gives the agent a generic message — but most 428s require *refetch + retry*, not blind retry.
8. **Add-ons endpoint your workflow uses (`manage.wix.com/_api/add-ons-service/v1/add-ons/{id}`) is the legacy internal path.** The public path is now under `wixapis.com/_api/bookings/v2/...`. The legacy path can break without notice.
9. **Timezone double-think.** Wix Bookings has TWO date fields per slot: top-level `startDate` (UTC) and `bookedEntity.slot.startDate` (local + `timezone` string). Around DST the two diverge by an hour. Your workflow normalizes by stripping `Z` and timezone suffixes (`Validate: Slots Args` code node) — that works today but is fragile.

### 2.3 Workflow-level fragility

- **Contact lookup branch is brittle.** `Wix: Search Contact1` → `Format: Contact Response1` → `If: Contact Found` → either `Wix: Create Booking` directly (with `Wix: Search Contact1.contacts[0].id`) or `Wix: Create Contact` then `Wix: Create Booking`. The `book_appointment` jsonBody references both `Wix: Create Contact` and `Wix: Search Contact1` via `isExecuted` — but Wix's "contact not found" success path returns `contacts: []`, so `.contacts[0].id` would throw if the branch logic ever drifts.
- **`Format: Time Slots Response` discards the slot's identity.** The code maps Wix's response into a slimmed object but doesn't preserve the original Wix `slot` blob. To send the full slot verbatim to `Create Booking` (Wix's official recommendation), you'd need to keep that blob — currently impossible.
- **No idempotency or retry semantics.** A flaky network = duplicate booking risk.
- **No persistent state across tool calls within a single call.** Every tool call is independent; the agent is the only memory.
- **Hardcoded `resourceTypeId` and `locationId`** in `Wix: Query Time Slots`, `Wix: Create Booking`, and `Wix: Reschedule Booking` — not portable across sites.
- **Generic error fallbacks ("Error getting slots", "Error booking service")** discard Wix's `applicationError.code` and `details`, so neither the agent nor ops can diagnose specific failures.

---

## 3. The redesign — "Thin agent / Fat backend with opaque tokens"

### 3.1 Guiding principles

1. **The agent only handles human-readable strings.** No UUIDs. No full ISO timestamps. The agent passes `serviceName`, `date` (`"2026-05-30"`), `time` (`"3:00 PM"`), `therapistName`, `phone` — strings LLMs handle reliably.
2. **No external storage. No tokens. No cache.** n8n is fully stateless across tool calls. Each tool call re-queries Wix live and re-resolves whatever IDs it needs from the human-readable inputs the agent supplied.
3. **Slot objects are preserved verbatim within a single n8n execution.** Because n8n re-queries time-slots immediately before `Create Booking` (which is Wix's documented recommendation anyway), it has the fresh slot blob in hand and passes it verbatim — no reconstruction.
4. **All Wix IDs (`serviceId`, `variantId`, `scheduleId`, `staffId`, `resourceTypeId`, `locationId`, `bookingId`, `revision`) are resolved live, server-side.** The agent never sees them.
5. **Idempotency / double-book defense uses Wix as the source of truth** — before `Create Booking`, n8n does a quick `Query Bookings` filtered by phone+startDate+serviceId; if a matching CREATED/CONFIRMED booking already exists, return that instead of creating a duplicate.

### 3.2 New tool surface (agent-facing contract)

| Tool | Input the agent sends | What it gets back |
|---|---|---|
| `list_services` | (none, or `serviceName` fuzzy) | `[{ name, description, prices: "60min: $90, 90min: $130", addOns: ["Aromatherapy", ...] }]` — **no IDs** |
| `find_slots` | `serviceName`, `durationMinutes?`, `dateRange`, `timeOfDay?`, `therapistName?`, `therapistGender?`, `earliestFirst?` | `[{ date: "2026-05-30", time: "3:00 PM", duration: 60, therapists: ["Lily","Rocky"] }]` — **no IDs, no full ISO timestamps** |
| `book` | `serviceName`, `durationMinutes`, `date`, `time`, `therapistName?`, `firstName`, `lastName`, `phone`, `addOnNames?: ["Aromatherapy"]` | `{ confirmed: true, summary: "Signature 1hr, Sat May 30 3PM with Lily, $90" }` |
| `find_my_bookings` | `phone?` (defaults to caller ID) | `[{ serviceName, date, time, durationMinutes, therapistName }]` — **no booking ID** |
| `cancel` | `phone`, `date`, `time` (enough to disambiguate which booking) | `{ canceled: true }` |
| `reschedule` | `phone`, `date`, `time` (existing) + `newDate`, `newTime`, `newTherapistName?` | `{ rescheduled: true, summary: "..." }` |
| `flag_callback` | (unchanged) | (unchanged) |

Everything Wix-specific — `serviceId`, `variantId`, `scheduleId`, `staffId`, `revision`, the slot blob, `resourceTypeId`, `locationId`, `bookingId` — is resolved **live, server-side**, every tool call. n8n is stateless across calls.

The agent's system prompt collapses from "remember and pass these 7 UUID fields exactly as returned" to "ask the caller, pass the human-readable details back."

### 3.3 New backend topology (stateless)

```
┌────────────┐
│   Aria     │ Passes human strings: serviceName, date, time, therapistName, phone
└─────┬──────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  n8n  (stateless across tool calls)                          │
│                                                              │
│  Per request:                                                │
│   1. Resolve serviceName + durationMinutes → serviceId,      │
│      variantId   (live: Wix Query Services)                  │
│   2. Re-query time-slots for the requested date/time         │
│      (live: Wix Time Slots V2) — finds the matching slot     │
│      blob fresh                                              │
│   3. For modifications: look up booking by phone + date/time │
│      (live: Wix Query Bookings) — gets bookingId+revision    │
│   4. Execute the requested Wix operation, passing the fresh  │
│      slot blob verbatim                                      │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
   ┌──────────┐
   │  Wix v2  │
   └──────────┘
```

> **No cache. No tokens. No external store. No Redis.** Every tool call is an independent stateless transaction. The agent's human-readable inputs are sufficient to re-resolve everything Wix needs.

### 3.4 Two non-negotiable behavioral changes

1. **Preserve the full Wix `slot` object within the booking execution.** Because n8n re-queries time-slots inside the `book` execution, it has the fresh slot blob in hand. Pass that blob verbatim into `Create Booking` (no field-by-field reconstruction). This is what Wix's docs explicitly recommend to avoid the documented race condition.
2. **Implement a "refetch on 428, retry once" pattern.** On any Wix 428 from `Create Booking`, automatically:
   - Re-query time-slots for that exact serviceId/staffId/window
   - If the same start time is still bookable, retry with the fresh slot
   - If not, return `slot_no_longer_available: true` + 2–3 nearby alternatives (the agent already knows how to offer alternatives)

### 3.5 What the agent's prompt loses

These prompt sections become server-side concerns and can be deleted:

- "pass `variantId` only when the service has `pricingVariants`"
- "Only book a time that `get_slots` actually returned"
- "Pass `addOns` only if `get_services` returned them" / `{id, groupId}` plumbing
- "Pass the `resourceId` from get_staff as `staffId` downstream"
- Most of "Tool-calling discipline: never invent IDs"
- "For RESCHEDULES where the caller said 'same time,' pass `timeOfDay` matching..."

What the prompt keeps: personality, escalation rules, the call flows themselves, pronunciation, hearing-the-caller accents handling. All the genuinely-AI work.

---

## 4. Wix-side hardening (independent of agent redesign)

These wins ship regardless of whether you do the token redesign:

1. **Stop using `flowControlSettings.withoutPayment`.** Use the documented two-step `Create Booking` (status `CREATED`) → `Confirm Booking` flow — which the workflow already does. Just remove the undocumented flag from the create body.
2. **Discover `resourceTypeId` and `locationId` dynamically.** Look them up via the Resources / Locations APIs at request time (or once at workflow load and store in n8n static data — but do not hardcode site-specific UUIDs in the workflow JSON).
3. **Switch add-ons fetch from `manage.wix.com/_api/add-ons-service/v1/add-ons/{id}`** to the public `wixapis.com/_api/bookings/v2/...` add-ons endpoints.
4. **Always log `applicationError.code`** from Wix responses — the 12-code 428 set is collapsed in the public docs; you learn the real mapping from production traces.
5. **Normalize phone to E.164 once at the front door** (libphonenumber-style) — the current code passes whatever Retell sent. Wix Contacts dedup is byte-exact on the `phone` field.
6. **Add a `dayOfWeek` calculation guard.** Already done in `Format: Get Booking Response` and `Format: Reschedule Response` — extend to all booking-returning paths so the agent never computes day-of-week.

---

## 5. Phased implementation plan

> Each phase is independently shippable and provides standalone value. **Don't do them all at once.**

---

### Phase 0 — Instrumentation (3–5 days)

**Goal:** stop guessing which failures matter.

**Tasks:**

- Add a "Log: Tool Call" branch after `Parse Retell Payload` that fires on every request. Persist `{call_id, tool, args, ts}` to a Postgres/Supabase table.
- Add a "Log: Tool Response" branch before every `Respond:` node. Persist `{call_id, tool, success, errorCode, wixApplicationErrorCode, ts}`.
- Capture the raw Wix response body on every error (today the error-output `Error: …` nodes throw away the response).
- Build a one-page report: tool call counts, failure rates, top 5 Wix error codes, top 5 LLM arg-validation failures.

**Acceptance:** After one week of data, you can answer the question: "of failed bookings, what % are ID hallucinations vs. slot races vs. validation vs. Wix errors?"

---

### Phase 1 — Wix-side hygiene (1 week)

**Goal:** kill the easy, AI-independent issues.

**Tasks:**

- Replace `manage.wix.com/_api/add-ons-service/v1/add-ons/{id}` (current `Wix: Get Add-ons` node) with the public `https://www.wixapis.com/_api/bookings/v2/add-ons/{id}` endpoint. Verify the response shape matches before swapping — the public path may nest the add-on under `addOn` instead of returning it at root.
- Remove `flowControlSettings.withoutPayment` from the `Wix: Create Booking` jsonBody. Keep the `Create Booking` → `Confirm Booking` two-step that's already in the workflow.
- **`resourceTypeId` dynamic discovery.** Add a one-time-per-workflow-load node that calls `POST https://www.wixapis.com/_api/bookings/v2/resources/query` with `{ "query": { "paging": { "limit": 1 } } }`. The first returned resource has a `resourceType.id` field — store it in n8n static data (key: `staff_resource_type_id`). All three places that currently hardcode `1cd44cf8-756f-41c3-bd90-3e2ffcaf1155` (`Wix: Query Time Slots`, `Wix: Create Booking`, `Wix: Reschedule Booking`) read from this key instead.
- **`locationId` dynamic discovery.** Add a node calling `GET https://www.wixapis.com/locations/v1/locations`. Use the location with `default: true` (or the first one). Store as `default_location_id`. Replace the hardcoded `a345d3c7-2a89-4816-ad3a-277ea40730a7` in `Wix: Create Booking` and `Wix: Reschedule Booking`.
- E.164-normalize the `phone` arg in `Validate: Booking Args`, `Validate: Get Booking Args`, `Validate: Get Contact`, `Validate: Flag Callback Args`. Use a small regex-based normalizer (`+1` prefix for US numbers, strip non-digits). **This is a prerequisite for Phases 4 and 5** — Wix Contacts dedup is byte-exact on the phone field.
- Improve error surfacing: in every `Format: …` Code node, extract `data.applicationError?.code` and `data.details` and include them as `wix_error_code` and `wix_error_detail` in the response. The current `Error: Get Slots`, `Error: Create Booking`, etc. nodes discard these — replace them with formatters that pass the Wix error through to the agent.

**Acceptance:** Zero hardcoded site-specific UUIDs in workflow JSON; structured `wix_error_code` flowing back to the agent for every failure path; add-ons fetched via supported `wixapis.com` path; E.164 normalization confirmed by inspecting logged tool call args.

---

### Phase 2 — Server-side service-name resolution + staff resolution (1 week)

**Goal:** the agent stops needing `serviceId`, `variantId`, and `staffId`. Resolution happens server-side, **live** (no Wix-data caching in this iteration).

**Tasks:**

- Add an internal `resolve_service(name, durationMinutes?)` helper inside n8n — a sub-workflow or shared Code node that:
  - Calls Wix Services V2 — prefer `search-services` (Wix-side fuzzy match) over `query-services` + client-side filtering. Fall back to `query-services` if `search-services` is unavailable.
  - For services that returned `payment.rateType === 'VARIED'`, additionally calls `GET /_api/bookings/v2/services/service-options-and-variants/by-service-id/{serviceId}` (same as current `Wix: Get Pricing Variants` node) to load variants.
  - If `durationMinutes` is provided and the service has variants, picks the variant whose `choices[0].duration.minutes === durationMinutes`; returns `{ serviceId, variantId, addOns[], priceUsd, durationMinutes, rateType }`.
  - If no `durationMinutes` and the service has variants, returns all variants so the agent can be told the price options.
  - For FIXED-price services (no variants — e.g. 30-Minute Focus), returns `{ serviceId, variantId: null, … }`. n8n omits `variantId` from Create Booking entirely (this is what current workflow already does).
  - Returns a structured error (`service_not_found`, `duration_not_available`) if no match — agent can confirm with the caller.
- Add an internal `resolve_staff(name?, gender?)` helper:
  - If `name` is provided, fuzzy-match against `Wix: Query Staff Members` (case-insensitive substring match on `name`); return `staffId`.
  - **`therapistGender` mapping stays in the agent's prompt** ("male" → "Rocky", "female" → "Lily"). Wix doesn't expose a structured gender field on staff members, so n8n can't resolve gender → name reliably. The agent's prompt already encodes this mapping; keep it there. n8n only ever receives a name.
  - On no match, return `staff_not_found` — agent then offers the real options or transfers.
- **Decision on `get_staff` tool:** *remove it* from the agent's tool list. The agent's prompt already lists the bookable therapists (Rocky and Lily) by name and gender; it doesn't need a live roster call. If the roster grows beyond what fits in the prompt, re-introduce `get_staff` later, but strip all IDs from its response.
- Rewrite `get-services` n8n route so its response to the agent is **human-readable only**: service names, descriptions, price-by-duration strings, add-on names. No `serviceId`, no `variantId`, no `groupId` in the response.
- Rewrite `get-slots` n8n route to accept `serviceName` + `durationMinutes` + optional `therapistName` from the agent (instead of `serviceId` + `staffId`). Internally calls `resolve_service` and `resolve_staff` then proceeds with the Wix time-slots query.
- Update Aria's tool schemas to drop `serviceId`, `variantId`, `staffId`. Replace with `serviceName` (keep the existing enum hint), `durationMinutes`, `therapistName`. Drop `get_staff` from `general_tools`.
- **Bilingual handling:** Spanish service phrasings (e.g. "masaje sueco" → "Swedish Massage") are translated by the agent before passing the tool call — the agent's prompt already speaks Spanish per its bilingual rule. n8n's `resolve_service` receives the English canonical name. Add one prompt rule: "When the caller names a service in Spanish, translate to the English canonical name in the enum before calling the tool." Keep the resolver English-only.

**Acceptance:** Agent never sees a raw Wix ID in any tool response. `serviceId` / `variantId` / `staffId` no longer appear in any tool's input schema. `get_staff` removed from agent.

> **Deferred (not in this iteration):** caching the resolved catalog. If `get_services` / `find_slots` latency or Wix rate limits become an issue later, add a cache layer behind `resolve_service` — but keep the agent-facing contract identical so the upgrade is invisible to Aria.

---

### Phase 3 — Stateless slot lookup at booking time (2 weeks — biggest lift, biggest payoff)

**Goal:** the agent stops handling `scheduleId`, `startDate`, `endDate`, `staffId`. n8n re-queries Wix live each call — no cache, no tokens, no store.

**Tasks:**

- Add a shared `parseTimeLabel(time)` helper in n8n that converts `"3:00 PM"` → `{ hour: 15, minute: 0 }`. Pair it with the existing `formatTimeLabel` (in `Format: Time Slots Response`) so the same string ↔ time conversion is used both directions.

- Add a shared `composeLocalStartDate(date, time)` helper that produces Wix's format `"2026-05-30T15:00:00.000"` from the agent's `date` + `time`. This is the format Wix returns as `localStartDate` and accepts in `bookedEntity.slot.startDate`.

- Rewrite `Format: Time Slots Response` (the `find_slots` response shape) to return only human-readable fields: `[{ date: "2026-05-30", time: "3:00 PM", duration: 60, therapists: ["Lily","Rocky"] }]`. Strip `scheduleId`, `startDate`, `endDate`, `staffId` from the agent-facing payload.

- Rewrite `book_appointment` n8n route. New input shape:
  ```
  { serviceName, durationMinutes, date, time, therapistName?,
    firstName, lastName, phone, addOnNames?: string[] }
  ```

  Implementation steps inside the n8n execution:
  1. Resolve `serviceName` + `durationMinutes` → `serviceId`, `variantId`, `addOnCatalog[]` via `resolve_service` (Phase 2).
  2. Resolve `therapistName` → `staffId` via `resolve_staff` (Phase 2), or leave null for "any therapist."
  3. Compose `localStartDate` via `composeLocalStartDate(date, time)`. Compute a same-day window (`date` 00:00 → `date` 23:59) for the time-slots query.
  4. Call `Wix: Query Time Slots` live with `serviceId`, the date window, `customerChoices.durationInMinutes` (for VARIED services), and (if therapist resolved) `resourceTypes: [{ resourceTypeId: <from Phase 1>, resourceIds: [staffId] }]`. This is the **fresh slot blob** Wix recommends using.
  5. From the response, find the `availabilityEntries[i]` whose `slot.localStartDate === localStartDate`. If none → return `{ success: false, reason: "slot_no_longer_available", alternatives: [<2-3 nearby times>] }`.
  6. If `therapistName` was provided, verify the chosen entry's `availableResources` contains that staffId; if not, fall back to alternatives.
  7. Resolve `addOnNames` (case-insensitive) → `[{ id, groupId }]` against `addOnCatalog[]` from step 1. **If any selected add-on has `durationInMinutes > 0`, re-query time-slots with `customerChoices.addOnIds: [...]` to confirm the slot still fits the extended duration** — Wix's slot length depends on the add-ons selected. If the slot is no longer available with add-ons, surface that to the agent (it can offer to drop the add-on or pick a different time).
  8. Contact upsert: reuse the existing `Wix: Search Contact1` → (if found) use returned `contactId`, else `Wix: Create Contact` then use new `contactId`. **Fix the current branch fragility:** in `Format: Contact Response1`, when `contacts: []`, explicitly set `found: false` so the `If: Contact Found` branch is reliable (today the `.contacts[0].id` path can throw if the success branch is reached with an empty array).
  9. **Pass the matched slot blob verbatim** into `Wix: Create Booking` `bookedEntity.slot` (Wix's recommended pattern — `availabilityEntries[i].slot` is shape-compatible with `bookedEntity.slot`). Pass `variantId` only when non-null. Use the discovered `resourceTypeId` and `locationId` from Phase 1.
  10. After Create succeeds (status `CREATED`), call `Wix: Confirm Booking` (unchanged from current workflow).
  11. On 428 Failed Precondition, refetch slots once → if same time still bookable, retry once with the fresh blob; else respond with alternatives.

- Update Aria's system prompt and tool schemas to drop all ID-handling and slot-echoing rules. The agent passes only the strings it heard from the caller and the strings it read out from `find_slots`.

- **Remove `response_variables` mappings for ID fields** from `book_appointment`, `get_booking`, `cancel_booking`, `reschedule_booking` in the Retell agent JSON. These currently surface `new_booking_id`, `booking_id`, `booking_revision`, `booking_service_id`, `booking_schedule_id`, `booking_staff_id`, etc. as dynamic variables — the agent should not be able to reference them in subsequent turns at all. Replace with only the human-readable fields (`confirmed_start`, `booking_service_name`, `booking_day_of_week`, `booking_duration_min`).

**Acceptance:** Book-failure rate from "agent sent bad UUIDs" drops to ~0. Slot-race failures handled invisibly via auto-refetch. n8n holds no state between tool calls. Agent JSON has no `*_id` / `*_revision` in `response_variables`.

---

### Phase 4 — Stateless booking lookup for find/cancel/reschedule (1 week)

**Goal:** the agent stops handling `bookingId` + `revision`. No booking cache — n8n re-queries Wix on every modification.

**Tasks:**

- `find_my_bookings`: input `{ phone? }` (default to caller ID). Implementation reuses the existing chain: `Wix: Search Contact` by phone → if found, `Wix: Query Bookings` filtered by `contactDetails.contactId` (same filter the current `Wix: Get Booking (by Contact)` node uses). Strip `bookingId`, `revision`, `serviceId`, `scheduleId`, `staffId` from the response. Return only `[{ serviceName, date, time, durationMinutes, therapistName }]`.

- `cancel`: input `{ phone, date, time }`. Implementation:
  1. Look up bookings by phone (same chain as `find_my_bookings`).
  2. Compose `localStartDate = composeLocalStartDate(date, time)`. Filter the returned bookings where `bookedEntity.slot.startDate === localStartDate`.
  3. If 0 matches → `{ success: false, reason: "booking_not_found" }`. If exactly 1 → proceed. If >1 (very rare — would require two same-time bookings) → return `{ success: false, reason: "ambiguous", choices: [<service names>] }` and the agent re-prompts with `serviceName`.
  4. Read `bookingId` + `revision` from the matched booking and call `Wix: Cancel Booking`.

- `reschedule`: input `{ phone, date, time, newDate, newTime, newTherapistName? }`. Implementation:
  1. Booking lookup + date/time match (same as `cancel` steps 1–3) → get `bookingId`, `revision`, original `serviceId`, original `variantId` (if any), original duration.
  2. Resolve `newTherapistName` (if provided) via `resolve_staff`.
  3. Call `Wix: Query Time Slots` for `newDate` + `newTime` window (Phase 3 algorithm), with the original `serviceId` and original `durationInMinutes` — match the exact slot.
  4. If not bookable → return `{ success: false, reason: "new_slot_not_available", alternatives: [...] }`.
  5. Call `Wix: Reschedule Booking` with original `bookingId`/`revision`/`serviceId` and the new fresh slot's `scheduleId` + `startDate` + `endDate` + `staffId` (from `availableResources` of the matched slot).

**Acceptance:** Caller can identify their booking using only phone + the date/time they remember; the agent never quotes a UUID; modifications never require the agent to thread 7+ fields.

---

### Phase 5 — Idempotency + double-book guard via Wix-as-source-of-truth (3–5 days)

**Goal:** no duplicate bookings under retries; no two concurrent calls both book the same slot. Achieved without any external dedup store.

**Tasks:**

- **Pre-create dedup query.** Before `Wix: Create Booking`, run a quick `Wix: Query Bookings` filtered by `contactDetails.phone` + `slot.startDate` + `serviceId`. If a `CREATED` or `CONFIRMED` booking already exists for that contact/slot/service → return that booking as the success response (idempotent retry behavior) instead of creating a duplicate.
- **Post-create double-book detection.** After `Wix: Create Booking` returns, check `booking.doubleBooked`. If `true` (two concurrent calls raced past the dedup query), immediately call `Wix: Cancel Booking` for the loser and respond with `{ success: false, reason: "slot_no_longer_available", alternatives: [...] }`. The winner keeps its booking; the racing caller is offered alternatives.
- Document the small race window: a sub-second overlap where two parallel `book` calls for the same slot can both pass the dedup query. The `doubleBooked` flag is Wix's explicit signal for this; we use it instead of a Redis mutex.

**Acceptance:** Chaos test (10 parallel `book` calls for the same slot) results in exactly 1 confirmed booking and 9 graceful `slot_no_longer_available` responses, with no orphaned bookings on the Wix side.

---

### Phase 6 — Reconciliation + observability (ongoing)

**Goal:** be the first to know when something diverges.

**Tasks:**

- Nightly reconciliation: pull all Wix bookings created in the last 24h vs. all n8n booking attempts; alert on any orphans (n8n thinks success, Wix has no record) or duplicates (`doubleBooked: true`).
- Daily report to ops Slack/email: success rate, p95 latency, top 3 error codes, # of slot-race recoveries.
- Synthetic canary call once an hour against staging Wix site: book + cancel an "Aria Test" customer; alert on any failure.

**Acceptance:** You'd find out about a Wix outage in under 5 minutes, not when a caller complains.

---

### Phase 7 — Multi-tenant extraction (optional, only if scaling clients)

If you're deploying this for 5+ spas/clinics:

- Lift the n8n logic into a dedicated small service (Cloudflare Workers, or a tiny FastAPI on Fly.io / Render). Multi-tenant by `site_id` from the header; per-site Wix credentials selected at request time.
- n8n becomes a stateless adapter between Retell webhooks and the new service — or is removed altogether.

---

## 6. Risk callouts

- **Phase 3 is the highest-risk change** — every slot lookup and booking path changes. Run n8n's old + new flows in parallel for 1–2 weeks, A/B by `call_id` hash, and compare outcomes before cutting over.
- **Don't migrate Aria's prompt all at once.** Ship Phases 1–2 first, then in Phase 3 swap one tool definition at a time, verifying each.
- **Wix call volume increases** because we re-query live instead of caching — every `book` performs a `Query Services` + `Query Time Slots` + `Query Bookings` (dedup) + `Create Booking` + `Confirm Booking`. Monitor for Wix 429 rate-limit responses; if you hit them, that's the trigger to revisit caching as a future iteration.
- **Disambiguating bookings by phone + date + time can be ambiguous** if a caller has two bookings the same day at different times of similar phrasing. The cancel/reschedule flow needs a clear "I see two — which one?" branch that asks for `serviceName` to break the tie.
- **The dedup race window in Phase 5 is real but small.** The `doubleBooked` post-create check is the safety net; do not skip it.
- **Phase 0 instrumentation is a prerequisite for everything.** Without baseline data, you can't prove Phases 1–6 actually improved anything.

---

## 7. Summary — what this buys you

| Today | After redesign |
|---|---|
| Agent sends raw UUIDs and full ISO timestamps | Agent sends `serviceName`, `date`, `time`, `therapistName`, `phone` |
| Slot race conditions silently corrupt bookings | Live re-query at booking time + auto-refetch on 428 + `doubleBooked` post-create check |
| Hardcoded site IDs; per-spa fork | All IDs discovered dynamically (live) |
| Agent must echo `serviceId` / `variantId` / `scheduleId` / `staffId` / `bookingId` / `revision` | Resolved server-side every tool call from human-readable inputs |
| No idempotency; retries can dup-book | Pre-create `Query Bookings` dedup + post-create `doubleBooked` rollback |
| Failures = generic "I'm having trouble" | Structured `wix_error_code` → distinct agent responses |
| No observability | Per-call logs, nightly reconciliation, canary calls |
| Aria's prompt ~9000 chars (much dedicated to ID hygiene) | ~6000 chars, all about the conversation |

> **Deliberately out of scope (this iteration):** any caching layer — no Wix-data cache, no slot/booking token store, no Redis. n8n is fully stateless. If Wix rate limits or latency become a problem later, a cache can be layered in behind the same agent-facing contract without the agent changing.

---

## 8. Validation appendix — plan vs. current files

This appendix walks the plan against the actual `aria_single_prompt.json` and `Retell AI ↔ Wix Bookings | Production v2.json` so every claim is traceable. Anything still uncertain is flagged "VERIFY IN SANDBOX" — these are the only items that could surprise during execution.

### 8.1 Agent-tool contract diff (current → after plan)

| Tool | Today's input fields | After plan |
|---|---|---|
| `get_services` | `serviceName?` (enum) | unchanged input; response strips IDs |
| `get_staff` | — | **removed** (Phase 2) |
| `get_slots` → `find_slots` | `serviceId`, `startDate`, `endDate`, `durationInMinutes`, `staffId?`, `timeOfDay?`, `earliestFirst?`, `limit?` | `serviceName`, `durationMinutes`, `dateRange` (or `startDate`+`endDate` as plain dates), `therapistName?`, `timeOfDay?`, `earliestFirst?`, `limit?` |
| `book_appointment` → `book` | `serviceId`, `variantId?`, `staffId?`, `scheduleId`, `startDate`, `endDate`, `firstName`, `lastName`, `phone`, `addOns[].{id, groupId}` | `serviceName`, `durationMinutes`, `date`, `time`, `therapistName?`, `firstName`, `lastName`, `phone`, `addOnNames[]?` |
| `get_booking` → `find_my_bookings` | `bookingId?`, `phone?` | `phone?` |
| `cancel_booking` → `cancel` | `bookingId`, `revision` | `phone`, `date`, `time` |
| `reschedule_booking` → `reschedule` | `bookingId`, `revision`, `serviceId`, `scheduleId`, `staffId`, `startDate`, `endDate` | `phone`, `date`, `time`, `newDate`, `newTime`, `newTherapistName?` |
| `flag_callback` | `callerName?`, `callerPhone?`, `reason`, `questionDetail?` | unchanged |
| `transfer_to_human` | (built-in) | unchanged |
| `end_call` | (built-in) | unchanged |

Net result: **the agent loses zero capabilities** but stops passing 13 distinct UUID/ISO fields across all tool calls.

### 8.2 n8n nodes touched per phase

| Phase | Nodes modified | Nodes added | Nodes removed |
|---|---|---|---|
| 0 | All `Respond: …` and `Error: …` (add logging branch upstream) | `Log: Tool Call`, `Log: Tool Response`, logging DB writer | — |
| 1 | `Wix: Create Booking` (remove `withoutPayment`), `Wix: Query Time Slots` / `Wix: Create Booking` / `Wix: Reschedule Booking` (de-hardcode IDs), `Wix: Get Add-ons` (URL swap), all `Validate: …` (E.164 normalize), all `Format: …` (surface `applicationError.code`) | `Discover: Resource Type ID`, `Discover: Location ID` (one-time-per-load) | All `Error: …` static-error nodes (replaced by formatter passthrough) |
| 2 | `Format: Services Response`, `Wix: Query Services` (consider `search-services`), `Validate: Slots Args`, `Validate: Booking Args` | `Helper: resolve_service`, `Helper: resolve_staff` | `Wix: Query Staff Members` + `Format: Staff Response` + `Respond: Get Staff` (the `get_staff` route) |
| 3 | `Format: Time Slots Response`, `Validate: Booking Args`, `Wix: Create Booking` jsonBody, `Format: Contact Response1` (fix `found:false` branch), `If: Contact Found` | `Helper: parseTimeLabel`, `Helper: composeLocalStartDate`, `Refetch slots on 428` retry node | — |
| 4 | `Validate: Cancel Args`, `Validate: Reschedule Args`, `Validate: Get Booking Args`, the cancel/reschedule jsonBody templates | Booking match-by-localStartDate Code node | — |
| 5 | `Wix: Create Booking` (wrap with pre-create dedup query and post-create `doubleBooked` check) | Pre-create `Query Bookings` dedup node, post-create `doubleBooked` check + rollback `Cancel Booking` | — |
| 6 | — | Nightly reconciliation workflow, hourly canary workflow, daily report workflow | — |

### 8.3 Wix endpoints used per phase (verified against current workflow + docs)

| Endpoint | Used by | Verified by |
|---|---|---|
| `POST /_api/bookings/v2/services/query` | get_services, resolve_service | Current `Wix: Query Services` node |
| `POST /_api/bookings/v2/services/search-services` (Phase 2) | resolve_service (preferred) | Services V2 intro doc — `search-services` op exists |
| `GET /_api/bookings/v2/services/service-options-and-variants/by-service-id/{id}` | resolve_service (for VARIED) | Current `Wix: Get Pricing Variants` node |
| `GET /_api/bookings/v2/add-ons/{id}` (Phase 1: swap to this) | resolve_service add-on resolution | Wix Add-Ons API intro doc |
| `POST /_api/bookings/v2/resources/query` | Phase 1 — discover `resourceTypeId` | Wix Resources V2 |
| `GET /locations/v1/locations` | Phase 1 — discover `locationId` | Wix Locations v1 |
| `POST /_api/bookings/v2/staff-members/query` | resolve_staff | Current `Wix: Query Staff Members` node |
| `POST /_api/service-availability/v2/time-slots` | find_slots, book (re-query), reschedule | Current `Wix: Query Time Slots` node |
| `POST /_api/contacts/v4/contacts/query` | Contact upsert during book | Current `Wix: Search Contact1` node |
| `POST /_api/contacts/v4/contacts` | Contact upsert during book | Current `Wix: Create Contact` node |
| `POST /_api/bookings/v2/bookings` | book (Create) | Current `Wix: Create Booking` node |
| `POST /_api/bookings/v2/bookings/{id}/confirm` | book (Confirm) | Current `Wix: Confirm Booking` node |
| `POST /_api/bookings/v2/bookings/query` | find_my_bookings, cancel, reschedule, Phase 5 dedup | Current `Wix: Get Booking (by ID/Contact)` nodes |
| `POST /_api/bookings/v2/bookings/{id}/cancel` | cancel, Phase 5 rollback | Current `Wix: Cancel Booking` node |
| `POST /_api/bookings/v2/bookings/{id}/reschedule` | reschedule | Current `Wix: Reschedule Booking` node |

No phase introduces a Wix endpoint the workflow doesn't already call (except `search-services` in Phase 2 and `resources/query` + `locations` in Phase 1) — meaning credential scope and rate-limit exposure are essentially unchanged.

### 8.4 Verified Wix behaviors the plan depends on

| Behavior | Status | Evidence |
|---|---|---|
| `availabilityEntries[i].slot` is shape-compatible with `Create Booking`'s `bookedEntity.slot` | **VERIFIED** | Wix end-to-end booking flow docs explicitly recommend passing the slot verbatim |
| `Confirm Booking` does NOT re-validate availability | **VERIFIED** | Wix Confirm docs |
| `booking.doubleBooked: true` is set when two bookings race onto the same slot | **VERIFIED** | Wix end-to-end booking flow docs |
| `payment.rateType === 'VARIED'` is the trigger for needing `variantId` | **VERIFIED** | Current workflow's `Extract Pricing IDs` Code node uses exactly this check |
| Booking lifecycle is `CREATED → PENDING → CONFIRMED/DECLINED` | **VERIFIED** | Bookings v2 intro doc |
| `Query Bookings` supports nested filter `contactDetails.contactId.$in` | **VERIFIED** | Current `Wix: Get Booking (by Contact)` works this way today |
| No `Idempotency-Key` header support | **VERIFIED** | Wix errors/get-started docs — none mentioned. We compensate via Phase 5 dedup. |
| Add-ons with `durationInMinutes > 0` extend slot length | **VERIFY IN SANDBOX** | The current workflow doesn't exercise this path; Sage & Willow's existing add-ons appear to have 0 added minutes. If any add-on actually adds duration, Phase 3 step 7 re-query is required. |
| `Query Bookings` filter on `bookedEntity.slot.startDate` works for the Phase 4/5 match | **VERIFY IN SANDBOX** | The current workflow filters on `contactDetails.contactId` and `status`, not on `slot.startDate`. Wix's nested-field filter syntax should support it but test before relying on it; fallback is client-side filter after fetching the contact's upcoming bookings. |
| `search-services` returns the same `Service` shape as `query-services` | **VERIFY IN SANDBOX** | Inferred from the Services v2 intro; if shape differs, Phase 2's `resolve_service` keeps `query-services` as the canonical call. |
| Wix returns the discovered `resourceTypeId` consistently across `query-resources` and `query-staff-members` | **VERIFY IN SANDBOX** | These are typically the same UUID per site but worth confirming once. |

### 8.5 Implementation prerequisites and ordering

- **Phase 0 → everything.** No baseline metrics = no proof any later phase helps.
- **Phase 1 (E.164 normalization) → Phases 4 and 5.** Wix Contacts dedup and booking-lookup-by-phone are byte-exact on the phone string. Without normalization first, Phase 4/5 will miss matches when callers' phones are stored inconsistently.
- **Phase 1 (resourceTypeId + locationId discovery) → Phases 3, 4.** The new book/reschedule paths reference these dynamically; the hardcoded values must be eliminated first or the workflow JSON stays site-locked.
- **Phase 2 (resolvers) → Phase 3, 4.** The book/cancel/reschedule paths call `resolve_service` and `resolve_staff`. They must exist before the new tool routes are wired.
- **Phase 3 → Phase 5.** Pre-create dedup needs the new book route's `serviceId` + `localStartDate` already resolved.
- **Phase 6 (reconciliation/observability) is safe to start in parallel with Phase 0** — they share the same logging table.

### 8.6 Things explicitly NOT changing

To set expectations during review:

- The Retell agent's identity, personality, escalation rules, pronunciation rules, hearing-the-caller logic, turn-taking rules, closing flow, recording disclosure, owner-anonymity rule.
- The `flag_callback`, `transfer_to_human`, `end_call` tools (no Wix surface, no failure mode).
- The two-step `Create Booking` → `Confirm Booking` flow (already correct).
- The `Wix: Search Contact1` → `Wix: Create Contact` upsert chain (improved in Phase 3 but the same Wix endpoints).
- The post-call analysis fields (`caller_intent`, `resolution_status`, etc.) — they remain, but `booking_id` can be sourced from the n8n side for analytics instead of from the agent.

### 8.7 Known gotchas pulled forward from the current workflow

- `Format: Contact Response1` returns `success: true, found: false` with `contacts: []` on the success branch; the `If: Contact Found` boolean check works but the downstream booking jsonBody fragment `$('Wix: Search Contact1').item.json.contacts[0].id` would throw if reached without a found contact. Phase 3 fixes this by gating contact reads on `found`.
- The `Wix: Search Contact1` node has a dual-output edge in the current workflow: success → `Format: Contact Response1`, error → `Wix: Create Contact`. This conflates "search errored" with "search succeeded but empty" — clean up as part of Phase 3.
- Revision is passed both as a quoted string (`Wix: Cancel Booking` jsonBody: `"revision": "{{ $json.args.revision }}"`) and as a number (`Wix: Confirm Booking`: `"revision": {{ $json.booking.revision }}`). Wix accepts both today but standardize on one in the rewritten flows.

---

## Sources

- [Wix Bookings API Introduction](https://dev.wix.com/docs/api-reference/business-solutions/bookings/introduction)
- [Wix Bookings End-to-End Booking Flows (race condition + "pass slot verbatim")](https://dev.wix.com/docs/api-reference/business-solutions/bookings/end-to-end-booking-flows)
- [List Availability Time Slots](https://dev.wix.com/docs/api-reference/business-solutions/bookings/time-slots/time-slots-v2/list-availability-time-slots)
- [Time Slot Object](https://dev.wix.com/docs/api-reference/business-solutions/bookings/time-slots/time-slots-v2/time-slot-object)
- [Create Booking (REST) — error codes](https://dev.wix.com/docs/api-reference/business-solutions/bookings/bookings/bookings-writer-v2/create-booking)
- [Create Booking (Velo, lists error codes)](https://dev.wix.com/docs/velo/apis/wix-bookings-v2/bookings/create-booking)
- [How Bookings Are Confirmed or Declined (Confirm does not re-validate)](https://dev.wix.com/docs/rest/business-solutions/bookings/bookings-and-time-slots/bookings-v2/bookings-v2-and-confirmation/how-bookings-are-confirmed-or-declined)
- [Service Options and Variants intro](https://dev.wix.com/docs/rest/business-solutions/bookings/services/service-options-and-variants/introduction)
- [Pricing Integration SPI](https://dev.wix.com/docs/api-reference/business-solutions/bookings/pricing/pricing-integration-service-plugin/introduction)
- [Add-On Groups (Create)](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/services-v2/create-add-on-group)
- [Add-Ons API (current public namespace)](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/add-ons/introduction)
- [Create Contact v4](https://dev.wix.com/docs/rest/crm/members-contacts/contacts/contacts/contact-v4/create-contact)
- [Query Contacts v4](https://dev.wix.com/docs/rest/crm/members-contacts/contacts/contacts/contact-v4/query-contacts)
- [Booking Confirmed webhook](https://dev.wix.com/docs/rest/business-solutions/bookings/bookings-and-time-slots/bookings-v2/bookings-v2-and-confirmation/booking-confirmed)
- [About Time Zones (Bookings)](https://dev.wix.com/docs/api-reference/business-solutions/bookings/about-time-zones)
- [Rate Limits / 429](https://dev.wix.com/docs/rest/articles/get-started/rate-limits)
- [About Errors](https://dev.wix.com/docs/rest/articles/get-started/errors)
- [BOOKINGS_SYSTEM_ERROR community thread](https://forum.wixstudio.com/t/getting-bookings-system-error-when-trying-to-checkoutbooking-in-wixbooking/34864)
