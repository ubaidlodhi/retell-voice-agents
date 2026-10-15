// Intake Alice (both flows on +1 213-205-3651), DRAFT v1 only — make her listen and sound human (Ubaid 2026-10-15).
// Evidence: 32 real intake calls since 2026-09-25 (re-asked facts the caller already gave, invented Spanish that
// disqualified a CPO lead, leading "So you mean it was new?", stale global-prompt rules, 16% of her turns cut off,
// minutes spent talking to voicemail menus).
//   node patch_humanize.js           -> dry run, writes out/<flow>_global_prompt.md + a change log
//   APPLY=1 node patch_humanize.js   -> PATCHes the draft flow + draft agent versions (refuses published ones)
const fs = require('fs');
const path = require('path');
const KEY = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const H = { Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };
const API = 'https://api.retellai.com';
const APPLY = process.env.APPLY === '1';
const OUT = path.join(__dirname, 'out');
fs.mkdirSync(OUT, { recursive: true });
const TARGETS = [
  { flow: 'conversation_flow_b4e1b9683eaf', agent: 'agent_de01f772a9de26ecf4387115a9', ver: 1, outbound: true },
  { flow: 'conversation_flow_fce8e3f30b49', agent: 'agent_22874d74b1dd6b9d6d72aa4c67', ver: 1, outbound: false },
];
const MODEL = { type: 'cascading', model: 'gpt-5.5', high_priority: true };
const AGENT_SETTINGS = { interruption_sensitivity: 0.7, language: ['en-US', 'es-419'] };

// ---------- global prompt ----------
const GP = [
  ['acknowledgments',
    '- Brief acknowledgments only ("Got it", "I see", "Okay"). Don\'t thank after every answer.',
    `- Listen, then react. Before your next question, respond in a few words to what the caller actually said, using their own details. When they first describe the problem, show brief, genuine empathy (caller: "the transmission keeps slipping" -> "Ugh, that's stressful, especially on a car you count on."). React naturally to later details too (caller: "it's been at the dealer for three weeks" -> "Three weeks? That's a long time to be without it."). A plain "yes" or "no" needs no reaction: go straight to the next question.
- Keep a reaction to one short sentence, never reuse the same one in a call, and never react to something the caller didn't say. Don't start your turns with "Okay", and don't thank after every answer. This applies in every step: put the reaction right before the scripted question.`],
  ['personality',
    '- Conversational and human: contractions, natural fillers ("so", "okay", "got it"), 1-2 sentences per turn. No lists or formatted text — you\'re speaking.',
    '- Warm, calm and unhurried, like a kind paralegal who has heard this story many times and genuinely cares. Contractions, plain words, 1-2 short sentences per turn. No lists or formatted text — you\'re speaking.'],
  ['latin american spanish',
    'Never ask which language they prefer. Be fully fluent and natural in both.',
    'Never ask which language they prefer. Be fully fluent and natural in both. In Spanish, speak Latin American (Mexican) Spanish: use "usted" and "carro", never Spain-only words such as "vale", "coche" or "vosotros".'],
];
const VERIFICATION = `## Verification
The name must match the caller's driver's license; the contact step handles that check and the spelling (a name is spelled out loud at most once per call). Read the email back once together with the consent question, never spell it out, and never read back the phone number. Read the vehicle's year, make and model back once; if the caller corrects any of it, the correction wins.

`;
const ESCALATION = `## Escalation (handled automatically by global nodes)
- FAQ — caller asks a general question about the firm, fees, lemon law, the process, or timelines -> answer it briefly, then resume where you left off.
- HUMAN — caller asks for a person -> address it once (you can take the basics so they don't have to repeat themselves); if they still want a person, they are connected.
- CALLBACK — caller is busy, driving, or asks to be called back -> ask when, and confirm the time.`;

