# Alice Retainer — Phase 1 Agent Design Spec

**Status:** DRAFT for review · **Date:** 2026-08-18 · **Author:** Engineering (Impleko)
**Source requirements:** `Alice Retainer Build Requirements Aug. 2026.md` (§1–§7) + client's 5 add-on points (below)
**Grounded against:** `automations/outbound-post-call-workflows.md`, `automations/representation-agreement-messages.md`, `automations/lead-classification-flows.md`, `kb/knight-law-faqs.md`

---

## 0 · What this spec covers (and what it doesn't)

This is the engineering design for the **two new Retell agents only** (Phase 1). The GHL/Zapier orchestration and the intake-agent edits are **Phase 2**, specified here only at the boundary (contracts they must honor), to be built **after the client approves the two agents**.

| | Phase 1 — THIS BUILD | Phase 2 — after agent approval |
|---|---|---|
| Retell | Build **Agent A (Immediate)** + **Agent B (Outbound)**, shared KB, tools, post-call analysis fields, voicemail handling | Bind phone numbers / go live |
| GHL | — | 48h cadence workflow, **status-change removal** workflow, `send_agreement` receiver, voicemail dynamic-var injection |
| Zapier/SF | — (reuse existing) | Repair Notes already handled; status sync already handled |
| Intake agent | — | Routing edits 3a/3b/3c + updated handoff line (client point 4) |

**Nothing goes live in Phase 1.** The two agents are validated via Retell test calls / simulation with mocked dynamic variables. Live wiring (intake transfers for A, GHL dialer for B) is Phase 2.

### The 5 client add-on points → where each lands
1. **Read SF Lead Status; stop if not "HF Retainer Sent"** → Phase 2 GHL *removal* workflow (event-driven, not per-touch polling).
2. **After 48h, pass recording+transcript to SF "Repair Notes"** → Phase 2, already handled via existing Zapier.
3. **Inbound warm-transfer routing (3a/3b/3c)** → Phase 2 intake edit; **Agent A built now to receive it**.
4. **Updated post-send handoff line** → Phase 2 intake edit (done last).
5. **Agent can (re)send the agreement if never received** → Phase 1 `send_agreement` tool + Phase 2 GHL receiver.

---

## 1 · Architecture overview

Two **single-prompt** Retell agents. Single-prompt (not conversation-flow) because the retainer job is objection-driven and delivery-adaptive ("facts fixed, delivery flexible") — a node graph would fight that.

```
                          ┌─────────────────────────────────────┐
                          │   SHARED Retell Knowledge Base       │
                          │   (Rep-Agreement facts, §4 long-tail)│
                          └───────────────┬─────────────────────┘
                        attached to both  │
        ┌───────────────────────────────┐ │ ┌───────────────────────────────┐
        │  AGENT A — Immediate           │ │ │  AGENT B — Outbound Follow-Up  │
        │  (single-prompt)               │◄┘►│  (single-prompt)               │
        │  Trigger: warm transfer         │   │  Trigger: GHL dials per touch  │
        │   • immediate_handoff (§5.1)   │   │  Voicemail: detect ON →        │
        │   • inbound_return (point 3a)  │   │   leave passed VM script       │
        │  Flow A: proactive walkthrough │   │  Flow B: permission→diagnostic │
        └───────────────┬────────────────┘   └───────────────┬───────────────┘
                        │   both share: objection branches (§5.3),            │
                        │   close paths (§5.4), escalation (§6), §7           │
                        └───────────────────┬────────────────────────────────┘
                                            ▼
                        Post-call custom_analysis_data  →  (Phase 2) GHL reads
                        outcome → advance / stop cadence / handoff
```

**Shared body, different head.** The KB (§4), objection branches (§5.3), close paths (§5.4), identity/rules (§3), escalation (§6), and already-signed handling (§7) are **identical** across both agents. Only the **opener** differs. To prevent drift on legally-sensitive facts, the shared body is maintained as **one canonical block** pasted into both prompts, and the reactive long-tail facts live **once** in the shared Retell KB.

---

## 2 · Shared Knowledge Base (Retell KB, attached to both agents)

