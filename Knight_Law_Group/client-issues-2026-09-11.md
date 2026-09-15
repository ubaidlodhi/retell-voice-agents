# Client Issues — Verified 11 Sep 2026

Everything below was checked against the actual call recordings/transcripts in Retell, the contact records in GHL, and the n8n execution logs. **No fixes have been made yet.**

## Quick summary

| # | Client's complaint | Real issue? | One-line cause | Who fixes it |
|---|---|---|---|---|
| 1 | Lead said "no calls" but Alice kept calling | **Yes** | There is no way to record "don't call me" — only "stop everything" | n8n + GHL |
| 2 | Transcripts in GHL are cut off | **No** — nothing is cut | The transcript box only keeps the *latest* call, and the latest call is usually a missed one | n8n / GHL |
| 3 | Spanish speaker was greeted in English, hung up | **Yes** | GHL never tells Alice the lead's language, so every call opens in English | GHL |
| 4 | Spanish spelling of the email was wrong | **Yes** (it was the *name*, not the email) | The AI model garbles letter-by-letter spelling in Spanish | Us (Retell flow) |
| 5 | Many Spanish spelling issues | **Yes** | Same as #4 — 3 out of 8 Spanish spell-backs had wrong letters | Us (Retell flow) |
| 6 | Alice promised to call at 4 PM and didn't | **Yes** | The callback time was in Spanish ("hoy a las cuatro") and our time-reader only understands English | Us (n8n) |

---

## Issue 1 — Lead asked not to be called, Alice kept calling
**Lead:** (937) 469-7889 — Arun

### What actually happened
1. **2 Sep, first call.** When Alice asked "is it okay if we text and email you?", he said: **"Text and email is fine. No calls."** Alice replied "Okay, we'll stick to text and email", sent the agreement, and the call ended.
2. **2 hours later** the retainer follow-up calls started anyway. He was called 3 times over 2 days.
3. **3 Sep, third call.** He said "please take me off the waiting list." Alice said she would stop reaching out. **The calls did stop after this.**

### Why it happened
- Our system can only record two things: "okay to text/email: yes/no" and "stop ALL contact: yes/no". There is **no option for "text/email yes, phone no"**, so his request had nowhere to go. (The AI even wrote "consented to text and email, but not calls" in its summary — but there was no box to put it in.)
- When he opted out on the 3rd call, our side correctly sent **"opt out"** to GHL. GHL removed him from the follow-up calls **but did not mark the contact** — his status is still "Retainer Lead", no Do-Not-Disturb, no tag. So if anything ever re-enrolls him, nothing would stop it.

### What needs to change
- Add a "no phone calls" flag (n8n) and have GHL skip the calling steps when it's set.
- GHL's opt-out step should also set the status to Opt-Out Consent and switch on DND, as originally designed.

---

## Issue 2 — "Transcripts are cut off since this week"

### What actually happened
I compared the transcript stored in GHL against the original in Retell for 17 contacts (including one of nearly 9,000 characters). **Every one was identical — nothing is being cut.**

### What the client is really seeing
The "Transcript of the Call" box on a contact holds **only the most recent call**. Since this week, each lead gets many more calls (up to 5 retainer follow-ups + up to 5 intake retries), and most of those are missed calls or voicemails. Each one **overwrites** the box.

Examples:
- **(747) 216-8121** — the 5-minute real conversation was replaced by a blank, because the last follow-up call was a no-answer.
- **(925) 768-8970** — the box now only says "call went to voicemail" (from attempt 6 of 6).

So the client listens to the recording of the real conversation, opens the contact, and finds a blank or a one-liner from a later missed call. That reads as "cut off".

### What needs to change
- Don't overwrite the transcript when the call was a no-answer / voicemail (n8n).
- Longer term: keep one note per call instead of one box per contact (GHL).

---

## Issue 3 — Spanish speaker was answered in English
**Lead:** (925) 768-8970 — Sandra

### What actually happened
She was called 6 times. Four went to voicemail. On the other two she answered **"¿Aló? ¿Bueno?"** — Alice started her **English** introduction — and Sandra hung up within 13 seconds, both times.

### Why it happened
- Alice *can* open in Spanish — the flow has a Spanish intro that switches on when GHL tells it the lead's language.
- **GHL never sends the language.** On all 273 outbound calls since 28 Aug, GHL sent only Name, Phone and Email. So every call opens in English, and Alice only switches to Spanish once the person speaks a full Spanish sentence or asks. Sandra never got that far.
- The same thing happened on 7 calls across 5 leads in the last 10 days (one lead hung up on the English intro three separate times).

### Bonus finding — retainer follow-up calls are always in English too
The retainer follow-up calls **do** send a language — but it's **"English" on all 20 calls**, including two leads whose GHL record says Spanish. So Spanish leads have been getting English voicemails and an English "Hi, is this Juan?".

