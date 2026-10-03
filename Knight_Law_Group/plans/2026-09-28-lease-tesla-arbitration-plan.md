# Lease + Tesla "Requires Arbitration" Filter — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Alice (intake, inbound + outbound) apply the client's new script: the purchase-vs-lease question with its arbitration / non-retainer rules, the Tesla arbitration disqualifier, the reworded new/used question and the new AI hand-off line, and carry the result (`Bad Lead` / `Requires Arbitration`, plus a new "Purchase or Lease" value) through n8n → GHL → Zapier → Salesforce.

**Architecture:** Retell decides the route *during* the call with a deterministic code node (`node-code-classify`); n8n re-decides the final status *after* the call from its own AI transcript extraction (`Classify Lead`). Both must apply the same rules in the same order, so both are driven by one shared case table and tested against it before anything is pushed. GHL stores the result and Zapier forwards it to Salesforce.

**Tech Stack:** Retell conversation flows (REST `PATCH /update-conversation-flow`), n8n on `automations.impleko.ai` (REST `PUT /api/v1/workflows/{id}`), GoHighLevel location `vHHnJlFVorkeBvqgaqqA`, Zapier → Salesforce, Node.js 20+ for patch/test scripts.

## Status (2026-09-28)

| Task | State |
|---|---|
| 0. Freeze live state (publish current versions, pin the number) | Steps 1–4 **done 2026-09-28** (Ubaid approved): retainer agents v3 published, swaps `latest_published`, intake agents v0 published, number on `latest_published`. Next: Step 5 (open the v1 drafts) when Retell work starts, Step 6 (watch the next live calls stay on v0), Step 7 (GHL cadence dialer version). |
| 1. Setup | Done |
| 2. Case table + Retell classifier | Done: `failures: 0 / 27` (was 16/27 on the live classifier) |
| 3. n8n patch | Built, dry run only: 27/27 rule cases, 4/4 gate cases, 288 combinations 0 differences. Lease/Tesla rules are gated to calls from the new flow, so it is **safe to push before the Retell publish**; not pushed yet (waiting for Ubaid's go). |
| 4. Retell flow patch | Built, dry run only on both flows, clean. Applies to the new DRAFT versions only after Task 0. |
| 5. GHL field + pre-call | GHL token fixed 2026-09-29. Waiting on Ubaid to create the "Purchase or Lease" field (not in GHL yet) |
| 6. Micol heads-up | Ready to send |
| 7–9. Go live, test calls, close-out | Not started |

The files in `Knight_Law_Group/automations/lease-filter/` are the source of truth. Two intentional differences from the code blocks below: `n8n_patch.js` no longer contains the `split(/s+/)` fix (it shipped on its own on 2026-09-28), and `retell_patch_flows.js` takes `OUT_VER` / `IN_VER` and refuses to write to a published flow version.

**Spec:** `Knight_Law_Group/NEW - Knight Law - Internal Intake Script - Alice (+Leased).md` (client script, converted from the .docx) plus Micol's Slack answers:
- Lease-vs-buyout follow-up: approved ("And did you later buy it out, or is it still leased?").
- New/used question for leases: reword to *"Was the vehicle new or used when you got it?"*; a leased vehicle can be used CPO, so the used-non-CPO disqualifier applies to leases too.
- Bad Lead Reason value: **Requires Arbitration** (client creates the SF picklist value herself; do not ask again).
- Lease bad-lead line (verbatim): *"Since your vehicle is leased, the manufacturer is actually a party to your lease agreement, and that agreement includes a clause requiring disputes to go through arbitration instead of a lawsuit. Our firm only handles cases through the court system, so unfortunately this isn't one we are able to take on."*

## Global Constraints

- Patch ONLY the two flows bound to +1 213-205-3651: outbound `conversation_flow_b4e1b9683eaf` (agent `agent_de01f772a9de26ecf4387115a9`) and inbound `conversation_flow_fce8e3f30b49` (agent `agent_22874d74b1dd6b9d6d72aa4c67`). Legacy V27/V30 flows are not bound to any number and are not touched.
- Client-supplied sentences are spoken word for word (lease line, Q2 question, new/used question, AI hand-off line).
- Bad Lead Reason text is exactly `Requires Arbitration` (n8n → GHL → SF). In-call Retell `bad_reason` keys are `arbitration_lease`, `arbitration_buyout`, `arbitration_tesla`.
- Rule order (script order): out-of-state → lease arbitration → possession → year → lease-buyout non-retainer → Tesla arbitration → retainer make list → non-retainer.
- Every n8n / Retell code change is executed against the case table before it is pushed. No push on a "strings are present" check.
- n8n pushes go through `PUT /api/v1/workflows/{id}` with `settings: { executionOrder: 'v1' }`. After a push, nobody saves that workflow from the n8n editor without reloading it first (the editor overwrites API changes).
- Retell: current endpoints only (check the `retell-impleko` MCP `list_api_endpoints`); legacy list endpoints are deprecated and email the client a warning. Lists are `/v2/list-…`, calls are `/v3/list-calls`, `/v2/create-phone-call`.
- **Live = published, work = draft.** The number runs `latest_published`; all edits go to the draft agent/flow version; nothing is published until Ubaid says so. n8n has no draft, so the n8n lease rules are pushed only right after the Retell publish.
- Any file containing a backslash (regexes, code inside strings) is written with the Write/Edit tool, never a Bash heredoc: heredocs here collapse a double backslash to one (that is how `split(/s+/)` reached production).
- No Retell batch / simulation tests (billed). Verification = real test calls + reading the transcripts.
- Test contacts in GHL must have "test" in the name. Prompts never contain real names or emails (use John Doe / jane@acme.ai).
- Keys stay outside the repo: `D:/tmp/n8nkey.txt`, `D:/tmp/retellkey.txt`.
- No git commit until Ubaid says so.

## Review Focus

1. **Caller already said "I leased it" in answer to Q1** → Alice must not re-ask "purchase or lease"; she goes straight to "still leased, or bought it out?" (Task 8, scenario A).
2. **Spanish "No, arrendé" mis-transcribed as "Rendée" / "renté"** → understood as a lease, not a purchase and not out-of-state (Task 8, scenario B).
3. **"It's financed" / "I'm making payments"** → Alice asks lease-or-loan once; an unclear answer must default to *purchased*, because a false "leased" on a Honda/Acura/BMW/Mercedes/MINI wrongly rejects a good lead (extraction default in Task 4; Task 8, scenario F).
4. **Returning inbound Incomplete lead** with no Purchase or Lease on file is asked Q2; with it on file is not re-asked (resume edges in Task 4; Task 8, scenario G).
5. **Precedence**: a 2019 Tesla is *Vehicle year* (not arbitration); a 2019 leased Honda is *Requires Arbitration* (not year); a 2019 lease-buyout BMW is *Vehicle year* (cases in Task 2).

---

## Decisions (approved by Ubaid 2026-09-28; not asked to Micol)

| # | Topic | Decision |
|---|---|---|
| 1 | Tesla line (the script reused "Since your vehicle is **leased**…", wrong for a bought Tesla) | *"Tesla's purchase and lease agreements include a clause requiring disputes to go through arbitration instead of a lawsuit. Our firm only handles cases through the court system, so unfortunately this isn't one we are able to take on."* |
| 2 | Leased-then-bought Honda/Acura line | *"Since your vehicle started out as a lease, the manufacturer was a party to that original lease agreement, and that agreement includes a clause requiring disputes to go through arbitration instead of a lawsuit. Our firm only handles cases through the court system, so unfortunately this isn't one we are able to take on."* |
| 3 | Leased-then-bought BMW / Mercedes-Benz / MINI → Non-Retainer | Possession and year are checked first, then Non-Retainer (a 2019 buyout BMW is Vehicle year). |
| 4 | Spanish versions of the new lines | Ours, as written in `retell_patch_flows.js`. |

---

## File Structure

All new files live in `Knight_Law_Group/automations/lease-filter/`:

| File | Responsibility |
|---|---|
| `rules_cases.js` | The shared case table: one row per rule, with the expected Retell route and the expected n8n status. |
| `retell_classify.js` | Body of the Retell code node `node-code-classify` (in-call routing). |
| `test_retell_classify.js` | Runs a Retell classify body against `rules_cases.js`. |
| `n8n_patch.js` | Pulls the live intake post-call workflow, patches `Classify Lead`, `AI - Post-Call Extract`, `Build Payload`, writes `out/`, pushes when `APPLY=1`. |
| `test_n8n_classify.js` | Runs the patched `Classify Lead` against `rules_cases.js`, a no-lease regression sweep versus live, and the Lead Language word-count fix. |
| `retell_patch_flows.js` | Pulls the two live flows, adds the lease / arbitration nodes, rewires, writes `out/`, pushes when `APPLY=1`. |
| `ghl_field_id.js` | Prints the ID of the new GHL "Purchase or Lease" field. |
| `precall_patch.js` | Patches the pre-call workflow to seed `purchase_type` and mention it in the recap; `APPLY=1` pushes. |
| `test_precall.js` | Runs the patched pre-call code against fake GHL contacts. |
| `.gitignore` | Ignores `out/` and `node_modules/`. |

---

### Task 0: Freeze the live state (Ubaid)

**Why:** on 2026-09-28 every live call ran an UNPUBLISHED draft: intake outbound `agent_de01f772…` v0 and inbound `agent_22874d74…` v0 had never been published, the number had no version pinned (resolves to `latest`), the retainer cadence agent `agent_83f8b296…` runs draft v3 (last published v2), and the three agent-swap nodes call the Immediate agent `agent_7540b5be…` with `agent_version: "latest"` (draft v3, last published v2). So any draft edit went live instantly. Each step below is behaviour-neutral: it publishes exactly what is running now.

**Order matters** (publishing the retainer agents first keeps `latest_published` on the same v3 that runs today):

- [ ] **Step 1: Publish the two retainer agents' current draft (v3) in place.** Dashboard → *Alice - Knight Law - Retainer Immediate (Single Prompt) V01* → Publish (version 3). Same for *Alice - Knight Law - Retainer Outbound (Single Prompt) V01* (version 3). API equivalent: `POST /publish-agent-version/{agent_id}` `{ "version": 3 }`.
- [ ] **Step 2: Point the three swap nodes at `latest_published`** (still the v0 intake drafts, so this edit is live, but it resolves to the same v3): outbound flow `node-ret-swap`, inbound flow `node-inb-ret-swap` and `node-inb-qual-swap`, `agent_version: "latest_published"`.
- [ ] **Step 3: Publish the two intake agents' v0.** *Alice - Knight Law (Outbound Conversation Flow) V01 - New Retainer Flow* and *Alice - Knight Law (Inbound Conversation Flow) V01 - NEW Retainer Flow*. This is exactly what runs today, including the 2026-09-28 greeting, spelling and confirmed-name changes.
- [ ] **Step 4: Pin the number.** (213) 205-3651 → inbound agent version and outbound agent version = **latest published** (API: `PATCH /update-phone-number/+12132053651` with `inbound_agents: [{agent_id: agent_22874d74b1dd6b9d6d72aa4c67, agent_version: "latest_published", weight: 1}]` and `outbound_agents: [{agent_id: agent_de01f772a9de26ecf4387115a9, agent_version: "latest_published", weight: 1}]`).
- [ ] **Step 5: Open the drafts.** For both intake agents: new draft from base version 0 (`POST /create-agent-version/{agent_id}` `{ "base_version": 0 }`). Note the new draft's flow version (`GET /get-agent/{agent_id}` → `response_engine.version`); that is `OUT_VER` / `IN_VER` for Task 4.
- [ ] **Step 6: Prove live calls stay on the published version.** After the next few real intake calls, `POST /v3/list-calls` must show `agent_version: 0` (not 1). If any call shows the draft, a GHL dialer passes `override_agent_id` without a version: add `"override_agent_version": "latest_published"` to that GHL webhook body before continuing.
- [ ] **Step 7 (GHL, recommended): pin the retainer cadence dialer.** The GHL workflow that calls `agent_83f8b296…` should send `"override_agent_version": "latest_published"`, so a future draft of that agent never goes live by accident.

### Task 1: Setup

**Files:**
- Create: `Knight_Law_Group/automations/lease-filter/.gitignore`
- Create: `D:/tmp/retellkey.txt` (outside the repo)

**Interfaces:**
- Produces: `D:/tmp/retellkey.txt` (Retell key, one line), `D:/tmp/n8nkey.txt` (already exists; n8n key synced from `.mcp.json` server `n8n-mcp-impleko`), local `luxon` for the pre-call test.

- [ ] **Step 1: Create the folder and ignore file**

```bash
mkdir -p "D:/retell-voice-agents/Knight_Law_Group/automations/lease-filter"
printf 'out/\nnode_modules/\npackage-lock.json\npackage.json\n' > "D:/retell-voice-agents/Knight_Law_Group/automations/lease-filter/.gitignore"
```

- [ ] **Step 2: Write the Retell key file from `.mcp.json` and refresh the n8n key**

```bash
node -e "const fs=require('fs');const j=JSON.parse(fs.readFileSync('D:/retell-voice-agents/.mcp.json','utf8'));const s=j.mcpServers||j;const k=JSON.stringify(s['retell-impleko'].args).match(/key_[0-9a-f]+/)[0];fs.writeFileSync('D:/tmp/retellkey.txt',k);const n=s['n8n-mcp-impleko'].env.N8N_API_KEY;fs.writeFileSync('D:/tmp/n8nkey.txt',n);console.log('retell',k.slice(0,8)+'...','n8n',n.slice(0,6)+'...')"
```
Expected: `retell key_ebc4... n8n eyJhbG...`

- [ ] **Step 3: Install luxon locally (pre-call test needs `$now`)**

```bash
cd "D:/retell-voice-agents/Knight_Law_Group/automations/lease-filter" && npm init -y >/dev/null && npm install --no-audit --no-fund luxon
```
Expected: `added 1 package`.

---

### Task 2: Shared rule table + Retell in-call classifier

**Files:**
- Create: `Knight_Law_Group/automations/lease-filter/rules_cases.js`
- Create: `Knight_Law_Group/automations/lease-filter/test_retell_classify.js`
- Create: `Knight_Law_Group/automations/lease-filter/retell_classify.js`

**Interfaces:**
- Produces: `rules_cases.js` exports an array of `{ label, make, pt, ptSeed, year, possess, retell: [route, bad_reason], n8n: [lead_status, bad_lead_reason] }`, where `pt` ∈ `'purchased' | 'leased' | 'lease_buyout' | ''` (in-call answer) and `ptSeed` ∈ `'Purchased' | 'Leased' | 'Leased, then purchased' | ''` (value on file in GHL).
- Produces: `retell_classify.js`, a Retell code-node body that reads `dv.vehicle_make`, `dv.vehicle_year`, `dv.in_possession`, `dv.purchase_type_call`, `dv.purchase_type` and returns `{ route, bad_reason, lead_status }`, with `route` ∈ `retainer | non_retainer | bad | reprompt` and new `bad_reason` values `arbitration_lease | arbitration_buyout | arbitration_tesla`.

- [ ] **Step 1: Write the case table**

`rules_cases.js`:
```js
// One row per rule. retell = [route, bad_reason] from node-code-classify (in-call).
// n8n = [lead_status, bad_lead_reason] from the n8n Classify Lead node (final, sent to GHL).
const C = (label, make, pt, year, possess, retell, n8n, ptSeed) => ({ label, make, pt, year, possess, retell, n8n, ptSeed: ptSeed || '' });
const RET = ['retainer', 'N/A'], NONRET = ['non_retainer', 'N/A'];
const N_RET = ['Retainer Lead', 'N/A'], N_NON = ['Non-Retainer Lead', 'N/A'];
const ARB = ['Bad Lead', 'Requires Arbitration'];
module.exports = [
  C('leased Honda 2023 -> arbitration', 'Honda', 'leased', 2023, true, ['bad', 'arbitration_lease'], ARB),
  C('leased Acura 2023 -> arbitration', 'Acura', 'leased', 2023, true, ['bad', 'arbitration_lease'], ARB),
  C('leased BMW 2023 -> arbitration', 'BMW', 'leased', 2023, true, ['bad', 'arbitration_lease'], ARB),
  C('leased Mercedes-Benz 2023 -> arbitration', 'Mercedes-Benz', 'leased', 2023, true, ['bad', 'arbitration_lease'], ARB),
  C('leased "Mercedes" alias -> arbitration', 'Mercedes', 'leased', 2023, true, ['bad', 'arbitration_lease'], ARB),
  C('leased MINI 2023 -> arbitration', 'MINI', 'leased', 2023, true, ['bad', 'arbitration_lease'], ARB),
  C('leased Ford 2023 -> retainer', 'Ford', 'leased', 2023, true, RET, N_RET),
  C('leased Toyota 2023 -> non-retainer', 'Toyota', 'leased', 2023, true, NONRET, N_NON),
  C('leased Ford not in possession -> possession', 'Ford', 'leased', 2023, false, ['bad', 'not_in_possession'], ['Bad Lead', 'Not in possession of vehicle']),
  C('leased Honda 2019 -> arbitration beats year', 'Honda', 'leased', 2019, true, ['bad', 'arbitration_lease'], ARB),
  C('buyout Honda 2023 -> arbitration', 'Honda', 'lease_buyout', 2023, true, ['bad', 'arbitration_buyout'], ARB),
  C('buyout Acura 2023 -> arbitration', 'Acura', 'lease_buyout', 2023, true, ['bad', 'arbitration_buyout'], ARB),
  C('buyout BMW 2023 -> non-retainer', 'BMW', 'lease_buyout', 2023, true, NONRET, N_NON),
  C('buyout Mercedes-Benz 2023 -> non-retainer', 'Mercedes-Benz', 'lease_buyout', 2023, true, NONRET, N_NON),
  C('buyout MINI 2023 -> non-retainer', 'MINI', 'lease_buyout', 2023, true, NONRET, N_NON),
  C('buyout BMW 2019 -> year first', 'BMW', 'lease_buyout', 2019, true, ['bad', 'vehicle_year'], ['Bad Lead', 'Vehicle year']),
  C('buyout Ford 2023 -> retainer', 'Ford', 'lease_buyout', 2023, true, RET, N_RET),
  C('purchased BMW 2023 -> retainer (unchanged)', 'BMW', 'purchased', 2023, true, RET, N_RET),
  C('purchased Honda 2023 -> non-retainer (unchanged)', 'Honda', 'purchased', 2023, true, NONRET, N_NON),
  C('purchased Tesla 2023 -> arbitration', 'Tesla', 'purchased', 2023, true, ['bad', 'arbitration_tesla'], ARB),
  C('leased Tesla 2023 -> tesla arbitration', 'Tesla', 'leased', 2023, true, ['bad', 'arbitration_tesla'], ARB),
  C('Tesla 2019 -> year beats tesla', 'Tesla', 'purchased', 2019, true, ['bad', 'vehicle_year'], ['Bad Lead', 'Vehicle year']),
  C('Tesla not in possession -> arbitration (Tesla not opted in)', 'Tesla', 'purchased', 2023, false, ['bad', 'arbitration_tesla'], ARB),
  C('purchase type unknown BMW -> retainer (old behaviour)', 'BMW', '', 2023, true, RET, N_RET),
  C('purchase type unknown Honda -> non-retainer', 'Honda', '', 2023, true, NONRET, N_NON),
  C('only GHL seed "Leased" Honda -> arbitration', 'Honda', '', 2023, true, ['bad', 'arbitration_lease'], ARB, 'Leased'),
  C('call answer beats seed (buyout over Purchased) BMW', 'BMW', 'lease_buyout', 2023, true, NONRET, N_NON, 'Purchased'),
];
```

- [ ] **Step 2: Write the Retell test runner**

`test_retell_classify.js`:
```js
// Usage: node test_retell_classify.js [code-file]   (default: retell_classify.js)
const fs = require('fs');
const path = require('path');
const CASES = require('./rules_cases');
const src = fs.readFileSync(path.resolve(__dirname, process.argv[2] || 'retell_classify.js'), 'utf8');
const run = (dv) => new Function('dv', src)(dv);
let fail = 0;
for (const c of CASES) {
  const dv = { vehicle_make: c.make, vehicle_year: String(c.year), in_possession: String(c.possess) };
  if (c.pt) dv.purchase_type_call = c.pt;
  if (c.ptSeed) dv.purchase_type = c.ptSeed;
  const got = run(dv);
  const ok = got.route === c.retell[0] && got.bad_reason === c.retell[1];
  if (!ok) fail++;
  console.log((ok ? '  ok   ' : '  FAIL ') + c.label.padEnd(60) + ' -> ' + got.route + ' / ' + got.bad_reason + (ok ? '' : '   WANT ' + c.retell.join(' / ')));
}
console.log('\nfailures: ' + fail + ' / ' + CASES.length);
process.exit(fail ? 1 : 0);
```

- [ ] **Step 3: Run it against today's live classifier to prove the table catches the gap**

```bash
cd "D:/retell-voice-agents/Knight_Law_Group/automations/lease-filter"
node -e "const fs=require('fs');(async()=>{const k=fs.readFileSync('D:/tmp/retellkey.txt','utf8').trim();const f=await (await fetch('https://api.retellai.com/get-conversation-flow/conversation_flow_b4e1b9683eaf',{headers:{Authorization:'Bearer '+k}})).json();fs.mkdirSync('out',{recursive:true});fs.writeFileSync('out/retell_classify_live.js',f.nodes.find(n=>n.id==='node-code-classify').code);console.log('saved')})()"
node test_retell_classify.js out/retell_classify_live.js
```
Expected: `failures: 16 / 27` (every lease-arbitration, buyout, Tesla and seed row fails; the unchanged rows pass).

- [ ] **Step 4: Write the new classifier**

`retell_classify.js`:
```js
const norm = (s) => (s || '').toString().toLowerCase().replace(/[^a-z]/g, '');
const aliases = { mercedes: 'mercedesbenz', benz: 'mercedesbenz', mercedesbenz: 'mercedesbenz', vw: 'volkswagen', volkswagon: 'volkswagen', chevy: 'chevrolet' };
const makeKey = aliases[norm(dv.vehicle_make)] || norm(dv.vehicle_make);
const possess = (dv.in_possession || '').toString().toLowerCase().trim() !== 'false';
// Purchase vs lease (script Q2): this call's answer first, else the value on file in GHL (seeded by the pre-call).
const ptOf = (v) => { const t = norm(v); if (!t || t === 'na') return ''; if (t === 'leasebuyout' || t.indexOf('leasedthenpurchased') === 0 || t.indexOf('buyout') !== -1) return 'lease_buyout'; if (t.indexOf('lease') === 0) return 'leased'; if (t.indexOf('purchase') === 0 || t === 'bought') return 'purchased'; return ''; };
const pt = ptOf(dv.purchase_type_call) || ptOf(dv.purchase_type);
const optedIn = ['alfaromeo','buick','cadillac','chevrolet','chrysler','dodge','fiat','ford','gmc','hummer','infiniti','jaguar','jeep','kia','landrover','lincoln','maserati','mercedesbenz','mercury','mitsubishi','nissan','pontiac','ram','saturn','smart','hyundai','subaru','genesis','vinfast'];
const retainerMakes = ['acura','buick','cadillac','gmc','chevrolet','ford','lincoln','hyundai','kia','nissan','infiniti','volkswagen','jeep','ram','dodge','chrysler','bmw','mercedesbenz','jaguar','landrover','mazda','audi'];
const leaseArbitration = ['honda','acura','bmw','mercedesbenz','mini'];
const buyoutArbitration = ['honda','acura'];
const buyoutNonRetainer = ['bmw','mercedesbenz','mini'];
if (!makeKey) { return { route: 'reprompt', bad_reason: 'N/A', lead_status: '' }; }
if (pt === 'leased' && leaseArbitration.includes(makeKey)) { return { route: 'bad', bad_reason: 'arbitration_lease', lead_status: 'Bad Lead' }; }
if (pt === 'lease_buyout' && buyoutArbitration.includes(makeKey)) { return { route: 'bad', bad_reason: 'arbitration_buyout', lead_status: 'Bad Lead' }; }
if (!possess && optedIn.includes(makeKey)) { return { route: 'bad', bad_reason: 'not_in_possession', lead_status: 'Bad Lead' }; }
const year = parseInt(dv.vehicle_year, 10);
if (!year || isNaN(year)) { return { route: 'reprompt', bad_reason: 'N/A', lead_status: '' }; }
if (year <= 2020) { return { route: 'bad', bad_reason: 'vehicle_year', lead_status: 'Bad Lead' }; }
if (pt === 'lease_buyout' && buyoutNonRetainer.includes(makeKey)) { return { route: 'non_retainer', bad_reason: 'N/A', lead_status: 'Non-Retainer Lead' }; }
if (makeKey === 'tesla') { return { route: 'bad', bad_reason: 'arbitration_tesla', lead_status: 'Bad Lead' }; }
if (retainerMakes.includes(makeKey)) { return { route: 'retainer', bad_reason: 'N/A', lead_status: 'Retainer Pending' }; }
return { route: 'non_retainer', bad_reason: 'N/A', lead_status: 'Non-Retainer Lead' };
```

- [ ] **Step 5: Run the tests**

```bash
cd "D:/retell-voice-agents/Knight_Law_Group/automations/lease-filter" && node test_retell_classify.js
```
Expected: `failures: 0 / 27`.

---

### Task 3: n8n intake post-call (Classify Lead, AI extract, Build Payload)

**Files:**
- Create: `Knight_Law_Group/automations/lease-filter/n8n_patch.js`
- Create: `Knight_Law_Group/automations/lease-filter/test_n8n_classify.js`
- Modifies (live, on push): workflow `8DuNGcG9ybV3wVlv` nodes `Classify Lead`, `AI - Post-Call Extract`, `Build Payload`

**Interfaces:**
- Consumes: `rules_cases.js` (Task 2).
- Produces: `Classify Lead` output gains `purchase_type` (`'Purchased' | 'Leased' | 'Leased, then purchased' | 'N/A'`) and can emit `bad_lead_reason: 'Requires Arbitration'`. `Build Payload` sends `custom_analysis_data['Purchase Type']`. The AI extractor returns a new key `purchase_type` with the same labels.

- [ ] **Step 1: Write the patcher (dry run by default)**

`n8n_patch.js`:
```js
// node n8n_patch.js           -> pulls live, writes out/classify_live.js + out/classify_new.js + prompt/payload files
// APPLY=1 node n8n_patch.js   -> also pushes to n8n and verifies
const fs = require('fs');
const path = require('path');
const KEY = fs.readFileSync('D:/tmp/n8nkey.txt', 'utf8').trim();
const BASE = 'https://automations.impleko.ai';
const WF = '8DuNGcG9ybV3wVlv';
const H = { 'X-N8N-API-KEY': KEY, 'Content-Type': 'application/json' };
const OUT = path.join(__dirname, 'out');
fs.mkdirSync(OUT, { recursive: true });
const lf = (s) => String(s).replace(/\r/g, '');

// Replace exactly one occurrence (string or regex), else throw.
function rep(src, find, repl, label) {
  if (find instanceof RegExp) {
    const all = src.match(new RegExp(find.source, find.flags.includes('g') ? find.flags : find.flags + 'g')) || [];
    if (all.length !== 1) throw new Error(label + ': expected 1 match, found ' + all.length);
    return src.replace(find, repl);
  }
  const n = src.split(find).length - 1;
  if (n !== 1) throw new Error(label + ': expected 1 match, found ' + n);
  return src.replace(find, repl);
}

function patchClassify(src) {
  src = rep(src,
    "const toBool = (v) => v === true || ['true','yes','y'].includes(String(v==null?'':v).trim().toLowerCase());",
    "const toBool = (v) => v === true || ['true','yes','y'].includes(String(v==null?'':v).trim().toLowerCase());\n" +
    "// Purchase vs lease (script Q2). Accepts the AI labels, the GHL labels and the Retell enum keys.\n" +
    "const ptLabel = (v) => { const t = String(v==null?'':v).toLowerCase().replace(/[^a-z]/g,''); if (!t || t==='na') return ''; if (t==='leasebuyout' || t.indexOf('leasedthenpurchased')===0 || t.indexOf('buyout')!==-1) return 'Leased, then purchased'; if (t.indexOf('lease')===0) return 'Leased'; if (t.indexOf('purchase')===0 || t==='bought') return 'Purchased'; return ''; };",
    'ptLabel helper');
  src = rep(src, /^(  is_owner:\s+toYN\(f\.is_owner\)\s+\|\| toYN\(seeded\.is_owner\),)$/m,
    "$1\n  purchase_type:     ptLabel(f.purchase_type)  || ptLabel(seeded.purchase_type),", 'merge purchase_type');
  src = rep(src, /^(const retainerMakes = \[.*\];)$/m,
    "$1\nconst leaseArbitration = ['honda','acura','bmw','mercedesbenz','mini'];\nconst buyoutArbitration = ['honda','acura'];\nconst buyoutNonRetainer = ['bmw','mercedesbenz','mini'];", 'lease make lists');
  src = rep(src, "  if (!makeKey) return { s:'Incomplete Lead', r:'N/A' };",
    "  if (!makeKey) return { s:'Incomplete Lead', r:'N/A' };\n" +
    "  if (x.purchase_type === 'Leased' && leaseArbitration.includes(makeKey)) return { s:'Bad Lead', r:'Requires Arbitration' };\n" +
    "  if (x.purchase_type === 'Leased, then purchased' && buyoutArbitration.includes(makeKey)) return { s:'Bad Lead', r:'Requires Arbitration' };",
    'lease arbitration rules');
  src = rep(src, "  if (year <= 2020) return { s:'Bad Lead', r:'Vehicle year' };",
    "  if (year <= 2020) return { s:'Bad Lead', r:'Vehicle year' };\n" +
    "  if (x.purchase_type === 'Leased, then purchased' && buyoutNonRetainer.includes(makeKey)) return { s:'Non-Retainer Lead', r:'N/A' };\n" +
    "  if (makeKey === 'tesla') return { s:'Bad Lead', r:'Requires Arbitration' };",
    'buyout non-retainer + tesla');
  // Bug fix: the word count for the no-contact Lead Language guard split on the letter "s" instead of whitespace.
  src = rep(src, 'split(/s+/)', 'split(/\\s+/)', 'word-count regex');
  src = rep(src, '  purchase_condition: pc,', '  purchase_type: out(m.purchase_type),\n  purchase_condition: pc,', 'output purchase_type');
  return src;
}

function patchPrompt(sys, user) {
  sys = rep(sys, '- ca_purchase: Yes / No / N/A (was the vehicle bought or leased from a California dealership)',
    '- ca_purchase: Yes / No / N/A (was the vehicle bought or leased from a California dealership)\n' +
    '- purchase_type: Purchased / Leased / Leased, then purchased / N/A. How the caller got the vehicle, from their answer to "Did you purchase the vehicle, or lease it?" and the follow-up "is it still leased, or did you later buy it out?". Purchased = they bought it (cash, loan or financing). Leased = it is on a lease now (Spanish "arrendado", "arrendé", "rentado", "lo rento"). Leased, then purchased = it started as a lease and they later bought it out. Treat close-sounding mis-transcriptions of lease ("liz", "list", "lists", "Rendée", "renté") as lease. Never return Leased or Leased, then purchased unless the caller actually said the vehicle is or was leased. N/A if not discussed.',
    'prompt purchase_type');
  sys = rep(sys, '- new_or_used: New / Used / N/A (was it purchased new or used)',
    '- new_or_used: New / Used / N/A (was the vehicle new or used when they got it, whether bought or leased)', 'prompt new_or_used');
  sys = rep(sys, '(issue, ca_purchase, in_possession, new_or_used, is_cpo, repairs_attempted, is_owner)',
    '(issue, ca_purchase, purchase_type, in_possession, new_or_used, is_cpo, repairs_attempted, is_owner)', 'prompt voicemail list');
  user = rep(user, '(issue, ca_purchase, in_possession, vehicle_year,', '(issue, ca_purchase, purchase_type, in_possession, vehicle_year,', 'user msg retainer-only list');
  return { sys, user };
}

function patchPayload(src) {
  return rep(src, "  'Purchase Condition': c.purchase_condition,", "  'Purchase Condition': c.purchase_condition,\n  'Purchase Type': c.purchase_type,", 'payload Purchase Type');
}

(async () => {
  const wf = await (await fetch(`${BASE}/api/v1/workflows/${WF}`, { headers: H })).json();
  const cl = wf.nodes.find((n) => n.name === 'Classify Lead');
  const ai = wf.nodes.find((n) => n.name === 'AI - Post-Call Extract');
  const bp = wf.nodes.find((n) => n.name === 'Build Payload');
  const live = { classify: lf(cl.parameters.jsCode), sys: lf(ai.parameters.messages.values[0].content), user: lf(ai.parameters.messages.values[1].content), payload: lf(bp.parameters.jsCode) };
  const next = { classify: patchClassify(live.classify), payload: patchPayload(live.payload), ...patchPrompt(live.sys, live.user) };
  fs.writeFileSync(path.join(OUT, 'classify_live.js'), live.classify);
  fs.writeFileSync(path.join(OUT, 'classify_new.js'), next.classify);
  fs.writeFileSync(path.join(OUT, 'ai_system_new.txt'), next.sys);
  fs.writeFileSync(path.join(OUT, 'ai_user_new.txt'), next.user);
  fs.writeFileSync(path.join(OUT, 'build_payload_new.js'), next.payload);
  new Function('$input', '$', next.classify); new Function('$input', '$', next.payload); // syntax check
  console.log('patched: classify ' + live.classify.length + ' -> ' + next.classify.length + ', system prompt ' + live.sys.length + ' -> ' + next.sys.length + ', payload ' + live.payload.length + ' -> ' + next.payload.length);
  if (process.env.APPLY !== '1') { console.log('DRY RUN: nothing pushed'); return; }

  cl.parameters.jsCode = next.classify;
  ai.parameters.messages.values[0].content = next.sys;
  ai.parameters.messages.values[1].content = next.user;
  bp.parameters.jsCode = next.payload;
  const put = await fetch(`${BASE}/api/v1/workflows/${WF}`, { method: 'PUT', headers: H, body: JSON.stringify({ name: wf.name, nodes: wf.nodes, connections: wf.connections, settings: { executionOrder: 'v1' } }) });
  console.log('PUT ' + put.status + (put.ok ? ' OK' : ' ' + (await put.text()).slice(0, 400)));
  const v = await (await fetch(`${BASE}/api/v1/workflows/${WF}`, { headers: H })).json();
  const g = (name) => v.nodes.find((n) => n.name === name).parameters;
  const checks = {
    active: v.active === true,
    classify: lf(g('Classify Lead').jsCode) === next.classify,
    system: lf(g('AI - Post-Call Extract').messages.values[0].content) === next.sys,
    user: lf(g('AI - Post-Call Extract').messages.values[1].content) === next.user,
    payload: lf(g('Build Payload').jsCode) === next.payload,
  };
  console.log('verify: ' + JSON.stringify(checks));
  fs.writeFileSync('D:/tmp/classify_known_good.js', next.classify);
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
```

- [ ] **Step 2: Write the n8n test runner**

`test_n8n_classify.js`:
```js
const fs = require('fs');
const path = require('path');
const CASES = require('./rules_cases');
const OUT = path.join(__dirname, 'out');
const NEW = fs.readFileSync(path.join(OUT, 'classify_new.js'), 'utf8');
const LIVE = fs.readFileSync(path.join(OUT, 'classify_live.js'), 'utf8');
const LABEL = { purchased: 'Purchased', leased: 'Leased', lease_buyout: 'Leased, then purchased' };

function run(src, ai, call) {
  const $input = { first: () => ({ json: { message: { content: JSON.stringify(ai) } } }) };
  const $ = () => ({ first: () => ({ json: { body: { call } } }) });
  return new Function('$input', '$', src)($input, $)[0].json;
}
const EN = 'User: Yes.\nUser: I bought it from a dealership here in California, it is a used vehicle.\nUser: Yes, I still have the car.\nUser: Okay, that is fine, thanks.';
const ai = (c) => ({ lead_language: 'English', opt_out: 'No', is_voicemail: 'No', requested_human: 'No', declined_ai: 'No', issue: 'Yes', ca_purchase: 'Yes', purchase_type: c.pt ? LABEL[c.pt] : 'N/A', in_possession: c.possess ? 'Yes' : 'No', vehicle_year: String(c.year), vehicle_make: c.make, vehicle_model: 'N/A', new_or_used: 'New', is_cpo: 'N/A', repairs_attempted: 'Yes', is_owner: 'Yes', full_name: 'N/A', confirmed_email: 'N/A', contact_consent: 'Yes', call_dnd: false, sms_dnd: false, email_dnd: false, call_summary: 'x' });
const call = (c, over) => Object.assign({ call_id: 'c', start_timestamp: 1000000, end_timestamp: 1300000, disconnection_reason: 'user_hangup', transcript: EN, retell_llm_dynamic_variables: Object.assign({ Name: 'John Doe', Phone: '+15555550100', Email: 'jane@acme.ai', lead_language: 'English' }, c && c.ptSeed ? { purchase_type: c.ptSeed } : {}) }, over || {});

let fail = 0;
console.log('== rule cases ==');
for (const c of CASES) {
  const o = run(NEW, ai(c), call(c));
  const wantPt = c.pt ? LABEL[c.pt] : (c.ptSeed || 'N/A');
  const ok = o.lead_status === c.n8n[0] && o.bad_lead_reason === c.n8n[1] && o.purchase_type === wantPt;
  if (!ok) fail++;
  console.log((ok ? '  ok   ' : '  FAIL ') + c.label.padEnd(60) + ' -> ' + o.lead_status + ' / ' + o.bad_lead_reason + ' / ' + o.purchase_type + (ok ? '' : '   WANT ' + c.n8n.join(' / ') + ' / ' + wantPt));
}

console.log('\n== regression: no purchase type, must equal live on every existing field ==');
const MAKES = ['Acura','Audi','BMW','Buick','Cadillac','Chevrolet','Chrysler','Dodge','FIAT','Ford','Genesis','GMC','Honda','HUMMER','Hyundai','INFINITI','Jaguar','Jeep','Kia','Land Rover','Lexus','Lincoln','Mazda','Mercedes-Benz','MINI','Mitsubishi','Nissan','Porsche','Ram','Subaru','Toyota','Volkswagen','Volvo','Rivian','Lucid'];
let reg = 0, n = 0;
for (const make of MAKES) for (const year of [2019, 2020, 2021, 2024]) for (const possess of [true, false]) {
  const c = { make, year, possess, pt: '' }; n++;
  const a = run(NEW, ai(c), call(c)), b = run(LIVE, ai(c), call(c));
  for (const k of Object.keys(b)) if (JSON.stringify(a[k]) !== JSON.stringify(b[k])) { reg++; console.log('  DIFF ' + make + ' ' + year + ' possess=' + possess + ' ' + k + ': ' + JSON.stringify(b[k]) + ' -> ' + JSON.stringify(a[k])); }
}
console.log('  ' + n + ' combinations, ' + reg + ' differences');

console.log('\n== Lead Language word count (split on whitespace, not on the letter s) ==');
const ES_FEW_S = 'User: Bueno, claro.\nUser: Lo compré nuevo aquí en California.\nUser: Tengo el carro, el Ford nuevo, del año pasado.';
const base = Object.assign(ai({ make: 'Ford', year: 2024, possess: true, pt: 'purchased' }), { lead_language: 'Spanish' });
const langNew = run(NEW, base, call(null, { transcript: ES_FEW_S })).lead_language;
const langLive = run(LIVE, base, call(null, { transcript: ES_FEW_S })).lead_language;
const langOk = langNew === 'Spanish';
if (!langOk) fail++;
console.log((langOk ? '  ok   ' : '  FAIL ') + 'real 5-min Spanish call, English on file -> ' + langNew + ' (live today: ' + langLive + ')');

console.log('\nfailures: ' + fail + ' | regressions: ' + reg);
process.exit(fail + reg ? 1 : 0);
```

- [ ] **Step 3: Pull live and generate the patched files (dry run)**

```bash
cd "D:/retell-voice-agents/Knight_Law_Group/automations/lease-filter" && node n8n_patch.js
```
Expected: `patched: classify 11059 -> ~12000, ...` then `DRY RUN: nothing pushed`. If any `expected 1 match, found 0` error appears, the live node changed since this plan was written: open `out/classify_live.js`, find the new text for that anchor, update the anchor in `n8n_patch.js`, rerun.

- [ ] **Step 4: Run the tests**

```bash
node test_n8n_classify.js
```
Expected: 27 rule rows `ok`, `280 combinations, 0 differences`, Lead Language row `ok ... -> Spanish (live today: English)`, `failures: 0 | regressions: 0`.

- [ ] **Step 5: Read the patched prompt diff**

```bash
node -e "const fs=require('fs');const a=fs.readFileSync('out/ai_system_new.txt','utf8');a.split('\n').forEach((l,i)=>{if(/purchase_type|new_or_used/.test(l))console.log(i+': '+l.slice(0,200))})"
```
Expected: the new `purchase_type` bullet after `ca_purchase`, the reworded `new_or_used` bullet, and `purchase_type` inside the voicemail rule list. Do NOT push yet (push happens in Task 7).

---

### Task 4: Retell flows (both live flows)

**Files:**
- Create: `Knight_Law_Group/automations/lease-filter/retell_patch_flows.js`
- Modifies (live, on push): `conversation_flow_b4e1b9683eaf`, `conversation_flow_fce8e3f30b49`

**Interfaces:**
- Consumes: `retell_classify.js` (Task 2) — pasted into `node-code-classify`.
- Produces: new nodes `node-q-lease`, `node-extract-lease` (writes `purchase_type_call`), `node-after-lease`, `node-disq-arb-lease`, `node-disq-arb-buyout`, `node-disq-arb-tesla`. `node-branch-bad` routes `bad_reason` `arbitration_lease | arbitration_buyout | arbitration_tesla` to them. Inbound resume nodes route `{{purchase_type}}` not_exist → `node-q-lease` (the pre-call seeds `purchase_type` in Task 5).

New call path: `Q1 California` → **`Q2 Purchase or Lease`** → `Extract Purchase Type` → `Route After Lease` (possession / vehicle questions, or straight to the vehicle read-back for a returning lead who already gave them) → … → `Classify` → bad branch → arbitration line → `End: Bad Lead`.

- [ ] **Step 1: Write the flow patcher**

`retell_patch_flows.js`:
```js
// node retell_patch_flows.js           -> dry run: writes out/flow_<id>.json, prints the change list, validates edges
// APPLY=1 node retell_patch_flows.js   -> PATCHes the two live flows (nodes only) and verifies
const fs = require('fs');
const path = require('path');
const KEY = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const APPLY = process.env.APPLY === '1';
const OUT = path.join(__dirname, 'out');
fs.mkdirSync(OUT, { recursive: true });
const FLOWS = ['b4e1b9683eaf', 'fce8e3f30b49']; // outbound, inbound: the only flows bound to +1 213-205-3651
const CLASSIFY = fs.readFileSync(path.join(__dirname, 'retell_classify.js'), 'utf8');

const TXT = {
  qLease: `Ask ONE question (caller's language), then wait.
English: "Did you purchase the vehicle, or lease it?"
Spanish: "¿Usted compró el vehículo, o lo arrendó?"

If the caller ALREADY said in an earlier answer that they lease it or leased it, do NOT ask that again: go straight to the follow-up below. If they already clearly said they bought it, do not ask again either: just say "Got it" ("Entendido") and move on.

Follow-up, ONLY if the vehicle is or was leased: "And is it still leased, or did you later buy it out?" In Spanish: "¿Y todavía lo tiene arrendado, o después lo compró?" Then wait.

If the answer is only "it's financed", "I'm making payments", "a loan" or "estoy pagando", that does not say lease or purchase. Ask once: "Is that a lease, or a loan to buy it?" In Spanish: "¿Es un arrendamiento, o un préstamo para comprarlo?"

How to read the answer (do NOT say this out loud): "lease", "leased", "leasing" and close-sounding mis-transcriptions such as "liz", "list" or "lists" mean LEASE. In Spanish, "arrendado", "arrendé", "lo arriendo", "rentado", "lo rento" and mis-transcriptions such as "Rendée" or "renté" mean LEASE. "Bought", "purchased", "paid cash", "financed with a loan", "compré", "lo compré" mean PURCHASED. "Bought it out", "bought out the lease", "lo compré al final del arrendamiento" mean LEASED, THEN PURCHASED.

Do NOT explain why you are asking, and do NOT mention arbitration or whether this affects their case. Only collect the answer.`,
  qLeaseDone: 'The caller has made clear whether they bought the vehicle, still lease it, or leased it and later bought it out.',
  extract: "How the caller got the vehicle. 'purchased' = they bought it (cash, loan or financing). 'leased' = it is on a lease right now. 'lease_buyout' = it started as a lease and they later bought it out. Mis-transcriptions of lease ('liz', 'list', 'lists', 'Rendée', 'renté') and Spanish 'arrendado', 'arrendé', 'rentado' mean lease. If the caller never made it clear, return 'purchased'. Never return 'leased' or 'lease_buyout' unless the caller actually said the vehicle is or was leased.",
  arbLeaseEn: "Since your vehicle is leased, the manufacturer is actually a party to your lease agreement, and that agreement includes a clause requiring disputes to go through arbitration instead of a lawsuit. Our firm only handles cases through the court system, so unfortunately this isn't one we are able to take on.",
  arbLeaseEs: 'Como su vehículo es arrendado, el fabricante en realidad forma parte de su contrato de arrendamiento, y ese contrato incluye una cláusula que exige que las disputas se resuelvan por arbitraje en lugar de una demanda. Nuestra firma solo lleva casos a través de los tribunales, así que lamentablemente este no es un caso que podamos aceptar.',
  arbBuyoutEn: "Since your vehicle started out as a lease, the manufacturer was a party to that original lease agreement, and that agreement includes a clause requiring disputes to go through arbitration instead of a lawsuit. Our firm only handles cases through the court system, so unfortunately this isn't one we are able to take on.",
  arbBuyoutEs: 'Como su vehículo comenzó como un arrendamiento, el fabricante formó parte de ese contrato de arrendamiento original, y ese contrato incluye una cláusula que exige que las disputas se resuelvan por arbitraje en lugar de una demanda. Nuestra firma solo lleva casos a través de los tribunales, así que lamentablemente este no es un caso que podamos aceptar.',
  arbTeslaEn: "Tesla's purchase and lease agreements include a clause requiring disputes to go through arbitration instead of a lawsuit. Our firm only handles cases through the court system, so unfortunately this isn't one we are able to take on.",
  arbTeslaEs: 'Los contratos de compra y de arrendamiento de Tesla incluyen una cláusula que exige que las disputas se resuelvan por arbitraje en lugar de una demanda. Nuestra firma solo lleva casos a través de los tribunales, así que lamentablemente este no es un caso que podamos aceptar.',
  retProcess: `In the caller's language, say this as ONE turn, word for word, then continue.
English: "Great, we can move forward. I'll text and email you the representation agreement to sign. Give me just a few seconds to confirm a couple of details. Then I will walk you through the representation agreement and explain exactly what it covers, so you know what you are signing and have a chance to ask any questions."
Spanish: "Muy bien, podemos seguir adelante. Le voy a enviar por mensaje de texto y por correo el acuerdo de representación para que lo firme. Deme unos segundos para confirmar un par de detalles. Después le explico el acuerdo de representación y exactamente lo que cubre, para que sepa lo que está firmando y pueda hacerme cualquier pregunta."
Do NOT explain the fee structure, the 50% split, the mileage offset, or the next steps here: you will walk through all of that in a moment. Do NOT refer to a different person or a specialist: it is you who will walk them through it. Do NOT mention a consultation link. Do NOT ask them to sign yet.`,
  newUsedOld: 'Ask (caller\'s language): "Did you purchase the car new or used?" Then wait.',
  newUsedNew: 'Ask (caller\'s language): "Was the vehicle new or used when you got it?" In Spanish: "¿El vehículo era nuevo o usado cuando lo obtuvo?" Then wait. Ask it the same way whether the vehicle was bought or leased.',
  cpoOld: 'the vehicle was bought used',
  cpoNew: 'the vehicle was used when they got it',
};

const P = (id, prompt, dest) => ({ id, destination_node_id: dest, transition_condition: { type: 'prompt', prompt } });
const EQ = (id, left, op, right, dest) => ({ id, destination_node_id: dest, transition_condition: { type: 'equation', operator: '&&', equations: [right == null ? { left, operator: op } : { left, operator: op, right }] } });
const swap = (text, oldS, newS, label) => { const n = text.split(oldS).length - 1; if (n !== 1) throw new Error(label + ': expected 1 match, found ' + n); return text.replace(oldS, newS); };

function patch(flow) {
  const byId = (id) => { const n = flow.nodes.find((x) => x.id === id); if (!n) throw new Error('missing node ' + id); return n; };
  if (flow.nodes.some((n) => n.id === 'node-q-lease')) throw new Error('already patched (node-q-lease exists)');
  const log = [];
  const qp = byId('node-q-possession').display_position || { x: 990, y: 126 };
  const dy = byId('node-disq-year').display_position || { x: 2600, y: 1000 };
  const possText = byId('node-disq-possession').instruction.text;
  const pushback = possText.slice(possText.indexOf('IMPORTANT:'));
  if (pushback.indexOf('IMPORTANT: Give this explanation only once.') !== 0) throw new Error('pushback paragraph not found in node-disq-possession');
  const disq = (id, name, en, es, pos) => ({
    id, name, type: 'conversation', skippable: false, display_position: pos,
    instruction: { type: 'prompt', text: `Say this in the caller's language, word for word, as ONE turn, then wait.\nEnglish: "${en}"\nSpanish: "${es}"\n\n${pushback}` },
    edges: [P('e-' + id.replace('node-', '') + '-done', 'Caller acknowledges, accepts it, or has no further questions', 'node-end-bad')],
  });

  // 1. New nodes
  flow.nodes.push(
    { id: 'node-q-lease', name: 'Q: Purchase or Lease', type: 'conversation', skippable: false, start_speaker: 'agent', display_position: { x: qp.x - 200, y: qp.y + 320 }, instruction: { type: 'prompt', text: TXT.qLease }, edges: [P('e-qlease-done', TXT.qLeaseDone, 'node-extract-lease')] },
    { id: 'node-extract-lease', name: 'Extract Purchase Type', type: 'extract_dynamic_variables', skippable: false, display_position: { x: qp.x, y: qp.y + 320 }, variables: [{ name: 'purchase_type_call', type: 'enum', choices: ['purchased', 'leased', 'lease_buyout'], description: TXT.extract }], edges: [P('e-xlease-ok', 'Always', 'node-after-lease')], else_edge: P('e-xlease-else', 'Else', 'node-after-lease') },
    { id: 'node-after-lease', name: 'Route After Lease', type: 'branch', skippable: false, display_position: { x: qp.x + 200, y: qp.y + 320 }, edges: [EQ('e-al-poss', '{{in_possession}}', 'not_exist', null, 'node-q-possession'), EQ('e-al-make', '{{vehicle_make}}', 'not_exist', null, 'node-q-vehicle'), EQ('e-al-year', '{{vehicle_year}}', 'not_exist', null, 'node-q-vehicle')], else_edge: P('e-al-else', 'Else', 'node-extract-vehicle') },
    disq('node-disq-arb-lease', 'Disqualify: Arbitration (Lease)', TXT.arbLeaseEn, TXT.arbLeaseEs, { x: dy.x + 400, y: dy.y }),
    disq('node-disq-arb-buyout', 'Disqualify: Arbitration (Lease Buyout)', TXT.arbBuyoutEn, TXT.arbBuyoutEs, { x: dy.x + 400, y: dy.y + 200 }),
    disq('node-disq-arb-tesla', 'Disqualify: Arbitration (Tesla)', TXT.arbTeslaEn, TXT.arbTeslaEs, { x: dy.x + 400, y: dy.y + 400 }),
  );
  log.push('added q-lease, extract-lease, after-lease, disq-arb-lease/buyout/tesla');

  // 2. Q1 (California) now continues to Q2 instead of possession
  for (const id of ['node-q-ca', 'node-q-ca-confirm']) {
    let hit = 0;
    for (const e of byId(id).edges) if (e.destination_node_id === 'node-q-possession') { e.destination_node_id = 'node-q-lease'; hit++; }
    if (hit !== 1) throw new Error(id + ': expected 1 edge to node-q-possession, found ' + hit);
  }
  log.push('q-ca + q-ca-confirm -> q-lease');

  // 3. Inbound returning-lead recap: ask Q2 if it is not on file (pre-call seeds {{purchase_type}})
  for (const id of ['node-inbound-resume', 'node-inbound-resume-es']) {
    const n = flow.nodes.find((x) => x.id === id);
    if (!n) continue; // outbound flow has no resume nodes
    const i = n.edges.findIndex((e) => e.destination_node_id === 'node-q-ca');
    if (i === -1) throw new Error(id + ': ca_purchase edge not found');
    n.edges.splice(i + 1, 0, EQ('e-' + id.replace('node-', '') + '-lease', '{{purchase_type}}', 'not_exist', null, 'node-q-lease'));
    log.push(id + ': purchase_type not_exist -> q-lease');
  }

  // 4. Bad-reason router
  byId('node-branch-bad').edges.push(
    EQ('e-bad-arb-lease', '{{bad_reason}}', '==', 'arbitration_lease', 'node-disq-arb-lease'),
    EQ('e-bad-arb-buyout', '{{bad_reason}}', '==', 'arbitration_buyout', 'node-disq-arb-buyout'),
    EQ('e-bad-arb-tesla', '{{bad_reason}}', '==', 'arbitration_tesla', 'node-disq-arb-tesla'),
  );
  log.push('branch-bad: 3 arbitration edges');

  // 5. Classifier, reworded questions, AI hand-off line
  byId('node-code-classify').code = CLASSIFY;
  const nu = byId('node-ret-newused'); nu.instruction.text = swap(nu.instruction.text, TXT.newUsedOld, TXT.newUsedNew, 'node-ret-newused');
  const cpo = byId('node-disq-cpo'); cpo.instruction.text = swap(cpo.instruction.text, TXT.cpoOld, TXT.cpoNew, 'node-disq-cpo');
  const rp = byId('node-ret-process');
  if (rp.instruction.text.indexOf("In the caller's language, warmly confirm they qualify") !== 0) throw new Error('node-ret-process text changed since the plan was written');
  rp.instruction = { type: 'prompt', text: TXT.retProcess };
  log.push('classify code, new/used question, CPO line, AI hand-off line');

  // 6. Validate
  const ids = new Set();
  for (const n of flow.nodes) { if (ids.has(n.id)) throw new Error('duplicate node id ' + n.id); ids.add(n.id); }
  const incoming = {};
  for (const n of flow.nodes) for (const e of [...(n.edges || []), ...(n.else_edge ? [n.else_edge] : [])]) {
    if (!ids.has(e.destination_node_id)) throw new Error('dangling edge ' + n.id + ' -> ' + e.destination_node_id);
    incoming[e.destination_node_id] = (incoming[e.destination_node_id] || 0) + 1;
  }
  for (const id of ['node-q-lease', 'node-extract-lease', 'node-after-lease', 'node-disq-arb-lease', 'node-disq-arb-buyout', 'node-disq-arb-tesla']) if (!incoming[id]) throw new Error(id + ' is unreachable');
  return log;
}

