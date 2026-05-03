# Standard Patterns

Reusable node-graph shapes for common conversation-flow problems. Don't write a flow from scratch — pick the closest pattern below and customize it.

---

## Pattern 1: Standard Collection Pattern (most common)

The proven 4-node shape for any flow that collects fields, calls a tool (e.g., create ticket / book appointment), and confirms back.

```
[COLLECTION NODE]            (conversation, multi-turn, conditional edges)
   "Collect N fields one per turn..."
   edges[] → matches "all fields collected"
        ↓
[SUBMIT NODE]                (conversation, single-line, skip_response_edge)
   "I'm submitting your request now."
   skip_response_edge → "Skip response"
        ↓
[TOOL NODE]                  (function node)
   tool: create_ticket
   speak_during_execution: true
   execution_message_description: "Just a moment please, this will only take a second."
   always_edge → "Always"
        ↓
[CONFIRMATION NODE]          (conversation, single-line readback + branching)
   "Your reference number is {{ticket_id}}."
   edges[] → close_call | next_topic | direct transfers
```

### Why each node is separate

| Node | Why split off |
|---|---|
| Collection | Multi-turn intake; conditional edges fire only after the last field |
| Submit | Lets `skip_response_edge` fire silently into the tool — no extra agent turn |
| Tool | Function node isolates speak-during-execution behavior |
| Confirmation | Single readback + branches; keeps closing logic out of the collection node |

### Why doing it all in one node fails

- LLM forgets it already spoke a closing and re-delivers it
- Conditional edge can fire before the closing
- Tool call has no clean "wait" surface
- Repetition rules degrade because the LLM blends multiple stages

### When to use

Any flow that: collects user input → calls a backend → reads result back. Booking, ticket creation, intake, registration, complaint logging.

Template available at `assets/collection-flow-template.json`.

---

## Pattern 2: Transfer with Fallback

Cold or warm transfer with a graceful fallback when the dial fails.

```
[QUALIFICATION NODE]         (conversation — verify caller wants transfer)
   "Got it, let me connect you to [department]. Please hold."
   edges[] → matches "caller confirmed transfer"
        ↓
[TRANSFER NODE]              (transfer_call)
   transfer_destination: ...
   transfer_option: cold_transfer | warm_transfer | agentic_warm_transfer
   edge (singular) → "Transfer failed" → FALLBACK NODE
        ↓ (if successful, call ends naturally)
[FALLBACK NODE]              (conversation)
   "I wasn't able to connect you. Let me create a ticket so someone follows up."
   skip_response_edge → CREATE TICKET → CONFIRMATION → CLOSE
```

### Decision: cold vs warm vs agentic warm

| Mode | When to use |
|---|---|
| Cold | Destination is a reliable team / direct line, low complexity. Fastest. |
| Warm | Receiving party benefits from context. Worth the 30s human-detect timeout. |
| Agentic warm | Destination is itself an IVR, or you want negotiation before connecting. Most powerful, adds latency. |

### Always wire `Transfer failed`

The singular `edge` field on `transfer_call` only fires on the magic string `"Transfer failed"`. Default destination should be a graceful fallback (apology + ticket creation + end), never silent dead-end.

Template at `assets/transfer-with-fallback.json`.

---

## Pattern 3: Code → Extract → Branch (deterministic mid-call routing)

Compute something, extract structured fields, route on the result — all without an agent turn.

```
[CONVERSATION NODE]          (collect raw caller input)
   "What's your date of birth?"
   edges[] → matches "DOB provided"
        ↓
[EXTRACT NODE]               (extract_dynamic_variables)
   variables: [{ name: "dob_iso", type: "string", description: "ISO date YYYY-MM-DD" }]
   edges[] → "Always" → CODE NODE
   else_edge → REPROMPT NODE
        ↓
[CODE NODE]                  (code, inline JS)
   const dob = new Date('{{dob_iso}}');
   const age = Math.floor((Date.now() - dob.getTime()) / (365.25 * 24 * 60 * 60 * 1000));
   return { age };
   wait_for_result: true
   edges[] → "Always" → BRANCH NODE
   else_edge → APOLOGY NODE
        ↓
[BRANCH NODE]                (branch — deterministic split)
   edges[]:
     - {{age}} >= 65   → SENIOR PATH
     - {{age}} >= 18   → ADULT PATH
   else_edge          → MINOR PATH
```

### Why this pattern

- The collection step is one short conversation node.
- Extract converts free-form caller speech ("July 4th 1985") into a structured value.
- Code does the math without a webhook round-trip.
- Branch routes deterministically — no LLM inference, no variance.

The whole sequence after the collection node is silent — no agent turn between the answer and the route.

Template at `assets/code-and-branch-pattern.json`.

---

## Pattern 4: Pre-Call Lookup → Personalized Opening

For inbound calls where you want to greet returning callers by name without asking.

```
[BEGIN] (start_speaker: "agent")
   ↓
[BRANCH NODE]                (branch — check if known caller)
   edges[]:
     - {{caller_name}} exists  → KNOWN OPENING
   else_edge                   → NEW OPENING
        ↓
[KNOWN OPENING] (conversation)
   "Hi {{caller_name}}, welcome back. How can I help you today?"
        ↓
[NEW OPENING] (conversation)
   "Hi, this is [Agent] with [Company]. May I have your name?"
```

### Pre-call data flow

Inject `{{caller_name}}` (and any other known fields) via the inbound webhook. Retell calls your webhook with the caller's number; you respond with `{"retell_llm_dynamic_variables": {"caller_name": "Sarah", "customer_id": "C-1234"}}`. All values must be **strings**.

