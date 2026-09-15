// Offline harness for the two code nodes around the AI classifier in the
// post-call callback workflow: "Prepare Call" (facts -> route) and
// "Apply Verdict" (model output + facts -> needsCallback).
//
//   node outbound/test_evaluate.js                 # synthetic cases
//   node outbound/test_evaluate.js calls.json      # + route real Retell call objects
//
// Node bodies are read out of post_call_callback_workflow.json (write it with
// `py _build_post_call_callback_workflow.py --dry-run` first) so the harness
// can never drift from what gets deployed. The model itself is NOT called here
// - its answers are mocked. Nothing touches the network.

const fs = require('fs');
const path = require('path');

const wf = JSON.parse(fs.readFileSync(path.join(__dirname, 'post_call_callback_workflow.json'), 'utf8'));
const code = (name) => wf.nodes.find(n => n.name === name).parameters.jsCode;
const PREPARE = code('Prepare Call');
const VERDICT = code('Apply Verdict');

const INBOUND = 'agent_eceb7448aa1f37e8f436a63a43';

const prepare = (body) => {
  const $input = { first: () => ({ json: { headers: {}, params: {}, query: {}, body } }) };
  return new Function('$input', PREPARE)($input)[0].json;
};
const verdict = (prep, agentItem) => {
  const $input = { first: () => ({ json: agentItem === undefined ? prep : agentItem }) };
  const $ = (name) => {
    if (name !== 'Prepare Call') throw new Error(`unexpected node ref ${name}`);
    return { first: () => ({ json: prep }) };
  };
  return new Function('$input', '$', VERDICT)($input, $)[0].json;
};

const call = (over) => ({
  call_id: 'call_test', agent_id: INBOUND, call_type: 'phone_call', direction: 'inbound',
  from_number: '+12532681856', to_number: '+16282862281', call_status: 'ended',
  start_timestamp: 1_757_600_000_000, end_timestamp: 1_757_600_045_000, duration_ms: 45_000,
  disconnection_reason: 'user_hangup',
  transcript: 'Agent: Hi, this is Aria from Sage and Willow Spa. How can I help you today?\nUser: I want to book a deep tissue massage\nAgent: Sure, which day works for you?',
  transcript_object: [
    { role: 'agent', content: 'Hi, this is Aria from Sage and Willow Spa. How can I help you today?' },
    { role: 'user', content: 'I want to book a deep tissue massage' },
    { role: 'agent', content: 'Sure, which day works for you?' },
  ],
  transcript_with_tool_calls: [
    { role: 'agent', content: 'Hi, this is Aria...' },
    { role: 'tool_call_invocation', tool_call_id: 'tc_1', name: 'get_slots', arguments: '{"serviceName":"Deep Tissue Massage"}' },
    { role: 'tool_call_result', tool_call_id: 'tc_1', content: '{"success":true,"slots":[]}' },
  ],
  ...over,
});

let failed = 0;
const check = (label, got, expected) => {
  const bad = Object.entries(expected).filter(([k, v]) => got[k] !== v);
  if (bad.length) {
    failed++;
    console.log(`FAIL  ${label}`);
    for (const [k, v] of bad) console.log(`        ${k}: expected ${JSON.stringify(v)}, got ${JSON.stringify(got[k])}`);
  } else {
    console.log(`ok    ${label}`);
  }
};

// ---- Prepare Call: routing on facts ---------------------------------------
console.log('Prepare Call');
const P = [
  ['transcript present -> classify', { event: 'call_analyzed', call: call({}) },
    { route: 'classify', caller_turns: 1, tools_invoked: 2 }],
  ['never connected -> callback, no model', { event: 'call_analyzed', call: call({ call_status: 'not_connected', duration_ms: 0, transcript: '', transcript_object: [] }) },
    { route: 'callback', route_reason: 'never connected / nothing said' }],
  ['under 5 s -> callback, no model', { event: 'call_analyzed', call: call({ duration_ms: 3_000 }) },
    { route: 'callback' }],
  ['no transcript at all -> callback', { event: 'call_analyzed', call: call({ transcript: undefined, transcript_object: undefined }) },
    { route: 'callback' }],
  ['platform error -> callback, no model', { event: 'call_analyzed', call: call({ disconnection_reason: 'error_llm_websocket_open' }) },
    { route: 'callback', route_reason: 'platform error (error_llm_websocket_open)' }],
  ['transferred -> skip', { event: 'call_analyzed', call: call({ disconnection_reason: 'call_transfer' }) },
    { route: 'skip', route_reason: 'transferred to the team' }],
  ['scam detected -> skip', { event: 'call_analyzed', call: call({ disconnection_reason: 'scam_detected' }) },
    { route: 'skip' }],
  ['outbound agent -> skip', { event: 'call_analyzed', call: call({ direction: 'outbound', agent_id: 'agent_4ef8160dc71826818c6fd8122b' }) },
    { route: 'skip', route_reason: 'not the inbound agent' }],
  ['web call -> skip', { event: 'call_analyzed', call: call({ call_type: 'web_call', from_number: undefined }) },
    { route: 'skip' }],
  ['call_ended event -> skip', { event: 'call_ended', call: call({}) },
    { route: 'skip', route_reason: 'event call_ended' }],
  ['anonymous caller -> skip', { event: 'call_analyzed', call: call({ from_number: 'anonymous' }) },
    { route: 'skip', route_reason: 'no usable caller number' }],
  ['spa calling itself -> skip', { event: 'call_analyzed', call: call({ from_number: '+16282862281' }) },
    { route: 'skip', route_reason: 'caller is the spa line' }],
  ['dryRun passes through', { event: 'call_analyzed', dryRun: true, call: call({}) },
    { route: 'classify', dryRun: true }],
  ['text transcript fallback', { event: 'call_analyzed', call: call({ transcript_object: undefined }) },
    { route: 'classify', caller_turns: 1 }],
  ['only the greeting on tape -> callback, no model', { event: 'call_analyzed', call: call({ transcript_object: [{ role: 'agent', content: 'Hi, this is Aria from Sage and Willow Spa.' }], duration_ms: 7_000 }) },
    { route: 'callback', route_reason: 'caller never spoke' }],
];
for (const [label, body, expected] of P) check(label, prepare(body), expected);

