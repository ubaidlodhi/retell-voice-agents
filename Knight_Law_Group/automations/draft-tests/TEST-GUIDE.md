# Draft test guide: Alice Intake v1 + Alice Retainer v4

Seven calls to your own phone cover everything that is built but not published. Each call tests several changes at once. All calls are in English.

The live number stays on the published versions throughout, so real leads are never affected.

## What is being tested

| Change (draft only) | Call |
|---|---|
| Short, natural acknowledgments and a lead-in to each question ("So, quick question —"), not a cold question; no empathy line on every turn | 1 (listen on every call) |
| She skips questions you already answered (bought it, bought it new, dealer already tried to fix it) without "confirming" them | 1 |
| FAQ mid-call: she answers, asks if there's anything else (different wording each time), then returns to her question once you say that's all | 1 |
| Fewer self-interruptions when you say "mm-hmm" while she talks (sensitivity 0.9 → 0.7) | 1 |
| New AI hand-off line before the retainer agent | 1 |
| Purchase-or-lease question is skipped when you already said "I bought it" | 1 |
| Neutral re-ask when "new or used?" gets a bare "No" (no more "So you mean it was new?") | 2 |
| CPO: explains or asks again on an unclear answer instead of disqualifying | 2 |
| Non-retainer transfer offer declined (in hours), or no offer at all (after hours) | 2 |
| Lease buyout BMW → non-retainer | 3 |
| Non-retainer live transfer (Mon–Fri 8 AM–8 PM PT) + n8n key `Non-Retainer Live Transfer = Yes` | 3 |
| Callback booked in the 3-day window: outside-hours re-ask, then a time, then a correction | 4 |
| Callback asked mid-call for next week → "our team will contact you soon" + n8n `Callback Outside Window` | 5 |
| "I'm making payments" → lease-or-loan question; Tesla arbitration line word for word; pushback answered in new words | 6 |
| Retainer "stuck" rule: offers the intake team instead of repeating itself | 7 |
| Retainer "discuss with my spouse" + follow-up time: keeps your "tonight", asks the time, waits for your answers | 7 |

## Before you start

- **Place test calls from the form or the script below, never from GHL.** GHL dials the live number, which runs the *published* agent, so none of the draft changes are heard. The 2026-10-15 test call ran on published v0 for this reason. Form: https://automations.impleko.ai/form/3e8f2b9a-b463-4bc1-bd59-03a53b3740c0 (it calls the latest created version).
- **Call 1** sends a real representation agreement to the phone and email you pass, then hands you to the retainer agent. Use your own phone and email. That hand-off lands on the *published* retainer agent (v3); the retainer draft (v4) is tested in call 7.
- **Call 3** warm-transfers to Knight Law's real English intake line. Run it Mon–Fri, 8 AM–8 PM PT, and give the intake team a heads-up. Tell whoever answers that it's a test.
- Every call needs the same two commands. The script prints a call ID; run the check with that ID once you've hung up. The check shows PASS/FAIL, the route Alice took, the n8n payload and the full transcript.

```bash
cd D:/retell-voice-agents/Knight_Law_Group/automations/draft-tests
node test_call.js call 1 --to +1XXXXXXXXXX --email you@example.com
node test_call.js check <call_id> 1
```

**Always read the transcript, not just the checks.** The main question is whether she reacts like a person to what you said.

---

## Call 1 · retainer path, listening and empathy