// ---------- node edits: [node, label, from, to] (each `from` must match exactly once) ----------
const ALREADY = (confirm) => ` If the caller already told you earlier, don't ask the question: confirm it in a few words instead (${confirm}).`;
const NODE = [
  ['node-q-possession', 'already said: in the shop',
    'A vehicle that is in the shop or being repaired still counts as yes.',
    'A vehicle that is in the shop or being repaired still counts as yes. If the caller already said where it is (for example "it\'s in the shop", "it\'s at the dealer"), don\'t ask the question: confirm it in a few words ("And it\'s still yours, just at the shop right now?").'],
  ['node-ret-newused', 'already said',
    'Ask it the same way whether the vehicle was bought or leased.',
    'Ask it the same way whether the vehicle was bought or leased.' + ALREADY('"And you got it new, right?"')],
  ['node-ret-newused', 'neutral re-ask instead of "So you mean it was new?"',
    'If the caller\'s answer comes through only as "No" or "Nope" (or is otherwise unclear and not clearly "used"), do NOT re-ask the same question - a bare "No" here is almost always a mis-transcription of "New." Confirm it ONCE in the caller\'s language: "So you mean it was new?" Then wait. If they confirm (yes / correct / right), treat the vehicle as purchased NEW and move on. If they clarify it was actually used or pre-owned, treat it as USED.',
    'If the answer comes through only as "No" or "Nope", or is otherwise unclear, ask ONCE, briefly and neutrally, without suggesting an answer: "Sorry, was it new or used?" (Spanish: "Perdón, ¿era nuevo o usado?"). A bare "No" is often a mis-heard "New", but let the caller say which.'],
  ['node-ret-cpo', 'Spanish line + already said',
    'Ask (caller\'s language): "Is it certified pre-owned, also known as CPO?" Then wait.',
    'Ask (caller\'s language): "Is it certified pre-owned, also known as CPO?" In Spanish: "¿Es un vehículo certificado por el fabricante, lo que llaman CPO o certified pre-owned?" Never call it "seminuevo": that only means used. Then wait.' + ALREADY('"And it was certified pre-owned, right?"')],
  ['node-ret-cpo', 'Spanish CPO explanation',
    'Does that sound like what you got, or are you still not sure?" Then wait.',
    'Does that sound like what you got, or are you still not sure?" In Spanish: "CPO significa que el fabricante inspeccionó y certificó el vehículo usado, y que vino con una garantía adicional sin costo extra para usted. ¿Le suena a lo que usted recibió, o todavía no está seguro?" Then wait.'],
  ['node-ret-cpo', 'clarify before disqualifying',
    'that does not actually confirm CPO, do NOT assume it is certified pre-owned.',
    'that does not actually confirm CPO, do NOT assume it is certified pre-owned. Only treat it as NOT certified on a clear no: if the answer is garbled or you can\'t tell what they meant, ask once more in simple words before deciding.'],
  ['node-ret-repairs', 'Spanish line + already said',
    'Ask (caller\'s language): "Have you visited a dealership to try to get it repaired?" Then wait.',
    'Ask (caller\'s language): "Have you visited a dealership to try to get it repaired?" In Spanish: "¿Ya lo llevó a un concesionario para que intentaran repararlo?" Then wait. If the caller already said the vehicle has been to the dealer or is in the shop for repairs, don\'t ask the question: confirm it in a few words ("And the dealer\'s already tried to fix it, right?").'],
  ['node-ret-owner', 'Spanish line + already said',
    'are you the owner of the car, or did you sign the sales or lease contract?"',
    'are you the owner of the car, or did you sign the sales or lease contract?" In Spanish: "Y para confirmar, ¿usted es el dueño del carro, o firmó el contrato de compra o de arrendamiento?"' + ALREADY('"And you\'re the one on the contract, right?"')],
  ['node-ret-contact', 'Spanish consent line',
    '"And I\'ve got your email as {{Email}} — is it okay if our team reaches you by text and email?" Then wait.',
    '"And I\'ve got your email as {{Email}} — is it okay if our team reaches you by text and email?" In Spanish: "Y tengo su correo como {{Email}}. ¿Está bien si nuestro equipo le contacta por mensaje de texto y por correo electrónico?" Then wait.'],
  ['node-nonret-confirm', 'Spanish consent line',
    '"And I\'ve got your email as {{Email}} — is it okay if our team reaches you by text and email?" Then wait.',
    '"And I\'ve got your email as {{Email}} — is it okay if our team reaches you by text and email?" In Spanish: "Y tengo su correo como {{Email}}. ¿Está bien si nuestro equipo le contacta por mensaje de texto y por correo electrónico?" Then wait.'],
  ['node-consent-recheck-ret', 'Spanish re-confirm line',
    'is it okay if our team reaches you there?" Then wait.',
    'is it okay if our team reaches you there?" In Spanish: "Entiendo. Solo para que sepa, el mensaje de texto y el correo son los medios oficiales que usamos para enviarle los documentos para firmar y recibirlos de vuelta. ¿Está bien si nuestro equipo le contacta por ahí?" Then wait.'],
  ['node-consent-recheck-nonret', 'Spanish re-confirm line',
    'is it okay if our team reaches you there?" Then wait.',
    'is it okay if our team reaches you there?" In Spanish: "Entiendo. Solo para que sepa, el mensaje de texto y el correo son los medios oficiales que usamos para enviarle los documentos para firmar y recibirlos de vuelta. ¿Está bien si nuestro equipo le contacta por ahí?" Then wait.'],
];
const EDGE = [
  ['node-ret-newused', 'Caller indicates the vehicle was purchased NEW. This includes the case where the caller\'s answer came through only as "No" or "Nope" and then they confirmed "yes" to "So you mean it was new?" - a bare "No" to the new-or-used question is a mis-transcription of "New."',
    'Caller indicates the vehicle was NEW when they got it (including after the short "new or used?" re-ask, or confirming "you got it new, right?").'],
  ['node-ret-cpo', 'Caller says it is NOT certified pre-owned (no)', 'Caller CLEARLY says it is NOT certified pre-owned (a clear no, not a garbled or unclear answer)'],
  ['node-ret-repairs', 'Caller says YES, they attempted repairs at a dealership', 'Caller says YES, they attempted repairs at a dealership (including a vehicle that is at the dealer or in the shop for repairs right now)'],
];

