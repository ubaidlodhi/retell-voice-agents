// Alice Closer (Retainer Immediate + Retainer Outbound): "Alice — Workshop Change Spec (Oct 1, 2026)", items #5-#9.
// New DRAFT v6 from live v5 on both agents. Nothing is published here. Silence settings for #7 (reminder 120 s x1,
// end after ~300 s) wait for Ubaid's OK and are NOT changed by this script.
//   #5 Buyback: approved definition with the mileage deduction as a trailing clause; no negative framing; the
//      5,000 vs 15,000 miles comparison only if pressed. Objection C rewritten the same way.
//   #6 50/50 split: approved plain line once, no justification, "we fight hard" only when challenged; no worked
//      example in the walkthrough (only if they ask for one).
//   #7 Reading: "Of course, take your time, I'll wait.", silence, ONE check-in, no filler.
//   #8 Closing in two steps: farewell, let the caller answer, end on the next turn; never while they talk.
//   #9 Plain spoken English rule; "actual damages section" line replaced.
//   node patch_retainer_workshop.js / APPLY=1 node patch_retainer_workshop.js
const fs = require('fs');
const path = require('path');
const KEY = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const H = { Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };
const APPLY = process.env.APPLY === '1';
const BASE = 5;
const OUT = path.join(__dirname, 'out');
const AGENTS = { immediate: 'agent_7540b5be1e12d28fe1e937a832', outbound: 'agent_83f8b296e4652030d15a3417e6' };

const BUYBACK = '**The buyback.** Explain it in this approved wording (delivery can flex, the facts cannot): "A buyback is where the manufacturer takes the vehicle back and refunds the money you paid toward it, your down payment, monthly payments, tax, interest, and registration if it\'s on the face of the sales contract, minus a mileage deduction based on the miles you drove before the problems first emerged. They convert those miles into dollars using a formula in the Lemon Law, and that comes off your refund." The mileage deduction is always part of this one definition, never a separate point. Never frame it negatively: never say "you won\'t get 100% back", "the buyback isn\'t all your money", or anything like it. If they push back on the deduction, use the comparison instead: "Someone who drove five thousand miles gets a bigger refund than someone who drove fifteen thousand." Background facts, only if asked: the deduction is fixed (it does not grow while the case is pending) and it applies to every buyback, whichever firm handles the case.\n\n';
const SPLIT = '**Additional damages — the 50/50 split.** State it once, as plain fact, then move on: "If we recover additional damages, meaning money above and beyond your refund, that amount is split fifty-fifty between you and the firm." Do NOT explain or justify why the firm takes half unless the caller challenges it. Only if they challenge it ("why do you take half?"), say: "Unlike most firms, we\'re typically able to obtain additional damages for you above and beyond your refund. Because we fight hard, we\'re often able to get the manufacturer to pay more than the refund alone, and when we\'re able to add that value to your case, we take a portion of those additional damages." If they ask for an example of how the numbers work, you may give one, always "for the sake of argument": a fifty-thousand refund and a hundred-thousand settlement, the first fifty is all theirs and the extra fifty is split, so seventy-five thousand to them.\n\n';
const WALK = '1. **The buyback** — the approved buyback definition above, with the mileage deduction inside it as the trailing clause.\n2. **Manufacturer-paid fees** — the manufacturer pays the firm\'s fees; they never get a bill from us.\n3. **The split on additional damages** — the approved line, once, as plain fact. No worked example and no justification here.\n';
const OBJ_B = 'If they ask about the 50%:\n> "That only applies to additional damages, meaning money above and beyond your refund, and that amount is split fifty-fifty between you and the firm. Your refund itself isn\'t split."\n\nIf they challenge why the firm takes half, use the approved "we fight hard" answer from the facts above, once.\n\n';
const OBJ_C = '**C — Mileage deduction ("Why is there a deduction?" / "Why don\'t I get everything back?").** Never answer with a negative. Restate the mechanics and use the comparison.\n> "That deduction is set by the Lemon Law itself, and it\'s based only on the miles you drove before the problems first showed up. They convert those miles into dollars with a formula, so it\'s a fixed amount. Someone who drove five thousand miles gets a bigger refund than someone who drove fifteen thousand."\n\n';
const READING = '- When they say they are opening it, reading it, or need a moment (for example "I\'m opening it", "give me a minute", "let me read it", "hold on"), say exactly: "Of course, take your time, I\'ll wait." Then stay completely silent and let them read or sign.\n- If they only murmur a tiny filler while reading - a bare "okay," "mhm," "one sec," "alright" - with nothing to answer, do not talk over them; reply with exactly this, in all caps and nothing else: NO_RESPONSE_NEEDED\n- Never fill the silence: no "I\'m still here", no "still with you", no "no rush". The ONLY check-in allowed is ONE, after a long silence (at least two minutes): "Just checking in, I\'m here whenever you\'re ready if anything comes up." After that one check-in, stay silent again; never check in a second time and never stack lines.\n';
const CLOSE = '- **Close in two steps, never mid-sentence.** (1) Say your farewell out loud as part of your reply ("Thanks for your time today — take care."), then STOP and let the caller answer. (2) Call end_call only on your NEXT turn: after the caller has answered your farewell ("bye", "thanks", "you too") say a brief "Bye now!" and call it, or call it when the silence timeout comes. Never call end_call in the same turn as a farewell the caller has not answered yet, never while they are still talking, and if their reply is a new question, answer it instead of ending. Your farewell must be a real goodbye, never a purely business sentence ("...moving to the manufacturer.") that would land as an abrupt hang-up. The end_call tool\'s own message field is NOT spoken to the caller, so a goodbye placed there is never heard.\n- **Plain spoken English, no legal or internal jargon.** Say "refund" (not "actual damages" or "restitution"), "mileage deduction" (not "offset" or "statutory"), and "money above and beyond your refund" whenever you mention additional damages. Never use internal labels. The register to match: "We need to get your case going. The first step is signing the representation agreement. That\'s what makes the attorney-client relationship official and lets us start working."';

