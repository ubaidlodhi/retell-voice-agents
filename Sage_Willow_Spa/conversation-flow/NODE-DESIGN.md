# Aria — Conversation Flow Node Design

**Basis:** structural patterns lifted from `Sample - Risen Strategic - Inbound Receptionist (Conversation Flow).json`, applied to the flows in [`CURRENT-FLOWS-SPEC.md`](CURRENT-FLOWS-SPEC.md).

**Constraint:** the flows themselves do not change. This document only decides *which node type* implements each step already specified.

Status: **design only — nothing built.**

---

## 1. Patterns observed in the Risen sample

| Pattern | Node type | How Risen uses it | Key fields |
|---|---|---|---|
| Opening + intent routing | `conversation`, `start_speaker: "agent"` | One greeting node with 5 prompt-condition edges, one per flow | `edges[]` with `transition_condition.type: "prompt"` |
| Deterministic routing on a variable | `branch` | `node-book-router` checks `{{existing_appointment}} contains BOOKED` | equation `edges[]` + mandatory `else_edge` |
| Multi-turn dialog that needs tools mid-conversation | `subagent` | `node-book-assistant` owns the whole booking dialog | `tool_ids: []`, long `instruction`, outcome `edges[]` |
| Single deterministic tool call | `function` | `node-find-check` calls `find_appointment` then moves on | `tool_id`, `always_edge`, `wait_for_result: true` |
| Cross-cutting interrupt | any node + `global_node_setting` | FAQ, human request, stop/not-interested | `condition`, `cool_down`, `positive_finetune_examples`, `go_back_conditions` |
| Silent transition | `skip_response_edge` | stop → hangup with no extra agent turn | — |
| Human handoff | `transfer_call` | warm transfer with a failure path | `transfer_destination`, `transfer_option`, `edge` (= "Transfer failed") |
| Terminate | `end` | `node-hangup` | — |

Risen totals: **33 nodes** — 20 `conversation`, 5 `function`, 4 `subagent`, 2 `branch`, 1 `transfer_call`, 1 `end`. Seven tools, all pointed at one webhook.

**The important structural idea:** Risen does not decompose booking into a rigid collect → tool → confirm chain. It hands the entire booking dialog to **one `subagent`** holding `["check_availability", "book_appointment"]`, and enforces ordering through a long, very explicit instruction. The graph handles *routing between flows*; the subagent handles *conversation within a flow*.

---

## 2. Our node graph

37 nodes. Same type distribution and same architectural split as Risen.

```
                          ┌────────────────────────┐
                          │ node-greeting (conv)   │  start_speaker: agent
                          └───────────┬────────────┘
        ┌──────────┬──────────┬───────┼────────┬──────────┬──────────┐
        ▼          ▼          ▼       ▼        ▼          ▼          ▼
     BOOK       CANCEL   RESCHEDULE  WHAT-IS  PRICING  CALLBACK   CLOSE
        │          │          │       │        │          │          │
        └──────────┴──────────┴───────┴────────┴──────────┴──────────┘
                                      │
                             node-hangup (end)

GLOBALS (reachable from any node):
  FAQ · HUMAN → TRANSFER → (fail) CALLBACK · EMERGENCY · CRISIS
  INAPPROPRIATE · SPAM · OFF-TOPIC · RECORDING-DECLINE · CLOSE
```

### 2.1 Entry

| id | type | purpose | edges |
|---|---|---|---|
| `node-greeting` | conversation | Opening line + recording disclosure + intent routing | 7 prompt edges → book / cancel / reschedule / what-is / pricing / callback / close |

Opening line stays verbatim from the current agent:
> "Hi, this is Aria from Sage and Willow Spa. Just to let you know, this call is recorded for quality purpose. How can I help you today?"

### 2.2 Booking (F1)

| id | type | tools | purpose |
|---|---|---|---|
| `node-book-service` | conversation | — | Identify which massage. Names the seven only if asked; **never describes** |
| `node-fetch-services` | function | `get_services` | Pull live catalog → `always_edge` |
| `node-book-assistant` | **subagent** | `get_staff`, `get_slots` | Duration + price offer, day/time, therapist *only if raised*, slot offer |
| `node-book-addons` | conversation | — | "Want to add any enhancements?" — names none until yes |
| `node-book-details` | conversation | — | Spell name (no readback) → confirm `{{user_number}}` |
| `node-book-readback` | conversation | — | Single consolidated readback → `skip_response_edge` |
| `node-book-submit` | function | `book_appointment` | → `always_edge` |
| `node-book-confirm` | conversation | — | **One line.** "You're all set for Tuesday at two PM." |
| `node-book-failed` | conversation | — | Retry once, else offer callback |