### What needs to change (all on the GHL side)
- To force Sandra to Spanish: set her Lead Language to Spanish in GHL **and** have the dialer pass that field to Alice. The flow already supports it.
- The retainer follow-up must read the contact's Lead Language field at each call instead of using "English".

---

## Issues 4 & 5 — Spanish spelling
**Lead:** (562) 246-7811 — Juan Contreras

### What actually happened
The client said "email", but on this call it was the **name**. Alice spelled "Juan Contreras" as:

> "Jota, U, A, N, espacio, **C, E, R, R, A, S**"

The letters O-N-T are missing (it should be C-O-N-T-R-E-R-A-S), and it mixes Spanish letter names with English capitals. He said "Sí" to a wrong spelling.

### How widespread is it
I checked every spell-back since 28 Aug against the name on file:

| Language | Spell-backs checked | Wrong letters | Right letters but messy format |
|---|---|---|---|
| English | 10 | **0** | 0 |
| Spanish | 8 | **3** | 4 |

The three wrong ones: "Gallegos" → "Galegos" (one L dropped); "Contreras" → "Cerras"; "Andrés" → **"A, N, E, D, E, R, E, E, S"** (nonsense).

### Why it happens
The instructions are correct — they tell Alice to use Spanish letter names ("jota, u, a, ene…") with examples. The problem is the **AI model itself cannot reliably spell a name letter-by-letter in Spanish**. In English it's perfect; in Spanish it drops and invents letters. No prompt wording will fix this.

### About emails in Spanish
- The older agent (used until 1 Sep) read the raw address "jcontreras1193@gmail.com" straight to the Spanish voice instead of saying it word by word — the voice engine pronounced it however it liked. That's probably what the client heard.
- The current agent reads it out properly, but mixes English "at" and "dot" into Spanish sentences instead of "arroba" and "punto".

### What needs to change (our side)
- Take spelling away from the AI: pre-build the Spanish spelling ("jota, u, a, ene…") automatically from the name on file, so Alice just reads it.
- Use "arroba" / "punto" for emails when speaking Spanish.

---

## Issue 6 — Alice agreed to call at 4 PM and never did
**Lead:** (747) 216-8121 — Andrés

### What actually happened
8 Sep, 8:09 AM, Spanish call. He said he was at work and asked Alice to call later. Alice offered tomorrow morning; he said **"today at four"**; Alice confirmed **"Hoy a las cuatro entonces."**

Then the standard follow-up ran as if nothing was agreed: calls at **10:10 AM, 2:10 PM**, next day **8:05 AM and 4:05 PM**, and **8:07 AM** the day after. Never at 4 PM on the 8th.

### Why it happened
Our post-call step correctly understood that he wanted a callback and wrote down his words: **"Hoy a las cuatro"**. But the part that turns those words into an actual date and time **only understands English** ("today at 4", "tomorrow morning"). It failed on the Spanish, so the callback was dropped and GHL was told to continue the normal cadence.

I tested this directly: "today at 4" → 4:00 PM ✔ · "hoy a las cuatro" → fails ✘.

### About "can we make Alice call at the time the user prefers"
- **Retainer calls:** this already exists and works — in English. It needs to understand Spanish.
- **Intake calls (first contact / incomplete leads):** there is no callback feature at all. A lead who says "call me at 4" just gets the normal retry loop. That would be new work.

### What needs to change (our side)
- Teach the time-reader Spanish ("hoy", "mañana", "a las cuatro", "en la tarde", etc.) — small n8n change.
- Optionally add the same callback feature to the intake agent.

---

