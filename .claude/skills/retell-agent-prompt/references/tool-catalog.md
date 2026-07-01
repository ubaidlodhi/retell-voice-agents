# Tool Catalog — Retell tools & trigger-prompt patterns

Every function type a single-prompt agent can use, with the **exact prompt language** that makes the LLM call it at the right time. Tools are added in the dashboard's **Functions** section; the prompt just tells the agent *when* to use them.

The cardinal rule (from Retell's prompt-engineering guide): the LLM decides whether to call a tool from your **prose**, so define clear triggers, **reference each tool by its exact configured name** (in backticks), and state when *not* to call. Without explicit triggers, agents mis-fire or skip calls — and single-prompt agents have no node graph to fall back on.

## Table of contents
- [How to write a trigger (the pattern)](#how-to-write-a-trigger-the-pattern)
- [Speak-during / speak-after execution](#speak-during--speak-after-execution)
- Pre-built tools: [End Call](#end-call) · [Transfer Call](#transfer-call) · [Press Digit](#press-digit-ivr) · [Check Availability](#check-availability) · [Book Calendar](#book-calendar) · [Send SMS](#send-sms)
- Builder tools: [Custom Function](#custom-function) · [Code Tool](#code-tool) · [Extract Dynamic Variables](#extract-dynamic-variables) · [Agent Transfer](#agent-transfer-agent-swap) · [MCP](#mcp-tools)
- [Choosing between them](#choosing-between-overlapping-tools)
- [Keep it under 5 tools](#keep-it-under-5-tools)

---

## How to write a trigger (the pattern)

For every tool, the prompt should answer four things:

1. **Name** — the exact function name, in backticks: `book_appointment`.
2. **Trigger** — a keyword, intent, or phase: "once the caller confirms the date and time."
3. **Inputs** — which collected values to pass.
4. **Speech** — what to say before it runs and after it returns.

**Template:**
```
- When [precise trigger condition], call function `[exact_name]` with [inputs].
  Before it runs, say: "[short say-before line]."
  After it returns: "[how to use / speak the result]."
```

## Speak-during / speak-after execution

Two dashboard toggles per tool that the LLM honors when the caller is silent during the call:

- **Speak during execution** — agent says one line the moment the tool fires. Enable for user-facing actions (looking something up); disable for background tasks (attaching a note). Pin the line so it doesn't improvise differently each time.
- **Speak after execution** — agent keeps talking after the result returns (deliver the result, continue, or call another tool). Enable for almost everything *except* fire-and-forget actions like pressing a digit.

Both are prompt-based: the LLM generates the message from the config and the conversation.

---

## End Call

Gracefully hangs up. By default the agent never ends the call — you must add this tool and tell it when.

- **When to use:** task complete, caller says goodbye, or after the disconnection check in the silence rule.
- **Trigger prompt:**
```
When the caller says "thank you", "goodbye", or "bye", or once the booking is confirmed and there's nothing left to do,
call function `end_call`. Say a warm closing first: "Thanks so much, {{first_name}} — have a great day!"
```

## Transfer Call

Routes the live call to a human or another number (phone calls only, not web calls). Number is e.164 or a SIP URI, or a dynamic variable resolved at runtime.

- **Cold transfer:** hand off and drop. **Warm transfer:** agent can detect a human, play hold music, navigate an IVR, whisper a private message to the target, or do a three-way intro.
- **When to use:** caller explicitly asks for a person; out-of-scope issue; escalation/anger.
- **Trigger prompt:**
```
If the caller asks to speak to a person, says "transfer me" or "let me talk to someone", or is frustrated and you can't
resolve it, call function `transfer_call`. Say first: "Sure thing, let me connect you right now."
```
- **Config notes:** choose caller-ID (Retell number vs caller's number — requires telephony support); for warm transfers set whisper / three-way / human-detection in the dashboard. Custom SIP headers must start with `X-` or be `User-To-User`.

## Press Digit (IVR)

Sends DTMF keypad tones — for **outbound** agents navigating phone trees. Audio-input IVRs you handle by just speaking; DTMF menus need this tool.

- **When to use:** outbound call hits an automated menu requiring keypress.
- **Trigger prompt** (give navigation goal + keywords, not just a digit):
```
## IVR Navigation
Your goal is to reach the [scheduling / appointments] department.
- If the IVR lets you speak a department, say it clearly.
- If it instructs you to press a number, call function `press_digit` with that digit.
- Prefer options: Scheduling, Appointments, New patients, Front desk. Avoid: Billing, Referrals, Medical records.
- If you reach the wrong company, call `end_call`. If put on hold, respond with NO_RESPONSE_NEEDED until a person speaks.
```
- If you know the exact path, you can hard-code it: "Press digit 1 to reach support."
- For IVR-heavy outbound work with post-call IVR analytics, that's a sign you've outgrown single-prompt — consider `retell-conversation-flow`.

## Check Availability

Pre-built tool that queries open calendar slots (Cal.com / Google Calendar style).

- **When to use:** appointment-setting Core Task, before offering a time.
- **Trigger prompt:**
```
When the caller wants to book and you have their preferred day, call function `check_availability` for that day.
While it runs, say: "Let me see what we've got open." Then offer the nearest slot: "I've got [time] on [date] — does that work?"
```

## Book Calendar

Pre-built tool that creates the calendar event once a slot is agreed.

- **Trigger prompt:**
```
Once the caller confirms a specific date and time from the available slots, call function `book_appointment`
with the date, time, timezone, and caller name. Say first: "Perfect, let me lock that in." After it returns, confirm:
"You're all set for [date] at [time]."
```
- Always **confirm the slot back** before booking, and only book times that came from `check_availability`.

## Send SMS

Sends a text mid-call (confirmations, links, follow-ups).

- **Trigger prompt:**
```
After booking, if the caller wants a confirmation text, call function `send_sms` to {{user_number}} with the appointment
details. Say: "I'll text you the details now."
```

---

## Custom Function

Your own API call. Retell POSTs the function name + args to your URL; the response (any format, capped at 15,000 chars) comes back as a string to the LLM. Use for CRM lookups, order status, eligibility checks, writes to your systems.

- **When to use:** any integration with your backend — especially anything needing auth, secrets, or writes.
- **Trigger prompt:**
```
When the caller gives their name and date of birth, call function `lookup_patient` to pull their record.
While it runs, say: "One sec while I pull that up." Then use the returned details to continue.
```
- **Config notes:** GET/POST/PATCH/PUT/DELETE; headers and query params can include dynamic variables; define params as JSON schema (remember top-level `"type": "object"`); extract response fields into dynamic variables (e.g. `{{patient_status}}`) for use later. Verify requests via the `X-Retell-Signature` header. Set a generous timeout for cold-start endpoints (n8n/serverless).

## Code Tool

Runs JavaScript in Retell's sandbox — no server needed. For formatting, calculations, and simple read-only lookups.

- **When to use:** date math, string cleanup, combining variables, a quick `fetch()` to a low-risk public API.
- **Trigger prompt:**
```
When the caller asks about shipping cost, use the `calculate_shipping` tool with their zip and order weight.
```
- **Environment:** `dv.<name>` for dynamic variables (all strings), `metadata.<key>` for call metadata, `fetch()` for HTTP, `console.log()` for test output. Standard JS built-ins only — no `require`/`import`. Code ≤5,000 chars; result ≤15,000 chars; timeout 5–60s.
- **Security:** `dv` and `metadata` are stored in plaintext on every call record — never put API keys or credentials there. For internal systems, writes, payments, or regulated data, use a **Custom Function** on your backend, not Code Tool.

## Extract Dynamic Variables

Pulls typed values from the caller's speech and saves them as dynamic variables for later in the call.

- **Types:** Text, Number, Enum (with options), Boolean.
- **Trigger prompt:**
```
When the caller states their name and phone number, call function `extract_contact_details` to capture them.
```
- Useful for capturing structured data you'll reference later (e.g. routing on an enum) without a backend round-trip.

## Agent Transfer (Agent Swap)

Hands the conversation to **another Retell agent** with near-zero latency and full context — no new phone call.

- **Why over Transfer Call:** lower latency, no telephony failure risk, the destination agent inherits the full transcript, call metadata, and all dynamic variables (so no handoff message needed), and you don't need separate numbers per agent.
- **When to use:** switch between *your own* agents — front-desk → specialist, or English → Spanish agent.
- **Trigger prompt:**
```
If the caller asks to book an appointment, use the `agent_transfer` tool to hand off to the Booking Agent.
```
- To pass a specific value, extract it into a dynamic variable first; there's no separate "pass variables" param — shared call context carries it.
- Note: multiple agents swapping mid-call is itself a sign the job may be better modeled as a `retell-conversation-flow`.

## MCP Tools

Connect the agent to a remote MCP server and call its tools mid-call.

- **Trigger prompt:**
```
When the caller asks to verify their account, call tool `verify_user` with their account number.
```
- **Config notes:** add the MCP server (URL, optional headers/query params), select which tools to expose, and extract response fields into dynamic variables. Same prompt discipline as custom functions — explicit triggers by exact tool name.

---

## Choosing between overlapping tools

| You need to… | Use |
|---|---|
| Look up / write to your own backend, with auth or secrets | **Custom Function** |
| Format, calculate, or hit a low-risk public API, no server | **Code Tool** |
| Capture typed fields from what the caller said | **Extract Dynamic Variables** |
| Hand off to *your other* Retell agent, keep context | **Agent Transfer** |
| Send the call to a human / external number | **Transfer Call** |
| Use an external MCP server's tools | **MCP** |
| Book/check appointments on a connected calendar | **Check Availability + Book Calendar** |

## Keep it under 5 tools

Retell's guidance: a single prompt handling **more than 5 functions** starts calling them unreliably. If the agent genuinely needs more, that's the graduation signal — recommend `retell-conversation-flow`, where each tool lives on a deterministic node instead of competing for the LLM's attention in one prompt.