**Source:** build the KB document from the existing `kb/knight-law-faqs.md` → **"Representation Agreement - FAQs"** section (already matches §4 substance almost 1:1), supplemented with the §4 items it lacks (mileage-offset mechanics, 90-day hold, negative equity pre-suit, sanctions/arbitration/lien clauses, the 128×/$8M proof point, >90% success rate).

**Inline vs KB split:**
- **Inline in both prompts** (must be stated exactly, proactively): the buyback definition, manufacturer-paid fees, the 50/50 additional-damages rule, the mileage offset, and the **worked example** (see §4 decision below). These are the scripted core Alice leads with — too important for RAG.
- **In the shared KB** (reactive lookup when a lead asks): the long-tail clauses — lien, sanctions, arbitration, negative equity, refinancing, "using the vehicle," reimbursements, the ~90-day hold, the "you never send us money" edge case, proof points.

---

## 3 · Shared prompt body (identical in both agents)

1. **Identity & tone (§3):** Alice, Knight Law Group, attorney's assistant; professional, warm, confident, unhurried; bilingual EN/ES, **matches the lead's language** (`lead_language`). "Aggressive" = persistent/assumptive, never rushed or scolding.
2. **Absolute guardrails (§3, §6):**
   - **Never** guarantee/imply a specific dollar amount or outcome. Worked example always framed "for the sake of argument."
   - **Never** misstate the fee structure, mileage offset, or outcome expectations.
   - **AI disclosure:** if asked, answer honestly, reassure she can clarify the agreement, offer live transfer only if she genuinely can't help.
   - **Honor any stop request immediately** (not just the word "STOP") → emit opt-out (§8).
   - **One close attempt per resolved objection**; two unresolved in a row → offer warm transfer.
   - **Graceful exit:** lead declines + reconfirms once after a single value restatement → accept, end, log.
3. **Objection branches (§5.3)** — A "haven't read it/busy", B fee confusion, C mileage offset, D spouse/family review, E shopping-around/dealer-or-mfr offer. Verbatim guide scripts included; delivery adaptive, facts exact.
4. **Close paths (§5.4)** — 1 sign-on-call (target), 2 commitment-with-deadline, 3 warm transfer.
5. **Warm-transfer-now triggers (§6)** — legal advice / SOL, already-accepted or signed dealer/mfr offer, existing attorney or filed suit, factual dispute, distress/anger.
6. **Already-signed handling (§7)** — confirm, reassure, flag for human verification, do not argue/re-pitch → emit `already_signed`.

---

## 4 · Agent A — Immediate Retainer Walkthrough

**Modality:** single-prompt. **Direction:** inbound / warm-transfer target.

**Two entry triggers, selected by dynamic variable `entry_mode`:**
| `entry_mode` | Source (wired Phase 2) | Opener |
|---|---|---|
| `immediate_handoff` | Intake Alice transfers right after the lead qualifies, same call (§5.1) | *"Ok, I'm back — let me go through the most common questions we get about the representation agreement, so you know exactly what you're signing."* |
| `inbound_return` | Intake Alice detects **HF Retainer Sent** on an inbound call (point 3a) and transfers | *"Thanks for calling about your representation agreement — I can walk you through it and answer anything before you sign."* |

**Flow (both entry modes converge):** opener → proactive walkthrough of the 4 key points (buyback → manufacturer-paid fees → 50% on additional damages w/ worked example → mileage offset, brief) → *"That's the whole thing in a nutshell. What questions can I answer before I walk you through signing?"* → objection branches (§5.3) as needed → **Close Path 1** (sign on the call, stay on the line through submission).

**Dynamic variables in:** `first_name`, `lead_language`, `agreement_link`, `entry_mode`. (On transfer, intake passes these — Phase 2.)
**Tools:** `send_agreement`, `warm_transfer` (§7 tools).
**Post-call analysis out:** `retainer_outcome` + `Lead Status` (§8).

---

## 5 · Agent B — Outbound Follow-Up

**Modality:** single-prompt. **Direction:** outbound; **dialed by the GHL cadence per touch** (Phase 2), one invocation per call (Calls 1–5).

