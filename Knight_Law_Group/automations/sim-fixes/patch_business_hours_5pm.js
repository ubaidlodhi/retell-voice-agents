// Ubaid 2026-10-20: business hours are 8 AM - 5 PM. The only business-hours logic in the agents is the non-retainer live
// transfer check (node-nonret-hours, both intake flows): Mon-Fri 8 AM - 8 PM PT -> Mon-Fri 8 AM - 5 PM PT.
// Source of truth: ../intake-callback-nonret/code_nonret_hours.js. The code is tested against fixed clock times first.
// Intake agents are live, so this creates new drafts (outbound v2 -> v3, inbound v1 -> v2), patches them, and with
// PUBLISH=1 publishes them (voice and everything else are carried over from the live version).
//   node patch_business_hours_5pm.js            -> code tests + dry run
//   APPLY=1 node patch_business_hours_5pm.js    -> create drafts + patch
//   APPLY=1 PUBLISH=1 node patch_business_hours_5pm.js
const fs = require('fs');
const path = require('path');
const KEY = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const H = { Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };
const APPLY = process.env.APPLY === '1';
const PUBLISH = process.env.PUBLISH === '1';
const CODE = fs.readFileSync(path.join(__dirname, '..', 'intake-callback-nonret', 'code_nonret_hours.js'), 'utf8');
const AGENTS = [
  { label: 'Intake Outbound', agent: 'agent_de01f772a9de26ecf4387115a9', base: 2 },
  { label: 'Intake Inbound', agent: 'agent_22874d74b1dd6b9d6d72aa4c67', base: 1 },
];

// Run the node body with a fixed clock. Times are UTC instants; comments give the Pacific time.
function runAt(iso) {
  const real = Date.now;
  Date.now = () => Date.parse(iso);
  try { return new Function('dv', CODE)({}).nonret_hours; } finally { Date.now = real; }
}
const CASES = [
  ['2026-10-19T14:59:00Z', 'closed', 'Mon 7:59 AM PDT'],
  ['2026-10-19T15:00:00Z', 'open', 'Mon 8:00 AM PDT'],
  ['2026-10-19T23:59:00Z', 'open', 'Mon 4:59 PM PDT'],
  ['2026-10-20T00:00:00Z', 'closed', 'Mon 5:00 PM PDT'],
  ['2026-10-20T02:30:00Z', 'closed', 'Mon 7:30 PM PDT (was open under 8-8)'],
  ['2026-10-23T23:30:00Z', 'open', 'Fri 4:30 PM PDT'],
  ['2026-10-24T19:00:00Z', 'closed', 'Sat 12:00 PM PDT'],
  ['2026-12-07T16:00:00Z', 'open', 'Mon 8:00 AM PST (winter)'],
  ['2026-12-08T00:59:00Z', 'open', 'Mon 4:59 PM PST (winter)'],
  ['2026-12-08T01:00:00Z', 'closed', 'Mon 5:00 PM PST (winter)'],
];

const api = async (method, p, body) => {
  const r = await fetch('https://api.retellai.com' + p, { method, headers: H, body: body ? JSON.stringify(body) : undefined });
  const t = await r.text();
  if (!r.ok) throw new Error(method + ' ' + p + ' -> ' + r.status + ' ' + t.slice(0, 400));
  return t ? JSON.parse(t) : {};
};

(async () => {
  let bad = 0;
  for (const [iso, want, label] of CASES) {
    const got = runAt(iso);
    if (got !== want) bad++;
    console.log((got === want ? 'ok   ' : 'FAIL ') + label.padEnd(38) + got);
  }
  if (bad) throw new Error(bad + ' code test(s) failed');
  for (const s of AGENTS) {
    const live = await api('GET', '/get-agent/' + s.agent + '?version=' + s.base);
    if (!live.is_published) throw new Error(s.label + ' v' + s.base + ' is not the live version');
    console.log(s.label + ': live v' + s.base + ' (flow v' + live.response_engine.version + ')' + (APPLY ? '' : ' [dry run]'));
    if (!APPLY) continue;
    const d = await api('POST', '/create-agent-version/' + s.agent, { base_version: s.base });
    const fv = d.response_engine.version;
    if (d.is_published || fv === live.response_engine.version) throw new Error(s.label + ': bad draft ' + JSON.stringify({ v: d.version, fv }));
    const f = await api('GET', '/get-conversation-flow/' + d.response_engine.conversation_flow_id + '?version=' + fv);
    const n = f.nodes.find((x) => x.id === 'node-nonret-hours');
    if (!n || !n.code.includes('h < 20')) throw new Error(s.label + ': node-nonret-hours anchor');
    n.code = CODE;
    await api('PATCH', '/update-conversation-flow/' + d.response_engine.conversation_flow_id + '?version=' + fv, { nodes: f.nodes });
    const v = await api('GET', '/get-conversation-flow/' + d.response_engine.conversation_flow_id + '?version=' + fv);
    const ok = v.nodes.find((x) => x.id === 'node-nonret-hours').code.includes('h < 17');
    console.log('  draft v' + d.version + ' flow v' + fv + ': 5 PM code=' + ok + ' hand-offs=' + v.nodes.filter((x) => x.type === 'agent_swap').map((x) => x.agent_version).join(',') + ' voice=' + d.voice_id);
    if (!ok) throw new Error('verify failed');
    if (!PUBLISH) continue;
    await api('POST', '/publish-agent-version/' + s.agent, { version: d.version });
    const p = await api('GET', '/get-agent/' + s.agent + '?version=' + d.version);
    console.log('  published v' + d.version + ': ' + p.is_published);
  }
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
