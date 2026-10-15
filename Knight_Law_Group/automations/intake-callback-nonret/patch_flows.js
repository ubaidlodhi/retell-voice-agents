// Intake Alice (both flows on +1 213-205-3651), DRAFT versions only:
//   1. Callback request: Alice books the callback time the lead asks for, inside the 3-day Alice Qualifying
//      follow-up window; outside it she says the team will contact them soon (Micol, feedback-03).
//   2. Non-retainer live transfer: Mon-Fri 8 AM-8 PM PT a qualified non-retainer lead is offered a warm transfer
//      to an Intake Analyst; outside those hours (or if they decline / nobody answers) today's booking-link close.
//   3. Arbitration lines (lease / lease buyout / Tesla) spoken word for word: static text per language.
//   node patch_flows.js                          -> dry run against the latest flow versions, writes out/*.json
//   OUT_VER=<n> IN_VER=<n> APPLY=1 node patch_flows.js   -> PATCHes those DRAFT flow versions
// GLOBAL_STOP=conversation forces the fallback shape for the global "call me back" node (see makeGlobalStop).
const fs = require('fs');
const path = require('path');
const KEY = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const APPLY = process.env.APPLY === '1';
const OUT = path.join(__dirname, 'out');
fs.mkdirSync(OUT, { recursive: true });
// outbound (agent_de01f772…), inbound (agent_22874d74…)
const FLOWS = { b4e1b9683eaf: process.env.OUT_VER, fce8e3f30b49: process.env.IN_VER };
const CODE_CB = fs.readFileSync(path.join(__dirname, 'code_callback.js'), 'utf8');
const CODE_HOURS = fs.readFileSync(path.join(__dirname, 'code_nonret_hours.js'), 'utf8');
const CODE_XFER = "return { nonret_live_transfer: 'attempted' };";

const P = (id, prompt, dest) => ({ id, destination_node_id: dest, transition_condition: { type: 'prompt', prompt } });
const EQS = (id, eqs, dest) => ({ id, destination_node_id: dest, transition_condition: { type: 'equation', operator: '&&', equations: eqs.map(([left, operator, right]) => ({ left, operator, right })) } });
const pos = (n, dx, dy) => ({ x: (n.display_position || { x: 0 }).x + dx, y: (n.display_position || { y: 0 }).y + dy });

