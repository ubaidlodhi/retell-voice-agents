// Reverts part A of patch_skip_and_endcall.js: `skippable` on node-ret-owner / node-q-possession / node-ret-cpo did NOT
// skip on the FAQ go-back (re-run test_batch_e025bbb86101: still "Got it." with no question), so back to false.
const fs = require('fs');
const KEY = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const H = { Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };
const NODES = ['node-ret-owner', 'node-q-possession', 'node-ret-cpo'];
(async () => {
  for (const id of ['conversation_flow_b4e1b9683eaf', 'conversation_flow_fce8e3f30b49']) {
    const f = await (await fetch('https://api.retellai.com/get-conversation-flow/' + id + '?version=1', { headers: H })).json();
    if (f.is_published) throw new Error(id + ' v1 is published');
    for (const n of f.nodes) if (NODES.includes(n.id)) n.skippable = false;
    const r = await fetch('https://api.retellai.com/update-conversation-flow/' + id + '?version=1', { method: 'PATCH', headers: H, body: JSON.stringify({ nodes: f.nodes }) });
    if (!r.ok) throw new Error(r.status + ' ' + (await r.text()).slice(0, 300));
    const v = await (await fetch('https://api.retellai.com/get-conversation-flow/' + id + '?version=1', { headers: H })).json();
    console.log(id + ': ' + NODES.map((x) => x + '=' + v.nodes.find((n) => n.id === x).skippable).join(' ') + ' published=' + v.is_published);
  }
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
