# Feedback-01 — Implementation Plan

> Source: [feedback-01.md](feedback-01.md) (client, inbound Alice) + Stephen's answers (2026-06-20).
> Scope: changes span **3 systems** — Inbound Alice, Outbound Alice, and the Meta DM chatbot.
> Status: **BUILT 2026-06-20** — inbound V09, outbound V12, n8n post-call, Meta DM (extraction + chatbot), and docs updated & validated. Remaining: re-import both agents + dashboard wiring (see end). On-hold item (non-retainer dropped-call → Calendly) untouched.

---

## Locked decisions (from client answers)

1. **Driver's-license name confirmation** — replace the seeded name read-back with this exact flow:
   - Alice: *"I've got your name as **{{Name}}** — is that the same name as it appears on your driver's license?"*
   - **If YES** → spell it back letter-by-letter to confirm: *"Okay, let me repeat that to confirm: J — O — H — N, D — O — E."*
   - **If NO** → *"Please spell out your name for me,"* capture it, then **spell it back to reconfirm**.
   - Plain letters (NOT NATO phonetic). Phone + email + consent stay as the batched read-back.

2. **Returning-lead routing** — three GHL statuses get transferred, routed **by language**:
   - `HF Retainer Sent`, `HF Appointment Booked`, **`Bad Lead`** → transfer.
   - English → **+1 844 482 5282** · Spanish → **+1 844 539 8811**.

3. **Transfer style** — **COLD** transfer. **Do NOT check business hours** (always transfer). **Do NOT** offer the consultation/booking link on these paths.

4. **"Representation Agreement"** — change **caller-facing wording only**. Internal lead-status names, GHL fields, classification, dedup tags all stay exactly as they are.
   - Offer: *"We can proceed with your case. I'll send you the representation agreement to sign via text and email."*
   - Next steps: *"Once you sign the representation agreement, we can begin working on your case. You'll be contacted by someone from our Client Services team who will walk you through the next steps and help you get us all the documents we need to move your case forward. Once those documents are received, your case will move into preparation for filing. If anything is still missing, our team will let you know exactly what's needed to avoid delays. The sooner we receive the required documents, the sooner your case can be filed."*

5. **Year criteria** — **2020 or older = Bad Lead.** Only **2021 and newer** qualify. (Was `≤ 2019` in voice, `≤ 2016` in Meta DM — both move to `≤ 2020`.)

6. **Greet in the caller's known language** — open in seeded `lead_language` (Spanish/English) instead of defaulting to English; still switch if the caller uses the other language.

### On hold (not this round)
- **Non-Retainer dropped-call → Calendly link** (feedback bullet 6) — client confirmed **2026-06-20: leave as is**. No change needed: the current design already sends the Calendly link via the seeded contact details + the GHL non-retainer drip, even when the call drops before the contact step. **Closed.**
- **DocuSign** — Knight's team configures it; HeroFlow connects via Zapier. Dependency, no action.

---

## Open questions — ALL RESOLVED (2026-06-20)

- **Q1:** `lead_status` is the standard 5 (Retainer / Non-Retainer / Bad / Incomplete / Opt-Out). Returning **Retainer Lead / Non-Retainer Lead / Bad Lead** → cold transfer by language; **Incomplete** → resume intake; **Opt-Out** → opt-out node.
- **Q2:** DL-confirmed name overwrites the **same Name field** (n8n: AI extracts `full_name`, Build Payload prefers it over seeded).
- **Q3:** Human/cold transfer is **inbound only** — outbound keeps its link path.
- **Q4:** Meta DM chatbot prompt = `agents/meta-dm/meta-dm-chatbot.md`; it already asks for the DL name, so only year + representation wording changed.

_Original questions (for the record):_

