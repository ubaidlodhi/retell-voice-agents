// Intake DRAFT v1 (both flows + both agents), from Ubaid's draft test call call_ae39414d2242b47385710cce38a:
//   - FAQ: every answer ends with a varied check-in ("Does that help?"); fee answers state the fixed fact (the KB also
//     holds a "contingency" FAQ, and on a follow-up Alice invented "usually from the recovery").
//   - Voice speed the same in every node: drop the 0.85 override on the two contact-collection nodes.
//   - Model gpt-5.5 without the fast tier (high_priority false).
//   - Agent: interruption sensitivity 0.8; response wait time 0.7 s.
//     The dashboard shows responsiveness as "Response wait time" in seconds; 0.8 shows as 1.5 s and 1.0 as 0.4 s, i.e.
//     wait = 0.4 + (1 - responsiveness) * 5.5, so 0.7 s = responsiveness 0.95 (the value the dashboard itself stores for 0.7 s on the inbound agent).
//   - TESTING ONLY: the retainer hand-off nodes point at the retainer DRAFT (v4) so test calls hear its fixes.
//     Set them back to "latest_published" before (or together with) publishing — see RESTORE=1.
//   node patch_settings_faq.js / APPLY=1 node patch_settings_faq.js / RESTORE=1 APPLY=1 node patch_settings_faq.js
const fs = require('fs');
const KEY = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const H = { Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };
const API = 'https://api.retellai.com';
const APPLY = process.env.APPLY === '1';
const RESTORE = process.env.RESTORE === '1';
const VER = 1;
const RETAINER_DRAFT = 4;
const T = [
  { flow: 'conversation_flow_b4e1b9683eaf', agent: 'agent_de01f772a9de26ecf4387115a9', swaps: ['node-ret-swap'] },
  { flow: 'conversation_flow_fce8e3f30b49', agent: 'agent_22874d74b1dd6b9d6d72aa4c67', swaps: ['node-inb-qual-swap', 'node-inb-ret-swap'] },
];
const MODEL = { type: 'cascading', model: 'gpt-5.5', high_priority: false };
const AGENT = { interruption_sensitivity: 0.8, responsiveness: 0.95 };

const FAQ_FROM = 'Only the FIRST time, offer to answer anything else; after that, vary how you check in and keep it light (like "Anything else I can help with?" or "Happy to cover anything else") and do NOT repeat the same "does that help" line every turn. Do NOT ask any qualification or intake questions here; only offer to answer more questions.';
const FAQ_TO = 'End EVERY answer with a short check-in question, worded differently each time (for example "Does that help?", "Did that answer it?", "Anything else you\'d like to know?"). Do NOT ask any qualification or intake questions here.';
const FEE_ANCHOR = 'Answer the caller\'s question helpfully in two to three short sentences from the Knowledge Base, in the caller\'s language.';
const FEE_TO = FEE_ANCHOR + ' On cost or fees, the fact is: the manufacturer pays our attorney\'s fees and costs under the California Lemon Law, so the caller never pays us or gets a bill from us. Never say our fees come out of their recovery; only money recovered above the buyback ("additional damages") is split 50/50, and mention that only if they ask about a split or percentage.';
const GB_FROM = "Return to the qualification flow once the caller has no more questions — they say no, that's all, I'm good, nope, that answers it, thanks, or otherwise signal they're done. Stay in this node only if they ask another general question.";
const GB_TO = "Return to the qualification flow once the caller has no more questions — they say no, that's all, I'm good, nope, that answers it, yes that helps, thanks, or otherwise signal they're done. Stay in this node only if they ask another general question.";

function once(s, from, to, label) {
  const n = s.split(from).length - 1;
  if (n !== 1) throw new Error(label + ': anchor found ' + n + ' times');
  return s.replace(from, () => to);
}

(async () => {
  const req = async (method, p, body) => {
    const r = await fetch(API + p, { method, headers: H, body: body ? JSON.stringify(body) : undefined });
    const t = await r.text();
    if (!r.ok) throw new Error(method + ' ' + p + ' ' + r.status + ' ' + t.slice(0, 400));
    return t ? JSON.parse(t) : {};
  };
  for (const t of T) {
    const f = await req('GET', '/get-conversation-flow/' + t.flow + '?version=' + VER);
    const a = await req('GET', '/get-agent/' + t.agent + '?version=' + VER);
    if (f.is_published || a.is_published) throw new Error(t.flow + ': v' + VER + ' is published — refusing');
    const log = [];
    if (RESTORE) {
      for (const id of t.swaps) { f.nodes.find((n) => n.id === id).agent_version = 'latest_published'; }
      log.push('hand-off nodes -> latest_published (publish-ready)');
    } else {
      const faq = f.nodes.find((n) => n.id === 'node-global-faq');
      faq.instruction.text = once(once(faq.instruction.text, FAQ_FROM, FAQ_TO, 'faq check-in'), FEE_ANCHOR, FEE_TO, 'faq fee fact');
      const gb = faq.global_node_setting.go_back_conditions.filter((g) => g.transition_condition.prompt === GB_FROM);
      if (gb.length !== 1) throw new Error('faq go-back anchor');
      gb[0].transition_condition.prompt = GB_TO;
      log.push('FAQ: varied check-in after every answer + fee fact');
      for (const n of f.nodes) if (n.voice_speed !== undefined && n.voice_speed !== null) { log.push(n.id + ': voice_speed ' + n.voice_speed + ' -> agent default'); delete n.voice_speed; }
      for (const id of t.swaps) { const n = f.nodes.find((x) => x.id === id); log.push(id + ': agent_version ' + n.agent_version + ' -> ' + RETAINER_DRAFT + ' (TESTING ONLY)'); n.agent_version = RETAINER_DRAFT; }
      log.push('model ' + JSON.stringify(f.model_choice) + ' -> ' + JSON.stringify(MODEL));
      log.push('agent interruption ' + a.interruption_sensitivity + ' -> ' + AGENT.interruption_sensitivity + ', responsiveness ' + a.responsiveness + ' -> ' + AGENT.responsiveness + ' (~0.7 s wait)');
    }
    console.log('\n===== ' + t.flow + ' v' + VER + '\n  ' + log.join('\n  '));
    if (!APPLY) continue;
    await req('PATCH', '/update-conversation-flow/' + t.flow + '?version=' + VER, RESTORE ? { nodes: f.nodes } : { nodes: f.nodes, model_choice: MODEL });
    if (!RESTORE) await req('PATCH', '/update-agent/' + t.agent + '?version=' + VER, AGENT);
    const v = await req('GET', '/get-conversation-flow/' + t.flow + '?version=' + VER);
    const av = await req('GET', '/get-agent/' + t.agent + '?version=' + VER);
    console.log('  verify: model=' + JSON.stringify(v.model_choice) + ' voice_speed overrides=' + v.nodes.filter((n) => n.voice_speed != null).length
      + ' swaps=' + t.swaps.map((id) => v.nodes.find((n) => n.id === id).agent_version).join(',')
      + ' faq check-in=' + v.nodes.find((n) => n.id === 'node-global-faq').instruction.text.includes('End EVERY answer')
      + ' agent=' + av.interruption_sensitivity + '/' + av.responsiveness + ' published=' + v.is_published + '/' + av.is_published);
  }
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
