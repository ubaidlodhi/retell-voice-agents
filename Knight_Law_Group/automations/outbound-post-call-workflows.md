# GHL Knight Law Group - Post Retell workflow


High-Level Overview
Trigger: Inbound webhook from your voice AI / call system.
Core logic:
Try to find an existing contact by phone/email.
If not found, create the contact, then continue.
Update contact fields from call analysis data.
Tag the contact as “voice”.
Branch by Lead Status:
Incomplete Lead
Retainer Lead
Non-Retainer Lead
Bad Lead
Opt-Out Consent
None (fallback)
For Non-Retainer Leads, further branch by Lead Language (English / Spanish / None).
Each branch then sends webhooks, manages opportunities, and/or moves contacts into follow-up workflows or removes them from workflows.
Detailed Architecture
Trigger
Triggers:

Inbound Webhook:
Type: inbound_webhook
Starts the workflow whenever your external system posts call data into this webhook.
Initial Contact Resolution
Actions:

Find Contact:
Type: find_contact (multi-path)
Looks up a contact using:
Phone: {{inboundWebhookRequest.call.retell_llm_dynamic_variables.Phone}}
Email: {{inboundWebhookRequest.call.call_analysis.custom_analysis_data._email _address}}
Has two branches:
Contact Found
Contact Not Found
Path A – Contact Found
Flow: Inbound Webhook → Find Contact → Contact Found transition

Contact Found (Transition):

Type: transition (branch of Find Contact)
Next: Update contact field
Update contact field:

Type: update_contact_field
Updates many fields on the contact from call analysis, including:
Are you having issues with your vehicle?
Did you purchase or lease your vehicle from a dealership in California?
Are you still in possession of the vehicle?
Vehicle year, make, model
Purchase condition (new/used/CPO)
Whether they visited a dealership for repair
Whether they are the owner / signed the sales contract
Phone Number
Email Address
Lead Status
Lead Language
Transcript of the Call
Full Name
Bad Lead Reason
Add voice tag:

Type: add_contact_tag
Adds tag: voice
Lead Status Branching (If/Else):

Type: if_else (condition node)
Evaluates: inboundWebhookRequest.call.call_analysis.custom_analysis_data.Lead Status
Branches:
Incomplete Lead
Retainer Lead
Non-Retainer Lead
Bad Lead
Opt-Out Consent
None (else)
From here, each branch has its own sub-flow.

Branch A1 – Incomplete Lead
Flow: Lead Status If/Else → Incomplete Lead branch

Incomplete Lead (Branch Node):

Type: if_else (branch-yes)
Next: Add to Followup Workflow
Add to Followup Workflow:

Type: add_to_workflow
Name: “Add to Followup Workflow”
Adds the contact to workflow ID: d41b1884-7adc-44dc-9930-ad48b6c34f37
Passes trigger parameters into that workflow.
This branch ends here.
Branch A2 – Retainer Lead
Flow: Lead Status If/Else → Retainer Lead branch

Retainer Lead (Branch Node):

Type: if_else (branch-yes)
Next: Retainer Zapier Webhook - Post Call (Voice AI)
Retainer Zapier Webhook - Post Call (Voice AI):

Type: webhook
Method: POST
URL: https://hooks.zapier.com/hooks/catch/24533896/umwlbur/
Sends call/lead data to Zapier.
Create Or Update Opportunity (Retainer):

Type: create_opportunity
Pipeline: hjM5PWMprkNJNLZbDT6x
Stage: 1434edf3-c7cd-4e28-988c-91d486181faa
Name: {{contact.name}}
Source: {{contact.source}}
Status: won
Creates or updates a “won” opportunity for this retainer lead.
Remove from Workflow (multiple):

Type: remove_from_workflow
Removes contact from workflows:
d41b1884-7adc-44dc-9930-ad48b6c34f37
b60daf25-8c0a-43cb-a01f-fd05598e47ff
9dfbcfc4-33bc-4f85-b8f4-1322abefd50a
This branch ends here.
Branch A3 – Non-Retainer Lead
Flow: Lead Status If/Else → Non-Retainer Lead branch

Non-Retainer Lead (Branch Node):

Type: if_else (branch-yes)
Next: Non-Retainer Zapier Webhook - Post Call (Voice AI)
Non-Retainer Zapier Webhook - Post Call (Voice AI):

Type: webhook
Method: POST
URL: https://hooks.zapier.com/hooks/catch/24533896/umwlbur/
Sends non-retainer lead data to Zapier.
Remove from Workflow (Non-Retainer – initial):

Type: remove_from_workflow
Removes from workflow:
d41b1884-7adc-44dc-9930-ad48b6c34f37
Next: Lead Language If/Else
Lead Language Branching (If/Else):

Type: if_else (condition node)
Evaluates: inboundWebhookRequest.call.call_analysis.custom_analysis_data.Lead Language
Branches:
English
Spanish
None (else)
Branch A3a – Non-Retainer, English
English (Branch Node):