const TXT = {
  cbTime: 'Use the LATEST time the caller asked for: if they corrected themselves or changed it, use the correction.',
  cbGives: 'The caller names a day and/or a time for the callback, or changes or corrects one (for example "tomorrow", "at 5", "Friday afternoon", "in two hours", "mañana a las cinco").',
  cbNoTime: 'The caller will not give a time: they say anytime or whenever, that they will call us back themselves, that they are not interested in a callback, or they just have to go.',
  reask: `Say exactly this, in the caller's language, as ONE short turn, then wait:
English: "{{callback_ask_en}}"
Spanish: "{{callback_ask_es}}"
Do not add anything else, do not continue the intake, and keep it short: they are busy.`,
  confirm: `Say this in the caller's language as ONE short turn, then wait:
English: "Perfect, we'll give you a call {{callback_when_en}}. Talk to you then!"
Spanish: "Perfecto, le llamamos {{callback_when_es}}. ¡Hablamos entonces!"
Say the day and time exactly as written. Do not add a date, a time zone or anything else, and do not continue the intake.`,
  cbEnd: 'Say a brief, warm goodbye in the caller\'s language (for example "Take care!" / "¡Que esté muy bien!"). Then end the call.',
  cbOut: `Say this warmly in the caller's language, as ONE turn:
English: "No problem. Our team will contact you soon. Take care!"
Spanish: "No hay problema. Nuestro equipo se comunicará con usted pronto. ¡Que esté muy bien!"
Do not promise a specific day or time. Then end the call.`,
  globalStopAsk: `The caller can't talk right now or asked to be called back. In ONE short turn, in the caller's language, ask when to call:
English: "No problem at all. What's a good day and time for us to give you a call back?"
Spanish: "No hay problema. ¿Qué día y a qué hora le podemos volver a llamar?"
If the caller ALREADY said when (for example "call me tomorrow at 5"), do not ask: just say "Got it." ("Entendido.").
Do not continue the intake.`,
  nrOffer: `In the caller's language, as ONE short turn, then wait:
English: "Great news, we may be able to help. One of our Intake Analysts is available right now to go over your case and set up your consultation. Would you like me to connect you now?"
Spanish: "Buenas noticias, es posible que podamos ayudarle. Uno de nuestros analistas de admisión está disponible ahora mismo para revisar su caso y programar su consulta. ¿Quiere que le comunique ahora?"
Do NOT mention a booking link here.`,
  nrYes: 'The caller agrees to be connected now (yes / sure / okay / go ahead / sí / claro).',
  nrNo: 'The caller says no, not now, that they are busy, or that they would rather book the consultation themselves.',
  nrBusy: `Say warmly (caller's language), in one short turn:
English: "Looks like our Intake Analysts are tied up right now. No problem, we'll text you a booking link shortly so you can set up your consultation. Thanks for contacting Knight Law Group."
Spanish: "Parece que nuestros analistas de admisión están ocupados en este momento. No se preocupe, en breve le enviaremos por mensaje de texto un enlace para que programe su consulta. Gracias por comunicarse con Knight Law Group."`,
  lang: "The language the CALLER has actually been speaking on this call: 'Spanish' if the caller has been answering in Spanish, otherwise 'English'. Ignore the language on file.",
  arbAfter: `You have ALREADY told the caller why we can't take this case: the agreement requires arbitration, and our firm only handles cases through the court system. Do NOT repeat that explanation.
If the caller pushes back or asks to proceed anyway, briefly and kindly reaffirm, in fresh words, that the vehicle is outside our criteria so we can't move forward, then ask if there's anything else you can help with. If they ask a simple question, answer it briefly. Never say the same sentence twice in a row. Speak the caller's language.`,
  arbDone: 'Caller acknowledges, accepts it, says okay / thanks / bye, or has no further questions',
  arbMore: 'Caller pushes back, asks a question, or says anything other than a plain acknowledgement',
};

const extractNode = (id, name, p, variables, dest) => ({ id, name, type: 'extract_dynamic_variables', skippable: false, display_position: p, variables, edges: [P('e-' + id.replace('node-', '') + '-ok', 'Always', dest)], else_edge: P('e-' + id.replace('node-', '') + '-else', 'Else', dest) });
const codeNode = (id, name, p, code, vars, dest) => ({ id, name, type: 'code', skippable: false, display_position: p, code, wait_for_result: true, speak_during_execution: false, enable_typing_sound: false, response_variables: Object.fromEntries(vars.map((v) => [v, v])), edges: [P('e-' + id.replace('node-', '') + '-ok', 'Always', dest)], else_edge: P('e-' + id.replace('node-', '') + '-else', 'Else', dest) });
const convo = (id, name, p, text, edges, extra) => Object.assign({ id, name, type: 'conversation', skippable: false, display_position: p, instruction: { type: 'prompt', text }, edges }, extra || {});
const endNode = (id, name, p, text) => ({ id, name, type: 'end', skippable: false, speak_during_execution: true, display_position: p, instruction: { type: 'prompt', text } });

