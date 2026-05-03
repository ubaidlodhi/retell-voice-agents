# Team Member Request — AI Test Cases

Test scenarios for Aubrey's team-member-request flow (when a caller asks for a specific person by name), structured for automated AI simulation.

**Source spec:** `../call_team_members.md`
**Flow path (handle):** `OPENING` → `TEAM MEMBER REQUEST` → `CAREGIVER MENU` → [standard topic flow]
**Flow path (transfer):** `OPENING` → `TEAM MEMBER REQUEST` → `TRANSFER - [HEALTH COACH | ELIGIBILITY | PAYROLL | CARE TEAM | CASE SUPPORT]`

**Spec rules:**
- Do NOT immediately transfer — first collect details, attempt first-touch resolution
- Opening line: "Absolutely, I can help with that."
- Collect (one per turn): first/last name, phone, state, status (current caregiver / getting started / case manager / other)
- Purpose question (exact spec): "So we can help you faster, can you share briefly what this is regarding?"
- Forbidden phrases: "the nature of your call", "routing", "getting you to the right person"
- Decision: handle if matches capabilities; transfer if not; transfer immediately if caller pushes back

---

## TM-01 | Handle Path — Caller's Purpose Matches Aubrey's Capabilities

**Caller persona**
- New caller, no CRM data
- Name: Maria Johnson, phone: 555-100-2000, state: Arizona, status: current caregiver
- Asks for "Sarah" (a specific Keyline team member)
- Real purpose: missed clock-out yesterday

**Objective**
Caller asks for a specific person but their actual issue (missed clock-out) is something Aubrey can resolve. Aubrey collects details, asks purpose, offers help, and routes to CAREGIVER MENU when caller agrees.

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** I'd like to speak to Sarah on your team please.
- **Aubrey:** Absolutely, I can help with that. May I have your first and last name?
- **Tester:** Maria Johnson.
- **Aubrey:** And your phone number?
- **Tester:** 555-100-2000.
- **Aubrey:** And what state are you calling from?
- **Tester:** Arizona.
- **Aubrey:** Are you a current caregiver, getting started, or a case manager or another party?
- **Tester:** Current caregiver.
- **Aubrey:** So we can help you faster, can you share briefly what this is regarding?
- **Tester:** I missed my clock-out yesterday and I wanted to ask Sarah about it.
- **Aubrey:** I can help you with that. *(routes to CAREGIVER MENU)*
- *(continues into the missed clock-out flow → MCO collection → MCO SUBMIT → ticket → close)*

**Pass criteria**
- Opening line delivered verbatim: "Absolutely, I can help with that."
- All 4 collection fields asked one per turn (name, phone, state, status)
- Purpose question asked using the exact spec wording
- Aubrey responds "I can help you with that" when purpose matches
- Routes to CAREGIVER MENU (then standard MCO flow follows)
- Does NOT transfer to a live person on first request

**Must not**
- Skip the opening "Absolutely, I can help with that"
- Transfer immediately without collecting fields and offering help
- Use "the nature of your call" / "routing" / "getting you to the right person"
- Re-ask any field the caller already provided

---

## TM-02 | Transfer Path — Health Coach Specifically Requested

