# GHL Knight Law Group - Post Retell workflow


Overall purpose

This workflow processes inbound webhook calls from your Voice AI system for Knight Law Group. It:

Finds or creates the contact based on phone/email
Writes detailed call analysis data into custom fields
Logs the call and adds internal notes
Routes the contact based on Lead Status and Lead Language
Triggers the right follow-up (retainer, non‑retainer, bad lead, opt‑out, human requested)
Manages opportunities and tags
Starts or stops other follow-up workflows as needed
1. Trigger & Contact Handling
Trigger

Inbound Webhook: Fires whenever your external system (Retell / n8n pipeline) sends a call payload into the platform.
Contact lookup / creation

Find Contact

Looks up a contact by:
Phone: {{inboundWebhookRequest.call.retell_llm_dynamic_variables.Phone}}
Email: {{inboundWebhookRequest.call.retell_llm_dynamic_variables.Email}}
If found → goes down Contact Found branch.
If not found → goes down Contact Not Found branch.
Contact Not Found branch

Create Contact: Creates a new contact with phone and email from the webhook.
Go To: Jumps into the same update step used for existing contacts (so both paths converge).
Contact Found branch (and post-create path)

Update contact field: Writes a large set of call-analysis values into contact fields, including:

Vehicle issues, purchase in CA, still in possession, year, make, model
Repairs attempted, is owner
Email, phone, full name
Lead Status, Lead Language
Purchase condition
Bad Lead Reason
Full transcript + Call ID into a “Transcript of the Call” field
Add voice tag: Adds the tag voice to mark this as a Voice AI lead.

n8n Execution Note: Adds a colored internal note with:

Call ID
Call time
n8n Execution ID
Link to the specific n8n workflow
Log external call: Logs the call as an outbound call record with:

Date, to/from numbers, status, recording URL as attachment.
2. Lead Status Routing (main decision hub)
After logging the call, the workflow runs a big If/Else on:

inboundWebhookRequest.call.call_analysis.custom_analysis_data.[Lead Status]
Branches:

Incomplete Lead
Retainer Lead
Non-Retainer Lead
Bad Lead
Opt-Out Consent
Human Requested
None (fallback if Lead Status doesn’t match any of the above)
Each branch has its own logic.

3. Incomplete Lead branch
Add to Followup Workflow: Enrolls the contact into another workflow:
Workflow ID: d41b1884-7adc-44dc-9930-ad48b6c34f37
Passes trigger parameters through.
This is essentially a handoff to a separate “Incomplete Lead” follow-up sequence.

4. Retainer Lead branch
First, it checks whether the contact already has the retainer-sent tag.

Condition: retainer-sent Tag Exists?
If No (tag does NOT exist) → run retainer sequence.
If Yes (tag exists) → do nothing further in this branch.
If No (retainer not yet sent):

Retainer Zapier Webhook - Post Call (Voice AI)

Sends a POST to a Zapier hook with recording_url from the call.
Create Or Update Opportunity

Pipeline: hjM5PWMprkNJNLZbDT6x
Stage: 1434edf3-c7cd-4e28-988c-91d486181faa
Status: won
Name: {{contact.name}}
Source: {{contact.source}}
Add retainer-sent Tag

Adds retainer-sent to the contact.
Language split (Lead Language)

Checks Lead Language from the inbound webhook:
English
Spanish
None (fallback)
English sub-branch:

Email: Sends an English retainer email with:
Explanation of next steps
Link to sign agreement: https://sign.knightlaw.com/d/JU6yZ9Utb5qpG3
SMS: Sends an English SMS with the same agreement link and opt-out language.
Remove from Workflow: Removes the contact from:
d41b1884-7adc-44dc-9930-ad48b6c34f37
b60daf25-8c0a-43cb-a01f-fd05598e47ff
9dfbcfc4-33bc-4f85-b8f4-1322abefd50a
Spanish sub-branch:

