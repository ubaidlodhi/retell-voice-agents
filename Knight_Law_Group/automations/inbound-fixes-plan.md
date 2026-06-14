# Knight Law — Inbound Agent Fix Plan (from test-calls-01)

> **Status:** Plan only — **no implementation yet.**
> **Source:** 4 web test calls in [`test-cases/inbound/test-calls/test-calls-01.md`](../test-cases/inbound/test-calls/test-calls-01.md).
> **Builds on:** [`inbound-agent-plan.md`](inbound-agent-plan.md) (architecture) — this doc is the fix layer after first testing.

---

## 0. Test context (corrected)

The 4 calls were **web/text tests with manually-filled dynamic variables**. Two corrections to the first read:

- **The post-call webhook DID fire and reach GHL.** Web tests still emit `call_analyzed`, so the post-call workflow ran and wrote to the contact — which is how the **Incomplete-status bug was confirmed in GHL for real**: returning Retainer/Non-Retainer leads were labeled `Incomplete Lead` and landed in the **Incomplete follow-up workflow**. This is a **confirmed production bug**, not an analysis preview.
- **Time gating is handled by the Agent Handbook and works correctly.** It's genuinely after-hours, which is why every call correctly routed to **Book Callback** — **correct behavior, not an artifact.** The only leg a web test can't exercise is the **live in-hours warm transfer**; that still needs a real in-hours call.

So findings are **real agent bugs** (fix in flow) and **post-call/GHL design** (fix in the new inbound workflow). The earlier "test artifact" framing for the callback routing was wrong.

---

## 1. Locked decisions

| Decision | Choice |
|---|---|
| **Returning Retainer / Non-Retainer scope** | **Greet + reliable transfer only** — no FAQ/Q&A on these paths; greet, confirm who they are, route to transfer (live during hours, callback after). |
| **GHL inbound write-back** | **Dedicated inbound workflow** that trusts the **seeded** dynamic variables for returning leads (not the post-call LLM judgment). |

---

## 2. Findings → root causes

| # | Call(s) | Symptom | Root cause | Class |
|---|---|---|---|---|
| A | 01, 02, 03, 04 | Lead Status mislabeled (Retainer↔Non-Retainer, →Incomplete); vehicle/contact fields empty/0. **Confirmed in GHL:** returning leads landed in the Incomplete follow-up. | Post-call **Lead Status is an LLM re-judgment of the transcript**; returning/short calls have no intake in the transcript → defaults to Incomplete or misreads partial retainer questions, and re-extracts fields as empty | Post-call / GHL **(confirmed real)** |
| B | 03 | Returning caller asked to be transferred → got stuck (number + booking link instead) | `GLOBAL - Human Request` (inherited from outbound, which has no transfer) intercepts "connect me" and hands out the number/link — never reaches the Business Hours Gate. Also why a **Retainer wrongly got a consultation link**. | Agent |
| C | 03 | "No, thank you" → "we'll reach back out at a better time" + call ended | `GLOBAL - Stop / Busy` over-fires on a normal call-end, and its closing is an **outbound callback framing** wrong for an inbound caller | Agent |
| D | 01 | "Let's pick up right where we left off" to a missed-call lead who never spoke to Alice | Resume greeting assumes prior engagement; many "Incomplete" leads are no-answers with no intake data | Agent |
| D | 04 | "The next step is a consultation…" when they may have already booked | Greeting asserts a stale next-step | Agent |
| E | 01 | Non-Retainer closing never spoke before `end_call` | Relied on the end node's flaky `speak_during_execution`; also starved the post-call LLM of the distinguishing close (feeds A) | Agent |
| — | 01 | Behavior questioned ("should be non-retainer") was **actually correct** | Classify → retainer-track, then **"no repairs attempted" correctly diverts to Non-Retainer** (repairs are required for retainer). Working as designed; only the *label* + *closing* were wrong. | (not a bug) |
| — | 02, 04 | Booked callback instead of transferring | **Correct behavior** — genuinely after-hours; time gating via the Agent Handbook works. Live in-hours transfer just needs a real-call test. | Not a bug |
| — | 01 | Post-call phone `+142555295398` (extra digit); 04 phone/email blank | Post-call re-extracted contact info from speech instead of using seeded values | Post-call / GHL |

---

## 3. Agent-side fix plan (inbound flow → next version)

