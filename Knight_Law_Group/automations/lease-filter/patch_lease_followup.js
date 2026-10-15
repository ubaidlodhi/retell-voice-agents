// Intake DRAFT v1 (both flows) — from Ubaid's test call call_141929a27d8ea836d930f1b310e (lease buyout BMW):
//   1. "Did you buy it, or lease it?" -> "I lose it" (= leased) -> Alice said "Okay, leased." and moved on WITHOUT the
//      "still leased, or did you later buy it out?" follow-up, so the buyout BMW was taken as still leased -> arbitration.
//      Cause: the node's only edge ("made clear whether they bought / still lease / bought out") also fires on a bare
//      "leased". Fix: the edge needs the still-leased-vs-bought-out answer.
//   2. After the arbitration line the caller said "I leased it first, then bought it out last year" -> the follow-up
//      node reaffirmed the rejection ("even with the buyout ... outside what we can take on"), which is wrong for BMW.
//      Cause: no way back from the arbitration nodes. Fix: a correction edge from the six arbitration lines and the
//      follow-up node -> re-extract the purchase type -> re-run the classifier (vehicle already known).
//   node patch_lease_followup.js / APPLY=1 node patch_lease_followup.js
const fs = require('fs');
const KEY = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const H = { Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };
const APPLY = process.env.APPLY === '1';
const VER = 1;
const FLOWS = ['conversation_flow_b4e1b9683eaf', 'conversation_flow_fce8e3f30b49'];

const LEASE_EDGE_FROM = 'The caller has made clear whether they bought the vehicle, still lease it, or leased it and later bought it out.';
const LEASE_EDGE_TO = 'The caller has said they bought it, OR confirmed it is still leased, OR said they leased it and later bought it out. A bare "I leased it" is not enough: the "still leased, or bought it out?" follow-up must be answered first.';
const CORRECTION = 'The caller corrects how they got the vehicle: for example they say they later bought out the lease, that it is no longer leased, or that they bought it rather than leased it.';
const ARB_NODES = ['node-disq-arb-lease-en', 'node-disq-arb-lease-es', 'node-disq-arb-buyout-en', 'node-disq-arb-buyout-es', 'node-disq-arb-tesla-en', 'node-disq-arb-tesla-es', 'node-disq-arb-after'];
const P = (id, prompt, dest) => ({ id, destination_node_id: dest, transition_condition: { type: 'prompt', prompt } });

(async () => {
  for (const id of FLOWS) {
    const f = await (await fetch('https://api.retellai.com/get-conversation-flow/' + id + '?version=' + VER, { headers: H })).json();
    if (f.is_published) throw new Error(id + ' v' + VER + ' is published — refusing');
    if (f.nodes.some((n) => n.id === 'node-extract-lease-fix')) throw new Error(id + ': already patched');
    const byId = (x) => { const n = f.nodes.find((y) => y.id === x); if (!n) throw new Error('missing ' + x); return n; };
    const q = byId('node-q-lease');
    const e = q.edges.filter((x) => x.transition_condition.prompt === LEASE_EDGE_FROM);
    if (e.length !== 1) throw new Error(id + ': q-lease edge anchor');
    e[0].transition_condition.prompt = LEASE_EDGE_TO;
    const xl = byId('node-extract-lease');
    const fix = {
      id: 'node-extract-lease-fix', name: 'Extract Purchase Type (correction)', type: 'extract_dynamic_variables', skippable: false,
      display_position: { x: (byId('node-disq-arb-after').display_position || { x: 3000 }).x + 300, y: (byId('node-disq-arb-after').display_position || { y: 1600 }).y + 200 },
      variables: JSON.parse(JSON.stringify(xl.variables)),
      edges: [P('e-xlease-fix-ok', 'Always', 'node-code-classify')], else_edge: P('e-xlease-fix-else', 'Else', 'node-code-classify'),
    };
    f.nodes.push(fix);
    for (const nid of ARB_NODES) {
      const n = byId(nid);
      n.edges.unshift(P('e-' + nid.replace('node-', '') + '-correct', CORRECTION, 'node-extract-lease-fix'));
    }
    console.log(id + ' v' + VER + ': q-lease edge requires the follow-up answer; correction edge on ' + ARB_NODES.length + ' arbitration nodes -> re-extract -> re-classify');
    const ids = new Set(f.nodes.map((n) => n.id));
    for (const n of f.nodes) for (const x of [...(n.edges || []), n.else_edge, n.edge, n.skip_response_edge].filter(Boolean)) if (!ids.has(x.destination_node_id)) throw new Error(n.id + ' -> missing ' + x.destination_node_id);
    if (!APPLY) continue;
    const r = await fetch('https://api.retellai.com/update-conversation-flow/' + id + '?version=' + VER, { method: 'PATCH', headers: H, body: JSON.stringify({ nodes: f.nodes }) });
    if (!r.ok) throw new Error('PATCH ' + r.status + ' ' + (await r.text()).slice(0, 300));
    const v = await (await fetch('https://api.retellai.com/get-conversation-flow/' + id + '?version=' + VER, { headers: H })).json();
    const g = (x) => v.nodes.find((n) => n.id === x);
    console.log('  verify: nodes=' + v.nodes.length + ' fix node=' + !!g('node-extract-lease-fix') + ' q-lease edge=' + (g('node-q-lease').edges[0].transition_condition.prompt === LEASE_EDGE_TO)
      + ' correction edges=' + ARB_NODES.filter((x) => g(x).edges[0].destination_node_id === 'node-extract-lease-fix').length + '/' + ARB_NODES.length + ' published=' + v.is_published);
  }
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
