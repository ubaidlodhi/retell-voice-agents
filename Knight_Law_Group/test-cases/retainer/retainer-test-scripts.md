# Alice Retainer — Test Scripts (Immediate + Outbound)

How to run: open the test form → **https://automations.impleko.ai/form/c1343a46-7114-40dc-abb6-8e9e7119a09f** → set the fields shown in each test → submit → **answer the call** and play the "Caller" lines (improvise naturally, you don't have to read verbatim). Then check the **Pass criteria**. After the call, open the call in the Retell dashboard and confirm the **Expected post-call** `retainer_outcome`.

**Golden rules that apply to EVERY test (auto-fail if broken):**
- Never guarantees a specific dollar amount/outcome; any figure is framed "for the sake of argument."
- Never misstates: fees are **paid by the manufacturer**, the mileage offset is **statutory/fixed**, the 50% touches **only additional damages**.
- Never reads the signing URL aloud (says "the link in your text").
- If asked "are you an AI?" → answers honestly.
- Any clear "stop contacting me" → acknowledges and ends immediately.

---

# PART A — Immediate Walkthrough agent
Form: **Agent = Immediate**, First Name = your name, Language = English (unless noted). (The form sends `entry_mode = immediate_handoff`, so Alice opens with "Ok, I'm back…".)

### A1 — Happy path, sign on the call
- **Caller:** "Sure, go ahead." Then after the walkthrough: "No questions, I'll sign now."
- **Listen for:** the "I'm back…" opener → a brief run through **buyback → manufacturer-paid fees → 50% on additional damages (with the $50k→$100k→$75k example) → mileage offset** → "What questions can I answer before I walk you through signing?" → Close Path 1 ("pull up the text… take a second with the actual damages section…").
- **Pass:** walks all four points, invites questions, drives to signing, says a welcome line after "I signed."
- **Expected post-call:** `retainer_outcome = signed_on_call`.

### A2 — Fee confusion (Branch B)
- **Caller:** "Wait, so what is this going to cost me? I saw hourly rates in there." Then: "And what's that 50% about?"
- **Pass:** "our fees and costs are **paid by the manufacturer, not you**… hourly rates are there for **transparency**… you never get a bill from us." On the 50%: it applies **only to additional damages above the buyback**, walks the $50k→$100k→**$75k** example, "that's the only place a percentage touches your money." Then closes.
- **Expected:** `signed_on_call` (if they sign) or `callback_scheduled`.

### A3 — Mileage offset (Branch C)
- **Caller:** "Why don't I get everything I paid back? There's some mileage deduction."
- **Pass:** validates → "written into the lemon law… **every buyback has it, no matter the firm**… fixed number, doesn't grow… the buyback is only part of your recovery; clients typically end up with more than 100%."
- **Expected:** `signed_on_call` or `callback_scheduled`.

### A4 — Spouse/family review (Branch D) → callback
- **Caller:** "I need to run this by my wife before I sign." Then decline to sign now but agree to a time: "Tonight around 8."
- **Pass:** doesn't fight it, offers to join a call with both, controls the timeline, locks a **specific** follow-up time (no vague "this week").
- **Expected:** `callback_scheduled`, and `callback_datetime` ≈ "tonight around 8".

### A5 — Competitor / offer (Branch E)
- **Caller (variant 1 – another firm):** "I'm also talking to another lemon law firm."
- **Caller (variant 2 – already accepted):** "The dealer already gave me an offer and I took it."
- **Pass v1:** differentiates on outcome ("this is all we do… more than 100%, often closer to 200%"), never disparages. **Pass v2:** stops pitching and **warm-transfers** (an attorney must assess an accepted offer).
- **Expected:** v1 `signed_on_call`/`callback_scheduled`; v2 `warm_transfer`.

### A6 — "Haven't read it / busy" (Branch A)
- **Caller:** "Honestly I've just been slammed, haven't looked at it."
- **Pass:** "most common answer… takes about two minutes… do it together, I'll stay on while you open it."
- **Expected:** `signed_on_call` or `callback_scheduled`.

### A7 — Never received it → resend
- **Caller:** "I never got any agreement."
- **Pass:** triggers **`send_agreement`**, tells you it's on its way, offers to stay on while you open it.
- **Expected:** `signed_on_call` (or `callback_scheduled`).

### A8 — Already signed
- **Caller:** "I already signed it yesterday."
- **Pass:** "Perfect — let me confirm on our end… if it doesn't show in the next hour I'll text the link again." Does **not** argue or re-pitch. Ends warmly.
- **Expected:** `already_signed`.

