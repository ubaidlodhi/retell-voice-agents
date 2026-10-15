// Alice Retainer (Immediate + Outbound) DRAFT v4: fixes from Ubaid's test call call_47c5b8d99aa0855a9f6fa0624f8
// ("I have to discuss this with my wife" -> caller said "tonight" four times, Alice kept saying "tomorrow").
// Cause: Branch D and Close Path 2 hard-code "I'll check back tomorrow", and the "…" in the scripts reads as one
// breath, so Alice answered her own question. Also shrinks the "stuck" section added on 2026-10-05 (same rules,
// about half the size) and removes the stale "welcomed them aboard" (contradicts "never confirm a signature").
//   node patch_retainer_close.js          -> dry run, writes out/<agent>_prompt_v4_close.md
//   APPLY=1 node patch_retainer_close.js  -> PATCHes the draft LLM versions (refuses published ones)
const fs = require('fs');
const path = require('path');
const RK = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const H = { Authorization: 'Bearer ' + RK, 'Content-Type': 'application/json' };
const API = 'https://api.retellai.com';
const APPLY = process.env.APPLY === '1';
const TARGETS = [['Immediate', 'llm_3fd5f54719d06cade80d25c16859', 4], ['Outbound', 'llm_4d3a25e444334df5155b2bb9b3ab', 4]];

const D_TO = '> "Of course, that makes sense. If it helps, I\'m happy to hop on a quick call with both of you and walk through it together. When are you two planning to look at it?"';
const CP2_TO = `**Close Path 2 — Lock a follow-up time.** Use only when they genuinely can't sign now. Never end on a vague "sometime this week."
- Ask when they'll have two minutes for it, then stop and wait for the answer.
- Use exactly the day and time THEY give — never turn "tonight" into "tomorrow". If they give only a day or a part of the day, ask once for the time.
- Confirm and close in one turn: "Perfect, I'll call you [their day and time]. If it's signed before then, we'll just get moving on our side." Then your farewell.`;
const STUCK_TO = `# When you're stuck — offer the intake team

You're stuck when the caller asks the same question again after you answered it, wants something you can't give (a guaranteed amount, a promise about outcome or timing, details of their own case, a change to the agreement), won't sign without it, has two unresolved objections, is frustrated or says you're not listening, or is about to hang up unsigned for a reason you couldn't resolve.

Then don't repeat your answer and don't accept the "no" yet. Offer once, in one short turn: "That's a fair question, and I'd rather you get a real answer than hear me repeat myself. Want me to connect you with someone on our intake team who can go over your specific situation?"
- Yes → "One moment." and call the warm-transfer tool for their language in that same turn.
- No → respect it: Close Path 2, or the graceful exit.
- The transfer doesn't connect → "Looks like the team is tied up right now." Then Close Path 2.
At most once per call; a question you can answer the first time isn't "stuck". Never imply the intake team can guarantee an amount or outcome.
`;
const ELLIPSIS_RULE = '- **"…" inside a script means stop there and wait for their answer** before you say the rest. Never answer your own question.\n';

function lineStarting(s, start, label) {
  const lines = s.split('\n').filter((l) => l.startsWith(start));
  if (lines.length !== 1) throw new Error(label + ': expected 1 line starting with ' + JSON.stringify(start.slice(0, 40)) + ', found ' + lines.length);
  return lines[0];
}
function once(s, from, to, label) {
  const n = s.split(from).length - 1;
  if (n !== 1) throw new Error(label + ': anchor found ' + n + ' times');
  return s.replace(from, () => to);
}

function patch(p) {
  if (p.indexOf('Lock a follow-up time') !== -1) throw new Error('already patched');
  // Branch D: the scripted line that ends "I'll check back with you tomorrow either way."
  p = once(p, lineStarting(p, '> "Of course — that makes total sense.', 'Branch D'), D_TO, 'Branch D');
  // Close Path 2: heading + script line + "Lock a specific time before ending."
  const cp2Head = lineStarting(p, '**Close Path 2 — Commitment with a deadline.**', 'CP2 head');
  const cp2Line = lineStarting(p, '> "No problem. When do you think you\'ll have those two minutes', 'CP2 script');
  p = once(p, cp2Head + '\n' + cp2Line + '\n\n- Lock a specific time before ending.', CP2_TO, 'Close Path 2 block');
  // Stuck section: everything from its heading to the next "# " heading
  const a = p.indexOf("# When you're stuck — offer the intake team");
  const b = p.indexOf('\n# ', a + 5);
  if (a === -1 || b === -1) throw new Error('stuck section not found');
  p = p.slice(0, a) + STUCK_TO + p.slice(b);
  // "…" rule, right after "Ask only ONE question per turn"
  p = once(p, lineStarting(p, '- **Ask only ONE question per turn, then stop and wait for the answer.**', 'one-question rule') + '\n',
    lineStarting(p, '- **Ask only ONE question per turn, then stop and wait for the answer.**', 'one-question rule') + '\n' + ELLIPSIS_RULE, 'ellipsis rule');
  p = once(p, "they have submitted their signature and you've welcomed them aboard", "they have submitted their signature and you've thanked them", 'end_call wording');
  if (/check back (with you )?tomorrow/.test(p)) throw new Error('a hard-coded "check back tomorrow" is still in the prompt');
  return p;
}

(async () => {
  const req = async (method, p, body) => {
    const r = await fetch(API + p, { method, headers: H, body: body ? JSON.stringify(body) : undefined });
    const t = await r.text();
    if (!r.ok) throw new Error(method + ' ' + p + ' ' + r.status + ' ' + t.slice(0, 300));
    return t ? JSON.parse(t) : {};
  };
  fs.mkdirSync(path.join(__dirname, 'out'), { recursive: true });
  for (const [label, llmId, ver] of TARGETS) {
    const llm = await req('GET', '/get-retell-llm/' + llmId + '?version=' + ver);
    if (llm.is_published) throw new Error(label + ' llm v' + ver + ' is published — refusing');
    fs.writeFileSync(path.join(__dirname, 'out', label + '_prompt_v' + ver + '_before_close.md'), llm.general_prompt);
    const next = patch(llm.general_prompt);
    fs.writeFileSync(path.join(__dirname, 'out', label + '_prompt_v' + ver + '_close.md'), next);
    console.log(label + ' llm v' + ver + ': prompt ' + llm.general_prompt.length + ' -> ' + next.length + ' chars');
    if (!APPLY) continue;
    await req('PATCH', '/update-retell-llm/' + llmId + '?version=' + ver, { general_prompt: next });
    const v = await req('GET', '/get-retell-llm/' + llmId + '?version=' + ver);
    const pub = await req('GET', '/get-retell-llm/' + llmId + '?version=3');
    console.log('  verify: matches=' + (v.general_prompt === next) + ' published v3 untouched=' + (pub.general_prompt.indexOf('Lock a follow-up time') === -1));
  }
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
