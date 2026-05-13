# Test Script — Ambiguous Prospect Inquiry

**Why this flow:** Q3 from client feedback (the "what happens next" caller) has **no follow-up disambiguator** in the current build. The OPENING node has three plausible destinations for this kind of caller (`prospect-intake`, `prospect-status-check`, `transfer-eligibility/Alyssa`) and routing depends entirely on the LLM's inference. With a vague opener, the agent will often guess wrong.

---

## Test Call Script (caller side)

> **Aubrey:** *Hi, this is Aubrey with Keyline Home Care. How can I support you today?*
>
> **You:** Hi — I'm just trying to figure out what happens next.
>
> *(Stay vague. Don't say "I applied", don't say "I want to enroll", don't say "screening".)*
>
> **You (if Aubrey asks who you are):** I'm a caregiver.
>
> **You (if Aubrey asks anything else):** Yeah, I just want to know what the next step is.

---

## Likely Mistake

With no explicit signal, the agent will pick **one** of these — and the choice is non-deterministic across calls:

| Wrong route | What you hear | Why it's wrong |
|---|---|---|
| → `PROSPECT INTAKE` | "Keyline helps families get paid to care for loved ones at home..." then starts asking the 16 intake questions | You may have already applied — re-collecting from scratch is poor UX |
| → `PROSPECT STATUS CHECK` | "You can check status through the Keyline app. Want me to send the link?" | You may NOT have applied yet — the app link won't help |
| → `TRANSFER - ALYSSA` | "Let me connect you with Alyssa who handles phone screening..." | You may not have submitted an application at all yet |

The agent **does not** ask one clarifying question to find out which case you're in.

---

## Correct Flow (what should happen)

```
OPENING
  └─ Caller says something ambiguous about "next steps" / "what happens now"
       │
       ▼
[NEW NODE: PROSPECT DISAMBIGUATOR]
  "Just to point you to the right place — have you already
   submitted an application with us, or are you just starting
   to explore your options?"
       │
       ├─ "Not yet / just exploring"  ───►  PROSPECT INTAKE (collect 16 fields)
       │
       ├─ "Applied, no screening yet" ───►  PROSPECT STATUS CHECK
       │                                    (app link or Care Team callback)
       │
       └─ "Applied + had screening"   ───►  TRANSFER - ALYSSA
                                            (next step is nurse assessment)
```

**One clarifying turn. Three clean routes. No guessing.**

---

## How to Verify After Fix

Run the same vague script three times. The agent should:

1. Always ask the clarifying question (not jump straight into a flow).
2. Route correctly based on your answer.
3. Never start the 16-question intake without confirming the caller hasn't already applied.
