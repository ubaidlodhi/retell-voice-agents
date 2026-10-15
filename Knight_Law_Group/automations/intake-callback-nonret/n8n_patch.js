// n8n "Knight Law - Intake Post Call (Voice AI Review)" (8DuNGcG9ybV3wVlv) — two additive, gated changes:
//   1. Classify Lead: when the intake flow booked the callback itself (collected var callback_status, only set by the
//      new draft flow), its resolved time / 3-day-window decision wins over the transcript parse.
//      out_of_window -> Callback Requested Yes, no time, new key 'Callback Outside Window' = true (normal cadence + NBA).
//   2. Build Payload: new key 'Non-Retainer Live Transfer' = 'Yes' when Alice live-transferred a non-retainer lead
//      (collected var nonret_live_transfer = 'attempted' AND the call ended in a transfer), else 'No'.
//      Lead Status stays Non-Retainer Lead; GHL uses this key to keep the lead out of the normal follow-up cadence.
// Calls from the published flow carry neither variable, so their payload only gains the two keys at their defaults.
//   node n8n_patch.js          -> fetch live, patch in memory, run the tests (no write)
//   PUSH=1 node n8n_patch.js   -> same, then PUT and verify
const fs = require('fs');
const path = require('path');
const { DateTime } = require('../lease-filter/node_modules/luxon');
const KEY = fs.readFileSync('D:/tmp/n8nkey.txt', 'utf8').trim();
const BASE = 'https://automations.impleko.ai/api/v1/workflows/8DuNGcG9ybV3wVlv';
const OUT = path.join(__dirname, 'out');
fs.mkdirSync(OUT, { recursive: true });

const CL_ANCHOR = "const __cb = __cbRaw ? __parseCallback(__cbRaw) : { cbIso: '', cbPac: '', cbFail: __cbRequested };";
const CL_INSERT = `
// The intake flow (new draft) books the callback itself: it resolved the time and the 3-day follow-up window during
// the call, so its answer wins over the transcript parse. Calls from older flows have no callback_status: unchanged.
const __fcv = call.collected_dynamic_variables || {};
const __flowCb = String(__fcv.callback_status || '');
let __cbReq = __cbRequested, __cbRawOut = __cbRaw, __cbIso = __cb.cbIso, __cbPac = __cb.cbPac, __cbFail = __cb.cbFail, __cbOutside = false;
if (__cbAllowed && __flowCb === 'in_window' && txt(__fcv.callback_at_iso)) {
  __cbReq = true; __cbRawOut = __cbRaw || txt(__fcv.callback_when_en); __cbIso = txt(__fcv.callback_at_iso); __cbPac = txt(__fcv.callback_at_pacific); __cbFail = false;
} else if (__cbAllowed && __flowCb === 'out_of_window') {
  // Asked for a time after the follow-up window: Alice said the team will contact them soon, the normal cadence continues.
  __cbReq = true; __cbIso = ''; __cbPac = ''; __cbFail = false; __cbOutside = true;
}`;
const CL_OUT_FROM = `  callback_requested: __cbRequested ? 'Yes' : 'No',
  callback_datetime: __cbRaw || 'N/A',
  callback_datetime_iso: __cb.cbIso,
  callback_datetime_pacific: __cb.cbPac,
  callback_parse_failed: __cb.cbFail`;
const CL_OUT_TO = `  callback_requested: __cbReq ? 'Yes' : 'No',
  callback_datetime: __cbRawOut || 'N/A',
  callback_datetime_iso: __cbIso,
  callback_datetime_pacific: __cbPac,
  callback_parse_failed: __cbFail,
  callback_outside_window: __cbOutside`;
const BP_FROM = "  'Callback Parse Failed': c.callback_parse_failed === true,";
const BP_TO = `  'Callback Parse Failed': c.callback_parse_failed === true,
  'Callback Outside Window': c.callback_outside_window === true,
  // Non-retainer lead Alice live-transferred to an Intake Analyst (Mon-Fri 8 AM-8 PM PT). Lead Status is unchanged;
  // GHL keeps these leads out of the normal follow-up cadence.
  'Non-Retainer Live Transfer': ((call.collected_dynamic_variables || {}).nonret_live_transfer === 'attempted' && call.disconnection_reason === 'call_transfer') ? 'Yes' : 'No',`;

