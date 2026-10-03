// Patches the two LIVE intake flows for the lease / Tesla arbitration rules — DRAFT versions only.
//   node retell_patch_flows.js                                      -> dry run against the latest flow version
//   OUT_VER=<n> IN_VER=<n> APPLY=1 node retell_patch_flows.js       -> PATCHes those DRAFT flow versions
// OUT_VER / IN_VER = the flow version behind the new draft agent version of the outbound / inbound intake agent.
// The script refuses to write to a published flow version.
const fs = require('fs');
const path = require('path');
const KEY = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const APPLY = process.env.APPLY === '1';
const OUT = path.join(__dirname, 'out');
fs.mkdirSync(OUT, { recursive: true });
// outbound (agent_de01f772…), inbound (agent_22874d74…): the only flows bound to +1 213-205-3651
const FLOWS = { b4e1b9683eaf: process.env.OUT_VER, fce8e3f30b49: process.env.IN_VER };
const CLASSIFY = fs.readFileSync(path.join(__dirname, 'retell_classify.js'), 'utf8');

const TXT = {
  qLease: `Ask ONE question (caller's language), then wait.
English: "Did you purchase the vehicle, or lease it?"
Spanish: "¿Usted compró el vehículo, o lo arrendó?"

If the caller ALREADY said in an earlier answer that they lease it or leased it, do NOT ask that again: go straight to the follow-up below. If they already clearly said they bought it, do not ask again either: just say "Got it" ("Entendido") and move on.

Follow-up, ONLY if the vehicle is or was leased: "And is it still leased, or did you later buy it out?" In Spanish: "¿Y todavía lo tiene arrendado, o después lo compró?" Then wait.

If the answer is only "it's financed", "I'm making payments", "a loan" or "estoy pagando", that does not say lease or purchase. Ask once: "Is that a lease, or a loan to buy it?" In Spanish: "¿Es un arrendamiento, o un préstamo para comprarlo?"

How to read the answer (do NOT say this out loud): "lease", "leased", "leasing" and close-sounding mis-transcriptions such as "liz", "list", "lists", "leave it" or "I'll leave it" (for "I leased it") mean LEASE. In Spanish, "arrendado", "arrendé", "lo arriendo", "rentado", "lo rento" and mis-transcriptions such as "Rendée" or "renté" mean LEASE. "Bought", "purchased", "paid cash", "financed with a loan", "compré", "lo compré" mean PURCHASED. "Bought it out", "bought out the lease", "lo compré al final del arrendamiento" mean LEASED, THEN PURCHASED.

Do NOT explain why you are asking, and do NOT mention arbitration or whether this affects their case. Only collect the answer.`,
  qLeaseDone: 'The caller has made clear whether they bought the vehicle, still lease it, or leased it and later bought it out.',
  extract: "How the caller got the vehicle. 'purchased' = they bought it (cash, loan or financing). 'leased' = it is on a lease right now. 'lease_buyout' = it started as a lease and they later bought it out. Mis-transcriptions of lease ('liz', 'list', 'lists', 'leave it', 'I'll leave it', 'Rendée', 'renté') and Spanish 'arrendado', 'arrendé', 'rentado' mean lease. If the caller never made it clear, return 'purchased'. Never return 'leased' or 'lease_buyout' unless the caller actually said the vehicle is or was leased.",
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
  for (const [fid, ver] of Object.entries(FLOWS)) {
    if (APPLY && !/^[0-9]+$/.test(ver || '')) throw new Error('APPLY needs OUT_VER and IN_VER (draft flow versions)');
    const q = APPLY ? '?version=' + ver : '';
    const url = 'https://api.retellai.com/get-conversation-flow/conversation_flow_' + fid + q;
    const flow = await (await fetch(url, { headers: { Authorization: 'Bearer ' + KEY } })).json();
    if (APPLY && flow.is_published) throw new Error(fid + ' version ' + ver + ' is PUBLISHED — refusing to edit. Use the draft version.');
    const log = patch(flow);
    fs.writeFileSync(path.join(OUT, 'flow_' + fid + '.json'), JSON.stringify(flow, null, 2));
    console.log('\n===== ' + fid + ' v' + flow.version + ' (published=' + flow.is_published + ', ' + flow.nodes.length + ' nodes)\n  ' + log.join('\n  '));
    if (!APPLY) continue;
    const res = await fetch('https://api.retellai.com/update-conversation-flow/conversation_flow_' + fid + q, { method: 'PATCH', headers: { Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ nodes: flow.nodes }) });
    console.log('  PATCH ' + res.status + (res.ok ? ' OK' : ' ' + (await res.text()).slice(0, 500)));
    const v = await (await fetch(url, { headers: { Authorization: 'Bearer ' + KEY } })).json();
    const g = (id) => v.nodes.find((n) => n.id === id);
    console.log('  verify v' + v.version + ': q-lease=' + !!g('node-q-lease') + ' classify=' + (g('node-code-classify').code === CLASSIFY) + ' q-ca->' + g('node-q-ca').edges.map((e) => e.destination_node_id).join(',') + ' branch-bad edges=' + g('node-branch-bad').edges.length);
  }
  if (!APPLY) console.log('\nDRY RUN: nothing pushed');
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
