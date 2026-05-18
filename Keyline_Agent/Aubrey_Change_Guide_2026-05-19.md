# Aubrey — Change Guide

Two changes from your recent feedback. The first one we already applied on the backend (n8n side); the second is a quick Retell edit you can make yourselves.

---

## Change 1 — Ticket SMS: footer removed + flow simplified ✅ done on backend

**What you asked for:** remove the trailing *"Keyline Home Care | 1-855-453-9546"* footer from the ticket-confirmation text message.

**What we did:**
1. **Removed the footer** from the ticket confirmation SMS. New body:
   > Hi! Your Keyline Home Care request has been submitted.
   >
   > Ticket Number: 12039261736
   >
   > Our team will follow up within 1-2 business days.
2. **Removed the footer from the app-link SMS too** (same footer was on it — kept them consistent).
3. **Moved the ticket SMS into the create-ticket workflow.** Previously, Aubrey called two separate tools per ticket — one to create it in Monday, then a second to send the SMS. Now the SMS fires automatically the moment the ticket is created. One operation, can't get out of sync, faster turn.

**What this means for you:**
- Nothing changes about how callers experience the call — Aubrey still says *"Your ticket number is…"* and the SMS still arrives.
- The system is just more reliable: if a ticket is created, the SMS is guaranteed to follow.
- The Monday board entry and the SMS both arrive on every ticket — same as before.

**If you ever want to edit the SMS text yourself in the future**, here's where:
- Open n8n → **`Aubrey - Create Ticket`** workflow → the **`Send Ticket Confirmation SMS`** node (the Twilio one branching off `Create Ticket in Monday.com`).
- The `Message` field is the full SMS body. Edit, save.
- (The standalone `aubrey-send-sms` workflow is still there for app-link / travel-link / prospect-link messages — those are separate.)

---

## Change 2 — Ask the caller the purpose of their trip on travel requests

**What you want:** add one more question to the travel intake — *"What's the purpose of the trip?"* (e.g., personal travel, family event, medical, work).

**Where:** Retell → Aubrey agent → flow editor → node named **`TRAVEL REQUEST`**.
(Ctrl+F in the canvas to jump straight to it.)

**Steps:**
1. Open the Aubrey agent in Retell → click the **`TRAVEL REQUEST`** node.
2. Open the **Prompt** tab.
3. Find the list of fields the prompt tells Aubrey to collect (it's a numbered or bulleted list — *"ask for name, then dates, then destination…"*).
4. Add one more bullet to that list:
   > Purpose of the trip — ask briefly: *"And what's the purpose of your trip — personal, family, medical, or something work-related?"*
5. Make sure the surrounding instructions still say **one question per turn** (so Aubrey doesn't pile questions together).
6. Click **Save** in the top right.

**Test it (before publishing):**
1. Click **Test Call** in the top right.
2. Trigger the travel flow: say *"I need to request travel"* → caregiver → state → walk through the fields.
3. Confirm Aubrey asks the purpose question naturally in sequence, not crammed in with another field.
4. After the call, check the Monday.com ticket's **Call Summary** column — the purpose should appear in the summary text (no Monday schema change needed; the summary is generated automatically from what Aubrey collected).

**When it looks good:** click **Publish** in the top right and route your real number to the new version.

**Heads up:** you do **not** need to change anything in n8n, Monday columns, or the tool schema for this. The purpose flows through automatically inside the `call_summary` that the create-ticket workflow already writes.

---

## Reminder — the safe change workflow

Any Retell edit (like Change 2) should ride the same workflow we covered in the training:

1. Duplicate the agent.
2. Make the change on the duplicate.
3. Web Test → Test Number → review a few real test calls.
4. Apply to production. Publish. Forward the live number to the updated version.

If anything looks off mid-test, **don't publish** — save the draft and ping us with a screenshot of where it broke.
