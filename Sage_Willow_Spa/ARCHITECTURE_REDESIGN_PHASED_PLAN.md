# Aria + n8n + Wix Bookings — Architectural Review & Phased Redesign Plan

> **Scope:** Sage & Willow Spa voice-agent stack (Retell single-prompt agent "Aria" → n8n "Retell AI ↔ Wix Bookings | Production v2" → Wix Bookings REST API).
> **Goal:** Eliminate the failure modes where the AI sends incorrect / hallucinated Wix identifiers, by moving booking intelligence from the agent into the backend.
> **Status:** Proposal — phased, each phase independently shippable.

---

## Table of contents

1. [Current architecture](#1-current-architecture-what-is-actually-happening)
2. [Failure modes you're hitting (and why)](#2-failure-modes-youre-hitting-and-why)
3. [The redesign — "Thin agent / Fat backend with opaque tokens"](#3-the-redesign--thin-agent--fat-backend-with-opaque-tokens)
4. [Wix-side hardening (independent of agent redesign)](#4-wix-side-hardening-independent-of-agent-redesign)
5. [Phased implementation plan](#5-phased-implementation-plan)
6. [Risk callouts](#6-risk-callouts)
7. [Summary — what this buys you](#7-summary--what-this-buys-you)
8. [Sources](#sources)

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

- Replace `manage.wix.com/_api/add-ons-service/v1/add-ons/{id}` with the public `wixapis.com/_api/bookings/v2/add-ons/...` endpoint.
- Remove `flowControlSettings.withoutPayment` from the `Wix: Create Booking` body.
- Add startup nodes (or a small scheduled workflow) that fetches `resourceTypes` and `locations` once and writes them to n8n static data; reference these instead of the hardcoded IDs in `Wix: Query Time Slots`, `Wix: Create Booking`, `Wix: Reschedule Booking`.
- E.164-normalize the `phone` arg in `Validate: Booking Args`, `Validate: Get Booking Args`, `Validate: Get Contact`.
- Improve error surfacing: bubble `applicationError.code` from Wix responses into a structured `wix_error_code` field that the response formatters return — so the agent's tool result distinguishes "slot taken" from "wrong service" from "5xx".

**Acceptance:** Zero hardcoded site-specific IDs in code; structured error codes flowing back to the agent; add-ons fetched via supported path.

---

### Phase 2 — Server-side service-name resolution (1 week)

**Goal:** the agent stops needing `serviceId` and `variantId`. Resolution happens server-side, **live** (no Wix-data caching in this iteration).

**Tasks:**

- Add an internal `resolve_service(name, durationMinutes?)` helper inside n8n — a sub-workflow or shared Code node that:
  - Calls `Wix: Query Services` live
  - Fuzzy-matches the agent-supplied `name` (substring + simple normalization)
  - If the service has `pricingVariants`, picks the variant whose `duration` matches `durationMinutes`; returns `{ serviceId, variantId, addOns[], priceUsd, durationMinutes }`
  - If no `durationMinutes` provided and the service has variants, returns all variants so the agent can be told the price options
  - Returns a structured error if no match — agent can confirm with the caller
- Rewrite `get-services` n8n route so its response to the agent is **human-readable only**: service names, descriptions, price-by-duration strings, add-on names. No `serviceId`, no `variantId`, no `groupId` in the response.
- Rewrite `get-slots` n8n route to accept `serviceName` + `durationMinutes` from the agent (instead of `serviceId`). Internally calls `resolve_service` then proceeds with the Wix time-slots query.
- Update Aria's tool schemas to drop the `serviceId` / `variantId` parameters and replace with `serviceName` / `durationMinutes`.

**Acceptance:** Agent never sees a raw Wix ID in any tool response. `serviceId` / `variantId` no longer appear in any tool's input schema.

> **Deferred (not in this iteration):** caching the resolved catalog. If `get_services` / `find_slots` latency or Wix rate limits become an issue later, add a cache layer behind `resolve_service` — but keep the agent-facing contract identical so the upgrade is invisible to Aria.

---

### Phase 3 — Stateless slot lookup at booking time (2 weeks — biggest lift, biggest payoff)

**Goal:** the agent stops handling `scheduleId`, `startDate`, `endDate`, `staffId`. n8n re-queries Wix live each call — no cache, no tokens, no store.

**Tasks:**

- Rewrite `Format: Time Slots Response` (the `find_slots` response shape) to return only human-readable fields: `[{ date: "2026-05-30", time: "3:00 PM", duration: 60, therapists: ["Lily","Rocky"] }]`. Strip `scheduleId`, `startDate`, `endDate`, `staffId` from the agent-facing payload.

- Rewrite `book_appointment` n8n route. New input shape:
  ```
  { serviceName, durationMinutes, date, time, therapistName?,
    firstName, lastName, phone, addOnNames?: string[] }
  ```

  Implementation steps inside the n8n execution:
  1. Resolve `serviceName` + `durationMinutes` → `serviceId`, `variantId` via the `resolve_service` helper (live Wix call from Phase 2).
  2. Build `startDateLocal` from `date` + `time` (local timezone) and a small window (e.g. `date 00:00 → date 23:59`).
  3. Call `Wix: Query Time Slots` live with `serviceId`, the date window, and (if `therapistName` supplied) the resolved `staffId`. This is the **fresh slot blob** Wix recommends using.
  4. From the response, find the entry whose `localStartDate` matches `date` + `time`. If none → return `{ success: false, reason: "slot_no_longer_available", alternatives: [...] }` with 2–3 nearby times.
  5. Resolve `staffId` from the chosen entry's `availableResources` (match `therapistName` case-insensitively; omit if the agent passed no preference and let Wix auto-assign).
  6. Resolve `addOnNames` → `[{id, groupId}]` via a live `Wix: Query Services` lookup against the matched `serviceId`.
  7. **Pass the matched slot blob verbatim** into `Wix: Create Booking` (Wix's recommended pattern).
  8. On 428, refetch slots once → if same time still bookable, retry; else respond with alternatives.

- Update Aria's system prompt and tool schemas to drop all ID-handling and slot-echoing rules. The agent passes only the strings it heard from the caller and the strings it read out from `find_slots`.

**Acceptance:** Book-failure rate from "agent sent bad UUIDs" drops to ~0. Slot-race failures handled invisibly via auto-refetch. n8n holds no state between tool calls.

---

### Phase 4 — Stateless booking lookup for find/cancel/reschedule (1 week)

**Goal:** the agent stops handling `bookingId` + `revision`. No booking cache — n8n re-queries Wix on every modification.

**Tasks:**

- `find_my_bookings`: input `{ phone? }` (default to caller ID). n8n calls `Wix: Query Bookings` live filtered by contact phone, returns `[{ serviceName, date, time, durationMinutes, therapistName }]` — **no `bookingId`, no `revision`** in the agent-facing response.

- `cancel`: input `{ phone, date, time }`. Implementation:
  1. Live `Wix: Query Bookings` by phone → list of upcoming bookings.
  2. Filter for the booking matching `date` + `time` (single-row resolution). If 0 matches → `{ success: false, reason: "booking_not_found" }`. If >1 (rare) → return brief disambiguators and ask the agent to re-prompt with `serviceName` too.
  3. Read `bookingId` + `revision` from the matched booking and call `Wix: Cancel Booking`.

- `reschedule`: input `{ phone, date, time, newDate, newTime, newTherapistName? }`. Implementation:
  1. Live booking lookup as in `cancel` → get `bookingId`, `revision`, `serviceId`.
  2. Live `Wix: Query Time Slots` for `newDate` + `newTime` (same algorithm as Phase 3) → get fresh slot blob, `staffId` (if `newTherapistName`).
  3. Call `Wix: Reschedule Booking` with original `bookingId`/`revision`/`serviceId` and the new fresh slot blob.

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
