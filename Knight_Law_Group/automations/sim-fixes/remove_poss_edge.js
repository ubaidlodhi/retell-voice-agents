// Intake DRAFT v1 (both flows): remove e-poss-vehicle-known, added by patch_intake_sim_fixes.js (fix 3a).
// Re-run batch test_batch_20d79d2a608d: the prompt edge fired on 4/4 calls although no vehicle had been named, the
// extract node then invented a make (Ford / Acura / Toyota) with year 0, and the call fell into confirm/reprompt loops.
// Fix 3b (vehicle_readback_confirmed -> skip the second read-back) stays: it extracted "no" correctly on every run.
//   node remove_poss_edge.js / APPLY=1 node remove_poss_edge.js
const fs = require('fs');
const KEY = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const H = { Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };
const APPLY = process.env.APPLY === '1';
const FLOWS = ['conversation_flow_b4e1b9683eaf', 'conversation_flow_fce8e3f30b49'];

(async () => {
  for (const id of FLOWS) {
    const f = await (await fetch('https://api.retellai.com/get-conversation-flow/' + id + '?version=1', { headers: H })).json();
    if (f.is_published) throw new Error(id + ' v1 is published — refusing');
    const poss = f.nodes.find((n) => n.id === 'node-q-possession');
    const before = poss.edges.length;
    poss.edges = poss.edges.filter((e) => e.id !== 'e-poss-vehicle-known');
    if (poss.edges.length !== before - 1) throw new Error(id + ': edge not found');
    if (poss.edges.length !== 1 || poss.edges[0].destination_node_id !== 'node-q-vehicle') throw new Error(id + ': unexpected remaining edges');
    console.log(id + ': possession edges ' + before + ' -> ' + poss.edges.length + (APPLY ? '' : ' [dry run]'));
    if (!APPLY) continue;
    const r = await fetch('https://api.retellai.com/update-conversation-flow/' + id + '?version=1', { method: 'PATCH', headers: H, body: JSON.stringify({ nodes: f.nodes }) });
    if (!r.ok) throw new Error('PATCH ' + r.status + ' ' + (await r.text()).slice(0, 300));
    const v = await (await fetch('https://api.retellai.com/get-conversation-flow/' + id + '?version=1', { headers: H })).json();
    console.log('  verify: possession edges=' + v.nodes.find((n) => n.id === 'node-q-possession').edges.map((e) => e.id).join(',') + ' published=' + v.is_published);
  }
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