**Voicemail:** Retell **"detect voicemail"** enabled. On voicemail detection → leave the message passed in `voicemail_script` (GHL injects VM1–VM5 per touch), then end. On human answer → run the live flow.

**Live flow (§5.2):** Opener + permission (*"Hi, is this [name]? … this is Alice from Knight Law Group about your vehicle. Do you have two quick minutes?"*) → **Diagnostic question** (*"Was there anything in the agreement that gave you pause — or has it just been a busy week?"* — then stop and listen) → objection branch (concrete objection before "busy") → close path (1 sign-now / 2 deadline / 3 transfer).

Opener sub-cases: **not the client** (no case details, ask to pass a message, end), **bad time** (lock a specific time, end), **"I already signed"** → §7 handling.

**Dynamic variables in:** `first_name`, `lead_language`, `agreement_link`, `voicemail_script`, `call_number` (1–5, lets the final-attempt call soften/close differently per §2).
**Tools:** `send_agreement`, `warm_transfer`.
**Post-call analysis out:** `retainer_outcome` + `Lead Status` (§8), incl. `no_answer_voicemail_left`.

---

## 6 · Tools (Retell custom functions — both agents)

### `send_agreement` (client point 5)
- **When:** the lead says they never received / can't find the agreement, or asks to be re-sent the link.
- **Effect:** the Retell tool POSTs the contact details to a **GHL webhook you'll build** (Phase 2 receiver); that GHL workflow **re-sends the existing EN/ES retainer email + SMS** with the DocuSeal signing link (existing retainer-send path — not a new envelope).
- **Params (passed by the tool):** `full_name`, `phone`, `email`, `lead_language`, `contact_id` (if available).
- **DocuSeal links (reference):** EN `https://sign.knightlaw.com/d/JU6yZ9Utb5qpG3` · ES `https://sign.knightlaw.com/d/ES92PraGmTb2ym`.
- After sending, Alice confirms verbally and, if on a live call, offers to stay on while they open it → Close Path 1.

### `warm_transfer`
- **When:** Close Path 3 / any §6 warm-transfer-now trigger / two unresolved objections.
- **Effect:** warm transfer to a live person via the established intake process, using the **existing intake agent's EN/ES human-transfer destinations** (copied from the live intake flow so the numbers stay in sync — never re-typed).
- Emits `retainer_outcome = warm_transfer` in post-call.

*No separate `schedule_callback` tool.* Close Path 2 committed times are captured into the post-call analysis field `callback_datetime`; the GHL cadence reads it and schedules (Phase 2). Keeps the tool surface minimal.

---

## 7 · Post-call analysis contract (Phase 1 deliverable; Phase 2 GHL consumes)

Both agents emit Retell `call_analysis.custom_analysis_data` fields, mirroring the existing intake pattern (`Lead Status` is already the routing key GHL reads).

| Field | Type | Values / notes |
|---|---|---|
| `retainer_outcome` | enum | `signed_on_call` · `callback_scheduled` · `confirmed_decline` · `already_signed` · `warm_transfer` · `opt_out` · `no_answer_voicemail_left` (B only) · `not_client` · `bad_time` |
| `callback_datetime` | string | set when `callback_scheduled` (Close Path 2) |
| `objection_logged` | string | the concrete objection(s) raised, for human review at handoff |
| `Lead Status` | enum | **reuse existing plumbing** for the two shared exits: `Opt-Out Consent` (→ existing DND/Burnt-Lead flow) and `Human Requested` (→ existing human flow). Left unset otherwise so the retainer-specific `retainer_outcome` drives Phase 2. |

**Why both fields:** opt-out and human-requested already have working GHL/Zapier/SF handling keyed on `Lead Status` — reuse it. Retainer-specific outcomes (signed/callback/decline/already-signed) are new and drive the Phase 2 cadence via `retainer_outcome`.

---

## 8 · Stop conditions — who owns what (§2)

