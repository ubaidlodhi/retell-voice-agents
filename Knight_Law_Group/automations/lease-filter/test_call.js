// Quick test runner for the lease / Tesla changes on the DRAFT intake agent (live number stays on the published version).
//
//   node test_call.js call <A|B|C|D> --to +1XXXXXXXXXX --email you@example.com [--version N]
//        -> places an outbound test call from (213) 205-3651 to your phone, on the draft version
//   node test_call.js check <call_id> <A|B|C|D>
//        -> waits for the call to finish, then prints PASS/FAIL for that scenario (Retell + n8n)
//
// Scenarios and what to say: TEST-SCRIPT.md. Current Retell endpoints only.
const fs = require('fs');
const RK = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const NK = fs.readFileSync('D:/tmp/n8nkey.txt', 'utf8').trim();
const RH = { Authorization: 'Bearer ' + RK, 'Content-Type': 'application/json' };
const AGENT = 'agent_de01f772a9de26ecf4387115a9'; // intake outbound
const FROM = '+12132053651';

// What each scenario must show. say/notSay = distinctive substrings of Alice's lines (case-insensitive).
const S = {
  A: {
    title: 'EN - leased (said in Q1), still leased, Honda -> lease arbitration',
    name: 'Test Lease Honda', lang: '',
    // "did you purchase the vehicle, or lease it" MAY be asked again if the transcriber garbles "I leased it"
    // (Sep 29 test: "I'll leave it in LA"); that is the safe fallback, so it is not checked here.
    say: ['calling about the lemon law inquiry', 'still leased', 'party to your lease agreement'],
    notSay: [],
    vars: { purchase_type_call: 'leased', bad_reason: 'arbitration_lease' },
    n8n: { lead_status: 'Bad Lead', bad_lead_reason: 'Requires Arbitration', purchase_type: 'Leased' },
  },
  B: {
    title: 'ES - "¿Bueno?" pickup, leased then bought, Acura -> buyout arbitration (Spanish)',
    name: 'Test Buyout Acura', lang: '',
    say: ['le habla alice, de knight law group', 'lo arrendó', 'comenzó como un arrendamiento'],
    notSay: [],
    vars: { purchase_type_call: 'lease_buyout', bad_reason: 'arbitration_buyout' },
    n8n: { lead_status: 'Bad Lead', bad_lead_reason: 'Requires Arbitration', purchase_type: 'Leased, then purchased' },
  },
  C: {
    title: 'EN - bought, 2024 Tesla -> Tesla arbitration',
    name: 'Test Tesla', lang: '',
    say: ['did you purchase the vehicle, or lease it', 'purchase and lease agreements include a clause'],
    notSay: ['party to your lease agreement'],
    vars: { purchase_type_call: 'purchased', bad_reason: 'arbitration_tesla' },
    n8n: { lead_status: 'Bad Lead', bad_lead_reason: 'Requires Arbitration', purchase_type: 'Purchased' },
  },
  D: {
    title: 'EN - "financed" -> lease, Ford, used CPO -> retainer; name spelled by caller; AI hand-off',
    name: 'Test Retainer Ford', lang: '',
    say: ['is that a lease, or a loan', 'new or used when you got it', 'great, we can move forward'],
    notSay: [],
    vars: { purchase_type_call: 'leased', route: 'retainer' },
    maxAgentSpellings: 0, // caller says the license name is different and spells it: Alice must NOT spell it back
    needConfirmedName: true,
    n8n: { lead_status: 'Retainer Lead', purchase_type: 'Leased' },
  },
};

const arg = (k) => { const i = process.argv.indexOf(k); return i > -1 ? process.argv[i + 1] : ''; };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function draftVersion() {
  if (arg('--version')) return Number(arg('--version'));
  const r = await (await fetch('https://api.retellai.com/list-agent-versions/' + AGENT + '?limit=10', { headers: RH })).json();
  const d = (r.items || []).filter((v) => !v.is_published).sort((a, b) => b.version - a.version)[0];
  if (!d) throw new Error('No draft version of the intake agent exists yet. Open one first (plan Task 0 Step 5) and apply the lease patch.');
  return d.version;
}

async function place(sc) {
  const s = S[sc]; const to = arg('--to'); const email = arg('--email');
  if (!s || !/^\+1\d{10}$/.test(to) || !email) throw new Error('usage: node test_call.js call <A|B|C|D> --to +1XXXXXXXXXX --email you@example.com');
  const version = await draftVersion();
  const body = { from_number: FROM, to_number: to, override_agent_id: AGENT, override_agent_version: version, retell_llm_dynamic_variables: { Name: s.name, Phone: to, Email: email, lead_language: s.lang } };
  const r = await fetch('https://api.retellai.com/v2/create-phone-call', { method: 'POST', headers: RH, body: JSON.stringify(body) });
  const j = await r.json();
  if (!r.ok) throw new Error('create-phone-call HTTP ' + r.status + ' ' + JSON.stringify(j).slice(0, 300));
  console.log('Scenario ' + sc + ': ' + s.title + '\nCalling ' + to + ' on DRAFT v' + version + ' as "' + s.name + '"\ncall_id: ' + j.call_id + '\nWhen done: node test_call.js check ' + j.call_id + ' ' + sc);
}

