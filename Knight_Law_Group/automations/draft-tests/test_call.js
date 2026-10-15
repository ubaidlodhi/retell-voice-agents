// Test calls for everything sitting in the Knight Law DRAFT versions (scripts: TEST-GUIDE.md).
// The live number stays on the published versions, so real leads are never affected.
//   node test_call.js call <1-7> --to +1XXXXXXXXXX --email you@example.com [--version N]
//        -> places an outbound call from (213) 205-3651 to your phone on the draft version
//   node test_call.js check <call_id> <1-7>
//        -> waits for the call to end, prints the checks, the route Alice took, the n8n payload and the transcript
const fs = require('fs');
const RK = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const NK = fs.readFileSync('D:/tmp/n8nkey.txt', 'utf8').trim();
const RH = { Authorization: 'Bearer ' + RK, 'Content-Type': 'application/json' };
const FROM = '+12132053651';
const INTAKE = 'agent_de01f772a9de26ecf4387115a9'; // intake outbound
const RETAINER_OUT = 'agent_83f8b296e4652030d15a3417e6';
const INTAKE_POSTCALL = '8DuNGcG9ybV3wVlv';

// vars: in-call collected variables that must match. n8n: GHL payload fields (Build Payload) that must match.
// notSay: things Alice must never say on this call (case-insensitive).
const NEVER = ['so you mean it was new', '{{'];
const S = {
  1: { title: 'EN - retainer path, listening + empathy, FAQ mid-call, AI hand-off', agent: INTAKE, name: 'John Test Retainer Ford',
    vars: { route: 'retainer' }, notSay: NEVER.concat(['did you purchase the vehicle, or lease it']),
    say: ["i'll text and email you the representation agreement"], n8n: { 'Lead Status': 'Retainer Lead' } },
  2: { title: 'EN - non-retainer (used, CPO unsure), neutral re-ask, transfer offer declined', agent: INTAKE, name: 'John Test Nissan Used',
    vars: { route: 'non_retainer' }, notSay: NEVER,
    say: ['new or used', 'certified'], n8n: { 'Lead Status': 'Non-Retainer Lead', 'Non-Retainer Live Transfer': 'No' } },
  3: { title: 'EN - lease buyout BMW -> non-retainer -> LIVE TRANSFER accepted (Mon-Fri 8 AM-8 PM PT)', agent: INTAKE, name: 'John Test Buyout BMW',
    vars: { purchase_type_call: 'lease_buyout', route: 'non_retainer', nonret_hours: 'open', nonret_live_transfer: 'attempted' }, notSay: NEVER,
    say: ['available right now'], n8n: { 'Lead Status': 'Non-Retainer Lead', 'Non-Retainer Live Transfer': 'Yes' }, transferred: true },
  4: { title: 'EN - callback from the opening: outside calling hours, then a booked time, then a correction', agent: INTAKE, name: 'John Test Callback Window',
    vars: { callback_status: 'in_window', callback_next: 'confirm' }, notSay: NEVER, say: ['between 8 am and 9 pm', 'tomorrow at 6 pm'],
    n8n: { 'Callback Requested': 'Yes', 'Callback Outside Window': false, 'Callback Parse Failed': false }, callbackPacificEnds: '06:00 PM' },
  5: { title: 'EN - callback mid-call, asked for next week -> outside the 3-day window', agent: INTAKE, name: 'John Test Callback Week',
    vars: { callback_status: 'out_of_window', callback_next: 'out' }, notSay: NEVER, say: ['will contact you soon'],
    n8n: { 'Callback Requested': 'Yes', 'Callback Outside Window': true, 'Callback Datetime ISO': '' } },
  6: { title: 'EN - "making payments" -> loan, Tesla -> Tesla arbitration word for word, pushback', agent: INTAKE, name: 'John Test Tesla Loan',
    vars: { purchase_type_call: 'purchased', bad_reason: 'arbitration_tesla', call_language: 'English' }, notSay: NEVER,
    say: ['is that a lease, or a loan', "tesla's purchase and lease agreements include a clause requiring disputes to go through arbitration instead of a lawsuit"],
    n8n: { 'Lead Status': 'Bad Lead', 'Bad Lead Reason': 'Requires Arbitration', 'Purchase Type': 'Purchased' } },
  7: { title: 'Retainer Outbound draft v4 - "stuck" rule: repeated money question + guarantee demand -> offers the intake team', agent: RETAINER_OUT, name: 'John Test Stuck Rule',
    retainer: true, vars: {}, notSay: ['check back tomorrow', 'tomorrow night'], say: ['intake team', 'tonight at 8'], n8n: {} },
};