const once = (s, from, to, label) => { const n = s.split(from).length - 1; if (n !== 1) throw new Error(label + ': anchor found ' + n + ' times'); return s.replace(from, () => to); };

function patchCodes(wf) {
  const cl = wf.nodes.find((n) => n.name === 'Classify Lead'), bp = wf.nodes.find((n) => n.name === 'Build Payload');
  if (cl.parameters.jsCode.indexOf('__flowCb') !== -1) throw new Error('already patched');
  let c = once(cl.parameters.jsCode, CL_ANCHOR, CL_ANCHOR + CL_INSERT, 'Classify anchor');
  c = once(c, CL_OUT_FROM, CL_OUT_TO, 'Classify output');
  const b = once(bp.parameters.jsCode, BP_FROM, BP_TO, 'Build Payload');
  return { classify: c, build: b, oldClassify: cl.parameters.jsCode, oldBuild: bp.parameters.jsCode };
}

// ---------- run the node code with n8n stubs ----------
function runNode(code, nodes) {
  const $ = (name) => ({ first: () => ({ json: nodes[name] }), item: { json: nodes[name] } });
  const $input = { first: () => ({ json: nodes.$input }) };
  const fn = new Function('$', '$input', '$now', '$execution', '$workflow', code);
  return fn($, $input, DateTime.now().setZone('America/Los_Angeles'), { id: 'test' }, { id: 'test' })[0].json;
}
const AI = (o) => ({ content: [{ type: 'text', text: JSON.stringify(Object.assign({
  lead_language: 'English', opt_out: 'No', is_voicemail: 'No', requested_human: 'No', declined_ai: 'No', issue: 'Yes', ca_purchase: 'Yes',
  in_possession: 'Yes', vehicle_year: '2023', vehicle_make: 'Honda', vehicle_model: 'Civic', new_or_used: 'N/A', is_cpo: 'N/A',
  repairs_attempted: 'N/A', is_owner: 'N/A', full_name: 'John Doe', confirmed_email: 'jane@acme.ai', contact_consent: 'Yes',
  call_dnd: false, sms_dnd: false, email_dnd: false, callback_requested: 'No', callback_datetime: 'N/A', call_summary: 'Test summary.' }, o)) }] });
const CALL = (o) => Object.assign({ call_id: 'call_test', agent_id: 'agent_test', direction: 'outbound', disconnection_reason: 'user_hangup',
  start_timestamp: Date.now() - 120000, end_timestamp: Date.now(), transcript: 'Agent: Hi, this is Alice.\nUser: Hi, yes my car has issues and I want help with it please.\nAgent: Okay.',
  retell_llm_dynamic_variables: { Name: 'John Doe', Phone: '+15555550123', Email: 'jane@acme.ai', lead_language: 'English' }, collected_dynamic_variables: {} }, o);

function pipeline(codes, call, ai) {
  const webhook = { body: { call } };
  const cl = runNode(codes.classify, { Webhook: webhook, $input: ai });
  // NBA Gate / NBA Decide pass the Classify object through unchanged (+ NBA keys); simulate that.
  const bp = runNode(codes.build, { Webhook: webhook, $input: Object.assign({}, cl, { nba_reason: '' }) });
  return { cl, cad: bp.payload.call.call_analysis.custom_analysis_data };
}