Type: if_else (branch-yes)
Next: Add to Workflow - Non-Retainer Leads - Follow up English
Add to Workflow - Non-Retainer Leads - Follow up English:

Type: add_to_workflow
Workflow ID: b60daf25-8c0a-43cb-a01f-fd05598e47ff
Adds English-speaking non-retainer leads to the English follow-up workflow.
Create Or Update Opportunity (Non-Retainer English):

Type: create_opportunity
Pipeline: hjM5PWMprkNJNLZbDT6x
Stage: 1434edf3-c7cd-4e28-988c-91d486181faa
Name: {{contact.name}}
Source: {{contact.source}}
Status: won
This branch ends here.
Branch A3b – Non-Retainer, Spanish
Spanish (Branch Node):

Type: if_else (branch-yes)
Next: Add to Workflow - Non-Retainer Leads - Follow up Spanish
Add to Workflow - Non-Retainer Leads - Follow up Spanish:

Type: add_to_workflow
Workflow ID: 9dfbcfc4-33bc-4f85-b8f4-1322abefd50a
Adds Spanish-speaking non-retainer leads to the Spanish follow-up workflow.
Create Or Update Opportunity (Non-Retainer Spanish):

Type: create_opportunity
Pipeline: hjM5PWMprkNJNLZbDT6x
Stage: 1434edf3-c7cd-4e28-988c-91d486181faa
Name: {{contact.name}}
Source: {{contact.source}}
Status: won
This branch ends here.
Branch A3c – Non-Retainer, None (Language not matched)
None (Language Else Branch):
Type: if_else (branch-no)
No further actions configured.
This branch ends with no follow-up workflow or opportunity.
Branch A4 – Bad Lead
Flow: Lead Status If/Else → Bad Lead branch

Bad Lead (Branch Node):

Type: if_else (branch-yes)
Next: Bad Lead Zapier Webhook - Post Call (Voice AI)
Bad Lead Zapier Webhook - Post Call (Voice AI):

Type: webhook
Method: POST
URL: https://hooks.zapier.com/hooks/catch/24533896/umwlbur/
Sends bad lead data to Zapier.
Create Or Update Opportunity (Bad Lead):

Type: create_opportunity
Pipeline: hjM5PWMprkNJNLZbDT6x
Stage: b23bab57-3063-44a9-81ba-4acbac350e16
Name: {{contact.name}}
Source: {{contact.source}}
Status: lost
Tracks this as a lost opportunity.
Remove from Workflow (Bad Lead):

Type: remove_from_workflow
Removes from workflow:
d41b1884-7adc-44dc-9930-ad48b6c34f37
This branch ends here.
Branch A5 – Opt-Out Consent
Flow: Lead Status If/Else → Opt-Out Consent branch

Opt-Out Consent (Branch Node):

Type: if_else (branch-yes)
Next: Opt-out Zapier Webhook - Post Call (Voice AI)
Opt-out Zapier Webhook - Post Call (Voice AI):

Type: webhook
Method: POST
URL: https://hooks.zapier.com/hooks/catch/24533896/umwlbur/
Sends opt-out consent data to Zapier.
Wait:

Type: wait
Waits 5 minutes after the webhook:
Mode: time-based
Unit: minutes
Value: 5
Remove from Workflow (All):

Type: remove_from_workflow
Attributes:
allWorkflows: true
includeCurrent: true
Removes the contact from all workflows, including this one.
This branch ends here.
Branch A6 – None (Lead Status Else)
None (Lead Status Else Branch):
Type: if_else (branch-no)
No further actions configured.
If Lead Status doesn’t match any of the defined values, the contact reaches this node and the flow ends with no additional processing.
Path B – Contact Not Found
Flow: Inbound Webhook → Find Contact → Contact Not Found transition

Contact Not Found (Transition):

Type: transition
Next: Create Contact
Create Contact:

Type: create_update_contact
Creates a new contact with:
Phone: {{inboundWebhookRequest.call.call_analysis.custom_analysis_data._phone _number}}
Email: {{inboundWebhookRequest.call.call_analysis.custom_analysis_data._email _address}}
Go To (Existing Contact Path):

Type: goto
Target Node: Update contact field (846ca259-690d-42c5-8611-d3d4a6ac936c)
After creating the contact, the flow jumps into the same path as “Contact Found”:
Update contact fields → Add voice tag → Lead Status branching → all the same branches described above.
Summary of Action Types Used
Trigger:

Inbound Webhook
Contact Management:

Find Contact
Create Contact (create_update_contact)
Update contact field
Add contact tag
Logic / Branching:

If/Else (Lead Status)
If/Else (Lead Language)
Branch nodes (Incomplete, Retainer, Non-Retainer, Bad Lead, Opt-Out, None; English, Spanish, None)
Goto
External Integrations:

Webhook (multiple to Zapier URL)
Sales Pipeline:

Create Or Update Opportunity (various stages and statuses)
Workflow Control:

Add to Workflow (3 different follow-up workflows)
Remove from Workflow (specific workflows and all workflows)
Wait (5 minutes before global removal in Opt-Out branch)

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