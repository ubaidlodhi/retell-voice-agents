# Variables & Knowledge Base

How to feed per-call data and bulk facts into a single-prompt agent. Two mechanisms: **dynamic variables** (small, per-call values via `{{...}}`) and the **Knowledge Base** (large bodies of facts retrieved automatically).

## Table of contents
- [Dynamic variables overview](#dynamic-variables-overview)
- [System variables (auto-populated)](#system-variables-auto-populated)
- [Custom variables (you inject)](#custom-variables-you-inject)
- [Inbound: using {{user_number}}](#inbound-using-user_number)
- [Missing & nested variables](#missing--nested-variables)
- [Knowledge Base](#knowledge-base)

---

## Dynamic variables overview

Dynamic variables use `{{variable_name}}` syntax and let one prompt adapt to every call. Two kinds: **system** variables Retell populates automatically (zero setup), and **custom** variables you inject per call. They work in prompts, the begin message, tool URLs/descriptions/params, voicemail prompts, transfer numbers, and the webhook URL.

> **All custom variable values must be strings.** Numbers, booleans, and other types aren't supported when injected via the API.

In supported fields, type `{{` to open a variable picker; you can also type the name by hand.

## System variables (auto-populated)

No configuration required. Include the relevant ones in the **Context** section so the agent grounds in real time and never hallucinates the date.

**Universal (voice + chat):**
| Variable | Meaning | Example |
|---|---|---|
| `{{current_time}}` | Current time in America/Los_Angeles | "Thursday, March 28, 2024 at 11:46 PM PST" |
| `{{current_time_<TZ>}}` | Current time in any IANA zone, e.g. `{{current_time_America/New_York}}` | EST string |
| `{{current_hour}}` / `{{current_hour_<TZ>}}` | Hour as a decimal fraction | "3.5" |
| `{{current_calendar}}` / `{{current_calendar_<TZ>}}` | 14-day calendar from today | multi-line list |
| `{{session_type}}` | "voice" or "chat" | voice |
| `{{session_duration}}` | How long the session's been running | "20 minutes 30 seconds" |

**Phone-call only:**
| Variable | Meaning |
|---|---|
| `{{user_number}}` | The other party's number — caller's `from` on inbound, the dialed number on outbound |
| `{{agent_number}}` | The Retell number — dialed number on inbound, originating number on outbound |
| `{{direction}}` | "inbound" or "outbound" |
| `{{call_id}}` | Unique call session ID |
| `{{call_type}}` | "web_call" or "phone_call" |

(Multi-state agents also get `{{current_agent_state}}` / `{{previous_agent_state}}` — not relevant to single-prompt.)

**Always set `<TZ>` to the client's real IANA zone** (`America/New_York`, `Asia/Karachi`, `Europe/London`, `Australia/Sydney`…). The bare `{{current_time}}` defaults to Los Angeles, which silently breaks scheduling for clients elsewhere.

## Custom variables (you inject)

Per-call data passed in at call start:
- **Outbound:** in the `retell_llm_dynamic_variables` field of the Create Phone Call API.
- **Inbound:** returned from your Inbound Call Webhook.
- **Defaults:** set agent-level default values as fallbacks for when a variable isn't supplied.

Document each in the **Context** section with usage guidance. Example:
```
- {{first_name}}: caller's first name. Use it a couple of times, not every sentence.
- {{company_name}}: caller's company (B2B). "I see you're with {{company_name}}."
- {{lead_source}}: where the lead came from — internal context only, don't mention it to the caller.
```

## Inbound: using {{user_number}}

For inbound agents, `{{user_number}}` is the caller's number — useful for:
- **CRM lookup:** pass it to a custom function immediately to pull the caller's record before the conversation proceeds (so the agent can greet by name without asking).
- **Callback scheduling:** "I've got your number as [read with pronunciation rules] — is that the best one to reach you?"
- **Caller ID / spam check:** cross-reference against known lists.

Example Context snippet:
```
The caller is reaching you from {{user_number}}. If a CRM lookup function is available, call it immediately with this
number to pull their profile before continuing. Otherwise, use it as the callback number. When reading it back, use the
phone-number pronunciation rule (digit by digit with pauses).
```

## Missing & nested variables

**Missing:** if a variable isn't set, it stays literal — the caller would hear "Hello {{user_name}}". Always include the defensive rule in the Context section:
```
If any variable still shows its curly braces (e.g. you literally see "{{first_name}}"), it wasn't set —
do not read the braces or the name aloud. Use a generic alternative instead ("Hey there").
```
Best practices: set agent-level defaults, write the prompt to work with or without the variable, and test both set and unset.

**Nested:** Retell resolves inside-out. If a custom `my_timezone` = `America/Chicago`, then `{{current_time_{{my_timezone}} }}` resolves to `{{current_time_America/Chicago}}` and then to the time string — handy when the timezone is per-caller.

---

## Knowledge Base

When the agent must answer from a large body of facts (product catalog, FAQ, policies, pricing, service descriptions), attach a **Knowledge Base** instead of stuffing it into the prompt. The prompt is for *instructions*; the KB is for *supporting information*.

### How it works
- Create a KB from URLs, documents, or text snippets; link it to the agent.
- Retrieval is automatic — **no prompt change needed to trigger it.** On every response, Retell uses the transcript so far to pull the most relevant chunks and appends them under the header `## Related Knowledge Base Contexts`.
- Latency impact is generally under 100ms.

### Retrieval settings
- **Chunks to retrieve:** 1–10, default **3**. More chunks = more context but a longer prompt and possibly worse generation. 3 is right for most cases.
- **Similarity threshold:** default **0.6**. Higher = fewer but closer matches.

### Anti-hallucination guard
KBs reduce made-up answers but don't eliminate them. To force grounding, add to the **Guardrails** section:
```
Only answer using the information in ## Related Knowledge Base Contexts. If that section is missing or doesn't contain
the answer, say: "I don't have that information, but I can connect you with someone who does."
```
The **Scope Boundaries** preset does the same thing as a one-click toggle — use one or the other.

### Authoring best practices
- Prefer **`.md`** over `.txt` — well-structured Markdown chunks and retrieves more accurately.
- Clear, descriptive headings; keep each `##` focused and short; split long sections.
- Short paragraphs and lists; avoid walls of text.
- Be specific — include names, dates, units; avoid ambiguous "it"/"this" since prior chunks may not be in context.
- Put **instructions in the prompt, facts in the KB** — never the reverse.

### When KB instead of prompt
If you're tempted to paste a pricing sheet, FAQ list, or policy doc into the prompt, that's the signal to use a KB — it keeps the prompt under the token budget and the facts easier to update. Bulk reference material is exactly what the KB is for.