// Outbound only: stop talking to voicemail menus / system messages (3 calls spent ~4.6 min each on one).
// Deliberately NOT the voicemail greeting itself (the agent's voicemail_option leaves the client's message there),
// and NOT call screeners or "this call is recorded" notices.
const AUTOMATED = {
  id: 'node-global-automated', name: 'GLOBAL - Automated System (end)', type: 'end', skippable: false, speak_during_execution: false,
  display_position: { x: 4900, y: 2400 },
  instruction: { type: 'prompt', text: 'Do not say anything. End the call.' },
  global_node_setting: {
    condition: 'The other side is clearly a machine running a menu or a system message, not a person: a full mailbox, a "press 1 to listen to your message" menu after a recording, "your message has been sent", or "the recording has reached its maximum length". NOT a voicemail greeting asking you to leave a message, NOT a call-screening assistant asking who is calling or for your name and reason (answer those), NOT a "this call may be recorded" notice, and NOT a person.',
    positive_finetune_examples: [
      { transcript: [{ role: 'user', content: 'Mailbox is full. To send an SMS notification, press five.' }] },
      { transcript: [{ role: 'user', content: 'Su grabación ha alcanzado la longitud máxima. Para volver a escuchar su mensaje, oprima uno. Para borrar y volver a grabar su mensaje, oprima tres.' }] },
      { transcript: [{ role: 'user', content: 'To listen to your message, press one. To re-record, press two.' }] },
    ],
    negative_finetune_examples: [
      { transcript: [{ role: 'user', content: "Hi. If you record your name and reason for calling, I'll see if this person is available." }] },
      { transcript: [{ role: 'user', content: 'Thanks. Please stay on the line.' }] },
      { transcript: [{ role: 'user', content: 'This call may be recorded for quality assurance.' }] },
      { transcript: [{ role: 'user', content: 'Hello? Hello?' }] },
    ],
  },
};

function once(s, from, to, label) {
  const n = s.split(from).length - 1;
  if (n !== 1) throw new Error(label + ': anchor found ' + n + ' times');
  return s.replace(from, () => to);
}

