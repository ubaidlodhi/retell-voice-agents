## CALL - 01:

Node Transition
0:00
previous node: begin

new node: OPENING

transition type: normal

Agent
0:02
Hi, this is Aubrey with Keyline Home Care. How can I support you today?

User
0:08
Uh, Hi. I need to report a hospital admission. 

Knowledge Base Retrieval
Agent
0:14
Okay, I can help with that. Just so I can help you best, are you a caregiver, a client, a case manager, or another party?

User
0:25
I am a caregiver. 

Node Transition
0:27
previous node: OPENING

new node: CAREGIVER - TOPIC MENU

transition type: normal

Knowledge Base Retrieval
Agent
0:27
Alright. I’ll help you report the hospital admission now. Can I get your full name, please?

User
0:34
Yeah. It's debit Jackson. 

Node Transition
0:42
previous node: CAREGIVER - TOPIC MENU

new node: APP OFFER - INCIDENT

transition type: normal

Knowledge Base Retrieval
Agent
0:42
I'm sorry to hear your member was admitted. I can help you report this now. You can also submit hospital admissions through your caregiver app if that's easier. Would you like me to text you the app link?

User
0:55
No. Let's do it over the phone. 

Node Transition
0:59
previous node: APP OFFER - INCIDENT

new node: INCIDENT REPORT

transition type: normal

Knowledge Base Retrieval
Agent
0:59
Just to confirm, your first name is Debit and your last name is Jackson, right?

User
1:05
Correct. 

Knowledge Base Retrieval
Agent
1:08
Thanks, Debit. What’s the best phone number to reach you at?

User
1:14
You can use the number from which I'm calling. 

Knowledge Base Retrieval
Agent
1:18
Okay, I’ll use the number you’re calling from: [phone number 1]. Is that correct?

User
1:26
Correct. 

Knowledge Base Retrieval
Agent
1:28
Thanks. Who is the patient or member that was admitted to the hospital?

User
1:35
So there's Dorothy Williams 

Knowledge Base Retrieval
Agent
1:41
Just to confirm, this is for Dorothy Williams, right?

User
1:45
Correct. 

Knowledge Base Retrieval
Agent
1:48
What type of incident is this — was it a fall, an urgent care visit, an emergency room visit, or a hospital admission?

User
1:57
A hospital admission. 

Knowledge Base Retrieval
Agent
2:02
What date did the hospital admission happen?

User
2:06
Yesterday around ten AM. 

Knowledge Base Retrieval
Agent
2:09
What’s the name of the hospital where Dorothy was admitted?

User
2:15
It's [address 1] 

Knowledge Base Retrieval
Agent
2:20
What city is [address 1] located in?

User
2:25
So it's located in [address 2]. 

Knowledge Base Retrieval
Agent
2:31
What state is [address 1] in?

User
2:36
[address 3]. 

Knowledge Base Retrieval
Agent
2:38
What time was Dorothy admitted to the hospital?

User
2:44
Around eleven AM. 

Knowledge Base Retrieval
Agent
2:46
What was the reason Dorothy was admitted to the hospital?

User
2:51
Elevated blood pressure. 

Knowledge Base Retrieval
Agent
2:54
What treatments is Dorothy receiving right now?

User
3:00
So she's being like, she's admitted and getting the drift I guess. 

Knowledge Base Retrieval
Agent
3:11
Is Dorothy still admitted in the hospital, or has she been discharged and returned home?

User
3:18
She just still admitted 

Knowledge Base Retrieval
Agent
3:21
Please do not clock in or out while Dorothy is in the hospital. Call us back once she's been discharged and is back home receiving care. Can you briefly describe what actually happened?

User
3:32
So she woke up busy, her BP was very high. 

Node Transition
3:38
previous node: INCIDENT REPORT

new node: INCIDENT SUBMIT

transition type: normal

Agent
3:38
We wish your loved one a speedy recovery. I'm submitting your request now.

Node Transition
3:43
previous node: INCIDENT SUBMIT

