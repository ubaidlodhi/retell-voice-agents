// Intake DRAFT v1 (both flows): fixes from the 2026-10-19 simulation batch (draft-tests/sim_intake_v1.js, out/sim/).
//   1. T1: "new or used?" and "dealer repairs?" were re-asked after the caller already said "brand new" / "at the dealer
//      three times". `skippable` does not fire when those nodes are reached through the classifier code/branch nodes.
//      Fix: node-extract-vehicle also extracts said_new_or_used / said_dealer_repairs from what was already said, and two
//      branch nodes route past the questions (node-ret-skip-newused, node-ret-skip-repairs).
//   2. T2: "it came with some kind of warranty" took the CPO "unsure" edge before Alice explained CPO, so a possible CPO
//      (retainer) lead went non-retainer. Fix: the unsure edge needs the explanation to have been given; a warranty
//      mention or any not-clear answer triggers the explanation first.
//   3. T8: vehicle volunteered at the possession question -> q-vehicle read it back and got a yes -> confirm-vehicle had
//      nothing to ask ("Perfecto, lo tengo.") = dead air. Fix: possession edge straight to the extract when year + make
//      are already known, and an extracted vehicle_readback_confirmed skips the second read-back.
//      NOTE: the possession edge (e-poss-vehicle-known) was REMOVED again by remove_poss_edge.js — it fired on every call
//      and the extractor invented a make. Only vehicle_readback_confirmed (3b) is live.
//   4. T3: the spelling example had no question, so the turn could end on a statement. Fix: "Is that right?" added.
//   node patch_intake_sim_fixes.js / APPLY=1 node patch_intake_sim_fixes.js
const fs = require('fs');
const path = require('path');
const KEY = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const H = { Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };
const APPLY = process.env.APPLY === '1';
const VER = 1;
const FLOWS = ['conversation_flow_b4e1b9683eaf', 'conversation_flow_fce8e3f30b49'];
const OUT = path.join(__dirname, 'out');

const P = (id, prompt, dest) => ({ id, destination_node_id: dest, transition_condition: { type: 'prompt', prompt } });
const EQ = (id, v, val, dest) => ({ id, destination_node_id: dest, transition_condition: { type: 'equation', operator: '&&', equations: [{ left: '{{' + v + '}}', operator: '==', right: val }] } });

const NEW_VARS = [
  {
    name: 'said_new_or_used', type: 'enum', choices: ['new', 'used', 'unknown'],
    description: 'Only from what the caller has ALREADY said earlier in this call: was the vehicle new or used when they got it? '
      + '"new" if they clearly said so (e.g. "I bought it brand new", "it was new", "I leased it new", "lo compré nuevo"). '
      + '"used" if they clearly said used or pre-owned (including certified pre-owned). '
      + '"unknown" if they have not said it, or it is unclear. Do not infer it from the model year, and ignore "new" about something else (e.g. "a new problem", "a brand new transmission").',
  },
  {
    name: 'said_dealer_repairs', type: 'enum', choices: ['yes', 'unknown'],
    description: 'Only from what the caller has ALREADY said earlier in this call: "yes" if they said the vehicle has been taken to a dealership or dealer for repairs, '
      + 'or is at the dealer / in the shop for repairs right now (e.g. "it\'s been at the dealer three times", "the dealer couldn\'t fix it", "it\'s at the dealer right now"). '
      + 'Otherwise "unknown".',
  },
  {
    name: 'vehicle_readback_confirmed', type: 'enum', choices: ['yes', 'no'],
    description: '"yes" only if Alice has ALREADY read the vehicle\'s year and make back to the caller in this call and the caller confirmed it (e.g. "yes", "that\'s right", "sí, es correcto") without correcting it. Otherwise "no".',
  },
];

