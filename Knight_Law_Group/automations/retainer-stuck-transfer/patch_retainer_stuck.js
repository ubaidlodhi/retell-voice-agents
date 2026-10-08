// Alice Retainer (Immediate + Outbound): when Alice is "stuck" she offers the intake team and warm-transfers,
// instead of repeating herself and accepting the "no" (Micol, R Rico call_3a8e07a1296677e6eea7b00242d).
// DRAFT ONLY: creates a draft from the latest published version if needed, refuses to touch a published LLM.
//   node patch_retainer_stuck.js          -> dry run, writes out/<agent>_prompt.md for review
//   APPLY=1 node patch_retainer_stuck.js  -> writes the draft
const fs = require('fs');
const path = require('path');
const RK = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const H = { Authorization: 'Bearer ' + RK, 'Content-Type': 'application/json' };
const API = 'https://api.retellai.com';
const AGENTS = ['agent_7540b5be1e12d28fe1e937a832', 'agent_83f8b296e4652030d15a3417e6']; // Immediate, Outbound
const APPLY = process.env.APPLY === '1';

const req = async (method, p, body) => {
  const r = await fetch(API + p, { method, headers: H, body: body ? JSON.stringify(body) : undefined });
  const t = await r.text();
  if (!r.ok) throw new Error(method + ' ' + p + ' ' + r.status + ' ' + t.slice(0, 300));
  return t ? JSON.parse(t) : {};
};

const STUCK = `
# When you're stuck — offer the intake team

You decide on your own when a person on the intake team will do better than you. You are stuck when ANY of these is true:
- The caller asks the same question again after you already answered it (for example "but how much will I get?" a second time). A repeated question means your answer did not land. Never give the same answer a third time.
- They want something you cannot give: a guaranteed or specific dollar amount for their case, a promise about the outcome or timing, details of their own case (their buyback amount, their repair history), or a change to the agreement.
- They say they will not sign unless they get something you cannot provide ("if you can't guarantee it, then we can't do this").
- Two objections in a row are still unresolved.
- They are frustrated with you, say you are not listening, or the conversation is going in circles.
- They are about to end the call without signing, for a reason you could not resolve.

When you are stuck, do NOT repeat your answer and do NOT accept the "no" yet. Offer the intake team once, in one short turn:
> "That's a fair question, and I'd rather you get a real answer than hear me repeat myself. Let me connect you with someone on our intake team who can go over your specific situation. Is that okay?"
> Spanish: "Es una pregunta muy válida, y prefiero que reciba una respuesta real en vez de escucharme repetir lo mismo. Permítame comunicarle con alguien de nuestro equipo de admisión que puede revisar su situación específica. ¿Le parece bien?"

- They say yes / okay / sure → say "One moment." and call the warm-transfer tool for their language (\`warm_transfer_english\` / \`warm_transfer_spanish\`) in that same turn.
- They say no → respect it. If they are open to it, use Close Path 2 (lock a specific time); otherwise use the graceful exit.
- The transfer does not connect → "Looks like the team is tied up right now. I'll make sure they get your question." Then Close Path 2 (lock a specific time).
- Offer the intake team at most once per call. A question you can answer the first time is not "stuck" — just answer it.
- Never say or imply that the intake team can guarantee an amount or outcome.
`;

const EDITS = [
  {
    name: 'graceful exit offers intake first',
    from: "- **Graceful exit.** If they say they don't want to proceed and confirm it once after a single value restatement, accept gracefully and end. Never badger.",
    to: "- **Graceful exit.** If they say they don't want to proceed for a reason you could not resolve, first offer the intake team once (see \"When you're stuck\"). If they decline that, or they confirm the no after a single value restatement, accept gracefully and end. Never badger.",
  },
  {
    name: 'Close Path 3 includes stuck',
    from: '**Close Path 3 — Warm transfer to intake.** Use for hard objections, legal questions beyond this script, competitor comparisons they want to dig into, disputes, or two unresolved objections.',
    to: "**Close Path 3 — Warm transfer to intake.** Use for hard objections, legal questions beyond this script, competitor comparisons they want to dig into, disputes, two unresolved objections, or whenever you're stuck (see \"When you're stuck\").",
  },
  {
    name: 'Close Path 3 names the real tools',
    from: '- Use the `warm_transfer` tool.',
    to: "- Use the warm-transfer tool for the caller's language (`warm_transfer_english` / `warm_transfer_spanish`).",
    optional: true,
  },
  {
    name: 'Escalation names the real tools',
    from: 'Use `warm_transfer` immediately for:',
    to: "Use the warm-transfer tool for the caller's language (`warm_transfer_english` / `warm_transfer_spanish`) immediately for:",
    optional: true,
  },
  {
    name: 'Tools: transfer when stuck',
    from: 'Call for Close Path 3, any warm-transfer-now trigger, or after two unresolved objections.',
    to: "Call for Close Path 3, any warm-transfer-now trigger, after two unresolved objections, or when you're stuck and the caller agreed to be connected.",
  },
  {
    name: 'Tools: end_call only after intake offer',
    from: 'they clearly declined and reconfirmed after one restatement',
    to: 'they clearly declined and reconfirmed after one restatement (and, if their reason was something you could not resolve, also declined your offer of the intake team)',
  },
  {
    name: 'stuck section before Escalation',
    from: '\n# Escalation — warm-transfer now',
    to: STUCK + '\n# Escalation — warm-transfer now',
  },
];

