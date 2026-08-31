# Alice Retainer — Objection Register

Single source of truth for every objection, hesitation, and pushback Alice Retainer can meet, and where each one is answered. Both retainer agents (Immediate + Outbound) share this list.

Two places an objection can be handled:
- **Prompt** — a scripted branch inside both agent prompts (`alice-retainer-immediate-v01.md`, `alice-retainer-outbound-v01.md`). Used for the objections that actually block signing.
- **KB** — a reactive fact Alice pulls from the shared Retell knowledge base (`Knight Law - Retainer KB` = `kb_faqs.txt` + `kb_supp.txt`). Used for the long tail.

Escalation always outranks both: anything in §4 stops the pitch and warm-transfers.

---

## 1 · Scripted objection branches (client doc §5.3)

These are the five that carry a written script in both prompts. One genuine close attempt per objection resolved; two unresolved in a row → offer the warm transfer.

| ID | Objection | Core answer | Then |
|----|-----------|-------------|------|
| **A** | "Haven't read it / been busy" | Not a real objection — the task fell down their list. Shrink it: the whole thing takes ~2 minutes, and it's the buyback + manufacturer-paid fees + the split above the buyback. Offer to stay on while they open it. | Yes → Close Path 1. Later → Close Path 2. |
| **B** | Fee confusion — "What does this cost me?" | Fees and costs are paid by the **manufacturer**, not the client; the client never gets a bill. Hourly rates are listed purely for transparency. If they ask about the 50%: it applies **only** to additional damages (money above the buyback) — use the worked example. | Confirm understanding → Close Path 1. |
| **C** | Mileage offset — "Why don't I get everything back?" | Statutory, written into the lemon law, applies to every buyback at every firm. Fixed — it does not grow while the case is pending. The buyback is only part of the recovery; typical clients still end up above 100%. | Close Path 1. |
| **D** | "My spouse / family needs to review it" | Legitimate — don't fight it. Name the two parts people actually ask about (fees, the split), offer to join a call with both of them, and control the timeline. | Joint call → schedule. Otherwise Close Path 2 with a specific time locked. |
| **E** | Shopping around / dealer or manufacturer offer | Never disparage. **Another firm:** this is all we do; typical client walks away with >100%, often closer to 200%. **Dealer trade-in / direct mfr offer:** a trade-in rolls the problem into a new loan; the dealer works for the dealership; a direct manufacturer offer has nobody checking it includes finance charges, taxes, and fees. | Close Path 1; hesitant → Close Path 3. **Already accepted or signed with them → stop pitching, warm-transfer (§4).** |

**Ordering rule:** handle the concrete objection before the vague one (fees before "I've been busy").

---

## 2 · Reactive objections answered from the KB

No scripted branch — Alice answers from the knowledge base and returns to the close. These are questions that read as objections but are really requests for reassurance.

**Agreement clauses**
- Why hourly rates are listed at all — transparency; the manufacturer is required to pay them; fees may exceed the client's recovery, which is exactly why they're itemized.
- The **lien clause** — only bites if the client substitutes in another firm; Knight Law files a lien to recover fees, costs, and time invested to that point.
- **Sanctions** — court penalties for disobeying a rule or order. If the firm is sanctioned, the firm pays, never the client.
- The **arbitration clause** — governs disputes between client and firm, not the case itself.
- The additional-damages percentage is **fixed and non-negotiable**.

