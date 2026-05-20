# Aubrey — Change Guide

Two changes from your recent feedback. Each one tells you exactly where to click and what to change.

---

## Change 1 — Remove the phone-number footer from the ticket SMS

**You want:** the trailing *"Keyline Home Care | 1-855-453-9546"* line removed from the ticket-confirmation text message that callers receive after a ticket is created.

**Where:** n8n → the **Aubrey - Create Ticket** workflow → the **Send Ticket Confirmation SMS** node.

### Steps

1. Open n8n → Workflows → **Aubrey - Create Ticket**.
2. On the canvas, find the node called **Send Ticket Confirmation SMS** (it's the Twilio node that branches off `Create Ticket in Monday.com`). Click it to open.
3. Look at the **Message** field — it contains the full SMS body. It currently reads:
   ```
   Hi! Your Keyline Home Care request has been submitted.

   Ticket Number: {{ $('Create Ticket in Monday.com').item.json.id }}

   Our team will follow up within 1-2 business days.

   Keyline Home Care | 1-855-453-9546
   ```
4. Delete the last line (the phone-number footer) along with the blank line above it. The Message field should now end at *"Our team will follow up within 1-2 business days."*
5. Click **Save** in the top right of the workflow.

### Test it

1. From Retell, place a Test Call and walk through a flow that creates a ticket — e.g., *"I forgot to clock out yesterday."*
2. Confirm the SMS arrives on the caller's phone **without** the footer.
3. Open the matching ticket in Monday.com to confirm everything else still looks right.

---

## Change 2 — Ask the caller the purpose of their trip on travel requests

**You want:** Aubrey to ask one more question during travel intakes — the **purpose of the trip** (personal, family event, medical, work, etc.).

**Where:** Retell → Aubrey agent → flow editor → node called **`TRAVEL REQUEST`**.

### Steps

1. Open the Aubrey agent in Retell → flow editor.
2. Press **Ctrl+F** and search for **`TRAVEL REQUEST`** — click that node when it appears.
3. Open the **Prompt** tab.
4. Find the list of fields the prompt tells Aubrey to collect (name, dates, destination, etc.). Add one more item to the list:
   > **Purpose of the trip** — ask briefly: *"And what's the purpose of your trip — personal, family, medical, or something work-related?"*
5. Make sure the surrounding instructions still say **one question per turn** so Aubrey doesn't stack questions together.
6. Click **Save** in the top right.

### Test it

1. Click **Test Call** in the top right.
2. Trigger the travel flow — say *"I need to request travel"* → caregiver → state → walk through the questions.
3. Confirm Aubrey asks about the purpose naturally in sequence (not crammed in with another field).
4. After the call ends, open the matching ticket in Monday.com and check the **Call Summary** column — the purpose should appear in the summary text.

**No Monday.com schema changes needed.** The Call Summary is generated automatically from what Aubrey collected, so the new field flows through on its own.

### When it looks good

Click **Publish** in the top right, then forward your real number to the updated version.

---

## Reminder — the safe change workflow

Any change should ride the same workflow we covered in the training:

1. **Duplicate** the agent (or, for n8n, duplicate the workflow)
2. **Web Test** the change
3. **Publish to a test number** and call it like a real caller
4. **Review the first 10–20 real calls** routed to the test number
5. **Apply to production** and forward the main line

If anything looks off mid-test, **don't publish** — save the draft and ping us with a screenshot of where it broke.

---

Any questions or hiccups, send a note our way. Thanks!