async function check(callId, sc) {
  const s = S[sc]; if (!s || !callId) throw new Error('usage: node test_call.js check <call_id> <A|B|C|D>');
  let c;
  for (let i = 0; i < 40; i++) { // up to ~4 min for the call to end and be analyzed
    c = await (await fetch('https://api.retellai.com/v2/get-call/' + callId, { headers: RH })).json();
    if (c.call_status === 'ended' && c.call_analysis) break;
    if (i === 0) console.log('waiting for the call to end and be analyzed...');
    await sleep(6000);
  }
  const lines = String(c.transcript || '').split('\n');
  const agentText = lines.filter((l) => l.startsWith('Agent:')).join('\n').toLowerCase();
  const v = c.collected_dynamic_variables || {};
  const res = [];
  const t = (ok, label) => res.push((ok ? 'PASS ' : 'FAIL ') + label);
  t(c.agent_version !== undefined, 'ran on agent version v' + c.agent_version + ' (should be the draft)');
  for (const p of s.say) t(agentText.includes(p.toLowerCase()), 'Alice said "' + p + '"');
  for (const p of s.notSay) t(!agentText.includes(p.toLowerCase()), 'Alice did NOT say "' + p + '"');
  for (const [k, want] of Object.entries(s.vars)) t(v[k] === want, 'in-call ' + k + ' = ' + want + ' (got ' + JSON.stringify(v[k]) + ')');
  if (s.maxAgentSpellings !== undefined) {
    const spelled = lines.filter((l) => l.startsWith('Agent:') && (/\b[A-Z] - [A-Z] - [A-Z]\b/.test(l) || /\b(eme|ene|ese|ere|te|jota|ele), (a|e|i|o|u|eme|ene|ese|ere|te), /.test(l))).length;
    t(spelled <= s.maxAgentSpellings, 'Alice spelled a name ' + spelled + ' time(s) (max ' + s.maxAgentSpellings + ')');
  }
  if (s.needConfirmedName) {
    t(!!v.confirmed_name, 'confirmed_name captured: ' + JSON.stringify(v.confirmed_name || ''));
    const first = String(v.confirmed_name || '').trim().split(/\s+/)[0];
    t(!!first && String(v.greeting || '').includes(first), 'hand-off greeting uses the confirmed first name "' + first + '"');
  }

  // n8n intake post-call result for this call (needs n8n running + the lease patch pushed)
  let cls = null;
  try {
    const list = await (await fetch('https://automations.impleko.ai/api/v1/executions?workflowId=8DuNGcG9ybV3wVlv&limit=15', { headers: { 'X-N8N-API-KEY': NK } })).json();
    for (const e of list.data || []) {
      const d = await (await fetch('https://automations.impleko.ai/api/v1/executions/' + e.id + '?includeData=true', { headers: { 'X-N8N-API-KEY': NK } })).json();
      if (!JSON.stringify(d.data || {}).includes(callId)) continue;
      const run = d.data.resultData.runData['Classify Lead'];
      cls = run && run[0] && run[0].data && run[0].data.main[0][0].json;
      if (cls) { cls.__exec = e.id + ' (' + e.status + ')'; break; }
    }
  } catch (e) { /* n8n unreachable */ }
  if (!cls) res.push('SKIP n8n: no finished intake post-call execution for this call yet (n8n down, still running, or not pushed)');
  else for (const [k, want] of Object.entries(s.n8n)) t(cls[k] === want, 'n8n ' + k + ' = ' + want + ' (got ' + JSON.stringify(cls[k]) + ', exec ' + cls.__exec + ')');

  console.log('\nScenario ' + sc + ': ' + s.title + '\ncall ' + callId + ' | ' + Math.round(((c.end_timestamp || 0) - (c.start_timestamp || 0)) / 1000) + ' s | ' + c.disconnection_reason + '\n');
  res.forEach((l) => console.log('  ' + l));
  const failed = res.filter((l) => l.startsWith('FAIL')).length;
  console.log('\n' + (failed ? failed + ' FAILED - read the transcript below' : 'ALL PASSED'));
  if (failed) console.log('\n' + c.transcript);
}

(async () => {
  const [cmd, a, b] = process.argv.slice(2);
  if (cmd === 'call') await place(a);
  else if (cmd === 'check') await check(a, b);
  else console.log('node test_call.js call <A|B|C|D> --to +1XXXXXXXXXX --email you@example.com\nnode test_call.js check <call_id> <A|B|C|D>');
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