function test(p) {
  const NEW = { classify: p.classify, build: p.build }, OLD = { classify: p.oldClassify, build: p.oldBuild };
  let fails = 0;
  const expect = (label, got, want) => {
    const bad = Object.keys(want).filter((k) => JSON.stringify(got[k]) !== JSON.stringify(want[k]));
    if (bad.length) { fails++; console.log('FAIL ' + label + ': ' + bad.map((k) => k + '=' + JSON.stringify(got[k]) + ' (want ' + JSON.stringify(want[k]) + ')').join(', ')); }
    else console.log('ok   ' + label);
  };
  // legacy calls (published flow): identical output apart from the two new keys at their defaults
  const legacy = [
    ['legacy non-retainer', CALL({}), AI({ vehicle_make: 'Honda' })],
    ['legacy transcript callback', CALL({}), AI({ vehicle_make: '', vehicle_year: '', callback_requested: 'Yes', callback_datetime: 'tomorrow at 11 AM' })],
    ['legacy warm transfer (consent refused)', CALL({ disconnection_reason: 'call_transfer' }), AI({ contact_consent: 'No' })],
    ['legacy voicemail', CALL({ disconnection_reason: 'voicemail_reached' }), AI({ is_voicemail: 'Yes' })],
  ];
  for (const [label, call, ai] of legacy) {
    const a = pipeline(OLD, call, ai), b = pipeline(NEW, call, ai);
    const bc = Object.assign({}, b.cad); delete bc['Callback Outside Window']; delete bc['Non-Retainer Live Transfer'];
    const bl = Object.assign({}, b.cl); delete bl.callback_outside_window;
    const same = JSON.stringify(a.cad) === JSON.stringify(bc) && JSON.stringify(a.cl) === JSON.stringify(bl);
    if (!same) { fails++; console.log('FAIL ' + label + ': output changed\n  old ' + JSON.stringify(a.cad) + '\n  new ' + JSON.stringify(bc)); }
    else expect(label + ' (unchanged + defaults)', b.cad, { 'Callback Outside Window': false, 'Non-Retainer Live Transfer': 'No' });
  }
  // new flow: callback booked in the window
  let r = pipeline(NEW, CALL({ collected_dynamic_variables: { callback_status: 'in_window', callback_at_iso: '2026-10-16T17:00:00.000-07:00', callback_at_pacific: '10-16-2026 05:00 PM', callback_when_en: 'tomorrow at 5 PM' } }),
    AI({ vehicle_make: '', vehicle_year: '', callback_requested: 'Yes', callback_datetime: 'tomorrow at 5 PM' }));
  expect('flow callback in window', r.cad, { 'Lead Status': 'Incomplete Lead', 'Callback Requested': 'Yes', 'Callback Datetime ISO': '2026-10-16T17:00:00.000-07:00', 'Callback Datetime Pacific': '10-16-2026 05:00 PM', 'Callback Parse Failed': false, 'Callback Outside Window': false });
  // flow wins even when the AI missed the callback
  r = pipeline(NEW, CALL({ collected_dynamic_variables: { callback_status: 'in_window', callback_at_iso: '2026-10-16T17:00:00.000-07:00', callback_at_pacific: '10-16-2026 05:00 PM', callback_when_en: 'tomorrow at 5 PM' } }),
    AI({ vehicle_make: '', vehicle_year: '', callback_requested: 'No' }));
  expect('flow callback, AI missed it', r.cad, { 'Callback Requested': 'Yes', 'Callback Datetime': 'tomorrow at 5 PM', 'Callback Datetime Pacific': '10-16-2026 05:00 PM' });
  // outside the window: no time sent, flag set, cadence continues
  r = pipeline(NEW, CALL({ collected_dynamic_variables: { callback_status: 'out_of_window' } }),
    AI({ vehicle_make: '', vehicle_year: '', callback_requested: 'Yes', callback_datetime: 'next Monday at 5 PM' }));
  expect('flow callback outside window', r.cad, { 'Callback Requested': 'Yes', 'Callback Datetime ISO': '', 'Callback Datetime Pacific': '', 'Callback Parse Failed': false, 'Callback Outside Window': true });
  // unclear / gave up: falls back to the transcript parse
  r = pipeline(NEW, CALL({ collected_dynamic_variables: { callback_status: 'unclear', callback_next: 'giveup' } }), AI({ vehicle_make: '', vehicle_year: '', callback_requested: 'Yes', callback_datetime: 'N/A' }));
  expect('flow callback gave up -> transcript rules', r.cad, { 'Callback Requested': 'Yes', 'Callback Datetime ISO': '', 'Callback Parse Failed': true, 'Callback Outside Window': false });
  // opt-out still blocks a callback
  r = pipeline(NEW, CALL({ collected_dynamic_variables: { callback_status: 'in_window', callback_at_iso: '2026-10-16T17:00:00.000-07:00' } }), AI({ opt_out: 'Yes' }));
  expect('opt-out blocks flow callback', r.cad, { 'Callback Requested': 'No', 'Callback Datetime ISO': '' });
  // non-retainer live transfer
  r = pipeline(NEW, CALL({ disconnection_reason: 'call_transfer', collected_dynamic_variables: { nonret_live_transfer: 'attempted', nonret_hours: 'open' } }), AI({ vehicle_make: 'Honda' }));
  expect('non-retainer transferred', r.cad, { 'Lead Status': 'Non-Retainer Lead', 'Non-Retainer Live Transfer': 'Yes' });
  r = pipeline(NEW, CALL({ disconnection_reason: 'agent_hangup', collected_dynamic_variables: { nonret_live_transfer: 'attempted', nonret_hours: 'open' } }), AI({ vehicle_make: 'Honda' }));
  expect('non-retainer transfer failed', r.cad, { 'Lead Status': 'Non-Retainer Lead', 'Non-Retainer Live Transfer': 'No' });
  r = pipeline(NEW, CALL({ disconnection_reason: 'agent_hangup', collected_dynamic_variables: { nonret_hours: 'closed' } }), AI({ vehicle_make: 'Honda' }));
  expect('non-retainer after hours', r.cad, { 'Lead Status': 'Non-Retainer Lead', 'Non-Retainer Live Transfer': 'No' });
  return fails;
}