| Stop condition | Owner |
|---|---|
| Signed on the call | Agent emits `signed_on_call`; GHL stops cadence |
| Lead says already signed | Agent emits `already_signed` (flag for human verify, pause) |
| Opt-out / do-not-contact | Agent emits `Lead Status = Opt-Out Consent` → existing DND flow |
| Confirmed decline | Agent emits `confirmed_decline` |
| Warm transfer completed | Agent emits `warm_transfer` |
| **SF status leaves "HF Retainer Sent"** | **Phase 2 GHL removal workflow** (event-driven) — not the agent |
| **48h elapsed** | **Phase 2 GHL** → auto-handoff to intake |

Agent's job = **detect + flag** via post-call analysis. Cadence timing, TCPA 8a–9p PT windowing, and removal = **GHL** (agent never dials, so it owns none of the scheduling/compliance-hours logic).

---

## 9 · Decisions — resolved (2026-08-18)

1. ✅ **`send_agreement` = re-send existing email.** The Retell tool passes contact details to a GHL webhook **you will build**; that workflow re-sends the existing EN/ES retainer email + SMS link (not a new envelope). See §6.
2. ✅ **Worked example = the new doc's version:** **$50k vehicle → $100k settlement → client $75k (150%)** (§4/§5.3-B). Alice uses this consistently on calls; the KB FAQ's older $10k/$20k example is not used.
3. ✅ **Callback number = the Alice number, (213) 205-3651.** This is the Retell line for Knight Law's Alice (identified in `ghl-setup/incomplete-leads-followup.md` as the agent's number), so callbacks land back on Alice inbound — which (point 3a) can then warm-transfer HF-Retainer-Sent leads straight to Agent A. This **matches the client's requirements doc §2** (no conflict after all). Used in Phase 2 voicemail/SMS copy. Human warm-transfer uses the **existing EN/ES intake transfer numbers** (reused from the live intake flow).
4. ✅ **Reuse the existing `Lead Status` field** for the opt-out and human-requested exits. Retainer-specific outcomes use `retainer_outcome` (§7).

---

## 10 · Phase 2 handoff (deferred — after client approves the agents)

- **GHL 48h cadence** workflow: 10 touches (5 calls dial Agent B / 5 SMS), voicemail `voicemail_script` injection per call, TCPA windowing, `send_agreement` receiver.
- **Cadence copy numbers:** voicemail/SMS point callbacks to the **Alice number (213) 205-3651** (matches the requirements doc); human transfer uses the existing EN/ES intake numbers.
- **GHL status-change removal** workflow: on SF status leaving "HF Retainer Sent" (synced), remove contact from the cadence.
- **Intake agent edits** (last): inbound routing — HF Retainer Sent → transfer to Agent A (`entry_mode=inbound_return`); HF Appointment → human (as today); else → qualification. Plus update the post-send **handoff line** to the client's point-4 wording. Warm handoff from qualify → Agent A passes `entry_mode=immediate_handoff` + `first_name`/`lead_language`/`agreement_link`.

---

## 11 · Testing (Phase 1 — before client approval)

Reuse the existing `test-cases/` harness (Retell simulation). Cover:
- **Openers:** Agent A `immediate_handoff` vs `inbound_return`; Agent B live-answer vs voicemail-detected.
- **Objection branches A–E**, each → correct close path; fee/mileage facts stated exactly; worked example correct.
- **Close paths 1/2/3**; Close Path 2 sets `callback_datetime`.
- **`send_agreement`** fires on "never received it."
- **Escalation (§6)** triggers → `warm_transfer`.
- **§7 already-signed** → `already_signed`, no re-pitch.
- **Guardrails:** no guaranteed amounts; honest AI disclosure; immediate stop → `Opt-Out Consent`.
- **EN + ES** parity for each.

---

## 12 · Build order (once this spec is approved)

1. Assemble the **shared KB** doc → create Retell Knowledge Base.
2. Write the **shared prompt body** (identity, guardrails, KB core inline, objections, closes, escalation, §7).
3. Build **Agent A** (add Flow-A opener + `entry_mode` logic) + attach KB + tools.
4. Build **Agent B** (add Flow-B opener/diagnostic + voicemail handling + `call_number`) + attach KB + tools.
5. Configure **post-call analysis fields** (§7) on both.
6. **Simulation tests** (§11), EN + ES.
7. Package for **client approval** → then Phase 2.