function patchFlow(flow, outbound) {
  const log = [];
  if (flow.global_prompt.indexOf('Listen, then react.') !== -1) throw new Error('already patched');
  let gp = flow.global_prompt;
  for (const [label, from, to] of GP) { gp = once(gp, from, to, 'global ' + label); log.push('global: ' + label); }
  const v0 = gp.indexOf('## Verification'), v1 = gp.indexOf('## Escalation');
  if (v0 === -1 || v1 < v0) throw new Error('Verification/Escalation sections not found');
  gp = gp.slice(0, v0) + VERIFICATION + ESCALATION + gp.slice(gp.indexOf('\n', gp.indexOf('- STOP')) === -1 ? gp.length : gp.indexOf('\n', gp.indexOf('- STOP')));
  if (gp.indexOf('- STOP') !== -1 || gp.indexOf('give the callback line') !== -1) throw new Error('stale escalation text still present');
  log.push('global: Verification trimmed to its essentials, Escalation rewritten (HUMAN + CALLBACK match the real flow)');
  const byId = (id) => { const n = flow.nodes.find((x) => x.id === id); if (!n) throw new Error('missing ' + id); return n; };
  for (const [id, label, from, to] of NODE) { const n = byId(id); n.instruction.text = once(n.instruction.text, from, to, id + ' ' + label); log.push(id + ': ' + label); }
  for (const [id, from, to] of EDGE) {
    const e = byId(id).edges.filter((x) => x.transition_condition.prompt === from);
    if (e.length !== 1) throw new Error(id + ' edge not found: ' + from.slice(0, 50));
    e[0].transition_condition.prompt = to; log.push(id + ': edge reworded');
  }
  if (outbound) {
    if (flow.nodes.some((n) => n.id === AUTOMATED.id)) throw new Error('automated node exists');
    flow.nodes.push(JSON.parse(JSON.stringify(AUTOMATED)));
    log.push('global node added: end the call on voicemail menus / system messages (outbound only)');
  }
  return { gp, log };
}

(async () => {
  const req = async (method, p, body) => {
    const r = await fetch(API + p, { method, headers: H, body: body ? JSON.stringify(body) : undefined });
    const t = await r.text();
    if (!r.ok) throw new Error(method + ' ' + p + ' ' + r.status + ' ' + t.slice(0, 400));
    return t ? JSON.parse(t) : {};
  };
  for (const t of TARGETS) {
    const flow = await req('GET', '/get-conversation-flow/' + t.flow + '?version=' + t.ver);
    const agent = await req('GET', '/get-agent/' + t.agent + '?version=' + t.ver);
    if (flow.is_published || agent.is_published) throw new Error(t.flow + ': version ' + t.ver + ' is published — refusing');
    if (agent.response_engine.version !== t.ver) throw new Error('agent v' + t.ver + ' does not point at flow v' + t.ver);
    fs.writeFileSync(path.join(OUT, 'backup_' + t.flow + '_v' + t.ver + '.json'), JSON.stringify(flow, null, 1));
    const before = flow.global_prompt.length;
    const { gp, log } = patchFlow(flow, t.outbound);
    fs.writeFileSync(path.join(OUT, t.flow + '_global_prompt.md'), gp);
    console.log('\n===== ' + t.flow + ' v' + t.ver + ' (draft) global prompt ' + before + ' -> ' + gp.length + ' chars\n  ' + log.join('\n  '));
    console.log('  model ' + JSON.stringify(flow.model_choice) + ' -> ' + JSON.stringify(MODEL));
    console.log('  agent interruption ' + agent.interruption_sensitivity + ' -> ' + AGENT_SETTINGS.interruption_sensitivity + ', language ' + JSON.stringify(agent.language) + ' -> ' + JSON.stringify(AGENT_SETTINGS.language));
    if (!APPLY) continue;
    await req('PATCH', '/update-conversation-flow/' + t.flow + '?version=' + t.ver, { global_prompt: gp, nodes: flow.nodes, model_choice: MODEL });
    await req('PATCH', '/update-agent/' + t.agent + '?version=' + t.ver, AGENT_SETTINGS);
    const f2 = await req('GET', '/get-conversation-flow/' + t.flow + '?version=' + t.ver);
    const a2 = await req('GET', '/get-agent/' + t.agent + '?version=' + t.ver);
    const p0 = await req('GET', '/get-conversation-flow/' + t.flow + '?version=0');
    console.log('  verify: prompt matches=' + (f2.global_prompt === gp) + ' nodes=' + f2.nodes.length + ' model=' + JSON.stringify(f2.model_choice)
      + ' agent=' + a2.interruption_sensitivity + '/' + JSON.stringify(a2.language) + ' draft=' + !a2.is_published
      + ' | published v0 untouched=' + (p0.global_prompt.indexOf('Listen, then react.') === -1));
  }
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