| Alice | You say | Listen for |
|---|---|---|
| (you pick up) | "Hello?" | |
| Greeting with the AI disclosure | "Sure." | |
| "Are you having any issues with the vehicle?" | **"Yeah, the transmission keeps slipping, and it's been at the dealer three times already."** | A short, genuine reaction to *your* problem before the next question |
| California question | **"Yes, I bought it in Los Angeles."** | She does **not** ask "purchase or lease?" and there is **no** pause: she goes straight to the next question |
| Possession | **"It's at the dealer right now, actually."** | Treated as yes |
| Year / make / model | **"2023 Ford F-150. I bought it brand new."** | Read-back, then you say "Yes" |
| New or used, dealer repairs | — | Both **skipped**: you already said "brand new" and "at the dealer three times". No "you got it new, right?" either |
| Owner question | **"Wait, how much is this going to cost me?"** | Brief answer (no bill, the manufacturer pays the fees), then "anything else?" in some form |
| | **"How long does it take?"** | Answer, then "anything else?" in **different** words than before |
| | **"No, that's all."** | She goes back to the owner question |
| Owner question | "Yes, it's my truck." | |
| Name on license; she spells it | Say **"mm-hmm"** halfway through her sentence, then "Yes" | She keeps going instead of stopping and restarting |
| Email + "okay to text and email you?" | "Yes." | |
| **"Great, we can move forward. I'll text and email you the representation agreement…"** | Listen to the retainer agent's opener, then hang up | New hand-off line, word for word |

## Call 2 · non-retainer, neutral re-ask, transfer offer declined

| Alice | You say | Listen for |
|---|---|---|
| Greeting | "Sure." | |
| Issues | **"Yes, the car keeps shutting off on the freeway."** | A reaction to how scary that is |
| California | "Yes, I bought it in Fresno." | No "purchase or lease" question |
| Possession | "Yes." | |
| Year / make / model | **"2022 Nissan Altima."** → "Yes." | |
| "Was the vehicle new or used when you got it?" | **"No."** | A neutral "Sorry, was it new or used?", **not** "So you mean it was new?" |
| Neutral re-ask | **"Used."** | |
| "Is it certified pre-owned, also known as CPO?" | **"Hmm, it came with some kind of warranty, I think."** | She explains what CPO means or asks again, and does **not** disqualify you |
| CPO again | **"Honestly, I'm not sure."** | Moves on (not disqualified) |
| Name, spelled once | "Yes." | |
| Email + "okay to text and email you?" | "Yes." | |
| **In hours:** offer to connect you with an Intake Analyst now | **"No, not right now. Just send me the link."** | Booking-link close |
| **After hours (after 8 PM PT or weekend):** no offer | — | Goes straight to the booking-link close |

## Call 3 · lease buyout BMW, live transfer (Mon–Fri 8–8 PT)