| # | Question | Blocks |
|---|---|---|
| Q1 | Full set of GHL `lead_status` values the pre-call sends. We know `HF Retainer Sent`, `HF Appointment Booked`, `Bad Lead`, `Incomplete Lead`. What about returning `Retainer Lead` / `Non-Retainer Lead` (interim) and `Opt-Out`? Do interim retainer/non-retainer also cold-transfer, or resume/intake? | Inbound router (#6) |
| Q2 | Where should the **DL-confirmed legal name** be written in GHL (so the representation agreement uses the correct name)? New field, or overwrite Name? | DL-name downstream (#15) |
| Q3 | Outbound: should its "human request" path **also** cold-transfer to the two language numbers, or keep sending the link? (Feedback was inbound-focused.) | Outbound transfer scope |
| Q4 | Where does the **Meta DM conversational chatbot** script live (the bot that talks to users)? The n8n workflow I audited is only post-chat extraction — the "representation agreement" wording must change in the chatbot itself. | Meta DM #14 |

---

## Work by system

### A. Inbound Alice (`inbound-conversation-flow-agent.json`, → V09)
- **A1. Year cutoff** → `year <= 2020` in `Classify Lead (deterministic)`; disqualify-year node text "model year **2021** and newer."
- **A2. Representation-agreement wording** → `Retainer: Process` + `End: Retainer` + the offer line (internal statuses unchanged).
- **A3. DL-name confirm flow** → rebuild the name portion of `Retainer: Contact Collection` and `Non-Retainer: Confirm`: ask "same as driver's license?" → spell-back on yes / re-spell + reconfirm on no. Add a `confirmed_name` extract var so a corrected legal name is captured. Update global-prompt **Verification** (name IS now spelled letter-by-letter; email still not). Keep NATO preset OFF.
- **A4. Cold transfer by language** → router: `HF Retainer Sent` / `HF Appointment Booked` / `Bad Lead` → language branch (`lead_language == Spanish` → +1 844 539 8811, else +1 844 482 5282) → **cold** transfer with line *"Please hold for just a moment while I transfer your call to one of our specialists."* Remove the Business-Hours Gate + Book-Callback from these paths; no consultation. Retire the old warm-transfer to (310) 552-2250 for these.
- **A5. Language-aware open** → greet/resume in seeded `lead_language`; update global prompt "Start in English" rule.

### B. Outbound Alice (`conversation-flow-agent.json`, → V12)
- **B1. Year cutoff** → same `≤ 2020` change in its `Classify Lead`.
- **B2. Representation-agreement wording** → same nodes.
- **B3. DL-name confirm flow** → same as A3.
- **B4. Language-aware open** → open in seeded `lead_language` (we know it from the inquiry).
- **B5. (pending Q3)** human-request transfer destination.

### C. n8n post-call (`L1oNbhjnF9czixEH`)
- **C1. Year cutoff** → `if (year <= 2020)` in the `Classify Lead` code (serves both directions).
- **C2. (pending Q2)** prefer the DL-confirmed name when forwarding, and map it to the agreed GHL field in `Build Payload`.

### D. Meta DM
- **D1. Extraction workflow (`iWFOdD0JCO8Id0pg`)** → bad-lead rule #4: `≤ 2016` → **`≤ 2020`** (also fixes the pre-existing drift from the voice agents).
- **D2. Conversational chatbot (pending Q4)** → representation-agreement wording; confirm its year logic matches `≤ 2020`. (DL-name and transfer likely N/A for chat — confirm.)

### E. Docs
- **E1.** Update [lead-classification-flows.md](../automations/lead-classification-flows.md): year cutoff (2021+ qualifies) + a note that "retainer agreement" is spoken as "representation agreement."

---

## Notes / risks
- **A3 changes data, not just wording.** Capturing a corrected DL name means a new dynamic variable and a downstream field (Q2). Phone/email stay seeded.
- **A4 depends on Q1.** The router keys on the exact GHL `lead_status` strings; we need the full taxonomy to avoid an unhandled status falling through to fresh intake.
- **"Representation agreement" is wording-only** (decision 4) — do not rename `Retainer Lead` / `Non-Retainer Lead` or any GHL field/tag.
- Each agent change ends with `validate_flow.py` + a V## version bump before delivery.
