// Two fixes from the full-flow suite (draft-tests/out/sim/suite-test_batch_cbc9e02a3817):
//   A. Intake DRAFT v1 (both flows): after an FAQ the caller said "No, that's all. And yes, it's my truck." The FAQ
//      go-back re-entered the owner node, which had nothing left to ask and said only "Got it — you're the owner."
//      (no question = dead air). Fix: `skippable` (use memory to skip) on the single-answer question nodes the FAQ can
//      return to. Only nodes whose every edge needs a real answer: a node with a catch-all edge (q-ca: "whenever
//      California has not been clearly confirmed"; confirm-vehicle: "or does not dispute them") would skip on entry.
//   B. Retainer Immediate + Outbound DRAFT v5: end_call had speak_during_execution=true with a prompt-type message, while
//      the prompt says that field is never heard, so internal notes were spoken on live calls
//      (call_b82e35f4488aa… 2026-10-18: "Caller says already signed; ending after spoken thanks."). Fix: speak_during_execution=false;
//      the prompt already makes Alice say the goodbye herself before calling end_call.
//   node patch_skip_and_endcall.js / APPLY=1 node patch_skip_and_endcall.js
const fs = require('fs');
const KEY = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const H = { Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };
const APPLY = process.env.APPLY === '1';
const FLOWS = ['conversation_flow_b4e1b9683eaf', 'conversation_flow_fce8e3f30b49'];
const SKIP_NODES = ['node-ret-owner', 'node-q-possession', 'node-ret-cpo'];
const RETAINER = { immediate: 'agent_7540b5be1e12d28fe1e937a832', outbound: 'agent_83f8b296e4652030d15a3417e6' };
const DRAFT_VER = 5;

const api = async (method, p, body) => {
  const r = await fetch('https://api.retellai.com' + p, { method, headers: H, body: body ? JSON.stringify(body) : undefined });
  const t = await r.text();
  if (!r.ok) throw new Error(method + ' ' + p + ' -> ' + r.status + ' ' + t.slice(0, 400));
  return t ? JSON.parse(t) : {};
};

(async () => {
  for (const id of FLOWS) {
    const f = await api('GET', '/get-conversation-flow/' + id + '?version=1');
    if (f.is_published) throw new Error(id + ' v1 is published — refusing');
    for (const nid of SKIP_NODES) {
      const n = f.nodes.find((x) => x.id === nid);
      if (!n || n.type !== 'conversation') throw new Error(id + ': ' + nid + ' missing / not conversation');
      n.skippable = true;
    }
    console.log(id + ' v1: skippable on ' + SKIP_NODES.join(', ') + (APPLY ? '' : ' [dry run]'));
    if (!APPLY) continue;
    await api('PATCH', '/update-conversation-flow/' + id + '?version=1', { nodes: f.nodes });
    const v = await api('GET', '/get-conversation-flow/' + id + '?version=1');
    console.log('  verify: ' + SKIP_NODES.map((x) => x + '=' + v.nodes.find((n) => n.id === x).skippable).join(' ') + ' published=' + v.is_published);
  }
  for (const [label, aid] of Object.entries(RETAINER)) {
    const a = await api('GET', '/get-agent/' + aid + '?version=' + DRAFT_VER);
    if (a.is_published) throw new Error(label + ' v' + DRAFT_VER + ' is published — refusing');
    const { llm_id: llm, version: lv } = a.response_engine;
    const l = await api('GET', '/get-retell-llm/' + llm + '?version=' + lv);
    const tools = l.general_tools.map((t) => (t.type === 'end_call' ? { ...t, speak_during_execution: false } : t));
    if (tools.filter((t) => t.type === 'end_call').length !== 1) throw new Error(label + ': expected one end_call tool');
    console.log(label + ' v' + DRAFT_VER + ' (llm ' + llm + ' v' + lv + '): end_call speak_during_execution ' + l.general_tools.find((t) => t.type === 'end_call').speak_during_execution + ' -> false' + (APPLY ? '' : ' [dry run]'));
    if (!APPLY) continue;
    await api('PATCH', '/update-retell-llm/' + llm + '?version=' + lv, { general_tools: tools });
    const v = await api('GET', '/get-retell-llm/' + llm + '?version=' + lv);
    const pub = await api('GET', '/get-retell-llm/' + llm + '?version=4');
    console.log('  verify: draft end_call speak=' + v.general_tools.find((t) => t.type === 'end_call').speak_during_execution
      + ' tools ' + l.general_tools.length + '->' + v.general_tools.length + ' | published v4 unchanged speak=' + pub.general_tools.find((t) => t.type === 'end_call').speak_during_execution);
  }
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