**Couples** is not a separate branch — it's a conditional inside `node-book-assistant`'s instruction plus `numberOfParticipants: 2` on submit, exactly as specified in §6 F1.

### 2.3 Cancel (F2)

| id | type | tools | purpose |
|---|---|---|---|
| `node-find-cancel` | function **GLOBAL** | `get_booking` | Lookup by `{{user_number}}` → `always_edge` |
| `node-cancel-offer` | conversation | — | One-line readback + offer reschedule once |
| `node-cancel-confirm` | conversation | — | Explicit yes gate |
| `node-cancel-do` | function | `cancel_booking` | → `always_edge` |
| `node-cancel-done` | conversation | — | One-line confirm → "Anything else?" |
| `node-cancel-notfound` | conversation | — | "Not finding anything under that number…" |

Routing uses an **equation edge** on `{{bookings_count}} == 0` → `node-cancel-notfound`. Never mentions the 24-hour policy here (§6 F2).

### 2.4 Reschedule (F3)

| id | type | tools | purpose |
|---|---|---|---|
| `node-find-reschedule` | function **GLOBAL** | `get_booking` | → `always_edge` |
| `node-reschedule-confirm` | conversation | — | One-line readback + ask new day/time |
| `node-reschedule-assistant` | **subagent** | `get_slots` | Offer 2–3, handle "same time" band mapping |
| `node-reschedule-do` | function | `reschedule_booking` | → `always_edge` |
| `node-reschedule-done` | conversation | — | Confirm new day/time once |
| `node-reschedule-failed` | conversation | — | Callback fallback |

### 2.5 Info

| id | type | tools | purpose |
|---|---|---|---|
| `node-what-is-x` | conversation | — | 2-sentence KB description → "Want me to check pricing?" |
| `node-pricing` | **subagent** | `get_services` | Quote → "Want to book that?" |
| `node-global-faq` | conversation **GLOBAL** | — | Hours, parking, payment, gift cards, attire, prenatal, couples. **States the 24-hour courtesy when asked** |

### 2.6 Human handoff / callback (F7)

| id | type | tools | purpose |
|---|---|---|---|
| `node-global-human` | conversation **GLOBAL** | — | Soft first ask → offer to help directly |
| `node-handoff-say` | conversation | — | "Sure — hold on, let me connect you" → `skip_response_edge` |
| `node-handoff-transfer` | transfer_call | — | Cold transfer + `edge` = "Transfer failed" |
| `node-handoff-callback` | function | `flag_callback` | → `always_edge` |
| `node-handoff-say-callback` | conversation | — | "I couldn't reach anyone, but I've passed your message along" |

### 2.7 Escalation globals (§7)

| id | type | after speaking |
|---|---|---|
| `node-global-emergency` | conversation **GLOBAL** | `skip_response_edge` → hangup |
| `node-global-crisis` | conversation **GLOBAL** | `skip_response_edge` → hangup |
| `node-global-inappropriate` | conversation **GLOBAL** | one deflection; second → hangup |
| `node-global-spam` | conversation **GLOBAL** | `skip_response_edge` → hangup |
| `node-global-offtopic` | conversation **GLOBAL** | redirect; second push → hangup |
| `node-global-recording-decline` | conversation **GLOBAL** | `skip_response_edge` → hangup |
| `node-close` | conversation **GLOBAL** | closing line → `skip_response_edge` → hangup |
| `node-hangup` | end | — |

Each global gets `positive_finetune_examples` — the Risen pattern — so the classifier is trained rather than relying on prose. Critical for two of ours:
- **Off-topic must not fire on a garbled service name** ("synchrony massage" → Signature). Add negative-shaped examples.
- **Spam vs. genuine human request** turns entirely on intent-to-sell. Risen's `node-global-stop` shows the exact shape to copy.

---

## 3. Tool mapping

All 8 existing tools carry over unchanged — same webhook, same `tool` header, same `args_at_root: true`. Each gains a `tool_id` for node references.

| tool_id | Used by node(s) | Node type |
|---|---|---|
| `get_services` | `node-fetch-services`, `node-pricing` | function, subagent |
| `get_staff` | `node-book-assistant` | subagent |
| `get_slots` | `node-book-assistant`, `node-reschedule-assistant` | subagent |
| `book_appointment` | `node-book-submit` | function |
| `get_booking` | `node-find-cancel`, `node-find-reschedule` | function |
| `cancel_booking` | `node-cancel-do` | function |
| `reschedule_booking` | `node-reschedule-do` | function |
| `flag_callback` | `node-handoff-callback` | function |

`transfer_to_human` becomes a **node** (`transfer_call`), not a tool. `end_call` becomes the **`end` node**.

---

