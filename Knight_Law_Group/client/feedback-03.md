Micol  [8:39 PM]
Hi @ubaid-impleko question on the callback requested times - You mentioned it is implemented for Alice Retainer in Spanish. We need it in English too. Also, for Alice Qualifying we will also have this.

ubaid-impleko  [8:47 PM]
Hi @Micol, we already implemented this on the English Retainer agent earlier, and later extended it to the Spanish agent as well.

We'll now apply the same logic to the Intake Alice agent, but I have a quick question:

If a lead says "call me next Monday at 5," we'll wait until that scheduled time and won't enroll them in the 4-day incomplete follow-up cadence, correct? And if the lead doesn't pick up at the requested time, we'll then move them into the incomplete cadence, right?
3 repliesMicol  [10:08 PM]
If the lead requests a callback outside the follow up timeframe, then just have her say we will contact them soon
[10:09 PM]the 3 day follow up cadence for incomplete leads (Alice Qualifying) and the 2 day follow up cadence for retainer leads (Alice Closer) shall prevail
ubaid-impleko  [10:20 PM]
Alright

Micol  [10:05 PM]
On the transcript fixes: I’m good with having the full history including date, who answered and duration of the call. Remove the overwrite across the board, I should be able to see everything

---

Micol  [10:11 PM]
I saw this today RE: callback request. This lead requested a callback for Sept. 20 at 11 AM PT, but the call went out one hour earlier (10 AM PT). Please note on the screenshot, times are AST (Attached Image #1)

---

Micol  [10:12 PM]
and she is messing up the Spanish spelling again, with the name this time

ubaid-impleko  [10:21 PM]
Let me check what else I can try
Micol  [10:22 PM]
let’s just limit the spelling. We don’t need her to spell the name several times
[10:22 PM]have her spell it once
[10:22 PM]then if user says it is not correct, have the user spell it
[10:22 PM]and stop there
[10:22 PM]we will have their name recorded either way
[10:22 PM]but of course that first time spelling should be good
ubaid-impleko  [10:24 PM]
Alright

---

Micol  [10:15 PM]
on the callback and follow up in general, what we actually need to implement is a “Next Best Action” feature, where we have another agent audit the calls and identify what is the best time to either call, text or email based on the lead’s responses
[10:15 PM]this is when the lead doesn’t state a specific time to be called back

---

Let’s also please address this ASAP (retell api deprication email)

(Attached Image #2)