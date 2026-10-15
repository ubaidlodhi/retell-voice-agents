// Intake draft v1 (both flows) — rework after Ubaid's draft test call call_2fd5d6201e9569b308b0c4d9282.
// The 2026-10-15 "humanize" pass made Alice worse: a stall after "Okay." (no question to answer), robotic
// "And X, right?" confirmations, empathy on every turn (on top of the agent's high-empathy handbook preset), and a
// robotic FAQ hand-back. This rebuilds the touched parts from the pre-humanize draft (out/backup_*_v1.json, which
// had the working published wording) and re-applies only the fixes that held up:
//   kept   : Latin American Spanish, Spanish lines on CPO/repairs/owner/consent, neutral new-or-used re-ask,
//            CPO disqualifies only on a clear no, escalation text that matches the real flow (HUMAN, CALLBACK),
//            the voicemail-menu global node, interruption 0.7, model settings, callback / non-retainer / lease work.
//   removed: "Listen, then react" rule, every "confirm instead of asking" line, "just say Got it and move on",
//            the FAQ hand-back (FAQ is back to the published behaviour: answer, ask if there's anything else with
//            varied wording, return to the pending question once the caller says that's all).
//   new    : Retell's own "skip this node if already answered" (skippable) on the purchase-or-lease, new-or-used and
//            dealer-repairs questions, so a fact the caller already gave is not asked again and not "confirmed";
//            one line asking for a natural lead-in to the next question instead of a cold one.
//   node patch_rework.js / APPLY=1 node patch_rework.js
const fs = require('fs');
const path = require('path');
const KEY = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const H = { Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };
const API = 'https://api.retellai.com';
const APPLY = process.env.APPLY === '1';
const VER = 1;
const FLOWS = ['conversation_flow_b4e1b9683eaf', 'conversation_flow_fce8e3f30b49'];
const SKIPPABLE = ['node-q-lease', 'node-ret-newused', 'node-ret-repairs'];
const REBUILT = ['node-q-possession', 'node-q-lease', 'node-ret-newused', 'node-ret-cpo', 'node-ret-repairs', 'node-ret-owner', 'node-global-faq'];

function once(s, from, to, label) {
  const n = s.split(from).length - 1;
  if (n !== 1) throw new Error(label + ': anchor found ' + n + ' times');
  return s.replace(from, () => to);
}

function globalPrompt(gp) {
  gp = once(gp, '- Brief acknowledgments only ("Got it", "I see", "Okay"). Don\'t thank after every answer.',
    '- Brief acknowledgments only ("Got it", "I see", "Okay"). Don\'t thank after every answer. Lead into the next question the way a person would, with a short connector you vary ("So, quick question —", "And —", "Next thing —"), rather than firing it cold.', 'ack');
  gp = once(gp, 'Never ask which language they prefer. Be fully fluent and natural in both.',
    'Never ask which language they prefer. Be fully fluent and natural in both. In Spanish, speak Latin American (Mexican) Spanish: use "usted" and "carro", never Spain-only words such as "vale", "coche" or "vosotros".', 'spanish');
  gp = once(gp, '- HUMAN — caller asks for a person -> give the callback line and offer to keep helping.',
    '- HUMAN — caller asks for a person -> address it once (you can take the basics so they don\'t have to repeat themselves); if they still want a person, they are connected.', 'human');
  gp = once(gp, '- STOP — caller is busy / driving / wants to call back later -> close warmly.',
    '- CALLBACK — caller is busy, driving, or asks to be called back -> ask when, and confirm the time.', 'callback');
  return gp;
}

// Fixes kept on the rebuilt question nodes (applied to the pre-humanize text).
const NODE_FIX = {
  'node-q-lease': [['If they already clearly said they bought it, do not ask again either: just say "Got it" ("Entendido") and move on.', '']],
  'node-ret-newused': [[
    'If the caller\'s answer comes through only as "No" or "Nope" (or is otherwise unclear and not clearly "used"), do NOT re-ask the same question - a bare "No" here is almost always a mis-transcription of "New." Confirm it ONCE in the caller\'s language: "So you mean it was new?" Then wait. If they confirm (yes / correct / right), treat the vehicle as purchased NEW and move on. If they clarify it was actually used or pre-owned, treat it as USED.',
    'If the answer comes through only as "No" or "Nope", or is otherwise unclear, ask ONCE, briefly and neutrally, without suggesting an answer: "Sorry, was it new or used?" (Spanish: "Perdón, ¿era nuevo o usado?"). A bare "No" is often a mis-heard "New", but let the caller say which.']],
  'node-ret-cpo': [
    ['Ask (caller\'s language): "Is it certified pre-owned, also known as CPO?" Then wait.',
      'Ask (caller\'s language): "Is it certified pre-owned, also known as CPO?" In Spanish: "¿Es un vehículo certificado por el fabricante, lo que llaman CPO o certified pre-owned?" Never call it "seminuevo": that only means used. Then wait.'],
    ['Does that sound like what you got, or are you still not sure?" Then wait.',
      'Does that sound like what you got, or are you still not sure?" In Spanish: "CPO significa que el fabricante inspeccionó y certificó el vehículo usado, y que vino con una garantía adicional sin costo extra para usted. ¿Le suena a lo que usted recibió, o todavía no está seguro?" Then wait.'],
    ['that does not actually confirm CPO, do NOT assume it is certified pre-owned.',
      'that does not actually confirm CPO, do NOT assume it is certified pre-owned. Only treat it as NOT certified on a clear no: if the answer is garbled or you can\'t tell what they meant, ask once more in simple words before deciding.']],
  'node-ret-repairs': [['Ask (caller\'s language): "Have you visited a dealership to try to get it repaired?" Then wait.',
    'Ask (caller\'s language): "Have you visited a dealership to try to get it repaired?" In Spanish: "¿Ya lo llevó a un concesionario para que intentaran repararlo?" Then wait.']],
  'node-ret-owner': [['are you the owner of the car, or did you sign the sales or lease contract?"',
    'are you the owner of the car, or did you sign the sales or lease contract?" In Spanish: "Y para confirmar, ¿usted es el dueño del carro, o firmó el contrato de compra o de arrendamiento?"']],
};
const EDGE_FIX = {
  'node-ret-newused': ['Caller indicates the vehicle was purchased NEW. This includes the case where the caller\'s answer came through only as "No" or "Nope" and then they confirmed "yes" to "So you mean it was new?" - a bare "No" to the new-or-used question is a mis-transcription of "New."',
    'Caller indicates the vehicle was NEW when they got it (including after the short "new or used?" re-ask).'],
  'node-ret-cpo': ['Caller says it is NOT certified pre-owned (no)', 'Caller CLEARLY says it is NOT certified pre-owned (a clear no, not a garbled or unclear answer)'],
  'node-ret-repairs': ['Caller says YES, they attempted repairs at a dealership', 'Caller says YES, they attempted repairs at a dealership (including a vehicle that is at the dealer or in the shop for repairs right now)'],
};