const END_CALL_FROM = '"Not interested" for the SECOND time, after your one genuine attempt.';
const END_CALL_TO = '"Not interested" for the SECOND time, after your one genuine attempt and, if their reason was something you could not resolve, after they declined your offer to connect them with the intake team.';

function patchPrompt(p) {
  if (p.includes("# When you're stuck")) throw new Error('already patched');
  for (const e of EDITS) {
    const n = p.split(e.from).length - 1;
    if (n === 0 && e.optional) continue;
    if (n !== 1) throw new Error('edit "' + e.name + '" anchor found ' + n + ' times');
    p = p.replace(e.from, () => e.to);
  }
  return p;
}

(async () => {
  fs.mkdirSync(path.join(__dirname, 'out'), { recursive: true });
  for (const id of AGENTS) {
    let vers = await req('GET', '/list-agent-versions/' + id);
    vers = Array.isArray(vers) ? vers : vers.items || [];
    const latest = vers.reduce((a, v) => (v.version > a.version ? v : a));
    let draftVer = latest.is_published ? null : latest.version;
    if (draftVer === null && APPLY) {
      const created = await req('POST', '/create-agent-version/' + id, { base_version: latest.version });
      draftVer = created.version;
      console.log(id + ': created draft v' + draftVer + ' from published v' + latest.version);
    }
    const baseVer = draftVer === null ? latest.version : draftVer;
    const agent = await req('GET', '/get-agent/' + id + '?version=' + baseVer);
    const llmId = agent.response_engine.llm_id;
    const llmVer = agent.response_engine.version;
    const llm = await req('GET', '/get-retell-llm/' + llmId + '?version=' + llmVer);
    const prompt = patchPrompt(llm.general_prompt);
    const tools = llm.general_tools.map((t) => {
      if (t.name !== 'end_call') return t;
      if (t.description.split(END_CALL_FROM).length !== 2) throw new Error('end_call anchor not found once');
      return { ...t, description: t.description.replace(END_CALL_FROM, () => END_CALL_TO) };
    });
    fs.writeFileSync(path.join(__dirname, 'out', agent.agent_name.replace(/[^\w]+/g, '_') + '_prompt.md'), prompt);
    console.log(agent.agent_name + ' | agent v' + baseVer + ' published=' + agent.is_published + ' | llm v' + llmVer + ' published=' + llm.is_published + ' | prompt ' + llm.general_prompt.length + ' -> ' + prompt.length);
    if (!APPLY) continue;
    if (agent.is_published || llm.is_published) throw new Error(id + ': refusing to edit a published version');
    await req('PATCH', '/update-retell-llm/' + llmId + '?version=' + llmVer, { general_prompt: prompt, general_tools: tools });
    const check = await req('GET', '/get-retell-llm/' + llmId + '?version=' + llmVer);
    const pub = await req('GET', '/get-retell-llm/' + llmId + '?version=' + latest.version);
    console.log('  verify draft: stuck section=' + check.general_prompt.includes("# When you're stuck") + ' matches=' + (check.general_prompt === prompt) + ' end_call updated=' + check.general_tools.find((t) => t.name === 'end_call').description.includes('intake team') + ' | published v' + latest.version + ' untouched=' + !pub.general_prompt.includes("# When you're stuck"));
  }
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