const arg = (k) => { const i = process.argv.indexOf(k); return i > -1 ? process.argv[i + 1] : ''; };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const get = async (p) => (await fetch('https://api.retellai.com' + p, { headers: RH })).json();

async function draftVersion(agent) {
  if (arg('--version')) return Number(arg('--version'));
  const r = await get('/list-agent-versions/' + agent + '?limit=20');
  const d = (Array.isArray(r) ? r : r.items || []).filter((v) => !v.is_published).sort((a, b) => b.version - a.version)[0];
  if (!d) throw new Error('no draft version of ' + agent);
  return d.version;
}

async function place(n) {
  const s = S[n]; const to = arg('--to'); const email = arg('--email');
  if (!s || !/^\+1\d{10}$/.test(to) || !email) throw new Error('usage: node test_call.js call <1-7> --to +1XXXXXXXXXX --email you@example.com');
  const version = await draftVersion(s.agent);
  const first = s.name.split(' ')[0];
  const vars = s.retainer
    ? { first_name: first, full_name: s.name, phone: to, email, lead_language: 'English', greeting: 'Hi, is this ' + first + '?', call_number: '1',
      voicemail_script: 'Hi ' + first + ', this is Alice with Knight Law Group about your representation agreement. Call us at (213) 205-3651.', agreement_link: '' }
    : { Name: s.name, Phone: to, Email: email, lead_language: '' };
  const body = { from_number: FROM, to_number: to, override_agent_id: s.agent, override_agent_version: version, retell_llm_dynamic_variables: vars };
  const r = await fetch('https://api.retellai.com/v2/create-phone-call', { method: 'POST', headers: RH, body: JSON.stringify(body) });
  const j = await r.json();
  if (!r.ok) throw new Error('create-phone-call HTTP ' + r.status + ' ' + JSON.stringify(j).slice(0, 300));
  console.log('Test ' + n + ': ' + s.title + '\nCalling ' + to + ' on DRAFT v' + version + ' as "' + s.name + '"\ncall_id: ' + j.call_id + '\nWhen done: node test_call.js check ' + j.call_id + ' ' + n);
}

async function n8nPayload(callId) {
  try {
    const list = await (await fetch('https://automations.impleko.ai/api/v1/executions?workflowId=' + INTAKE_POSTCALL + '&limit=20', { headers: { 'X-N8N-API-KEY': NK } })).json();
    for (const e of list.data || []) {
      const d = await (await fetch('https://automations.impleko.ai/api/v1/executions/' + e.id + '?includeData=true', { headers: { 'X-N8N-API-KEY': NK } })).json();
      if (!JSON.stringify(d.data || {}).includes(callId)) continue;
      const run = d.data.resultData.runData['Build Payload'];
      const out = run && run[0] && run[0].data && run[0].data.main[0][0].json;
      if (out) return Object.assign({ __exec: e.id + ' (' + e.status + ')' }, out.payload.call.call_analysis.custom_analysis_data);
    }
  } catch (e) { /* n8n unreachable */ }
  return null;
}

