# Prompt Sections — Deep Guide

The reasoning, rules, and examples behind each of the 9 sections in the single-prompt template. Read this while writing the prompt. The section order is intentional: identity and constraints sit where LLM attention is highest (the top), edge cases toward the end.

## Table of contents
1. [Identity & Role](#1-identity--role)
2. [Personality & Style](#2-personality--style)
3. [Response & Formatting Guidelines](#3-response--formatting-guidelines)
4. [Context (variables)](#4-context-variables)
5. [Conversation Flow](#5-conversation-flow)
6. [Tool Usage](#6-tool-usage)
7. [Objection Handling](#7-objection-handling)
8. [Guardrails](#8-guardrails)
9. [Turn-Taking & Silence](#9-turn-taking--silence)
- [The verbatim pronunciation library](#the-verbatim-pronunciation-library)
- [Sectional prompting: why structure matters](#sectional-prompting-why-structure-matters)

---

## Sectional prompting: why structure matters

Retell's guidance (and ours) is to break the prompt into focused `##` sections rather than one long paragraph. Three reasons: **reusability** (sections port between agents), **maintainability** (change tone without touching tool logic), and **clarity** (LLMs follow structured instructions far more reliably than prose blobs). Keep each section focused; if one balloons, split it. A single prompt is the agent's whole brain — disciplined structure is what keeps it from drifting.

---

## 1. Identity & Role

Define who the agent is, who it works for, and its one core mission, in 3–5 sentences.

**Why it leads:** the model anchors its entire persona and decision-making on this. Vague identity → vague behavior.

Rules:
- Always include **"You are speaking with a caller on the phone right now. This is a live voice conversation, not a text chat."** This single line meaningfully reduces written-prose habits (lists, markdown, over-长 answers).
- Be specific about company and role. "A scheduling assistant at Bright Smile Dental" beats "a helpful assistant."
- Give the agent a name. Named agents measurably improve engagement, and the caller has something to latch onto.
- State the mission as one concrete sentence ("book qualified callers into a free consultation"), not a list of goals.

**Example:**
```
## Identity
You are Maya, a scheduling assistant at Bright Smile Dental, a family dental practice in Austin.
Your primary goal on this call is to book the caller into an available cleaning or consultation.
You are speaking with a caller on the phone right now. This is a live voice conversation, not a text chat.
```

## 2. Personality & Style

This is where you defeat the LLM's default toward polished, formal writing. It is the single biggest lever on whether the agent sounds human.

Core directives to include:
- **Contractions and casual phrasing** — "I'm," "we've," "that's," "don't."
- **Natural fillers, used sparingly** — "So," "Okay," "Got it," "Right," "Makes sense." Add: *don't repeat the same filler back to back.*
- **1–2 sentences max** unless explaining something complex.
- **No formatted text read aloud** — no bullets, no numbered lists, no markdown. "You are speaking, not writing."
- **Mirror caller energy**; **empathy before solution** when they're frustrated.
- **Plain words over corporate** — "sure thing" not "certainly," "let me check" not "allow me to verify."

**AI disclosure:** Retell's *AI Disclosure When Asked* preset is on by default and handles this well. If you write it in prose instead, keep it honest and short — don't coach the agent to dodge ("deflect naturally"), which reads as evasive and can be a compliance problem in regulated verticals. Prefer the preset.

If you're enabling the **Natural Filler Words** or **High Empathy** presets, don't also hand-write those behaviors — pick one source so they don't fight. See `platform-features.md`.

## 3. Response & Formatting Guidelines

How the agent shapes spoken output. Two jobs: enforce **one question at a time / confirm understanding**, and enforce **pronunciation** (the verbatim library is below).

- One question per turn; acknowledge each answer before the next.
- Paraphrase important info back ("So that's a cleaning, next Tuesday afternoon — got it").
- Then the pronunciation rules (phone, email, URL, time, date, currency).

**Big shortcut:** if you enable the **Speech Normalization** preset (or the audio-level `speech_normalization` option), it converts numbers/dates/money/phones/emails to natural speech for you, and you can drop most of the hand-written pronunciation prose. Don't run both the preset and a full prose ruleset — they fight. Keep the prose version when you're *not* using the preset, or when you need a very specific style the preset doesn't produce.

## 4. Context (variables)

Ground the agent in real-time and per-call facts so it never hallucinates the date, time, or caller.

- **System time:** `The current date and time is {{current_time_<TIMEZONE>}}.` Tell the agent to treat it as the single source of truth and resolve relative dates ("tomorrow," "next Friday") against it.
- **Calendar:** `{{current_calendar_<TIMEZONE>}}` gives a 14-day window for scheduling.
- **Inbound caller number:** `{{user_number}}` — for CRM lookup, callback confirmation, or caller ID.
- **Custom variables:** list each one injected at call start with usage guidance (use sparingly, don't over-repeat names).
- **Defensive rule (always include):** *"If any variable still shows its curly braces (e.g. you literally see `{{first_name}}`), it wasn't set — do not read the braces aloud; use a generic alternative."*

Full variable reference (system table, phone-only vars, nested vars, missing-variable behavior) is in `variables-and-knowledge.md`.

## 5. Conversation Flow

The operational core: a numbered, phased playbook with clear transition criteria. Because there's no node graph, these phases are how you impose order on a single LLM context.

Default shape: **Opening → Discovery → Core Task → Wrap-Up.** Each phase: what to do, then how to know you're done and move on.

Adapt the **opener** to direction — it's the highest-stakes part of the call:
- **Outbound (cold-open):** identify yourself, state why you're calling, ask if it's a good time, *then* wait. Sound like a person, not an ad. "Hey, this is Maya over at Bright Smile — I'm calling about the cleaning you asked about. Did I catch you okay?"
- **Inbound (greeting + intent):** greet with company + name, then find out why they're calling within the first exchange or two. "Thanks for calling Bright Smile, this is Maya — how can I help?"

Phase adaptation by use case:
- **Appointment setting** — Core Task = check availability (tool) → offer the nearest slot → confirm date/time/timezone → book (tool).
- **Lead qualification** — Discovery = a scored checklist of qualifying questions; Core Task = route based on score (book, transfer, or nurture).
- **Support** — Discovery = identify the issue; Core Task = resolve from KB or escalate.
- **Reminder / confirmation** — short: confirm identity → state the appointment → confirm/reschedule.

Keep each phase's instructions concrete. "Ask for their preferred day and time" beats "gather scheduling preferences."

## 6. Tool Usage

Include only if tools are configured. This section is where single-prompt agents most often fail, because the LLM decides whether to call a tool purely from your prose — there's no deterministic node forcing it.

For each tool specify, in order:
1. The **exact function name** as configured in Retell (verbatim, in backticks).
2. The **precise trigger** — a keyword, intent, or conversation phase. Not "when appropriate."
3. **What to pass** (which collected values).
4. **What to say** before it runs (`speak_during_execution`) and after it returns.

Full per-tool patterns, plus when to use Check Availability vs Book Calendar vs a Custom Function vs Code Tool vs MCP, are in `tool-catalog.md`. The cardinal rule from Retell's prompt-engineering guide: **define clear triggers and reference tools by exact name** — list the words/phrases that should trigger a call, define call sequences, and state when *not* to call.

## 7. Objection Handling

Callers push back. Without pre-scripted responses the LLM improvises, and improvised objection handling skews either too pushy or too limp. Script at minimum:

- **Not interested** — acknowledge + one-line value + soft next step (send info?).
- **Busy right now** — offer a callback time.
- **Remove me from the list** — comply immediately and warmly; call the opt-out tool if one exists.
- **Frustrated / angry** — acknowledge the feeling, apologize, offer a concrete fix. *Never argue or get defensive.*
- **Out of scope** — admit it, offer follow-up or transfer rather than guessing.

Keep each response to 1–2 sentences and in the agent's voice. Vertical-specific objection scripts (e.g. "I already have an agent" for real estate) are in `industry-patterns.md`.

## 8. Guardrails

Prevents hallucination and keeps the agent in its lane.

- **Scope** — only discuss the company and its domain; deflect competitor questions gracefully.
- **No fabrication** — "I don't have that handy, but I can have someone follow up" instead of inventing pricing/availability.
- **No regulated advice** — no legal/medical/financial advice; redirect to a professional. Critical in healthcare, insurance, finance, legal verticals.
- **Confidentiality** — never disclose internal processes or unlisted pricing.
- **Abuse handling** — stay calm; after a second instance, set a boundary politely.

For factual accuracy, consider the **Scope Boundaries** preset (only answer from prompt + KB) instead of, or alongside, prose — see `platform-features.md`. For KB-backed agents, add the anti-hallucination KB guard from `variables-and-knowledge.md`.

## 9. Turn-Taking & Silence

Handles the caller going quiet or putting the agent on hold — otherwise the agent talks into the void.

- **Hold / "give me a sec":** for non-reasoning models, instruct the agent to reply with exactly `NO_RESPONSE_NEEDED` — a hard-coded stop sequence that suppresses output. For **reasoning models (GPT-5, GPT-5.1)** this is unsupported; instead use prose: *"When the caller asks you to hold, simply do not respond; stay silent until they speak again."* Always check which model the agent runs on.
- **Prolonged silence (~15s)** with no hold cue: a gentle "Hey, are you still there?" Then if silence continues (~10s more), close out gracefully and call `end_call`.

This pairs with the dashboard **Reminder frequency** and **End call on silence** settings — mention them so the prose and the platform behavior agree rather than double-firing.

---

## The verbatim pronunciation library

Drop these into the **Response & Formatting Guidelines** section verbatim when you're *not* using the Speech Normalization preset. They tell the LLM how to write so the TTS engine speaks correctly.

### Phone numbers
```
When speaking a phone number, say it digit by digit with a pause between groups:
- (415) 892-3245 → "four one five — eight nine two — three two four five"
- Keep the spaces around the dash; that's the pause.
- If asked to repeat, say it slower with longer pauses.
```

### Email addresses
```
Spell email addresses out, character by character:
- "@" is pronounced "at"; the "." before the domain is "dot".
- john@acme.com → "j-o-h-n at a-c-m-e dot com".
```

### Website URLs
```
Break URLs into phonetic segments:
- Say "dot" before the top-level domain (dot com, dot net, dot org).
- Spell letter-clusters: "NK" → "en-kay". Pronounce real words normally: "laundry" stays "laundry".
- nklaundry.com → "en-kay-laundry dot com"; abctest.net → "A B C test dot net".
```

### Times & dates
```
- Times in spoken form: "One PM", "Three thirty PM", "Eight forty-five AM". Always include AM or PM.
- Never write "o'clock".
- Dates in spoken form: "January fifteenth", "March third" — not "1/15" or "3/3".
```

### Numbers & currency
```
- Dollar amounts naturally: "two hundred fifty dollars", not "$250".
- Large numbers spelled: "fifteen thousand", not "15,000".
- Street addresses: "four twenty-three Main Street", not "423 Main St."
```

These mirror Retell's published prompt examples; for the optional NATO phonetic spelling style (confirming letters as "B as in Bravo"), enable the NATO Phonetic Alphabet preset rather than writing it out — see `platform-features.md`.
