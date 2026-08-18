**Target: 2 working days · Due by Day 2**
Refer to the Master Document for brand voice, knowledge base, qualifying criteria, and escalation.

## Objective

An AI Voice Receptionist on a dedicated business number that answers every inbound call 24/7, qualifies the caller on the team's scripts, and books a confirmed appointment onto the calendar during the call, plus a voice bot on the website.

**Tools:** Retell AI, n8n, Twilio, and Google Calendar or Calendly (pending).

---

## Requirements

- Dedicated business number provisioned in Twilio, or the existing number ported (a ported number leaves the Sierra dialer).
- Voice qualification scripts for each caller type (agent, buyer, seller) drafted from the team's call recordings and signed off by the client.
- Website knowledge base available so the voice bot can answer from it.
- Booking calendar access (Google Calendar or Calendly, pending).
- Agreement that inbound calls route to the dedicated number.

---

## Action Points

1. Provision or port the dedicated business number in Twilio and route inbound calls to the agent.
2. Build the Retell AI voice agent using the master brand voice and the opening greeting.
3. Implement the qualifying flow using the shared criteria, one question at a time, with confirm-back on names, numbers, and addresses.
4. Integrate live calendar booking (provider-agnostic) so the agent offers real open slots and confirms the appointment during the call.
5. Deploy the voice bot on the website, reading from the website knowledge base.
6. Implement the after-hours / voicemail variant.
7. Wire objection handling and the escalation triggers (warm transfer to the correct direct line).
8. Add end-of-call confirmation ("You're all set...") and the clear next step.

---

## Approval Points

- [ ] Client approves the qualification scripts for agent, buyer, and seller.
- [ ] Test call passes end to end: greeting, qualify, live booking, confirm-back.
- [ ] After-hours / voicemail variant tested.
- [ ] Escalation to a human (warm transfer) works.
- [ ] Website voice bot answers from the knowledge base.
- [ ] Client point of contact signs off on Milestone 1.

---

## Voice Call Script

**Call flow:** greet + identify business, discover reason for call, qualify (one question at a time), offer booking / check calendar live, confirm details back, close with a clear next step.

**Opening greeting**

> "Thanks for calling The Santos Group at Keller Williams, this is Maria, how can I help you today?"

**Discovery and qualifying (example)**

> Caller: "Hi, I'm looking to sell my house in Pembroke Pines."
> AI: "Happy to help with that. Can I grab your name first?"
> Caller: "It's John."
> AI: "Thanks, John. And just to confirm, is the property in Broward or Miami-Dade County?"
> Caller: "Broward, in Pembroke Pines."
> AI: "Perfect, that's right in our service area. Are you looking to list soon, or more just exploring what it's worth for now?"

Continue through the remaining qualifiers, one at a time.

**Booking**

> "I can get that on the calendar right now with Julissa. I've got Thursday at 2 or Friday at 10, does either work?"
> "Great, Thursday at 2 PM with Julissa. What's the best number and email for the confirmation?"
> "You're all set, Thursday at 2 PM with The Santos Group. You'll get a text and email confirmation in a few minutes. Anything else before you go?"

**If no suitable time / caller hesitates**

> "No problem, I'll have Juan or Julissa reach out directly to find a time that works better. What's the best number to reach you?"

**After-hours / voicemail variant**

> "Thanks for calling The Santos Group. We're closed right now, but I can still get you booked in or take down your info for a callback first thing. Which would you prefer?"

**Objection handling**
| Caller says | AI response logic |
| --- | --- |
| "What's your commission?" | "That varies by property, a specialist will go over exact numbers at the consultation." Keep moving to booking. |
| "I'm just looking around / not ready." | "Totally understand, a lot of sellers start there. Want me to pencil in a no-pressure time just to see what your home's worth?" |
| "Can I talk to a real person?" | "Of course, let me get you over to the team." Trigger escalation. |
| Angry / upset caller | Acknowledge once, no debate, move straight to escalation. |
| Neighborhood demographics / "who lives there" | Redirect to objective criteria (price, size, schools); escalate if pressed. |
