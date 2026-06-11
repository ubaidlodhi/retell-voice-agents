# GHL 

Overall Structure

Workflow name: 01. Website and FB Form to Retell Outbound
Trigger type: Inbound Webhook
Flow type: Linear (no branches/if-else) — every enrolled contact follows the same path.
Triggers:

Inbound Webhook:
Fires when an external system (e.g., your website form or Facebook form integration) sends an HTTP request into this workflow’s unique webhook URL.
The incoming payload is expected to include at least:
Phone
FullName
Email
Record ID (Salesforce Record ID)
Actions & Flow Path:

Create Contact (type: create_update_contact)

Purpose: Create or update a contact record using fields from the inbound webhook.
Field mappings:
Phone → {{inboundWebhookRequest.Phone}}
Full Name → {{inboundWebhookRequest.FullName}} → stored in contact name
Email → {{inboundWebhookRequest.Email}}
Salesforce Record ID → custom field with ID Nut24vIH6AHbXoKyhX9M (labelled “Salesforce Record ID”) mapped from {{inboundWebhookRequest.Record ID}}
Next step: Create Or Update Opportunity
Create Or Update Opportunity (type: create_opportunity)

Purpose: Create a new opportunity (or update an existing one) in a specific pipeline and stage for this contact.
Configuration:
Pipeline: hjM5PWMprkNJNLZbDT6x
Stage: 3e9236f1-4321-4721-bd1a-74e0e68e3493
Opportunity name: {{contact.name}} (the contact’s name)
Opportunity source: {{contact.source}}
Status: open
Monetary value: empty (no value set)
Next step: Format Phone Number
Format Phone Number (type: number_formatter)

Purpose: Normalize the contact’s phone number into E.164 format for outbound calling.
Input: {{contact.phone_raw}}
Conversion:
From type: number
To type: phone
Options:
Format: E164
Country code: US
Output token: {{number_formatter.1.result}} (this is the formatted phone number)
Next step: Custom Webhook
Custom Webhook (type: custom_webhook)

Purpose: Call the Retell API to initiate an outbound phone call using the formatted number and pass dynamic variables.
HTTP details:
Method: POST
URL: https://api.retellai.com/v2/create-phone-call
Authorization: Bearer token (stored in the action config)
Request body (JSON):
{
  "from_number": "+12132053651",
  "to_number": "{{number_formatter.1.result}}",
  "override_agent_id": "agent_3f40804e015246d679e9aeaf36",
  "retell_llm_dynamic_variables": {
    "Name": "{{contact.name}}",
    "Phone": "{{number_formatter.1.result}}",
    "Email": "{{contact.email}}"
  }
}
from_number: Your fixed outbound caller ID.
to_number: The formatted contact phone from the Format Phone Number step.
override_agent_id: The specific Retell agent to use.
retell_llm_dynamic_variables: Contact data passed into Retell for personalization.
Response handling:
saveResponse: false (the response is not stored on the contact or used later in this workflow).
Next step: None — this is the terminal step of the workflow.
End-to-End Flow Path (Narrative):

External form (website or Facebook) submits data →
Inbound Webhook trigger fires with Phone, FullName, Email, Record ID →
Create Contact: contact is created/updated with phone, name, email, and Salesforce Record ID →
Create Or Update Opportunity: an open opportunity is created/updated in the specified pipeline/stage, named after the contact →
Format Phone Number: the contact’s raw phone is converted to US E.164 format →
Custom Webhook: a POST request is sent to Retell to start an outbound call from your fixed number to the formatted contact number, with name/phone/email passed as dynamic variables →
Workflow ends.

---

# Zapier

Zap Architecture: Voice AI (Pre-call)
Here's the complete breakdown of your automation flow:

Steps & Actions
 Step 	 App 	 Action Type 	 Purpose 
 1. Trigger 	 Salesforce 	 New Lead 	 Monitors Salesforce for new lead records 
 2. Filter 	 Filter by Zapier 	 Conditional Logic 	 Routes leads based on qualification status 
 3. Action 	 Webhooks by Zapier 	 POST Request 	 Sends qualified lead data to LeadConnector HQ 
Flow Path
┌─────────────────────────────────────────┐
│ Salesforce: New Lead Created            │
│ (Trigger - Step 1)                      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Filter by Zapier (Step 2)               │
│ Checks: Status = "HF Qualified"         │
│    AND Processor = "HeroFlow"           │
└──────────┬──────────────────────────────┘
           │
           ├─ ✓ Both conditions match
           │  └──────────────────────────┐
           │                             │
           ▼                             │
    ┌──────────────────────────────┐    │
    │ Webhook POST to LeadConnector │    │
    │ (Step 3 - Action)            │    │
    │ Sends:                       │    │
    │ • Name                       │    │
    │ • Email                      │    │
    │ • Phone                      │    │
    │ • Record ID                  │    │
    └──────────────────────────────┘    │
           │                            │
           ▼                            │
    [Zap Completes]                     │
                                        │
           ✗ Filter doesn't match       │
           └──────────────────────────► [Stop - No Action]

Key Details
Filter Conditions (Both Must Be True):

Lead Status = "HF Qualified" (case-insensitive match)
Processor = "HeroFlow" (case-insensitive match)
Webhook Payload (JSON):

Destination: LeadConnector HQ webhook endpoint
Data mapped from Salesforce lead record:
FullName ← Salesforce Name field
Email ← Salesforce Email field
Phone ← Salesforce Phone field
Record ID ← Salesforce Lead ID
Summary
This is a single-path workflow: New qualified leads from Salesforce (matching both criteria) are automatically forwarded to LeadConnector HQ via webhook. Leads that don't match both filter conditions stop and do not trigger the webhook.