Email: Sends a Spanish retainer email with:
Link: https://sign.knightlaw.com/d/ES92PraGmTb2ym
SMS: Sends a Spanish SMS with the same link and opt-out language.
Remove from Workflow: Same three workflows removed as in English.
None sub-branch:

Does nothing further (no language match).
5. Non-Retainer Lead branch
First, it checks whether the contact already has the non-retainer-followup tag.

Condition: non-retainer-followup Tag Exists?
If No → run non-retainer follow-up.
If Yes → do nothing further in this branch.
If No:

Non-Retainer Zapier Webhook - Post Call (Voice AI)

POST to the same Zapier hook with recording_url.
Add non-retainer-followup Tag

Adds non-retainer-followup.
Remove from Workflow

Removes from workflow d41b1884-7adc-44dc-9930-ad48b6c34f37 (the incomplete follow-up).
Language split (Lead Language)

English
Spanish
None
English sub-branch:

Add to Workflow - Non-Retainer Leads - Follow up English
Adds to workflow b60daf25-8c0a-43cb-a01f-fd05598e47ff.
Create Or Update Opportunity
Same pipeline and stage as Retainer Lead, status won.
Spanish sub-branch:

Add to Workflow - Non-Retainer Leads - Follow up Spanish
Adds to workflow 9dfbcfc4-33bc-4f85-b8f4-1322abefd50a.
Create Or Update Opportunity
Same pipeline/stage, status won.
None sub-branch:

No further actions.
6. Bad Lead branch
Bad Lead Zapier Webhook - Post Call (Voice AI)

POST to Zapier with recording_url.
Create Or Update Opportunity

Pipeline: hjM5PWMprkNJNLZbDT6x
Stage: b23bab57-3063-44a9-81ba-4acbac350e16
Status: lost
Name/source from contact.
Remove from Workflow

Removes from workflow d41b1884-7adc-44dc-9930-ad48b6c34f37.
7. Opt-Out Consent branch
Opt-out Zapier Webhook - Post Call (Voice AI)

POST to Zapier with recording_url.
Wait

Waits 5 minutes.
Remove from Workflow

Removes the contact from all workflows, including the current one.
This effectively cleans the contact out of all automations after an opt-out.

8. Human Requested branch
This branch is triggered when the Lead Status logic routes to “Human Requested” (and also there’s a separate branch in the main condition that checks the contact’s Lead Status field for “Human Requested”).

HR Zapier Webhook - Post Call (Voice AI)

POST to Zapier with recording_url.
Language split (Lead Language)

English
Spanish
None
English sub-branch:

SMS: Sends an English SMS with a Calendly link:
https://calendly.com/knight-law/ca-lemon-case-evaluation
Email: Sends an English email with the same Calendly link and explanation.
Remove from Workflow: Removes from all workflows (include current).
Spanish sub-branch:

SMS: Sends a Spanish SMS with Calendly link:
https://calendly.com/knight-law/consultagratis-california
Email: Sends a Spanish email with the same link and explanation.
Remove from Workflow: Removes from all workflows (include current).
None sub-branch:

No further actions.
9. None (fallback) branch
If Lead Status doesn’t match any of the defined values, the None branch under the main Lead Status condition is taken.
This branch has no actions; the workflow effectively ends for that contact.
10. Summary of key behaviors
Data capture: Rich call analysis is stored on the contact, including transcript and custom fields.
Tagging: Uses voice, retainer-sent, and non-retainer-followup to control logic and prevent duplicates.
Opportunities: Creates/updates opportunities in a single pipeline, with different stages/statuses for retainer, non-retainer, and bad leads.
External systems:
Multiple POSTs to a single Zapier hook for downstream processing.
Links out to n8n for execution tracking.
Uses Calendly links for human-requested consults.
Language-aware: All client-facing communication (email/SMS) is split between English and Spanish based on Lead Language.
Workflow hygiene: Several branches remove contacts from other workflows or all workflows to avoid conflicting automations.

---

# ZAPIER 02.01. Post Call (Voice AI)

Full Zap Architecture: "02.01. Post Call (Voice AI)"
Here's the complete flow breakdown for your Zap:

