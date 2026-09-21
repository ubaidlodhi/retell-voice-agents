// Harness for post_call_email.js (the "Compose: Post-Call Email" node).
//
//   node outbound/test_post_call_email.js [path-to-real-call.json ...]
//
// Runs the node body with n8n's $input stubbed. Built-in fixtures cover the
// send / skip rules; any real call objects passed on the command line (as saved
// from get-call) are composed too and their HTML written next to this file for
// a look in a browser.
const fs = require('fs');
const path = require('path');

const CODE = fs.readFileSync(path.join(__dirname, 'post_call_email.js'), 'utf8');
const run = (body) => new Function('$input', CODE)({ first: () => ({ json: { body, headers: {}, params: {}, query: {} } }) })[0].json;

let failed = 0;
const check = (label, got, want) => {
  const g = JSON.stringify(got), w = JSON.stringify(want);
  if (g === w) console.log('ok    ' + label);
  else { failed++; console.log('FAIL  ' + label + '\n        expected ' + w + '\n        got      ' + g); }
};

const INBOUND = 'agent_eceb7448aa1f37e8f436a63a43';
const OUTBOUND = 'agent_4ef8160dc71826818c6fd8122b';
const SPAM = /\b(free|guarantee|urgent|act now|click here|limited time|winner|congratulations|no obligation|risk[- ]free|100%|\$\$\$|buy now|order now)\b/i;

const baseCall = (over) => ({
  call_id: 'call_test0001', call_type: 'phone_call', call_status: 'ended', agent_id: INBOUND, direction: 'inbound',
  from_number: '+14155550100', to_number: '+16282862281', start_timestamp: 1789960000000, end_timestamp: 1789960090000, duration_ms: 90000,
  disconnection_reason: 'user_hangup', recording_url: 'https://example.invalid/rec.wav',
  retell_llm_dynamic_variables: {},
  transcript_object: [{ role: 'agent', content: 'Hi, this is Aria.' }, { role: 'user', content: 'Hi, I want to book a massage.' }],
  transcript_with_tool_calls: [],
  call_analysis: { call_summary: 'The user called to book a massage — the agent found a time and the user confirmed it with the agent.', user_sentiment: 'Positive', in_voicemail: false,
    custom_analysis_data: { caller_intent: 'new_booking', resolution_status: 'booking_created', callback_required: false, caller_sentiment: 'positive', language_used: 'english', tool_failure: false } },
  ...over,
});
const booking = (start, end, service) => [
  { role: 'tool_call_invocation', tool_call_id: 'b1', name: 'book_appointment', arguments: JSON.stringify({ firstName: 'Test', lastName: 'John', serviceName: service, startDate: start, endDate: end, phone: '+14155550100' }) },
  { role: 'tool_call_result', tool_call_id: 'b1', content: JSON.stringify({ success: true, confirmed: true, bookingId: 'x' }) },
];

