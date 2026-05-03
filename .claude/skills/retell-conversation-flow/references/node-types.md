# Retell Conversation Flow — Node Types Reference

Complete schema for every node type. Read when picking a node type or writing JSON.

## Table of Contents

1. [`conversation`](#1-conversation--standard-dialog-node) — multi-turn dialog
2. [`subagent`](#2-subagent--conversation--tool-calling) — dialog + tools
3. [`transfer_call`](#3-transfer_call--live-transfer) — cold / warm / agentic warm
4. [`end`](#4-end--terminate-the-call) — close call
5. [`press_digit`](#5-press_digit--ivr-navigation) — DTMF
6. [`branch`](#6-branch--logic-split-no-agent-turn) — pure routing
7. [`extract_dynamic_variables`](#7-extract_dynamic_variables--structured-extraction) — typed extraction
8. [`code`](#8-code--inline-javascript) — JS computation
9. [`sms`](#9-sms--send-sms-during-call) — text mid-call
10. [`mcp`](#10-mcp--call-an-mcp-server-tool) — Model Context Protocol
11. [`function`](#11-function--custom-tool-call) — bespoke webhook

Plus: [Tools](#tools--three-ways-to-call-external-systems), [Per-node settings](#per-node-settings), [Global node setting](#global-node-setting).

Every node has: `id`, `type`, `name`, `display_position`, plus type-specific fields below.

---

## 1. `conversation` — Standard dialog node

The workhorse. Agent speaks based on `instruction.text`, then evaluates `edges[]` after the user's next turn.

```json
{
  "type": "conversation",
  "id": "node-collect-name",
  "name": "Collect Name",
  "instruction": { "type": "prompt", "text": "say \"What's your first and last name?\"" },
  "edges": [
    {
      "id": "edge-name-collected",
      "transition_condition": { "type": "prompt", "prompt": "Caller has provided their full name" },
      "destination_node_id": "node-collect-phone"
    }
  ],
  "skip_response_edge": { ... },
  "always_edge": { ... },
  "interruption_sensitivity": 0.9,
  "start_speaker": "agent"
}
```

**Cannot call tools.** Use `subagent` if you need tools mid-dialog.

---

## 2. `subagent` — Conversation + tool calling

A conversation node that **can also invoke tools** during the dialogue turn. Use when a step needs both natural conversation **and** the ability to call MCP tools / custom functions / SMS / agent transfers.

```json
{
  "type": "subagent",
  "id": "node-booking-assistant",
  "name": "Booking Assistant",
  "instruction": { "type": "prompt", "text": "Help the caller pick a slot. Use check_availability tool to look up open times. Then offer the slot conversationally." },
  "tool_ids": ["check_availability", "create_booking"],
  "edges": [ ... ]
}
```

> **⚠️ Field name is `tool_ids` (plural, array of tool_id strings) — NOT `tools`.** Retell's import endpoint rejects a `tools` field on subagent nodes with an opaque oneOf-mismatch error. The strings inside `tool_ids` must match `tool_id` values from `conversationFlow.tools[]`.

**vs plain `conversation`:** plain conversation can't call tools at all. Subagent allows fluid weaving — "let me check… ok, I see two slots…".

**vs separate `function` node:** subagent is right when the LLM should *decide* whether to call the tool based on context. Function node is right when the tool call is a deterministic step in a fixed flow ("after collecting all 5 fields, always create a ticket").

Default to function node. Use subagent only when you specifically want LLM-driven tool invocation.

---

## 3. `transfer_call` — Live transfer

Transfers to a phone number or SIP URI. Has a single `edge` (not `edges[]`) for the failure case.

```json
{
  "type": "transfer_call",
  "id": "node-transfer-payroll",
  "name": "Transfer to Payroll",
  "instruction": { "type": "prompt", "text": "Transferring you to our payroll team now. Please hold." },
  "transfer_destination": { "type": "predefined", "number": "+12096086888" },
  "transfer_option": {
    "type": "cold_transfer",
    "show_transferee_as_caller": true,
    "enable_bridge_audio_cue": true
  },
  "edge": {
    "id": "edge-transfer-failed",
    "transition_condition": { "type": "prompt", "prompt": "Transfer failed" },
    "destination_node_id": "node-fallback-ticket"
  },
  "global_node_setting": { "condition": "When user is angry or requests a human agent" }
}
```

### Transfer destination types

| Type | Format |
|---|---|
| `predefined` | E.164 number, e.g., `"+12096086888"` |
| Dynamic variable | `"{{transfer_number}}"` resolved at runtime |
| SIP URI | `"sip:user@domain"` |

### Three transfer modes

1. **Cold transfer** — Agent says closing line, drops the call onto destination via SIP INVITE (default) or SIP REFER. No verification destination answered. Fastest. Use for low-complexity transfers when destination is reliable.

2. **Warm transfer** — Agent stays briefly involved. Detects whether human picked up, can play hold music, can leave a private whisper message before bridging. Default 30s timeout for human detection (`agent_detection_timeout_ms`). Use when receiving party benefits from context.

3. **Agentic warm transfer** — A dedicated transfer agent (configurable, with its own version) has a **two-way conversation** with the destination, then decides whether to bridge or cancel. Most powerful but adds latency. Use when destination is itself an IVR or you want negotiation before connecting.

### Always wire `Transfer failed`

Default destination: graceful fallback (apology + ticket creation + end), not silent dead-end. The `edge` field is singular — only fires on the magic string `"Transfer failed"`.

---

## 4. `end` — Terminate the call

```json
{
  "type": "end",
  "id": "node-close-call",
  "name": "Close Call",
  "instruction": { "type": "prompt", "text": "Politely end the call: \"Thanks so much for calling. Have a great day, {{caller_name}}!\"" },
  "speak_during_execution": true
}
```

Plays a closing line then hangs up. The instruction text is what the agent says before hangup.

---

## 5. `press_digit` — IVR navigation

Used to navigate IVR menus during outbound calls — agent automates keypad inputs to route through phone trees.

```json
{
  "type": "press_digit",
  "id": "node-press-digit",
  "name": "Press Digit",
  "instruction": {
    "type": "prompt",
    "text": "Press 1 for support, 2 for billing. Use keywords like 'Scheduling' or 'Appointments' if speech-prompted. Call end_call if the IVR routes to the wrong company. Respond with NO_RESPONSE_NEEDED during hold music."
  },
  "delay_ms": 1000,
  "edges": []
}
```

### Configuration tips

- **Specify allowed keywords** the agent should listen for in the IVR prompt AND keywords to avoid (false positives).
- **Direct sequences are preferred when known**: `"Press 1 to reach support"`.
- **Behavior rules to include**: speak department names when IVR accepts speech; press digit only when IVR explicitly says "press X"; call `end_call` if routed wrong; `NO_RESPONSE_NEEDED` during hold.
- `delay_ms` waits before pressing — gives the IVR time to finish prompting.

### Post-call IVR fields

For IVR-heavy outbound flows, configure these 9 fields in `post_call_analysis_data`: `hit_ivr`, `reached_human`, `ivr_loop`, `ivr_type`, `ivr_outcome`, `ivr_steps_count`, `ivr_retries_count`, `ivr_path`, `ivr_notes`, `ivr_tree_text`.

### Pitfall

IVRs that detect human voices first will trip your agent's begin-message into the IVR. Set `begin_message_delay_ms` and use `interruption_sensitivity` carefully on outbound IVR-traversing flows.

---

## 6. `branch` — Logic Split (no agent turn)

Evaluates conditions and routes immediately on entry — no TTS produced, no waiting. Designed to decompose complex multi-condition logic that would otherwise stack inside a conversation node's edges.

```json
{
  "type": "branch",
  "id": "node-route-by-tier",
  "name": "Route by Customer Tier",
  "edges": [
    {
      "id": "edge-vip",
      "transition_condition": {
        "type": "equation",
        "equations": [{ "left": "{{customer_tier}}", "operator": "==", "right": "VIP" }]
      },
      "destination_node_id": "node-vip-handler"
    },
    {
      "id": "edge-overdue",
      "transition_condition": {
        "type": "equation",
        "equations": [
          { "left": "{{balance}}", "operator": ">", "right": "0" },
          { "left": "{{days_overdue}}", "operator": ">=", "right": "30" }
        ],
        "operator": "&&"
      },
      "destination_node_id": "node-collections"
    }
  ],
  "else_edge": {
    "id": "edge-default",
    "transition_condition": { "type": "prompt", "prompt": "Else" },
    "destination_node_id": "node-standard-handler"
  }
}
```

### Verified rules

- Transition fires immediately on entry — no agent turn taken.
- `else_edge` is **mandatory** — default fallback when no condition matches.
- Equation conditions evaluate first (top-to-bottom), then prompt conditions.
- Available as a global node (set `global_node_setting`).
- Supports `finetune_transition_examples` for refining ambiguous prompt conditions.

### When branch vs prompt-based edges on conversation node

- **`branch`** for deterministic routing on dynamic-variable values — no LLM inference, no latency, no variance.
- **prompt-based edges** when routing depends on what the caller said in their last turn.

---

## 7. `extract_dynamic_variables` — Structured extraction

Pulls typed variables out of conversation history. Built-in lightweight tool that doesn't need a webhook. **Doesn't speak.**

```json
{
  "type": "extract_dynamic_variables",
  "id": "node-extract-intent",
  "name": "Extract Intent",
  "variables": [
    { "name": "customer_name", "type": "string", "description": "Customer's full name" },
    { "name": "appointment_date", "type": "string", "description": "Date in YYYY-MM-DD format" },
    { "name": "is_urgent", "type": "boolean", "description": "Whether this is urgent" },
    { "name": "issue_type", "type": "enum", "choices": ["billing", "tech", "general"], "description": "Caller's primary issue" },
    { "name": "ticket_count", "type": "number", "description": "Past ticket count if mentioned" }
  ],
  "edges": [ ... ],
  "else_edge": { ... }
}
```

### Verified types

`Text` (string), `Number`, `Enum` (with `choices: [...]`), `Boolean`. No others.

### Each variable requires

- `name` — short, used as `{{var_name}}` reference
- `description` — the LLM uses this to know what to extract
- `type` (above)
- For enum: `choices: []`

### Best-practice patterns

- **After a function/MCP/code call** — map response payload into named variables for downstream use. E.g., extract `patient_id` from a DB lookup so the next sentence can say "Got it, your ID is {{patient_id}}."
- **Before a `branch` node** — convert free-form caller speech into structured values that equation conditions can route on.
- **Don't use as validation** — it doesn't validate, it extracts. Pair with a branch for validation.

### Per-node LLM override

You can pick a different model for extraction (e.g., a stronger model when accuracy matters, a faster one when it's simple).

---

## 8. `code` — Inline JavaScript

Execute custom JS during the call **without an external server**. Use for: date/time math, validation, format conversion, simple lookups in arrays, basic conditional computation. Anything more complex belongs in a function/MCP node.

```json
{
  "type": "code",
  "id": "node-compute-age",
  "name": "Compute Age",
  "code": "const dob = new Date('{{customer_dob}}'); const ageMs = Date.now() - dob.getTime(); const age = Math.floor(ageMs / (365.25 * 24 * 60 * 60 * 1000)); return { age };",
  "wait_for_result": true,
  "speak_during_execution": false,
  "enable_typing_sound": true,
  "edges": [],
  "else_edge": { ... }
}
```

| Field | Effect |
|---|---|
| `code` | JS source — has access to dynamic variables via `{{}}` substitution |
| `wait_for_result` | Block flow until code returns. Almost always `true`. |
| `speak_during_execution` | Agent speaks during execution — rarely needed for inline JS (usually fast) |
| `enable_typing_sound` | Plays a typing sound while running — UX cue that "the system is working" |

### When code over function (custom webhook)

- Pure computational, no external API → `code`
- Needs a database, CRM, or third-party API → `function` or `mcp`
- Fast (<200ms) and pure → `code` avoids network latency
- Has secrets/credentials that shouldn't ship to the client → `function` (server-side)

Code node return values become dynamic variables for downstream nodes. Always pair with `else_edge` for execution failure.

---

## 9. `sms` — Send SMS during call

Sends an SMS without leaving the call.

```json
{
  "type": "sms",
  "id": "node-send-confirmation",
  "name": "Send Booking SMS",
  "from_number_type": "agent_number",
  "to_number": "{{customer_phone}}",
  "content": { "type": "prompt", "text": "Tell the caller their appointment is confirmed for {{appointment_date}} at {{appointment_time}}." },
  "edges": [ ... ]
}
```

| Aspect | Detail |
|---|---|
| Sending number | SMS-approved Retell number (preset templates only) OR your own A2P-approved number (custom dynamic content) |
| Recipient | Defaults to caller; can override with static number or `{{variable}}` |
| Content | A2P number: write a prompt for the agent to infer SMS content, or use a static body. Retell number: fixed template, no edits possible. |
| Transition | Fires within ~2 seconds whether send succeeded or failed. Always handle both via edges. |
| Bidirectional | Can also receive SMS during the call (text/images/audio/video) on compatible numbers |

**Common pattern:** after closing a sales call, send an SMS with the booking link or confirmation. Avoids a follow-up email.

---

## 10. `mcp` — Call an MCP server tool

Invokes a tool hosted on a Model Context Protocol server. **Alternative to custom function tools** — useful when tools are exposed via an MCP server (Zapier, n8n, AWS Lambda + MCP wrapper) and you don't want to redefine them per agent.

```json
{
  "type": "mcp",
  "id": "node-lookup-customer",
  "name": "Look up Customer",
  "mcp_server_url": "https://mcp.example.com/sse",
  "headers": { "Authorization": "Bearer {{auth_token}}" },
  "query_params": { "customer_id": "{{customer_id}}" },
  "tool_name": "lookup_customer",
  "response_variables": { "customer_tier": "$.tier", "lifetime_value": "$.ltv" },
  "edges": [ ... ]
}
```

### MCP node vs custom function

- **Custom function** — HTTP webhook, defined per-agent, JSON Schema parameters. Best for one bespoke webhook per use case.
- **MCP node** — remote tool catalog, agent picks which tool to call from server's exposed list. Best when you have many tools across many agents (centralized) — e.g., a Zapier MCP exposing 30 actions.

Sub-second latency preserved during MCP calls per Retell benchmarks.

---

## 11. `function` — Custom tool call

Function nodes call a custom tool defined in `conversationFlow.tools[]`. Execute deterministically when the agent enters them — unlike subagent/conversation, the LLM doesn't decide whether to call.

```json
{
  "type": "function",
  "id": "node-create-ticket",
  "name": "Create Ticket",
  "tool_id": "create_ticket",
  "tool_type": "local",
  "wait_for_result": true,
  "edges": [],
  "always_edge": {
    "id": "edge-after-tool",
    "transition_condition": { "type": "prompt", "prompt": "Always" },
    "destination_node_id": "node-ticket-confirmation"
  }
}
```

> **`tool_type` is required by Retell's import schema.** Use `"local"` for custom tools defined in `conversationFlow.tools[]`. Without it, import fails with a oneOf-mismatch error citing every other node type's required field.
>
> **`wait_for_result: true`** is almost always what you want — it blocks the flow until the tool returns so downstream nodes can read response variables. The default is `false`, which fires the next node immediately and your `{{response_var}}` will be empty.

Tool config (in `conversationFlow.tools[]`) — see next section.

---

## Tools — Three ways to call external systems

| Mechanism | Use when |
|---|---|
| `function` node + custom tool | Bespoke webhook per use case; you own the endpoint |
| `mcp` node | Many tools exposed via an MCP server — agent picks which to call |
| `subagent` node + attached tools | LLM should fluidly weave tool calls into multi-turn conversation |

### Custom tool definition

Lives in `conversationFlow.tools[]`:

```json
{
  "tool_id": "create_ticket",
  "name": "create_ticket",
  "type": "custom",
  "description": "Create a ticket in CRM. Call after collecting required fields.",
  "method": "POST",
  "url": "https://example.com/webhook/create-ticket",
  "args_at_root": true,
  "parameter_type": "form",
  "headers": {},
  "query_params": {},
  "timeout_ms": 120000,
  "speak_during_execution": true,
  "execution_message_description": "Just a moment please, this will only take a second.",
  "parameters": {
    "type": "object",
    "required": ["caller_name", "summary"],
    "properties": {
      "caller_name": { "type": "string", "description": "Caller full name" },
      "summary": { "type": "string", "description": "Call summary" },
      "collected_fields": { "type": "object" }
    }
  },
  "response_variables": {
    "ticket_id": "$.ticket_id",
    "ticket_success": "$.ticket_success"
  }
}
```

### Critical settings

| Field | Why |
|---|---|
| `speak_during_execution: true` | Without it, agent goes silent during slow webhooks (5–15s) — caller thinks call dropped |
| `execution_message_description` | Pins exact filler line; without it, LLM improvises a different line every call |
| `timeout_ms: 120000` | Cold-start webhooks often exceed default; bump to 2 min for n8n / serverless |
| `response_variables` | JSONPath → variable name; exposes return values to subsequent nodes |
| `args_at_root: true` | Production-validated default. Sends LLM-extracted args spread at the body root (e.g., `{ "phone": "...", "call": {...} }`) instead of nested under `args:{}`. Your webhook must read fields from the body root. |
| `parameter_type: "form"` | Production-validated default. The other valid value is `"json"`. `"form"` is what working production agents use. |

### URL hygiene

Placeholder URLs (`TODO.example.com`) silently fail at runtime — call breaks, no clear error. Always real URL or remove the tool reference.

---

## Per-node settings

Every node accepts these optional fields:

| Field | Purpose |
|---|---|
| `display_position` | Canvas X/Y (visual editor only — does not affect runtime) |
| `interruption_sensitivity` | Per-node override of agent-level value (0.0–1.0) |
| `start_speaker` | Per-node override (rare; mostly on the start node) |
| `delay_ms` | Pause before executing node action |
| `global_node_setting` | Makes this node available as a global trigger |

---

## `global_node_setting`

Any node can be made global by adding `global_node_setting`. It can be triggered from **any** node when its condition matches.

```json
"global_node_setting": {
  "condition": "When user expresses acute emotional distress, mentions self-harm, or says they cannot continue"
}
```

### Common global nodes

| Trigger | Node type | Purpose |
|---|---|---|
| Acute distress | `transfer_call` or `conversation` | Empathy + escalate |
| Death / fatality | `conversation` then `end` | Condolence, no ticket, clean exit |
| "Speak to a human" | `transfer_call` | Direct transfer |
| FAQ / general question | `conversation` (with KB) | Answer + return to caller |
| Topic change | `branch` or `conversation` | Route to relevant flow |

### Rules

1. **Conditions must be specific.** "When user is upset" is too loose — fires mid-collection on minor frustration. Use "When user expresses acute emotional distress…" instead.
2. **Pair with a return path** when side-trip is informational (FAQ → return to caller).
3. **Test interaction with mid-collection state** — globals can yank caller out of intake mid-flow. Decide whether side-trip should preserve or reset collected fields.
4. **Order matters at runtime** — Retell evaluates global conditions per turn. If two globals could match, refine the prompts.
