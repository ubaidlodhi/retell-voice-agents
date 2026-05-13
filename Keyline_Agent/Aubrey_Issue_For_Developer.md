# Issue — Pending Applicant Routed to Wrong Team

## What happened
A new applicant called to get an update on their submitted application. Aubrey correctly:
- Identified them as a caregiver in Texas
- Asked a clarifying follow-up and learned they'd applied last week with no response
- Routed into `PROSPECT STATUS CHECK` and sent the app link

Then the caller said *"can I also talk with someone who can assist me directly?"* and Aubrey **transferred to +1 678-785-7010 (Case Support)** — the wrong team. It should have gone to **+1 678-785-7013 (Care Team)**, since Case Support handles active members and Care Team handles pending applicants.

## Why it happened
The `GLOBAL - HUMAN REQUEST` handler fires on any "speak to a human" phrasing and routes to Case Support as its default. It triggered even though the caller was already inside `PROSPECT STATUS CHECK`, which has its own local edge: *"if caller wants to speak with someone → TRANSFER - CARE TEAM"*. The global handler pre-empted the local edge.

## Proposed fix
Tighten the `GLOBAL - HUMAN REQUEST` transition condition so it does **not** fire when the current node already has its own "speak with someone" / human-request edge.
