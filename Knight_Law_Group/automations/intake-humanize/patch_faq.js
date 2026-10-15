// Intake draft v1 (both flows): the FAQ global node answered, then asked "Anything else I should cover?" and stayed
// there until the caller said "No, that's all" (Ubaid's test call call_47c5b8d99aa0855a9f6fa0624f8). Now it answers,
// hands back in a few words, and returns to the pending question as soon as the caller accepts the answer.
//   node patch_faq.js / APPLY=1 node patch_faq.js
const fs = require('fs');
const KEY = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const H = { Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };
const APPLY = process.env.APPLY === '1';
const FLOWS = ['conversation_flow_b4e1b9683eaf', 'conversation_flow_fce8e3f30b49'];
const VER = 1;

const TXT_FROM = 'Only the FIRST time, offer to answer anything else; after that, vary how you check in and keep it light (like "Anything else I can help with?" or "Happy to cover anything else") and do NOT repeat the same "does that help" line every turn. Do NOT ask any qualification or intake questions here; only offer to answer more questions.';
const TXT_TO = 'Don\'t ask "anything else?" and don\'t offer to answer more questions. End your answer with a short, natural hand-back instead, for example "Does that help? Let\'s pick up where we left off." (vary it), so the call keeps moving. Do NOT ask any qualification or intake questions here yourself.';
const GB_FROM = "Return to the qualification flow once the caller has no more questions — they say no, that's all, I'm good, nope, that answers it, thanks, or otherwise signal they're done. Stay in this node only if they ask another general question.";
const GB_TO = "Return to the qualification flow as soon as the caller accepts the answer or agrees to go on — okay, got it, makes sense, sure, yes, no more questions, thanks — or says anything that isn't another general question. Stay in this node only if they ask another general question.";

(async () => {
  for (const id of FLOWS) {
    const f = await (await fetch('https://api.retellai.com/get-conversation-flow/' + id + '?version=' + VER, { headers: H })).json();
    if (f.is_published) throw new Error(id + ' v' + VER + ' is published — refusing');
    const n = f.nodes.find((x) => x.id === 'node-global-faq');
    if (n.instruction.text.split(TXT_FROM).length !== 2) throw new Error(id + ': FAQ text anchor not found once');
    const gb = n.global_node_setting.go_back_conditions.filter((g) => g.transition_condition.prompt === GB_FROM);
    if (gb.length !== 1) throw new Error(id + ': go-back anchor not found once');
    n.instruction.text = n.instruction.text.replace(TXT_FROM, () => TXT_TO);
    gb[0].transition_condition.prompt = GB_TO;
    console.log(id + ' v' + VER + ': FAQ node hand-back + go-back reworded');
    if (!APPLY) continue;
    const r = await fetch('https://api.retellai.com/update-conversation-flow/' + id + '?version=' + VER, { method: 'PATCH', headers: H, body: JSON.stringify({ nodes: f.nodes }) });
    if (!r.ok) throw new Error('PATCH ' + r.status + ' ' + (await r.text()).slice(0, 300));
    const v = await (await fetch('https://api.retellai.com/get-conversation-flow/' + id + '?version=' + VER, { headers: H })).json();
    const vn = v.nodes.find((x) => x.id === 'node-global-faq');
    console.log('  verify: text=' + vn.instruction.text.includes(TXT_TO) + ' go-back=' + (vn.global_node_setting.go_back_conditions[0].transition_condition.prompt === GB_TO) + ' nodes=' + v.nodes.length + ' published=' + v.is_published);
  }
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