(async () => {
  for (const fid of FLOWS) {
    const url = 'https://api.retellai.com/get-conversation-flow/conversation_flow_' + fid;
    const flow = await (await fetch(url, { headers: { Authorization: 'Bearer ' + KEY } })).json();
    const log = patch(flow);
    fs.writeFileSync(path.join(OUT, 'flow_' + fid + '.json'), JSON.stringify(flow, null, 2));
    console.log('\n===== ' + fid + ' (' + flow.nodes.length + ' nodes)\n  ' + log.join('\n  '));
    if (!APPLY) continue;
    const res = await fetch('https://api.retellai.com/update-conversation-flow/conversation_flow_' + fid, { method: 'PATCH', headers: { Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ nodes: flow.nodes }) });
    console.log('  PATCH ' + res.status + (res.ok ? ' OK' : ' ' + (await res.text()).slice(0, 500)));
    const v = await (await fetch(url, { headers: { Authorization: 'Bearer ' + KEY } })).json();
    const g = (id) => v.nodes.find((n) => n.id === id);
    console.log('  verify: q-lease=' + !!g('node-q-lease') + ' classify=' + (g('node-code-classify').code === CLASSIFY) + ' q-ca->' + g('node-q-ca').edges.map((e) => e.destination_node_id).join(',') + ' branch-bad edges=' + g('node-branch-bad').edges.length);
  }
  if (!APPLY) console.log('\nDRY RUN: nothing pushed');
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
```

- [ ] **Step 2: Dry run**

```bash
cd "D:/retell-voice-agents/Knight_Law_Group/automations/lease-filter" && node retell_patch_flows.js
```
Expected: both flows print the change list (the inbound flow also prints the two `resume` lines), no `ERROR`, then `DRY RUN: nothing pushed`.

- [ ] **Step 3: Re-run the classifier tests against the exact code that will be pasted**

```bash
node -e "const f=require('./out/flow_b4e1b9683eaf.json');require('fs').writeFileSync('out/retell_classify_patched.js',f.nodes.find(n=>n.id==='node-code-classify').code)" && node test_retell_classify.js out/retell_classify_patched.js
```
Expected: `failures: 0 / 27`.

- [ ] **Step 4: Read the new node texts once, top to bottom**

```bash
node -e "const f=require('./out/flow_fce8e3f30b49.json');for(const id of ['node-q-lease','node-disq-arb-lease','node-disq-arb-buyout','node-disq-arb-tesla','node-ret-newused','node-ret-process']){const n=f.nodes.find(x=>x.id===id);console.log('\n### '+id+'\n'+n.instruction.text)}"
```
Expected: client lines verbatim; Spanish lines present; no leftover "Did you purchase the car new or used?". Do NOT push yet: the flows are only patched into the DRAFT versions opened in Task 0 (Task 7 Step 4).

---

### Task 5: GHL field + pre-call seeding

**Files:**
- Create: `Knight_Law_Group/automations/lease-filter/ghl_field_id.js`
- Create: `Knight_Law_Group/automations/lease-filter/precall_patch.js`
- Create: `Knight_Law_Group/automations/lease-filter/test_precall.js`
- Modifies (live, on push): workflow `v6S2efil2FR2QrEg` node `Pick Contact + Map Fields`
- Manual (Ubaid, GHL UI): new custom field + router mappings

**Interfaces:**
- Consumes: payload key `custom_analysis_data['Purchase Type']` (Task 3).
- Produces: GHL contact field **Purchase or Lease** (TEXT); pre-call dynamic variable `purchase_type` (value as stored in GHL: `Purchased | Leased | Leased, then purchased`) consumed by the inbound resume edges and `node-code-classify` (Task 4).

- [ ] **Step 1 (Ubaid, GHL UI): create the field**

Settings → Custom Fields → Contact → **Add Field** → *Single Line* (same type as the other intake fields, which are all TEXT) → name **Purchase or Lease** → folder: same folder as "Purchase Condition" → Save.

- [ ] **Step 2 (Ubaid, GHL UI): map it in both intake post-call routers**

In the outbound router workflow (triggered by the `outbound_ghl_url` webhook) and in the inbound router (`inbound_ghl_url`), find the action that writes **Purchase Condition** from the webhook payload. Duplicate that mapping row and point it at **Purchase or Lease**, with source key **Purchase Type** (same path as Purchase Condition, only the last key changes). Save both workflows.

- [ ] **Step 3 (Ubaid, GHL UI): check any branch on Bad Lead Reason**

Search GHL workflows for conditions on *Bad Lead Reason* (for example "Bad Lead Reason is Vehicle year"). For each, confirm a contact with `Requires Arbitration` goes down the correct branch (usually the generic Bad Lead branch). Optional: rename the field label "Did you purchase the car new or used?" to "Was the vehicle new or used when you got it?" (the field key does not change, nothing breaks).

- [ ] **Step 4: Get the new field's ID**

Token: `Knight_Law_Group/.env` key `GHL_KNIGHT_LAW_GROUP` (refreshed 2026-09-29, verified 200 on custom fields and contacts).

`ghl_field_id.js`:
```js
const fs = require('fs');
const line = fs.readFileSync('D:/retell-voice-agents/Knight_Law_Group/.env', 'utf8').split(/\r?\n/).find((l) => l.startsWith('GHL_KNIGHT_LAW_GROUP='));
// the stored value includes a "Bearer " prefix; strip it
const TOK = line.slice(line.indexOf('=') + 1).trim().replace(/^["']|["']$/g, '').replace(/^Bearer\s+/i, '');
(async () => {
  const r = await fetch('https://services.leadconnectorhq.com/locations/vHHnJlFVorkeBvqgaqqA/customFields', { headers: { Authorization: 'Bearer ' + TOK, Version: '2021-07-28', Accept: 'application/json' } });
  if (!r.ok) { console.log('HTTP ' + r.status + ' ' + (await r.text()).slice(0, 200)); process.exit(1); }
  const hit = ((await r.json()).customFields || []).find((f) => f.name.trim().toLowerCase() === 'purchase or lease');
  if (!hit) { console.log('field "Purchase or Lease" not found'); process.exit(1); }
  console.log(hit.id + '  ' + hit.fieldKey + '  ' + hit.dataType);
})();
```
Run: `node ghl_field_id.js` → Expected: `<20-char id>  contact.purchase_or_lease  TEXT`. Keep the id for the next steps.

- [ ] **Step 5: Write the pre-call patcher**

`precall_patch.js`:
```js
// PURCHASE_TYPE_FIELD_ID=<id> node precall_patch.js          -> dry run, writes out/precall_live.js + out/precall_new.js
// PURCHASE_TYPE_FIELD_ID=<id> APPLY=1 node precall_patch.js  -> pushes and verifies
const fs = require('fs');
const path = require('path');
const KEY = fs.readFileSync('D:/tmp/n8nkey.txt', 'utf8').trim();
const BASE = 'https://automations.impleko.ai';
const WF = 'v6S2efil2FR2QrEg';
const H = { 'X-N8N-API-KEY': KEY, 'Content-Type': 'application/json' };
const ID = process.env.PURCHASE_TYPE_FIELD_ID;
if (!/^[A-Za-z0-9]{15,30}$/.test(ID || '')) throw new Error('set PURCHASE_TYPE_FIELD_ID to the id printed by ghl_field_id.js');
const OUT = path.join(__dirname, 'out');
fs.mkdirSync(OUT, { recursive: true });
const rep = (src, a, b, label) => { const n = src.split(a).length - 1; if (n !== 1) throw new Error(label + ': expected 1 match, found ' + n); return src.replace(a, b); };

function patch(src) {
  src = rep(src, "retainer_sent_at:'gFoYMBousYeSonnsbX82'}", "purchase_type:'" + ID + "',retainer_sent_at:'gFoYMBousYeSonnsbX82'}", 'field map');
  src = rep(src, "put('ca_purchase',cf(c,F.ca_purchase));", "put('ca_purchase',cf(c,F.ca_purchase));\nput('purchase_type',cf(c,F.purchase_type));", 'seed');
  src = rep(src, "if(dv.in_possession){parts.push(",
    "if(dv.purchase_type){const __p=String(dv.purchase_type).toLowerCase();parts.push(es?(__p.indexOf('then')!==-1?'lo arrendó y después lo compró':(__p.indexOf('lease')===0?'lo tiene arrendado':'lo compró')):(__p.indexOf('then')!==-1?'you leased it and later bought it out':(__p.indexOf('lease')===0?'you lease it':'you bought it')));}\nif(dv.in_possession){parts.push(",
    'recap');
  return src;
}

(async () => {
  const wf = await (await fetch(`${BASE}/api/v1/workflows/${WF}`, { headers: H })).json();
  const node = wf.nodes.find((n) => /Pick Contact/.test(n.name));
  const live = node.parameters.jsCode.replace(/\r/g, '');
  const next = patch(live);
  fs.writeFileSync(path.join(OUT, 'precall_live.js'), live);
  fs.writeFileSync(path.join(OUT, 'precall_new.js'), next);
  console.log('pre-call ' + live.length + ' -> ' + next.length);
  if (process.env.APPLY !== '1') { console.log('DRY RUN: nothing pushed'); return; }
  node.parameters.jsCode = next;
  const put = await fetch(`${BASE}/api/v1/workflows/${WF}`, { method: 'PUT', headers: H, body: JSON.stringify({ name: wf.name, nodes: wf.nodes, connections: wf.connections, settings: { executionOrder: 'v1' } }) });
  console.log('PUT ' + put.status + (put.ok ? ' OK' : ' ' + (await put.text()).slice(0, 400)));
  const v = await (await fetch(`${BASE}/api/v1/workflows/${WF}`, { headers: H })).json();
  console.log('verify: active=' + v.active + ' code matches=' + (v.nodes.find((n) => /Pick Contact/.test(n.name)).parameters.jsCode.replace(/\r/g, '') === next));
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
```

- [ ] **Step 6: Write the pre-call test**

`test_precall.js`:
```js
const fs = require('fs');
const path = require('path');
const { DateTime } = require('luxon');
const ID = process.env.PURCHASE_TYPE_FIELD_ID;
const NEW = fs.readFileSync(path.join(__dirname, 'out', 'precall_new.js'), 'utf8');
const LIVE = fs.readFileSync(path.join(__dirname, 'out', 'precall_live.js'), 'utf8');
function run(src, contact) {
  const $ = () => ({ first: () => ({ json: { body: { call_inbound: { from_number: '+15555550100' } } } }) });
  const $input = { first: () => ({ json: { contacts: contact ? [contact] : [] } }) };
  return new Function('$', '$input', '$now', src)($, $input, DateTime.now())[0].json.call_inbound.dynamic_variables;
}
const contact = (lang, pt) => ({ id: 'TESTC1', contactName: 'Test Lease Honda', phone: '+15555550100', tags: [], customFields: [
  { id: 'KXtfUXZAiVchURizdzxW', value: 'Incomplete Lead' }, { id: 'Iw4Gtrz6t4It6itTdWY4', value: lang },
  { id: '8hrW19JucZMrvkaInbdq', value: 'Yes' }, { id: 'psMc0nlcBlb4jrgtyT6t', value: 'Yes' },
  { id: 'gswt6GWEUgPVhuveoZBS', value: 'Honda' }, { id: 'Xy9KVmiPlkh1udw4n5Je', value: '2023' },
  ...(pt ? [{ id: ID, value: pt }] : []),
] });
const CASES = [
  ['EN Leased', contact('English', 'Leased'), 'Leased', 'you lease it'],
  ['EN Leased, then purchased', contact('English', 'Leased, then purchased'), 'Leased, then purchased', 'you leased it and later bought it out'],
  ['ES Purchased', contact('Spanish', 'Purchased'), 'Purchased', 'lo compró'],
  ['not on file', contact('English', ''), undefined, null],
];
let fail = 0;
for (const [label, c, wantPt, wantRecap] of CASES) {
  const dv = run(NEW, c);
  const ok = dv.purchase_type === wantPt && (wantRecap === null ? !/lease|bought it|compró|arrend/.test(dv.recap_line) : dv.recap_line.indexOf(wantRecap) !== -1);
  if (!ok) fail++;
  console.log((ok ? '  ok   ' : '  FAIL ') + label.padEnd(28) + ' purchase_type=' + dv.purchase_type + ' | recap: ' + dv.recap_line);
}
// everything the live code returned must be unchanged for a contact without the new field
const a = run(NEW, contact('English', '')), b = run(LIVE, contact('English', ''));
let diffs = 0;
for (const k of Object.keys(b)) if (k !== 'retainer_hours_since' && a[k] !== b[k]) { diffs++; console.log('  DIFF ' + k + ': ' + b[k] + ' -> ' + a[k]); }
const nf = run(NEW, null);
if (nf.contact_found !== 'false') { fail++; console.log('  FAIL not-found fallback'); }
console.log('\nfailures: ' + fail + ' | regressions: ' + diffs);
process.exit(fail + diffs ? 1 : 0);
```

- [ ] **Step 7: Dry run + tests**

```bash
cd "D:/retell-voice-agents/Knight_Law_Group/automations/lease-filter"
PURCHASE_TYPE_FIELD_ID=<id from Step 4> node precall_patch.js
PURCHASE_TYPE_FIELD_ID=<id from Step 4> node test_precall.js
```
Expected: `DRY RUN: nothing pushed`, then 4 `ok` rows and `failures: 0 | regressions: 0`. Do NOT push yet (Task 7).

---

### Task 6: Micol sign-off (gate before go-live)

- [ ] **Step 1: Send Micol this message (short, no em dashes)**

```text
Hi Micol, quick heads up on the lease and Tesla filter. Once it goes live, GHL will start sending Bad Lead Reason "Requires Arbitration", so that value needs to exist in the Salesforce picklist first. We are also adding a new field "Purchase or Lease" (Purchased / Leased / Leased, then purchased) in case you want it mapped to Salesforce. Let us know once the picklist is ready.
```

The three wording / order decisions are already approved by Ubaid (see "Decisions") and are not asked.

- [ ] **Step 2: Confirm Salesforce is ready**

Wait for Micol (or whoever owns the Zap) to confirm "Requires Arbitration" exists in the SF Bad Lead Reason picklist and the Zap passes the value through (if the Zap uses a lookup table for reasons, the new row is added).

---

### Task 7: Deploy — draft first, publish last

Order: backups → n8n and pre-call (safe while the old flow is live: the n8n lease/Tesla rules only fire when the call went through the new lease question) → Retell patch into the DRAFT versions → test calls on the draft (Task 8) → Ubaid publishes.

**Updated steps (supersede Steps 2–5 below where they differ):**
- Step 2 n8n push is safe before the publish (gate `__leaseFlow`; tests prove old-flow Tesla / leased Honda / leased BMW keep the live result).
- Step 4 becomes: `OUT_VER=<draft flow version> IN_VER=<draft flow version> APPLY=1 node retell_patch_flows.js` (from Task 0 Step 5). The script refuses a published version.
- New Step 4b: run Task 8 on the draft. Outbound: `POST /v2/create-phone-call` from +12132053651 to your own phone with `override_agent_id: agent_de01f772a9de26ecf4387115a9`, `override_agent_version: <draft agent version>` and `retell_llm_dynamic_variables` `{Name: "Test Lease Honda", Phone, Email}`. Inbound draft: Retell dashboard test call on the inbound agent's draft version (the number stays on the published version).
- New Step 4c (Ubaid): publish both intake drafts. The number follows `latest_published`; confirm with `POST /v3/list-calls` that the next live calls show the new version.
- Step 5 Retell rollback becomes: pin the number back to the previous numeric version (`PATCH /update-phone-number/+12132053651`, `agent_version: <old version>` for inbound and outbound). No flow restore needed.

- [ ] **Step 1: Back up everything that will change**

```bash
cd "D:/retell-voice-agents/Knight_Law_Group/automations/lease-filter"
node -e "const fs=require('fs');const rk=fs.readFileSync('D:/tmp/retellkey.txt','utf8').trim();const nk=fs.readFileSync('D:/tmp/n8nkey.txt','utf8').trim();fs.mkdirSync('out',{recursive:true});(async()=>{for(const id of ['b4e1b9683eaf','fce8e3f30b49']){const f=await (await fetch('https://api.retellai.com/get-conversation-flow/conversation_flow_'+id,{headers:{Authorization:'Bearer '+rk}})).json();fs.writeFileSync('out/backup_flow_'+id+'.json',JSON.stringify(f));console.log('flow',id,f.nodes.length,'nodes')}for(const id of ['8DuNGcG9ybV3wVlv','v6S2efil2FR2QrEg']){const w=await (await fetch('https://automations.impleko.ai/api/v1/workflows/'+id,{headers:{'X-N8N-API-KEY':nk}})).json();fs.writeFileSync('out/backup_wf_'+id+'.json',JSON.stringify(w));console.log('workflow',id,w.nodes.length,'nodes')}})()"
```
Expected: 4 lines (`flow b4e1b9683eaf 52 nodes`, `flow fce8e3f30b49 59 nodes`, `workflow 8DuNGcG9ybV3wVlv 15 nodes`, `workflow v6S2efil2FR2QrEg …`).

- [ ] **Step 2: Push n8n post-call**

```bash
node test_n8n_classify.js && APPLY=1 node n8n_patch.js
```
Expected: tests pass, then `PUT 200 OK` and `verify: {"active":true,"classify":true,"system":true,"user":true,"payload":true}`.

- [ ] **Step 3: Push the pre-call**

```bash
PURCHASE_TYPE_FIELD_ID=<id> node test_precall.js && PURCHASE_TYPE_FIELD_ID=<id> APPLY=1 node precall_patch.js
```
Expected: `PUT 200 OK`, `verify: active=true code matches=true`.

- [ ] **Step 4: Push the Retell flows**

```bash
node test_retell_classify.js && APPLY=1 node retell_patch_flows.js
```
Expected: per flow `PATCH 200 OK` and `verify: q-lease=true classify=true q-ca->node-q-lease,node-q-ca-confirm branch-bad edges=5`.

- [ ] **Step 5: Rollback (only if something breaks)**

```bash
# Retell: put the pre-change nodes back
node -e "const fs=require('fs');const k=fs.readFileSync('D:/tmp/retellkey.txt','utf8').trim();(async()=>{for(const id of ['b4e1b9683eaf','fce8e3f30b49']){const b=JSON.parse(fs.readFileSync('out/backup_flow_'+id+'.json','utf8'));const r=await fetch('https://api.retellai.com/update-conversation-flow/conversation_flow_'+id,{method:'PATCH',headers:{Authorization:'Bearer '+k,'Content-Type':'application/json'},body:JSON.stringify({nodes:b.nodes})});console.log('restore flow',id,r.status)}})()"
# n8n: put the pre-change workflows back
node -e "const fs=require('fs');const k=fs.readFileSync('D:/tmp/n8nkey.txt','utf8').trim();(async()=>{for(const id of ['8DuNGcG9ybV3wVlv','v6S2efil2FR2QrEg']){const w=JSON.parse(fs.readFileSync('out/backup_wf_'+id+'.json','utf8'));const r=await fetch('https://automations.impleko.ai/api/v1/workflows/'+id,{method:'PUT',headers:{'X-N8N-API-KEY':k,'Content-Type':'application/json'},body:JSON.stringify({name:w.name,nodes:w.nodes,connections:w.connections,settings:{executionOrder:'v1'}})});console.log('restore workflow',id,r.status)}})()"
```
Expected: `200` for each. Retell and n8n can be rolled back independently.

---

### Task 8: Live test calls (Ubaid) and verification

Use a GHL contact named with "test" (e.g. **Test Lease Honda**) on your own phone and email: the retainer scenario really sends the agreement. For each call, read the transcript (not just the status), then check the n8n execution of `8DuNGcG9ybV3wVlv` (`Classify Lead` output, `Build Payload` body), the GHL contact fields (Lead Status, Bad Lead Reason, Purchase or Lease) and the call note.

| # | Scenario (what you say) | Expected on the call | Expected in GHL |
|---|---|---|---|
| A | EN outbound. Q1: "Yes, I leased it in LA." Then "still leased", 2023 Honda Civic | Alice does NOT ask "purchase or lease", asks only "still leased, or bought it out?"; says the lease arbitration line; ends | Bad Lead / Requires Arbitration / Leased |
| B | ES outbound. Q1: "No, lo arrendé." Then location confirm "en California", "después lo compré", 2022 Acura | Location confirm, not out-of-state; buyout follow-up; Spanish buyout line | Bad Lead / Requires Arbitration / Leased, then purchased |
| C | EN. Purchased, 2024 Tesla Model 3 | Tesla line | Bad Lead / Requires Arbitration / Purchased |
| D | EN. Leased then bought out, 2023 BMW X3 | Non-Retainer close (booking link) | Non-Retainer Lead / Leased, then purchased |
| E | EN. Leased, still leased, 2023 Ford, used, CPO yes, repairs yes, owner yes | "Was the vehicle new or used when you got it?"; AI hand-off line word for word; agreement sent; retainer agent takes over | Retainer Lead / Leased |
| F | EN. Q2: "It's financed." Then "a loan", 2023 Honda | Alice asks lease-or-loan once; Non-Retainer | Non-Retainer Lead / Purchased |
| G | Inbound call from the test contact set to Incomplete Lead with California, possession, make and year on file and Purchase or Lease EMPTY; then fill Purchase or Lease = Purchased and call again | 1st call: recap, then Q2 asked. 2nd call: recap mentions "you bought it", Q2 NOT asked | Purchase or Lease updated after call 1 |

- [ ] **Step 1: Place calls A–G** and fill in the table with call IDs and pass/fail.
- [ ] **Step 2: Confirm Salesforce** shows Bad Lead Reason "Requires Arbitration" for A, B, C (Zapier run history).
- [ ] **Step 3: Fix anything that failed** by editing the relevant `TXT.*` text or rule, rerun the tests, `APPLY=1` again (the flow patcher refuses to run on an already-patched flow: run the Task 7 Step 5 Retell restore first, then `APPLY=1 node retell_patch_flows.js` again).

---

### Task 9: Close-out

- [ ] **Step 1: Update memory** `project_knight_law_leased_filter.md`: status LIVE, date, node ids, Micol's answers to the 3 questions, test call ids.
- [ ] **Step 2: Mark the old script as superseded**: add one line at the top of `Knight_Law_Group/Knight Law - Internal Intake Script - Alice (+Leased).md`: `> Superseded by NEW - Knight Law - Internal Intake Script - Alice (+Leased).md (2026-09-28).`
- [ ] **Step 3: Commit, only when Ubaid says so**

```bash
cd "D:/retell-voice-agents"
git add "Knight_Law_Group/NEW - Knight Law - Internal Intake Script - Alice (+Leased).md" "Knight_Law_Group/NEW - Knight Law - Internal Intake Script - Alice (+Leased).docx" "Knight_Law_Group/plans/2026-09-28-lease-tesla-arbitration-plan.md" "Knight_Law_Group/automations/lease-filter" "Knight_Law_Group/Knight Law - Internal Intake Script - Alice (+Leased).md"
git commit -m "Knight Law: lease + Tesla arbitration filter (script, plan, patch scripts)"
```

---

## What does NOT change

- **Retainer agents** (`agent_83f8b296…` outbound cadence, `agent_7540b5be…` immediate): their prompts already say the buyback refunds "what was paid toward the purchase or lease". No edit.
- **Retainer post-call** (`DU0LE0flap97hU3W`): no edit.
- **GHL dialer body**: no new variable needed (outbound leads have no purchase type on file; Alice asks).
- **Legacy flows** V27 (`5c14270ba401`) and V30 (`bc0fa972ddf4`): not bound to any number.
