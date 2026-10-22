// Alice Intake: "Alice — Workshop Change Spec (Oct 1, 2026)" (Knight_Law_Group/client/), items decided with Ubaid 2026-10-22.
// New DRAFTS from the live versions: Intake Outbound v3 -> v4, Intake Inbound v2 -> v3. Nothing is published here.
//   #1 Shorter opening (outbound + inbound, Ubaid: inbound too): greeting keeps the disclosure, new last line, then goes
//      straight on (skip_response) to the California question. "Mind if I ask…", the "having issues?" gate, the
//      "problems in the past?" branch and the non-lemon disqualification are removed.
//   #2 Lead says the car is at the dealer / in the shop before the possession question -> possession is skipped and
//      Alice says "Got it, so it's with the dealer now." with the vehicle question (repairs were already skipped: Oct 19).
//   #3 Outbound only: no text/email consent question; the email is confirmed instead ("…is that right?", Ubaid).
//      Inbound keeps the consent question unchanged.
//   #4 (part) Intake never says the lead's name: hand-off line "Okay, thank you, I just sent you…", inbound greeting,
//      inbound resume / opt-out greetings, plus a global rule. The driver's-license name check (TURN 1 of the contact
//      steps) waits for Ubaid's decision and is excepted from the rule for now.
//   node patch_intake_workshop.js / APPLY=1 node patch_intake_workshop.js
const fs = require('fs');
const path = require('path');
const KEY = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const H = { Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };
const APPLY = process.env.APPLY === '1';
const OUT = path.join(__dirname, 'out');
const AGENTS = [
  { label: 'outbound', agent: 'agent_de01f772a9de26ecf4387115a9', base: 3, flow: 'conversation_flow_b4e1b9683eaf' },
  { label: 'inbound', agent: 'agent_22874d74b1dd6b9d6d72aa4c67', base: 2, flow: 'conversation_flow_fce8e3f30b49' },
];

const P = (id, prompt, dest) => ({ id, destination_node_id: dest, transition_condition: { type: 'prompt', prompt } });
const EQ = (id, v, val, dest) => ({ id, destination_node_id: dest, transition_condition: { type: 'equation', operator: '&&', equations: [{ left: '{{' + v + '}}', operator: '==', right: val }] } });
const SKIP = (id, dest) => ({ id, destination_node_id: dest, transition_condition: { type: 'prompt', prompt: 'Skip response' } });

const OUT_EN = 'Hi, this is Alice with Knight Law Group, calling about the lemon law inquiry you submitted for your vehicle. Just a heads-up, I\'m an AI assistant and this line is recorded. I can connect you to someone on our team anytime you\'d like. I\'m guessing you\'re reaching out because you\'re having issues with your vehicle, so let me get a little information about the car.';
const OUT_ES = 'Hola, le habla Alice, de Knight Law Group, sobre la consulta que usted envió acerca de su vehículo. Le aviso que soy una asistente de inteligencia artificial y que esta línea está grabada. Puedo comunicarle con una persona de nuestro equipo cuando usted quiera. Me imagino que nos contactó porque está teniendo problemas con su vehículo, así que déjeme tomar un poco de información sobre el carro.';
const IN_EN = 'Thanks for calling Knight Law Group, this is Alice. Just a heads-up, I\'m an AI assistant and this line is recorded. I can connect you to someone on our team anytime you\'d like. I\'m guessing you\'re reaching out because you\'re having issues with your vehicle, so let me get a little information about the car.';
const IN_ES = 'Gracias por llamar a Knight Law Group, le habla Alice. Le aviso que soy una asistente de inteligencia artificial y que esta línea está grabada. Puedo comunicarle con una persona de nuestro equipo cuando usted quiera. Me imagino que nos llama porque está teniendo problemas con su vehículo, así que déjeme tomar un poco de información sobre el carro.';
const TAIL_EN = 'Say it word for word as ONE single turn. It ends on a statement on purpose: do NOT add a question to it. The next step asks the first qualifying question right away. Continue the whole call in the language you greeted in.';

