// Workshop spec #7 (Ubaid OK 2026-10-22): the lead must get at least 2 minutes of silence while reading the agreement,
// with ONE check-in. Retell's reminder settings drive the automatic check-ins (they were 13 s x 3 = the "I'm still here"
// filler), so on both retainer DRAFT v6: reminder 120 s, max 1 reminder, hang up after 300 s of silence.
// Agent-wide trade-off accepted: a lead who goes quiet elsewhere in the call also gets a 2-minute wait.
// Also points the intake DRAFT hand-offs at Retainer Immediate v6 so test calls reach it (reset to latest_published
// before publishing intake).
//   node patch_retainer_silence.js / APPLY=1 node patch_retainer_silence.js
const fs = require('fs');
const KEY = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const H = { Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };
const APPLY = process.env.APPLY === '1';
const SETTINGS = { reminder_trigger_ms: 120000, reminder_max_count: 1, end_call_after_silence_ms: 300000 };
const RETAINER = { immediate: 'agent_7540b5be1e12d28fe1e937a832', outbound: 'agent_83f8b296e4652030d15a3417e6' };
const DRAFT = 6;
const INTAKE = [['conversation_flow_b4e1b9683eaf', 4], ['conversation_flow_fce8e3f30b49', 3]];

const api = async (method, p, body) => {
  const r = await fetch('https://api.retellai.com' + p, { method, headers: H, body: body ? JSON.stringify(body) : undefined });
  const t = await r.text();
  if (!r.ok) throw new Error(method + ' ' + p + ' -> ' + r.status + ' ' + t.slice(0, 400));
  return t ? JSON.parse(t) : {};
};
const pick = (a) => Object.keys(SETTINGS).map((k) => k + '=' + a[k]).join(' ');

(async () => {
  for (const [label, id] of Object.entries(RETAINER)) {
    const a = await api('GET', '/get-agent/' + id + '?version=' + DRAFT);
    if (a.is_published) throw new Error(label + ' v' + DRAFT + ' is published');
    console.log(label + ' v' + DRAFT + ': ' + pick(a) + ' -> ' + pick(SETTINGS) + (APPLY ? '' : ' [dry run]'));
    if (!APPLY) continue;
    await api('PATCH', '/update-agent/' + id + '?version=' + DRAFT, SETTINGS);
    const v = await api('GET', '/get-agent/' + id + '?version=' + DRAFT);
    const live = await api('GET', '/get-agent/' + id + '?version=5');
    console.log('  verify draft: ' + pick(v) + ' | live v5 unchanged: ' + pick(live));
  }
  for (const [fid, ver] of INTAKE) {
    const f = await api('GET', '/get-conversation-flow/' + fid + '?version=' + ver);
    if (f.is_published) throw new Error(fid + ' v' + ver + ' is published');
    const swaps = f.nodes.filter((n) => n.type === 'agent_swap' && n.agent_id === RETAINER.immediate);
    console.log(fid + ' v' + ver + ': hand-offs ' + swaps.map((n) => n.agent_version).join(',') + ' -> ' + DRAFT + ' (testing only)' + (APPLY ? '' : ' [dry run]'));
    if (!APPLY) continue;
    for (const n of swaps) n.agent_version = DRAFT;
    await api('PATCH', '/update-conversation-flow/' + fid + '?version=' + ver, { nodes: f.nodes });
  }
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
