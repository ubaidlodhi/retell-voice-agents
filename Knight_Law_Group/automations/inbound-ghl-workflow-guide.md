# Knight Law — Inbound Post-Call GHL Workflow (build guide)

> **Goal:** a dedicated **"Inbound — Post Retell"** workflow that fixes the bugs seen in test-calls-01: returning Retainer/Non-Retainer leads being mislabeled **Incomplete** and dumped into the Incomplete follow-up, and their good intake fields getting overwritten with empties.
> **Approach:** **duplicate the existing outbound "Post Retell" workflow**, then make the changes below. Don't build from scratch — the branching, opportunities, and Zapier webhooks are already correct; we only add a front-gate, split the field update, and add tag guards.

---

## 1. The one golden rule

The Retell post-call webhook carries **two** data sets. Use the right one:

| Data set | Webhook path | When to trust it |
|---|---|---|
| **Seeded values** (from the pre-call lookup) | `inboundWebhookRequest.call.retell_llm_dynamic_variables.*` | **The truth for returning leads.** Always reliable — it's what we already knew about them. |
| **Fresh post-call analysis** (LLM judgment of *this* call) | `inboundWebhookRequest.call.call_analysis.custom_analysis_data.*` | Only trustworthy when intake **actually happened on this call** (a returning **Incomplete** lead who finished, or a brand-new caller). For a returning *completed* lead it's empty/garbage. |

**Decision:** if the **seeded** `lead_status` is already a finished status (Retainer / Non-Retainer / Bad / Opt-Out) → it's a **returning completed lead** → trust seeded, log the call, and **stop**. Only when seeded `lead_status` is `Incomplete Lead` or blank do we use the fresh analysis and run the full branching.

---

## 2. Prerequisites

- **Tags exist** (already created): `retainer-sent`, `non-retainer-followup`. ✅
- **Outbound workflow must STAMP those tags** on first completion (so a returning call can see them):
  - In the **outbound** "Post Retell": in the Retainer branch, after the Zapier webhook → **Add Tag `retainer-sent`**; in the Non-Retainer branch, after drip enrollment → **Add Tag `non-retainer-followup`**.
- **Inbound agent webhook → this workflow.** The inbound agent's post-call `webhook_url` is set (V04) to this workflow's Inbound Webhook trigger:
  `https://services.leadconnectorhq.com/hooks/vHHnJlFVorkeBvqgaqqA/webhook-trigger/yR9ujHBXMJBERxKN1Y9H`
  **Subscribe that webhook to the `call_analyzed` event ONLY** (not `call_started` / `call_ended`) so it fires once with full analysis + seeded variables.

---

## 3. Webhook field reference (copy these paths)

**Seeded (trust for returning leads) — `inboundWebhookRequest.call.retell_llm_dynamic_variables.<name>`:**

`lead_status`, `lead_language`, `salesforce_record_id`, `bad_lead_reason`, `contact_id`, `Name`, `Phone`, `Email`, `vehicle_year`, `vehicle_make`, `vehicle_model`, `ca_purchase`, `in_possession`, `purchase_new_used`, `is_cpo`, `purchase_condition`, `dealership_repair`, `is_owner`, `having_issues`, `prior_summary`, `num_calls_made`

**Fresh analysis (use only on the intake path) — `inboundWebhookRequest.call.call_analysis.custom_analysis_data.<Field>`:**

`Lead Status`, `Bad Lead Reason`, `Lead Language`, `Vehicle Year`, `Vehicle Make`, `Vehicle Model`, `Purchased In California`, `Still In Possession`, `Purchase Condition`, `Repairs Attempted`, `Is Owner`, `Full Name`, `Phone Number`, `Email Address`, `Call Summary`, `Call Successful`