const CB_VARS = [
  { name: 'callback_day', type: 'enum', choices: ['today', 'tomorrow', 'day_after_tomorrow', 'in_days', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'next_week', 'specific_date', 'unspecified'],
    description: "Which day the caller wants us to call them back. 'today' (hoy, this afternoon, tonight), 'tomorrow' (mañana), 'day_after_tomorrow' (pasado mañana), 'in_days' for 'in N days' (then fill callback_in_days), a weekday name for a named day ('Friday', 'next Friday', 'el viernes'; 'this weekend' = 'saturday'), 'next_week' for 'next week' / 'la próxima semana' with no day, 'specific_date' for a calendar date ('the 20th', 'October 20') (then fill callback_specific_date), 'unspecified' if no day was said. Leave it 'unspecified' for a relative time like 'in two hours' (use callback_in_minutes). " + TXT.cbTime },
  { name: 'callback_specific_date', type: 'string', description: "Only when callback_day is 'specific_date': the date as MM-DD (for example 10-20). If only the day of the month was said, use the current month. Otherwise empty." },
  { name: 'callback_in_days', type: 'number', description: "Only when callback_day is 'in_days': the number of days ('in two days' = 2, 'en tres días' = 3). Otherwise 0." },
  { name: 'callback_in_minutes', type: 'number', description: "Only for a time RELATIVE to now: minutes from now ('in two hours' = 120, 'in half an hour' = 30, 'en una hora' = 60, 'in 15 minutes' = 15). Otherwise 0." },
  { name: 'callback_time', type: 'string', description: "The time of day for the callback as 24-hour HH:MM (5 PM = 17:00, 9:30 in the morning = 09:30, 'a las cinco de la tarde' = 17:00). A bare hour from 1 to 7 with no AM/PM means PM ('at 5' = 17:00); a bare 8 to 11 means AM unless they said evening or night. Parts of the day: morning / en la mañana = 09:00, noon / mediodía = 12:00, afternoon / en la tarde = 14:00, evening / tonight / en la noche = 18:00. Empty if no time of day was said. " + TXT.cbTime },
];
const CB_OUT_VARS = ['callback_status', 'callback_next', 'callback_tries', 'callback_ask_en', 'callback_ask_es', 'callback_when_en', 'callback_when_es', 'callback_at_iso', 'callback_at_pacific'];

function makeGlobalStop(old, mode) {
  const keep = { id: old.id, name: 'GLOBAL - Callback Request', display_position: old.display_position, global_node_setting: old.global_node_setting, skippable: false };
  if (mode === 'extract') return Object.assign(keep, { type: 'extract_dynamic_variables', variables: CB_VARS, edges: [P('e-global-stop-ok', 'Always', 'node-cb-compute')], else_edge: P('e-global-stop-else', 'Else', 'node-cb-compute') });
  return Object.assign(keep, { type: 'conversation', instruction: { type: 'prompt', text: TXT.globalStopAsk }, edges: [P('e-global-stop-time', TXT.cbGives + ' This includes a time they already gave before you asked.', 'node-cb-extract'), P('e-global-stop-none', TXT.cbNoTime, 'node-end-incomplete')] });
}