new node: Create Ticket

transition type: normal

Tool Invocation: create_ticket
3:45
tool_call_id: tool_call_bdf0ae

{
  "caller_name": "Debit Jackson",
  "collected_fields": null,
  "caller_phone": "[phone number 2]",
  "caller_state": "[address 3]",
  "patient_name": "Dorothy Williams",
  "caller_email": null,
  "priority": "urgent",
  "call_type": "incident",
  "call_summary": "Caregiver Debit Jackson reported that client Dorothy Williams was admitted to [address 4], on May twenty-fifth around eleven AM due to elevated blood pressure. Dorothy is still admitted and receiving treatment. Debit described that Dorothy woke up dizzy and had very high blood pressure."
}
User
3:45
Thank you. 

Tool Result
3:46
tool_call_id: tool_call_bdf0ae

Knowledge Base Retrieval
Agent
3:47
Is there anything else I can help you with today?

Node Transition
3:49
previous node: Create Ticket

new node: Send Ticket SMS

transition type: normal

Tool Invocation: send_ticket_sms
3:50
tool_call_id: tool_call_212782

{
  "ticket_id": "ticket_id_placeholder",
  "call_type": "incident",
  "message_type": "ticket_confirmation"
}
Tool Result
3:51
tool_call_id: tool_call_212782

{"success":true,"message":"SMS has been sent successfully.","message_type":"ticket_confirmation"}

Node Transition
3:51
previous node: Send Ticket SMS

new node: Ticket Confirmation

transition type: normal

User
3:51
No. Thank you. 

Node Transition
3:53
previous node: Ticket Confirmation

new node: CLOSE CALL

transition type: normal

Agent
3:53
Thank you for calling Keyline Home Care.Have a great day, Debit!

Node Transition
3:57
previous node: CLOSE CALL

new node: END CALL

transition type: normal

Tool Invocation: end_call
3:57
tool_call_id: end_call_5975c3

{}

---

## CALL - 02:

Node Transition
0:00
previous node: begin

new node: OPENING

transition type: normal

Agent
0:02
Hi, this is Aubrey with Keyline Home Care. How can I support you today?

User
0:09
Oh, hi. I want to sign up to get paid to to take care of my mom. 

Node Transition
0:16
previous node: OPENING

new node: PROSPECT INTAKE

transition type: normal

Knowledge Base Retrieval
Agent
0:16
Sure, Keyline helps families get paid to care for loved ones at home. Let's get started with a few details. What's your first name?

User
0:26
So it's John Doe. 

Knowledge Base Retrieval
Agent
0:30
Just to confirm — your first name is John, right?

User
0:35
Yes. 

Knowledge Base Retrieval
Agent
0:38
Okay, John. And your last name is Doe, right?

User
0:43
Yeah. The last name is Do. 

Knowledge Base Retrieval
Agent
0:46
Alright, just to confirm — your last name is spelled D O, correct?

User
0:52
Yeah. It's d o e. 

Knowledge Base Retrieval
Agent
0:57
Alright, just to confirm — your last name is D O E, right?

User
1:03
Correct. 

Agent
1:05
Thanks. Now, can you confirm the best phone number to reach you? I have it as [phone number 1]. Is that correct?

User
1:15
Yes. Correct. 

Knowledge Base Retrieval
Agent
1:17
Alright. What city and state are you calling from?

User
1:23
So uh-huh. 

User
1:28
Yeah. 

Knowledge Base Retrieval
Agent
1:27
Okay. Which 

User
1:28
So I'm calling from yeah, I'm calling from let me check. 

Knowledge Base Retrieval
Agent
1:39
Take your time. When 

User
1:40
Yeah. I'm calling from new [address 1]. 

Knowledge Base Retrieval
Agent
1:45
Got it. Are you the family caregiver for your mom?

User
1:50
Yes. 

Knowledge Base Retrieval
Agent
1:52
Alright. What is your relationship to your mom — are you her son?

User
1:58
Yep. I am. 

