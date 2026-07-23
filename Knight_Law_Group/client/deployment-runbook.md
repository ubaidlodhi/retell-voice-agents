# Feedback-03 Runbook (your side)

Covers **only the feedback-03 fixes**. The n8n post-call workflow (`L1oNbhjnF9czixEH`) is already updated and live — nothing to do there.

**Agents to import:** Inbound **V21**, Outbound **V24**
**Transfer lines:** EN `+1 844 482 5282` / ES `+1 844 539 8811`

---

## PHASE 1 — Retell

### 1.1 Import
- [ ] Import **Inbound V21** and **Outbound V24**.
- [ ] **Re-attach the Knowledge Base(s)** on the inbound agent (the export strips KB IDs).

### 1.2 Verify the new warm transfer (feedback-03 #1)
- [ ] Open **Warm Transfer: Intake (English)** and **(Spanish)** — confirm each shows **Warm transfer**, the right number, and the **whisper / private handoff message**. If the whisper looks empty or malformed, re-enter it in the UI (the dashboard is authoritative for that field).
- [ ] Confirm the **returning-lead transfer is still Cold** (I deliberately left it untouched).

### 1.3 Voice settings — fixes spelling (#2 Spanish spelling, #4 fast/looping spell-back)

Agent → **Voice** section:

| Setting | Range | Set to |
| --- | --- | --- |
| **Voice Temperature** | 0 – 2 | **0.3 – 0.5** (main lever: lower = more stable, stops letters drifting/blending/dropping) |
| **Voice Speed** | 0.5 – 2 | **0.95** — only if spelling is still rushed after the temperature change |

- [ ] Lower **Voice Temperature** first, **on its own**, and re-test spelling.
- [ ] Only then touch **Voice Speed** — it is global and slows the whole conversation, not just spell-outs.
- [ ] Leave **dynamic voice speed adjustment** OFF while tuning.
- [ ] Do **NOT** enable NATO Phonetic (that's the "i as in India" behavior you rejected).

> There is **no "Read Slowly" toggle** in Retell. English letter-pausing comes from the hyphenated spelling format (`j-o-h-n`), which the agent prompt already uses; Spanish uses comma-separated letter names. So the prompt side is done — temperature is the missing piece.

### 1.4 Turn-taking — fixes interrupting (#2.1)
- [ ] Raise the end-of-turn silence threshold / lower responsiveness so Alice waits for the caller to finish. Matters most for Spanish callers, who pause longer mid-sentence.

> These voice/turn-taking settings do most of the work for #2, #2.1 and #4 — the prompt changes alone won't fix TTS pacing. Re-test spelling **after** applying them.

---

## PHASE 2 — GoHighLevel

- [ ] Add the new Lead Status **`No Contact Consent`** → maps to Salesforce **`HF Appointment`** (manual outreach).
- [ ] Map the new **`Contact Consent`** field (`Yes` / `No` / `N/A`) from the webhook payload.
- [ ] Add a guard so SMS/email are **NOT** sent when **`Contact Consent = No`**.
- [ ] Route `No Contact Consent` to a **phone call-back task** (these leads still want to pursue their case — they just won't accept text/email).

That closes the original complaint (docs sent to someone who said no). The agent now also re-confirms consent and warm-transfers anyone who still declines.

> **Do not** treat `No Contact Consent` like `Opt-Out Consent`. Opt-Out = doesn't want to pursue (Burnt Lead). This one = still wants help, just not by text/email.

---

## PHASE 3 — Test

- [ ] **Consent "No"** → Alice re-confirms ("text and email are the official channels we use to send the documents to sign…"). Say No again → **warm transfer** to the correct language line. Confirm GHL sends **no** SMS/email.
- [ ] **Consent "No" then Yes** → Alice continues normally to the close.
- [ ] **CPO unsure** (#2.2) → answer *"I don't know"* or *"the dealer offered gap insurance"* → lead lands as **Non-Retainer**, NOT Retainer.
- [ ] **Past issues** (#3) → say *"not right now"*, then *"it had problems before"* → Alice asks about past problems and **continues qualifying** (not Bad Lead).
- [ ] **Spelling** (#2/#4, after 1.3) → Spanish name spelled with **Spanish letter names only**, slow on every attempt, and the correction loop **stops after 3 tries** instead of going forever.
- [ ] **Interrupting** (#2.1) → give a slow, pause-heavy answer and confirm Alice doesn't cut in.

---

## Notes
- Don't re-run old n8n executions to correct a lead — it re-POSTs to GHL. Fix those records manually.
- `AI Declined` has been **removed** from the payload — `Human Requested` status is the single signal.