Trigger
🔵 Webhook Listener (WebHookCLIAPI)

Receives incoming POST/GET data from Voice AI system
Outputs: full_name, phone, Lead Status, Lead Language, Salesforce Record ID, email, vehicle details, etc.
Linear Action Steps (Sequential)
Step 2: AI by Zapier - Name Parser
Model: OpenAI GPT-4o-mini
Input: {{321866861__full_name}}
Task: Extract and separate FirstName, MiddleName, LastName
Outputs: 
FirstName
MiddleName
LastName
Step 3: Formatter by Zapier - Phone Formatter
Transform: Format Phone Number (US format)
Input: {{321866861__phone}}
Output: {{326564301__output}} (formatted phone)
Parallel Paths Container - Lead Status Router
Evaluates {{321866861__Lead Status}} and routes to one of 4 branches:

Branch A: "Retainer Lead" ✅ (Path Eval Index: 0)
Filter: Checks if Lead Status = "Retainer Lead" (exact match)
Salesforce: Find Record (by Lead ID)
Salesforce: Update Lead with:

Name components (AI output)
Phone (formatted)
Vehicle details (possession, year, make, model)
Repair notes (compiled from webhook data)
Status → "HF Retainer Sent"
Processor → "HeroFlow"
→ Then enters NESTED Parallel Path for Lead Language:

Nested Path A1: English ✅
Filter: Lead Language contains "English"
DocuSign: Send Envelope from Template
Template: "Knight Law Fee Agreement" (English)
Recipient: webhook email & full name
Pre-fills: phone, vehicle make
Nested Path A2: Spanish ✅
Filter: Lead Language contains "Spanish"
DocuSign: Send Envelope from Template
Template: "Knight Law Fee Agreement Spanish"
Recipient: webhook email & full name (Spanish template)
Pre-fills: phone, vehicle make
Branch B: "Non-Retainer Lead" (Path Eval Index: 1)
Filter: Checks if Lead Status = "Non-Retainer Lead" (exact match)
Salesforce: Find Record (by Lead ID)
Salesforce: Update Lead with:
Name components (AI output)
Phone (formatted)
Vehicle details
Repair notes
Status → "HF Appointment"
Processor → "HeroFlow"
(No DocuSign envelope sent)
Branch C: "Bad Leads" (Path Eval Index: 2)
Filter: Checks if Lead Status = "Bad Lead" (exact match)
Salesforce: Find Record (by Lead ID)
Salesforce: Update Lead with:
Status → "HF Bad Lead"
HasOptedOutOfEmail → true
DoNotCall → true
Bad Lead Reason (from webhook)
(Keeps existing name if not parsed)
Branch D: "Opt-out Lead" (Path Eval Index: 3)
Filter: Checks if Lead Status contains "Opt-Out Consent"
Salesforce: Find Record (by Lead ID)
Salesforce: Update Lead with:
Status → "Burnt Lead"
HasOptedOutOfEmail → true
DoNotCall → true
Opt_Out_All_Communication__c → true
Burnt Lead Reason → "Requested no more follow-ups/remove from list"
Data Flow Summary
Webhook Input
    ↓
[AI Parsing] → FirstName, MiddleName, LastName
    ↓
[Phone Formatter] → Formatted Phone
    ↓
[Parallel Paths - Lead Status Check]
    ├─→ Retainer Lead
    │   ├─ Update SF Lead (Status: HF Retainer Sent)
    │   └─ [Nested Path - Lead Language]
    │       ├─→ English → DocuSign (EN template)
    │       └─→ Spanish → DocuSign (ES template)
    │
    ├─→ Non-Retainer Lead
    │   └─ Update SF Lead (Status: HF Appointment)
    │
    ├─→ Bad Lead
    │   └─ Update SF Lead (Status: HF Bad Lead, Mark DND)
    │
    └─→ Opt-Out Lead
        └─ Update SF Lead (Status: Burnt Lead, Opt-out all comms)