Knowledge Base Retrieval
Agent
2:01
Does your mom have Medicaid?

User
2:05
Yeah. She has. 

Knowledge Base Retrieval
Agent
2:08
Is your mom currently receiving home care services?

User
2:13
No. She's not. 

Knowledge Base Retrieval
Agent
2:15
Is anyone currently being paid to care for your mom?

User
2:20
Nope. 

Knowledge Base Retrieval
Agent
2:24
Alright. What's your mom's first name?

User
2:30
Her first name is Grace. 

Knowledge Base Retrieval
Agent
2:34
Alright. What's your mom's last name?

User
2:38
Williams. 

Knowledge Base Retrieval
Agent
2:40
Do you have your mom's date of birth? If so, please share it. If not, that's no problem.

User
2:48
Actually, I can't remember that right now. 

Agent
2:52
No problem. Does your mom need help with bathing or dressing?

User
2:58
Yeah. She does. 

Agent
3:00
Does your mom have Alzheimer's or dementia?

User
3:05
No. None of that. 

Agent
3:08
Does your mom have autism or an intellectual or developmental disability?

User
3:15
No. Thankfully not. 

Knowledge Base Retrieval
Agent
3:18
Got it — one moment.

Agent
3:29
Still with me? Take your time.

User
3:32
Yes. Yes. 

Node Transition
3:34
previous node: PROSPECT INTAKE

new node: PROSPECT SUBMIT

transition type: normal

Knowledge Base Retrieval
Agent
3:34
Caregivers deserve real support, and we're going to start reviewing your case right away. You'll receive an update on your eligibility within one business day or sooner. Please be on the lookout for a call or text with next steps. I'm submitting your request now.

Node Transition
3:50
previous node: PROSPECT SUBMIT

new node: Create Ticket

transition type: normal

Tool Invocation: create_ticket
3:52
tool_call_id: tool_call_f2fb49

{
  "caller_name": "John Doe",
  "collected_fields": null,
  "caller_phone": "[phone number 2]",
  "caller_state": "[address 2]",
  "patient_name": "Grace Williams",
  "caller_email": null,
  "priority": "normal",
  "call_type": "prospect",
  "call_summary": "John Doe called to sign up to get paid to care for his mother, Grace Williams, in [address 1]. His mother has Medicaid, is not currently receiving home care, and no one is being paid to care for her. She needs help with bathing or dressing, but does not have Alzheimer's, dementia, autism, or an intellectual or developmental disability. John is her son and primary caregiver."
}
Tool Result
3:54
tool_call_id: tool_call_f2fb49

{"ticket_id":"12099437115","ticket_success":true}

Node Transition
3:54
previous node: Create Ticket

new node: Send Ticket SMS

transition type: normal

Tool Invocation: send_ticket_sms
3:56
tool_call_id: tool_call_2fb84c

{
  "ticket_id": "12099437115",
  "call_type": "prospect",
  "message_type": "ticket_confirmation"
}
Tool Result
3:56
tool_call_id: tool_call_2fb84c

{"success":true,"message":"SMS has been sent successfully.","message_type":"ticket_confirmation"}

Node Transition
3:56
previous node: Send Ticket SMS

new node: Ticket Confirmation

transition type: normal

Knowledge Base Retrieval
Agent
3:58
Your ticket number is one two zero - nine nine four - three seven one - one five. Take a moment to write that down if you need to. You'll also get a text message with your ticket details. Would you like me to repeat the number?

User
4:14
No. Thank you. 

Knowledge Base Retrieval
Agent
4:16
Is there anything else I can help you with today?

User
4:21
That's all. 

Node Transition
4:23
previous node: Ticket Confirmation

new node: CLOSE CALL

transition type: normal

Agent
4:23
Thank you for calling Keyline Home Care.Have a great day, John!

Node Transition
4:27
previous node: CLOSE CALL

new node: END CALL

transition type: normal

Tool Invocation: end_call
4:27
tool_call_id: end_call_e848c6

{}