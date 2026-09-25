// Harness for post_call_email_render.js (the "Render: Recap Email" node).
//
//   node outbound/test_post_call_email_render.js
//
// Composes a real-shaped call with post_call_email.js, then feeds the render
// node fake GPT replies - good ones and every kind it must refuse. No API calls.
const fs = require('fs');
const path = require('path');

const COMPOSE = fs.readFileSync(path.join(__dirname, 'post_call_email.js'), 'utf8');
const RENDER = fs.readFileSync(path.join(__dirname, 'post_call_email_render.js'), 'utf8');
const compose = (body) => new Function('$input', COMPOSE)({ first: () => ({ json: { body } }) })[0].json;
const render = (composed, reply) => new Function('$', '$input', RENDER)(
  () => ({ first: () => ({ json: composed }) }),
  { first: () => ({ json: reply }) })[0].json;
const gpt = (obj) => ({ choices: [{ message: { content: typeof obj === 'string' ? obj : JSON.stringify(obj) } }] });

let failed = 0;
const check = (label, got, want) => {
  const g = JSON.stringify(got), w = JSON.stringify(want);
  if (g === w) console.log('ok    ' + label);
  else { failed++; console.log('FAIL  ' + label + '\n        expected ' + w + '\n        got      ' + g); }
};

const call = {
  call_id: 'call_render0001', call_type: 'phone_call', call_status: 'ended', agent_id: 'agent_eceb7448aa1f37e8f436a63a43',
  direction: 'inbound', from_number: '+14155550100', to_number: '+16282862281', start_timestamp: 1790106703302,
  duration_ms: 95000, disconnection_reason: 'agent_hangup', retell_llm_dynamic_variables: {},
  transcript_object: [{ role: 'agent', content: 'Hi, this is Aria.' }, { role: 'user', content: 'I want a Signature massage with Nicky.' }],
  transcript_with_tool_calls: [
    { role: 'tool_call_invocation', tool_call_id: 'b1', name: 'book_appointment', arguments: JSON.stringify({ firstName: 'Test', lastName: 'John', serviceName: 'Signature Massage', startDate: '2026-10-01T17:00:00', endDate: '2026-10-01T18:00:00' }) },
    { role: 'tool_call_result', tool_call_id: 'b1', content: '{"success":true,"confirmed":true}' }],
  call_analysis: { call_summary: 'The user booked.', custom_analysis_data: { caller_intent: 'new_booking', resolution_status: 'booking_created', caller_sentiment: 'positive' } },
};
const c = compose({ event: 'call_analyzed', call });
const GOOD = {
  subject: 'Call recap: Test John, appointment booked',
  paragraphs: [
    'I just took a call from Test John, who wanted a Signature Massage with Nicky.',
    'Nicky was available at 5 PM, so I booked a Signature Massage, one hour, on Thursday, October 1 at 5:00 PM with her.',
    'They sounded happy with it. Nothing else needs doing.'],
};

let r = render(c, gpt(GOOD));
check('good reply: written by the model', r.writer, 'gpt-4.1-mini');
check('good reply: subject from the model', r.subject, GOOD.subject);
check('good reply: paragraphs in the html', r.html.includes('I just took a call from Test John, who wanted a Signature Massage with Nicky.'), true);
check('good reply: greeting from code, exactly once', r.html.split('Hi Nicky,').length - 1, 1);
check('good reply: call link and cards kept', [r.html.includes('dashboard/logs?call=call_render0001'), r.html.includes('Call details'), r.html.includes('Contact')], [true, true, true]);
check('good reply: text version filled', r.text.startsWith('Hi Nicky,\n\nI just took a call from Test John'), true);
check('good reply: no marker left', /ARIA_BODY/.test(r.html + r.text), false);
check('good reply: to/cc/send carried', [r.to, r.cc, r.send], ['sagewillowspa@gmail.com', 'engineering@aiemply.com', true]);

r = render(c, gpt({ ...GOOD, paragraphs: ['Hi Nicky,', ...GOOD.paragraphs, 'Best, Aria'] }));
check('model greeting/sign-off dropped', [r.writer, r.html.split('Hi Nicky,').length - 1, /Best, Aria/.test(r.html)], ['gpt-4.1-mini', 1, false]);
r = render(c, gpt({ ...GOOD, paragraphs: ['I just took a call from Test John — a lovely chat.', GOOD.paragraphs[1]] }));
check('long dash tidied, not rejected', [r.writer, /[—–]/.test(r.html + r.text + r.subject)], ['gpt-4.1-mini', false]);
r = render(c, gpt({ ...GOOD, paragraphs: ['- I just took a call from **Test John**.', GOOD.paragraphs[1]] }));
check('markdown tidied', [r.writer, r.html.includes('**'), r.html.includes('>- ')], ['gpt-4.1-mini', false, false]);

const refuse = [
  ['model error item', { error: { message: 'ETIMEDOUT' } }],
  ['empty reply', { choices: [] }],
  ['not JSON', gpt('Sure! Here is the recap...')],
  ['no paragraphs', gpt({ subject: 'x', paragraphs: [] })],
  ['a link', gpt({ ...GOOD, paragraphs: [...GOOD.paragraphs, 'See https://example.com for details.'] })],
  ['a price', gpt({ ...GOOD, paragraphs: [...GOOD.paragraphs, 'It came to ninety dollars.'] })],
  ['a dollar figure', gpt({ ...GOOD, paragraphs: [...GOOD.paragraphs, 'Total $90.'] })],
  ['a time not in the facts', gpt({ ...GOOD, paragraphs: ['I booked Test John for 4:30 PM on Thursday, October 1.'] })],
  ['a date not in the facts', gpt({ ...GOOD, paragraphs: ['I booked Test John for 5:00 PM on October 8.'] })],
  ['a weekday not in the facts', gpt({ ...GOOD, paragraphs: ['I booked Test John for Friday at 5:00 PM, one hour.'] })],
  ['a phone number not the caller', gpt({ ...GOOD, paragraphs: [...GOOD.paragraphs, 'They also gave 415 555 0199.'] })],
  ['spam wording', gpt({ ...GOOD, paragraphs: [...GOOD.paragraphs, 'Act now to keep the slot!'] })],
  ['mentions the software', gpt({ ...GOOD, paragraphs: [...GOOD.paragraphs, 'The transcript shows they were happy.'] })],
];
for (const [label, reply] of refuse) {
  r = render(c, reply);
  check(`refused -> template: ${label}`, [r.writer, r.subject, r.html === c.html], ['template', c.subject, true]);
}
r = render(c, gpt({ ...GOOD, paragraphs: [...GOOD.paragraphs, 'Their number is +1 (415) 555-0100 if you need it.'] }));
check('the caller\'s own number is allowed', r.writer, 'gpt-4.1-mini');
r = render(c, gpt({ ...GOOD, paragraphs: ['I checked and Nicky was free at 5 PM, so I booked it for Thursday, October 1 at 5:00 PM.'] }));
check('"free" as in available is fine', r.writer, 'gpt-4.1-mini');
r = render({ ...c, send: false, dryRun: true }, gpt(GOOD));
check('dry run: rendered, not sent', [r.writer, r.send], ['gpt-4.1-mini', false]);

console.log('\n' + (failed ? 'FAILED ' + failed : 'all passed'));
process.exit(failed ? 1 : 0);