function patch(flow, globalMode) {
  const byId = (id) => { const n = flow.nodes.find((x) => x.id === id); if (!n) throw new Error('missing node ' + id); return n; };
  if (flow.nodes.some((n) => n.id === 'node-cb-extract')) throw new Error('already patched (node-cb-extract exists)');
  const log = [];
  const inc = byId('node-end-incomplete'), nrc = byId('node-speak-nonret-close'), dy = byId('node-disq-year');

  // ---------- 1. Callback request ----------
  flow.nodes.push(
    extractNode('node-cb-extract', 'Callback: Extract Time', pos(inc, 0, 300), CB_VARS, 'node-cb-compute'),
    codeNode('node-cb-compute', 'Callback: Resolve Time (deterministic)', pos(inc, 300, 300), CODE_CB, CB_OUT_VARS, 'node-cb-branch'),
    { id: 'node-cb-branch', name: 'Callback: Route', type: 'branch', skippable: false, display_position: pos(inc, 600, 300),
      edges: [EQS('e-cb-confirm', [['{{callback_next}}', '==', 'confirm']], 'node-cb-confirm'), EQS('e-cb-out', [['{{callback_next}}', '==', 'out']], 'node-cb-out'), EQS('e-cb-reask', [['{{callback_next}}', '==', 'reask']], 'node-cb-reask')],
      else_edge: P('e-cb-else', 'Else', 'node-end-incomplete') },
    convo('node-cb-reask', 'Callback: Ask When', pos(inc, 900, 150), TXT.reask, [P('e-cb-reask-time', TXT.cbGives, 'node-cb-extract'), P('e-cb-reask-none', TXT.cbNoTime, 'node-end-incomplete')]),
    convo('node-cb-confirm', 'Callback: Confirm', pos(inc, 900, 300), TXT.confirm, [P('e-cb-confirm-change', 'The caller changes or corrects the day or the time.', 'node-cb-extract'), P('e-cb-confirm-ok', 'The caller accepts, says okay / thanks / bye, or has nothing to change.', 'node-cb-end')]),
    endNode('node-cb-end', 'End: Callback Booked', pos(inc, 1200, 300), TXT.cbEnd),
    endNode('node-cb-out', 'End: Callback Outside Window', pos(inc, 900, 450), TXT.cbOut),
  );
  let hits = 0;
  for (const n of flow.nodes) for (const e of n.edges || []) {
    if (e.destination_node_id === 'node-end-incomplete' && /call(ed)? back later/i.test(e.transition_condition.prompt || '') && n.id.indexOf('node-cb-') !== 0) { e.destination_node_id = 'node-cb-extract'; hits++; }
  }
  if (!hits) throw new Error('no "call back later" edge into node-end-incomplete found');
  log.push('callback: 7 nodes added, ' + hits + ' "not a good time / call back later" edge(s) -> node-cb-extract');
  const gi = flow.nodes.findIndex((n) => n.id === 'node-global-stop');
  if (gi === -1 || flow.nodes[gi].type !== 'end') throw new Error('node-global-stop not found as an end node');
  flow.nodes[gi] = makeGlobalStop(flow.nodes[gi], globalMode);
  log.push('node-global-stop -> ' + globalMode + ' (same trigger condition), feeds the callback flow');

  // ---------- 2. Non-retainer live transfer ----------
  const xEn = byId('node-xfer-warm-en'), xEs = byId('node-xfer-warm-es');
  const xfer = (src, id, name, text, handoff, p) => Object.assign(JSON.parse(JSON.stringify(src)), {
    id, name, display_position: p, instruction: { type: 'static_text', text },
    transfer_option: Object.assign(JSON.parse(JSON.stringify(src.transfer_option)), { private_handoff_option: { type: 'static_message', message: handoff } }),
    edge: { id: 'e-' + id.replace('node-', '') + '-failed', destination_node_id: 'node-nonret-busy', transition_condition: { type: 'prompt', prompt: 'Transfer failed' } },
  });
  flow.nodes.push(
    codeNode('node-nonret-hours', 'Non-Retainer: Business Hours? (deterministic)', pos(nrc, 0, -450), CODE_HOURS, ['nonret_hours'], 'node-nonret-hours-branch'),
    { id: 'node-nonret-hours-branch', name: 'Non-Retainer: Route by Hours', type: 'branch', skippable: false, display_position: pos(nrc, 300, -450),
      edges: [EQS('e-nr-hours-open', [['{{nonret_hours}}', '==', 'open']], 'node-nonret-offer')], else_edge: P('e-nr-hours-else', 'Else', 'node-speak-nonret-close') },
    convo('node-nonret-offer', 'Non-Retainer: Offer Live Transfer', pos(nrc, 600, -450), TXT.nrOffer, [P('e-nr-offer-yes', TXT.nrYes, 'node-nonret-lang'), P('e-nr-offer-no', TXT.nrNo, 'node-speak-nonret-close')]),
    extractNode('node-nonret-lang', 'Non-Retainer: Caller Language', pos(nrc, 900, -450), [{ name: 'call_language', type: 'enum', choices: ['English', 'Spanish'], description: TXT.lang }], 'node-nonret-xfer-prep'),
    codeNode('node-nonret-xfer-prep', 'Non-Retainer: Mark Live Transfer', pos(nrc, 1200, -450), CODE_XFER, ['nonret_live_transfer'], 'node-nonret-xfer-lang'),
    { id: 'node-nonret-xfer-lang', name: 'Non-Retainer: Transfer Language Router', type: 'branch', skippable: false, display_position: pos(nrc, 1500, -450),
      edges: [EQS('e-nr-xfer-es', [['{{call_language}}', '==', 'Spanish']], 'node-nonret-xfer-es')], else_edge: P('e-nr-xfer-en', 'Else', 'node-nonret-xfer-en') },
    xfer(xEn, 'node-nonret-xfer-en', 'Non-Retainer: Live Transfer (English)', 'Perfect, connecting you now. Please hold for just a moment.',
      "Hi, this is Alice, the AI intake assistant at Knight Law Group. I'm connecting you with a caller who qualifies as a non-retainer lead and would like to set up a consultation now.", pos(nrc, 1800, -550)),
    xfer(xEs, 'node-nonret-xfer-es', 'Non-Retainer: Live Transfer (Spanish)', 'Perfecto, le comunico ahora. Por favor, espere un momento.',
      'Hola, le habla Alice, la asistente de admisión con inteligencia artificial de Knight Law Group. Le comunico con un cliente que califica como caso sin retención y quiere programar una consulta ahora.', pos(nrc, 1800, -350)),
    convo('node-nonret-busy', 'Non-Retainer: Transfer Failed Close', pos(nrc, 2100, -450), TXT.nrBusy, [], { skip_response_edge: P('e-nr-busy-skip', 'Skip response', 'node-end-nonret') }),
  );
  const xnr = byId('node-extract-name-nr');
  let nrHits = 0;
  for (const e of [...xnr.edges, xnr.else_edge]) if (e.destination_node_id === 'node-speak-nonret-close') { e.destination_node_id = 'node-nonret-hours'; nrHits++; }
  if (nrHits !== 2) throw new Error('node-extract-name-nr: expected 2 edges to node-speak-nonret-close, found ' + nrHits);
  log.push('non-retainer: 9 nodes added, node-extract-name-nr -> node-nonret-hours (closed / declined / failed -> booking-link close)');

  // ---------- 3. Arbitration lines word for word ----------
  const lines = {};
  for (const k of ['lease', 'buyout', 'tesla']) {
    const t = byId('node-disq-arb-' + k).instruction.text;
    const en = t.match(/English: "([^\n]+)"\n/), es = t.match(/Spanish: "([^\n]+)"\n/);
    if (!en || !es) throw new Error('arbitration line not found in node-disq-arb-' + k);
    lines[k] = { en: en[1], es: es[1], p: byId('node-disq-arb-' + k).display_position };
  }
  flow.nodes = flow.nodes.filter((n) => !/^node-disq-arb-(lease|buyout|tesla)$/.test(n.id));
  const bb = byId('node-branch-bad');
  let arbHits = 0;
  for (const e of bb.edges) if (/^node-disq-arb-/.test(e.destination_node_id)) { e.destination_node_id = 'node-arb-lang'; arbHits++; }
  if (arbHits !== 3) throw new Error('node-branch-bad: expected 3 arbitration edges, found ' + arbHits);
  const arbEdges = [];
  const statics = [];
  for (const k of ['lease', 'buyout', 'tesla']) for (const lg of ['en', 'es']) {
    const id = 'node-disq-arb-' + k + '-' + lg;
    arbEdges.push(EQS('e-arb-' + k + '-' + lg, [['{{bad_reason}}', '==', 'arbitration_' + k], ['{{call_language}}', lg === 'es' ? '==' : '!=', 'Spanish']], id));
    statics.push({ id, name: 'Disqualify: Arbitration (' + ({ lease: 'Lease', buyout: 'Lease Buyout', tesla: 'Tesla' })[k] + ', ' + (lg === 'es' ? 'Spanish' : 'English') + ')', type: 'conversation', skippable: false,
      display_position: { x: lines[k].p.x + (lg === 'es' ? 300 : 0), y: lines[k].p.y }, instruction: { type: 'static_text', text: lines[k][lg] },
      edges: [P('e-' + id.replace('node-', '') + '-done', TXT.arbDone, 'node-end-bad'), P('e-' + id.replace('node-', '') + '-more', TXT.arbMore, 'node-disq-arb-after')] });
  }
  flow.nodes.push(
    extractNode('node-arb-lang', 'Arbitration: Caller Language', pos(dy, 200, 600), [{ name: 'call_language', type: 'enum', choices: ['English', 'Spanish'], description: TXT.lang }], 'node-arb-branch'),
    { id: 'node-arb-branch', name: 'Arbitration: Route by Reason + Language', type: 'branch', skippable: false, display_position: pos(dy, 400, 600), edges: arbEdges, else_edge: P('e-arb-else', 'Else', 'node-end-bad') },
    ...statics,
    convo('node-disq-arb-after', 'Disqualify: Arbitration (follow-up)', pos(dy, 1100, 600), TXT.arbAfter, [P('e-disq-arb-after-done', 'Caller acknowledges, accepts it, or has no further questions', 'node-end-bad')]),
  );
  log.push('arbitration: 3 prompt nodes -> language router + 6 static-text nodes (word for word) + 1 follow-up node');

  // ---------- integrity: every edge points at a node that exists ----------
  const ids = new Set(flow.nodes.map((n) => n.id));
  for (const n of flow.nodes) for (const e of [...(n.edges || []), n.else_edge, n.edge, n.skip_response_edge].filter(Boolean)) {
    if (!ids.has(e.destination_node_id)) throw new Error(n.id + ' -> missing ' + e.destination_node_id);
  }
  return log;
}

