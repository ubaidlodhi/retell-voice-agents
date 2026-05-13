

**STANDARD OPERATING PROCEDURE**

**Keyline Aubrey AI Agent**

**Complete System Documentation & Guide**

Prepared by Impleko  |  May 2026  |  Confidential

# **Table of Contents**

1\. System Overview

2\. Retell AI Agent Setup

3\. Conversational Flow Walkthrough

4\. How to Edit Prompts & Nodes

5\. Sample Changes — "If I Want To Do X, Do Y"

6\. Testing Before Publishing

7\. Retell Tool Calls

8\. n8n Workflows & Architecture

9\. Monday.com Integration

10\. Call Transfer Directory

11\. Troubleshooting & Common Issues

# **1\. System Overview**

Aubrey is your AI phone agent. When someone calls Keyline's main line (770-882-8015), Aubrey answers, figures out what the caller needs, collects the right information, creates a ticket so your team can follow up, and sends a text message to the caller with their ticket number.

## **What Each System Does**

| System | What It Does | Where To Access It |
| :---- | :---- | :---- |
| Retell AI | This is Aubrey herself. She answers calls, talks to people, and follows the script you set up. | retellai.com |
| n8n | The behind-the-scenes helper. Looks up callers, creates tickets, sends texts. | keyline.app.n8n.cloud |
| Monday.com | Where all tickets are stored. Your team reviews and updates them here. | monday.com |
| Twilio | The text messaging service. Sends app links and ticket confirmations. | twilio.com |
| Aircall | Your phone system. Main line forwards calls to Aubrey. | aircall.io |

## **What Happens When Someone Calls**

**1\.** The call comes in on your main line (770-882-8015)

**2\.** Aubrey silently checks if she knows this caller by looking up their phone number

**3\.** If she recognizes them, she says "Hi \[Name\], welcome back\!"

**4\.** If she doesn't recognize them, she asks "Are you a caregiver, client, case manager, or another party?"

**5\.** She figures out what they need and asks the right questions, one at a time

**6\.** When she has all the information, she creates a ticket on Monday.com

**7\.** She sends a text message with the ticket number to the caller's phone

**8\.** She reads the ticket number out loud so the caller can write it down

**9\.** She asks if there's anything else, then says goodbye and ends the call

# **2\. Retell AI Agent Setup**

Retell AI is where Aubrey lives. This is where you control how she sounds, what she says, and how she behaves on calls. Think of it as Aubrey's brain.

## **2.1 Changing Aubrey's Voice**

![][image1]

Right now, Aubrey uses a voice called Dakota (Engaging and Steady). If you want to change how she sounds:

**1\.** Open your agent in Retell and click Global Settings on the right side

**2\.** Look for Voice & Language near the top

**3\.** Click the dropdown to see all available voices

**4\.** Click the play button next to any voice to hear a preview

**5\.** Pick the one you like

**6\.** Click the Publish button in the top right corner

*Tip: You MUST click Publish for any change to take effect. If you don't publish, nothing changes.*

## **2.2 The Global Prompt (Agent Handbook)**

The global prompt is like Aubrey's rulebook. It tells her how to behave on every single call.

| Rule Category | What It Means | Example |
| :---- | :---- | :---- |
| Tone Rules | How Aubrey talks | Keep sentences short. Never more than 2 at a time. |
| Banned Words | Things she must never say | Never say 'Absolutely\!', 'Certainly\!', or 'Perfect\!' |
| Caller Memory | What she does with known callers | If we have their name on file, confirm instead of asking again |
| Spelling Back | How she confirms important info | Spell emails letter by letter. Read phone numbers digit by digit. |
| Off-Topic Handling | What to do with unrelated questions | Answer briefly, then go back to what you were collecting |
| Before Transfers | What to do before connecting to someone | Always confirm the issue first to avoid misrouting |

**1\.** Click Global Settings on the right side of the flow editor

**2\.** Click Agent Handbook to open the text box

**3\.** Make your changes (the rules are written in plain English)

**4\.** Click Publish to save and apply