// ---- inbound, booked ------------------------------------------------------------
let r = run({ event: 'call_analyzed', call: baseCall({ transcript_with_tool_calls: booking('2026-10-07T10:00:00', '2026-10-07T11:00:00', 'Swedish Massage') }) });
check('inbound booked: sends', r.send, true);
check('inbound booked: subject', r.subject, 'Call recap: Test John, appointment booked');
check('inbound booked: booking line', r.text.includes('Appointment: Swedish Massage, one hour, Wednesday, October 7 at 10:00 AM'), true);
check('inbound booked: intro in first person', r.text.includes('I just took a call from Test John at +1 (415) 555-0100.'), true);
check('inbound booked: summary rewritten to Aria', r.text.includes('The caller called to book a massage, I found a time and the caller confirmed it with me.'), true);
check('inbound booked: no long dashes anywhere', /[—–]/.test(r.html + r.text + r.subject), false);
check('inbound booked: no spam words', SPAM.test(r.subject + ' ' + r.text), false);
check('inbound booked: brand colours present', ['#1563E0', '#144EB8', '#F3F6F9', '#0F1729', '#E1E7EF'].every(c => r.html.includes(c)), true);
check('inbound booked: no images', /<img/i.test(r.html), false);
check('inbound booked: only the AIEmply call link', r.html.includes('https://app.aiemply.com/dashboard/logs?call=call_test0001') && !r.html.includes('rec.wav') && !r.text.includes('rec.wav'), true);
check('inbound booked: greets Nicky', r.text.startsWith('Hi Nicky,'), true);
check('inbound booked: no Retell link in a client-facing mail', r.html.includes('retellai.com'), false);
check('inbound booked: to the spa, engineering on copy', [r.to, r.cc], ['sagewillowspa@gmail.com', 'engineering@aiemply.com']);
check('test line inbound: no recap', run({ event: 'call_analyzed', call: baseCall({ from_number: '+12532681856' }) }).skip_reason, 'test line');
check('test line outbound: no recap', run({ event: 'call_analyzed', call: baseCall({ agent_id: OUTBOUND, direction: 'outbound', from_number: '+16282862281', to_number: '+12532681856' }) }).skip_reason, 'test line');
check('test line, other formatting: no recap', run({ event: 'call_analyzed', call: baseCall({ from_number: '12532681856' }) }).skip_reason, 'test line');
check('inbound booked: html escaped', r.html.includes('Sage &amp; Willow Spa'), true);

// ---- inbound, cancelled via tool, model says otherwise --------------------------------
r = run({ event: 'call_analyzed', call: baseCall({ transcript_with_tool_calls: [
  { role: 'tool_call_invocation', tool_call_id: 'c1', name: 'cancel_booking', arguments: '{"bookingId":"abc","phone":"+14155550100"}' },
  { role: 'tool_call_result', tool_call_id: 'c1', content: '{"success":true,"cancelFlag":"yes"}' }],
  call_analysis: { call_summary: 'The user cancelled.', custom_analysis_data: { caller_intent: 'cancel', resolution_status: 'other', callback_required: true, callback_reason: 'wants a price list emailed' } } }) });
check('cancel: tool result beats the model label', r.outcome, 'appointment cancelled');
check('cancel: callback note', r.text.includes('They would like someone from the spa to call them back: wants a price list emailed'), true);
check('cancel: no name -> phone in subject', r.subject, 'Call recap: +1 (415) 555-0100, appointment cancelled');

// ---- outbound, real conversation ----------------------------------------------------------
const outCall = (over) => baseCall({ agent_id: OUTBOUND, direction: 'outbound', from_number: '+16282862281', to_number: '+14155550101',
  retell_llm_dynamic_variables: { lead_first_name: 'TEST', lead_last_name: 'JOHN', lead_phone: '+14155550101', lead_source: 'missed_call', lead_name_known: 'yes', inbound_intent: '' },
  call_analysis: { call_summary: 'The agent initiated an outbound call and spoke with the user, who booked.', in_voicemail: false, user_sentiment: 'Neutral',
    custom_analysis_data: { reached_lead: 'lead', outbound_outcome: 'booked', callback_required: false, caller_sentiment: 'neutral' } }, ...over });
r = run({ event: 'call_analyzed', call: outCall({ transcript_with_tool_calls: booking('2026-10-14T13:00:00', '2026-10-14T14:00:00', 'Deep Tissue Massage') }) });
check('outbound real: sends', r.send, true);
check('outbound real: missed-call intro', r.text.includes('I just called Test John at +1 (415) 555-0101 back after they rang the spa earlier.'), true);
check('outbound real: contact source', r.text.includes('Came from: a missed call to the spa'), true);
check('outbound real: summary first person', r.text.includes('I initiated an outbound call and spoke with the caller, who booked.'), true);
r = run({ event: 'call_analyzed', call: outCall({ retell_llm_dynamic_variables: { lead_first_name: 'TEST', lead_last_name: 'JOHN', lead_source: 'website_form' } }) });
check('outbound form: intro', r.text.includes('about the booking form they sent in'), true);
check('outbound form: name from dynamic vars', r.name, 'TEST JOHN');

