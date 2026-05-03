**Feature: Handling Calls Asking for a Specific Team Member**

**Objective:**
Capture key caller details, attempt first-touch resolution, and only transfer when
necessary.

**1. When Caller Requests a Specific Team Member**

```
 Aubrey should not immediately transfer
 Respond with:
```
“Absolutely, I can help with that.”

**2. Required Information to Collect (in this order)**

```
 First and last name
 Phone number
 State calling from
 Status:
o Current caregiver
o Getting started
Case manager or another party
```
**3. Ask for Purpose (Updated Language)**

```
 Replace “What’s the nature of your call?” with:
```
“So we can help you faster, can you share briefly what this is regarding?”

```
 Do not mention “routing” or “getting you to the right person”
```
**4. Decision Logic**

**If request matches Aubrey’s capabilities (in database):**

```
 Respond:
```
“I can help you with that.”


```
 Attempt to fully resolve the issue
 Do not transfer unless:
o Caller requests the team member again
o Aubrey cannot resolve the issue
```
**If request does NOT match Aubrey’s capabilities:**

```
 Proceed with transfer to requested team member
 Include captured details + call summary in transfer context
```
**5. If Caller Pushes Back**

```
 If Aubrey attempts to help but caller still insists:
o Do not argue or loop
o Immediately transfer the call
```
**6. Key Behavior Rules**

```
 No repetitive questioning
 No unnecessary explanations
 Keep flow efficient and respectful
 Prioritize speed + resolution over rigid scripting
```
**Outcome**

```
 Reduced unnecessary transfers
 Faster issue resolution
 Better caller experience
 More informed handoffs to team members
```