## Suggested order
1. **Issue 6** — Spanish callback times (n8n, small, fully on our side).
2. **Issue 2** — stop overwriting transcripts with blank/missed calls (n8n, small).
3. **Issue 1** — "no calls" flag (n8n) + GHL opt-out step marking the contact (client's GHL).
4. **Issue 3** — GHL to send Lead Language on every dial (client's GHL).
5. **Issues 4/5** — pre-computed Spanish spelling in the flow (our side, needs a test call).

---
---

# Batch 2 — reported by Micol, verified 12 Sep 2026

| # | Client's complaint | Real issue? | One-line cause | Who fixes it |
|---|---|---|---|---|
| 7 | Alice disqualified a lead who said "No, I leased it" as out-of-state | **Yes** | Two-part question ("did you buy *or lease*… in California?") + a garbled transcription of "No, arrendé" → Alice took the "No" as "not California" and disqualified with no double-check | Us (Retell flow) |
| 8 | Alice changed the email on the call and the email failed | **No** — Alice didn't change anything | The email on file was wrong from the start (`yuan…` instead of `juan…`); Gmail bounced it; a person corrected it in GHL the next day | Data / GHL |
| 9 | Can only see the first call's transcript, not follow-ups | **Yes** (same root cause as Issue 2) | The follow-up transcript box is overwritten by every later call, and the latest is nearly always a voicemail | Us (n8n) + GHL |
| 9b | Wants a tag every time someone actually talks to Alice Retainer | Feature request — easy | We already send "answered by: Human" on every retainer call; GHL just needs to add a tag on it | GHL (or us) |

---

## Issue 7 — Lead disqualified as "out of state" after saying he leased
**Lead:** (626) 678-7761 — Humberto

### What actually happened
Spanish call, 10 Sep. Alice asked *"¿Compró o arrendó el vehículo en un concesionario de California?"* ("Did you buy or lease the vehicle from a California dealership?"). He answered **"No, arrendé"** — meaning *"No [I didn't buy it], I leased it."*

The speech-to-text heard it as **"No, Rendée"**. Alice saw a "No" and immediately said sorry, we can't help, your vehicle was from out of state. He hung up. Our post-call marked him **Bad Lead – out of state**. (Someone has since manually reset him to Incomplete Lead in GHL on 11 Sep, so he will be re-called.)

### Why it happened
1. **The question asks two things at once** — *buy or lease?* and *in California?* — so a "No" is ambiguous. A lot of people answer the first half.
2. **The transcription was garbled** ("Rendée"), so the model only had a clear "No" to go on.
3. **There is no double-check before disqualifying.** The rule is simply "caller says it was NOT purchased or leased in California → disqualify". One misheard word ends the case, and it is an expensive mistake — a real lead lost.

### What needs to change (our side)
- Before disqualifying on this question, Alice should confirm in one sentence: *"Just to be sure — the vehicle was bought or leased **outside** California?"* and only disqualify on a clear yes.
- Optionally split the question: "Did you get it from a dealership in California?" then "Did you buy or lease?" — "lease vs buy" is already asked later anyway.

---

## Issue 8 — "Alice changed the email and the email failed"
**Lead:** (559) 660-3952 — Juan Rodríguez

### What actually happened
- The email on file when the call started was **`yuanrodriuguez5369@gmail.com`** (that's what the lead form / GHL had). Alice read it back exactly as written — "yuanrodriuguez5369 at gmail dot com" — and he said "Sí".
- Alice sent the agreement to that exact address. **Gmail rejected it: "5.1.1 The email account that you tried to reach does not exist."** (visible on the email in GHL, status = failed). The SMS with the same link **was delivered**.
- Later in the call he said an email had been deleted by accident — Alice re-sent to the same (bad) address.
- The next day (7 Sep, between 8 AM and 4 PM PT) the email on the contact was changed to **`juanrodriuguez5369@gmail.com`**. **No automation did this** — I checked every n8n run in that window; none touched this contact. It was edited by a person in GHL.

### So, is it an issue?
- Alice did **not** change the email — she used what was on file. The address was wrong before she ever called.
- Two things worth noting:
  1. **The corrected address still looks wrong** — "rodri**u**guez" has an extra "u". It may bounce again. Worth checking with the lead.
  2. **Nothing reacts to a bounced email.** The agreement email failed within 2 seconds and no one was alerted, no SMS asked him to confirm his address. The only reason he still got the link is the text message.
- By design Alice reads the email back but does not spell it letter by letter (spelling emails aloud goes badly, especially in Spanish). That means a typo in the lead form will not be caught on the call.

### What could change
- GHL: when an agreement email bounces, send an SMS asking the lead to reply with their correct email, and/or notify the team.
- Optional: have Alice confirm the part before the "@" more carefully when the lead's language is Spanish.

---

## Issue 9 — "I can only see the initial call transcript, not follow-ups"

### What actually happened
This is the same problem as Issue 2, seen from the other side. Each contact has **two** transcript boxes:
- **Transcript of the Call** — the intake call (there's usually only one, so it looks fine).
- **Transcript of Retainer Agent Call** — the follow-up calls. This one is **overwritten on every follow-up call, including no-answers and voicemails**.

For Juan Rodríguez: he had two real follow-up conversations (2 min 43 s on 6 Sep, 4 min 40 s on 7 Sep). Both are gone from the box — it now holds a 42-second voicemail from 8 Sep. So Micol sees the intake transcript and a voicemail, and nothing in between.

### What needs to change
- **Stop overwriting the box with voicemails / no-answers** (n8n — small change).
- **Better: save every call as a Note on the contact** — "Alice Retainer, call 2 of 5, 6 Sep 12:41 PM, spoke to Juan, 2 min 43 s" + the transcript. Notes stack up as a timeline, so nothing is ever lost and auditing is a scroll, not a guess. This is a bigger help than tags.

## Issue 9b — Tag every time someone talks to Alice Retainer
Easy. Every retainer post-call already tells GHL **who answered** (`Human` / `Voicemail` / `Automated system` / `No answer`). GHL's router just needs one step: *if answered by Human → add tag* (for example `alice retainer: spoke`). If the client wants it per attempt, the payload also carries the attempt number (1–5), so tags like `retainer call 2: spoke` are possible.

Note a tag can only be "on" or "off" — it can't show *how many* times someone spoke to Alice. The per-call Notes above give the full history; the tag is the quick filter.