// ---- outbound machine outcomes: no e-mail ------------------------------------------------------
for (const [label, over] of [
  ['voicemail_reached', { disconnection_reason: 'voicemail_reached' }],
  ['in_voicemail flag', { call_analysis: { in_voicemail: true, custom_analysis_data: {} } }],
  ['dial_no_answer', { disconnection_reason: 'dial_no_answer', duration_ms: 0 }],
  ['dial_busy', { disconnection_reason: 'dial_busy' }],
  ['dial_failed', { disconnection_reason: 'dial_failed' }],
  ['reached_lead no_answer', { call_analysis: { in_voicemail: false, custom_analysis_data: { reached_lead: 'no_answer' } } }],
  ['reached_lead voicemail', { call_analysis: { in_voicemail: false, custom_analysis_data: { reached_lead: 'voicemail' } } }],
  ['nobody spoke', { transcript_object: [{ role: 'agent', content: 'Hi, is this Test?' }] }],
  ['call not connected', { call_status: 'not_connected' }],
  ['user_declined', { disconnection_reason: 'user_declined' }],
  ['error_no_audio_received', { disconnection_reason: 'error_no_audio_received' }],
]) {
  r = run({ event: 'call_analyzed', call: outCall(over) });
  check(`outbound skip: ${label}`, [r.send, !!r.skip_reason], [false, true]);
}
r = run({ event: 'call_analyzed', call: outCall({ call_analysis: { custom_analysis_data: { reached_lead: 'wrong_person', outbound_outcome: 'wrong_number' } } }) });
check('outbound wrong person still counts as a real call', [r.send, r.outcome], [true, 'wrong person answered']);

// ---- generic skips ---------------------------------------------------------------------------
check('other event skipped', run({ event: 'call_ended', call: baseCall() }).send, false);
check('other agent skipped', run({ event: 'call_analyzed', call: baseCall({ agent_id: 'agent_other' }) }).send, false);
check('web call skipped', run({ event: 'call_analyzed', call: baseCall({ call_type: 'web_call' }) }).send, false);
check('inbound with no caller speech skipped', run({ event: 'call_analyzed', call: baseCall({ transcript_object: [{ role: 'agent', content: 'Hello?' }] }) }).send, false);
r = run({ event: 'call_analyzed', dryRun: true, call: baseCall() });
check('dry run composes but does not send', [r.send, r.skip_reason, r.html.length > 1000], [false, 'dry run (composed, not sent)', true]);
check('template-variable name is ignored', run({ event: 'call_analyzed', call: baseCall({ retell_llm_dynamic_variables: { lead_first_name: '{{lead_first_name}}' } }) }).name, '');

// ---- real calls passed on the command line -----------------------------------------------------------
for (const file of process.argv.slice(2)) {
  const call = JSON.parse(fs.readFileSync(file, 'utf8'));
  const out = run({ event: 'call_analyzed', call });
  const label = path.basename(file, '.json');
  console.log(`\n${label}: send=${out.send} ${out.skip_reason || ''} | ${out.subject || ''}`);
  if (out.html) {
    const dest = path.join(__dirname, `_preview_${label}.html`);
    fs.writeFileSync(dest, out.html);
    console.log(`   html -> ${dest}`);
    console.log('   ' + out.text.split('\n').slice(0, 6).join('\n   '));
    if (/[—–]/.test(out.html + out.text + out.subject)) { failed++; console.log('FAIL  long dash in real-call output'); }
    if (SPAM.test(out.subject + ' ' + out.text)) { failed++; console.log('FAIL  spam word in real-call output'); }
  }
}

console.log('\n' + (failed ? 'FAILED ' + failed : 'all passed'));
process.exit(failed ? 1 : 0);