*Tip: Changes to the global prompt affect EVERY call. Always test after editing.*

## **2.3 How Fast Aubrey Responds**

![][image2]

| Setting | Current Value | What It Means |
| :---- | :---- | :---- |
| Response Eagerness | 0.63 | How quickly Aubrey starts talking after the caller stops. Lower to 0.5 if she talks over callers. |
| Interruption Sensitivity | 1.0 | How easily Aubrey stops when the caller speaks. Lower to 0.5 if she stops mid-sentence too often. |
| Background Sound | None | Whether Aubrey has office noise. Keep on None for clarity. |

To change: Global Settings \> scroll to Speech Settings \> drag sliders \> click Publish.

# **3\. Conversational Flow Walkthrough**

The conversational flow is Aubrey's script. It's made up of 47 boxes (called "nodes") connected to each other. Each box tells Aubrey what to say or do. The connections (called "edges") tell her when to move to the next step.

![][image3]

## **Node Groups**

| Group | What It Does | Nodes In This Group |
| :---- | :---- | :---- |
| 1\. Entry | Where every call starts. | OPENING, END CALL |
| 2\. Routing | Figures out where to send the caller. | TOPIC MENU, CASE MANAGER, TEAM MEMBER REQUEST, OUT OF SCOPE |
| 3\. App Offers | Asks if caller wants a text with the app link. | APP OFFER for INCIDENT, PAY STUBS, TRAVEL |
| 4\. Intake | Collects information one question at a time. | MISSED CLOCK OUT, INCIDENT, TRAVEL, PROSPECT, and more |
| 5\. Info Only | Gives information without creating a ticket. | PAY STUBS W2, PAY STUBS SFC, TICKET STATUS |
| 6\. SMS | Sends text messages to the caller. | Send App Link, SMS APP LINK |
| 7\. Submit | Reads disclosures and submits the request. | MCO, INCIDENT, TRAVEL, PROSPECT SUBMIT |
| 8\. Tickets | Creates ticket, sends text, reads ticket number. | Create Ticket, Send Ticket SMS, Ticket Confirmation |
| 9\. Transfers | Connects caller to a real person. | 7 TRANSFER nodes |
| 10\. Global | Emergency handlers from anywhere. | DISTRESS, FATALITY, HUMAN REQUEST, FAQ, TOPIC CHANGE |
| 11\. Denials | Blocks requests that can't be processed. | TRAVEL DENY, DD HOLD, DD SECURITY BLOCK |
| 12\. Close | Says goodbye and ends the call. | CLOSE CALL, END CALL |

# **4\. How to Edit What Aubrey Says**

## **4.1 Editing a Node**

![][image4]

**1\.** Click on any box (node) in the flow to open it. Use Ctrl+F in the Retell editor to search by node name.

**2\.** You'll see two tabs: Prompt (instructions Aubrey interprets) and Static Sentence (exact words)

**3\.** Edit the text, then click Publish

| Mode | When to use |
| :---- | :---- |
| Prompt | Most cases. Aubrey reads instructions and adapts wording. Sounds natural. |
| Static Sentence | Legal disclosures, exact apology language, ticket-number reads. Aubrey says these word-for-word. |

*Tip: Nothing changes until you click Publish. You can make edits but they only go live when published.*

## **4.2 Edge Conditions**

Edges tell Aubrey WHEN to move to the next step. For example: "When the caller says they're done, go to CLOSE CALL."

**1\.** Open a node and scroll down to the Transition section

**2\.** Click the \+ button to add a new connection

**3\.** Pick the destination node and write the condition in plain English

**4\.** Click Publish

| Good condition | Why |
| :---- | :---- |
| "Caller said they don't want the app link, declined, or said no thanks" | Specific phrases — Aubrey knows what to listen for |
| "Caller wants to update direct deposit, bank info, or cost share" | Names the topics explicitly |

| Bad condition | Why |
| :---- | :---- |
| "Caller is done" | Vague — could match almost anything |
| "User wants to leave" | Doesn't say what they would actually say |

