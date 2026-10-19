// Retainer Immediate + Retainer Outbound: new DRAFT v5 from published v4, with one Close Path 1 fix.
// Sim batch 2026-10-19 (draft-tests/out/sim/T1.txt): after the walkthrough the lead said "I think I'm all set... Goodbye"
// without ever saying they signed, and Alice used the signed close ("Thanks for getting that done..."). Cause: Close
// Path 1 allows that close when the lead "clearly says they need to go". Fix: ask once when it's unclear whether they
// signed; a lead leaving unsigned goes to Close Path 2 (lock a time); the signed close only after they confirm submit.
// Also points the intake drafts' hand-off node at the Immediate v5 draft so intake test calls reach the fix
// (RESTORE=1 APPLY=1 node ../intake-humanize/patch_settings_faq.js still resets it to latest_published before publish).
//   node patch_retainer_v5_close.js / APPLY=1 node patch_retainer_v5_close.js
const fs = require('fs');
const path = require('path');
const KEY = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const H = { Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };
const APPLY = process.env.APPLY === '1';
const BASE_VER = 4;
const AGENTS = { immediate: 'agent_7540b5be1e12d28fe1e937a832', outbound: 'agent_83f8b296e4652030d15a3417e6' };
const INTAKE_FLOWS = ['conversation_flow_b4e1b9683eaf', 'conversation_flow_fce8e3f30b49'];
const OUT = path.join(__dirname, 'out');

const FROM = 'Wait until they confirm they have hit submit (or clearly say they need to go). Then close warmly WITHOUT confirming receipt';
const TO = 'Wait until they confirm they have hit submit. If it is unclear whether they actually signed (for example "I think I\'m all set" or "okay, I looked at it"), ask once: "Did you get a chance to hit submit?" Never assume a signature. If they need to go before signing, do not thank them for signing; go to Close Path 2 and lock a time. Once they confirm they submitted, close warmly WITHOUT confirming receipt';

const api = async (method, p, body) => {
  const r = await fetch('https://api.retellai.com' + p, { method, headers: H, body: body ? JSON.stringify(body) : undefined });
  const t = await r.text();
  if (!r.ok) throw new Error(method + ' ' + p + ' -> ' + r.status + ' ' + t.slice(0, 400));
  return t ? JSON.parse(t) : {};
};

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  let immediateVer = null;
  for (const [label, id] of Object.entries(AGENTS)) {
    const base = await api('GET', '/get-agent/' + id + '?version=' + BASE_VER);
    if (!base.is_published) throw new Error(label + ' v' + BASE_VER + ' is not the published base');
    const baseLlm = await api('GET', '/get-retell-llm/' + base.response_engine.llm_id + '?version=' + base.response_engine.version);
    const hits = baseLlm.general_prompt.split(FROM).length - 1;
    if (hits !== 1) throw new Error(label + ': close anchor found ' + hits + 'x');
    fs.writeFileSync(path.join(OUT, 'backup_retainer_' + label + '_v' + BASE_VER + '_prompt.txt'), baseLlm.general_prompt);
    console.log(label + ': base v' + BASE_VER + ' llm ' + base.response_engine.llm_id + ' v' + base.response_engine.version + ', anchor ok' + (APPLY ? '' : ' [dry run]'));
    if (!APPLY) continue;
    const draft = await api('POST', '/create-agent-version/' + id, { base_version: BASE_VER });
    const ver = draft.version;
    const llmVer = draft.response_engine.version;
    if (draft.is_published || ver === BASE_VER) throw new Error(label + ': unexpected draft ' + JSON.stringify({ ver, pub: draft.is_published }));
    if (llmVer === base.response_engine.version) throw new Error(label + ': draft still points at the published llm v' + llmVer + ' — refusing to edit it');
    const llm = await api('GET', '/get-retell-llm/' + draft.response_engine.llm_id + '?version=' + llmVer);
    if (llm.general_prompt.split(FROM).length - 1 !== 1) throw new Error(label + ': anchor missing in draft llm');
    await api('PATCH', '/update-retell-llm/' + draft.response_engine.llm_id + '?version=' + llmVer, { general_prompt: llm.general_prompt.replace(FROM, TO) });
    const check = await api('GET', '/get-retell-llm/' + draft.response_engine.llm_id + '?version=' + llmVer);
    const pubLlm = await api('GET', '/get-retell-llm/' + base.response_engine.llm_id + '?version=' + base.response_engine.version);
    console.log('  draft agent v' + ver + ' (published=' + draft.is_published + ') llm v' + llmVer + ': fix=' + check.general_prompt.includes(TO)
      + ' len ' + llm.general_prompt.length + '->' + check.general_prompt.length + ' | published v' + BASE_VER + ' untouched=' + pubLlm.general_prompt.includes(FROM));
    if (label === 'immediate') immediateVer = ver;
  }
  if (!APPLY) return;
  for (const fid of INTAKE_FLOWS) {
    const f = await api('GET', '/get-conversation-flow/' + fid + '?version=1');
    if (f.is_published) throw new Error(fid + ' v1 is published — refusing');
    const swaps = f.nodes.filter((n) => n.type === 'agent_swap' && n.agent_id === AGENTS.immediate);
    for (const n of swaps) n.agent_version = immediateVer;
    await api('PATCH', '/update-conversation-flow/' + fid + '?version=1', { nodes: f.nodes });
    const v = await api('GET', '/get-conversation-flow/' + fid + '?version=1');
    console.log(fid + ' v1: hand-off nodes -> Immediate v' + v.nodes.filter((n) => n.type === 'agent_swap' && n.agent_id === AGENTS.immediate).map((n) => n.agent_version).join(','));
  }
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