> For **Transcript** and **Summary**, reuse the exact field references the **outbound** workflow already uses (they're proven) — don't re-derive them.

---

## 4. Build steps (duplicate outbound, then modify)

**Step 0 — Duplicate** the outbound "Post Retell" workflow → rename **"Inbound — Post Retell"**. Point its Inbound Webhook at the inbound agent (§2).

**Step 1 — Find Contact** *(keep)* — match by **Phone = `…retell_llm_dynamic_variables.Phone`** (seeded, already normalized). Inbound leads always pre-exist.
- **Contact Not Found → END.** Inbound **never creates** a lead (unlike outbound — delete the "Create Contact" path).

**Step 2 — Update Contact Field (SAFE, always)** — before the branch, update ONLY:
- `Lead Language`
- **Do NOT** write `Transcript of the Call` or `conversation_summary` here — those custom fields hold the **main / original qualifying call** and must be preserved across return calls. This call's transcript/summary is logged as a **Note** on the returning path (Step 4b), or written to the main-record fields only on a genuine qualifying call (Step 5).
- **Do NOT** write vehicle / CA / possession / Lead Status / Bad Lead Reason here either.

**Step 3 — Add Tag** *(keep)* — add `voice-inbound` (so inbound calls are distinguishable from outbound `voice`).

**Step 4 — NEW If/Else: "Did intake happen on this call?"**
- Condition (**ANY / OR**):
  - `…retell_llm_dynamic_variables.lead_status` **is** `Incomplete Lead`
  - `…retell_llm_dynamic_variables.lead_status` **is empty**
- **TRUE → Fresh-intake path** (Step 5).
- **FALSE → Returning completed → Step 4b → END.**

**Step 4b — [Returning path] Add Note, then END.** Append this call to the contact **timeline as a Note** (Notes append — they never overwrite the custom fields).

Note body (paste into the Add Note action):
```
📞 INBOUND RETURN CALL (not the original qualifying call)

Call type: {{inboundWebhookRequest.call.call_type}}
Ended:     {{inboundWebhookRequest.call.end_timestamp}}

──────────── SUMMARY ────────────
{{inboundWebhookRequest.call.call_analysis.call_summary}}

─────────── TRANSCRIPT ───────────
{{inboundWebhookRequest.call.transcript}}
```
> `end_timestamp` is **Unix epoch ms** — run it through a GHL Date/Time formatter first if you want a human-readable date.

Then **END.** No field overwrite, no status change, no enrollment, no opportunity, **no Incomplete follow-up** — and the **original Transcript / Summary custom fields stay intact.** *(Core fix + preserves the main call record.)*

**Step 5 — [Fresh path] Update Contact Field (INTAKE + main record)** — this is a genuine qualifying call, so it's correct to (re)write the main record:
- `Transcript of the Call` = `…call.transcript`, `conversation_summary` = `…custom_analysis_data.Call Summary`  ← the main/original call data is stored here, only on a qualifying call
- `Lead Status` = `…custom_analysis_data.Lead Status`
- `Bad Lead Reason`, Vehicle Year/Make/Model, CA, Possession, New/Used, CPO, Purchase Condition, Repairs, Owner = analysis values
- **Full Name / Phone / Email → prefer the SEEDED** `…retell_llm_dynamic_variables.Name/Phone/Email` (the analysis re-extracts these from speech and mangles them — e.g. the extra-digit phone in Call 01).

**Step 6 — [Fresh path] Branch by Lead Status** *(keep the existing If/Else)* — evaluates `…custom_analysis_data.Lead Status`:
- **Incomplete Lead** → Add to Followup Workflow *(keep)*.
- **Retainer Lead** → **tag-guarded** (Step 7a).
- **Non-Retainer Lead** → **tag-guarded** (Step 7b).
- **Bad Lead** → Zapier webhook + Create Opportunity (lost) + DND *(keep)*.
- **Opt-Out Consent** → Zapier webhook + Wait + Remove from all + DND *(keep)*.

---

## 5. Tag guards (Step 7) — stamp on first completion, skip if already done

### 7a. Retainer branch
- Wrap **Retainer Zapier Webhook + Create Opportunity** in an If/Else:
  - Condition: **Tags → does NOT have → `retainer-sent`**
  - **YES (first time):** Zapier webhook → Create Opportunity (won) → **Add Tag `retainer-sent`**.
  - **NO (already sent):** skip — **no second DocuSign envelope.**

### 7b. Non-Retainer branch
- Wrap **Add-to-Workflow (EN/ES drip) + Create Opportunity** in an If/Else:
  - Condition: **Tags → does NOT have → `non-retainer-followup`**
  - **YES (first time):** Lead Language branch → add to EN/ES drip → Create Opportunity → **Add Tag `non-retainer-followup`**.
  - **NO (already enrolled):** skip — **no duplicate booking-link drip.**

> The Zapier webhooks themselves are harmless to re-fire (they just re-stamp Salesforce); only the **DocuSign-triggering** retainer webhook and the **drip enrollment** must be gated.

---

## 6. Flow at a glance

```
Inbound Webhook (call_analyzed)
  → Find Contact (by seeded Phone)         [not found → END, never create]
  → Update SAFE field (Lead Language only)
  → Add Tag: voice-inbound
  → IF intake happened?  (seeded lead_status = Incomplete OR empty)
        FALSE → Add Note (this call's Summary+Transcript) → END   ← Transcript/Summary custom fields PRESERVED
        TRUE  ↓
          Update MAIN RECORD (Transcript+Summary) + INTAKE fields (Name/Phone/Email from seeded)
          Branch by analysis Lead Status:
            Incomplete   → Incomplete follow-up
            Retainer     → [no retainer-sent?] webhook + opp(won) + tag
            Non-Retainer → [no non-retainer-followup?] drip(EN/ES) + opp + tag
            Bad          → webhook + opp(lost) + DND
            Opt-Out      → webhook + wait + remove-all + DND
```

---

## 7. Test checklist (real-number calls)

- **Returning Retainer** (seeded `Retainer Lead`) → status **stays Retainer**, **not** added to Incomplete follow-up, vehicle fields **unchanged**, **Transcript/Summary custom fields unchanged**, a **new timeline Note** is added for this call, no second DocuSign.
- **Returning Non-Retainer** → same: stays Non-Retainer, no re-drip, fields intact, return call saved as a Note.
- **Incomplete → completes to Retainer** (seeded `Incomplete Lead`) → fresh path → retainer branch → DocuSign sent (first time) → `retainer-sent` stamped.
- **Returning Bad / Opt-Out** → logged only, status preserved.
- **Brand-new / not found** → END, no contact created.

---

## 8. Notes / future

- **Status source:** Step 6 branches on the call's **fresh** `Lead Status` (the LLM's judgment of this call). Inbound V02's reliable closings make that accurate. If we later add a deterministic **`final_lead_status`** dynamic variable at each agent terminal, switch Step 6 to branch on that for bulletproof accuracy.
- **Field overwrite confirmation:** this design sidesteps GHL's empty-overwrite behavior entirely by never writing intake fields on the returning-completed path — so it doesn't matter whether GHL clears on empty.
- Keep the outbound "Post Retell" workflow as-is **except** for the two tag-STAMP steps (§2).