async function check(callId, n) {
  const s = S[n]; if (!s || !callId) throw new Error('usage: node test_call.js check <call_id> <1-7>');
  let c;
  for (let i = 0; i < 40; i++) {
    c = await get('/v2/get-call/' + callId);
    if (c.call_status === 'ended' && c.call_analysis) break;
    if (i === 0) console.log('waiting for the call to end and be analyzed...');
    await sleep(6000);
  }
  const lines = String(c.transcript || '').split('\n');
  const agentLines = lines.filter((l) => l.startsWith('Agent:'));
  const said = agentLines.join('\n').toLowerCase();
  const v = c.collected_dynamic_variables || {};
  const res = [];
  const t = (ok, label) => res.push((ok ? 'PASS ' : 'FAIL ') + label);
  t(true, 'ran on agent version v' + c.agent_version);
  for (const p of s.say) t(said.includes(p.toLowerCase()), 'Alice said "' + p + '"');
  for (const p of s.notSay) t(!said.includes(p.toLowerCase()), 'Alice never said "' + p + '"');
  for (const [k, want] of Object.entries(s.vars)) t(v[k] === want, 'in-call ' + k + ' = ' + want + ' (got ' + JSON.stringify(v[k]) + ')');
  if (s.transferred) t(c.disconnection_reason === 'call_transfer', 'call ended in a transfer (got ' + c.disconnection_reason + ')');
  if (!s.retainer) {
    const okay = agentLines.filter((l) => /^Agent:\s*(okay|ok)\b/i.test(l)).length;
    res.push('INFO ' + okay + ' of ' + agentLines.length + ' Alice turns start with "Okay" (was 12% before)');
    if (Object.keys(s.n8n).length) {
      let p = null;
      for (let i = 0; i < 10 && !p; i++) { p = await n8nPayload(callId); if (!p) await sleep(6000); }
      if (!p) res.push('SKIP n8n: no intake post-call execution for this call yet');
      else {
        for (const [k, want] of Object.entries(s.n8n)) t(p[k] === want, 'n8n ' + k + ' = ' + JSON.stringify(want) + ' (got ' + JSON.stringify(p[k]) + ')' + (s.n8nNote ? ' [' + s.n8nNote + ']' : ''));
        if (s.callbackPacificEnds) {
          t(p['Callback Datetime Pacific'] === v.callback_at_pacific && String(v.callback_at_pacific).endsWith(s.callbackPacificEnds),
            'n8n callback time = the time Alice confirmed (' + p['Callback Datetime Pacific'] + ' / ' + v.callback_at_pacific + ')');
        }
        res.push('INFO n8n exec ' + p.__exec + ' | Lead Status ' + p['Lead Status'] + ' | Callback ' + p['Callback Requested'] + ' ' + p['Callback Datetime Pacific'] + ' | Live Transfer ' + p['Non-Retainer Live Transfer']);
      }
    }
  }
  const path = (c.transcript_with_tool_calls || []).filter((x) => x.role === 'node_transition').map((x) => x.new_node_name);
  console.log('\nTest ' + n + ': ' + s.title + '\ncall ' + callId + ' | ' + Math.round(((c.end_timestamp || 0) - (c.start_timestamp || 0)) / 1000) + ' s | ' + c.disconnection_reason + '\n');
  res.forEach((l) => console.log('  ' + l));
  const failed = res.filter((l) => l.startsWith('FAIL')).length;
  console.log('\n' + (failed ? failed + ' FAILED' : 'ALL CHECKS PASSED') + ' — now read the transcript: does she react to what you said, and sound natural?');
  if (path.length) console.log('\nRoute: ' + path.join(' > '));
  console.log('\n' + c.transcript);
}

(async () => {
  const [cmd, a, b] = process.argv.slice(2);
  if (cmd === 'call') await place(a);
  else if (cmd === 'check') await check(a, b);
  else console.log('node test_call.js call <1-7> --to +1XXXXXXXXXX --email you@example.com\nnode test_call.js check <call_id> <1-7>');
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