const INTRO_OUT = 'Outbound opening greeting, ONE turn. The caller has already picked up and said something — choose the language from their first words (see the Language rules): if they answered with a Spanish greeting such as "aló", "bueno", "diga", "mande", "hola", "sí" or "buenos días/tardes", deliver the greeting in SPANISH; otherwise deliver it in ENGLISH.\n\nEnglish: "' + OUT_EN + '"\nSpanish: "' + OUT_ES + '"\n\n' + TAIL_EN;
const INTRO_OUT_ES = 'Saludo de apertura saliente, EN ESPAÑOL, UNA sola intervención, palabra por palabra: "' + OUT_ES + '"\n\nTermina en una afirmación a propósito: NO le agregue una pregunta. El siguiente paso hace la primera pregunta de inmediato. Continúe toda la llamada en español.';
const INTRO_IN = 'Inbound opening greeting, ONE turn. Never say the caller\'s name. FIRST choose the language: if {{lead_language}} is "Spanish", or the caller opened with a Spanish greeting ("aló", "bueno", "diga", "hola", "buenos días/tardes", "sí"), use the Spanish greeting (see the Language rules); otherwise use the English one.\n\nEnglish: "' + IN_EN + '"\nSpanish: "' + IN_ES + '"\n\n' + TAIL_EN;

const SAID_AT_DEALER = {
  name: 'said_at_dealer', type: 'enum', choices: ['yes', 'unknown'],
  description: '"yes" only if the caller has said that the vehicle is CURRENTLY at a dealership / dealer or in a repair shop (e.g. "it\'s at the dealer right now", "it\'s in the shop", "the dealer has it"). Past visits ("it\'s been to the dealer three times") do NOT count. Otherwise "unknown".',
};
const DEALER_NODE_TEXT = 'The caller already told you the vehicle is at the dealer or in the shop right now, so do NOT ask whether they still have it. In ONE turn (caller\'s language), acknowledge it and ask for the vehicle, mirroring their words (dealer or shop): "Got it, so it\'s with the dealer now. What\'s the year, make, and model of your vehicle?" Spanish: "Entendido, entonces ahorita está en el concesionario. ¿Cuál es el año, la marca y el modelo de su carro?" If the caller already mentioned any of the year, make or model, do NOT re-ask it: ask only for what is missing. Then wait.';

const TURN2_OUT = 'TURN 2 — only AFTER the name is confirmed. Read back ONLY the email to confirm it, in ONE turn: "And I\'ve got your email as {{Email}} — is that right?" In Spanish: "Y tengo su correo como {{Email}}. ¿Es correcto?" Then wait. Do NOT ask for permission to text or email: this lead already gave consent on the form. Do NOT read back or confirm the phone number, and do NOT spell the email out. If the caller says the email is wrong, incorrect, not theirs, or needs to be changed, apologize briefly, ask them to tell you the correct email, and capture the corrected version (you don\'t need to spell it back).\n\n';
const DONE_OUT = 'The caller\'s name has been confirmed AND, in a later turn, they confirmed the email is right (yes) or gave a corrected email.';
const NAME_RULE = '- Never say the caller\'s name out loud: the name on file often comes from a web or Facebook form and can be wrong or mispronounced. Use neutral phrasing instead ("Okay, thank you"). The only exception is the driver\'s-license name check in the contact step.\n';

const HANDOFF_FIX = [
  ["('Muy bien' + (first ? ', ' + first : '') + ' — su acuerdo de representación acaba de salir a su teléfono y a su correo.", "('Muy bien, gracias, le acabo de enviar su acuerdo de representación por mensaje de texto y por correo."],
  ["('Okay' + (first ? ' ' + first : '') + \" — that agreement just went out to your phone and email.", "(\"Okay, thank you, I just sent you the agreement by text and email."],
];
const INB_NAME_FIX = {
  'node-inbound-resume': [['Greet by name and confirm', 'Greet warmly (never say their name) and confirm'], ['"Hi {{Name}}, thanks', '"Hi, thanks']],
  'node-inbound-resume-es': [['Salude por su nombre y confirme', 'Salude cordialmente (nunca diga su nombre) y confirme'], ['"Hola {{Name}}, gracias', '"Hola, gracias']],
  'node-inbound-optout': [['greet by name if we have it: "Hi {{Name}}, thanks', 'do not say their name: "Hi, thanks']],
  'node-inbound-optout-es': [['salude por su nombre si lo tenemos: "Hola {{Name}}, gracias', 'no diga su nombre: "Hola, gracias']],
};

