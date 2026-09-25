---
name: retell-conversation-flow
description: >
  Build production-grade Retell AI conversation-flow voice agents — the multi-node, branching kind
  with tools, transfers, IVR navigation, KB, and post-call analysis. Use this skill whenever the user
  wants to build, design, refactor, or debug a Retell conversation-flow agent (NOT a single-prompt
  agent — for that, use retell-agent-prompt instead). Trigger on phrases like "Retell conversation
  flow", "voice agent with multiple nodes", "build a phone agent that does X then Y then Z",
  "agent that books appointments and transfers when stuck", "multi-step inbound agent",
  "convert this call script into a Retell flow", "Retell flow JSON", "design the nodes for…",
  "fix this Retell flow", "my Retell agent is looping/stuck/repeating". Also trigger when the user
  shows you an exported conversation-flow JSON, or talks about nodes, edges, transitions,
  global nodes, branch nodes, code nodes, MCP nodes, extract dynamic variables, ticket creation flows,
  warm-vs-cold transfer logic, agent versions and publishing, or tuning call behaviour (interruption
  sensitivity, silence timeout, voicemail, backchannel). Even partial mentions ("help me with my
  Retell flow") should trigger.
---

# Retell Conversation Flow — Production Agent Builder

Build robust, human-sounding Retell **conversation-flow** voice agents. Output is a complete, importable conversation-flow JSON plus a global prompt — the user pastes the result into the Retell dashboard or imports the JSON file directly.

## When to use this vs `retell-agent-prompt`

| Need | Use |
|---|---|
| Single big prompt that governs the whole call (one LLM context, no graph) | `retell-agent-prompt` |
| Multi-node graph: collect data, branch, call tools, transfer, return — with deterministic transitions | **this skill** |
| Anything involving multiple distinct flows (booking + status check + cancellation) on one agent | **this skill** |
| Outbound IVR navigation (press digit, navigate phone trees) | **this skill** |
| Anything needing structured per-flow tickets, MCP tools, SMS during call, or warm transfers | **this skill** |

If you're not sure, ask the user: "Is this one continuous conversation, or does it have multiple branches with different tool calls per branch?" Multiple branches → conversation flow.

## Why conversation flow over single-prompt

A single prompt struggles when you need: deterministic routing on a variable, mid-flow tool calls without LLM-decided invocation, bulletproof guardrails between flows, post-call extraction, or any IVR/transfer logic. Conversation flows give you a graph with explicit edges, equation-evaluated transitions, function/code/branch/extract nodes that don't need an agent turn, and per-node LLM overrides. The cost is more upfront design — this skill is the design harness.

---

## Core Principles

1. **Single responsibility per node.** A node either collects, decides, calls a tool, transfers, or speaks one line — never a mix. When in doubt, split.

2. **Equations before prompts.** Equation conditions evaluate first (top to bottom), then prompt conditions. Put deterministic checks first; let LLM-evaluated prompts handle nuance.

3. **Never instruct silence.** "Do nothing" / "stay silent" / "system transitions automatically" makes the LLM read the stage direction aloud. Either give it a concrete short line, or use a silent edge primitive (`always_edge`, `skip_response_edge`, `branch`).

4. **Brevity on voice.** Default to 1–2 sentence agent turns. Phone attention drops sharply after 8–10 seconds of uninterrupted AI speech.

5. **Sound human.** Contractions, filler words ("so," "got it," "okay"), one question per turn. The TTS engine reads what the LLM writes — pronunciation rules in the global prompt are not optional.

6. **Structure beats prose.** A rule the model has ignored twice is a graph problem, not a wording problem. Move the capability, don't sharpen the sentence: a step that must not look things up gets its own node carrying only the tool it may use. Node shape and `tool_ids` are enforcement; instruction text is a hint.

7. **Every turn ends with a question.** Prompt transitions are judged on the caller's *next* turn, so a turn ending in a statement gives the caller nothing to answer and the call stalls until the reminder fires. Acknowledgements belong at the top of the next node's instruction, where a question follows them.

8. **The flow is half the agent.** Silence timeout, interruption sensitivity, voicemail behaviour, STT mode and publishing decide as much of the call as the graph does — see `references/agent-settings.md`. And a fix only reaches callers once the agent is **published**.

---

## The Workflow

Follow this sequence. Don't skip steps — each one prevents a class of bug observed in production.

### Step 1 — Interview the user

Gather requirements before writing any JSON. Required questions:

- **Use case:** inbound or outbound? What does the agent do? (intake, booking, IVR navigation, qualification, support…)
- **Flows:** how many distinct flows does the agent handle? List them. Each flow becomes a sub-graph.
- **Identity:** agent name, company, brand voice (warm/professional/casual).
- **Tools / integrations:** what does the agent need to call? (CRM, booking, ticket creation, SMS, MCP server). For each: endpoint, method, params, expected response shape.
- **Transfers:** which departments/numbers? Cold, warm, or agentic warm? Fallback if transfer fails?
- **Knowledge base:** any KB attached? What domains?
- **Pre-call data:** what dynamic variables are injected per call? (caller name, account ID, etc.) — remember they must all be **strings**.
- **Post-call analysis:** what fields should be extracted after the call? (intent, outcome, satisfaction, structured data)
- **Timezone:** for `{{current_time_<IANA>}}` and `{{current_calendar_<IANA>}}`.
- **Compliance / disclosures:** any mandatory verbatim language? (HIPAA, mini-Miranda, recording disclosure)
- **Edge cases & escalation:** distress, fatality (healthcare), abuse, off-topic, hold/silence.

If the user comes in with an existing flow that's broken, skip to **Debug an existing flow** at the bottom.

### Step 2 — Design the node graph on paper first

Sketch the graph before writing JSON. For each flow, apply the **Standard Collection Pattern** (see `references/standard-patterns.md`):

```
[COLLECTION]  →  [SUBMIT]  →  [TOOL]  →  [CONFIRMATION]  →  [CLOSE | NEXT TOPIC | TRANSFER]
   conv          conv         function     conv               (edges)
   multi-turn    skip_resp    always_edge  edges[]
```

Plus global nodes for cross-cutting interrupts: distress, fatality, human-request, FAQ, topic-change.

Decide which node types to use for each step. Default mapping:
- **Greeting / opening** → `conversation` with `start_speaker: "agent"`
- **Field collection (multi-turn)** → `conversation`, conditional `edges[]`
- **Single-line "I'm submitting now"** → `conversation` with `skip_response_edge`
- **Tool call (deterministic)** → function node, `always_edge` to next
- **Tool call woven into dialog** → `subagent` node
- **External MCP call** → `mcp` node
- **Send SMS during call** → `sms` node
- **Inline JS (date math, validation)** → `code` node, `wait_for_result: true`, paired with `else_edge`
- **Pull structured fields from caller speech** → `extract_dynamic_variables` node
- **Variable-driven routing (no agent turn)** → `branch` node with mandatory `else_edge`
- **IVR navigation** → `press_digit` node
- **Transfer to human/dept** → `transfer_call`, mode = cold/warm/agentic_warm
- **Close call** → `end` node

For deeper explanation of any node type, read [`references/node-types.md`](references/node-types.md).

### Step 3 — Write the global prompt

Use [`references/global-prompt-template.md`](references/global-prompt-template.md) as the template. The global prompt loads on every turn — keep each section short. Required sections in this order:

1. **Identity** — who the agent is, who it works for, that this is a live phone call.
2. **Caller Context (fact-style)** — `Name: {{caller_name}}\nPhone: {{caller_phone}}\n…`. Never inline conditional substitution.
3. **Core Rules** — one question per turn, confirm data before submitting, no repetition, no fabrication.
4. **Personality & Style** — contractions, filler words, mirror caller energy, no formatted lists in speech.
5. **Pronunciation Rules** — phone digits, emails, URLs, times/dates, currency. Verbatim from `global-prompt-template.md`.
6. **Turn-Taking** — `NO_RESPONSE_NEEDED` for "hold on", "give me a moment".
7. **Verification** — readback patterns for emails/phones, phonetic alphabet for ambiguous letters.
8. **Tone & Empathy Triggers** — empathy before action.
9. **Escalation triggers** — pointers to global nodes (DISTRESS, FATALITY, HUMAN, etc).
10. **System variables** — `{{current_time_<TIMEZONE>}}` (formatted string), `{{current_hour_<TIMEZONE>}}` (numeric 24h fraction — use this, not `current_time`, for business-hours equation edges), `{{current_calendar_<TIMEZONE>}}`, `{{user_number}}` (caller's number on inbound), `{{direction}}`, `{{call_type}}`.

Always include the **defensive prompting rule for missing variables** — see `global-prompt-template.md`.

### Step 4 — Write the JSON

Build the conversation flow JSON. Start from a template in `assets/`:
- `assets/starter-flow.json` — minimal valid flow (greeting → end)
- `assets/collection-flow-template.json` — the 4-node Standard Collection Pattern
- `assets/transfer-with-fallback.json` — transfer node + Transfer-failed fallback
- `assets/code-and-branch-pattern.json` — code → extract_dynamic_variables → branch (deterministic mid-call computation + routing)

Edit JSON via Python scripts, not by hand. Manual edits drop edges and break references. Sample editor pattern:

```python
import json
path = "agent.json"
with open(path) as f: data = json.load(f)
# … modify data['conversationFlow']['nodes'] etc …
with open(path, 'w') as f: json.dump(data, f, indent=2, ensure_ascii=False)
```

For node-type details, edge schemas, transition condition schemas, and tool definitions, read [`references/node-types.md`](references/node-types.md) and [`references/edges-and-transitions.md`](references/edges-and-transitions.md).

### Step 5 — Wire tools

Tools live at `conversationFlow.tools[]` and are referenced by function/subagent nodes. For every tool:
- Set `speak_during_execution: true` for any tool with >2s latency, with a pinned `execution_message_description: "Just a moment please, this will only take a second."` Without the pinned phrase, the LLM improvises a different filler line on every call.
- Set `timeout_ms: 120000` for n8n / serverless cold-start endpoints. Default is too short.
- Define `response_variables` with JSONPath: `{"ticket_id": "$.ticket_id"}`. These become `{{ticket_id}}` downstream.
- Real URL only — `TODO.example.com` placeholders silently fail at runtime.

For three ways to call external systems and which to choose, see [`references/node-types.md`](references/node-types.md) §Tools.

### Step 5b — Agree the backend contract

The flow's tools are only as good as what answers them. Before wiring, settle these with whoever owns the endpoint — each one has broken a live call:

- **Response size** — Retell silently drops oversized tool results (budget ~10 KB). Give lookups a catalog shape and a detail shape rather than one fat payload.
- **No UUIDs in the model's hands** — tool parameters take what a person said (name, duration, the time they agreed to); the backend resolves IDs. See `references/backend-contract.md`.
- **Retries** — 3 attempts ~1 s apart on every outbound HTTP call, so one transient network blip doesn't become "I can't pull that up" on a healthy call.
- **Honest failure envelope** — a failed tool returns something the flow can route on, and the failure node offers a callback instead of inventing a value.
- **Post-call webhook** — subscribe to `call_analyzed` and derive outcomes from tool results, not from the model's own label.

### Step 6 — Configure post-call analysis

In `post_call_analysis_data` at agent level, declare structured fields the post-call LLM should extract. Types: `enum` (with `choices`), `number`, `string`, `boolean`. Naming these well makes them powerful filters in Retell's call history dashboard. Read [`references/post-call-analysis.md`](references/post-call-analysis.md) for use cases.

For IVR-traversing outbound flows, include the 9 IVR fields: `hit_ivr`, `reached_human`, `ivr_loop`, `ivr_type`, `ivr_outcome`, `ivr_steps_count`, `ivr_retries_count`, `ivr_path`, `ivr_notes`, `ivr_tree_text`.

### Step 7 — Validate the JSON before delivering

Run [`scripts/validate_flow.py`](scripts/validate_flow.py) against the output. It checks:
- JSON parses
- Edge IDs unique across the entire flow (including IDs nested inside `always_edge`, `skip_response_edge`, `else_edge`, `edge`, `success_edge`, `failed_edge`)
- All `destination_node_id` values resolve to a real node
- `branch`, `extract_dynamic_variables`, `code` nodes have an `else_edge`
- Every function node with `speak_during_execution: true` has an `execution_message_description`
- No placeholder URLs in tools

If validation fails, fix and re-run. Don't deliver an unvalidated flow.

```bash
python d:/retell-voice-agents/.claude/skills/retell-conversation-flow/scripts/validate_flow.py path/to/agent.json
```

### Step 7b — Set the agent-level settings, then publish

The flow JSON carries none of this, and it decides how the call feels. Full table in [`references/agent-settings.md`](references/agent-settings.md); the ones that are never negotiable:

- `enable_backchannel: false` — **always**. Deprecated in practice; injected "mm-hm" lands on the wrong beat and feeds the agent's own audio back into the STT. Drop `backchannel_frequency` / `backchannel_words` with it.
- `interruption_sensitivity: 0` **on the opening node** (line echo cuts off greetings; nobody real does).
- `end_call_after_silence_ms` 30–50 s — reminders and the timeout stack, so a 90 s default means ~2 minutes of dead air.
- Outbound: `start_speaker: "user"` + `begin_after_user_silence_ms`, plus `voicemail_option` static text.
- `webhook_url` + `webhook_events: ["call_analyzed"]` if anything downstream needs the call.

Then **publish**, and read the published version back: a draft edit changes nothing for real callers, and `publish-agent` opens a fresh draft N+1 (so the newest version legitimately reads `is_published: false`). Assert on the published copy that your change is present **and** that the tool URLs are the production ones.

### Step 8 — Deliver

Output to the user:
1. The full JSON file (or path to it).
2. The global prompt (paste-ready into the Retell dashboard or already inside the JSON's `conversationFlow.global_prompt`).
3. A **flow map** — text diagram of the node graph: which nodes exist, what they do, how they connect. Helps the user reason about the flow visually before importing.
4. **Validation summary** — confirm all checks passed.
5. **What to test first** (see Step 9).

### Step 9 — Recommend test scenarios

For every flow in the agent, recommend the user test these seven scenarios in the Retell simulator or live:

1. **Golden path** — every field provided correctly on first ask.
2. **Confirmation rejection** — caller says "no, that's wrong" to a confirmation.
3. **Mid-flow distress** — caller suddenly distressed (does GLOBAL DISTRESS fire?).
4. **Mid-flow topic change** — caller switches topic (correct routing?).
5. **Pause / hold-on** — caller asks for a moment (does `NO_RESPONSE_NEEDED` fire?).
6. **Tool failure** — webhook returns error or times out (failure path works?).
7. **Caller insists / push-back** — push-back after offer to handle (clean transfer?).

8. **Partial answer** — caller answers a different attribute than the one asked ("ninety minutes" to "which service?"). Does the node keep it and read the options back, or loop the same question?
9. **Silence after pickup** — say nothing at all. Does the reminder fire once, then the call close within the budget you set?
10. **Machine answers** (outbound) — does the agent stay quiet through the recorded greeting and leave exactly one message?

Plus per-flow specifics: variable extraction failure (else-edge), Transfer failed, IVR wrong-routing.

Retell's **test-case definitions** turn these into repeatable simulations: each definition carries a `response_engine` (pin it to the **published** flow version), a `user_prompt` persona written as the caller actually behaves, free-text `metrics` the judge scores, and optional `dynamic_variables` / `tool_mocks`. Run them as a batch test. Two rules learned the hard way: pin the version explicitly (a definition left on an old version silently tests the wrong agent), and if the tests run against a real backend, design the set to net to zero — book, then reschedule, then cancel the same fixture — and run them one at a time, in order.

---

## Anti-Patterns — Avoid These at All Costs

These are bugs observed repeatedly in production. The skill prevents them by default; awareness during iteration is the safety net. Detail in [`references/anti-patterns.md`](references/anti-patterns.md).

1. **Instructing silence.** "Do not generate any further text" → LLM reads the stage direction aloud verbatim. Always give it a concrete line.

2. **Anti-duplicate prose guards** that depend on LLM history-reading. Use an `equation` edge on `{{ticket_id}} exists` instead — equations evaluate before prompts, so this short-circuits any prose-based collection logic.

3. **`always_edge` on multi-turn collection nodes.** It fires after the first question, abandoning the flow. Use conditional `edges[]` for multi-turn collection.

4. **Inline conditional dynamic variables** ("that's `{{name}}`, right?"). Empty values produce literal `[Name]` substitution leaked to the caller. Always fact-style global Caller Context.

5. **Loose edge conditions** ("if caller wants help"). Captures intended cases plus unintended ones. Be specific; add `finetune_transition_examples` for ambiguous prompts.

6. **Combining collection + closing + tool call in one node.** The LLM forgets it already spoke a closing and re-delivers it. Split into the 4-node Standard Collection Pattern.

7. **Tool with placeholder URL.** Silently fails at runtime. Always use a real URL or remove the tool reference.

8. **Duplicate edge IDs.** Caused by copy-pasting nodes. Validation script catches these — never skip Step 7.

9. **`enable_backchannel: true`.** Deprecated in practice and audible as interrupting. Keep it false everywhere.

10. **Line echo treated as a caller.** The line plays the agent's own voice back ~1 s late and STT files it as speech, so the agent answers itself on the greeting. Opening node at `interruption_sensitivity: 0` **plus** an echo rule in Turn-Taking.

11. **A turn that ends in a statement.** Nothing for the caller to answer → no edge can fire → dead air until the reminder. End every turn with a question.

12. **Sharpening prose instead of moving the capability.** If a node can call the tool, it will. Split the step into a node that carries only the tool it may use.

13. **`exists` on a variable that may be empty.** It is true for an empty string, and a missing variable renders as literal braces. Branch on an exact sentinel and make the else-path the safe one.

14. **Model-carried UUIDs.** IDs get garbled between tool calls. Resolve them server-side from what the caller actually said.

---

## Debug an Existing Flow

If the user shows you a broken `conversationFlow` JSON or describes a stuck/looping/repeating call, follow this triage:

1. **Read the symptom.** "Two tickets created" → confirmation node re-entering collection. "Stage direction read aloud" → instructing silence. "Stuck after tool call" → missing `always_edge`. "Wrong department transfer" → loose edge condition. The symptom-to-cause map is in [`references/anti-patterns.md`](references/anti-patterns.md) §Common Failure Modes.

2. **Run validation.** `python validate_flow.py <agent.json>` — surfaces structural problems (duplicate IDs, broken refs, missing `else_edge`, tool placeholder URLs).

3. **Audit the node in question.** Read its instruction text for the anti-patterns list above. Look for "DO NOT" / "STOP" / "STAY SILENT" / "DO NOTHING" — these are red flags.

4. **Check edge specificity.** Vague conditions like "ready" or "wants help" need either rewording (specific phrase) or `finetune_transition_examples` (3–4 short transcripts showing when this edge should and shouldn't fire).

5. **Propose a minimal fix** before rewriting. Often a single edge condition tightening, or replacing a "DO NOTHING" block with `"Got it — one moment."` plus an `always_edge` is enough.

### Before blaming the flow

Half of "the agent is broken" reports are not the graph. Check, in this order:

1. **Which version took the call?** The call record names the agent version. If it predates your fix, the fix was never published — or the number is pinned to a specific version.
2. **What did the tools return?** Read the actual tool results in the call record. A `success: false`, an empty payload, or a result that never arrived (dropped for size) explains most "she said something odd" reports.
3. **Is the "caller" turn really the caller?** A turn that repeats the agent's own words back, garbled, is line echo (anti-pattern 15), not a person.
4. **Did the caller actually answer?** A stall after a sensible agent line is usually a turn that ended in a statement (16), not a broken edge.
5. **What do the timestamps say?** Dead air that matches `reminder_trigger × count + end_call_after_silence_ms` is a settings problem, not a prompt problem.

Then read the whole transcript top to bottom before proposing anything. Quote the exact turn that went wrong when you report it — "the model got confused" is not a diagnosis.

---

## Reference Files

Read these on demand. They contain the depth that doesn't fit in this overview.

- [`references/node-types.md`](references/node-types.md) — Full schema for all 11 node types. Read when you're picking node types or writing JSON.
- [`references/edges-and-transitions.md`](references/edges-and-transitions.md) — Edge primitives, equation operators (full list verified against Retell docs), evaluation order, finetune examples. Read when designing transitions.
- [`references/global-prompt-template.md`](references/global-prompt-template.md) — Production-grade global prompt template with all 10 sections including pronunciation rules. Borrow verbatim.
- [`references/anti-patterns.md`](references/anti-patterns.md) — Failure modes library with symptom → cause → fix table. Read when debugging.
- [`references/standard-patterns.md`](references/standard-patterns.md) — The Standard Collection Pattern + 9 other reusable shapes (transfer-with-fallback, code-then-branch, IVR, choice gate, outbound opener with answering-machine guard, human-scale tool schemas).
- [`references/post-call-analysis.md`](references/post-call-analysis.md) — Field types, use cases, the IVR-fields cheatsheet.
- [`references/agent-settings.md`](references/agent-settings.md) — Everything that lives on the agent rather than the flow: backchannel, interruption sensitivity, the dead-air arithmetic, STT mode, voicemail, webhooks, versions and publishing, dashboard drift, building a sibling agent by transform. Read before shipping anything.
- [`references/backend-contract.md`](references/backend-contract.md) — What the webhook side owes the agent: response-size budget, server-side ID resolution, retries, honest failure envelopes, post-call records. Read when wiring tools.

## Asset Templates

Bundled JSON to copy and customize. Do not write a flow from scratch — start from one of these.

- [`assets/starter-flow.json`](assets/starter-flow.json) — Minimal valid flow (greeting → end). Use as the base for any new agent.
- [`assets/collection-flow-template.json`](assets/collection-flow-template.json) — 4-node Standard Collection Pattern, ready to fill.
- [`assets/transfer-with-fallback.json`](assets/transfer-with-fallback.json) — Transfer node + `Transfer failed` fallback path.
- [`assets/code-and-branch-pattern.json`](assets/code-and-branch-pattern.json) — `code` → `extract_dynamic_variables` → `branch` deterministic mid-call routing.

## Scripts

- [`scripts/validate_flow.py`](scripts/validate_flow.py) — Schema validator. Run before delivering. Failure means do not ship.

---

## Prefer platform features over hand-rolled prompt

Before writing custom prompt rules, check whether Retell already ships the behavior — it's more reliable and saves tokens:

- **Agent Handbook presets** (one-click toggles): **Smart Matching** (tolerates STT name variations like Brandon/Brendon — use instead of custom "match the name" prose), **Speech Normalization** (numbers/dates/money/phones/emails → natural speech), **Echo Verification** (read-back of names/numbers), **NATO Phonetic** (spelling), **Scope Boundaries** (only answer from prompt/KB — curbs KB over-answering for legal/medical), **AI Disclosure When Asked** (on by default). Don't duplicate a preset in your prompt — pick one or the other, or they fight each other.
- **Components** (reusable sub-flows): package a shared block (e.g. "Qualification Intake", "Verify Identity") as a **library Component** and drop it into multiple agents — the clean way to share intake nodes between, say, an outbound and an inbound flow instead of duplicating nodes. Components can't nest; the main flow's global prompt applies inside them.
- **Agent Transfer (Agent Swap)** node: hand off to another Retell agent with full history and near-zero latency (no new phone call) — prefer it over a phone `transfer_call` when switching between *your own* agents (e.g. English→Spanish, front-desk→specialist).
- **Knowledge Base**: retrieved chunks land under `## Related Knowledge Base Contexts`; defaults are 3 chunks / 0.6 similarity; prefer `.md` sources. To stop the agent inventing facts, add "Only answer using ## Related Knowledge Base Contexts; if absent, say you don't have that info" (or enable Scope Boundaries).

## Token Budget

Retell bills on prompt tokens. Keep the global prompt lean — under ~3,500 tokens stays in the base rate. If the agent needs large reference material (product catalogs, FAQ corpora, policy docs), attach as a Knowledge Base via `knowledge_base_ids` rather than stuffing into the global prompt.

---

## Final Checklist (do before delivering)

- [ ] Every flow uses the 4-node Standard Collection Pattern (or has a justified deviation)
- [ ] Global prompt has all 10 sections, including pronunciation rules and defensive variable handling
- [ ] Every tool with >2s latency has `speak_during_execution: true` AND a pinned `execution_message_description`
- [ ] Every `branch`, `extract_dynamic_variables`, `code` node has an `else_edge`
- [ ] Every transfer node has a `Transfer failed` edge to a graceful fallback
- [ ] No placeholder URLs (`TODO.example.com`)
- [ ] No "DO NOTHING" / "STAY SILENT" instructions in any node
- [ ] No inline conditional dynamic variable substitution in agent speech
- [ ] `enable_backchannel` is false (and `backchannel_frequency` / `backchannel_words` are gone)
- [ ] Opening node at `interruption_sensitivity: 0`, echo rule present in the global prompt's Turn-Taking
- [ ] Every conversation node's turn ends with a question
- [ ] Silence budget set deliberately (`end_call_after_silence_ms` + reminders ≈ 30–70 s of dead air), and the global prompt's silence prose matches it
- [ ] Outbound only: `start_speaker: "user"`, answering-machine rule in both openers, `voicemail_option` set, wrong-person / bad-time / not-interested exits wired
- [ ] No tool parameter asks the model to carry an ID it read from another tool
- [ ] `validate_flow.py` passes
- [ ] Agent **published**, and the published version read back: change present, tool URLs are production
- [ ] Recommended test scenarios delivered alongside the JSON
