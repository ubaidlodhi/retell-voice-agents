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
// ---- what GPT-4.1-mini is handed -------------------------------------------------------------
check('writer: real call is written', r.write, true);
check('writer: model is gpt-4.1-mini, JSON out', [r.openai_body.model, r.openai_body.response_format.type], ['gpt-4.1-mini', 'json_object']);
check('writer: facts carry the booking from the tool', r.facts.appointment, 'Swedish Massage, one hour, Wednesday, October 7 at 10:00 AM');
check('writer: transcript reaches the model', JSON.parse(r.openai_body.messages[1].content).transcript.includes('Caller: Hi, I want to book a massage.'), true);
check('writer: shells carry one body marker each', [r.html_shell.split('<!--ARIA_BODY-->').length, r.text_shell.split('{{ARIA_BODY}}').length], [2, 2]);
check('writer: greeting + link stay in code', [r.html_shell.includes('Hi Nicky,'), r.html_shell.includes('dashboard/logs?call=call_test0001')], [true, true]);
check('writer: skipped calls are not written', run({ event: 'call_analyzed', call: baseCall({ from_number: '+12532681856' }) }).write, false);
check('writer: outcome proven by the tool, no Retell labels in the facts', [r.facts.confirmed_outcome, r.facts.outcome, r.facts.they_wanted], ['appointment booked', undefined, undefined]);
check('writer: shells carry one detail-row marker each', [r.html_shell.split('<!--ARIA_TOP_ROWS-->').length, r.text_shell.split('{{ARIA_TOP_ROWS}}').length], [2, 2]);
check('writer: row template has both blanks', [r.row_tpl.includes('%%LABEL%%'), r.row_tpl.includes('%%VALUE%%')], [true, true]);
check('writer: template keeps its own Outcome row', [r.text.includes('Call details\n  Outcome: Appointment booked\n  They wanted to: book a massage\n  Appointment:'), r.html_shell.includes('>Outcome</td>')], [true, false]);
check('writer: asked for outcome + they_wanted, and "they" for the caller', ['"outcome"', '"they_wanted"', 'Never "he", "she"'].every(k => r.openai_body.messages[0].content.includes(k)), true);
// two people at once (call_cc43d37f): the guest count reaches the appointment line
const twoGuests = [
  { role: 'tool_call_invocation', tool_call_id: 'b2', name: 'book_appointment', arguments: JSON.stringify({ firstName: 'Test', lastName: 'John', serviceName: 'Deep Tissue Massage', numberOfParticipants: 2, startDate: '2026-09-26T12:00:00', endDate: '2026-09-26T13:30:00' }) },
  { role: 'tool_call_result', tool_call_id: 'b2', content: '{"success":true,"confirmed":true}' }];
const g2 = run({ event: 'call_analyzed', call: baseCall({ transcript_with_tool_calls: twoGuests }) });
check('two guests: appointment line', g2.text.includes('Appointment: Deep Tissue Massage, ninety minutes, Saturday, September 26 at 12:00 PM, for two guests'), true);
check('two guests: in the facts too', g2.facts.appointment, 'Deep Tissue Massage, ninety minutes, Saturday, September 26 at 12:00 PM, for two guests');
check('one guest: no guest wording', r.facts.appointment.includes('guest'), false);

// ---- V65: two people at once, and request-first services ----------------------------------------
const pairCall = [
  { role: 'tool_call_invocation', tool_call_id: 'p1', name: 'book_appointment', arguments: JSON.stringify({ firstName: 'Test', lastName: 'John',
    guestFirstName: 'Test', guestLastName: 'Jane', serviceName: 'Deep Tissue Massage', guestServiceName: 'Swedish Massage', guestDurationInMinutes: 60,
    startDate: '2026-09-30T14:00:00', endDate: '2026-09-30T15:30:00', phone: '+14155550100' }) },
  { role: 'tool_call_result', tool_call_id: 'p1', content: JSON.stringify({ success: true, guests: 2, status: 'CONFIRMED', bookings: [
    { who: 'caller', bookingId: 'a', startDate: '2026-09-30T14:00:00', endDate: '2026-09-30T15:30:00' },
    { who: 'guest', bookingId: 'b', startDate: '2026-09-30T14:00:00', endDate: '2026-09-30T15:00:00' }] }) }];
const pr = run({ event: 'call_analyzed', call: baseCall({ transcript_with_tool_calls: pairCall }) });
check('pair: both appointments on the line', pr.facts.appointment,
  'Wednesday, September 30 at 2:00 PM, side by side: Deep Tissue Massage, ninety minutes for Test John, and Swedish Massage, one hour for their guest Test Jane');
check('pair: booked, contact is the caller', [pr.outcome, pr.name], ['appointment booked', 'Test John']);
const pendCall = [
  { role: 'tool_call_invocation', tool_call_id: 'q1', name: 'book_appointment', arguments: JSON.stringify({ firstName: 'Test', lastName: 'John',
    serviceName: 'Couples Massage', startDate: '2026-10-01T13:00:00', endDate: '2026-10-01T14:00:00', phone: '+14155550100' }) },
  { role: 'tool_call_result', tool_call_id: 'q1', content: JSON.stringify({ success: true, confirmed: false, status: 'PENDING', requested: true }) }];
