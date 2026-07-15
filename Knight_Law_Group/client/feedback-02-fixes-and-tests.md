# Knight Law - Feedback 02: Fixes & Test Scripts

**Agents to import:** Inbound **V20** / Outbound **V23**
**n8n post-call workflow:** `L1oNbhjnF9czixEH` (live)
**Transfer lines:** English `+1 844 482 5282` / Spanish `+1 844 539 8811` (cold, by caller language)

---

## 1. What We Fixed

### Retell agent (Inbound V20 / Outbound V23)

| # | Fix |
| --- | --- |
| 1 | **Human request handling.** Alice now overcomes the objection ONCE ("I'm an automated assistant, but I'm fully set up to take down your basic details and pre-qualify your case so I can hand you straight to a human agent"). If the caller still insists, she cold-transfers to the English/Spanish intake line by language. |
| 1b | **"Stop calling, you're an AI" is no longer an opt-out.** It now routes to the human/transfer path. Genuine "I'm not interested in my case" still opts out. |
| 3 | **User speaks first.** Alice waits for the caller to speak before greeting (no more talking into a dead line or over an answering machine). |
| 4 | **Phone confirmation removed.** Alice confirms the name (spelled back) and reads the email (not spelled) with the text/email consent question. She no longer reads back the phone number. |
| 8 | **More empathy.** The retainer close and the FAQ handler now lead with empathy on vehicle issue/defect questions ("I'm sorry you've had to deal with that. Our team will gather all the details, including any issues, defects, or experience with your vehicle"). |
| 11 | **Lease mishearing fixed.** "liz / lists / leased / leasing" is understood as *lease* on BOTH the possession question and the ownership question. A leased vehicle counts as still in possession and as owner = yes. |
| 12 | **Less robotic.** Anti-repetition rule added, and the FAQ no longer repeats "Does that help, was there anything else?" after every single answer. |
| 13 | **Spanish on request.** If the caller asks "¿Hablas español?" or speaks Spanish, Alice switches to Spanish immediately and answers in Spanish. She no longer replies "Yes, I do speak Spanish" in English. A single stray word ("aló") still does NOT flip the call. |

### n8n post-call workflow

