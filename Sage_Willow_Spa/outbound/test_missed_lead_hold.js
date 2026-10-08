// Harness for missed_lead_hold.js (the "Decide: Still Missed?" node).
//
//   node outbound/test_missed_lead_hold.js [real-cases.json]
//
// Runs the node body with n8n's $() stubbed. Built-in fixtures cover the rules; a real-cases
// file ([{ name, call, list, expectMissed }], call = the outbound call as Retell sent it,
// list = what /v3/list-calls returned for "Retell: Reached Us Since?") is checked too.
const fs = require('fs');
const path = require('path');

const CODE = fs.readFileSync(path.join(__dirname, 'missed_lead_hold.js'), 'utf8');
const run = (email, call, listItems) => {
  const nodes = {
    'Compose: Post-Call Email': [{ json: email }],
    'Webhook - Retell call_analyzed': [{ json: { body: { event: 'call_analyzed', call } } }],
    'Retell: Reached Us Since?': listItems,
  };
  const $ = (name) => {
    if (!(name in nodes)) throw new Error('unknown node ' + name);
    return { first: () => nodes[name][0], all: () => nodes[name] };
  };
  return new Function('$', CODE)($)[0].json;
};

let failed = 0;
const check = (label, got, want) => {
  const g = JSON.stringify(got), w = JSON.stringify(want);
  if (g === w) console.log('ok    ' + label);
  else { failed++; console.log('FAIL  ' + label + '\n        expected ' + w + '\n        got      ' + g); }
};

const LEAD = '+14155550100';
const T0 = 1791333380556;                       // our callback starts
const EMAIL = { write: false, send: false, missed: true, subject: 'Missed lead: John Doe, please call them back',
                html: '<p>x</p>', text: 'x', to: 'sagewillowspa@gmail.com', cc: 'engineering@aiemply.com', call_id: 'call_out1' };
const outCall = (over) => ({ call_id: 'call_out1', direction: 'outbound', from_number: '+16282862281', to_number: LEAD,
                             start_timestamp: T0, end_timestamp: T0 + 17555, metadata: { source: 'website_form', inbound_call_id: '' }, ...over });
const inb = (id, startOffset, status, over) => ({ call_id: id, direction: 'inbound', from_number: LEAD, to_number: '+16282862281',
  start_timestamp: T0 + startOffset, call_status: 'ended',
  call_analysis: status ? { custom_analysis_data: { resolution_status: status } } : undefined, ...over });
const wrap = (calls) => [{ json: { items: calls, has_more: false } }];

// rang in 3.5 s after our voicemail and booked (call_d18cc6ab, 2026-10-06)
let r = run(EMAIL, outCall(), wrap([inb('call_in1', 21137, 'booking_created')]));
check('booked since -> no e-mail', [r.missed, r.reached_us], [false, 'rang us since: booking_created (call_in1)']);
check('e-mail fields pass through', [r.subject, r.to, r.cc, r.html, r.call_id], [EMAIL.subject, EMAIL.to, EMAIL.cc, EMAIL.html, 'call_out1']);

for (const s of ['booking_canceled', 'booking_rescheduled', 'info_provided', 'callback_flagged']) {
  check(`${s} since -> no e-mail`, run(EMAIL, outCall(), wrap([inb('call_in1', 60000, s)])).missed, false);
}
for (const s of ['abandoned', 'other', 'spam_declined', '']) {
  check(`"${s}" since -> e-mail goes`, run(EMAIL, outCall(), wrap([inb('call_in1', 60000, s || null)])).missed, true);
}
check('nobody rang -> e-mail goes', run(EMAIL, outCall(), wrap([])).missed, true);
check('on a call with Aria right now -> no e-mail',
      run(EMAIL, outCall(), wrap([inb('call_in1', 400000, null, { call_status: 'ongoing' })])).reached_us, 'on a call with us now (call_in1)');
check('a different number booked -> e-mail goes',
      run(EMAIL, outCall(), wrap([inb('call_in1', 60000, 'booking_created', { from_number: '+14155550199' })])).missed, true);
check('booked BEFORE our call (outside the margin) -> e-mail goes',
      run(EMAIL, outCall(), wrap([inb('call_in1', -5 * 60000, 'booking_created')])).missed, true);
check('rang in while ours was ringing (inside the margin) -> no e-mail',
      run(EMAIL, outCall(), wrap([inb('call_in1', -30000, 'booking_created')])).missed, false);
// a missed-call callback: the inbound call that triggered it is not "since", whatever it says
check('the triggering inbound call is ignored',
      run(EMAIL, outCall({ metadata: { source: 'missed_call', inbound_call_id: 'call_trig' } }),
          wrap([inb('call_trig', -60000, 'info_provided')])).missed, true);
check('look-up failed (error item) -> e-mail goes',
      run(EMAIL, outCall(), [{ json: { error: { message: 'timeout' } } }]).missed, true);
check('look-up returned one item per call -> parsed',
      run(EMAIL, outCall(), [{ json: inb('call_in1', 60000, 'booking_created') }]).missed, false);
check('outbound calls in the list are ignored',
      run(EMAIL, outCall(), wrap([inb('call_x', 60000, 'booking_created', { direction: 'outbound' })])).missed, true);
check('dry run stays unsent', run({ ...EMAIL, missed: false }, outCall(), wrap([])).missed, false);

// real cases
const file = process.argv[2];
if (file) {
  for (const c of JSON.parse(fs.readFileSync(file, 'utf8'))) {
    const out = run({ ...EMAIL, call_id: c.call.call_id }, c.call, wrap(c.list));
    check(`real: ${c.name} -> ${c.expectMissed ? 'e-mail' : 'no e-mail'} (${out.reached_us || 'not reached'}, ${out.later_inbound_calls} later inbound)`,
          out.missed, c.expectMissed);
  }
}

console.log(failed ? `\n${failed} FAILED` : '\nall pass');
process.exit(failed ? 1 : 0);