const pq = run({ event: 'call_analyzed', call: baseCall({ transcript_with_tool_calls: pendCall }) });
check('request-first: a request, not booked', [pq.outcome, pq.facts.confirmed_outcome, pq.subject], ['appointment requested', 'appointment requested', 'Call recap: Test John, appointment requested']);
check('request-first: the line says it waits for approval', pq.facts.appointment.endsWith('(a request, waiting for your approval in Wix)'), true);
check('request-first: the writer is told', pq.openai_body.messages[0].content.includes('"appointment requested"'), true);

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

// ---- outbound callback never reached them: one "missed lead" e-mail, no model (2026-10-03) ------
const SCREENER = [{ role: 'user', content: 'Hello. Please state your name after the tone, and Google Voice will try to connect you.' },
  { role: 'user', content: 'Hello?' }, { role: 'agent', content: 'Hi, this is Aria from Sage and Willow Spa.' }];
for (const [label, over, result] of [
  ['voicemail_reached', { disconnection_reason: 'voicemail_reached' }, 'Voicemail, message left'],
  ['in_voicemail flag', { call_analysis: { in_voicemail: true, custom_analysis_data: {} } }, 'Voicemail, message left'],
  ['dial_no_answer', { disconnection_reason: 'dial_no_answer', duration_ms: 0 }, 'No answer'],
  ['dial_busy', { disconnection_reason: 'dial_busy' }, 'Line busy'],
  ['dial_failed', { disconnection_reason: 'dial_failed' }, 'Call did not go through'],
  ['reached_lead no_answer', { call_analysis: { in_voicemail: false, custom_analysis_data: { reached_lead: 'no_answer' } } }, 'No answer'],
  ['reached_lead voicemail', { call_analysis: { in_voicemail: false, custom_analysis_data: { reached_lead: 'voicemail' } } }, 'Voicemail, message left'],
  ['nobody spoke', { transcript_object: [{ role: 'agent', content: 'Hi, is this Test?' }] }, 'Picked up, never talked'],
  ['call not connected', { call_status: 'not_connected' }, 'Call did not go through'],
  ['user_declined', { disconnection_reason: 'user_declined' }, 'Call did not go through'],
  ['error_no_audio_received', { disconnection_reason: 'error_no_audio_received' }, 'Call did not go through'],
  ['call screener, then "Hello?" (call_2e664e7e)', { transcript_object: SCREENER,
    call_analysis: { in_voicemail: false, custom_analysis_data: { reached_lead: 'unclear' } } }, 'Picked up, never talked'],
  ['one "Hello?" and gone', { transcript_object: [{ role: 'agent', content: 'Hi, this is Aria.' }, { role: 'user', content: 'Hello?' }],
    call_analysis: { in_voicemail: false, custom_analysis_data: { reached_lead: 'unclear' } } }, 'Picked up, never talked'],
]) {
  r = run({ event: 'call_analyzed', call: outCall(over) });
  check(`outbound missed lead: ${label}`, [r.write, r.send, r.missed, r.subject, r.text.includes(`Result: ${result}`)],
    [false, false, true, 'Missed lead: TEST JOHN, please call them back', true]);
}
r = run({ event: 'call_analyzed', call: outCall({ disconnection_reason: 'voicemail_reached',
  retell_llm_dynamic_variables: { lead_first_name: '', lead_last_name: '', lead_phone: '+14155550101', lead_source: 'missed_call',
    lead_submitted_at: 'Friday, October 2 at 12:13 PM', inbound_intent: 'booking a couples massage' } }) });
check('missed lead: no name -> phone in subject', r.subject, 'Missed lead: +1 (415) 555-0101, please call them back');
check('missed lead: their call, what they wanted, what I did, the ask', [
  r.text.includes('+1 (415) 555-0101 rang the spa on Friday, October 2 at 12:13 PM about booking a couples massage, and the call ended before I could help.'),
  r.text.includes('but it went to voicemail, so I left a message asking them to call us back.'),
  r.text.includes('Could you give them a call when you have a moment?'),
  r.text.includes('They wanted: booking a couples massage')], [true, true, true, true]);
check('missed lead: same look as the recap, call link, no dashes', [r.html.includes('#1563E0'), r.html.includes('dashboard/logs?call=call_test0001'),
  /[—–]/.test(r.html + r.text + r.subject)], [true, true, false]);
r = run({ event: 'call_analyzed', call: outCall({ disconnection_reason: 'voicemail_reached',
  retell_llm_dynamic_variables: { lead_first_name: 'Jane', lead_last_name: 'Doe', lead_source: 'website_form', lead_submitted_at: 'Friday, October 2 at 9:00 AM' } }) });
check('missed lead: website form wording', [r.text.includes('Jane Doe asked for a call back through the website form on Friday, October 2 at 9:00 AM.'),
  r.text.includes('Form sent: Friday, October 2 at 9:00 AM')], [true, true]);
r = run({ event: 'call_analyzed', dryRun: true, call: outCall({ disconnection_reason: 'voicemail_reached' }) });
check('missed lead: dry run composes, never sends', [r.missed, r.skip_reason], [false, 'dry run (missed lead composed, not sent)']);
r = run({ event: 'call_analyzed', call: outCall({ transcript_object: [{ role: 'user', content: 'Hello?' }, { role: 'user', content: 'Yes, speaking.' },
  { role: 'user', content: 'Not today, thanks.' }], call_analysis: { in_voicemail: false, custom_analysis_data: { reached_lead: 'unclear' } } }) });
check('outbound: three things said is a conversation -> normal recap', [r.write, !!r.missed], [true, false]);
check('outbound mid-call status is still skipped', run({ event: 'call_analyzed', call: outCall({ call_status: 'ongoing' }) }).skip_reason, 'call_status ongoing');
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