*Tip: Order matters\! Conditions are checked top to bottom. Put specific ones above general ones.*

## **4.3 Adding Notes**

Notes are yellow labels on the canvas for organization. They don't affect Aubrey. Click Note in the sidebar, click on canvas to place, type your text.

## **4.4 Dynamic Variables**

Anywhere you see `{{something}}` in a prompt, that's a placeholder filled in automatically at call time. Use them in your edits to make Aubrey sound personal.

| Variable | What It Holds |
| :---- | :---- |
| `{{caller_name}}` | Caller's first and last name (from Monday.com lookup) |
| `{{caller_state}}` | US state from their record |
| `{{caller_email}}` | Email on file |
| `{{caller_phone}}` | The number they called from |
| `{{ticket_id}}` | Ticket number returned after create\_ticket runs |
| `{{caller_tickets}}` | List of the caller's open tickets |
| `{{current_time_America/New_York}}` | Today's date and time in Eastern Time |

*Example: writing* `say "Hi {{caller_name}}, welcome back\!"` *in a prompt makes Aubrey use the caller's real name on the call.*

# **5\. Sample Changes — "If I Want To Do X, Do Y"**

A recipe book of the most common changes your team will make. Each recipe shows where to click, what to edit, and how to test.

## **Recipe 1 — Change Aubrey's Greeting**

**Want to:** Change "Hi, this is Aubrey..." to something else.

**Where:** Flow editor → click the OPENING box → Prompt tab.

**Edit:** Find the line that starts with `Greet caller. If recognized: "Hi [Name], welcome back..."` and replace only the text inside the quotes.

**Test:** Use the Test Call button (top right). Make sure both recognized and brand-new callers hear the right version.

**Common mistake:** Editing the recognition logic instead of just the greeting words. Touch only the quoted text.

## **Recipe 2 — Update a Transfer Phone Number**

