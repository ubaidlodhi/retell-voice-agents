# Platform Features — Presets, Speech Settings & LLM Config

The dashboard half of the agent. These are toggles and sliders, not prompt prose — and for many behaviors they're more reliable and cheaper (in prompt tokens) than writing the rule yourself. Recommend the right ones in Step 2, and in Step 4 make sure you didn't also hand-write something a preset already does.

## Table of contents
- [Agent Handbook presets](#agent-handbook-presets)
- [Don't duplicate a preset in prose](#dont-duplicate-a-preset-in-prose)
- [LLM configuration](#llm-configuration)
- [Speech settings](#speech-settings)
- [Call settings](#call-settings)

---

## Agent Handbook presets

One-click best-practice prompts. Each adds a small number of tokens to **every** turn, so enable deliberately. New agents start with **Default Personality** and **AI Disclosure When Asked** on.

| Preset | Tokens | Voice | Chat | Default | What it does / when |
|---|---|---|---|---|---|
| **Default Personality** | ~480 | ✓ | ✓ | On | Professional rep voice: Acknowledge → Statement → Next Step; trims filler; kills "Certainly!/Absolutely!". Leave on unless you wrote a fully custom personality. |
| **Natural Filler Words** | ~100 | ✓ | — | Off | Sparse "um/uh/you know" for a human feel. Great for sales/CS/casual. Avoid for medical/legal/formal. |
| **High Empathy** | ~70 | ✓ | ✓ | Off | Acknowledges feelings before solving. For support, complaints, emotional callers. |
| **Echo Verification** | ~190 | ✓ | — | Off | Reads back names/numbers; spells uncommon names. For booking & data capture. |
| **NATO Phonetic Alphabet** | ~190 | ✓ | — | Off | Spells using "A as in Alfa…". For emails, reference numbers, account IDs. |
| **Speech Normalization** | ~910 | ✓ | — | Off | Formats numbers/dates/money/phones/addresses/emails into natural speech. Highest token cost. |
| **Smart Matching** | ~110 | ✓ | — | Off | Tolerates STT name variants (Brandon/Brendon) on lookups — treats close matches as the same. |
| **AI Disclosure When Asked** | ~30 | ✓ | ✓ | On | Confirms it's a virtual assistant when asked. Keep on for transparency/compliance. |
| **Scope Boundaries** | ~60 | ✓ | ✓ | Off | Only answers from prompt + KB; says "I don't have that" instead of guessing. For healthcare/finance/legal. |

Notes:
- Five presets (Filler, Echo, NATO, Speech Normalization, Smart Matching) are **voice-only** and greyed out for chat agents.
- Presets are fixed — you can't edit their text. For custom behavior, write it in the prompt instead.
- **Speech Normalization** has two layers: this preset shapes the LLM's *text output*; the separate `speech_normalization` audio option converts text to spoken form at the audio level. They can be used together.

### Recommended preset sets by use case

- **Appointment booking / data capture:** Default Personality, Echo Verification, Speech Normalization (or NATO for spelling-heavy), Smart Matching (if doing name lookups).
- **Sales / outbound:** Default Personality, Natural Filler Words, High Empathy.
- **Support / complaints:** Default Personality, High Empathy, Scope Boundaries.
- **Healthcare / finance / legal:** Default Personality, Scope Boundaries, Echo Verification; **not** Natural Filler Words (too casual for the context).

## Don't duplicate a preset in prose

The most common conflict: a hand-written empathy paragraph **and** the High Empathy preset, or a full pronunciation ruleset **and** Speech Normalization. They produce inconsistent, sometimes contradictory behavior, and you pay tokens twice. **Pick one source per behavior.** During Step 4, scan the prompt against the enabled presets and delete the prose that overlaps. Rough mapping of prose section → preset:

| Prompt prose | Overlapping preset |
|---|---|
| Pronunciation library (phone/email/number/date) | Speech Normalization |
| "Spell it as B-as-in-Bravo…" | NATO Phonetic Alphabet |
| "Read names/numbers back to confirm" | Echo Verification |
| "Show empathy before solving" | High Empathy |
| "Use casual fillers like um/uh" | Natural Filler Words |
| "Only answer from what you know / the KB" | Scope Boundaries |
| "If asked, say you're an assistant" | AI Disclosure When Asked |

## LLM configuration

### Model
GPT-4.1 is Retell's recommended starting point — best balance of quality, latency, and cost for voice. Reasoning models (GPT-5, GPT-5.1) behave differently around silence (the `NO_RESPONSE_NEEDED` stop sequence is unsupported — see `prompt-sections.md` §9), so flag the model choice whenever you write turn-taking rules.

### Temperature
Controls randomness. Lower = more consistent, which matters most for reliable tool calls and data capture.

| Temperature | Behavior | Best for |
|---|---|---|
| 0.0–0.3 | Highly consistent, deterministic | Function calling, data collection, technical support |
| 0.4–0.7 | Balanced | General customer service, sales |
| 0.8–1.0 | Creative, varied | Casual/companion conversation |

By use case: **appointment booking** 0.1–0.3 · **support** 0.3–0.5 · **sales outreach** 0.5–0.7 · **companion** 0.7–0.9.

### Structured Output
Constrains the model to valid function calls with all required params. Enable for production agents with critical function calls or financial/medical data. Trade-offs: slower auto-save (schema caching), less flexibility. Consider leaving off during early iteration, then enable for production.

### Fast Tier
Routes calls through high-priority infrastructure: ~25% faster average response, 50% less latency variance, higher availability. Costs **1.5×** the model rate. Worth it for high-value or time-sensitive calls (emergency, premium support, demos); skip for internal testing and low-stakes/high-volume calls.

## Speech settings

Fine-tune how the agent interacts at the audio level (dashboard → speech settings):

- **Background sound** — ambient call-center/office sound for realism.
- **Responsiveness** — how quickly the agent jumps in. Lower it for elderly or deliberate callers (more wait time before responding). "Dynamically adjust based on user input" adapts to the caller's pace.
- **Interruption sensitivity** — how easily the caller can cut the agent off. Lower it to resist background speech/noise.
- **Backchanneling** — **keep it off** (`enable_backchannel: false`, and don't set `backchannel_frequency` / `backchannel_words`). Deprecated in practice: modern voices carry acknowledgement in their delivery, the injected "mm-hm" lands on the wrong beat and reads as interrupting, and it feeds more of the agent's own audio back into the STT.
- **Boosted keywords** — bias recognition toward specific terms; add brand names, product names, and people's names so STT gets them right.
- **Speech normalization (audio)** — converts dates/currency/numbers to plain words at the audio layer (complements the preset).
- **Reminder frequency** — how often the agent nudges an inactive caller (pairs with your silence prose — keep them consistent).
- **Pronunciation** — per-word pronunciation guide for tricky brand/product names.

**Voice speed** lives in the voice popover (0.5×–2.0×) and can "dynamically adjust based on user input" — the agent tracks the caller's words-per-minute and shifts to match, and the caller can ask it to speed up or slow down.

## Call settings

- **Voicemail detection** — what to do when voicemail is detected (leave a message / hang up).
- **End call on silence** — auto-end after N seconds of inactivity (make this longer than your prose silence check so they don't conflict).
- **Max call duration** — hard cap.
- **Pause before speaking** — when the agent speaks first, wait a moment so it doesn't talk over the caller picking up.

Recommend these alongside the prompt so the platform behavior and the prompt's turn-taking rules agree rather than fighting.