## 4. Where we deviate from Risen — and why

### 4.1 `speak_during_execution` → **off** ⚠️
Risen sets `speak_during_execution: true` with a pinned message on its function nodes. **We must not copy this.** Retell support identified it as the root cause of the fragmented-speech defect we hit:

> "the sentence is interrupted by the tool invocation, as the tool call responds before the agent finishes speaking" → "disable speech during execution and use a typing sound instead for fast tool calls."

All our tool latencies are 600–2600 ms, well inside typing-sound territory. Keep `speak_during_execution: false` + `enable_typing_sound: true`, as set in V27.

> Note: this contradicts the skill's default guidance (Step 5), which predates the support finding. Our production evidence wins.

### 4.2 Transfer is **cold**, not warm
Risen uses `warm_transfer` with bridge audio. Ours is `cold_transfer` / `sip_invite` per the current config. Keep cold — and keep the "Transfer failed" `edge` → callback path, which Risen models correctly.

### 4.3 Booking decomposition — **one decision to make**

Risen puts availability + booking in a single `subagent`. Faithful copying would give us:

```
node-book-service → node-fetch-services → node-book-assistant [get_staff, get_slots, book_appointment]
                                              → node-book-confirm / node-book-failed
```

The design in §2.2 instead keeps `book_appointment` in its **own `function` node**, with add-ons / details / readback as explicit `conversation` nodes.

**Why I'd recommend the split for booking specifically:** every one of these production defects came from one context deciding ordering and confirmation itself —

| Defect | Cause |
|---|---|
| Triple confirmation | readback + execution message + success line in one context |
| Collected name/phone before checking availability | ordering was prompt-enforced, model reordered it |
| Announced add-ons unprompted | same context held the add-on list while answering pricing |
| Claimed to have checked two services when it ran one search | narration and tool state in the same context |

Explicit nodes make those structurally impossible rather than prompt-suppressed. The cost is rigidity: a caller who volunteers everything at once still walks the chain.

**Recommendation:** subagent for *discovery* (duration, day/time, therapist, slot offer — genuinely conversational, benefits from flexibility), explicit nodes for *commitment* (add-ons → details → readback → submit → confirm). That is what §2.2 encodes. Say the word if you'd rather match Risen exactly and put the whole thing in one subagent.

### 4.4 Knowledge base
Risen ships `knowledge_base_ids: []` at flow level. We attach `knowledge_base_cb1d71238e1ba5fe` with `top_k: 2`, `filter_score: 0.75`.

### 4.5 Settings carried from V27
`responsiveness: 0.6` · `interruption_sensitivity: 0.8` · `denoising_mode: noise-cancellation` · `enable_expressive_mode: false` · `voice_speed: 1.0` · `reminder_trigger_ms: 20000` · `reminder_max_count: 2`.

Risen has `enable_backchannel` configured — worth evaluating for us, but as a separate change so its effect is measurable.

---

## 5. Global prompt

Shrinks substantially. Per-flow instructions move into node instructions; the global prompt keeps only what applies on every turn:

1. Identity + recording disclosure
2. Caller context (fact-style: `Phone: {{user_number}}`)
3. **How you talk** — 2-sentence cap, one question per turn, no filler acks, no parroting, no self-narration, no volunteering (the V27 block, verbatim)
4. Pronunciation — phone / durations-as-hours / currency / times / dates / URL
5. Owner anonymity + **the Nicky rule** (sayable as therapist, never as owner)
6. Turn-taking / `NO_RESPONSE_NEEDED`
7. Bilingual rule
8. Defensive variable handling
9. System variables

Estimated ~1,200–1,500 words versus V27's 2,452 — inside Retell's guidance, and per-node instructions are only loaded when that node is active.

---

## 6. Open build decisions

| # | Decision | Default if unspecified |
|---|---|---|
| 1 | Booking: split commitment path (§4.3) or one subagent like Risen? | Split, per §2.2 |
| 2 | `enable_backchannel` on? | Off — change separately so it's measurable |
| 3 | Orphan `get-contact` n8n route — expose or delete? | Leave unexposed |
| 4 | Resolve `serviceId` server-side in n8n (kills the Frankenstein-UUID class permanently)? | Recommended, needs an n8n change |

---

## 7. Build order (when approved)

1. Start from `assets/starter-flow.json`
2. Global prompt (§5)
3. Tools with `tool_id`s (§3)
4. Booking sub-graph → validate
5. Cancel + reschedule sub-graphs → validate
6. Info + callback/transfer
7. Escalation globals with finetune examples
8. `post_call_analysis_data` — carry the 9 fields from spec §9
9. `validate_flow.py` — must pass
10. Flow map + the 15 test scenarios from spec §13