// The model prompt must carry the evidence the rules depend on.
const prep = prepare({ event: 'call_analyzed', call: call({}) });
check('llm_input names the tools', { has: prep.llm_input.includes('invoked get_slots') && prep.llm_input.includes('result of get_slots') }, { has: true });
check('llm_input carries the transcript', { has: prep.llm_input.includes('Caller: I want to book a deep tissue massage') }, { has: true });
check('llm_input carries length and ending', { has: /Call length: 45 seconds\. Ended by: user_hangup/.test(prep.llm_input) }, { has: true });

// ---- Apply Verdict: model output + facts ----------------------------------
console.log('\nApply Verdict');
const agentOut = (o) => ({ output: o });
const okModel = { outcome: 'incomplete', needs_callback: true, reason: 'Caller hung up while picking a day.', caller_first_name: 'Dana', caller_wanted: 'booking a deep tissue massage', confidence: 'high' };
const V = [
  ['model says incomplete -> callback', prep, agentOut(okModel),
    { needsCallback: true, first_name: 'Dana', inbound_intent: 'booking a deep tissue massage', outcome: 'incomplete', reason: 'incomplete: Caller hung up while picking a day.' }],
  ['model says booking_made -> no', prep, agentOut({ ...okModel, outcome: 'booking_made', needs_callback: false }),
    { needsCallback: false, skipReason: 'booking_made: Caller hung up while picking a day.' }],
  ['model says question_answered -> no', prep, agentOut({ ...okModel, outcome: 'question_answered', needs_callback: false }),
    { needsCallback: false }],
  ['model says leave_alone -> no', prep, agentOut({ ...okModel, outcome: 'leave_alone', needs_callback: false }),
    { needsCallback: false }],
  ['needs_callback true but outcome not incomplete -> no (belt and braces)', prep, agentOut({ ...okModel, outcome: 'message_taken', needs_callback: true }),
    { needsCallback: false }],
  ['outcome incomplete but needs_callback false -> no', prep, agentOut({ ...okModel, needs_callback: false }),
    { needsCallback: false }],
  ['junk name dropped', prep, agentOut({ ...okModel, caller_first_name: 'Aria' }),
    { needsCallback: true, first_name: '' }],
  ['multi-word name dropped', prep, agentOut({ ...okModel, caller_first_name: 'the caller did not say' }),
    { first_name: '' }],
  ['model failed (error item) -> fail closed', prep, { error: { message: 'Rate limit reached' } },
    { needsCallback: false, skipReason: 'classifier failed: Rate limit reached' }],
  ['model returned nothing -> fail closed', prep, {},
    { needsCallback: false, skipReason: 'classifier failed: no model output' }],
  ['callback route bypasses the model', prepare({ event: 'call_analyzed', call: call({ duration_ms: 0, call_status: 'not_connected', transcript_object: [] }) }), undefined,
    { needsCallback: true, reason: 'never connected / nothing said', inbound_intent: '' }],
  ['skip route bypasses the model', prepare({ event: 'call_analyzed', call: call({ disconnection_reason: 'call_transfer' }) }), undefined,
    { needsCallback: false, skipReason: 'transferred to the team' }],
];
for (const [label, p, item, expected] of V) check(label, verdict(p, item), expected);

console.log(`\n${failed ? 'FAILED ' + failed : 'all passed'}`);

// Optional: route real call objects (as returned by Retell list-calls) - no model.
const replay = process.argv[2];
if (replay) {
  const calls = JSON.parse(fs.readFileSync(replay, 'utf8'));
  console.log(`\nRouting ${calls.length} real calls (model not called):`);
  for (const c of calls) {
    const r = prepare({ event: 'call_analyzed', call: c });
    const secs = Math.round((c.duration_ms ?? (c.end_timestamp - c.start_timestamp)) / 1000);
    console.log(`  ${r.route.padEnd(9)} ${c.call_id}  ${String(secs).padStart(4)}s  turns=${String(r.caller_turns ?? '-').padStart(2)} tools=${String(r.tools_invoked ?? '-').padStart(2)}  ${r.route_reason}`);
  }
}
process.exit(failed ? 1 : 0);