const EDITS = [
  { what: '#5 buyback + offset facts', from: '**The buyback (actual damages).**', to: '**How the firm is paid.**', insert: BUYBACK },
  { what: '#6 split facts + worked example', from: '**Additional damages — the 50/50 split.**', to: '**The process.**', insert: SPLIT },
  { what: '#5/#6 walkthrough points', from: '1. **The buyback (actual damages)**', to: 'Then invite questions and move toward signing:', insert: WALK + '\n', optional: true },
  { what: '#6 objection B 50%', from: 'If they ask about the 50%:\n', to: '→ Confirm understanding, then Close Path 1.', insert: OBJ_B },
  { what: '#5 objection C', from: '**C — Mileage offset', to: '→ Close Path 1.', insert: OBJ_C },
  { what: '#7 reading', from: '- When they ask for a moment, say they are looking it over', to: '- Break in immediately with a normal reply', insert: READING },
  { what: '#8/#9 closing + jargon', from: '- **Always sign off out loud before hanging up.**', to: 'so a goodbye placed there is never heard.', insert: CLOSE, dropTo: true },
];
const SIMPLE = [
  ['#9 close path 1 line', 'Take a second with the actual damages section — that\'s your buyback — and I\'m right here', 'Take a second with the part about your refund, and I\'m right here'],
  ['#8 end_call guidance', 'Always speak your closing line in the same turn; never hang up silently.', 'Close in two steps (see Voice & delivery): farewell first, let them answer, then end on your next turn; never hang up silently and never while they are talking.'],
  ['walkthrough count (title)', 'all four points in ONE continuous turn', 'all three points in ONE continuous turn', true],
  ['walkthrough count (body)', 'deliver ALL FOUR points below', 'deliver ALL THREE points below', true],
  ['walkthrough count (list)', 'Walk these four points in order', 'Walk these three points in order', true],
  ['walkthrough count (rule)', 'where all four points are delivered proactively', 'where all three points are delivered proactively', true],
  ['re-explain rule', 'the 50% split, the worked example, or the mileage offset a second time', 'the 50% split or the mileage deduction a second time', true],
];
// optional = only the Immediate agent has the four-point walkthrough; Outbound (follow-up calls) has none.
const TOOL_FROM = 'ALWAYS speak a closing line out loud in the SAME turn right before calling this — never hang up silently.';
const TOOL_TO = 'Call it only on the turn AFTER your farewell was answered (or met silence), with a brief "Bye now!". Never while the caller talks.';

