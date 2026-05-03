# Retell AI — Inbound Voice Agent Build Guide
## How to Build a Best-in-Class Conversational Flow Agent

**Source:** Retell AI Official Documentation, Retell AI Engineering Blog, Retell AI Changelog  
**Applies to:** Conversation Flow Agents (recommended for complex inbound routing)  
**Last verified:** April 2026

---

## Table of Contents

1. [Architecture Decision — Which Agent Type to Use](#1-architecture-decision--which-agent-type-to-use)
2. [Global Settings Configuration](#2-global-settings-configuration)
3. [Node Types Reference](#3-node-types-reference)
4. [Building the Conversation Flow](#4-building-the-conversation-flow)
5. [Transition Conditions](#5-transition-conditions)
6. [Prompt Engineering — Global Prompt](#6-prompt-engineering--global-prompt)
7. [Node-Level Prompt Engineering](#7-node-level-prompt-engineering)
8. [Agent Handbook Presets](#8-agent-handbook-presets)
9. [Components — Reusable Sub-Flows](#9-components--reusable-sub-flows)
10. [Global Nodes — Handling Deviations](#10-global-nodes--handling-deviations)
11. [Tools and Function Calling](#11-tools-and-function-calling)
12. [Guardrails](#12-guardrails)
13. [Speech and Audio Settings](#13-speech-and-audio-settings)
14. [Testing Strategy](#14-testing-strategy)
15. [Debugging Playbook](#15-debugging-playbook)
16. [Deployment and Monitoring](#16-deployment-and-monitoring)
17. [Performance and Cost Optimization](#17-performance-and-cost-optimization)
18. [Critical Rules and Anti-Patterns](#18-critical-rules-and-anti-patterns)

---

## 1. Architecture Decision — Which Agent Type to Use

Retell AI offers three agent types. Choose correctly before building.

| Agent Type | Use Case | When to Choose |
|---|---|---|
| Single Prompt | Simple, linear flows with 1-3 decision paths | Basic FAQ, simple routing, quick lookups |
| Multi Prompt | Moderate complexity with a few branching paths | 3-5 distinct call intents, moderate tool use |
| Conversation Flow | Complex inbound routing, multiple call types, strict data collection, policy disclosures | Any agent with 5+ distinct call paths, compliance requirements, or mandatory field collection |

**For a complex inbound agent (like Keyline's Aubrey), always use Conversation Flow.** Reasons:

- Single prompts become "prompt spaghetti" beyond 3-4 conditional branches
- A single long prompt increases hallucination risk and latency proportionally
- Conversation Flow provides deterministic transitions and node-level control
- Each node is independently optimizable without touching the rest of the agent
- Conversation Flow agents are easier to QA test and maintain long-term

**The 32k token context limit** applies to all agent types. Single prompt agents risk exhausting this on long calls. Conversation Flow nodes reset context per node, avoiding this issue entirely.

---

## 2. Global Settings Configuration

Access global settings by clicking the empty canvas and selecting Settings in the dashboard.

### 2.1 Voice Selection
- Select voice from the dropdown. Listen to samples before selecting.
- Adjust voice temperature (lower = more stable and consistent, higher = more expressive variation).
- Adjust voice speed (reduce for elderly callers, increase for brief transactional calls).
- Adjust voice volume as needed.
- Custom voices can be added from ElevenLabs community or via voice cloning.
- Cartesia is available as a secondary provider with automatic fallback capability.

### 2.2 Language
- Set the language the agent will understand (the language of the incoming audio).
- If callers may speak multiple languages, set to `multi` to auto-detect.
- Include `respond in [language]` in the prompt for the agent to respond in a specific language.

### 2.3 LLM Model Selection
- **Recommended starting model:** GPT-4.1 — optimal balance of quality, latency, and cost.
- Models can be overridden at the individual node level. Use cheaper models for simple routing nodes, premium models for sensitive or complex intake nodes.
- Pricing is calculated by time spent in each node multiplied by the model price for that node, aggregated across the full call.
- Tune LLM temperature: lower = more deterministic (recommended for data collection nodes), higher = more natural variation (recommended for conversational opening nodes).

### 2.4 Global Prompt
- Defines the agent's persona, identity, and agent-wide constraints.
- Available in every node and influences all response generation across the full call.
- Keep the global prompt focused on identity and guardrails, not task logic. Task logic belongs in individual nodes.

### 2.5 Speech Settings
| Setting | Recommendation |
|---|---|
| Background sound | Enable "call center" background sound for human-like environment |
| Responsiveness | Default is fine for most callers. Reduce by 0.1 increments for elderly callers (adds 0.5s wait time per 0.1 reduction) |
| Interruption Sensitivity | Reduce if callers in noisy environments cause false barge-ins |
| Backchanneling | Enable with words like "uh huh", "got it", "I see" for natural active listening signals |
| Boosted Keywords | Add brand names, product names, and caller names commonly mentioned |
| Speech Normalization | Enable if agent frequently reads back dates, prices, addresses, or phone numbers |
| Reminder Frequency | Set how often agent reminds a silent caller that it is still on the line |

### 2.6 Call Settings
- Voicemail detection: Configure behavior when voicemail is detected (leave message or hang up).
- End call on silence: Set duration of silence after which the call auto-ends.
- Call duration limit: Set a maximum call length.
- Pause before speaking: Add a brief pause at the start to handle the moment the caller is still picking up.

### 2.7 Who Speaks First
- Click the Begin node to configure whether the agent speaks first or waits for the caller.
- For inbound calls, agent speaks first. Always.

---

## 3. Node Types Reference

Conversation flow agents use multiple node types to handle different scenarios. Every node defines a small set of logic, and the transition condition determines which node to transition to next.

| Node Type | Purpose | Use When |
|---|---|---|
| Conversation Node | Dialogue without tool calling | Collecting information, delivering information, asking questions |
| Subagent Node | Dialogue with tool calling | Collecting data AND triggering an API, CRM write, or function simultaneously |
| Function Node | Deterministic API/tool execution | Executing a lookup, creating a ticket, sending an SMS, triggering a transfer |
| Logic Node | Conditional branching | Routing based on variables collected earlier in the call |
| End Node | Call termination | Clean call close with a farewell message |
| Global Node | Available from any point in the flow | Distress detection, fatality handling, out-of-scope fallback, app push refusal |

### Node Naming Convention
Name every node descriptively using the pattern `[Action]_[Outcome]`:
- `collect_caller_name`
- `verify_caregiver_id`
- `route_travel_request`
- `deliver_10day_warning`
- `transfer_payroll_team`

Descriptive names are essential because node transition history in call transcripts shows node names. This is your primary debugging tool.

---

## 4. Building the Conversation Flow

### 4.1 Flow Design Principles

**One job per node.** A node should do exactly one thing. If a node collects name, state, and call type, split it into three nodes: `collect_name`, `collect_state`, `identify_call_type`. This is the most important design rule.

**Design entry and exit on every node.** Every node must have a defined incoming edge and at least one outgoing edge. Nodes without exits create dead ends where the call gets stuck.

**Map your flows on paper first.** Before touching the dashboard, draw the full flow:
- Start node
- Caller identification branch
- Each call type as its own sub-flow
- Transfer nodes
- End nodes
- Global fallback nodes

**Cover all branches.** For every decision point, define what happens in every possible scenario including refusals, ambiguous answers, and unexpected inputs. Uncovered branches cause the agent to get stuck or loop.

### 4.2 Recommended Node Architecture for Inbound

```
[Begin]
    |
[Open Call — Greeting + Who Speaks First]
    |
[Identify Caller Type]
    |--- New Caller? → [Collect Name + State]
    |--- Returning Caller (Caller ID match)? → [Skip to Intent Detection]
    |
[Intent Detection / Routing Node]
    |--- Travel Request → [Travel Sub-Flow]
    |--- Incident Report → [Incident Sub-Flow]
    |--- Pay Stubs → [Pay Stubs Sub-Flow]
    |--- Direct Deposit → [DD Sub-Flow]
    |--- Income Letter → [Income Letter Sub-Flow]
    |--- Pay Issue → [Immediate Transfer Node]
    |--- New Prospect → [Prospect Sub-Flow]
    |--- Case Manager → [Case Manager Sub-Flow]
    |--- Unclear → [Clarify Caller Type]
    |
[Sub-Flow Nodes per Call Type]
    |
[Confirmation + Ticket Creation]
    |
[Close / End Node]

[GLOBAL NODES — Active from any point]
    |--- Distressed Caller → [Empathy + Immediate Transfer]
    |--- Fatality → [Fatality Sensitivity + Human Callback Flag]
    |--- Out-of-Scope → [Redirect + Callback Ticket]
```

### 4.3 Splitting Data Collection Across Nodes

Never collect more than one field per conversation node. The agent will inconsistently skip fields if a single node is responsible for multiple data points.

**Wrong — single node collecting 4 fields:**
```
Node: collect_incident_details
Instruction: Collect caregiver name, patient name, date/time of incident, and location.
```

**Correct — one node per field:**
```
Node: collect_caregiver_name
Node: collect_patient_name
Node: collect_incident_datetime
Node: collect_incident_location
```

This approach ensures 100% field collection consistency and gives you precise debugging visibility when a field is being missed.

---

## 5. Transition Conditions

Transition conditions are the core control mechanism of Conversation Flow. They determine when and where the agent moves between nodes.

### 5.1 Two Types of Conditions

**Prompt Conditions (LLM-evaluated):**
Used when the trigger depends on what the caller said or the conversation context.
```
- User indicates they want to submit a travel request
- User confirms the summary is correct
- User declines the app link and wants to proceed by phone
- User expresses distress or frustration
- User mentions their member is in the hospital
```

**Equation Conditions (Hardcoded, evaluated before prompt conditions):**
Used when the trigger depends on a known variable value. Evaluated in order top to bottom, first match wins.
```
- {{departure_days_out}} > 30
- {{departure_days_out}} >= 10 AND {{departure_days_out}} <= 30
- {{departure_days_out}} < 10
- {{travel_destination}} == "outside_us"
- {{caller_type}} == "case_manager"
- {{dd_hold_reason}} == "authorization"
- {{caller_id_recognized}} exists
```

### 5.2 Transition Condition Best Practices

Write conditions that are self-contained and do not rely on the node instruction text for interpretation:
- Good: `When user confirms they do not want to use the app and want to proceed by phone`
- Bad: `User refuses` (too vague, may match unintended responses)

Cover every possible exit from a node:
- Happy path (user gives expected input)
- Refusal path (user says no or pushes back)
- Ambiguous input path (user gives unclear answer)
- Silence path (user does not respond)

Use Global Nodes to catch anything not covered by specific conditions rather than trying to enumerate every edge case in every node.

Order matters for equation conditions. Place the most specific conditions first. The first condition that evaluates true wins.

---

## 6. Prompt Engineering — Global Prompt

The global prompt sets identity, tone, and agent-wide guardrails. It is injected into every node. Keep it focused and under 500 tokens.

### 6.1 Recommended Global Prompt Structure

```
## Identity
You are [Agent Name], a [role] for [Company Name].
Your job is to [one sentence purpose].
You speak on behalf of [Company Name] and represent their brand in every interaction.

## Tone and Style
- Warm, confident, and efficient. Never robotic.
- Use natural contractions. Sound like a professional human, not a script.
- Keep responses concise. Ask one question at a time.
- Acknowledge what the caller says before moving to the next step.
- Never use filler acknowledgments like "Certainly!" or "Absolutely!"

## Core Constraints
- You only handle: [list supported call types briefly]
- You never provide legal, medical, financial, or contractual advice.
- You never accept financial information (account numbers, routing numbers) by phone.
- You never fabricate information. If you do not know, redirect to a human team member.
- You never close a call while the caller still has an open question.

## Mandatory Behaviors
- Always collect caller name and state before beginning any intake.
- Always confirm collected data back to the caller before submitting.
- Always generate a ticket for every unresolved call.
- If caller shows distress at any point, stop intake and escalate immediately.
```

### 6.2 What NOT to Put in the Global Prompt
- Step-by-step task instructions (put these in individual nodes)
- Field-by-field data collection sequences (put these in individual nodes)
- Call-type-specific policy rules (put these in the relevant sub-flow nodes)
- Transfer logic (put this in function/transfer nodes)

Keeping the global prompt lean keeps every node fast and reduces hallucination risk.

---

## 7. Node-Level Prompt Engineering

Each node instruction should be narrow, specific, and focused on exactly one task.

### 7.1 Node Prompt Structure

```
## Goal
[One sentence describing what this node must accomplish]

## Your Task
[Exact steps the agent must follow in this node]

## What to Say
[Sample script or talking points. Not word-for-word required, but must cover all required content]

## What NOT to Do
[Explicit prohibitions specific to this node]

## Mandatory Content
[Any disclosures, warnings, or statements that must be delivered verbatim or near-verbatim]
```

### 7.2 Example Node Prompts

**Node: deliver_travel_10day_warning**
```
## Goal
Inform the caller that their travel date is within 10 days and approval is not guaranteed.

## Your Task
Deliver the 10-day timing warning before proceeding to collect the remaining travel fields.

## Mandatory Content
You must say: "Since your travel date is within 10 days, we can submit this request but 
approval is not guaranteed due to the timing."

## What NOT to Do
Do not skip this warning even if the caller seems to already know.
Do not stop the intake. Continue collecting fields after delivering the warning.
```

**Node: collect_hospital_details**
```
## Goal
Collect the full hospital name, city, and state where the member was admitted.

## Your Task
Ask for the hospital name and its city and state. Collect both city AND state explicitly.
Do not assume the state from context. Always ask for it directly.

## What to Say
"Which hospital was she taken to, and what city and state is it in?"

## What NOT to Do
Do not accept city alone. If the caller only provides a city, follow up:
"And what state is that hospital in?"
Do not accept a geographically impossible city/state combination without flagging it.
```

---

## 8. Agent Handbook Presets

The Agent Handbook is a collection of ready-to-use prompt presets that improve how your agent communicates. Each preset encodes a specific best practice — toggle it on and the behavior is added automatically.

### 8.1 Preset Reference Table

| Preset | Tokens | Default | Recommended Setting for Inbound Care Agent |
|---|---|---|---|
| Default Personality | ~480 | ON | Keep ON — enforces Acknowledge → Statement → Next Step structure |
| Natural Filler Words | ~100 | OFF | Optional — adds "um", "uh" sparingly. Enable for casual tone, disable for formal/regulated contexts |
| High Empathy | ~70 | OFF | Enable — essential for distress, incident, and fatality calls |
| Echo Verification | ~190 | OFF | Enable — confirms names, IDs, phone numbers, critical intake fields |
| NATO Phonetic Alphabet | ~190 | OFF | Enable — useful for confirming email addresses and caregiver IDs |
| Speech Normalization | ~910 | OFF | Enable — converts dates, times, numbers to natural spoken form |
| Smart Matching | ~110 | OFF | Enable — handles transcription variations of names gracefully |
| AI Disclosure When Asked | ~30 | ON | Keep ON |
| Scope Boundaries | ~60 | OFF | Enable — prevents agent from fabricating out-of-scope answers |

### 8.2 Key Behavioral Note — Default Personality
The Default Personality preset enforces the response structure: **Acknowledge → Statement → Next Step**. It also prevents the agent from using robotic affirmations like "Certainly!" and "Absolutely!" which are common AI tells. This is the single highest-value preset. Never disable it unless you have written your own full personality prompt.

### 8.3 Conflict Avoidance
If your custom prompt already covers empathy guidelines or scope boundaries, disable the overlapping preset to prevent inconsistent behavior from duplicated instructions.

---

## 9. Components — Reusable Sub-Flows

Components are mini flows (groups of nodes) that you can reuse across agents and flows. Benefits include reusability, consistency, clean canvas, and faster iteration.

### 9.1 When to Use Components

Create a Component for any sub-flow that:
- Appears in more than one call type (e.g., caller identification is used in every flow)
- Has independent logic that does not depend on the parent flow's context
- Would benefit from centralized maintenance

**Recommended Components for a complex inbound agent:**

| Component | Purpose | Used In |
|---|---|---|
| `caller_identification` | Collect name + state for new callers | Every call type |
| `app_push` | Offer app link, handle refusal | Travel, Incident, Pay Stubs |
| `ticket_creation` | Generate ticket and confirm to caller | Every unresolved call |
| `warm_transfer` | Execute warm transfer with hold message | Pay Issue, Auth Hold, Health Coach |
| `confirmation_summary` | Read back collected fields and confirm | Travel, Incident, Address Update |

### 9.2 Shared vs Local Components

Use **Shared (Library) Components** for logic used across multiple agents (e.g., caller ID, ticket creation). Changes sync automatically to every agent.

Use **Local (Agent) Components** for logic specific to one agent. Changes only affect that agent.

**Critical:** When you publish an agent, shared components are snapshotted as local copies in the published version. This prevents library updates from breaking production calls. Your draft keeps syncing with the library.

### 9.3 Component Design Rules
- Every component must have a Begin node and at least one Exit node properly linked.
- If the Exit node is not linked correctly, the agent gets stuck inside the component and cannot transition out.
- Components cannot contain other components.
- Tools defined inside a component are scoped to that component and are not visible at agent level.

---

## 10. Global Nodes — Handling Deviations

Global nodes allow users to skip or jump between nodes. This is particularly useful for inbound support cases without a rigid call structure.

### 10.1 What Are Global Nodes
Global nodes are conversation nodes with a defined entry condition that can trigger from any point in the flow. They interrupt the current flow, handle the special case, and then return control to the main flow.

### 10.2 Required Global Nodes for Inbound Agents

**Distressed Caller Global Node**
- Entry condition: `User expresses distress, frustration, crying, panic, or any strong negative emotion`
- Action: Deliver empathy response, then immediate warm transfer. No further intake.
- Do NOT continue standard intake after distress is detected.

**Fatality Notification Global Node**
- Entry condition: `User reports the death of a member or client`
- Action: Deliver condolences, do not process as standard ticket, flag for human callback.
- Priority flag required. Human callback even after hours.

**Out-of-Scope Request Global Node**
- Entry condition: `User asks for something the agent cannot help with (legal, medical advice, contract terms, billing, etc.)`
- Action: Acknowledge scope limit, offer transfer or callback ticket, collect name and number.
- Never fabricate an answer to avoid the scope boundary.

**App Push Refusal Global Node**
- Entry condition: `User declines the app link offer`
- Action: Accept refusal immediately and proceed to manual intake. Never push the app a second time.

### 10.3 Adding Example Conversations to Global Nodes
You can add example conversations to help the LLM understand when and when NOT to trigger a global node. This is essential for distress detection to avoid false positives (e.g., a caller saying "I'm frustrated about the form" vs. a caller who is genuinely in crisis).

---

## 11. Tools and Function Calling

### 11.1 Available Built-In Tools
- Calendar / appointment scheduling
- SMS sending (send app link, confirmation texts)
- Warm call transfer
- Custom API integrations via webhooks
- MCP (Model Context Protocol) server connections for CRMs, ticketing systems, etc.

### 11.2 SMS Node — Sending App Links
Use an SMS node to send the caregiver app link mid-call. Triggered when the caller agrees to receive the link. The SMS is sent using the same phone number as the voice agent with no extra setup.

### 11.3 Warm Transfer Best Practices
- Always deliver a hold message before initiating the transfer: "Please hold while I connect you."
- Always create a backup ticket before the transfer in case the transfer fails.
- Configure the transfer node with a fallback destination in case the primary destination is unavailable.
- The transferred agent inherits the full conversation context from the original call.

### 11.4 Ticket Creation via Function Node
Place a function node after every intake completion node. The function node calls your CRM (Monday.com, HubSpot, etc.) with all collected fields:
- Call summary
- Caller name
- Caregiver or client name
- State
- Callback number
- Call type
- Timestamp

After the function node confirms success, the conversation node delivers the ticket confirmation to the caller.

### 11.5 Explicit Tool Trigger Instructions
Always specify exact trigger conditions for tool calls in the node prompt. LLMs do not reliably infer when to call tools from tool descriptions alone.

```
## Tool Usage
When the user confirms the summary is correct, call `create_ticket` immediately.
Do not wait for additional confirmation. Do not ask any further questions before calling.

When the user says "yes I want the link" or any affirmative to the app offer, 
call `send_sms_app_link` immediately with the caller's phone number.
```

---

## 12. Guardrails

Guardrails are a built-in content moderation layer that checks agent responses and user messages for prohibited topics. When a guardrail triggers, the prohibited content is automatically replaced with a safe placeholder message, keeping the call going without interruption.

### 12.1 Guardrail Types

**Output Guardrails** — checks what the agent says:
- `regulated_professional_advice` — prevents agent from giving legal, medical, or financial advice
- `illicit_and_harmful_activity` — blocks harmful content
- `harassment` — blocks abusive language

**Input Guardrails** — checks what the caller says:
- `platform_integrity_jailbreaking` — detects and blocks attempts to manipulate the agent

### 12.2 Recommended Guardrails for Healthcare/Homecare Agents

Enable these output guardrails at minimum:
- `regulated_professional_advice` — prevents agent from advising on medical treatment, legal rights, or financial decisions
- `harassment`

Enable input guardrail:
- `platform_integrity_jailbreaking`

Note: Guardrails add approximately 50ms of latency per call. This is acceptable for most use cases.

---

## 13. Speech and Audio Settings

### 13.1 Backchanneling
Enable backchanneling to add natural active listening signals during caller speech. Configure words like "uh huh", "I see", "got it". This prevents calls from sounding like the agent went silent while the caller is still speaking.

### 13.2 Boosted Keywords
Add domain-specific terms that the speech recognition engine should bias toward:
- Company name and product names
- Staff names (health coaches, case managers)
- Medical terms relevant to your service (for healthcare agents)
- Caregiver ID formats (e.g., "CG-" prefix)

### 13.3 Pronunciation Guide
Add pronunciation entries for any term the TTS engine consistently mispronounces. Common entries for homecare: caregiver ID numbers, medical center names, specific city/county names.

### 13.4 Speech Normalization (LLM Level)
Enables the LLM to format its text output for natural speech. "$758.08" becomes "seven fifty-eight dollars and eight cents". "4/13" becomes "April thirteenth". Enable this for any agent that reads back dates, times, amounts, or phone numbers.

---

## 14. Testing Strategy

### 14.1 Testing Tools Available in Retell

| Tool | Purpose |
|---|---|
| LLM Playground | Test node-level responses in text without audio |
| LLM Simulation Testing | AI-simulated caller with custom persona. Run automated test cases. |
| Audio Testing | Full end-to-end voice call simulation |
| Call History | View past calls with node transition path highlighted |

### 14.2 LLM Simulation Testing — Writing Test Personas

For each test case, write a caller persona that specifies exactly how the simulated caller should behave:

```
You are a caregiver calling to report an incident. Your member fell at home and was 
taken to St. Mary Medical Center in Houston, Texas. You are slightly anxious but 
cooperative. You decline the app link when offered. You will give information only 
when asked — do not volunteer fields the agent has not requested yet.
```

### 14.3 Test Case Coverage Checklist

For every call type, run tests for:
- Happy path (caller follows expected flow perfectly)
- App refusal path (caller declines app, agent proceeds manually)
- Ambiguous input (caller gives unclear answer, agent must clarify)
- Missing field (caller skips a required field, agent must catch it)
- Out-of-scope question mid-flow (caller asks something unrelated mid-intake)
- Distress mid-call (caller becomes upset mid-intake)
- Multi-request call (caller has more than one issue, agent must handle each)

### 14.4 Validating Node Transitions

After each test, check the call transcript in the History tab. Node transition events appear inline with the transcript. Verify:
- Agent entered the correct node for each caller input
- Agent did not skip any required nodes
- Agent transitioned at the correct trigger point
- No nodes looped unexpectedly

### 14.5 Import/Export Test Cases
Test cases can be imported and exported as JSON. Export your test suite before making major flow changes so you can regression test after updates.

---

## 15. Debugging Playbook

### 15.1 Issue: Agent Skips a Required Field

**Cause:** Multiple fields assigned to one node.  
**Fix:** Split into one node per field. Each node has one and only one field to collect with a single transition condition: "user has provided the field."

### 15.2 Issue: Agent Transitions to Wrong Node

**Cause:** Transition conditions are too vague or overlap between paths.  
**Fix:**
1. Make each condition more specific. Add the exact trigger intent.
2. Add finetune examples to the transition condition showing the correct mapping.
3. Simplify the condition into multiple smaller conditions.

### 15.3 Issue: Agent Loops on the Same Node

**Cause:** Transition condition is never satisfied, or missing a default exit edge.  
**Fix:**
1. Add a fallback transition condition: "After 2 failed attempts to collect the information, transition to `fallback_transfer`."
2. Ensure all nodes have at least one unconditional fallback edge.

### 15.4 Issue: Agent Ignores Caller's New Request Mid-Flow

**Cause:** No Global Node defined to intercept topic changes.  
**Fix:** Add Global Nodes for all major topic changes. When caller mid-flow asks about something unrelated to the current node, the Global Node intercepts and routes correctly.

### 15.5 Issue: Agent Confirms Incorrect Data

**Cause:** Agent echoed back caller speech without validating it.  
**Fix:**
1. Enable Echo Verification in Agent Handbook.
2. Add an explicit node instruction: "Validate that the city and state combination is geographically valid. If impossible (e.g., Denver, Florida), ask for clarification before confirming."
3. Add Smart Matching to handle transcription variations.

### 15.6 Issue: Agent Hallucinates Information

**Cause:** Single long prompt attempting to cover all scenarios; agent fills gaps with invented content.  
**Fix:**
1. Enable Scope Boundaries in Agent Handbook.
2. Break down to Conversation Flow architecture if not already using it.
3. Add explicit node instruction: "If you do not have the answer, say: 'I do not have that information. Let me connect you with someone who can help.'"
4. Use a Knowledge Base for factual content rather than embedding facts in the prompt.

### 15.7 Issue: Agent Ends Call Before Caller Is Finished

**Cause:** Premature close trigger or missing check for follow-up questions.  
**Fix:**
1. Before every End Node, add an offer node: "Is there anything else I can help you with today?" with a transition condition back into the routing node if the caller says yes.
2. Add explicit prompt instruction in the close node: "Do not close the call if the caller is still speaking or has asked an unanswered question."

---

## 16. Deployment and Monitoring

### 16.1 Versioning
- Use agent versioning to separate draft and production versions.
- Never edit a live production agent directly. Always draft in a separate version.
- Publish to production only after completing the full test case suite.

### 16.2 A/B Testing
- Retell supports A/B testing between agent versions.
- Use A/B testing to validate prompt changes, voice changes, or flow restructures on a subset of live calls before full rollout.

### 16.3 Post-Call Analysis
Configure post-call analysis to automatically extract:
- Call outcome (resolved / transferred / unresolved)
- Caller intent
- Required fields captured (yes/no per field)
- Policy disclosures delivered (yes/no per required disclosure)
- Sentiment at close

Post-call analysis data feeds into the Analytics Dashboard for trend monitoring.

### 16.4 Monitoring KPIs
| KPI | Target |
|---|---|
| First call resolution rate | Track percentage resolved without transfer |
| Field capture rate | Track per-field collection success across call types |
| Disclosure delivery rate | Track whether mandatory policy disclosures are delivered |
| Average call duration | Baseline and monitor for regressions after prompt changes |
| Transfer success rate | Track whether warm transfers complete vs. drop |
| Node transition accuracy | Review via call history transcripts |

### 16.5 Alerting
Configure alerts for:
- Call volume spikes (may indicate a system issue)
- High transfer rate on a specific call type (may indicate broken node)
- High average call duration (may indicate agent looping)
- Low resolution rate (may indicate missing flow coverage)

---

## 17. Performance and Cost Optimization

### 17.1 Model Assignment Strategy
Assign models at the node level to balance cost and quality:

| Node Type | Recommended Model |
|---|---|
| Opening / greeting | Standard model (GPT-4.1-mini or equivalent) |
| Caller type routing | Standard model |
| Data collection | Standard model |
| Policy disclosure delivery | Standard model (content is scripted, not generative) |
| Distress detection / empathy | Premium model (GPT-4.1 or equivalent) |
| Out-of-scope handling | Premium model |
| Complex confirmation summary | Premium model |

### 17.2 Prompt Length and Latency
Latency grows approximately linearly with prompt length. Best practice targets:
- Global prompt: under 500 tokens
- Individual node instructions: under 500 tokens each
- Total active tokens at any node: aim below 5,000 tokens

Prompt token billing on Retell activates at 3,500 tokens. Prompts beyond this threshold incur proportionally higher cost per call.

### 17.3 Reduce Redundancy
Do not repeat global prompt content in node prompts. Global content is already available to every node. Node prompts should contain only what is unique to that node.

### 17.4 Call Duration Impact on Cost
Calls are billed by duration. Reducing unnecessary turns reduces cost:
- Deliver information once clearly, do not repeat unless asked.
- Ask one question per turn. Multi-question turns cause longer responses and more processing time.
- Do not over-confirm. One confirmation summary at the end of intake is sufficient.

---

## 18. Critical Rules and Anti-Patterns

### 18.1 Critical Rules — Never Violate

| Rule | Why It Matters |
|---|---|
| One node, one job | Multiple responsibilities per node causes inconsistent field collection |
| Never push app after first refusal | Caller experience degrades; agent sounds persistent and robotic |
| Always collect name and state before any intake | Without identification, tickets and callbacks are useless |
| Always create a backup ticket before warm transfer | Transfers can fail; ticket ensures follow-up regardless |
| Never close while caller has open question | Premature closes generate callbacks and negative experience |
| Never confirm geographically incorrect data | Bad data in tickets creates operational failures downstream |
| Always deliver all mandatory policy disclosures | Missing disclosures create compliance and payroll liability |
| Never fabricate out-of-scope information | Hallucinated answers create trust and legal risk |

### 18.2 Anti-Patterns to Avoid

**The Routing Loop:** Agent keeps returning to the same routing node because it lost context of what was already collected. Fix: use dynamic variables to track collected fields and use equation conditions to skip already-completed steps.

**The Prompt Essay:** A single node instruction that is 2,000+ words attempting to cover all scenarios. Fix: split into multiple nodes, use global nodes for edge cases.

**The Orphan Node:** A node that has incoming edges but no outgoing edges. The agent reaches it and cannot continue. Fix: every node must have at least one outgoing edge.

**The Phantom Name:** Agent addresses the caller by name without having collected it in this session. Fix: name must always be established through either caller ID recognition or explicit collection. Never assume a name.

**The Silent Transfer:** Agent says "I am connecting you" and immediately closes the call without confirming the transfer completed. Fix: hold message, then confirm transfer before closing.

**The Repeated App Push:** Agent offers the app link more than once after a refusal. Fix: use a dynamic variable `{{app_refused}}` set to true on first refusal, and use an equation condition to skip the app push node if `{{app_refused}} == true`.

---

*Sources: Retell AI Documentation (docs.retellai.com), Retell AI Engineering Blog (retellai.com/blog), Retell AI Changelog (retellai.com/changelog), OpenAI x Retell AI partnership documentation.*