If you don't have a webhook lookup, the branch falls through to `NEW OPENING` automatically.

---

## Pattern 5: Global Distress / Fatality / Human-Request

Cross-cutting interrupts. Add `global_node_setting` to make any node available from anywhere.

```
[GLOBAL DISTRESS]
   global_node_setting.condition:
     "When user expresses acute emotional distress, mentions self-harm,
      or states they cannot continue the call"
   instruction: empathy line
   then transfer_call → live human team

[GLOBAL FATALITY] (healthcare/services agents only)
   global_node_setting.condition:
     "When user reports the death of a member, patient, or family member"
   instruction: condolence
   skip_response_edge → end (no ticket, no further questions)

[GLOBAL HUMAN REQUEST]
   global_node_setting.condition:
     "When user explicitly asks to speak with a person, agent, or representative,
      OR insists on a human after Aubrey has offered to help"
   instruction: "Got it — let me connect you. Please hold."
   then transfer_call → default routing

[GLOBAL FAQ HANDLER]
   global_node_setting.condition:
     "When user asks a general informational question about the company
      (services, hours, locations, contact info)"
   instruction: KB-backed answer
   then return_to_caller (back to the node they came from)
```

### Tuning rules

- **Specific conditions only.** "When user is upset" is too loose — it'll hijack collection on minor frustration.
- **Pair with return path** when informational. FAQ globals return to the origin node. Distress / fatality / transfer globals end or transfer.
- **Test mid-flow scenarios.** Make sure routine answers don't accidentally satisfy the condition.

---

## Pattern 6: IVR Navigation (Outbound)

Outbound agent that has to traverse a phone tree to reach the right person.

```
[BEGIN]                      (start_speaker: "agent", begin_message_delay_ms: 1500)
   ↓
[CONVERSATION NODE]          (initial spoken intro, only if a human picks up immediately)
   instruction: short hello, listen for IVR
   edges[]:
     - "Caller is a human and is asking why we called"  → HUMAN ROUTING
     - "An IVR is detected (recording, menu options spoken)"  → IVR ENTRY
        ↓
[IVR ENTRY = press_digit]    (press_digit)
   instruction: "Press 1 for [target dept]. Speak 'Customer Service' if speech is offered.
                 Call end_call if routed to wrong company. Use NO_RESPONSE_NEEDED on hold music."
   delay_ms: 1000
   edges[] → matches "Reached a human in [target dept]" → BUSINESS LOGIC NODE
   edges[] → matches "Stuck in IVR loop" → end_call
        ↓
[BUSINESS LOGIC NODE]        (conversation — actual purpose of the call)
   ...
```

### Required IVR fields in `post_call_analysis_data`

```json
{ "name": "hit_ivr",            "type": "boolean" },
{ "name": "reached_human",      "type": "boolean" },
{ "name": "ivr_loop",           "type": "boolean" },
{ "name": "ivr_type",           "type": "string"  },
{ "name": "ivr_outcome",        "type": "enum",   "choices": ["reached_target", "wrong_company", "voicemail", "abandoned"] },
{ "name": "ivr_steps_count",    "type": "number" },
{ "name": "ivr_retries_count",  "type": "number" },
{ "name": "ivr_path",           "type": "string"  },
{ "name": "ivr_notes",          "type": "string"  },
{ "name": "ivr_tree_text",      "type": "string"  }
```

These are critical for debugging IVR runs — without them you can't tell why a campaign failed.

### Pitfall

IVRs that detect human voices first will trip the agent's begin-message into the IVR. Set `begin_message_delay_ms: 1500` and tune `interruption_sensitivity` lower (~0.3) on outbound IVR-traversing flows.

---

## Pattern 7: Subagent for Multi-Tool Conversation

When the agent needs to weave multiple tool calls into a single fluent conversation (e.g., booking that requires availability check + calendar create + SMS confirmation).

```
[SUBAGENT NODE]              (subagent — has all booking-related tools attached)
   instruction: "Help the caller book an appointment. Use check_availability to find slots,
                 confirm with the caller, then use create_booking. Once confirmed, use
                 send_sms_confirmation. Speak naturally between tool calls."
   tool_ids: [check_availability, create_booking, send_sms_confirmation]
   edges[] → matches "booking confirmed and SMS sent" → CLOSE
   edges[] → matches "caller declined all offered slots" → ALTERNATIVE PATH
```

> **Field name is `tool_ids` (plural, array of tool_id strings).** Each entry must match a `tool_id` defined in `conversationFlow.tools[]`. A `tools` field (plural-without-`_ids` suffix) on a subagent node will fail Retell's import oneOf schema with an opaque error.

### When subagent is right

- The order of tool calls depends on the conversation (e.g., availability first, only book if caller likes the slot)
- Multiple tool calls happen in one back-and-forth
- The agent should narrate naturally between calls

### When function nodes are right instead

- Single deterministic tool call after collection (use Pattern 1)
- Tool calls happen at fixed points in a fixed flow
- You want easier-to-test, deterministic execution

---

## Composing patterns

Real agents use multiple patterns. A typical inbound healthcare agent might have:

- **Pattern 4** (pre-call lookup → personalized opening)
- **Pattern 1** (Standard Collection × N flows: appointment, refill, billing, etc.)
- **Pattern 2** (Transfer with fallback to clinical staff)
- **Pattern 5** (Global distress, fatality, human-request)
- **Pattern 6** (rare; only for outbound IVR campaigns)

Lay out the graph on paper before writing JSON. Once the patterns are clear, the JSON writes itself.
