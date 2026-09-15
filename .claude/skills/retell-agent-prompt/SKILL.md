---
name: retell-agent-prompt
description: >
  Create production-grade Retell AI single-prompt voice agents — one comprehensive prompt that governs an
  entire phone call (identity, conversation flow, tool triggers, pronunciation, guardrails). Use this skill
  whenever the user wants to build a Retell single-prompt agent, write a voice agent prompt, create an AI
  phone/voice caller or receptionist, design an outbound or inbound calling script, or turn a call script
  into a single-prompt agent — in any vertical (appointment setting, lead qualification, customer support,
  real estate, healthcare, insurance, home services, debt collection, SaaS demos). Trigger on "Retell
  single-prompt agent", "voice agent prompt", "AI caller prompt", "AI receptionist", "write me a Retell
  prompt", "outbound calling script", "convert this script into a Retell agent", or even just "I need a
  prompt for my AI phone agent". This is for ONE-PROMPT agents (a single LLM context, no node graph). If the
  agent needs a multi-node branching graph with deterministic per-branch tool calls, transfers, and IVR
  navigation, use retell-conversation-flow instead. When unsure between the two, still trigger this skill and
  use its decision guide to route.
---

# Retell Single-Prompt Agent Builder

Build robust, human-sounding Retell **single-prompt** voice agents. The output is a complete, copy-paste-ready prompt the user drops straight into the Retell dashboard's prompt editor, plus the dashboard settings (model, temperature, presets, tools, KB) that make it work.

A single-prompt agent uses **one comprehensive prompt as the agent's entire brain**. There is no node graph and no deterministic routing — every behavior (identity, tone, flow, tool calls, pronunciation, guardrails) is governed by prose the LLM reads on every turn. That makes the prompt's structure and clarity the whole ballgame.

## When to use this vs multi-prompt vs conversation-flow