const CPO_INSTR_FROM = 'If the caller does not know what CPO means or asks you to explain it, say ONCE';
const CPO_INSTR_TO = 'If the caller does not know what CPO means, asks you to explain it, mentions some kind of warranty, or gives any answer that is not a clear yes or a clear no, say ONCE';
const CPO_UNSURE = 'Alice has ALREADY given the CPO explanation in this conversation ("CPO means the manufacturer inspected and certified the used vehicle..."), and the caller is still unsure, still does not know, or answers with something unrelated (e.g. gap insurance, a paid or extended warranty, a dealer or third-party warranty, a service contract) that does not actually confirm CPO.';
const POSS_EARLY = 'Caller has answered whether they still have the vehicle (yes or no), AND earlier in this call the caller already said the vehicle\'s model year and make (e.g. "it\'s a 2023 Honda Civic").';
const SPELL_FIXES = [
  ['"Great — let me confirm the spelling: {{name_spelled_en}}"', '"Great — let me confirm the spelling: {{name_spelled_en}}. Is that right?"'],
  ['"Muy bien — le confirmo la ortografía: {{name_spelled_es}}"', '"Muy bien — le confirmo la ortografía: {{name_spelled_es}}. ¿Es correcto?"'],
];

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  for (const id of FLOWS) {
    const f = await (await fetch('https://api.retellai.com/get-conversation-flow/' + id + '?version=' + VER, { headers: H })).json();
    if (f.is_published) throw new Error(id + ' v' + VER + ' is published — refusing');
    if (f.nodes.some((n) => n.id === 'node-ret-skip-newused')) throw new Error(id + ': already patched');
    fs.writeFileSync(path.join(OUT, 'backup_' + id + '_v' + VER + '.json'), JSON.stringify(f, null, 1));
    const byId = (x) => { const n = f.nodes.find((y) => y.id === x); if (!n) throw new Error(id + ': missing ' + x); return n; };
    const edge = (n, eid) => { const e = (n.edges || []).find((x) => x.id === eid); if (!e) throw new Error(id + ': missing edge ' + eid); return e; };
    const pos = (nid, dx, dy) => { const p = byId(nid).display_position || { x: 0, y: 0 }; return { x: p.x + dx, y: p.y + dy }; };

    // 1. skip known answers
    const xv = byId('node-extract-vehicle');
    for (const v of NEW_VARS) if (xv.variables.some((x) => x.name === v.name)) throw new Error(id + ': var exists ' + v.name);
    xv.variables.push(...NEW_VARS);
    f.nodes.push({
      id: 'node-ret-skip-repairs', name: 'Retainer: Repairs already said?', type: 'branch', display_position: pos('node-ret-repairs', 0, -220),
      edges: [EQ('e-skiprep-yes', 'said_dealer_repairs', 'yes', 'node-ret-owner')], else_edge: P('e-skiprep-else', 'Else', 'node-ret-repairs'),
    });
    f.nodes.push({
      id: 'node-ret-skip-newused', name: 'Retainer: New/Used already said?', type: 'branch', display_position: pos('node-ret-newused', 0, -220),
      edges: [EQ('e-skipnu-new', 'said_new_or_used', 'new', 'node-ret-skip-repairs'), EQ('e-skipnu-used', 'said_new_or_used', 'used', 'node-ret-cpo')],
      else_edge: P('e-skipnu-else', 'Else', 'node-ret-newused'),
    });
    const toSkipNu = edge(byId('node-branch-route'), 'e-route-retainer');
    if (toSkipNu.destination_node_id !== 'node-ret-newused') throw new Error(id + ': e-route-retainer anchor');
    toSkipNu.destination_node_id = 'node-ret-skip-newused';
    for (const [nid, eid] of [['node-ret-newused', 'e-ret-new'], ['node-ret-cpo', 'e-cpo-yes']]) {
      const e = edge(byId(nid), eid);
      if (e.destination_node_id !== 'node-ret-repairs') throw new Error(id + ': ' + eid + ' anchor');
      e.destination_node_id = 'node-ret-skip-repairs';
    }

    // 2. CPO: explain before routing an unclear answer
    const cpo = byId('node-ret-cpo');
    if (!cpo.instruction.text.includes(CPO_INSTR_FROM)) throw new Error(id + ': CPO instruction anchor');
    cpo.instruction.text = cpo.instruction.text.replace(CPO_INSTR_FROM, CPO_INSTR_TO);
    edge(cpo, 'e-cpo-unsure').transition_condition.prompt = CPO_UNSURE;

    // 3. vehicle confirmed once
    const poss = byId('node-q-possession');
    poss.edges.unshift(P('e-poss-vehicle-known', POSS_EARLY, 'node-extract-vehicle'));
    xv.edges.unshift(EQ('e-extract-confirmed', 'vehicle_readback_confirmed', 'yes', 'node-code-spell'));
    if (!f.nodes.some((n) => n.id === 'node-code-spell')) throw new Error(id + ': missing node-code-spell');

    // 4. spelling turn ends in a question
    for (const nid of ['node-nonret-confirm', 'node-ret-contact']) {
      const n = byId(nid);
      for (const [a, b] of SPELL_FIXES) {
        if (!n.instruction.text.includes(a)) throw new Error(id + ': ' + nid + ' spelling anchor ' + a.slice(0, 30));
        n.instruction.text = n.instruction.text.replace(a, b);
      }
    }

    const ids = new Set(f.nodes.map((n) => n.id));
    const eids = new Set();
    for (const n of f.nodes) for (const x of [...(n.edges || []), n.else_edge, n.edge, n.always_edge, n.skip_response_edge].filter(Boolean)) {
      if (!ids.has(x.destination_node_id)) throw new Error(n.id + ' -> missing ' + x.destination_node_id);
      if (eids.has(x.id)) throw new Error('duplicate edge id ' + x.id);
      eids.add(x.id);
    }
    console.log(id + ' v' + VER + ': ok (nodes ' + f.nodes.length + ', edges ' + eids.size + ')' + (APPLY ? '' : ' [dry run]'));
    if (!APPLY) continue;
    const r = await fetch('https://api.retellai.com/update-conversation-flow/' + id + '?version=' + VER, { method: 'PATCH', headers: H, body: JSON.stringify({ nodes: f.nodes }) });
    if (!r.ok) throw new Error('PATCH ' + r.status + ' ' + (await r.text()).slice(0, 400));
    const v = await (await fetch('https://api.retellai.com/get-conversation-flow/' + id + '?version=' + VER, { headers: H })).json();
    const g = (x) => v.nodes.find((n) => n.id === x);
    console.log('  verify: published=' + v.is_published
      + ' route->' + g('node-branch-route').edges.find((e) => e.id === 'e-route-retainer').destination_node_id
      + ' vars=' + g('node-extract-vehicle').variables.map((x) => x.name).filter((x) => NEW_VARS.some((y) => y.name === x)).join('/')
      + ' cpo-unsure=' + (g('node-ret-cpo').edges.find((e) => e.id === 'e-cpo-unsure').transition_condition.prompt === CPO_UNSURE)
      + ' poss-edge=' + (g('node-q-possession').edges[0].id === 'e-poss-vehicle-known')
      + ' extract-eq=' + (g('node-extract-vehicle').edges[0].id === 'e-extract-confirmed')
      + ' spell=' + ['node-nonret-confirm', 'node-ret-contact'].every((x) => g(x).instruction.text.includes('. Is that right?"')));
  }
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