module.exports = { patch };

if (require.main === module) (async () => {
  const H = { Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };
  for (const [fid, ver] of Object.entries(FLOWS)) {
    if (APPLY && !/^[0-9]+$/.test(ver || '')) throw new Error('APPLY needs OUT_VER and IN_VER (draft flow versions)');
    const q = APPLY ? '?version=' + ver : '';
    const flow = await (await fetch('https://api.retellai.com/get-conversation-flow/conversation_flow_' + fid + q, { headers: H })).json();
    if (APPLY && flow.is_published) throw new Error(fid + ' version ' + ver + ' is PUBLISHED — refusing to edit. Use the draft version.');
    const before = flow.nodes.length;
    let mode = process.env.GLOBAL_STOP || 'extract';
    const orig = JSON.parse(JSON.stringify(flow.nodes));
    let log = patch(flow, mode);
    console.log('\n===== ' + fid + ' v' + flow.version + ' (published=' + flow.is_published + ', ' + before + ' -> ' + flow.nodes.length + ' nodes)\n  ' + log.join('\n  '));
    fs.writeFileSync(path.join(OUT, fid + '_v' + flow.version + '_patched.json'), JSON.stringify(flow.nodes, null, 1));
    if (!APPLY) continue;
    const send = async () => fetch('https://api.retellai.com/update-conversation-flow/conversation_flow_' + fid + q, { method: 'PATCH', headers: H, body: JSON.stringify({ nodes: flow.nodes }) });
    let res = await send();
    if (!res.ok && mode === 'extract') {
      const err = (await res.text()).slice(0, 400);
      console.log('  PATCH ' + res.status + ' with an extract-type global node: ' + err + '\n  retrying with GLOBAL_STOP=conversation');
      flow.nodes = JSON.parse(JSON.stringify(orig));
      mode = 'conversation';
      log = patch(flow, mode);
      res = await send();
    }
    console.log('  PATCH ' + res.status + (res.ok ? ' OK (global stop = ' + mode + ')' : ' ' + (await res.text()).slice(0, 600)));
    if (!res.ok) process.exit(1);
    const v = await (await fetch('https://api.retellai.com/get-conversation-flow/conversation_flow_' + fid + q, { headers: H })).json();
    const g = (id) => v.nodes.find((n) => n.id === id);
    const pub = await (await fetch('https://api.retellai.com/get-conversation-flow/conversation_flow_' + fid + '?version=0', { headers: H })).json();
    console.log('  verify v' + v.version + ' (published=' + v.is_published + '): nodes=' + v.nodes.length + ' cb code=' + (g('node-cb-compute').code === CODE_CB) + ' hours code=' + (g('node-nonret-hours').code === CODE_HOURS)
      + ' global-stop=' + g('node-global-stop').type + ' xnr->' + g('node-extract-name-nr').edges[0].destination_node_id + ' static arb=' + v.nodes.filter((n) => /^node-disq-arb-.*-(en|es)$/.test(n.id) && n.instruction.type === 'static_text').length
      + ' | published v0 untouched=' + !pub.nodes.some((n) => n.id === 'node-cb-extract'));
  }
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