| Need | Use |
|---|---|
| One continuous conversation, mostly linear, 1–3 tools | **this skill** |
| Quick prototype, demo, or simple inbound/outbound script | **this skill** |
| Conversation splits into distinct prompted *states* (qualify → then book) where you want tools available only in certain states | multi-prompt agent (point the user to Retell's multi-prompt builder) |
| Multi-node graph: branch on a variable, call tools mid-flow without an LLM decision, IVR navigation, warm transfers, per-flow tickets, post-call extraction | `retell-conversation-flow` |

**Retell's own graduation rule:** move off a single prompt once it exceeds **~1000 words** or needs **more than 5 functions**. Past that, single prompts start to drift — see *Why a single prompt drifts at scale* below. If the user is already past these thresholds, say so and recommend `retell-conversation-flow`; don't force a giant single prompt.

When you're genuinely unsure, ask: *"Is this one continuous conversation, or does it branch into separate stages with different tools per stage?"* Branches with per-stage tools → conversation flow.

## Why a single prompt drifts at scale

A single prompt has no graph to enforce order or gate tools, so as it grows you see: **behavioral drift** (agent ignores instructions in edge cases), **unreliable function calling** (with many tools, the LLM mis-fires or skips calls), **context confusion** (loses track of where it is), and **maintenance pain** (one wall of text becomes impossible to debug). This skill counters drift with disciplined sectioning, numbered conversation phases, and explicit tool triggers — but those techniques have a ceiling. Respect the graduation rule.

---

## Core Principles

These are the non-negotiables. Everything in the architecture exists to serve them.

1. **Brevity is king on voice.** Caller attention drops sharply after 8–10 seconds of uninterrupted AI speech. Default every response to 1–2 sentences. Go longer only to explain something genuinely complex, and even then break it into conversational chunks. A monologuing agent is the #1 cause of hang-ups.

2. **Sound human, not helpful.** LLMs default to polished written prose; phone calls are messy. The prompt must explicitly demand contractions ("I'm," "we've," "that's"), natural fillers ("so," "got it," "okay," "hmm"), and casual phrasing. "Sure thing," not "Certainly." Where Retell ships a preset for this (Natural Filler Words, High Empathy), prefer the preset over writing your own — see *Prefer platform features* below.

3. **One question at a time.** Stacking questions in one turn confuses callers and tanks completion. Ask one thing, wait, acknowledge the answer, then move on.

4. **Explicit tool triggers — this matters more here than anywhere.** With no graph to force a call, the LLM decides whether to invoke a tool purely from your prose. Vague descriptions cause mis-fires and missed calls. Specify exact trigger conditions (keyword, intent, or phase), reference each tool by its **exact configured name**, and say what to speak before/after. See [`references/tool-catalog.md`](references/tool-catalog.md).

5. **Pronunciation is not optional.** The TTS engine reads exactly what the LLM writes. Write "1/15" and the caller hears "one slash fifteen." Phone numbers, emails, URLs, times, dates, and currency all need explicit spoken-form rules — either in the prompt (verbatim library in [`references/prompt-sections.md`](references/prompt-sections.md)) or via the Speech Normalization preset.

6. **Prefer platform features over hand-rolled prompt.** Retell ships one-click Agent Handbook presets and dashboard speech/LLM settings that are more reliable and cheaper (in your prompt's token budget) than reinventing them in prose. Always check what's built-in before writing a rule. See below.

---

## The Workflow

Follow this sequence. Each step prevents a class of failure seen in production.

### Step 1 — Interview the user

Don't write a prompt until you know:

- **Purpose:** appointment setting, lead qual, support, reminder, survey, receptionist…?
- **Direction:** inbound or outbound? (Shapes the opener completely — cold-open vs greeting.)
- **Company / brand:** name, what they do, the agent's name (named agents engage better).
- **Tone:** friendly, professional, casual, authoritative? Any brand voice rules?
- **Tools/functions configured** in Retell: end call, transfer, calendar/booking, CRM lookup, SMS, custom API, code tool, MCP? For each, the exact name and when it should fire.
- **Timezone** (IANA, e.g. `America/New_York`, `Asia/Karachi`) for `{{current_time_<TZ>}}` / `{{current_calendar_<TZ>}}`.
- **Inbound only:** should the agent use `{{user_number}}` for CRM lookup / callback / caller ID?
- **Custom dynamic variables** injected at call start (first_name, account_id, lead_source…)? Remember: all must be **strings**.
- **Knowledge base** attached? What domain? (Bulk facts belong in a KB, not the prompt.)
- **Objections / edge cases** specific to their business.
- **Compliance:** any mandatory verbatim language (recording disclosure, mini-Miranda, HIPAA)?

If the user already pasted a draft prompt or call script, extract these answers from it first and only ask about gaps.

### Step 2 — Recommend dashboard settings

The prompt is half the agent; the dashboard settings are the other half. Recommend (details in [`references/platform-features.md`](references/platform-features.md)):

- **Model:** GPT-4.1 is Retell's default sweet spot (quality/latency/cost). Note: reasoning models (GPT-5, GPT-5.1) change how silence is handled — see Turn-Taking.
- **Temperature:** by use case — 0.1–0.3 for data capture/booking, 0.3–0.5 for support, 0.5–0.7 for sales. Lower = more consistent tool calls.
- **Structured Output:** enable for production agents with critical function calls.
- **Conversation initiation:** agent-first (with a begin message) for outbound; user-first or agent-first greeting for inbound.
- **Agent Handbook presets** to toggle on (see Step 4).
- **Fast Tier** only for high-value/time-sensitive calls (1.5× cost).

### Step 3 — Write the prompt, section by section

Start from [`assets/single-prompt-template.md`](assets/single-prompt-template.md) — the paste-ready 9-section skeleton. Fill every section in order; the ordering is tuned for LLM attention (identity + constraints first, edge cases last). For the depth behind each section (rules, examples, the verbatim pronunciation library), read [`references/prompt-sections.md`](references/prompt-sections.md).

The nine sections:

1. **Identity & Role** — who the agent is, who it works for, that this is a live phone call.
2. **Personality & Style** — contractions, fillers, 1–2 sentences, no lists read aloud, mirror caller energy.
3. **Response & Formatting Guidelines** — pronunciation rules (phone/email/URL/time/date/currency), one question at a time, confirm understanding.
4. **Context** — system variables (`{{current_time_<TZ>}}`, `{{current_calendar_<TZ>}}`, `{{user_number}}`, `{{direction}}`) and custom variables, grounded so the LLM never guesses date/time/caller.
5. **Conversation Flow** — numbered phases (Open → Discover → Core Task → Wrap-Up) with transition criteria. Adapt the opener for inbound vs outbound.
6. **Tool Usage** — exact trigger conditions per tool, by exact function name.
7. **Objection Handling** — pre-scripted responses (not interested, busy, remove me, frustrated, out of scope).
8. **Guardrails** — scope limits, no fabrication, no legal/medical/financial advice, abuse handling.
9. **Turn-Taking & Silence** — `NO_RESPONSE_NEEDED` on hold (or the reasoning-model variant), prolonged-silence handling.

For vertical-specific flows, objection scripts, and compliance language, read [`references/industry-patterns.md`](references/industry-patterns.md).

### Step 4 — Prefer platform features over hand-rolled prompt

Before writing prose for a behavior, check whether Retell already ships it. Built-in is more reliable and doesn't eat your prompt's token budget. Full table in [`references/platform-features.md`](references/platform-features.md). Highlights:

- **Default Personality** (on by default) — Acknowledge → Statement → Next Step structure, kills robotic phrasing.
- **Natural Filler Words** — human "um/uh/you know"; great for sales, avoid for medical/legal/formal.
- **High Empathy** — empathy before solution; for support/complaints.
- **Echo Verification** / **NATO Phonetic** — read-back and spelling of names/numbers/emails; for booking and data capture.
- **Speech Normalization** — numbers/dates/money/phones/emails → natural speech. If you enable this, you can drop most of your hand-written pronunciation prose (don't run both — they fight).
- **Smart Matching** — tolerates STT name variants (Brandon/Brendon) on CRM lookups.
- **Scope Boundaries** — only answer from prompt + KB; for healthcare/finance/legal accuracy.

The rule: **don't duplicate a preset in your prompt.** Pick the preset OR the prose, not both, or they produce inconsistent behavior.

### Step 5 — Offload bulk knowledge to a Knowledge Base

If the agent needs to answer from a large body of facts (product catalog, FAQ, policies, pricing), do **not** stuff it into the prompt — attach a Knowledge Base. Retrieved chunks are appended under `## Related Knowledge Base Contexts` automatically (no prompt change needed to trigger retrieval). To stop the agent inventing facts, add: *"Only answer using the information in ## Related Knowledge Base Contexts. If it's missing or doesn't contain the answer, say you don't have that information."* (or enable Scope Boundaries). Details in [`references/variables-and-knowledge.md`](references/variables-and-knowledge.md).

### Step 6 — Deliver

Give the user:
1. The full prompt as one continuous markdown block (`##` headers, **no code fences around it** unless asked) — ready to paste into the prompt editor.
2. A short **dashboard settings summary** — model, temperature, which presets to toggle, conversation initiation, begin message, tools to add, KB to attach.
3. **Variables they must supply** — list every `{{custom_variable}}` the prompt expects at call start, and confirm the timezone used.
4. **What to test first** (Step 7).

### Step 7 — Recommend test scenarios

Tell the user to test these in the Retell web-call simulator before going live:

1. **Golden path** — everything provided smoothly.
2. **Opener** — does the first line sound natural spoken aloud? (Read it in your head as if hearing it.)
3. **Objection** — "not interested" / "I'm busy" / "remove me."
4. **Tool trigger** — does the function fire at the right moment, with the right say-before line?
5. **Out-of-scope question** — does it decline gracefully instead of hallucinating?
6. **Hold / silence** — caller says "hold on" (does it go quiet?); long silence (does it check in / end?).
7. **Missing variable** — run with a custom variable unset; the agent must not read `{{first_name}}` aloud.

---

## Common Pitfalls

The architecture prevents these by default; awareness helps during iteration.

1. **Agent monologues.** 15-second speeches → hang-ups. Enforce 1–2 sentences and micro-phase the flow.
2. **Tool misfires.** Vague trigger prose → wrong-time or skipped calls. Use explicit keyword/phase triggers and exact function names.
3. **TTS disasters.** "one slash fifteen," "four one five eight nine two…" mashed together. Pronunciation rules or Speech Normalization.
4. **Robotic opener.** The first 5 seconds decide if the caller stays. Write the opener as natural speech, not marketing copy.
5. **Reading curly braces aloud.** Unset `{{first_name}}` gets spoken literally. Always include the defensive-variable rule.
6. **Hallucinated facts.** Made-up pricing/availability. Guardrails + KB scope rule.
7. **Duplicating a preset in prose.** Hand-written empathy *and* the High Empathy preset fight each other. Choose one.
8. **Prompt bloat past the graduation rule.** >1000 words or >5 tools → recommend conversation-flow instead of fighting drift.

## Token budget

Retell bills on prompt tokens; the base rate covers roughly the first ~3,500 tokens, and cost + latency scale up beyond that. Keep the prompt lean. Move large reference material to a Knowledge Base. Remember each enabled Handbook preset also adds tokens to every turn (Speech Normalization alone is ~910) — enable deliberately.

---

## Reference files

Read on demand; they hold the depth that doesn't belong in this overview.

- [`references/prompt-sections.md`](references/prompt-sections.md) — Deep guide to all 9 sections, with rules, examples, and the **verbatim pronunciation library** (phone/email/URL/time/date/currency). Read when writing the prompt.
- [`references/tool-catalog.md`](references/tool-catalog.md) — Every Retell tool (End Call, Transfer, Press Digit, Check Availability, Book Calendar, Send SMS, Extract Dynamic Variables, Code Tool, Custom Function, Agent Transfer, MCP) with exact trigger-prompt patterns and speak-during/after guidance. Read when wiring tools.
- [`references/platform-features.md`](references/platform-features.md) — Agent Handbook presets (full table + token costs), speech settings (responsiveness, interruption, boosted keywords), and LLM config (model, temperature, structured output, fast tier). Read in Step 2 and Step 4.
- [`references/variables-and-knowledge.md`](references/variables-and-knowledge.md) — System + custom dynamic variables, defensive handling, nested variables, and the Knowledge Base (when to use, retrieval defaults, anti-hallucination guard). Read for Steps 4–5.
- [`references/industry-patterns.md`](references/industry-patterns.md) — Per-vertical conversation flows, objection scripts, and compliance notes (real estate, healthcare, insurance, home services, financial, SaaS, debt collection, retail).

## Asset template

- [`assets/single-prompt-template.md`](assets/single-prompt-template.md) — The paste-ready 9-section prompt skeleton. Start every new agent from this; fill in, don't write from scratch.

---

## Final checklist (before delivering)

- [ ] Inbound vs outbound opener is correct and sounds natural read aloud
- [ ] Every response example is 1–2 sentences; no bullet/numbered lists inside spoken dialogue
- [ ] Pronunciation handled (rules in prompt **or** Speech Normalization preset — not both)
- [ ] Every tool referenced by its exact configured name, with an explicit trigger condition
- [ ] Objection handling covers: not interested, busy, remove from list, frustrated/angry, out of scope
- [ ] Guardrails section is specific to the domain (scope, no fabrication, no regulated advice)
- [ ] Turn-taking/silence handling present (`NO_RESPONSE_NEEDED` or reasoning-model variant)
- [ ] `{{current_time_<TZ>}}` uses the client's real IANA timezone; defensive rule for unset variables present
- [ ] Inbound: `{{user_number}}` usage addressed. Outbound: custom variables documented with usage guidance
- [ ] No preset duplicated in prose; bulk facts offloaded to a KB
- [ ] Prompt under the graduation rule (~1000 words / 5 tools) — or conversation-flow recommended instead
- [ ] Delivered with dashboard settings summary + required variables + test scenarios