const api = async (method, p, body) => {
  const r = await fetch('https://api.retellai.com' + p, { method, headers: H, body: body ? JSON.stringify(body) : undefined });
  const t = await r.text();
  if (!r.ok) throw new Error(method + ' ' + p + ' -> ' + r.status + ' ' + t.slice(0, 400));
  return t ? JSON.parse(t) : {};
};
const replaceOnce = (s, a, b, what) => { if (s.split(a).length !== 2) throw new Error(what + ': anchor found ' + (s.split(a).length - 1) + 'x: ' + a.slice(0, 60)); return s.replace(a, b); };
const edgesOf = (n) => [...(n.edges || []), n.else_edge, n.edge, n.always_edge, n.skip_response_edge].filter(Boolean);

function patchFlow(f, s) {
  const by = (x) => { const n = f.nodes.find((y) => y.id === x); if (!n) throw new Error(s.label + ': missing ' + x); return n; };
  const log = [];
  // #1 opening
  const intro = by('node-intro');
  intro.instruction.text = s.label === 'outbound' ? INTRO_OUT : INTRO_IN;
  intro.edges = [];
  intro.skip_response_edge = SKIP('e-intro-skip', 'node-q-ca');
  if (s.label === 'outbound') {
    const es = by('node-intro-es');
    es.instruction.text = INTRO_OUT_ES;
    es.edges = [];
    es.skip_response_edge = SKIP('e-intro-es-skip', 'node-q-ca');
  }
  const dead = ['node-intro-issue', 'node-past-issue-check', 'node-disq-nonlemon'].filter((x) => f.nodes.some((n) => n.id === x));
  f.nodes = f.nodes.filter((n) => !dead.includes(n.id));
  log.push('#1 greeting + skip to q-ca; removed ' + dead.join(','));
  // #2 at the dealer -> skip possession
  const xl = by('node-extract-lease');
  if (xl.variables.some((v) => v.name === 'said_at_dealer')) throw new Error('already patched');
  xl.variables.push(SAID_AT_DEALER);
  const qv = by('node-q-vehicle');
  f.nodes.push({
    id: 'node-q-vehicle-dealer', name: 'Q: Vehicle (already at the dealer)', type: 'conversation', skippable: false,
    display_position: { x: (qv.display_position || { x: 1350 }).x, y: (qv.display_position || { y: 198 }).y - 220 },
    instruction: { type: 'prompt', text: DEALER_NODE_TEXT },
    edges: [P('e-veh-dealer-done', qv.edges[0].transition_condition.prompt, 'node-extract-vehicle')],
  });
  const al = by('node-after-lease');
  if (al.edges[0].id !== 'e-al-poss') throw new Error('after-lease anchor');
  al.edges.unshift(EQ('e-al-at-dealer', 'said_at_dealer', 'yes', 'node-q-vehicle-dealer'));
  log.push('#2 said_at_dealer -> node-q-vehicle-dealer');
  // #3 outbound: email confirmation instead of consent
  if (s.label === 'outbound') {
    for (const [nid, done, nocon] of [['node-ret-contact', 'e-contact-done', 'e-contact-noconsent'], ['node-nonret-confirm', 'e-nonret-done', 'e-nonret-noconsent']]) {
      const n = by(nid);
      const t = n.instruction.text;
      const a = t.indexOf('TURN 2 — only AFTER the name is confirmed.');
      const b = t.indexOf('Once the name is confirmed and they\'ve answered the text-and-email permission, stop.');
      if (a < 0 || b < a) throw new Error(nid + ': TURN 2 anchors');
      n.instruction.text = t.slice(0, a) + TURN2_OUT + 'Once the name is confirmed and the email is confirmed or corrected, stop.' + t.slice(b + 'Once the name is confirmed and they\'ve answered the text-and-email permission, stop.'.length);
      const e = n.edges.find((x) => x.id === done);
      if (!e) throw new Error(nid + ': ' + done);
      e.transition_condition.prompt = DONE_OUT;
      if (!n.edges.some((x) => x.id === nocon)) throw new Error(nid + ': ' + nocon);
      n.edges = n.edges.filter((x) => x.id !== nocon);
    }
    f.global_prompt = replaceOnce(f.global_prompt, 'read it back in ONE turn with the consent question', 'read it back in ONE turn to confirm it ("is that right?"); never ask for text or email consent (the form already gave it)', 'global consent line');
    const orphans = ['node-consent-recheck-ret', 'node-consent-recheck-nonret'].filter((x) => !f.nodes.some((n) => n.id !== x && edgesOf(n).some((e) => e.destination_node_id === x)));
    f.nodes = f.nodes.filter((n) => !orphans.includes(n.id));
    log.push('#3 email confirm, consent removed; deleted ' + orphans.join(','));
  }
  // #4 no spoken name in Intake
  const prep = by(s.label === 'outbound' ? 'node-ret-handoff-prep' : 'node-inb-qual-prep');
  for (const [a, b] of HANDOFF_FIX) prep.code = replaceOnce(prep.code, a, b, prep.id);
  if (s.label === 'inbound') for (const [nid, fixes] of Object.entries(INB_NAME_FIX)) { const n = by(nid); for (const [a, b] of fixes) n.instruction.text = replaceOnce(n.instruction.text, a, b, nid); }
  f.global_prompt = replaceOnce(f.global_prompt, '- Ask ONE question per turn and wait for the answer.\n', '- Ask ONE question per turn and wait for the answer.\n' + NAME_RULE, 'global core rules');
  log.push('#4 hand-off line, ' + (s.label === 'inbound' ? 'greetings, ' : '') + 'global no-name rule');
  // validate
  const ids = new Set(f.nodes.map((n) => n.id));
  const eids = new Set();
  for (const n of f.nodes) for (const e of edgesOf(n)) {
    if (!ids.has(e.destination_node_id)) throw new Error(n.id + ' -> missing ' + e.destination_node_id);
    if (eids.has(e.id)) throw new Error('duplicate edge id ' + e.id);
    eids.add(e.id);
  }
  if (!ids.has(f.start_node_id)) throw new Error('start node missing');
  const named = f.nodes.filter((n) => /\{\{Name\}\}/.test((n.instruction && n.instruction.text) || '')).map((n) => n.id);
  log.push('spoken {{Name}} left in: ' + (named.join(',') || 'none'));
  return log;
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  for (const s of AGENTS) {
    const live = await api('GET', '/get-agent/' + s.agent + '?version=' + s.base);
    if (!live.is_published) throw new Error(s.label + ' v' + s.base + ' is not live');
    if (!APPLY) {
      const f = await api('GET', '/get-conversation-flow/' + s.flow + '?version=' + live.response_engine.version);
      console.log(s.label + ' (dry run on live flow v' + live.response_engine.version + '):\n  ' + patchFlow(f, s).join('\n  '));
      continue;
    }
    const d = await api('POST', '/create-agent-version/' + s.agent, { base_version: s.base });
    const fv = d.response_engine.version;
    if (d.is_published || fv === live.response_engine.version) throw new Error(s.label + ': bad draft');
    const f = await api('GET', '/get-conversation-flow/' + s.flow + '?version=' + fv);
    fs.writeFileSync(path.join(OUT, 'backup_' + s.flow + '_v' + fv + '.json'), JSON.stringify(f, null, 1));
    const log = patchFlow(f, s);
    await api('PATCH', '/update-conversation-flow/' + s.flow + '?version=' + fv, { nodes: f.nodes, global_prompt: f.global_prompt });
    const v = await api('GET', '/get-conversation-flow/' + s.flow + '?version=' + fv);
    console.log(s.label + ': DRAFT agent v' + d.version + ' / flow v' + fv + ' (published=' + v.is_published + ', nodes ' + v.nodes.length + ')\n  ' + log.join('\n  '));
    console.log('  verify: intro skip=' + !!v.nodes.find((n) => n.id === 'node-intro').skip_response_edge + ' dealer node=' + v.nodes.some((n) => n.id === 'node-q-vehicle-dealer') + ' name rule=' + v.global_prompt.includes('Never say the caller\'s name'));
  }
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