function rework(cur, pre) {
  const log = [];
  const gp = globalPrompt(pre.global_prompt);
  log.push('global prompt rebuilt from the pre-humanize version (+ lead-in line, Latin American Spanish, HUMAN/CALLBACK escalation)');
  for (const id of REBUILT) {
    const i = cur.nodes.findIndex((n) => n.id === id);
    const old = pre.nodes.find((n) => n.id === id);
    if (i === -1 || !old) throw new Error('node missing: ' + id);
    const n = JSON.parse(JSON.stringify(old));
    for (const [from, to] of NODE_FIX[id] || []) n.instruction.text = once(n.instruction.text, from, to, id);
    n.instruction.text = n.instruction.text.replace(/  +/g, ' ').replace(/ \n/g, '\n');
    if (EDGE_FIX[id]) {
      const [from, to] = EDGE_FIX[id];
      const e = n.edges.filter((x) => x.transition_condition.prompt === from);
      if (e.length !== 1) throw new Error(id + ': edge anchor not found');
      e[0].transition_condition.prompt = to;
    }
    n.skippable = SKIPPABLE.includes(id);
    cur.nodes[i] = n;
    log.push(id + ': rebuilt' + (NODE_FIX[id] ? ' + kept fixes' : '') + (n.skippable ? ' + skippable' : ''));
  }
  const leftovers = cur.nodes.filter((n) => n.instruction && /confirm it in a few words|Listen, then react|pick up where we left off/.test(n.instruction.text || '')).map((n) => n.id);
  if (leftovers.length || /Listen, then react/.test(gp)) throw new Error('humanize text still present in: ' + leftovers.join(','));
  return { gp, log };
}

(async () => {
  const req = async (method, p, body) => {
    const r = await fetch(API + p, { method, headers: H, body: body ? JSON.stringify(body) : undefined });
    const t = await r.text();
    if (!r.ok) throw new Error(method + ' ' + p + ' ' + r.status + ' ' + t.slice(0, 400));
    return t ? JSON.parse(t) : {};
  };
  for (const id of FLOWS) {
    const cur = await req('GET', '/get-conversation-flow/' + id + '?version=' + VER);
    if (cur.is_published) throw new Error(id + ' v' + VER + ' is published — refusing');
    const pre = JSON.parse(fs.readFileSync(path.join(__dirname, 'out', 'backup_' + id + '_v' + VER + '.json'), 'utf8'));
    fs.writeFileSync(path.join(__dirname, 'out', 'before_rework_' + id + '_v' + VER + '.json'), JSON.stringify(cur, null, 1));
    const before = cur.global_prompt.length;
    const { gp, log } = rework(cur, pre);
    fs.writeFileSync(path.join(__dirname, 'out', id + '_global_prompt_rework.md'), gp);
    console.log('\n===== ' + id + ' v' + VER + ': global prompt ' + before + ' -> ' + gp.length + ' chars (published: ' + pre.global_prompt.length + ')\n  ' + log.join('\n  '));
    if (!APPLY) continue;
    await req('PATCH', '/update-conversation-flow/' + id + '?version=' + VER, { global_prompt: gp, nodes: cur.nodes });
    const v = await req('GET', '/get-conversation-flow/' + id + '?version=' + VER);
    const g = (x) => v.nodes.find((n) => n.id === x);
    console.log('  verify: prompt=' + (v.global_prompt === gp) + ' nodes=' + v.nodes.length + ' skippable=' + v.nodes.filter((n) => n.skippable).map((n) => n.id).join(',')
      + ' faq=published text ' + (g('node-global-faq').instruction.text === pre.nodes.find((n) => n.id === 'node-global-faq').instruction.text)
      + ' callback/nonret/arb kept=' + !!(g('node-cb-compute') && g('node-nonret-hours') && g('node-arb-branch')) + ' published=' + v.is_published);
  }
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