1. **Returning Retainer & Non-Retainer = greet + connect only.**
   - Retainer: warm greeting by name, "your case is with our team," → offer to connect → Business Hours Gate.
   - Non-Retainer: drop the stale "next step is a consultation" — neutral "how can I help, or shall I connect you with the team?" → Business Hours Gate.
   - No intake, no Q&A on these paths. *(D / 03#1 / 04#1)*

2. **Repurpose `GLOBAL - Human Request` (inbound only) → route to the Business Hours Gate.**
   - Any "I want a person / connect me," from anywhere → **live warm transfer during hours, callback after**. Stop handing out the number + consultation link. *(B / 03#2)*
   - Outbound agent's Human Request stays as-is (no transfer there).

3. **Closing must be intent-driven — never auto-fire on "no thanks / I'm done."**
   - A caller can say "No, thank you" or "I'm done" **mid-flow** without wanting to end the call. So these phrases must **never be a blanket close trigger.** `GLOBAL - Stop / Busy` currently over-fires on them.
   - Tighten it to only **explicit leave-now signals** ("I'm driving," "I have to go," "call me later") and remove the generic "no thanks / I'm good / I'm done" matches. End-of-call should be read from **actual closing intent in context**, via each node's own wrap-up edge — not a global phrase match. Drop the outbound "we'll reach back out at a better time" framing for inbound. *(C / 03#3)*

4. **Adaptive Incomplete greeting.**
   - No intake data seeded → greet fresh, start the questions (don't imply we spoke before). Recap only when details exist. *(D / 01#3)*

5. **Reliable closings via speak-then-end.**
   - Move terminal closings (esp. Non-Retainer) into a short speak node + `skip_response_edge` → bare end node, instead of the end node's flaky `speak_during_execution`. *(E / 01#2)*

6. **Deterministic `final_lead_status` at each terminal (recommended).**
   - Stamp the outcome deterministically so status never depends on the post-call LLM re-reading the transcript. This is what makes **Call 01 (Incomplete→Non-Retainer)** land correctly, and hardens both agents. Sent in the post-call webhook for GHL to consume. *(A)*

7. **FAQ note.** FAQ stays global for the **intake paths**; the returning-lead nodes push straight to transfer so it rarely engages there. *Option:* fully suppress FAQ for returning leads by scoping its condition — decide later.

> Versioning: ship as the next inbound version (V02) with an incrementing `V##` suffix in `agent_name`; validate with `validate_flow.py` before delivery.

---

## 4. GHL-side fix plan (new dedicated inbound workflow)

1. **New workflow** triggered by the **inbound agent's own post-call webhook** (see §5).
2. **Trust seeded truth.** Read `call.retell_llm_dynamic_variables.*` (same place the outbound workflow reads `Phone`).
   - Returning **Retainer / Non-Retainer / Bad / Opt-Out** → use **seeded `lead_status`** and **seeded vehicle/contact fields**; ignore the post-call analysis. *(A / 02 / 03 / 04 mislabels + field emptying)*
3. **Fresh analysis only when intake happened** — seeded status was `Incomplete Lead` or blank → use `final_lead_status` + freshly collected fields → branch/enroll like outbound.
4. **No re-enroll, no downgrade.** Returning completed calls only log transcript/summary + tag `voice-inbound`; never added to the Incomplete follow-up *(04#2)*; never re-trigger drips/DocuSign (existing `retainer-sent` / `non-retainer-followup` tag guards).
5. **No empty overwrites.** Never write empty post-call values over good intake data.

---

## 5. Wiring & testing

- **Inbound agent needs its own post-call `webhook_url`** → the new inbound workflow (the clone currently inherited the outbound URL). Change during build.
- **Subscribe the post-call webhook to the `call_analyzed` event only** (not `call_started` / `call_ended`) — so it fires once, with the complete analysis **and** the seeded dynamic variables, and doesn't double-trigger the workflow.
- **One real in-hours call still needed** to exercise the **live warm transfer** leg (web tests are after-hours → booking, which is correct). Test matrix: returning-Retainer (in-hours transfer + after-hours callback), returning-Non-Retainer, Incomplete-resume, missed-call Incomplete (no data), Bad re-check, Opt-Out, not-found.

---

## 6. Build sequence (when approved)

1. ✅ **DONE** — Agent-side flow edits shipped as inbound **V02** (validated 0/0). Changes 1–5 applied; deterministic `final_lead_status` (6) deferred to the GHL phase.
2. Build the new inbound GHL workflow (seeded-truth logic + tag guards).
3. Point the inbound agent's post-call `webhook_url` at the new workflow.
4. Real-number test matrix (§5); fix side-by-side.

---

## 7. Open / verify items

- **Transfer destination number** still a placeholder (`+13105522250` = main line stand-in) — replace with the real intake-transfer number.
- **Business hours via Agent Handbook** (confirmed working — after-hours → booking). At build, confirm whether the Handbook also covers **weekday** gating (Mon–Fri), or whether the Business Hours Gate equation still needs a weekday signal — and reconcile the two so they don't conflict.
- `final_lead_status` mechanism (small set-variable nodes at terminals) — confirm at build.