**Caller persona**
- New caller, no CRM data
- Name: Daniel Reyes, phone: 555-200-3000, state: Texas, status: current caregiver
- Asks for his health coach by name; purpose is wellness check-in (not in Aubrey's scope)

**Objective**
Caller wants their health coach for a wellness conversation — Aubrey can't fully replace that. Routes to TRANSFER - HEALTH COACH.

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** I want to talk to my health coach, her name is Lisa.
- **Aubrey:** Absolutely, I can help with that. May I have your first and last name?
- **Tester:** Daniel Reyes.
- **Aubrey:** And your phone number?
- **Tester:** 555-200-3000.
- **Aubrey:** And what state are you calling from?
- **Tester:** Texas.
- **Aubrey:** Are you a current caregiver, getting started, or a case manager or another party?
- **Tester:** Current caregiver.
- **Aubrey:** So we can help you faster, can you share briefly what this is regarding?
- **Tester:** I just want to do my regular check-in with Lisa about how my mom is doing.
- **Aubrey:** Got it — let me connect you. Please hold.
- *(routes to TRANSFER - HEALTH COACH)*

**Pass criteria**
- Routes specifically to TRANSFER - HEALTH COACH (not generic case support)
- Reaches transfer only AFTER collecting all 4 fields and asking purpose
- Caller's captured info is preserved in conversation history for the live agent

**Must not**
- Route to CASE SUPPORT (that's the wrong department)
- Transfer before collecting fields
- Try to handle the wellness check-in itself

---

## TM-03 | Transfer Path — Payroll Team Requested

**Caller persona**
- New caller, no CRM data
- Name: James Carter, phone: 555-300-4000, state: California, status: current caregiver
- Asks for "Mike from payroll"; purpose is a specific paycheck question

**Objective**
Caller wants payroll specifically. Routes to TRANSFER - PAYROLL TEAM.

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** Can I talk to Mike from payroll?
- **Aubrey:** Absolutely, I can help with that. May I have your first and last name?
- **Tester:** James Carter.
- **Aubrey:** And your phone number?
- **Tester:** 555-300-4000.
- **Aubrey:** And what state are you calling from?
- **Tester:** California.
- **Aubrey:** Are you a current caregiver, getting started, or a case manager or another party?
- **Tester:** Current caregiver.
- **Aubrey:** So we can help you faster, can you share briefly what this is regarding?
- **Tester:** I have a question about a deduction on my last paycheck — Mike usually handles it for me.
- **Aubrey:** Got it — let me connect you. Please hold.
- *(routes to TRANSFER - PAYROLL TEAM)*

**Pass criteria**
- Routes to TRANSFER - PAYROLL TEAM specifically
- Aubrey did NOT attempt to answer the deduction question (no fabrication)
- All 4 fields collected before transfer

**Must not**
- Route to CASE SUPPORT
- Fabricate an answer about deductions
- Skip the purpose question

---

## TM-04 | Push-Back Path — Caller Insists After Offer to Help

**Caller persona**
- New caller, no CRM data
- Name: Linda Hayes, phone: 555-400-5000, state: Florida, status: current caregiver
- Asks for her case manager Anna; purpose looks resolvable but caller insists on Anna

**Objective**
Aubrey offers to help, caller pushes back insisting on the specific person. Per spec, transfer immediately — don't argue or loop.

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** I need to speak with Anna, she's my case manager.
- **Aubrey:** Absolutely, I can help with that. May I have your first and last name?
- **Tester:** Linda Hayes.
- **Aubrey:** And your phone number?
- **Tester:** 555-400-5000.
- **Aubrey:** And what state are you calling from?
- **Tester:** Florida.
- **Aubrey:** Are you a current caregiver, getting started, or a case manager or another party?
- **Tester:** Current caregiver.
- **Aubrey:** So we can help you faster, can you share briefly what this is regarding?
- **Tester:** I need to update my address.
- **Aubrey:** I can help you with that.
- **Tester:** No, I really just want to talk to Anna directly.
- **Aubrey:** Got it — let me connect you. Please hold.
- *(routes to TRANSFER - CASE SUPPORT)*

**Pass criteria**
- Aubrey offered help once ("I can help you with that")
- After caller insists, Aubrey transfers immediately — does NOT keep insisting
- Transfer destination: TRANSFER - CASE SUPPORT (default when no specific team mentioned)

**Must not**
- Argue back after caller insists
- Loop — re-offer help a second time
- Continue collecting more fields after the insist
- Try to start the address-update flow after caller said no

---

## TM-05 | Out of Scope — Generic Team Member, Legal Question

**Caller persona**
- New caller, no CRM data
- Name: Sarah Kim, phone: 555-500-6000, state: Nevada, status: current caregiver
- Asks for "John from the office"; purpose is a contract question (out of Aubrey's scope)

**Objective**
Caller's purpose is genuinely outside Aubrey's capabilities. Aubrey transfers without offering false help.

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** Can you put me through to John in the office?
- **Aubrey:** Absolutely, I can help with that. May I have your first and last name?
- **Tester:** Sarah Kim.
- **Aubrey:** And your phone number?
- **Tester:** 555-500-6000.
- **Aubrey:** And what state are you calling from?
- **Tester:** Nevada.
- **Aubrey:** Are you a current caregiver, getting started, or a case manager or another party?
- **Tester:** Current caregiver.
- **Aubrey:** So we can help you faster, can you share briefly what this is regarding?
- **Tester:** I have a question about the contract terms in my caregiver agreement.
- **Aubrey:** Got it — let me connect you. Please hold.
- *(routes to TRANSFER - CASE SUPPORT)*

**Pass criteria**
- Aubrey did NOT say "I can help you with that" — purpose is genuinely out of scope
- Aubrey did NOT attempt to interpret or answer the contract question (no fabrication)
- Routes to TRANSFER - CASE SUPPORT (default for generic team member + out of scope)

**Must not**
- Offer to help with contract terms
- Fabricate any contract details
- Re-ask any field

---

## TM-06 | Returning Caller — CRM Pre-Filled

**Caller persona**
- Returning caller
- CRM injected: `caller_name = "Maria Johnson"`, `caller_state = "Arizona"`, `is_returning_caller = "true"`
- Asks for her case manager; purpose: pay stubs question

**Objective**
Aubrey confirms CRM-injected fields instead of asking fresh. Phone still asked because not in CRM. Purpose matches Aubrey's capabilities → handles.

**Dialog**
- **Aubrey:** Hi Maria, welcome back. How can I support you today?
- **Tester:** Hi! I'd like to talk to my case manager Anna.
- **Aubrey:** Absolutely, I can help with that. Just to confirm — that's Maria Johnson, right?
- **Tester:** Yes.
- **Aubrey:** And the best phone number to reach you?
- **Tester:** 555-100-2000.
- **Aubrey:** I've got your state as Arizona — is that right?
- **Tester:** Yes.
- **Aubrey:** Are you a current caregiver, getting started, or a case manager or another party?
- **Tester:** Current caregiver.
- **Aubrey:** So we can help you faster, can you share briefly what this is regarding?
- **Tester:** I just need a copy of my last pay stub.
- **Aubrey:** I can help you with that. *(routes to CAREGIVER MENU → PAY STUBS flow)*

**Pass criteria**
- Greeting uses caller name from CRM ("Hi Maria, welcome back")
- Confirms name once, doesn't re-ask from scratch
- Confirms state from CRM, doesn't re-ask from scratch
- Phone still asked (not in CRM)
- Routes to CAREGIVER MENU when purpose matches capability

**Must not**
- Ask "May I have your first and last name?" when CRM has it
- Speak the literal "{{caller_name}}" template syntax
- Skip the status or purpose question

---

## TM-07 | Distress Escalation Mid-Flow

**Caller persona**
- New caller, no CRM data
- Name: Linda Hayes
- Asks for someone, breaks down emotionally mid-collection

**Objective**
Verify GLOBAL - DISTRESS fires from inside TEAM MEMBER REQUEST and routes to live transfer. Collection is abandoned.

**Dialog**
- **Aubrey:** Hi, this is Aubrey with Keyline Home Care. How can I support you today?
- **Tester:** I really need to talk to Anna please.
- **Aubrey:** Absolutely, I can help with that. May I have your first and last name?
- **Tester:** Linda — I'm sorry, I just can't deal with this right now, I don't know what to do.
- **Aubrey:** *(GLOBAL - DISTRESS)* I'm so sorry you're going through this. I want to make sure you get the right support right away.
- **Aubrey:** I'm going to connect you with someone from our team now. Please hold.
- **[Live transfer to Care Team]**

**Pass criteria**
- GLOBAL - DISTRESS triggers on emotional distress signal
- Empathetic acknowledgment delivered before transfer
- Live transfer to Care Team executes
- Team-member intake fully abandoned — no further field collection

**Must not**
- Continue collecting fields after distress is detected
- Try to resolve the issue itself
- Confuse this for fatality (fatality is callback-only, no live transfer)

---

## Coverage Summary

| Case | Path | Specific Team | Tests |
|------|------|---------------|-------|
| TM-01 | Handle | n/a | Handle path → CAREGIVER MENU when purpose matches |
| TM-02 | Transfer | Health Coach | Specific-team routing for wellness check |
| TM-03 | Transfer | Payroll | Specific-team routing for paycheck question |
| TM-04 | Transfer (push-back) | Case Support | Caller insists after one offer → immediate transfer |
| TM-05 | Transfer (out of scope) | Case Support | Genuinely out-of-scope purpose → no false help |
| TM-06 | Handle (returning caller) | n/a | CRM-injected name + state confirmed once |
| TM-07 | — | — | Distress escalation (global) |

## Universal Guardrails (must pass in every test)

1. **Opening line** — "Absolutely, I can help with that." delivered verbatim before collecting anything
2. **One question per turn** — never combine fields
3. **4 fields collected** — first/last name, phone, state, status (skip if on file via CRM)
4. **Purpose question** — exact spec wording: "So we can help you faster, can you share briefly what this is regarding?"
5. **Forbidden phrases** — never say "the nature of your call", "routing", or "getting you to the right person"
6. **No immediate transfer on first request** — at minimum, collect 4 fields and ask purpose first
7. **Push-back rule** — after one offer to help, if caller still insists on the specific person, transfer immediately (no looping or arguing)
8. **No fabrication** — for purposes Aubrey cannot actually resolve, transfer rather than invent answers
9. **Specific team routing** — health coach / eligibility / payroll / care team / case support based on which department the caller named (case support is the default)
10. **No re-asking** — never re-ask a field already provided

**Out of scope for this file** (covered in shared global-flow tests): fatality escalation, FAQ interruption, topic-change mid-flow.
