// Ubaid 2026-10-20: publish all Knight Law agents on the Cartesia voice (custom_voice_f00a0f2aff75710357d19e8292,
// "Skylar - Friendly Guide", Cartesia id db6b0ed5-d5d3-463d-ae85-518a07d3c2b4). Intake Outbound v1 was already
// published by Ubaid with that voice. Order matters — retainer first, so no intake hand-off ever lands on a draft:
//   1. Retainer Immediate + Retainer Outbound draft v5: voice -> Cartesia, publish.
//   2. Intake Inbound draft v1: hand-off nodes -> "latest_published" (were pinned to retainer draft v5 for testing), voice, publish.
//   3. Intake Outbound draft v2 (copy of published v1): hand-off node -> "latest_published", publish.
// The number +12132053651 is bound to latest_published both ways, so each publish is live immediately.
//   node publish_all_cartesia.js / APPLY=1 node publish_all_cartesia.js
const fs = require('fs');
const KEY = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const H = { Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };
const APPLY = process.env.APPLY === '1';
const VOICE = 'custom_voice_f00a0f2aff75710357d19e8292';
const STEPS = [
  { label: 'Retainer Immediate', agent: 'agent_7540b5be1e12d28fe1e937a832', ver: 5 },
  { label: 'Retainer Outbound', agent: 'agent_83f8b296e4652030d15a3417e6', ver: 5 },
  { label: 'Intake Inbound', agent: 'agent_22874d74b1dd6b9d6d72aa4c67', ver: 1, flow: 'conversation_flow_fce8e3f30b49' },
  { label: 'Intake Outbound', agent: 'agent_de01f772a9de26ecf4387115a9', ver: 2, flow: 'conversation_flow_b4e1b9683eaf' },
];

const api = async (method, p, body) => {
  const r = await fetch('https://api.retellai.com' + p, { method, headers: H, body: body ? JSON.stringify(body) : undefined });
  const t = await r.text();
  if (!r.ok) throw new Error(method + ' ' + p + ' -> ' + r.status + ' ' + t.slice(0, 400));
  return t ? JSON.parse(t) : {};
};

(async () => {
  const voice = await api('GET', '/get-voice/' + VOICE);
  if (voice.provider !== 'cartesia') throw new Error('voice provider is ' + voice.provider);
  for (const s of STEPS) {
    const a = await api('GET', '/get-agent/' + s.agent + '?version=' + s.ver);
    if (a.is_published) throw new Error(s.label + ' v' + s.ver + ' is already published');
    let swaps = [];
    if (s.flow) {
      if (a.response_engine.conversation_flow_id !== s.flow || a.response_engine.version !== (s.ver === 2 ? 2 : 1)) throw new Error(s.label + ': unexpected engine ' + JSON.stringify(a.response_engine));
      const f = await api('GET', '/get-conversation-flow/' + s.flow + '?version=' + a.response_engine.version);
      if (f.is_published) throw new Error(s.label + ': flow version already published');
      swaps = f.nodes.filter((n) => n.type === 'agent_swap');
      if (!swaps.length) throw new Error(s.label + ': no hand-off nodes');
      console.log(s.label + ' v' + s.ver + ': voice ' + a.voice_id + ' -> ' + VOICE + ' | hand-offs ' + swaps.map((n) => n.id + '@' + n.agent_version).join(',') + ' -> latest_published' + (APPLY ? '' : ' [dry run]'));
      if (APPLY) {
        for (const n of swaps) n.agent_version = 'latest_published';
        await api('PATCH', '/update-conversation-flow/' + s.flow + '?version=' + a.response_engine.version, { nodes: f.nodes });
      }
    } else {
      console.log(s.label + ' v' + s.ver + ': voice ' + a.voice_id + ' -> ' + VOICE + (APPLY ? '' : ' [dry run]'));
    }
    if (!APPLY) continue;
    if (a.voice_id !== VOICE) await api('PATCH', '/update-agent/' + s.agent + '?version=' + s.ver, { voice_id: VOICE });
    await api('POST', '/publish-agent-version/' + s.agent, { version: s.ver });
    const p = await api('GET', '/get-agent/' + s.agent + '?version=' + s.ver);
    let extra = '';
    if (s.flow) {
      const f = await api('GET', '/get-conversation-flow/' + s.flow + '?version=' + p.response_engine.version);
      extra = ' flow v' + p.response_engine.version + ' published=' + f.is_published + ' hand-offs=' + f.nodes.filter((n) => n.type === 'agent_swap').map((n) => n.agent_version).join(',');
    }
    console.log('  verify: v' + s.ver + ' published=' + p.is_published + ' voice=' + (p.voice_id === VOICE ? 'cartesia ok' : p.voice_id) + extra);
  }
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
