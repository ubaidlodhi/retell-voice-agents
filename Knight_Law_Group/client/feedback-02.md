Adjustments Required 07/10:

For those users that expressly ask to speak to a human, we want Alice to overcome that objection (something in the lines of: I totally understand, I’m an AI agent fully prepared to help you gather all the basic information to pre-qualify your case and move you to a human agent). If the user insists that wants to speak to a human, then transfer the call to our English/Spanish lines provided. Update the Lead Status to: HF Appointment. But, send one text with the Calendly link and then stop the follow up cadence for this specific user.
Update all follow up cadence to direct people to call Alice at: +12132053651. Keep the (310) 552-2250 for the SMS that go out with a Calendly link or a Retainer.
Add a small latency as soon as the user picks up the call, wait for the user to answer and then proceed with the greeting.
Remove the confirmation of phone number. Keep the confirmation of the full name (spell it) and email address (no need for spelling).
We continue to see spelling issues - Improve this (In Spanish and English).
Attached are the updated FAQs.
Build the SMS agent as an interactive agent to respond to FAQs and drive leads to a call, book a Calendly or sign the retainer. Not a full qualification agent.
Add more empathy to the agent when responding to FAQs, specially related to vehicle issues, vehicle defects. Those type of questions “Do you want to know what happened?” or “How do I know if I have a case” - (Something in the lines of: “Our team will gather all necessary details, including any issues, defects or experience with your vehicle”)


Let’s also update the number on the VM to Alice’s number please
Also, let’s please keep the consent confirmation to text and email. Even though we are removing the need to confirm the phone number

1. Improve prompt to recognize “leased” “lease”, as transcript sometimes picks "liz", "lists", etc, so similar matching words should he understand by AI. Can make the prompts fixes where we are asking questions related to lease.

2. Spelling of characters is not correct, sometimes it wents smooth, and sometime it is mixing letters, misses letters or goes too fast, or like instead of repeating letter by letter, she make it as a word.

3. Repeatedly asking the same question —> Need variation —> “Just to confirm”, “Does that help — was there anything else you wanted to ask?”, So it should not everytime say "just to confirm" there should be variations so it should not feel AI, and on the FAQs part, after each, the agent asks “Does that help — was there anything else you wanted to ask?”, which feels annoying if user is asking question again and again, so let me know how we should handle it.

4. In one call, User asked “Do you speak Spanish”? and the agent said “Yes” and asked the question above in English. Then switched to Spanish

see this call as well, same issue:

Node Transition
0:00
previous node: begin

new node: node-intro-lang

transition type: normal

Node Transition
0:00
previous node: node-intro-lang

new node: Introduction

transition type: normal

Agent
0:00
Hi! This is Alice from Knight Law Group, calling on a recorded line. I'm following up on your inquiry about your vehicle — are you currently having issues with it?

User
0:12
Hola, ¿hablas español? 

Agent
0:14
Yes, I do speak Spanish, but just to confirm — are you currently having any issues with your vehicle?

Agent
0:41
Um, just checking in — are you currently having any issues with your vehicle?

5. Email spelling should take effect in contact details


6. Check the following under “Opt-Out Consent” that were put there by mistake:

Robert Farrow
Lorraine Skomars Ray
Brenda Santana
Sandrine Masseron Tiller
Pedro A Hernandez

In all cases, Alice got a recorded message from the user and marked the lead as opt out.
Please put them all as Incomplete Leads and have Alice call back

View Transcript:

Node Transition
0:00
previous node: begin

new node: node-intro-lang

transition type: normal

Node Transition
0:00
previous node: node-intro-lang

new node: Introduction

transition type: normal

Agent
0:00
Hi! This is Alice from Knight Law 

User
0:03
Please leave 

Agent
0:02
Group, calling on 

User
0:03
your message for nine one six five zero four six zero seven six. Sorry. Mailbox is full. To send an SMS notification, press five. 

Agent
0:16
Hi, this is Alice from Knight Law Group, calling on a 

User
0:20
To send 

Agent
0:20
recorded line.

User
0:21
an SMS notification, press five. 

Agent
0:25
Hi! This is Alice from Knight Law Group, calling on a recorded 

User
0:28
To 

Agent
0:28
line.

User
0:28
send an SMS notification, press five. 

Agent
0:32
Hi! This is Alice from Knight Law Group, calling on a recorded line. I'm following up 

User
0:36
Thank you for calling. Goodbye. 

https://heroflow.app.n8n.cloud/workflow/L1oNbhjnF9czixEH/executions/131940

