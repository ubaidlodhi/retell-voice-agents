# Retell AI Conversation Flow — Build Reference

Generic build reference for Retell Conversation Flow agents. Covers the full schema (agent + flow + nodes + edges), every node type, every transition mechanism, configuration knobs, common failure modes, and proven build patterns. Use this as a one-stop reference when building any voice agent.

---

## Table of Contents

1. [Agent-Level Configuration](#1-agent-level-configuration)
2. [Conversation Flow Configuration](#2-conversation-flow-configuration)
3. [Node Types — Full Catalog](#3-node-types--full-catalog)
4. [Edges and Transitions](#4-edges-and-transitions)
5. [Global Nodes](#5-global-nodes)
6. [Tools / Function Nodes](#6-tools--function-nodes)
7. [Dynamic Variables](#7-dynamic-variables)
8. [Post-Call Analysis](#8-post-call-analysis)
9. [Magic Strings](#9-magic-strings)
10. [The Standard Collection Pattern](#10-the-standard-collection-pattern)
11. [Anti-Patterns and Failure Modes](#11-anti-patterns-and-failure-modes)
12. [Prompt Hygiene Rules](#12-prompt-hygiene-rules)
13. [Testing Methodology](#13-testing-methodology)
14. [Edge ID Uniqueness and Schema Validation](#14-edge-id-uniqueness-and-schema-validation)
15. [Final Heuristics](#15-final-heuristics)

---

## 1. Agent-Level Configuration

These settings live at the **top of the agent JSON**, outside `conversationFlow`. They control voice, audio, language, and behavior toggles that apply to the whole call.

```json
{
  "agent_id": "...",
  "channel": "voice",
  "agent_name": "...",
  "language": "en-US",
  "voice_id": "retell-Cimo",
  "max_call_duration_ms": 3600000,
  "interruption_sensitivity": 0.9,
  "normalize_for_speech": true,
  "stt_mode": "accurate",
  "denoising_mode": "noise-and-background-speech-cancellation",
  "data_storage_setting": "everything",
  "post_call_analysis_model": "gpt-4.1",
  "is_published": false,
  "user_dtmf_options": { ... },
  "handbook_config": { ... },
  "post_call_analysis_data": [ ... ],
  "response_engine": {
    "type": "conversation-flow",
    "conversation_flow_id": "..."
  }
}
```

### Key fields

| Field | Purpose | Notes |
|---|---|---|
| `voice_id` | Voice selection | Browse voices in Retell dashboard |
| `language` | Locale | `en-US`, `en-GB`, `es-ES`, etc. |
| `max_call_duration_ms` | Hard cap on call length | Default 1 hour (3600000) |
| `interruption_sensitivity` | 0.0–1.0; how easily caller interrupts agent | 0.9 = sensitive (good for natural dialog); lower = more deliberate |
| `normalize_for_speech` | Auto-expand numbers, abbrevs to spoken form | "$50" → "fifty dollars"; usually `true` |
| `stt_mode` | `"accurate"` vs `"fast"` | Use `accurate` for noisy / accented callers |
| `denoising_mode` | Audio cleanup | `"noise-and-background-speech-cancellation"` filters secondary voices |
| `data_storage_setting` | Retention scope | `"everything"`, `"transcripts"`, `"none"` (per Retell tier) |
| `post_call_analysis_model` | LLM for post-call extraction | `"gpt-4.1"` |
| `user_dtmf_options` | DTMF input rules | For "press 1 for X" menus |
| `responsiveness` | 0.0–1.0; lowering by 0.1 adds ~0.5s of agent wait time | Lower = more deliberate, less likely to step on the caller |
| `backchanneling` | Inserts "uh-huh", "right" while caller speaks | Configurable frequency + word list |
| `boosted_keywords` | STT bias toward specific words | Brand names, product names, uncommon vocabulary |
| `pronunciation` | Per-word pronunciation guides | For names, acronyms, brand pronunciation |
| `reminder_frequency` / `reminder_max_count` | Re-prompt timing for inactive callers | Agent reminds caller after silence |
| `voicemail_detection_timeout_ms` | Detect and handle voicemail | Set behavior on detection |
| `end_call_after_silence_ms` | Auto-terminate on silence | Bound abandoned calls |
| `begin_message_delay_ms` (a.k.a. pause-before-speaking) | Initial delay before agent's first word | 0–2s typical |
| `ambient_sound` / background sound | Plays throughout the call | Mimics call-center, office; makes call feel more human |

### `handbook_config` — Built-in Behavior Toggles

Retell ships with several built-in behaviors you can flip on/off without prompt engineering:

| Toggle | Effect when `true` |
|---|---|
| `echo_verification` | Agent reads back collected fields automatically |
| `speech_normalization` | Spoken-style number/date expansion |
| `default_personality` | Adds Retell's default warm tone |
| `scope_boundaries` | Refuses out-of-scope topics automatically |
| `natural_filler_words` | Inserts "um", "let me see", etc. for naturalness |
| `nato_phonetic_alphabet` | Uses NATO phonetic for letter readback |
| `high_empathy` | Boosts empathy phrasing across the call |
| `ai_disclosure` | Auto-discloses AI identity if asked |
| `smart_matching` | Improves edge-condition matching with built-in heuristics |

**Tip:** turn on what you want as a baseline, then override in prompts only where you need different behavior. Don't fight the handbook with prompt rules.

---

## 2. Conversation Flow Configuration

The `conversationFlow` object holds the actual graph:

```json
"conversationFlow": {
  "conversation_flow_id": "...",
  "version": 1,
  "global_prompt": "...",
  "start_node_id": "start-node-...",
  "start_speaker": "agent",
  "model_choice": { "type": "cascading", "model": "gpt-4.1" },
  "knowledge_base_ids": [],
  "tools": [ ... ],
  "nodes": [ ... ],
  "begin_tag_display_position": { "x": 113, "y": 501 },
  "notes": [ ... ]
}
```

### Key fields

| Field | Purpose |
|---|---|
| `global_prompt` | Loaded on every turn; sets identity, rules, tone, dynamic-variable context |
| `start_node_id` | Entry point for the call |
| `start_speaker` | `"agent"` (agent greets) or `"user"` (agent waits for user) |
| `model_choice` | LLM used for prompt-based edge evaluation and conversation nodes |
| `knowledge_base_ids` | Attached KBs — agent can call them via `Knowledge Base Retrieval` |
| `tools` | Custom function tools (HTTP webhooks) callable from function nodes |
| `notes` | Canvas annotations (visual editor only) |

### `model_choice`

```json
{ "type": "cascading", "model": "gpt-4.1" }
```

Retell supports cascading models — fast model for routing, stronger model for content. Override per agent if you need consistency.

---

## 3. Node Types — Full Catalog

Every node has: `id`, `type`, `name`, `display_position`, plus type-specific fields. Below is the complete set.

### 3.1 `conversation` — Standard dialog node

The workhorse. Agent speaks based on `instruction.text`, then evaluates `edges[]` after the user's next turn.

```json
{
  "type": "conversation",
  "id": "node-...",
  "name": "Greetings",
  "instruction": { "type": "prompt", "text": "say \"Hi, this is...\"" },
  "edges": [ ... ],
  "skip_response_edge": { ... },
  "always_edge": { ... },
  "interruption_sensitivity": 1,
  "start_speaker": "agent"
}
```

### 3.2 `transfer_call` — Live call transfer

Transfers to a phone number. Has a single `edge` (not `edges[]`) for the failure case:

```json
{
  "type": "transfer_call",
  "id": "node-...",
  "name": "Transfer Call",
  "instruction": { "type": "prompt", "text": "Transferring your call now." },
  "transfer_destination": {
    "type": "predefined",
    "number": "+12096086888"
  },
  "transfer_option": {
    "type": "cold_transfer",
    "show_transferee_as_caller": true,
    "enable_bridge_audio_cue": true
  },
  "edge": {
    "id": "edge-...",
    "transition_condition": { "type": "prompt", "prompt": "Transfer failed" },
    "destination_node_id": "node-fallback"
  },
  "global_node_setting": { "condition": "When user is angry or requests a human" }
}
```

| Field | Notes |
|---|---|
| `transfer_destination.type` | `"predefined"` (hard-coded number), dynamic-variable-based, or SIP URI (`sip:user@domain`) |
| `transfer_option.type` | `"cold_transfer"`, `"warm_transfer"`, or **agentic warm transfer** (transfer agent has 2-way conversation, decides bridge/cancel) |
| `show_transferee_as_caller` | Caller ID passes through to the receiving party (provider support varies) |
| `enable_bridge_audio_cue` | Plays a bridging tone during dial |
| `agent_detection_timeout_ms` | For warm transfer: how long to wait for human pickup before failure (default 30000) |
| Hold music | Custom on-hold audio while caller waits for bridge |
| `edge` | Singular — only fires on `"Transfer failed"` magic string |

**Three transfer modes in detail:**

1. **Cold Transfer** — fastest path. Agent says a closing line, then drops the call onto the destination via SIP INVITE (default) or SIP REFER. No verification the destination answered. Use for low-complexity transfers when the destination is reliable.

2. **Warm Transfer** — agent stays briefly involved. Detects whether a human picked up (vs voicemail), can play hold music, can leave a private whisper message before bridging the original caller. Default 30s timeout for human detection. Use when receiving party benefits from context.

3. **Agentic Warm Transfer** — a dedicated transfer agent (configurable, with its own version) actually has a **two-way conversation** with the destination, then decides whether to bridge the original caller or cancel. Most powerful but adds latency. Use when the destination is itself an IVR or you want the AI to negotiate before connecting.

**Always wire a `Transfer failed` edge.** Default destination should be a graceful fallback (apology + ticket creation + end), not silent dead-end.

### 3.3 `end` — Terminate the call

```json
{
  "type": "end",
  "id": "node-...",
  "name": "End Call",
  "instruction": { "type": "prompt", "text": "Politely end the call" },
  "speak_during_execution": true
}
```

Plays a closing line then hangs up. The instruction text is what the agent says before hangup.

### 3.4 `press_digit` — DTMF / IVR navigation

Used to navigate IVR menus during a call — the agent automates keypad inputs to route through phone trees on outbound calls.

```json
{
  "type": "press_digit",
  "id": "node-...",
  "name": "Press Digit",
  "instruction": { "type": "prompt", "text": "Press 1 for support, 2 for billing. Use keywords like 'Scheduling' or 'Appointments' if speech-prompted." },
  "delay_ms": 1000,
  "edges": [],
  "global_node_setting": { "condition": "When agent needs to enter DTMF tones" }
}
```

**Configuration tips (from official docs):**
- **Specify allowed keywords** the agent should listen for in the IVR prompt (e.g., "Scheduling", "Appointments") AND keywords to avoid pressing on (false positives).
- **Direct sequences** are preferred when known: `"Press 1 to reach the support department"`.
- **Behavior rules to include in the instruction:**
  - Speak department names when the IVR accepts speech recognition
  - Use the digit-press function only when IVR explicitly says "press X"
  - Call `end_call` if the IVR routes to the wrong company
  - Respond with `NO_RESPONSE_NEEDED` during hold music
- `delay_ms` waits before pressing digits — gives the IVR time to finish its prompt before the agent speaks/presses.

**Post-call analysis hooks for IVR navigation:** Retell exposes 9 dedicated extraction fields for IVR runs — `hit_ivr`, `reached_human`, `ivr_loop`, `ivr_type`, `ivr_outcome`, `ivr_steps_count`, `ivr_retries_count`, `ivr_path`, `ivr_notes`, `ivr_tree_text`. Configure these in `post_call_analysis_data` for IVR-heavy outbound flows.

**Common pitfall:** IVRs that detect human voices first will trip your agent's begin-message into the IVR — set a `pause_before_speaking` and use `interruption_sensitivity` carefully on outbound IVR-traversing flows.

### 3.5 `branch` — Logic Split (no agent turn)

Evaluates conditions and routes immediately on entry — no TTS produced, no waiting. Designed to decompose complex multi-condition logic that would otherwise stack inside a conversation node's edges.

```json
{
  "type": "branch",
  "id": "node-...",
  "name": "Logic Split",
  "edges": [
    { "id": "...", "transition_condition": { "type": "prompt", "prompt": "..." } },
    { "id": "...", "transition_condition": { "type": "equation", "equations": [...] } }
  ],
  "else_edge": {
    "id": "...",
    "transition_condition": { "type": "prompt", "prompt": "Else" }
  },
  "finetune_transition_examples": [ ... ]
}
```

**Verified rules from Retell docs:**
- Transition fires immediately when the agent enters the node (no agent turn taken).
- The `else_edge` is **mandatory** — it's the default fallback when no condition matches.
- Equation conditions evaluate first (top-to-bottom), then prompt conditions (Section 4.2).
- Available as a global node (set `global_node_setting`).
- Supports `finetune_transition_examples` for refining ambiguous prompt conditions.

**When to use vs prompt-based edges on a conversation node:**
- Use a `branch` for **deterministic** routing on dynamic-variable values — no LLM inference, no latency, no variance.
- Use prompt-based edges on a conversation node when the routing depends on **what the caller said in their last turn**.

### 3.6 `extract_dynamic_variables` — Structured extraction

Pulls typed variables out of the conversation history. Effectively a built-in lightweight tool that doesn't need a webhook. **Not a conversation node** — it doesn't speak.

```json
{
  "type": "extract_dynamic_variables",
  "id": "node-...",
  "name": "Extract Variables",
  "variables": [
    { "name": "customer_name", "type": "string", "description": "Customer's full name" },
    { "name": "appointment_date", "type": "string", "description": "Date in YYYY-MM-DD format" },
    { "name": "is_urgent", "type": "boolean", "description": "Whether this is urgent" },
    { "name": "issue_type", "type": "enum", "choices": ["billing", "tech", "general"], "description": "Caller's primary issue" },
    { "name": "ticket_count", "type": "number", "description": "Number of past tickets" }
  ],
  "edges": [ ... ],
  "else_edge": { ... }
}
```

**Verified types (from official docs):** `Text` (string), `Number`, `Enum` (with `choices: [...]`), `Boolean`. No others.

**Each variable requires:**
- A short `name` for `{{}}` reference
- A `description` — the LLM uses it to know what to extract
- A `type` (above)
- For enum: `choices: []`

**Best-practice patterns:**
- **Use after a function/MCP/code node call** to map the response payload into named variables for downstream use (e.g., extract `patient_id` from a DB lookup so the next sentence can say `"Got it, your ID is {{patient_id}}."`).
- **Use before a `branch` node** to convert free-form caller speech into structured values that equation conditions can route on.
- **Don't use it as a "validation" step** — it doesn't validate, it extracts. Pair with a branch for validation.

**Per-node LLM override:** you can pick a different model for extraction (e.g., a stronger model when accuracy matters, a faster one when it's simple).

### 3.7 `code` — Run JavaScript inline

Execute custom JS during the call **without an external server** (no webhook round-trip). Use for: date/time math, validation, format conversion, simple lookups in arrays, basic conditional computation. Anything more complex belongs in a function/MCP node.

```json
{
  "type": "code",
  "id": "node-...",
  "name": "Code",
  "code": "/* JS body */",
  "wait_for_result": true,
  "speak_during_execution": false,
  "enable_typing_sound": true,
  "edges": [],
  "else_edge": { ... }
}
```

| Field | Effect |
|---|---|
| `code` | JS source — has access to dynamic variables via `{{}}` substitution or via runtime context |
| `wait_for_result` | Block flow until code returns. Almost always `true`. |
| `speak_during_execution` | If `true`, agent speaks during execution (rarely needed for inline JS — usually fast) |
| `enable_typing_sound` | Plays a typing/keyboard sound while running — UX cue that "the system is working" |

**When to choose `code` over `function` (custom webhook):**
- Operation is purely computational (no external API needed) → `code`
- Operation needs a database, CRM, or third-party API → `function` or `mcp`
- Operation is fast (<200ms) and pure → `code` avoids network latency
- Operation has secrets/credentials that shouldn't ship to the client → `function` (server-side)

Code nodes return values that become dynamic variables for downstream nodes. Always pair with `else_edge` to handle execution failure.

### 3.8 `subagent` — Conversation + tool calling combined

A conversation node that **can also invoke tools** during the dialogue turn. This is the pattern Retell now recommends when a step needs both natural conversation **and** the ability to call MCP tools / custom functions / SMS / agent transfers.

```json
{
  "type": "subagent",
  "id": "node-...",
  "name": "Booking Assistant",
  "instruction": { "type": "prompt", "text": "Help the caller pick a slot. Use check_availability tool to look up open times." },
  "tools": [ /* attached tool IDs */ ],
  "edges": [ ... ]
}
```

**Differences from a plain `conversation` node:**
- Conversation nodes do **not** call tools.
- Subagent nodes **can** call tools mid-dialogue (LLM decides when, based on context).
- Subagent UX is "all in one node": instruction + rules + tools, instead of splitting into `conversation` → `function` → return.

**When to use subagent vs the function-node pattern:**
- Use **subagent** when the LLM needs to fluidly weave tool calls into a conversation (e.g., "let me check… ok, I see two slots…").
- Use a **separate `function` node** when the tool call is a deterministic step in a fixed flow (e.g., "create the ticket after collecting all fields"). Easier to reason about and test.

### 3.9 `sms` — Send SMS during a call

Sends an SMS without leaving the call.

```json
{
  "type": "sms",
  "id": "node-...",
  "name": "Send appointment confirmation",
  "from_number_type": "agent_number",
  "to_number": "{{customer_phone}}",
  "content": { "type": "prompt", "text": "Tell the caller their appointment is confirmed for {{appointment_date}}." },
  "edges": [ ... ]
}
```

| Aspect | Detail |
|---|---|
| Sending number | Either an SMS-approved Retell number (preset templates only) or your own A2P-approved number (custom dynamic content) |
| Recipient | Defaults to caller; can override with static number or `{{variable}}` |
| Content | If on your A2P number: write a prompt for the agent to infer SMS content, or use a static body. If on a Retell number: fixed template, no edits possible. |
| Transition | Fires within ~2 seconds whether send succeeded or failed. Always handle both cases via edges. |
| Bidirectional | Can also receive SMS during the call (text, images, audio, video) on compatible numbers |

**Common pattern:** after closing a sales call, send an SMS with the booking link or confirmation. Avoids a follow-up email.

### 3.10 `mcp` — Call an external MCP server tool

Invokes a tool hosted on a Model Context Protocol server. **Alternative to custom `function` tools** — useful when you already have your tools exposed via an MCP server (Zapier, n8n, AWS Lambda + MCP wrapper, etc.) and don't want to redefine them per agent.

```json
{
  "type": "mcp",
  "id": "node-...",
  "name": "Look up customer",
  "mcp_server_url": "https://mcp.example.com/sse",
  "headers": { "Authorization": "Bearer {{auth_token}}" },
  "query_params": { "customer_id": "{{customer_id}}" },
  "tool_name": "lookup_customer",
  "response_variables": { "customer_tier": "$.tier", "lifetime_value": "$.ltv" },
  "edges": [ ... ]
}
```

**MCP node vs custom `function` tool:**
- Custom function = HTTP webhook, defined per-agent, parameters in JSON Schema.
- MCP node = remote tool catalog, agent picks which tool to call from the server's exposed list.
- MCP is better when you have many tools across many agents (centralized) — e.g., a Zapier MCP server exposing 30 different actions.
- Custom function is better when you have one bespoke webhook per use case.

**Sub-second latency** is preserved during MCP calls per Retell's published benchmarks.

### 3.11 Function (tool-call) nodes

Function nodes call a custom tool defined in `conversationFlow.tools[]`. Configuration of the tool itself is in Section 6. Function nodes execute deterministically when the agent enters them — unlike subagent/conversation nodes where the LLM decides whether to call the tool.

### 3.12 Visual / housekeeping fields

Every node also accepts:

| Field | Purpose |
|---|---|
| `display_position` | Canvas X/Y (visual editor only — does not affect runtime) |
| `interruption_sensitivity` | Per-node override of agent-level value |
| `start_speaker` | Per-node override (rare; mostly on the start node) |
| `delay_ms` | Pause before executing node action |
| `global_node_setting` | Makes this node available as a global trigger (Section 5) |

---

## 4. Edges and Transitions

### 4.1 The four edge primitives

| Primitive | When it fires | Use for |
|---|---|---|
| `edges[]` | After the next user turn, LLM evaluates each edge's condition | Multi-turn collection, branching on caller answer |
| `always_edge` | After every agent turn at this node | Function/code nodes; one-shot transitions |
| `skip_response_edge` | When agent's response is "Skip response", fires silently | Single-line submit nodes that don't need a user turn |
| `else_edge` | When no other edge matches | Required on `branch`, `extract_dynamic_variables`, `code` nodes |

### 4.2 Transition condition types

Every edge has a `transition_condition` object with a `type`:

#### `type: "prompt"` — LLM-evaluated natural language

```json
{
  "transition_condition": {
    "type": "prompt",
    "prompt": "Caller has provided their date of birth and zip code"
  }
}
```

The LLM checks whether the prompt matches the conversation history and picks the matching edge. **Be specific** — loose prompts ("if caller wants help") match too many cases.

#### `type: "equation"` — Programmatic condition (deterministic)

```json
{
  "transition_condition": {
    "type": "equation",
    "equations": [
      { "left": "{{age}}", "operator": ">=", "right": "18" },
      { "left": "{{state}}", "operator": "==", "right": "CA" },
      { "left": "{{score}}", "operator": "<", "right": "5" }
    ],
    "operator": "&&"
  }
}
```

**Verified operator list (from official Retell docs):**

| Operator | Type | Notes |
|---|---|---|
| `==` | String comparison | Case-sensitive equality |
| `!=` | String comparison | Inverse of `==` |
| `>` / `>=` / `<` / `<=` | Numeric only | If either side isn't a number, evaluates to `false` |
| `CONTAINS` | String | Substring match. **Direction matters:** `"New York, Los Angeles" CONTAINS {{location}}` checks if `{{location}}` is in the literal. |
| `NOT CONTAINS` | String | Inverse of `CONTAINS` |
| `exists` | Variable presence | True when variable is defined and has a value |
| `does not exists` | Variable presence | True when variable is undefined or empty |

**Combiner operators:** `AND` (`&&`) requires all equations true; `OR` (`\|\|`) requires any one true. The visual editor calls these "ALL" and "ANY".

**Examples:**
- `{{user_age}} > 18`
- `{{current_time}} > 9 AND {{current_time}} < 18`
- `{{user_location}} == "New York"`
- `"New York, Los Angeles" CONTAINS {{user_location}}` *(literal contains variable value)*
- `{{name}} exists`
- `{{ticket_id}} does not exists` *(useful as anti-duplicate gate — see Section 11)*

#### Evaluation order — critical rule

**Equation conditions are always evaluated first, top to bottom. Then prompt conditions are evaluated.** The agent transitions on the **first** matching condition.

This means:
- Put your hard-deterministic checks (variable comparisons) as `equation` edges at the top.
- Use `prompt` edges only for cases that require LLM reasoning (intent detection, free-form caller statements).
- A `prompt` edge will never fire if a higher-priority `equation` edge already matched — useful for short-circuit logic.

#### When to use equation vs prompt

| Use case | Choose |
|---|---|
| Variable value comparison | `equation` — deterministic, free, instant |
| Caller intent detection | `prompt` — LLM understands paraphrasing |
| "Already submitted" gate | `equation` on `{{ticket_id}} exists` |
| "Caller agreed" routing | `prompt` ("if customer agreed") |
| Time-of-day branching | `equation` on `{{current_time}}` |
| Sentiment/tone routing | `prompt` ("if caller sounds frustrated") |

Mix both freely — equations short-circuit the cheap, deterministic cases and prompts handle the rest.

### 4.3 Edge UI metadata

```json
{
  "id": "edge-...",
  "condition": "If customer agreed",          // friendly label for canvas UI
  "transition_condition": { "type": "prompt", "prompt": "If customer agreed" },
  "destination_node_id": "node-...",
  "finetune_transition_examples": [ ... ]
}
```

The `condition` field is a UI label — the actual matching is `transition_condition.prompt`. Keep them aligned to avoid confusion.

### 4.4 `finetune_transition_examples` — Few-shot edge teaching

You can attach example transcripts to an edge to teach the LLM exactly when to fire it. This dramatically improves edge accuracy on ambiguous conditions.

```json
"finetune_transition_examples": [
  {
    "destination_node_id": "node-yes-path",
    "transcript": [
      { "role": "user", "content": "Yes, please proceed." },
      { "role": "agent", "content": "" }
    ],
    "id": "fe-..."
  },
  {
    "destination_node_id": "node-no-path",
    "transcript": [
      { "role": "user", "content": "No, I don't want to." },
      { "role": "agent", "content": "" }
    ],
    "id": "fe-..."
  }
]
```

Use these on edges that misfire in testing. Three or four examples per edge typically resolves most ambiguity.

---

## 5. Global Nodes

A global node is any node with `global_node_setting`. It can be triggered from **any** node in the flow when its condition matches the conversation context.

```json
{
  "type": "transfer_call",
  "name": "Human Agent Transfer",
  "global_node_setting": {
    "condition": "When user is angry or requests a human agent"
  },
  "transfer_destination": { ... },
  ...
}
```

### Common global nodes

| Trigger | Node type | Purpose |
|---|---|---|
| Distress / acute emotion | `transfer_call` or `conversation` | Empathy + escalate |
| Death / fatality reported | `conversation` then `end` | Condolence, no ticket, clean exit |
| "Speak to a human" | `transfer_call` | Direct transfer |
| FAQ / general question | `conversation` (with KB) | Answer + return to caller |
| Topic change | `branch` or `conversation` | Route to relevant flow |

### Rules

1. **Conditions must be specific.** "When user is upset" is too loose — it'll fire mid-collection on minor frustration. Use "When user expresses acute emotional distress, mentions self-harm, or says they cannot continue" instead.
2. **Pair with a return path** when the side-trip is informational. FAQ globals should `return_to_caller`. Transfer / fatality globals should `end`.
3. **Test interaction with mid-collection state** — globals can yank the caller out of intake mid-flow. Decide whether the side-trip should preserve or reset collected fields.
4. **Order matters at runtime** — Retell evaluates global conditions per turn. If two globals could match, refine the prompts.

---

## 6. Tools / Function Nodes

Tools are HTTP webhooks declared at `conversationFlow.tools[]` and invoked by function nodes or attached to subagent nodes.

**Three ways to call external systems from a flow:**
| Mechanism | When to use |
|---|---|
| `function` node + custom tool | Bespoke webhook per use case; you own the endpoint |
| `mcp` node | You have many tools exposed via an MCP server (Zapier, n8n MCP, AWS Lambda MCP wrapper) — agent picks which to call |
| `subagent` node + attached tools | The LLM should fluidly weave tool calls into a multi-turn conversation |

**Tool definition (custom function example):**

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

| Field | Why it matters |
|---|---|
| `speak_during_execution: true` | Without it, agent goes silent during slow webhooks (5–15s) — caller thinks call dropped |
| `execution_message_description` | Pins the exact filler line; without it, the LLM improvises a different line every call |
| `timeout_ms: 120000` | Cold-start webhooks often exceed default; bump to 2 min for n8n / serverless |
| `response_variables` | JSONPath → variable name; exposes return values to subsequent nodes |
| `args_at_root: true` | Sends parameters at top level (not wrapped in `args:{}`) — match your webhook's expectation |

### Tool URL hygiene

- Placeholder URLs (`TODO.example.com`) silently fail at runtime — call breaks, no clear error.
- Always ship with a real URL or remove the tool reference.
- Set realistic timeouts; 5s is too short for any real webhook.

---

## 7. Dynamic Variables

### 7.1 Sources of variables

| Source | When set | Example |
|---|---|---|
| Pre-call injection | Before call connects (via `retell_llm_dynamic_variables` on Create Phone Call API) | `{{customer_name}}`, `{{customer_id}}` |
| `extract_dynamic_variables` node | Mid-call extraction | `{{appointment_date}}` |
| `code` node return values | Mid-call computation | `{{is_eligible}}` |
| Tool / function / MCP `response_variables` | After tool call | `{{ticket_id}}` |
| Built-in | Always | `{{current_time}}`, `{{call_id}}` |

**Critical constraint on pre-call injection:** all values in `retell_llm_dynamic_variables` **must be strings**. Numbers, booleans, arrays, and objects are not supported — convert to strings before passing in (e.g., `"true"` not `true`, `"42"` not `42`). Inside the agent, the LLM treats them naturally as their semantic type.

### 7.2 Fact-style vs inline-conditional usage

**Inline conditional (BAD — empty values leak):**
```
say "Just to confirm — that's {{customer_name}}, right?"
```
When `customer_name` is empty, the LLM substitutes literally — caller hears "that's bracket-name-bracket, right?" or random STT garbage.

**Fact-style global context (GOOD):**
```
CALLER CONTEXT (verify, don't re-collect):
Name: {{customer_name}}
DOB: {{dob}}
Zip: {{customer_zip}}

Rule: if a value is empty, ask fresh. If present, confirm: "I have your name as [value], is that right?"
```

Pushes the conditional logic into the LLM's natural reasoning instead of template substitution.

### 7.3 Naming conventions

- `customer_*` / `caller_*` for caller-side fields
- `client_*` / `patient_*` for the third party they reference
- Tool returns: short, lowercase, snake_case (`ticket_id`, `eligible`, `next_appointment`)
- Avoid spaces in names (`{{customer zip}}` won't parse cleanly — use `{{customer_zip}}`)

---

## 8. Post-Call Analysis

Retell can run an LLM after the call to extract structured data. Configured at agent level:

```json
"post_call_analysis_model": "gpt-4.1",
"post_call_analysis_data": [
  {
    "name": "Do you currently have a steady place to live?",
    "type": "enum",
    "choices": ["Yes.", "Yes, but I'm worried about losing it.", "No."]
  },
  {
    "name": "Number of concerned answers",
    "type": "number"
  },
  {
    "name": "Caller intent",
    "type": "string",
    "description": "Free-form classification of the caller's primary intent"
  }
]
```

### Field types (verified from official docs)

| Type | Purpose | Example |
|---|---|---|
| `enum` (with `choices: []`) | Constrained selection from fixed list | Issue type, resolution status, sentiment bucket |
| `number` | Quantitative measurements | Transaction amount, satisfaction score, tickets opened |
| `string` | Free-form textual extraction | Call summary, action items, caller intent description |
| `boolean` | Yes/no determinations | First-time caller, escalation needed, deal closed |

### Important constraint

> "We will not populate custom post-call analysis fields for calls that were not connected or where no conversation took place." — Retell docs

Always check field existence before reading. Filter out unconnected calls in your downstream pipeline.

**Use cases:**
- Quality scoring / call grading
- Downstream automation triggers (CRM updates based on extracted fields)
- Analytics dashboards (volume by intent, conversion by demographic)
- Call/chat history filtering by custom fields (Retell dashboard supports filtering on enum, boolean, number types)

These fields appear in the call's post-call payload and can be webhooked to your backend.

### Filtering and dashboards

Retell's dashboard supports filtering call/chat history by custom post-call analysis fields (enum, boolean, number types). Configure thoughtfully — well-named enum fields become powerful slicers for analytics.

---

## 9. Magic Strings

Retell recognizes specific literal strings in transition prompts and agent outputs. Memorize these:

| String | Where | Effect |
|---|---|---|
| `"Skip response"` | `skip_response_edge.transition_condition.prompt` | Triggers silent transition after a single-line node |
| `"Always"` | `always_edge.transition_condition.prompt` | Fires after every agent turn |
| `"Else"` | `else_edge.transition_condition.prompt` | Fires when no other edge matches (mandatory on `branch`, `extract_dynamic_variables`, `code`) |
| `"Transfer failed"` | `transfer_call` node's `edge.transition_condition.prompt` | Routes to fallback when transfer dial fails |
| `end_call` | Function callable from agent | Terminates the call from inside a node (e.g., when an IVR routes wrong) |
| `NO_RESPONSE_NEEDED` | LLM output (in agent text) | Suppresses TTS for that turn — agent stays silent |

**Variable-existence syntax** (in equation conditions only):
- `{{var}} exists` / `{{var}} does not exists` — note the unusual `does not exists` (with trailing `s` per docs)

These are not consistently documented in any one place — learn them from sample flows and the editor UI.

---

## 10. The Standard Collection Pattern

The proven shape for any flow that collects fields, calls a tool (e.g., create ticket), and confirms back. Use this as a template — every node has a single responsibility and transitions are deterministic.

```
[COLLECTION NODE]            (conversation, multi-turn, conditional edges)
   "Collect N fields one per turn..."
   edges[] → matches "all fields collected"
        ↓
[SUBMIT NODE]                (conversation, single-line, skip_response_edge)
   "I'm submitting your request now."
   skip_response_edge → "Skip response"
        ↓
[TOOL NODE]                  (function or conversation with tool binding)
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

- The LLM forgets it already spoke a closing and re-delivers it
- The conditional edge can fire before the closing
- The tool call has no clean "wait" surface
- Repetition rules degrade because the LLM blends multiple stages

---

## 11. Anti-Patterns and Failure Modes

### 11.1 The "Instructing Silence" Anti-Pattern

**Don't write:**
```
AFTER LAST FIELD — DO NOTHING:
Once the caller has answered question N, STOP IMMEDIATELY.
Do NOT generate ANY further text.
The system transitions automatically.
```

**Why it fails:** when a conditional edge requires the next user turn to evaluate, the agent is forced to produce a turn first. Told to "do nothing", the LLM:
1. Reads the stage direction aloud verbatim
2. Hallucinates that something has been completed and improvises a closing
3. Reaches for the most recent disclosure and recites it

**Correct pattern:** give the LLM a concrete safe line to produce, then let the conditional edge fire on the next turn:
```
AFTER LAST FIELD:
Say EXACTLY: "Got it — one moment."
Then STOP.
DO NOT use brackets [ ] in your response — never.
DO NOT deliver any closing or stage directions.
```

The throwaway acknowledgment line gives the LLM a deterministic action and triggers the next edge.

**Generalized rule:** never instruct the LLM to be silent. Either give it a specific line to say, or use `always_edge` / `skip_response_edge` / `branch` to transition without a turn.

### 11.2 The "Anti-Duplicate Guard" Trap

**Don't write:**
```
If a ticket has already been created in this call, do not collect again.
Say "Your ticket has already been submitted."
```

**Why it fails:** the guard depends on the LLM correctly reading history. The LLM is unreliable at this — it will fire the guard prematurely after any prior agent turn it can't fully parse.

**Correct pattern:** prevent re-entry at the **edge level**, not via prose:
- Tighten Confirmation node's edges so they don't loop back to collection
- Add an `equation` edge at the top of every collection node: `{{ticket_id}} exists` → route to a "ticket already submitted" node. Equations evaluate before prompts, so this short-circuits any prose-based collection logic.
- Or use a `branch` node before the collection node to deterministically route based on `{{ticket_id}} exists` / `does not exists`.

This is the single biggest win from understanding equation-based transitions — what used to require fragile prose guardrails is now one deterministic edge.

### 11.3 Common failure modes — quick reference

| Symptom | Root cause | Fix |
|---|---|---|
| Agent reads "[stage direction]" aloud | Instruction told it to be silent | Give a concrete line; use `always_edge` for silent transitions |
| Two tickets created | Collection node re-entered post-confirmation | Tighten confirmation edges; use equation gate on `{{ticket_id}}` |
| Disclosure repeated 3× | No-repetition rule missing | Add explicit "deliver exactly once" rule in global prompt |
| Closing inside collection | Collection had closing prose | Move closing to dedicated submit/end node |
| Stuck after tool call | `always_edge` missing on function node | Add `always_edge` with destination |
| Variables show as `[Name]` literally | Inline conditional in instruction | Switch to fact-style global Caller Context |
| Agent talks over caller | `interruption_sensitivity` too low | Raise to 0.9–1.0 |
| Agent rambles during tool wait | `execution_message_description` empty | Pin the exact filler line |
| Wrong edge fires | Edge condition too loose | Make conditions specific; add `finetune_transition_examples` |
| `skip_response_edge` doesn't fire | Node has too many turns | Single-purpose nodes only |
| Duplicate edge ID import error | Copy-pasted node | Run uniqueness check (Section 14) |
| Global node hijacks intake | Global condition too loose | Refine condition; test mid-flow trigger scenarios |
| Equation edge always misses | Type mismatch (string vs number) | Cast values; check operator semantics |

---

## 12. Prompt Hygiene Rules

### 12.1 The "No Repetition" Rule

Once any of the following has been spoken, it must not be spoken again in the same call:
- Reference / ticket / confirmation numbers
- Mandatory disclosures
- Closing line
- Empathy openers ("I'm so sorry you're going through this")

Add to the **global prompt**:
```
- Never repeat a disclosure, reminder, scripted message, reference-number 
  readback, or full closing line you have already delivered in this call. 
  If a topic comes up again, refer back briefly ("As I mentioned earlier, 
  your reference [number] has already been submitted") without re-delivering 
  the full text.
```

### 12.2 The "No Fabrication" Rule

For dangerous-to-invent domains (charges, deductions, policy timelines, medical specifics, legal terms):
```
- Never fabricate specific information you weren't told. For unknown 
  specifics, say: "I can connect you with our team for that specific 
  question — would you like me to?"
```

Pair with concrete transfer paths so the LLM has a safe escape hatch.

### 12.3 Turn-Taking and Caller Pause

```
TURN-TAKING:
If the caller says any of: "hold on", "give me a moment", "wait a second", 
"let me check", "one moment", "let me grab" — respond NO_RESPONSE_NEEDED. 
Do not say "okay" or "take your time" — stay silent until the caller 
speaks again.
```

Without this, the agent fills every silence with chatter.

### 12.4 Email and Number Verification

**Emails:**
- Common domains (`gmail.com`, `yahoo.com`, `outlook.com`, `hotmail.com`, `icloud.com`, `aol.com`): spell only the local part, speak the domain naturally as "at gmail dot com"
- Uncommon domains: spell the full address including domain
- Confirm with phonetic alphabet on ambiguous letters: "M as in Mike"

**Phone numbers:**
- Read back grouped 3-3-4: "Five five five — one two three — four five six seven"
- Always confirm before submitting

### 12.5 Global Prompt Structure

Effective layout — keep each section short; the global prompt loads on every turn:

```
1. IDENTITY
   "You are [Name], an inbound voice agent for [Company]..."

2. CALLER CONTEXT (fact-style)
   Name: {{customer_name}}
   Phone: {{customer_phone}}
   ...

3. CORE RULES
   - One question per turn
   - Confirm collected data before submitting
   - Never repeat disclosures
   - Never fabricate
   - Geographic / sanity validation

4. TURN-TAKING
   NO_RESPONSE_NEEDED rules

5. VERIFICATION
   Email/phone readback patterns
   Phonetic alphabet for ambiguous letters

6. TONE
   Warm, confident, efficient. Empathy before action.

7. ESCALATION TRIGGERS
   Distress → GLOBAL DISTRESS
   Fatality → GLOBAL FATALITY
   Human request → GLOBAL HUMAN
```

Bloat costs latency and dilutes the rules the LLM actually follows.

---

## 13. Testing Methodology

### 13.1 JSON edit cycle

Edit conversation flow JSON via scripts, not by hand — manual edits drop edges and break references. Standard verification after every change:

```python
import json
from collections import Counter

with open(path) as f:
    data = json.load(f)

# 1. JSON parses
nodes = data['conversationFlow']['nodes']
nodes_by_id = {n['id']: n for n in nodes}

# 2. Edge IDs unique
ids = []
for n in nodes:
    for e in n.get('edges', []):
        if e.get('id'): ids.append(e['id'])
    for k in ('always_edge', 'skip_response_edge', 'edge', 'else_edge', 'success_edge', 'failed_edge'):
        v = n.get(k)
        if isinstance(v, dict) and v.get('id'): ids.append(v['id'])
dupes = [i for i, c in Counter(ids).items() if c > 1]
assert not dupes, f"Duplicate edge IDs: {dupes}"

# 3. All destination_node_id values resolve
for n in nodes:
    for e in n.get('edges', []):
        d = e.get('destination_node_id')
        if d: assert d in nodes_by_id, f"Broken: {n['id']} → {d}"

# 4. Targeted prose checks: did the new text actually land?
# 5. Targeted regression checks: did anything I didn't mean to change move?
```

### 13.2 Live-test scenarios per flow

For every flow, test at minimum:

1. **Golden path** — every field provided correctly on first ask
2. **Confirmation rejection** — caller says "no, that's wrong" to a confirmation
3. **Mid-flow distress** — does GLOBAL DISTRESS fire?
4. **Mid-flow topic change** — does global topic-change fire correctly?
5. **Pause / hold-on** — does `NO_RESPONSE_NEEDED` fire?
6. **Tool failure** — webhook returns error or times out — does the failure path work?
7. **Caller insists** — push-back after agent offers to handle — does it transfer cleanly?
8. **Variable extraction failure** — `extract_dynamic_variables` else-edge — what happens when extraction fails?

### 13.3 Test case file format

For Retell's AI simulator, use plain numbered cases (no Pass/Fail markers — those break import):

```markdown
## TC-01: Standard happy path
Caller: I'd like to schedule an appointment.
Caller: My name is Sarah Johnson.
Caller: Tomorrow at 2pm works.
...
Expected: Appointment booked, confirmation read back, call closes warmly.

## TC-02: Mid-flow request for human
Caller: Wait, I just want to talk to a person.
Expected: GLOBAL HUMAN fires; agent transfers without finishing intake.
```

---

## 14. Edge ID Uniqueness and Schema Validation

**Every edge ID across the entire flow must be unique** — including IDs inside `always_edge`, `skip_response_edge`, `else_edge`, `edge`, `success_edge`, `failed_edge`. Duplicates cause opaque import errors.

A common cause: copy-pasting a node and forgetting to rename its edges. Run the uniqueness + reference check from Section 13 before every commit.

Other schema gotchas:
- `destination_node_id` referencing a deleted node → silent dead end
- `transition_condition.type: "equation"` with mismatched variable types → never matches
- Tool `parameters.required` listing a field not in `properties` → tool call fails
- `response_variables` JSONPath that doesn't resolve → variable is empty downstream

---

## 15. Final Heuristics

1. **Single responsibility per node.** If a node both collects and closes, split it.
2. **Never instruct silence.** Give the LLM a concrete line, or use a silent edge primitive (`always_edge`, `skip_response_edge`, `branch`).
3. **Specific edge conditions.** "All five fields collected and caller has confirmed" beats "ready to submit". Add `finetune_transition_examples` for ambiguous cases.
4. **Equations before prompts** — equation conditions evaluate first (top-to-bottom). Put deterministic gates as equations at the top of every node's edge list; let prompt edges handle nuance.
5. **Use equation edges for variable comparisons.** `==`, `!=`, `>`, `<`, `>=`, `<=`, `CONTAINS`, `NOT CONTAINS`, `exists`, `does not exists`, combined with `AND`/`OR`. Cheaper, deterministic, and more predictable than prompt edges.
6. **Fact-style variables.** No inline conditionals. Empty values must produce empty facts. Pre-call values must be **strings**.
7. **Pin tool wait phrases.** Set `execution_message_description` on every function node.
8. **Repetition rule lives globally.** Per-node guards leak.
9. **Test with the LLM in a confused state.** Run scenarios with mid-flow topic changes, pauses, and contradictions — that's where flows break.
10. **Verify edge ID uniqueness before importing.** Always.
11. **Lean on `handbook_config` first, prompt rules second.** Don't fight the platform.
12. **Use `code` nodes** instead of webhooks when the work is pure computation (date math, validation) — avoids network latency.
13. **Use `extract_dynamic_variables` after function/MCP calls** to map response data into named variables for downstream use.
14. **Use `branch` nodes for variable-driven routing** — they don't cost an agent turn, produce zero TTS, and run instantly on entry.
15. **Use `subagent` nodes** when a step needs both conversation **and** tool calls fluidly woven together. Use `function`/`mcp` standalone when the tool call is a deterministic single step.
16. **Use `mcp` nodes** when you have a centralized tool catalog (Zapier MCP, n8n MCP) — single connection, many tools.
17. **Use `sms` nodes** to send confirmations/links during the call — better UX than asking caller to wait for an email.
18. **Set `else_edge` on every node that requires one** — `branch`, `extract_dynamic_variables`, `code` all need fallback paths.
19. **Configure `post_call_analysis_data` early** — easier to add fields incrementally than to add extraction at the end. Remember: fields are **not populated** for unconnected calls.
20. **For warm transfers, always handle `Transfer failed`** — wire the `edge` to a graceful fallback (apology + ticket) instead of silent failure.
21. **For IVR navigation (outbound), include the 9 IVR post-call fields** — `hit_ivr`, `reached_human`, `ivr_outcome`, etc. Critical for debugging.

---

*This is a generic build reference compiled from production builds + verified against official Retell documentation. Adapt patterns to your domain — names, fields, transfer destinations, and disclosures change per use case, but the structural rules (edge primitives, node types, evaluation order, anti-patterns) hold across any Retell agent.*

*Source documentation: [docs.retellai.com](https://docs.retellai.com) — particularly the [Conversation Flow Overview](https://docs.retellai.com/build/conversation-flow/overview), [Node Overview](https://docs.retellai.com/build/conversation-flow/node), and [Transition Condition](https://docs.retellai.com/build/conversation-flow/transition-condition) pages.*
