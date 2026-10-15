# Next Best Action: how Alice decides when to follow up

*Knight Law Group · Next Best Action · October 2026*

## In short

When a lead needs a follow-up and **did not give us a specific time to call back**, Next Best Action picks the best time for our next **call**, **text message** and **email** to that lead.

If the lead **did** give a specific time (for example "call me tomorrow at 4"), that is a callback. We call at that exact time, and Next Best Action is not involved.

---

## Why we built it

The follow-up schedules used to run on fixed or random delays, such as "wait 4 hours, call again" or "wait a random number of minutes". Every lead was treated the same, whatever had happened on the call. In particular:

- **When a lead missed a call,** the next call often came at about the same time of day, when they were probably just as busy.
- **When a lead said something like "I'm at work" or "I need to show my wife first",** the schedule didn't take it into account.

Next Best Action replaces those delays with times chosen for each lead.

---

## When it is used

After every call where the lead goes into a follow-up schedule **without a specific callback time**:

| Follow-up | When |
|---|---|
| **Intake follow-up** | The lead hasn't finished qualifying yet |
| **Retainer follow-up** | The lead was sent the agreement but hasn't signed or declined yet |

This includes voicemails and unanswered calls, which is where a better time makes the biggest difference.

It is **not** used when the lead gives a specific callback time, signs, declines, opts out, or asks to speak to a person. Those work exactly as before.

---

## What it decides

For each lead it plans the next follow-up, always in this order:

1. **Call:** when Alice calls next.
2. **Text message:** sent after that call.
3. **Email:** sent after that text.

It also records one short sentence explaining why it chose those times. This sentence appears in the call note on the contact.

---

## How it chooses the time of the next call

**If the lead didn't pick up** (voicemail or no answer), we try **tomorrow at a different time of day**:

| The missed call was in the… | We try next… |
|---|---|
| Morning (before 12 PM) | Tomorrow, midday (12:00–2:30 PM) |
| Midday (12–5 PM) | Tomorrow, evening (5:00–7:30 PM) |
| Evening (after 5 PM) | Tomorrow, morning (9:00–11:30 AM) |

So a lead who keeps missing calls is tried across mornings, middays and evenings, not at the same hour every day.

**If the lead picked up but didn't give a time,** the assistant goes by what they said:

| What the lead said | When we call next |
|---|---|
| "Call me later" | Later the same day, 3–4 hours after the call |
| "Not a good time" / "I'm busy" | Tomorrow, at the same hour they picked up today |
| "I'm at work" | Tomorrow evening, 5:30–7:00 PM |
| "I'm driving" | Tomorrow, at the hour they picked up today |
| "I haven't read the agreement yet" | Tomorrow, at the hour they picked up today |
| "My spouse / family needs to see it" | Tomorrow evening, 6:00–7:00 PM |
| "Next week" / "in a few days" | The first weekday of that period |
| "I'm waiting on the dealer / talking to another firm" | In 3 days |
| "I'll call you back" | In 2 days |
| "I'd rather get a text or email" | In 2 days |

**We only call again on the same day if the lead asked us to call later.** Otherwise the next call is on a later day.

---

## How it chooses the text and the email

The text always comes **after** the call, and the email **after** the text. The assistant picks the exact times from how the call went. For example:

- **Normally:** the text goes about 20–45 minutes after the call and the email a little later, so the lead sees a message right after our call.
- **A lead who's at work or busy during the day** gets the text and email after 5 PM.
- **A lead reviewing the agreement with a spouse** gets them in the evening.
- **A lead who hasn't read the agreement yet** gets the text soon after the call, as a reminder.

---

## Built-in safeguards

- **Contact hours:** calls, texts and emails only go out **between 8 AM and 9 PM Pacific**, every day.
- **Do-not-contact preferences are respected:**
  - **No calls:** if a lead asked not to be called, they get no calls. Their texts and emails are spaced out: about half a day apart in the retainer follow-up, and a day apart in the intake follow-up.
  - **No texts or emails:** if a lead asked not to be texted or emailed, those messages are blocked.
- **Times stay reasonable:** never in the past, and never more than 14 days ahead.
- **If the assistant ever fails,** a safe default is used: tomorrow at a different time of day, with the text and email shortly after. Follow-up never stops because of a technical problem.
- **Leads leave follow-up automatically** when they sign, decline, opt out or qualify, exactly as before.

---

## What a lead experiences: examples

**Intake lead who doesn't answer:**

| When | What happens |
|---|---|
| Mon 10:05 AM | Alice calls. Voicemail. |
| Tue 1:10 PM | Follow-up call (midday this time). Voicemail. |
| Tue 1:40 PM | Text message |
| Tue 2:15 PM | Email |
| Wed 6:05 PM | Follow-up call (evening this time) … and so on, rotating the time of day |

**Retainer lead who picks up but is at work:**

| When | What happens |
|---|---|
| Thu 11:20 AM | Alice calls. The lead says: "I'm at work, I can't talk now." |
| Fri 6:15 PM | Follow-up call, in the evening after work |
| Fri 6:45 PM | Text reminder about the agreement |

---

## Where to see it

On each contact in GoHighLevel:

- **The call note** for every call has a **Next Best Action** line, with the planned call, text and email times and the reason.
- **The contact record** has the fields **NBA Call / SMS / Email Datetime** and **NBA Reason**, which show the latest plan.

---

## In one picture

```
Alice's call ends
      │
      ▼
Did the lead give a specific time to call back?
      │ yes ──► callback at that exact time (as before)
      │ no
      ▼
Next Best Action picks the follow-up times:
      CALL  ──►  then TEXT  ──►  then EMAIL   (between 8 AM and 9 PM Pacific)
      │
      ▼
GoHighLevel waits for each time and sends it.
After the next call, Next Best Action plans again.
```