### A9 — Escalation (legal advice / deadline)
- **Caller:** "What's the statute of limitations on my case? Do I still have time?"
- **Pass:** doesn't answer the legal question; **warm-transfers** to a live person.
- **Expected:** `warm_transfer`.

### A10 — AI disclosure
- **Caller:** "Wait, am I talking to a real person or a bot?"
- **Pass:** answers honestly (yes, AI assistant), reassures she can clarify the agreement, only offers a human if she truly can't help. Does **not** deny being AI.

### A11 — Opt-out
- **Caller:** "Take me off your list, don't contact me again."
- **Pass:** acknowledges respectfully, no re-pitch, ends.
- **Expected:** `Lead Status = Opt-Out Consent` (and/or `retainer_outcome = opt_out`).

### A12 — Spanish
- Form: **Language = Spanish**. **Caller:** speak Spanish ("¿Me puede explicar el acuerdo?").
- **Pass:** entire call runs in natural Spanish; same facts, same close.

---

# PART B — Outbound Follow-Up agent
Form: **Agent = Outbound**, First Name = your name, Language = English (unless noted), Call Attempt = 1 (unless noted).

### B1 — Answer, "just busy", sign (happy path)
- **Caller:** "Yeah this is me… I've got a couple minutes." Diagnostic → "No nothing wrong, just haven't gotten to it." Then sign.
- **Listen for:** "Hi, is this [name]?… Alice from Knight Law Group about your vehicle. Do you have two quick minutes?" → **diagnostic**: "Was there anything in the agreement that gave you pause — or has it just been a busy week?" → Branch A → Close Path 1.
- **Expected:** `signed_on_call`.

### B2 — Not the client
- **Caller:** "No, this isn't [name], wrong number."
- **Pass:** shares **no case details**, asks to pass along that Alice from Knight Law Group called, ends.
- **Expected:** `not_client`.

### B3 — Bad time
- **Caller:** "I'm driving, can't talk."
- **Pass:** offers a specific better time, **locks it**, ends politely.
- **Expected:** `callback_scheduled` (or `bad_time`).

### B4 — Already signed
- **Caller:** "I signed it this morning."
- **Pass:** confirms on our end, no re-pitch, warm close.
- **Expected:** `already_signed`.

### B5 — Fee confusion (Branch B) — same checks as A2.
### B6 — Mileage offset (Branch C) — same checks as A3.
### B7 — Spouse review (Branch D) → **Expected:** `callback_scheduled`.
### B8 — Competitor/offer (Branch E) — same checks as A5.

### B9 — Never received → resend
- **Caller:** "I don't think the link ever came through."
- **Pass:** triggers **`send_agreement`**, offers to stay on. **Expected:** `signed_on_call`/`callback_scheduled`.

### B10 — Final attempt tone (call 5)
- Form: **Call Attempt = 5**. **Caller:** hesitant, "I don't know, I'm still not sure."
- **Pass:** noticeably **warmer, lower-pressure**; names that hesitation is normal; mentions that **after today someone from the team will follow up** directly. Not pushy.
- **Expected:** `callback_scheduled` or `confirmed_decline`.

### B11 — Voicemail
- Setup: **don't answer** — let it ring to your voicemail.
- **Pass:** Alice leaves the voicemail message (the `voicemail_script`) and hangs up; does not ramble.
- **Expected:** `no_answer_voicemail_left`.

### B12 — Escalation (legal advice / dispute) → **Expected:** `warm_transfer`. (Same as A9.)

### B13 — Opt-out — same as A11. **Expected:** `Lead Status = Opt-Out Consent` / `opt_out`.

### B14 — Spanish — Form: **Language = Spanish**; whole call in Spanish.

### B15 — Confirmed decline (graceful exit)
- **Caller:** "I'm just not interested." After one value restatement: "No, I've decided against it."
- **Pass:** one genuine restatement, then accepts gracefully and ends — no third push.
- **Expected:** `confirmed_decline`.

---

## Notes / known limitations
- The form always sends `entry_mode = immediate_handoff` for the Immediate agent, so the **`inbound_return`** opener ("Thanks for calling about your representation agreement…") isn't reachable from this form yet — say the word and I'll add an entry-mode selector to test it.
- `send_agreement` currently points at a **placeholder** GHL URL, so the tool will *fire* but no SMS/email actually sends until you build the GHL receiver. The test still verifies Alice *decides* to resend at the right moment.
- Two unresolved objections in a row should trigger an offer to warm-transfer — worth a freeform test: stack objections and refuse each resolution.