| Fix |
| --- |
| **"It's in the shop" now counts as still in possession.** A car at a repair shop no longer turns a retainer lead into a Bad Lead. |
| **Voicemail is never an opt-out.** An answering-machine pickup is classified as **Incomplete Lead** (call back) instead of Opt-Out Consent. This was the cause of the 5 wrongly-tagged leads. |
| **AI-refusal tracking.** If the caller refuses the AI and either hangs up or gets transferred, the lead becomes **`Human Requested`** with **`AI Declined = Yes`**. If they insist but then continue and finish intake, it stays a normal lead. |
| **Email corrections** now update the contact's email. |
| **Call data passed to GHL:** Call ID, Call Recording URL, Execution ID, plus `call_log` (date, callDuration, callStatus, to_number, from_number) for the external call log. |
| **Language is decided by the whole conversation** (majority of the caller's own words), not a single word. |

### Status mapping

| GHL Status | Salesforce Status |
| --- | --- |
| Retainer Lead | HF Retainer Sent |
| Non-Retainer Lead | HF Appointment |
| Bad Lead | Bad Lead |
| Opt-Out Consent | Burnt Lead |
| Incomplete Lead | (retry, no SF push) |
| **Human Requested** (new) | **HF Appointment** + "did not communicate due to AI issue" note |

---

## 2. Still Pending

**Retell dashboard (not in the JSON):**
- **#5 Spelling clarity:** lower **voice temperature** (well under 1.0, around 0.3 to 0.5) and turn on **Read Slowly**. Do NOT enable the NATO Phonetic preset (that causes "i as in India").
- **#9 Voicemail number:** set the voicemail callback number to Alice's **+1 213 205 3651**.

**GHL:**
- Add the **`Human Requested`** status and the **`AI Declined`** field.
- On `Human Requested`: send ONE Calendly SMS, then stop the follow-up cadence.
- Cadence copy: "call Alice at **+1 213 205 3651**". Keep **310-552-2250** only on Calendly/Retainer link texts.
- Fix the 5 wrongly-tagged leads (Opt-Out to Incomplete + call back).
- Wire the external call log from `call_log`.

**Not started:** #6 FAQ Knowledge Base load, #7 SMS agent.

**On import:** re-attach the inbound Knowledge Bases (the export strips `knowledge_base_ids`).

---

## 3. Call Test Scripts

Say the **You:** lines. Check the **Expect:** behavior.

### T1. Golden path (Retainer Lead)
```
[Answer the call and stay SILENT for ~2 seconds]
Expect: Alice does NOT speak first.
You:   Hello?
Alice: (greets, asks if you're having vehicle issues)
You:   Yes, my transmission keeps failing.
You:   (CA dealership?) Yes.
You:   (still in possession?) Yes.
You:   (year/make/model?) It's a 2024 Hyundai Santa Fe.
Expect: Alice reads the year back as "twenty twenty-four", NOT "2024".
You:   (new or used?) New.
You:   (repairs at dealership?) Yes, three times.
You:   (owner / signed contract?) Yes.
Expect: Alice confirms your NAME and spells it back. Reads your EMAIL (not spelled)
        and asks text/email consent. She must NOT read back your phone number.
You:   Yes, that's right. / Yes, that's fine.
Expect: Retainer close (representation agreement by text and email).
```
**Post-call:** Lead Status = **Retainer Lead** → SF **HF Retainer Sent**

---

### T2. "It's in the shop" (was breaking retainer leads)
```
Alice: Are you still in possession of the vehicle?
You:   It's in the shop right now.
Expect: Alice continues normally, does NOT disqualify.
```
**Post-call:** `Still In Possession = Yes`. Must NOT be *Bad Lead / Not in possession of vehicle*.

---

### T3. Lease on the possession question
```
Alice: Are you still in possession of the vehicle?
You:   Yeah, I lease it.
Expect: Treated as YES (still in possession). Not disqualified.
```

### T4. Lease on the ownership question
```
Alice: Are you the owner of the car, or did you sign the sales or lease contract?
You:   I'm leasing it.
Expect: Counts as YES. Continues to contact collection (Retainer track),
        NOT Non-Retainer.
Expect: Alice does NOT read the "if you're a co-buyer, leasing..." list out loud.
```

---

### T5. Asks for human, then agrees to continue (normal flow)
```
You:   Can I talk to a real person?
Expect: Alice rebuts ONCE: "I completely understand. I'm an automated assistant,
        but I'm fully set up to take down your basic details and pre-qualify your
        case so I can hand you straight to a human agent. Can I quickly run
        through a few questions with you first?"
You:   Okay, sure, go ahead.
Expect: Alice picks up exactly where she left off. She does NOT repeat the rebuttal.
```
**Post-call:** normal status for the qualification, **`AI Declined = No`**

---

### T6. Asks for human and INSISTS (transfer)
```
You:   Can I talk to a real person?
Alice: (rebuts once)
You:   No. I want a human, now.
Expect: Alice does NOT argue. Cold-transfers to +1 844 482 5282 (English).
```
**Post-call:** Lead Status = **Human Requested**, **`AI Declined = Yes`** → SF **HF Appointment** + AI-issue note
*(Spanish caller → should transfer to +1 844 539 8811)*

---

### T7. "Stop calling, you're an AI" (must NOT be Opt-Out)
```
You:   Stop calling me, I don't want to talk to a robot.
Expect: Routes to the human path (rebuttal, then transfer if you insist).
        Alice must NOT say "I'll take you off our list".
```
**Post-call:** **Human Requested** / `AI Declined = Yes`. Must NOT be *Opt-Out Consent* or SF *Burnt Lead*.

---

### T8. Genuine opt-out (must BE Opt-Out)
```
You:   I'm not interested in pursuing this at all. Take me off your list.
Expect: Alice acknowledges respectfully and ends the call. No transfer.
```
**Post-call:** **Opt-Out Consent** → SF **Burnt Lead**

---

### T9. Spanish on request
```
Alice: (greets in English)
You:   Hola, ¿hablas español?
Expect: Alice switches to Spanish IMMEDIATELY and answers in Spanish
        ("Sí, claro, podemos continuar en español..."), then continues in Spanish.
        She must NOT say "Yes, I do speak Spanish" in English.
[Continue the rest of the call in Spanish]
```
**Post-call:** `Lead Language = Spanish`

### T10. Stray Spanish word (must NOT switch)
```
Alice: (greets in English)
You:   Aló?
[Then continue answering in English]
Expect: Alice stays in English the whole call.
```
**Post-call:** `Lead Language = English`

---

### T11. Empathy at the retainer close
```
Alice: (delivers the representation agreement explanation) Any questions about that?
You:   Yeah. Don't you want to know what happened first?
Expect: Empathetic answer, e.g. "I completely understand, and I'm sorry you've had
        to go through that. Our Client Services team will go over everything in
        detail, including the issues, defects, and your full experience with the
        vehicle, so nothing gets missed."
```

### T12. FAQ variation (not annoying)
```
You:   How much is this going to cost me?
You:   How long do these cases take?
You:   Do I keep making my car payments?
Expect: Offers "anything else?" only after the FIRST answer. After that she varies
        the check-in and does NOT repeat "Does that help, was there anything else
        you wanted to ask?" every single time.
```

---

### T13. AI disclosure
```
You:   Are you a real person?
Expect: Never claims to be human. Discloses once: "I'm an automated AI intake
        assistant for Knight Law Group..." then continues.
```

### T14. Bad lead by year
```
You:   It's a 2019 Chevy Silverado.
Expect: Alice reads it back as "twenty nineteen" and disqualifies politely.
```
**Post-call:** **Bad Lead** / reason *Vehicle year*

### T15. Voicemail (outbound)
```
[Let the outbound call go to voicemail / answering machine]
Expect: Alice does not try to qualify the machine.
```
**Post-call:** **Incomplete Lead** (call back). Must NOT be *Opt-Out Consent*.

---

## 4. Post-Call Checklist (per test call)

Check the n8n execution output / GHL payload for:
- `Lead Status` and `Bad Lead Reason` are correct for the scenario
- `Lead Language` matches the language actually spoken
- `AI Declined` is Yes only in T6 / T7
- `Still In Possession` = Yes for T2, T3
- `Is Owner` = Yes for T4
- `Full Name` / `Email Address` reflect any correction made on the call
- `Call ID`, `Call Recording`, `Execution ID` are populated
- `call_log`: date, callDuration, callStatus, to_number, from_number