**Cost, risk & recovery**
- "So I might have to send you money?" → **"You never send us money."** The single edge case (a settlement with no fee provision that the client accepts) has never happened.
- "What if we lose?" → the firm absorbs the costs; the client owes nothing.
- "Why do you take a percentage at all?" → it's the incentive to pursue money above the buyback; other firms waive it because they don't pursue additional damages. Additional damages also hold manufacturers accountable.
- "Are you sure you'll win?" → there is always some risk; the firm only takes cases it believes it can win, success rate over 90%, and in practice these settle. Proof point: largest result ~128× purchase price of a Ford Super Duty, over $8M — **proof point, never a promise**.
- Reimbursements — tows, a hotel after being stranded, out-of-warranty repairs tied to the defect, a rental during a warranty repair.
- **Negative equity** — pre-litigation the manufacturer may only deduct the mileage offset and non-manufacturer dealer-installed items, so negative equity can't shrink a pre-suit offer.
- Can I keep driving it? → yes, the case moves either way, but minimize mileage; the vehicle is the evidence.
- Can I refinance? → yes, fine during the lawsuit.
- Why the ~90-day hold before filing? → deliberate strategy by the managing partner, not a delay to worry about.
- **Will I have to pay taxes on my settlement?** → *(client addition, Aug 2026)* Not tax professionals; can't advise on tax treatment; depends on individual circumstances; recommend a tax advisor or CPA.

**Process / timeline pushback**
- "18–24 months is too long" → most participation is early; after filing it's largely waiting; ~99% settle before trial.
- "What will I actually have to do?" → depositions (prepped and accompanied by a firm attorney), interrogatories, a vehicle inspection (the firm's expert picks up and returns the vehicle), rare court hearings.
- "Five pages is a lot" → only two short sections matter to most people: **actual damages** (the buyback) and **manufacturer-paid fees**.

---

## 3 · Situational objections at the opener

Handled inline in the prompt, not via a branch.

| Situation | Handling |
|-----------|----------|
| **Not the client / wrong person** | No case details. "I'll try back — could you let them know Alice from Knight Law Group called?" End. |
| **Bad time** | "When's a better time today or tomorrow?" Lock a specific time, then end. |
| **"I already signed it"** | Do not argue or re-pitch. "Let me confirm on our end — if it doesn't show in the next hour I'll text the link again." End warmly; flag for human verification and pause the cadence. |
| **Never received it / can't find the link** | Use `send_agreement` to re-send, then move to Close Path 1. |
| **"Are you an AI?"** | Answer honestly, never deny. Reassure that Alice can clarify the agreement herself; offer a transfer only if genuinely unable to help. |
| **Automated pickup (IVR, call screening, "please hold")** | Not an objection and not a person. Stay silent (`NO_RESPONSE_NEEDED`) and keep waiting. Never say goodbye, never `end_call`. |
| **Stop / do-not-contact** | Honor immediately — any clear sign, not just the word "stop." Acknowledge respectfully, end, and log it. |

---

## 4 · Objections Alice must NOT handle — warm-transfer now

These override every branch above. Stop pitching and transfer (`warm_transfer_english` / `warm_transfer_spanish`).

- Requests for legal advice, or statute-of-limitations / deadline concerns.
- An **already-accepted** dealer or manufacturer offer, or anything already signed with them.
- An existing attorney representing them, or a lawsuit already filed.
- Disputes over something factual.
- Real distress or anger.
- **Two unresolved objections in a row** — offer the transfer instead of a third push.

---

## 5 · Coverage check

| Source | Count | Status |
|--------|-------|--------|
| Client doc §5.3 branches | 5 (A–E) | ✅ all present in both prompts |
| Client doc §4 clauses | 5 | ✅ in `kb_supp.txt` |
| Client doc §4 cost/risk quick answers | 10 | ✅ in `kb_supp.txt` |
| Client doc §6 escalation triggers | 5 | ✅ in both prompts |
| Client doc §7 already-signed | 1 | ✅ in both prompts |
| Client additions (Aug 2026) | 1 (taxes) | ✅ in `kb_supp.txt` |

**Adding a new objection:** if it blocks signing → new scripted branch in both prompts + a row in §1 here. If it's a reassurance question → add to `alice-retainer-kb-supplement.md`, re-upload `kb_supp.txt` to the Retell KB, and add a bullet in §2 here. Never edit `kb/knight-law-faqs.md` — that file is the client's original document and is kept byte-identical.
