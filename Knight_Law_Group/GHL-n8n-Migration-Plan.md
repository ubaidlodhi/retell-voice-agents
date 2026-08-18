# Knight Law Group — GHL + n8n Migration Plan

**Scope:** Migrate the GoHighLevel account and the n8n instance to new ones. **Retell stays on the same account** (only its webhook *targets* change). Downstream systems affected: Zapier, Salesforce, DocuSeal, and the LC Phone / SMS number.

**Prepared:** July 2026 · **Goal:** zero real downtime (parallel build + instant cutover); the downtime figures below are the worst-case fallback if parallel run fails.

---

## 0 · The one decision that changes everything

There are two fundamentally different ways to do this. Pick the strategy first — the rest of the runbook follows from it.

| | **Strategy A — Native Sub-Account Transfer** | **Strategy B — Snapshot + CSV Rebuild** *(this plan's default)* |
|---|---|---|
| **What it is** | GHL "Eject to new agency" / "Bulk transfer" — moves the **actual location** to the new agency | Build a **fresh sub-account** from a snapshot, migrate contacts by CSV, re-wire integrations, cut over |
| **Contacts + appointments + opportunities** | ✅ Move automatically | ❌ Contacts by CSV; appointments don't come across |
| **Conversation history (SMS/email/chat threads)** | ✅ Move automatically | ⚠️ Not via CSV — only via a scripted **API rebuild** with original timestamps (§3.6) |
| **In-flight workflow enrollment (the hard part)** | ✅ Preserved ("contacts remain in the workflow") | ❌ Lost — must be **reconstructed** (see §4.3) |
| **Phone number + A2P 10DLC** | ✅ Move automatically **if both agencies use LC Phone** | ❌ Provision new number + **re-register A2P** (days–weeks lead time) |
| **Custom field *values*** | ✅ Preserved | ⚠️ Only via mapped CSV columns |
| **Parallel run / test-before-flip** | ❌ One-way live move, no parallel | ✅ Full parallel build + test, old stays as fallback |
| **Integrations (n8n, Zapier, Salesforce, Stripe, Google/FB)** | ❌ **All disconnect** — must reconnect | ❌ Rebuilt deliberately (same effort, but planned) |
| **Workflows after move** | ⚠️ Reset to **Draft** — must re-publish | ✅ Come in from snapshot, publish when ready |
| **Best when** | New GHL is a **different agency taking ownership**, and you can tolerate a short reconnection window | New GHL is a **fresh build**, you need **zero downtime**, or you want a tested cutover |

> **Recommendation:** If the destination is a **different agency** and the objective is to move the existing live account wholesale, **Strategy A** is dramatically safer for the follow-up cadences and the SMS number — it preserves in-flight enrollment and A2P automatically. Reconnect n8n/Zapier/Salesforce right after the move.
> If you're **rebuilding into a fresh sub-account** (or must run old + new side-by-side to guarantee no downtime), use **Strategy B** — the detailed runbook below. It is the harder path precisely because in-flight follow-ups and the number/A2P don't carry, so those get dedicated sections.

**→ CONFIRM before starting: same agency or different? New sub-account or account takeover? Does the destination use LC Phone (so the number + A2P can move)?**

---

## 1 · Systems inventory (build this first, on the OLD account)

Nothing moves cleanly until every moving part is cataloged. Produce a spreadsheet with these tabs:

**GHL**
- Custom **fields** (contact, opportunity, conversation) — name, type, and **current field ID** (IDs change in the new account!)
- Custom **values**
- **Tags** (full list + counts)
- **Pipelines** + stages (+ IDs)
- **Workflows / automations** (which are active, which drive outbound calls/SMS)
- **Calendars**, forms, funnels/websites, trigger links, email/SMS templates
- **Conversation AI** bot(s) + knowledge base / FAQs
- **Phone number(s)** (LC Phone), A2P 10DLC brand + campaign registration
- **Users** + permissions
- Sub-account **API keys** / OAuth apps in use

**n8n**
- Every **workflow** (export JSON) — flag which have **Webhook trigger** nodes (their URLs will change)
- Every **credential** (name, type) — secrets do **not** export
- The **encryption key** location (`~/.n8n/config` or `N8N_ENCRYPTION_KEY` env)
- The Knight Law **post-call workflow** (`L1oNbhjnF9czixEH`) and its GHL node mappings (field IDs, pipeline IDs)

**External callers/consumers to re-point**
- **Retell** agents (inbound + outbound "Alice"): pre-call caller-lookup webhook, custom-function webhooks, post-call webhook
- **Zapier** zaps that call n8n or GHL
- **Salesforce** integration (GHL→SF status push / n8n→SF)
- **DocuSeal** submission webhooks (retainer follow-up)

---

## 2 · Target architecture / data-flow map

```
                         (UNCHANGED account)
   Caller ──► Retell "Alice" (inbound/outbound) ──► webhook ──► n8n (NEW host)
                                                                   │
                        pre-call caller lookup ◄──────────────────┤
                                                                   ▼
                                                     GHL (NEW account) ──► Salesforce
                                                                   ▲
   DocuSeal (signature webhook) ─────────────────────────────────┘
   Zapier zaps ──────────────► n8n (NEW host) / GHL (NEW account)
```

Every arrow that touches **n8n** or **GHL** gets a new URL/credential at cutover. Retell's own account/numbers do not change — only the URLs it calls.

---

## 3 · GHL migration (Strategy B — snapshot rebuild)

### 3.1 · Build the snapshot (structure only)
On the old account, create a snapshot and **select every asset type**:

- ☑ Workflows / automations ☑ Triggers ☑ Pipelines + stages
- ☑ Custom fields ☑ Custom values ☑ Tags
- ☑ Calendars ☑ Forms / surveys ☑ Funnels / websites
- ☑ Email & SMS templates ☑ Trigger links ☑ Products
- ☑ **Conversation AI** bot (now snapshot-supported — carries prompts, actions, workflows, and KB/FAQs; see §3.4)

> **Snapshot does NOT include:** contacts, conversation history, appointments, custom-field **values**, LC Phone numbers, A2P registration, integration credentials, domains, or smartlists. Plan each of those separately (§3.2–3.5).

Deploy the snapshot into the new sub-account. **Then re-capture every ID** — new field IDs, pipeline IDs, stage IDs, custom-value IDs all differ from the old account. This ID table feeds the n8n remap in §5.

### 3.2 · Contacts migration
1. **Export** contacts from old GHL to CSV — include tags, all custom-field values, `Contact ID`, pipeline stage, opportunity status, DND flags, and the **cadence anchor date(s)** (e.g. `agreement_sent`).
2. **Map** columns to the new account's field names on import (types must match; dropdown options must exist).
3. **Import in batches**, spot-check the first batch before proceeding.
4. **Preserve DND / opt-out state** — re-import the "do not contact / opt-out" flags so you never text or call someone who opted out. This is a compliance must, not a nice-to-have.
5. **Pause all outbound workflows** on the new account before importing, so the import itself doesn't fire calls/SMS.

### 3.3 · In-flight follow-ups — identify & re-hydrate (the critical part)
Snapshots/CSV do **not** carry "which contact is at which step of which workflow." Reconstruct it deterministically:

**Step 1 — Identify who's mid-cadence (on OLD account):**
- The Knight Law cadences are **anchored to a date field** (e.g. agreement-sent time, last-call time). Use Smart Lists to find in-flight contacts by state, e.g. *status = HF Retainer Sent AND not signed AND `agreement_sent` within the cadence window*.
- Where a state isn't obvious from a field, **stamp it before export**: run a one-time workflow/bulk action that applies a tag like `mig:retainer-followup` and writes `mig_anchor_date` = the enrollment/anchor timestamp onto every currently-enrolled contact. Tags + a date field become your portable source of truth.

**Step 2 — Carry the state across:** include `mig:*` tags and `mig_anchor_date` in the CSV.

**Step 3 — Re-enroll on NEW account:** build a one-time **re-hydration workflow** that triggers on `mig:*` tags and enrolls each contact into the correct cadence, using **Wait-until anchored to `mig_anchor_date`** (or a math step computing elapsed time) so a lead 30 hours into a 48-hour cadence resumes at ~30 hours, not from zero.

**Step 4 — Freeze the old account's outbound** the moment you export the in-flight set, so a lead can't get touched by both systems (double-call/double-text). Only one system sends at a time — see cutover §6.

> If in-flight fidelity matters more than a clean rebuild, this is the single strongest argument for **Strategy A** (native transfer preserves enrollment automatically).

### 3.4 · Conversation AI
Use GHL's **Conversation AI snapshot** support: it clones the bot's prompts, actions, linked workflows, and the knowledge base / FAQs (everything except the assigned business name). After deploy, set the business name and resolve any bot-name conflict in the new account.

### 3.5 · Phone number + A2P 10DLC (longest lead time — start FIRST)
- **If moving to a different agency that uses LC Phone (Strategy A):** the number + A2P registration move automatically. Nothing to rebuild.
- **If rebuilding (Strategy B):** you must either **port** the existing number into the new account (keeps the number identity; schedule a porting window) **or provision a new number and re-register A2P 10DLC** (brand + campaign approval takes **days to weeks**). Either way this is the **critical path** — kick it off before anything else. A new, unregistered number **cannot send SMS** until approved, and the callback number `(213) 205-3651` in the agents/voicemails must match whatever the final number is.

### 3.6 · Conversation history (SMS / email / chat threads)
**There is no native one-click conversation export/import** (it's an open GHL feature request), and CSV contact import does **not** carry messages. Two options:

- **Strategy A (native transfer):** conversation history moves automatically — nothing to do.
- **Strategy B (rebuild):** migrate programmatically via the **Conversations API**:
  1. **Export** each thread from the old account (search conversations → get messages), or use a third-party export tool (CSV/JSON).
  2. **Map** every old `contactId` → new `contactId` (the CSV import creates new IDs).
  3. **Re-inject** via the **Add Inbound Message API** — it accepts `contactId`, `channel` (sms/email/whatsapp/messenger/instagram/webchat), `content` + **attachments**, and **`metadata.timestamp`** so messages keep their **original date and thread order**.

**Caveats:** it's a scripted, message-by-message job; **rate limits** apply (handle `429` with backoff on bulk); only the **inbound** endpoint is clearly documented — **outbound** (agent-sent) messages re-inject less cleanly and may need the older conversation-ID pattern or will render as inbound. If full history fidelity matters, this effort is itself a reason to prefer **Strategy A**.

---

## 4 · n8n migration

### 4.1 · Credentials — decide the key strategy up front
Exported workflow JSON **excludes secrets**. Two clean options:

- **Preserve the encryption key (recommended if self-hosted):** set `N8N_ENCRYPTION_KEY` on the new host to the **old value** (from old `~/.n8n/config`) *before* importing the DB/credentials, so credentials decrypt intact — no manual re-entry.
- **Export decrypted, re-import:** `n8n export:credentials --all --decrypted` on the old host, import on the new host (re-encrypts under the new key). Cleaner, no key surgery, but the decrypted file is sensitive — handle and delete carefully.

Whichever you pick, **keep credential names identical** so workflow references resolve.

### 4.2 · Workflows
- Export all: `n8n export:workflow --all` (or per-workflow JSON). Import into the new instance.
- **Do not activate yet.** Import inactive; activate one at a time at cutover, starting with the post-call workflow.

### 4.3 · Webhook URLs change — this is the main re-wiring
Every **Webhook trigger** node gets a new production URL (new host). After import, list each webhook URL and update it in **every external caller**:

| Caller | What to update |
|---|---|
| **Retell** (inbound Alice) | pre-call caller-lookup webhook → new n8n URL |
| **Retell** (both agents) | custom-function + **post-call** webhook → new n8n URL |
| **GHL** workflows | any "Custom Webhook / HTTP POST to n8n" action → new n8n URL |
| **Zapier** | any zap posting to n8n → new n8n URL |
| **DocuSeal** | submission webhook → new n8n (or GHL) URL |

> Keep the **webhook path** identical where possible so only the host differs — smaller change surface.

### 4.4 · Re-point the GHL nodes in n8n (easy to miss)
The post-call workflow (`L1oNbhjnF9czixEH`) and any other GHL-touching workflow must be updated for the **new** account:
- New **GHL credential** (new location API key / OAuth) + new **Location ID**.
- Remap every hardcoded **field ID, pipeline ID, stage ID, custom-value ID** to the new account's IDs (from §3.1). *Mappings by ID will silently write to the wrong/no field if not remapped.*
- Re-verify the **Log External Call** node (Direction + contact phone mapping) and Create/Update Contact against the new field IDs.
- **Salesforce** nodes: same SF account — credential likely unchanged, but re-test the status mapping end-to-end.

---

## 5 · Integration re-wiring checklist (cutover-day)

- ☐ Retell inbound caller-lookup webhook → new n8n URL
- ☐ Retell post-call + custom-function webhooks (both agents) → new n8n URL
- ☐ n8n GHL credential + Location ID → new account
- ☐ n8n GHL field/pipeline/stage/value ID remap complete & tested
- ☐ GHL workflow "HTTP → n8n" actions → new n8n URL
- ☐ Zapier zaps (n8n URL + GHL credential) → new
- ☐ DocuSeal submission webhook → new endpoint (+ confirm `external_id` maps to the new contact ID)
- ☐ Salesforce push verified from the new stack (and old stack's SF step disabled to avoid double-writes)
- ☐ Callback number in Retell agents/voicemails matches the final SMS number
- ☐ A2P campaign **approved** on the new number before any SMS fires

---

## 6 · Cutover sequence (zero-downtime target)

Run **old and new in parallel**, flip in one controlled window:

1. **T-2 weeks:** start A2P registration / number port on the new account (§3.5). Deploy snapshot, build new n8n, remap IDs, re-wire everything into a **staging** state (not live).
2. **T-3 days:** full dress rehearsal — test call → new n8n → new GHL → Salesforce; test SMS; test DocuSeal signature → cadence stop. Fix issues. Old account still live and handling production.
3. **T-1 day:** final **incremental** contact export/import to catch new leads created since the first import. Re-stamp and re-hydrate any newly in-flight contacts.
4. **Cutover (single window):**
   a. **Freeze outbound** on the old account (pause call/SMS workflows) so no lead is double-touched.
   b. Do the final incremental contact + in-flight sync.
   c. **Flip webhook URLs** (Retell, GHL, Zapier, DocuSeal) to the new n8n.
   d. **Activate** new n8n workflows and **publish** new GHL workflows; run the re-hydration workflow.
   e. Point Salesforce writes to the new stack only.
5. **T+monitoring:** watch the first live calls/SMS/executions closely (§7). Keep the old stack **paused, not deleted**, as the rollback (§8).

**Why this is ~zero downtime for voice:** Retell never stops; only its webhook target flips. In-flight calls at the exact flip instant are the only exposure. SMS is the real caveat — if the number/A2P isn't ready on the new account, SMS is down until it is, so that must be resolved *before* cutover (or use Strategy A to move the number intact).

---

## 7 · Testing & validation

- ☐ Inbound test call → caller lookup returns Name/Email/language → post-call n8n execution → correct GHL contact/status → Salesforce record
- ☐ Outbound test call → classification → GHL status → SF status mapping correct (all 7 statuses incl. No Contact Consent, Human Requested)
- ☐ Consent = No path, voicemail path, human-requested path all land correctly
- ☐ SMS send from new number (post-A2P approval)
- ☐ DocuSeal test signature → cadence stop fires
- ☐ In-flight re-hydration: pick 3 sample leads, confirm they resume at the right cadence step, not from zero
- ☐ No duplicate leads in GHL or Salesforce; no double-processing
- ☐ Opt-out / DND leads confirmed suppressed on the new account

---

## 8 · Risks & mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| **A2P 10DLC not approved** on new number at cutover | SMS cadence dead | Start registration 2+ weeks early; or use Strategy A to move the number+A2P intact |
| **In-flight enrollment lost** (Strategy B) | Leads drop out of / restart cadences | Tag + anchor-date re-hydration (§3.3); or Strategy A |
| **n8n credentials break** (encryption key not carried) | Every credential fails on new host | Preserve `N8N_ENCRYPTION_KEY` or export `--decrypted` (§4.1) |
| **GHL field/pipeline IDs not remapped** in n8n | Data writes to wrong/no field silently | Rebuild ID table (§3.1); remap + test every GHL node (§4.4) |
| **Double-processing / double-contact** during parallel run | Leads called/texted twice; duplicate SF records | Freeze old outbound at cutover; only one stack writes to SF/sends outbound at a time |
| **Webhook URL propagation miss** | Some events silently stop reaching n8n | §5 checklist; monitor first executions; keep old n8n running as catch-net briefly |
| **Duplicate contacts on CSV import** | Messy DB, split histories | Import with "update if exists" on email/phone; de-dupe pass after |
| **Opt-out/DND state not carried** | Compliance breach (texting opt-outs) | Explicitly export/import DND flags; verify before enabling outbound |
| **Conversation history** (Strategy B) | Lost prior context / audit gaps if skipped | No native export/import — scripted API rebuild with `metadata.timestamp` (§3.6), or use Strategy A to move it intact |
| **Salesforce double-writes** during parallel | Duplicate/racing SF updates | Disable SF step on old stack at cutover |

---

## 9 · Rollback

- Keep the **old GHL account and old n8n instance fully intact and paused** (not deleted) for at least 1–2 weeks post-cutover.
- Rollback = re-flip webhook URLs back to old n8n, re-activate old workflows, re-enable old GHL outbound. Because Retell config is the only thing pointing at the new stack, rollback is a URL flip, not a data restore.
- **Point of no easy return:** once the new stack has processed live leads and written to Salesforce, rolling back means reconciling the delta. Decide a "commit" checkpoint (e.g. 48h clean) after which you decommission old.

---

## 10 · Expected downtime (fallback estimates — target is 0 via parallel run)

| Component | Target | Worst-case fallback |
|---|---|---|
| Voice (Retell inbound/outbound) | **0** (webhook flip only) | Minutes (in-flight calls at flip instant) |
| Post-call processing (n8n) | **0** (parallel + activate) | Minutes while activating workflows |
| GHL data/CRM | **0** (parallel account) | Import window (contacts read-only briefly) |
| **SMS (number/A2P)** | **0** if number moves/ports cleanly | **Days–weeks** if a new number needs A2P approval — *mitigate before cutover* |
| Salesforce sync | **0** | Minutes at write-repoint |

---

## 11 · Open questions to confirm before execution

1. **Same agency or different?** New sub-account (rebuild) or account takeover (native transfer)? → picks Strategy A vs B.
2. Does the destination agency use **LC Phone** (so the number + A2P can transfer)? If not, are we **porting** the existing number or **provisioning new** (A2P lead time)?
3. Is **Salesforce** staying on the same account/credentials, or also moving?
4. Which **Zapier** zaps are in play, and do they call n8n, GHL, or both?
5. Is **DocuSeal** wired yet, and does its webhook target n8n or GHL directly?
6. Is the **n8n** instance self-hosted (encryption-key path available) or cloud/managed?
7. Do we need **conversation history** migrated (Strategy A only), or is CRM structure + contacts + open opportunities sufficient?
8. Acceptable **cutover window** (day/time) and who owns the go/no-go?

---

## References
- GHL Snapshots — inclusions/exclusions: [HighLevel Support](https://help.gohighlevel.com/support/solutions/articles/48000982511) · [autogencrm](https://autogencrm.com/gohighlevel-snapshots/) · [oneexpand](https://oneexpand.com/gohighlevel-snapshots-guide/)
- Sub-account transfer / eject to new agency: [HighLevel Support](https://help.gohighlevel.com/support/solutions/articles/155000003465-sub-account-transfers-eject-sub-account-to-a-new-agency) · [bulk transfer](https://help.gohighlevel.com/support/solutions/articles/155000004570-sub-accounts-transfers-bulk-transfer-sub-accounts-to-an-existing-agency)
- Copy contacts between sub-accounts: [HighLevel Support](https://help.gohighlevel.com/support/solutions/articles/155000001034)
- Conversation AI snapshot support: [HighLevel Support](https://help.gohighlevel.com/support/solutions/articles/155000005460-conversation-ai-snapshot-support-how-to-snapshot-fully-configured-conversation-ai-bots)
- Conversations API — Add Inbound Message (timestamp/attachments for history rebuild): [HighLevel Support](https://help.gohighlevel.com/support/solutions/articles/155000007340-conversations-api-add-inbound-message-with-contact-id-)
- n8n migration (workflows, credentials, encryption key, webhooks): [MassiveGRID](https://massivegrid.com/blog/migrate-n8n-cloud-to-self-hosted/) · [instapods](https://instapods.com/blog/migrate-n8n/) · [DevSnit](https://devsnit.com/en/n8n-workflows-and-credentials-migration-tutorial/)
