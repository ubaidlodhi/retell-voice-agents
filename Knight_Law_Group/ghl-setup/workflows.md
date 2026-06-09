# Workflow name: Non-Retainer Leads - Follow up English

Overview / Purpose: This workflow is set up to repeatedly follow up with non-retainer leads via SMS and email, encouraging them to book a free consultation call using your Calendly link. It loops daily until you stop or remove the contact from the workflow.

Triggers:

No trigger configured:
Currently there is no trigger defined.
This means contacts must be manually added to the workflow or enrolled from another workflow/action; it does not start automatically on its own.
Actions (in order):

SMS:

Sends an SMS to the contact immediately when they enter the workflow.
Message content:
Thanks them for speaking with you.
States you want to discuss their claim in more detail.
Shares the Calendly link:
https://calendly.com/knight-law/ca-lemon-case-evaluation
Signs off as Alice from Knight Law Group.
Includes “Reply STOP to opt out.”
Email:

Sends an email right after the SMS.
Subject: “Schedule Your Free Vehicle Case Consultation”
From name: Knight Law Group
From email: alicep@h.knightlaw.com
Body mirrors the SMS:
Thanks them for speaking with you.
Explains you want to discuss their claim in more detail.
Provides the same Calendly link.
Signs off as Alice, Knight Law Group.
Includes “Reply STOP to opt out.”
Wait 1 day:

Pauses the workflow for 1 day after the email is sent.
Go To:

After the 1‑day wait, the workflow jumps back to the first SMS step.
This creates a loop:
Day 1: SMS → Email → Wait 1 day
Day 2: SMS → Email → Wait 1 day
Day 3: SMS → Email → Wait 1 day
…and so on, repeating until the contact is removed or the workflow is changed/stopped.
How it works end-to-end:

A contact is enrolled (manually or from another process, since there is no trigger).
They immediately receive:
SMS with the Calendly link and opt-out language.
Email with the same message and link.
The workflow waits 1 day.
After 1 day, the Go To action sends the contact back to the first SMS, restarting the sequence.
This daily SMS + email follow-up loop continues indefinitely until you intervene (e.g., remove the contact, stop the workflow, or change the structure).


---

# 