| Alice | You say | Listen for |
|---|---|---|
| Greeting | "Sure." | |
| Issues | **"The screen keeps going black while I drive."** | Reaction |
| California | "Yes." | |
| "Did you purchase the vehicle, or lease it?" | **"I leased it, then bought it out last year."** | If she asks "still leased or bought out?" → "Bought it out." |
| Possession, year / make / model | "Yes" / **"2022 BMW X5"** / "Yes" | No retainer questions (it's non-retainer) |
| Name + email consent | "Yes" / "Yes" | |
| **"Great news… One of our Intake Analysts is available right now… Would you like me to connect you now?"** | **"Yes, please."** | "Perfect, connecting you now." |
| Rings the intake line | Tell the analyst it's a test, then hang up | |

The check should show `nonret_live_transfer = attempted`, the call ending in a transfer, and in n8n `Lead Status = Non-Retainer Lead` with `Non-Retainer Live Transfer = Yes`. If nobody answers at intake, Alice should say the team is tied up and send the booking link; n8n then shows `No`.

## Call 4 · callback booked from the opening

| Alice | You say | Listen for |
|---|---|---|
| Greeting | **"I'm driving right now, can you call me back?"** | "No problem at all. What's a good day and time…?" |
| | **"Tomorrow morning, like 7."** | "We make calls between 8 AM and 9 PM Pacific. What time in that window works?" |
| | **"Okay, 5 PM then."** | "Perfect, we'll give you a call tomorrow at 5 PM. Talk to you then!" |
| | **"Actually, make it 6."** | Re-confirms **tomorrow at 6 PM** |
| | "Great, thanks, bye." | Short goodbye |

The check should show `callback_status = in_window`, and n8n should have the same `Callback Datetime Pacific` (tomorrow 06:00 PM) with `Callback Outside Window = false`.

## Call 5 · callback mid-call, outside the window

| Alice | You say | Listen for |
|---|---|---|
| Greeting | "Sure." | |
| Issues | "Yes, the brakes are making a loud grinding noise." | Reaction |
| California | "Yes." | |
| Purchase or lease (if asked) | "I bought it." | |
| Next question | **"Sorry, I can't talk right now, I'm at work. Can you call me next week?"** | "No problem. Our team will contact you soon." Then she ends the call |

n8n should show `Callback Requested = Yes`, `Callback Outside Window = true` and no callback time, so the normal cadence continues.

## Call 6 · loan, Tesla arbitration, pushback

| Alice | You say | Listen for |
|---|---|---|
| Greeting / issues / California | "Sure" / "The screen keeps turning off" / "Yes, in San Diego." | |
| "Did you purchase the vehicle, or lease it?" | **"I'm making payments on it."** | "Is that a lease, or a loan to buy it?" |
| | **"A loan."** | |
| Possession, year / make / model | "Yes" / **"2024 Tesla Model Y"** / "Yes" | |
| **"Tesla's purchase and lease agreements include a clause requiring disputes to go through arbitration…"** | **"Are you sure? There's no other way?"** | The line word for word; then a reply in **new** words, without repeating the line |
| | "Okay, thanks." | Goodbye |

n8n should show `Lead Status = Bad Lead`, `Bad Lead Reason = Requires Arbitration` and `Purchase Type = Purchased`.

## Call 7 · Retainer Outbound draft v4 · "stuck" rule and follow-up time

This call uses the retainer agent, not intake. It opens with "Hi, is this John?"

| Alice | You say | Listen for |
|---|---|---|
| "Hi, is this John?" | "Yes." | Intro and permission as separate turns |
| Intro + permission | "Sure." | |
| Her question about the agreement | **"How much money am I going to get from this?"** | Her normal answer (no guarantee) |
| | **"Yeah, but how much will I actually get?"** | She does **not** give the same answer a third time |
| | **"I need a forty thousand dollar guarantee, or I'm not signing."** | Offers **once** to connect you with the intake team |
| | **"No, that's okay. I have to discuss it with my wife first anyway."** | Respects it, offers a quick call with you both, asks **when** you two will look at it, and waits |
| | **"Tonight."** | Keeps "tonight" (never "tomorrow") and asks for a time |
| | **"Eight PM."** | "Perfect, I'll call you tonight at 8 PM…" then a spoken goodbye |

Optionally, say "Yes" to the intake offer instead. It then warm-transfers to the real intake line, so warn them first.

---

## Not covered by these calls

- **Spanish:** the drafts also have exact Spanish lines (greeting from "¿Bueno?", CPO question without "seminuevo", consent line, arbitration lines), Latin American Spanish (no "vale"), and the Spanish transfer line. Testing them needs a Spanish speaker on the team; pick up with "¿Bueno?" and Alice continues in Spanish.
- **Voicemail menus:** Alice now hangs up on mailbox-full and voicemail-menu messages instead of talking over them for minutes. This only shows on real calls, so check the first live voicemails after publishing.
- **Transfer fails:** the fallback in call 3 only shows if nobody answers at intake.
- **Callback give-up:** after three unclear answers she closes as before.
- **Lease and lease-buyout arbitration lines:** they use the same mechanism as the Tesla line in call 6.
- **Inbound draft:** it has the same changes, but the phone number stays on the published inbound agent. To try it, use a web call on the inbound agent's version 1 in the Retell dashboard.

## Meta DM bot (after you paste the new prompt into GHL)

Three short chats. Answer "yes" to the issue and California questions, and give any name, phone and email.

| Chat | Key answers | Expect |
|---|---|---|
| A | "I leased it" → still leased → Honda, still have it | The lease arbitration message, word for word |
| B | "Leased it, then bought it out" → BMW → still have it → 2022 | Not turned away; consultation link (non-retainer) |
| C | "I bought it" → still have it → 2024 → Tesla | The Tesla arbitration message, word for word |