(async () => {
  const H = { 'X-N8N-API-KEY': KEY, 'Content-Type': 'application/json' };
  const wf = await (await fetch(BASE, { headers: H })).json();
  if (!wf.nodes) throw new Error('fetch failed: ' + JSON.stringify(wf).slice(0, 200));
  console.log('live workflow updatedAt ' + wf.updatedAt + ', active ' + wf.active);
  fs.writeFileSync(path.join(OUT, 'n8n_backup_' + wf.updatedAt.replace(/[:.]/g, '-') + '.json'), JSON.stringify(wf, null, 1));
  const p = patchCodes(wf);
  const fails = test(p);
  console.log(fails ? fails + ' FAILURES' : 'all tests passed');
  if (fails || process.env.PUSH !== '1') return;
  wf.nodes.find((n) => n.name === 'Classify Lead').parameters.jsCode = p.classify;
  wf.nodes.find((n) => n.name === 'Build Payload').parameters.jsCode = p.build;
  const s = wf.settings || {};
  const settings = { executionOrder: s.executionOrder || 'v1' };
  for (const k of ['timezone', 'callerPolicy', 'saveExecutionProgress', 'saveManualExecutions', 'saveDataErrorExecution', 'saveDataSuccessExecution', 'executionTimeout', 'errorWorkflow']) if (s[k] !== undefined) settings[k] = s[k];
  const res = await fetch(BASE, { method: 'PUT', headers: H, body: JSON.stringify({ name: wf.name, nodes: wf.nodes, connections: wf.connections, settings }) });
  console.log('PUT ' + res.status + (res.ok ? '' : ' ' + (await res.text()).slice(0, 400)));
  if (!res.ok) process.exit(1);
  const v = await (await fetch(BASE, { headers: H })).json();
  const ok = v.nodes.find((n) => n.name === 'Classify Lead').parameters.jsCode === p.classify && v.nodes.find((n) => n.name === 'Build Payload').parameters.jsCode === p.build;
  console.log('verify: code matches=' + ok + ' active=' + v.active + ' nodes=' + v.nodes.length + ' connections same=' + (JSON.stringify(v.connections) === JSON.stringify(wf.connections)) + ' settings=' + JSON.stringify(v.settings));
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