**Want to:** Change the number a transfer rings (e.g., Payroll's number changed).

**Where:** Flow editor → click the relevant TRANSFER box → Destination field.

**Edit:** Replace the number in E.164 format: `+16787857010` (plus sign, country code, then digits — no spaces or dashes).

**Test:** Call, route into that flow, confirm the new number rings.

**Common mistake:** Leaving out the `+` and country code. Retell won't dial otherwise.

## **Recipe 3 — Add or Remove a Banned Word**

**Want to:** Stop Aubrey from saying a specific word (e.g., "actually").

**Where:** Global Settings → Agent Handbook.

**Edit:** Find the Banned Words rule and add your word, e.g. `Never say 'Actually', 'Absolutely\!', 'Certainly\!', or 'Perfect\!'`

**Test:** Run a call where Aubrey would naturally use that word. Confirm she avoids it.

*Tip: This affects every call. Publish, then listen to one or two live calls before going home.*

## **Recipe 4 — Change the Closing Line**

**Want to:** Replace "Thanks so much for calling. Have a great day\!"

**Where:** Flow editor → click the CLOSE CALL box → Prompt tab.

**Edit:** Update the closing sentence inside the prompt.

**Test:** Call, complete any flow, confirm the new wording plays before the call ends.

## **Recipe 5 — Add a New Caller Type at the Start**

**Want to:** When Aubrey asks "are you a caregiver, client, case manager, or another party?" — add a fourth option that routes to a specific team.

**Where:** Flow editor → click the OPENING box.

**Edit:**

**1\.** In the Prompt, add to the list, e.g.: `If VENDOR: route to TRANSFER - CASE SUPPORT.`

**2\.** Scroll to the Transition section, click the \+ button.

**3\.** Destination: choose the right transfer node.

**4\.** Condition: `Caller identified as a vendor or supplier calling about deliveries.`

**Test:** Call, say "I'm a vendor here to drop off supplies," verify the routing.

**Common mistake:** Adding the option to the prompt but forgetting the new edge — Aubrey will mention the option but have nowhere to send the caller.

## **Recipe 6 — Update a Tool URL (n8n Webhook Changed)**

**Want to:** Aubrey's create\_ticket or send\_app\_link tool needs to point to a new n8n webhook.

**Where:** Right sidebar → Tools → click the tool name.

**Edit:** Replace the URL field with the new webhook URL. Leave headers, parameters, and response variables alone.

**Test:** Run a call that triggers that tool. Open n8n Executions and confirm the new webhook received the request.

**Common mistake:** Forgetting to Publish after editing a tool — URL changes don't go live until the agent is republished.

## **Recipe 7 — Change What Aubrey Collects in an Intake Flow**

**Want to:** Add or remove a question in a flow like TRAVEL REQUEST or INCIDENT REPORT.

**Where:** Flow editor → click the intake node → Prompt tab.

**Edit:** Find the numbered list of questions and add, remove, or renumber a step. Keep the "ONE QUESTION PER TURN" rule at the top.

**Test:** Call and walk through the full flow. Confirm Aubrey asks the new question and that skipped fields stay skipped.

**Common mistake:** Adding a new field but forgetting to update the create\_ticket tool's parameters to receive it — the field gets collected but never lands in Monday.com.

## **Recipe 8 — Temporarily Disable a Global Handler**

**Want to:** Stop a global handler from firing during a transition period (e.g., you don't want every "I want a human" call to go to Case Support while testing a new flow).

**Where:** Flow editor → click the GLOBAL - HUMAN REQUEST box (or any global node).

**Edit:** In the global condition, change the wording to something that won't match, like: `DISABLED — do not trigger.` The node stays in the flow but doesn't activate.

**Test:** Call and ask for a human. Verify Aubrey stays in the current node instead of jumping to the global.

*Tip: To re-enable, restore the original condition wording.*

## **Recipe 9 — Add a Multi-Step Caller Identification Flow**

*(Use this pattern when you want Aubrey to ask the caller a question, branch on the answer, optionally collect info, and route differently for each branch. Modeled on the real change made when Keyline switched the main line to forward to Aubrey.)*

**Want to:** When Aubrey doesn't recognize a caller, ask if they're a caregiver, client, case manager, or another party. Then:

• Other party → transfer to Case Support

• Caregiver or client → continue normal script (ask state, etc.)

• Case manager → ask whether the client already started services, is starting, or is switching providers, AND collect the client's and caregiver's full names before transferring (Case Support if already started; Care Team for starting or switching)

This is more involved than the previous recipes because it has three layers: an identification question, a sub-question for one branch, and pre-transfer data collection.

### **Step 1 — Add the caller-type question to OPENING**

**Where:** Flow editor → click the OPENING box → Prompt tab.

**Edit:** Add this block to the prompt (place it after the existing greeting, before any topic routing):

```
If the caller is NOT recognized (caller_found = false or caller_name is blank):
After the caller states their reason, ask:
"Just so I can help you best — are you a caregiver, a client,
a case manager, or another party?"

- If ANOTHER PARTY: Say "Let me connect you with our support team.
  Please hold." → route to TRANSFER - CASE SUPPORT.
- If CAREGIVER or CLIENT: Continue the normal flow — ask what
  state they're calling from, then route based on their topic.
- If CASE MANAGER: Route to CASE MANAGER node.

If the caller IS recognized: skip the identification question and
route based on their topic as normal.
```

### **Step 2 — Add edges for the new outcomes**

In the same OPENING node, scroll to the Transition section and add two new edges:

**Edge A:**

• Destination: `TRANSFER - CASE SUPPORT`

• Condition: `Caller has been identified as "another party" — not a caregiver, client, or case manager. Examples: caller says "another party", "I'm a vendor", "I'm calling on behalf of...".`

**Edge B:**

• Destination: `CASE MANAGER`

• Condition: `Caller is a case manager from an outside agency.`

*(Caregiver/client doesn't need a new edge — they continue through the existing topic-routing edges.)*

### **Step 3 — Set up the CASE MANAGER node**

**Where:** Flow editor → click the CASE MANAGER box (or create one if it doesn't exist) → Prompt tab.

**Edit:** Replace the prompt with:

```
Caller has identified as a case manager from an outside agency.

STEP 1 — COLLECT NAMES (before anything else):
Ask: "Can I get the client's first and last name?"
Then ask: "And the caregiver's first and last name?"

STEP 2 — ASK ABOUT CLIENT STATUS:
Ask: "Has the client already started services with Keyline,
are they in the process of starting, or are they looking
to switch providers?"

ROUTING:
- Already started services → Say "Got it. Let me connect you with
  our Case Support team — they handle all active member concerns.
  Please hold while I transfer your call." → TRANSFER - CASE SUPPORT
- In the process of starting → Say "No problem. Let me connect you
  with our Care Team who can help with onboarding. Please hold while
  I transfer your call." → TRANSFER - CARE TEAM
- Looking to switch providers → Say "I'll connect you with our Care
  Team who handles new enrollments. Please hold while I transfer
  your call." → TRANSFER - CARE TEAM

ONE QUESTION PER TURN. Wait for the caller's reply before
asking the next.
```

### **Step 4 — Add edges from CASE MANAGER**

Add two edges on the CASE MANAGER node:

**Edge A:**

• Destination: `TRANSFER - CASE SUPPORT`

• Condition: `Client has already started services with Keyline. Member is active.`

**Edge B:**

• Destination: `TRANSFER - CARE TEAM`

• Condition: `Client is in the process of starting services, is new, or is looking to switch providers.`

### **Step 5 — Test**

Run the Test Call three times, one per caller type:

**1\.** Say "I'm calling on behalf of a client" → should route to Case Support.

**2\.** Say "I'm a caregiver" → should continue to normal topic routing (ask for state, etc.).

**3\.** Say "I'm a case manager" → should ask for client + caregiver names, then ask about status, then transfer to the correct team based on your answer.

**Common mistakes for this kind of multi-step change:**

• Writing the prompt logic but forgetting to add the edges — Aubrey will say the right things but won't route correctly.

• Putting the new edges below more general edges (like "Caller is done") — order matters. Put specific routes above general ones.

• Forgetting to publish after editing both nodes — only the OPENING change would go live and CASE MANAGER would still have its old behavior.

# **6\. Testing Before Publishing**

Never publish straight to production. Use this workflow every time:

**1\.** Click **Test Call** in the top right of the flow editor. Mic into your laptop and walk through the change.

**2\.** If your change touches edges or routing, run 2-3 variations:

   • The happy path (caller does the expected thing)

   • An adjacent flow (make sure you didn't break something nearby)

   • A topic change mid-flow (make sure global handlers still work)

**3\.** Only then click **Publish**.

**If something breaks after Publish:** right sidebar → Versions → revert to the previous version. Then debug.

*Tip: Retell keeps every published version. You can always roll back.*

# **7\. How Aubrey Sends Texts and Creates Tickets**

![][image5]

Aubrey uses three tools during calls. Think of these as buttons she presses behind the scenes.

## **Tool 1: send\_app\_link**

![][image6]

Sends a text with the Keyline app link. The caller's phone number is automatically filled in. Aubrey picks the right link based on who's calling:

| Caller Type | Link Sent |
| :---- | :---- |
| Regular caregiver | Keyline Family Connect app link |
| Travel request | Travel-specific app link |
| New prospect | Application/enrollment link |

## **Tool 2: create\_ticket**

Takes all information from the call and creates a ticket on Monday.com. Sends back the ticket number so Aubrey can read it to the caller.

## **Tool 3: send\_ticket\_sms**

After a ticket is created, sends a text with the ticket number and confirmation. Separate from the app link tool so Aubrey never sends the wrong type of message.

# **8\. Behind-the-Scenes Automations (n8n)**

n8n is the automation platform that does the heavy lifting. Think of it as Aubrey's assistant. There are three automations:

## **8.1 Caller Lookup**

![][image7]

Runs at the start of every call. Checks Monday.com for the caller's phone number. If found, sends their name, state, email, and history back to Aubrey so she can greet them by name.

## **8.2 Create Ticket**

![][image8]

Runs when Aubrey finishes collecting information. Creates a ticket on Monday.com. If it's a fatality, sends an emergency email to leadership immediately.

## **8.3 Send SMS**

![][image9]

Handles all text messages. Picks the right message based on type:

| Type | When Sent | What the Text Says |
| :---- | :---- | :---- |
| App Link | Caller wants the caregiver app | Here's your Keyline app link |
| Travel Link | Caller wants to submit travel | Here's your travel request link |
| Prospect Link | New applicant | Here's your application link |
| Ticket Confirmation | After ticket created | Your ticket has been submitted, we'll follow up in 1-2 days |

# **9\. Monday.com \- Your Ticket Board**

![][image10]

Every call Aubrey handles creates a ticket here. Your team uses this board to review, follow up, and resolve requests.

| Column | What It Shows | Auto-Filled? |
| :---- | :---- | :---- |
| Item Name | Ticket type and caller name | Yes |
| Caller Name | First and last name | Yes |
| Caller Email | Email (if collected) | Yes |
| Caller Phone | Phone number | Yes |
| Caller State | US state | Yes |
| Status | New / In Review / Awaiting / Resolved / Escalated | Yes (starts New) |
| Call Type | missed\_clockout, incident, travel, etc. | Yes |
| Priority | normal / high / fatality | Yes |
| Call Summary | AI-generated call summary | Yes |

**Ticket lifecycle:** New \> In Review \> Awaiting Caregiver \> Resolved (or Escalated at any point)

*Tip: Fatality tickets automatically send an email alert to leadership the moment they're created.*

# **10\. Who Gets Called For What**

| Team / Person | Phone Number | What They Handle |
| :---- | :---- | :---- |
| Case Support (Dani, Kyla, CJ, Lory) | \+1 (678) 785-7010 | Everything for people already in the program |
| Care Team (Mel) | \+1 (678) 785-7013 | Anyone new or interested, switching providers |
| Payroll Team | \+1 (678) 785-7010 | Pay-specific: wrong paycheck, deductions, direct deposit |
| Health Coach | \+1 (678) 785-7010 | Wellness or health coach requests |
| Alyssa | \+1 (470) 243-8993 | Phone screening, nurse assessments, nurse visits |
| Rochele | \+1 (678) 785-7013 | Prospect App, onboarding docs, enrollment |
| Kalil | \+1 (770) 658-0034 | Semi-annual visits, 6-month appointments |

## **Two Different Apps**

| App | Who Uses It | Transfer To |
| :---- | :---- | :---- |
| Prospect App (Keyline App) | People applying or just enrolled | Rochele at \+1 (678) 785-7013 |
| Family Connect (FC App / CareBravo) | Caregivers already in program | Case Support at \+1 (678) 785-7010 |

## **Case Manager Routing**

| If the Client Has... | Transfer To |
| :---- | :---- |
| Already started services | Case Support at \+1 (678) 785-7010 |
| Not started yet | Care Team (Mel) at \+1 (678) 785-7013 |
| Looking to switch providers | Care Team (Mel) at \+1 (678) 785-7013 |

# **11\. Common Problems and How to Fix Them**

| What's Happening | Why | How To Fix |
| :---- | :---- | :---- |
| Aubrey talks over the caller | Responds too quickly | Lower Response Eagerness to 0.5, then Publish |
| Ignores questions during intake | Old rule blocks off-topic | Edit global prompt to acknowledge then continue |
| Texts aren't sending | Automation might be down | Check n8n execution logs |
| Tickets aren't created | Webhook timing out | Check n8n Create Ticket workflow logs |
| Wrong type of link sent | Tool description unclear | Edit send\_app\_link description with clearer rules |
| Repeats same phrase | Node forces specific phrase | Remove forced phrase, add 'vary responses' rule |
| International travel accepted | Missing country check | Add 'Where will you be traveling?' as Step 2 |
| Call never ends after bye | Missing edge | Add transition: caller says bye \> CLOSE CALL |
| Re-asks known info | Rigid step-by-step | Add 'check context first' at top of node |
| Changes not showing | Forgot to publish | Click the Publish button in top right |
