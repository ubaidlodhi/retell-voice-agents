# Aria Outbound — Design & Deployment Spec

**Built 2026-09-06.** Outbound counterpart to the live inbound Aria agent. A lead
fills out the booking form on the Sage & Willow website; n8n normalizes the
submission and asks Retell to ring them; Aria opens the call, confirms she has
the right person, and runs the same booking conversation the inbound agent runs.

Everything below is deployed and verified except the two items under
[Not yet done](#not-yet-done).

---

## Deployed IDs

| Thing | ID / URL |
|---|---|
| Outbound agent | `agent_4ef8160dc71826818c6fd8122b` — "Aria - Sage & Willow Spa (Outbound) V01" |
| Outbound flow | `conversation_flow_599a68571a81` v0 — 39 nodes |
| Knowledge base | `knowledge_base_cb1d71238e1ba5fe` ("SPA Business Context") |
| Backend workflow | n8n `yfbpUaEzZQghelh3` — "Retell AI <-> Wix Bookings \| OUTBOUND (DEV CREDS)", **active** |
| Backend webhook | `POST https://automation.aiemply.com/webhook/retell-wix-outbound` |
| Trigger workflow | n8n `FFvcDEaxPi7UIEBK` — "Sage & Willow \| Website Lead -> Outbound Call (DEV)", **active** |
| Trigger webhook | `POST https://automation.aiemply.com/webhook/sage-willow-lead-callout` |
| Dials from | `+1 628 286 2281` (the existing Retell DID, via `override_agent_id`) |

The agent is **not published** and **not bound to any phone number**. Nothing
dials unless the trigger webhook is hit or you start a simulator run.

### Sources it was built from

| Source | ID |
|---|---|
| Inbound agent | `agent_eceb7448aa1f37e8f436a63a43` |
| Inbound flow | `conversation_flow_bdb1968b28ed` v3 — 34 nodes |
| Production backend | n8n `s5dWZOMRl0X7PV65` — 83 nodes, production Wix credentials |

---

## Environment isolation

This was the point of replicating the backend rather than sharing it.

|  | Inbound (production) | Outbound (dev) |
|---|---|---|
| n8n workflow | `s5dWZOMRl0X7PV65` | `yfbpUaEzZQghelh3` |
| Webhook | `/webhook/retell-wix` | `/webhook/retell-wix-outbound` |
| Wix credential | `poMGaCKgf32bUQQL` — Prod: Sage & Willow Spa | `wLpWbblaihcY4xnw` — Test: Wix Sage Site |
| Therapists | Nicky, winnie | Rocky (Male), Lily (Female) |
| Booking grid | 15 minutes | 30 minutes |
| Callback email | `sagewillowspa@gmail.com` | `engineering@aiemply.com` |

**An outbound test call cannot write to the client's real calendar.** Verified by
calling the dev webhook directly: `get-staff` returns Rocky and Lily, which only
exist on the test site.

The two workflows are otherwise identical — all 83 nodes, every Code node, the
whole `Route by Tool` switch — because the dev copy is generated from the
production one on every build rather than hand-maintained.

> **Before go-live**, the outbound agent's 8 tool URLs must be repointed at
> `/webhook/retell-wix` (production). That is one constant in
> `_build_outbound_agent.py` (`OUTBOUND_WEBHOOK`).

---

## The dynamic-variable contract

n8n passes these to Retell as `retell_llm_dynamic_variables`. All values are
strings.

| Variable | Source | Used by |
|---|---|---|
| `lead_first_name` | form | opening line, identity check, `book_appointment.firstName` |
| `lead_last_name` | form | `book_appointment.lastName` — deliberately empty when the form gave only one name token |
| `lead_phone` | form, normalized to E.164 | booking phone, callback phone, `get_booking` lookup |
| `lead_submitted_at` | form or receipt time, rendered in Pacific | lets Aria say when they filled it out |

### `{{user_number}}` is a trap on outbound

On an inbound call `{{user_number}}` is the caller. On an **outbound** call it is
the spa's own caller ID. A naive clone therefore books every appointment against
the spa's own phone number.

Three places referenced it, and all three are rewired to `{{lead_phone}}`:

1. The global prompt's caller-context block and phone-pronunciation rule.
2. `node-book-phone` and `node-message-collect` instructions.
3. **The tool JSON schemas** — `book_appointment.phone` and `get_booking.phone`
   both carried `"Defaults to {{user_number}}"` in their parameter descriptions.
   This is the one that is easy to miss, because it lives in the tool definitions
   rather than in any node.

The build script asserts that `{{user_number}}` appears **nowhere** in the
finished flow — nodes, tool schemas, or global prompt — and refuses to deploy
otherwise.

The warnings about it are phrased as *"the number this call is dialling from"*
rather than by naming the variable, because a `{{user_number}}` reference renders
as literal digits in the prompt, and the inbound spec documents that the model
reads example digits aloud verbatim.

---

## What differs from inbound

### Global prompt

Two changes; the rest is byte-identical so a shared fix diffs cleanly.

1. **Caller Context → Call Context.** States that this is outbound, that the lead
   filled out a form, and lists the four form variables.
2. **New section: "You rang them — outbound etiquette."** Get to the point inside
   two sentences; never ask for anything the form already supplied; take the first
   clear no as a no; a bad time is not a no; if the wrong person answered,
   apologise and end rather than pitching; never say "thanks for calling."

### Nodes

`node-greeting` keeps its ID — several nodes route back to it — but becomes the
outbound opening.

**Turn 1:** `"Hi, is this {{lead_first_name}}?"` and stop. One question, alone.
**Turn 2 (on confirmation):** `"Hi {{lead_first_name}}, this is Aria from Sage and
Willow Spa - you filled out our booking form. Is now a good time?"`

It also handles "Who is this?", "How did you get my number?", "Am I talking to a
robot?", and a `{{lead_first_name}}` that failed to render.

**Five new nodes**, each also a global node so it can fire mid-call:

| Node | Fires when | Does |
|---|---|---|
| `node-out-wrong-person` | not the lead / wrong number | Apologises, hangs up. No pitch to a stranger, no asking for the right number |
| `node-out-bad-time` | busy, driving, "call me later" | Takes a callback window, routes to `flag_callback` |
| `node-out-not-interested` | clear refusal, "take me off your list" | One line, hangs up. No why, no discount, no counter-offer |
| `node-out-no-form-recall` | "I never filled anything out", "is this a scam?" | Explains once, then books or drops |
| `node-out-voicemail` | answering machine | Leaves the message, hangs up |

Each carries positive **and** negative finetune examples. The negatives matter
most: `node-out-not-interested` must fire on "I'm not interested" but **not** on
"no thanks, no add-ons" or "not that time, something later", which are ordinary
booking turns.

**Modified nodes:**

- `node-book-name` — never asks. It has the name from the form. Asks for a
  spelling only if the variable comes through empty.
- `node-book-phone` — never asks or reads back. Uses `{{lead_phone}}`.
- Both gained a `skip_response_edge` so they can stay silent and fall through.
- `node-close` — "Thanks for your time. Take care." Never "thank you for calling."
- `node-global-recording-decline` — ends immediately. We rang them, so there is
  nothing to negotiate.

**Untouched:** booking discovery, add-ons, readback, submit, confirm, failure,
cancel, reschedule, status, FAQ, transfer, callback, emergency, crisis,
inappropriate, spam, off-topic. Full inbound parity.

### Agent config

Inherits the inbound voice and speech settings (Belle B, speed 1.06,
temperature 0.7, `stt_mode: accurate`, expressive mode). Deltas:

- `begin_message_delay_ms` 400 → **1000**, so Aria does not talk over "hello".
- `voicemail_option` — static text naming the lead and giving the callback
  number as `six two eight, two eight six, two two eight one` (the Retell DID,
  so a callback lands on inbound Aria).
- Four post-call fields on top of the inbound nine: `reached_lead`,
  `outbound_outcome`, `do_not_call`, `callback_window`.

---

## The trigger workflow

```
Webhook POST /webhook/sage-willow-lead-callout
  → Normalize Lead
  → IF: Lead Valid?
       no  → 400 { ok: false, errors: [...] }
       yes → IF: Dry Run?
                yes → 200 { ok: true, dryRun: true, wouldCall: {...} }   (no call placed)
                no  → Retell: Create Phone Call
                        ok    → 200 { ok: true, call_id, to }
                        error → 502 { ok: false, error: 'retell_create_call_failed' }
```

**No dialling-hours gate — a submission dials immediately, around the clock.**
This was an explicit decision. If it needs to change, it is one IF node between
"Lead Valid?" and "Dry Run?".

### The normalizer

The real Wix form does not exist yet, so the node accepts whatever shows up. It
strips n8n's `{headers, params, query, body}` envelope, then walks the payload to
depth 5, collecting every scalar into one lowercased bag and flattening
key/value array styles (`submissions`, `fields`, `answers`) on the way. Then:

- **Name** — `first_name`/`last_name` if present, else splits a full-name field.
  A single-token name leaves `lead_last_name` empty on purpose; the agent asks.
- **Phone** — normalized to E.164. Ten digits get `+1`; eleven starting with `1`
  get `+`. Rejects anything that is not `+1` + ten digits, because Retell only
  dials US destinations from a Retell-purchased number.
- **`lead_submitted_at`** — from the payload if present, else receipt time,
  rendered in `America/Los_Angeles`.

`dryRun: true` anywhere in the payload short-circuits before the Retell call and
echoes the normalized result. That is how the normalizer was tested end to end
without spending a phone call.

`outbound/test_normalizer.js` covers nine payload shapes — **9/9 passing**.
Re-paste the node body from the build script into that file when you change it.

---

## Build scripts

All three are re-runnable and idempotent. Each fetches its source live rather
than working from a checked-in copy, so nothing silently drifts.

| Script | Builds |
|---|---|
| `_build_outbound_backend_workflow.py` | dev backend. Fetches `s5dWZOMRl0X7PV65`, swaps 18 Wix credentials, repoints the webhook, redirects the callback email. `--update <id>` re-syncs. |
| `_build_outbound_agent.py` | flow + agent. Fetches inbound flow v3, applies the patch set, creates or updates via `_deployed_ids.json`. |
| `_build_lead_callout_workflow.py` | trigger workflow. |

All three take `--dry-run` (write snapshots, touch nothing remote).

Each asserts its assumptions and **refuses to deploy** rather than producing
something subtly wrong: exactly 18 production credentials to swap, exactly 8 tool
URLs to repoint, exactly 2 tools carrying a `{{user_number}}` phone default, the
three global-prompt anchors present, every edge target resolving, no
`{{user_number}}` anywhere in the output. If the inbound flow is restructured,
these fail loudly instead of shipping a half-applied patch.

> n8n's API rejects any `settings` key outside a small allowlist, and its WAF
> rejects the default `Python-urllib` User-Agent. Both are handled in the scripts.

---

## What was verified

- Dev backend returns Rocky/Lily from the **test** Wix site — real calendar untouchable.
- `get-services` and `get-staff` both return live data through the new webhook.
- Deployed flow: 39 nodes, 8 tools all on the dev webhook, KB attached, no dangling
  edge targets, no duplicate node or edge IDs, no `{{user_number}}` anywhere.
- Deployed agent: correct flow binding, voicemail option, 1000 ms delay, all 13
  post-call fields.
- Trigger workflow live on all three response paths (dry-run valid, dry-run
  nested-Wix, invalid → 400).
- Retell `create-phone-call` accepts the exact body, auth, agent ID and dynamic
  variables — probed with a deliberately invalid destination so nothing dialled.
- Normalizer: 9/9 cases.

## Not yet done

1. **No real call has been placed.** Every layer is verified independently and the
   API accepts the request, but no end-to-end dial has happened. First real test
   should be to your own phone.
2. **The Wix form is not wired.** Point the form's automation at
   `POST https://automation.aiemply.com/webhook/sage-willow-lead-callout`. The
   normalizer should handle its payload as-is; if a field is missed, add its
   spelling to the `pick(...)` lists.

## Before go-live

- [ ] Place a real test call to your own number and listen to the opening.
- [ ] Wire the Wix form to the trigger webhook.
- [ ] Repoint the agent's tool URLs to the **production** backend
      (`OUTBOUND_WEBHOOK` → `/webhook/retell-wix`) and rebuild.
- [ ] Decide whether the callback email should go to the client on outbound.
- [ ] Publish the agent.
- [ ] Confirm no dialling-hours gate is still what you want once real leads flow.
- [ ] Decide how `do_not_call: true` gets acted on — nothing consumes that field yet.

---

## Test scenarios for the simulator

| # | Scenario | Expect |
|---|---|---|
| 1 | Lead confirms, books a 60-min Swedish | Identity check → reason → booking. Never asks for name or phone |
| 2 | "Speaking" then "who is this?" | Answers, does not restart the opening |
| 3 | Wrong person answers | Apologises, hangs up. No pitch, no asking for the right number |
| 4 | "I'm driving, call me later" | Takes a window, fires `flag_callback`, does not pitch |
| 5 | "Not interested" | One line, hangs up. No why, no counter-offer |
| 6 | "Take me off your list" | Acknowledges, ends, `do_not_call: true` |
| 7 | "I never filled out a form" | Explains once, then books or drops |
| 8 | Voicemail greeting | Leaves the message once, hangs up |
| 9 | Lead wants to reschedule an existing booking | Reschedule flow, looks up by `lead_phone` |
| 10 | "No thanks" to add-ons, then books | Must **not** trip not-interested |
| 11 | Lead answers in Spanish | Switches, keeps outbound framing |
| 12 | Lead asks the price of a deep tissue | FAQ/pricing via `get_services`, returns to booking |
| 13 | Lead asks for a human | Transfer to `+1 626 890 8897` |
| 14 | `lead_first_name` unset | Falls back to "am I speaking with the person who filled out our booking form?" |
| 15 | Lead says a bad time, then changes their mind | Routes back into booking |

Scenario 10 is the important regression: a booking-flow "no" must not be read as
refusing the call.
