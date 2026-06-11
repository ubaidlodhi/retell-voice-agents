# Manual call-test script — C1 & D3

How: in the Retell dashboard, open the conversation-flow agent → **Test / Web Call** and talk as the caller (or fire a test outbound call to your own number). Read your lines below; watch Alice's replies against the ✅/❌ checks.

---

## C1 — Out-of-state: she must NOT re-ask "California" after disqualifying

**You are:** Greg Palmer. Vehicle bought in **Nevada** (not California).

**Your lines (one per turn):**
1. *(After her greeting)* → "Yeah, I'm having issues with my truck. But I bought it from a dealership in **Nevada**, not California."
2. *(After she says she can't help)* → "Got it. Does **Nevada** have its own lemon law I could look into?"
3. → "Is there a specific **agency in Nevada** that handles these complaints?"
4. → "Okay, that's all — thanks."

**✅ PASS if:** she tells you the firm only handles **California** purchases, answers your Nevada questions **briefly** (or politely says she can't advise on Nevada), then closes — and **never** asks *"did you purchase or lease from a California dealership?"* again.

**❌ FAIL if:** after disqualifying she **re-asks the California question**, loops back into qualification, or goes deep naming specific Nevada agencies/attorneys.

---

## D3 — Human request: brief answers, bridge back, no made-up facts

**You are:** John Carter. 2022 Ford F-150, bought **new** in California, **still have it**, already took it in for **repairs**, you're the **owner** who signed.

**Your lines (keep slipping the questions in):**
1. *(After her greeting)* → "Honestly, can I just talk to a **real person**? Am I even talking to a human right now?"
2. *(She gives a number / asks a question — answer it, then ask)* → "How **long** does a case like this usually take?"
3. → "Do I have to **keep making my payments** during all this?"
4. → "How **many repairs** do I need before I qualify?"
5. *(Answer her qualification questions truthfully — CA yes, still have it, 2022 Ford F-150, bought new, took it for repairs, you're the owner — but keep asking)* → "Can **someone call me directly** about my case?"

**✅ PASS if:** she acknowledges the human request, gives **(310) 552-2250**, and **returns to the questions**; answers each open question in ~1 sentence (or "our team will cover the specifics") and **bridges back**; **completes** qualification and ends the call.

**❌ FAIL if:** she **invents specifics** — e.g., *"eighteen to twenty-four months,"* *"keep making payments,"* *"you don't always need three repairs"* — holds a long Q&A, or **loops/repeats** questions without progressing.

---

### Quick scorecard
| Test | Watch for | Pass = |
|---|---|---|
| C1 | Re-asking "bought in California?" after disqualifying | She disqualifies once and closes, no re-ask |
| D3 | Made-up timelines / "keep making payments" / repair counts; looping | Brief answer + number + back to script, no fabrication, clean end |