function patchPrompt(p, label) {
  let out = p;
  for (const e of EDITS) {
    const a = out.indexOf(e.from);
    if (a < 0 && e.optional) continue;
    if (a < 0 || out.indexOf(e.from, a + 1) >= 0) throw new Error(label + ' ' + e.what + ': start anchor count');
    const b = out.indexOf(e.to, a + e.from.length);
    if (b < 0) throw new Error(label + ' ' + e.what + ': end anchor');
    out = out.slice(0, a) + e.insert + out.slice(e.dropTo ? b + e.to.length : b);
  }
  for (const [what, a, b, optional] of SIMPLE) {
    const n = out.split(a).length - 1;
    if (n === 0 && optional) continue;
    if (n !== 1) throw new Error(label + ' ' + what + ': found ' + n + 'x');
    out = out.replace(a, b);
  }
  return out;
}

const api = async (method, p, body) => {
  const r = await fetch('https://api.retellai.com' + p, { method, headers: H, body: body ? JSON.stringify(body) : undefined });
  const t = await r.text();
  if (!r.ok) throw new Error(method + ' ' + p + ' -> ' + r.status + ' ' + t.slice(0, 400));
  return t ? JSON.parse(t) : {};
};

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  for (const [label, id] of Object.entries(AGENTS)) {
    const live = await api('GET', '/get-agent/' + id + '?version=' + BASE);
    if (!live.is_published) throw new Error(label + ' v' + BASE + ' is not live');
    const l = await api('GET', '/get-retell-llm/' + live.response_engine.llm_id + '?version=' + live.response_engine.version);
    const np = patchPrompt(l.general_prompt, label);
    const ec = l.general_tools.find((t) => t.type === 'end_call');
    if (!ec || ec.description.split(TOOL_FROM).length !== 2) throw new Error(label + ': end_call description anchor');
    const left = ['actual damages section', 'more than 100% of the money', 'small piece of a much bigger picture', 'Still with you whenever', 'If the silence runs about 10 to 15 seconds'].filter((x) => np.includes(x));
    console.log(label + ': prompt ' + l.general_prompt.length + ' -> ' + np.length + ' chars; leftovers: ' + (left.join(' | ') || 'none') + (APPLY ? '' : ' [dry run]'));
    if (!APPLY) { fs.writeFileSync(path.join(OUT, 'preview_retainer_' + label + '_v6.txt'), np); continue; }
    const newTool = ec.description.replace(TOOL_FROM, TOOL_TO);
    if (newTool.length > 1024) throw new Error(label + ': end_call description ' + newTool.length + ' chars (max 1024)');
    // Reuse an unpublished v(BASE+1) left by an earlier failed run instead of creating another version.
    const existing = await api('GET', '/get-agent/' + id + '?version=' + (BASE + 1)).catch(() => null);
    const d = existing && existing.version === BASE + 1 && !existing.is_published ? existing : await api('POST', '/create-agent-version/' + id, { base_version: BASE });
    const lv = d.response_engine.version;
    if (d.is_published || lv === live.response_engine.version) throw new Error(label + ': bad draft');
    const dl = await api('GET', '/get-retell-llm/' + d.response_engine.llm_id + '?version=' + lv);
    fs.writeFileSync(path.join(OUT, 'backup_retainer_' + label + '_v' + BASE + '_prompt.txt'), dl.general_prompt);
    const tools = dl.general_tools.map((t) => (t.type === 'end_call' ? { ...t, description: t.description.replace(TOOL_FROM, TOOL_TO) } : t));
    await api('PATCH', '/update-retell-llm/' + d.response_engine.llm_id + '?version=' + lv, { general_prompt: patchPrompt(dl.general_prompt, label), general_tools: tools });
    const v = await api('GET', '/get-retell-llm/' + d.response_engine.llm_id + '?version=' + lv);
    console.log('  DRAFT agent v' + d.version + ' llm v' + lv + ' (published=' + d.is_published + '): buyback=' + v.general_prompt.includes('A buyback is where the manufacturer') + ' split=' + v.general_prompt.includes('Because we fight hard') + ' reading=' + v.general_prompt.includes("I'll wait.") + ' close=' + v.general_prompt.includes('Close in two steps') + ' tool=' + v.general_tools.find((t) => t.type === 'end_call').description.includes('turn AFTER'));
  }
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
