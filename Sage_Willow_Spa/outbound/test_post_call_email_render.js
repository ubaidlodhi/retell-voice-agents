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

// ---- Outcome / They wanted to come from the model (Ubaid, 2026-09-25) --------------------------------
const rowIn = (html, label, value) => html.includes(`>${label}</td>`) && html.includes(`>${value}</td>`);
r = render(c, gpt({ ...GOOD, outcome: 'Appointment booked with Nicky', they_wanted: 'book a Signature Massage with Nicky' }));
check('rows: model outcome + wanted in the html', [r.writer, rowIn(r.html, 'Outcome', 'Appointment booked with Nicky'), rowIn(r.html, 'They wanted to', 'book a Signature Massage with Nicky')], ['gpt-4.1-mini', true, true]);
check('rows: and in the text', [r.text.includes('  Outcome: Appointment booked with Nicky\n  They wanted to: book a Signature Massage with Nicky\n  Appointment:')], [true]);
check('rows: no marker or blank left', /ARIA_TOP_ROWS|%%LABEL%%|%%VALUE%%/.test(r.html + r.text), false);
check('rows: exactly one Outcome row', r.html.split('>Outcome</td>').length - 1, 1);
r = render(c, gpt({ ...GOOD, outcome: 'Asked a question', they_wanted: 'ask about prices' }));
check('booked on record, model says otherwise -> tool result wins the row', [r.writer, rowIn(r.html, 'Outcome', 'Appointment booked'), /replaced by the tool result/.test(r.writer_note)], ['gpt-4.1-mini', true, true]);

// the call Ubaid flagged: asked about massages, booked nothing, Retell said "book a massage"
const infoCall = { ...call, call_id: 'call_render0002', transcript_with_tool_calls: [],
  transcript_object: [{ role: 'agent', content: 'Do you want to book a massage?' }, { role: 'user', content: 'Can you go over the options? What is the signature massage?' }, { role: 'user', content: "No, I'm going to book later." }],
  call_analysis: { call_summary: 'The user asked about massage options and decided not to book.', custom_analysis_data: { caller_intent: 'new_booking', resolution_status: 'info_provided', caller_sentiment: 'neutral' } } };
const ci = compose({ event: 'call_analyzed', call: infoCall });
check('info call: facts carry no outcome label and no Retell intent', [ci.facts.confirmed_outcome, ci.facts.they_wanted, ci.facts.outcome], [undefined, undefined, undefined]);
const INFO = { subject: 'Call recap: +1 (415) 555-0100, asked about massages', outcome: 'Asked about massages, will book later', they_wanted: 'hear the massage options',
  paragraphs: ['I took a call from someone who wanted to hear the massage options.', 'I explained the Signature Massage. They said they would book later, so nothing needs doing.'] };
r = render(ci, gpt(INFO));
check('info call: model rows, not "book a massage"', [r.writer, rowIn(r.html, 'Outcome', 'Asked about massages, will book later'), rowIn(r.html, 'They wanted to', 'hear the massage options'), r.html.includes('book a massage</td>')], ['gpt-4.1-mini', true, true, false]);
r = render(ci, gpt({ ...INFO, subject: 'Call Recap: Some Title Case Subject' }));
check('subject = name/phone + the model outcome, lower-case start', r.subject, 'Call recap: +1 (415) 555-0100, asked about massages, will book later');
r = render(ci, gpt({ ...INFO, outcome: 'Appointment booked' }));
check('info call: outcome claiming a booking no tool made -> template', [r.writer, r.html === ci.html], ['template', true]);
r = render(ci, gpt({ ...INFO, outcome: 'Did not book' }));
check('info call: "did not book" is fine', [r.writer, rowIn(r.html, 'Outcome', 'Did not book')], ['gpt-4.1-mini', true]);
r = render(ci, gpt({ ...INFO, they_wanted: 'They wanted to find out the prices.' }));
check('wanted: repeated label and full stop trimmed', rowIn(r.html, 'They wanted to', 'find out the prices'), true);
r = render(ci, gpt({ ...INFO, they_wanted: '' }));
check('wanted: empty -> no row', [r.writer, r.html.includes('>They wanted to</td>'), r.text.includes('They wanted to:')], ['gpt-4.1-mini', false, false]);
r = render(ci, gpt({ ...INFO, they_wanted: 'find out about every single massage on the menu and also what each one costs today' }));
check('wanted: too long -> left out', [r.writer, r.html.includes('>They wanted to</td>')], ['gpt-4.1-mini', false]);
r = render(ci, gpt({ ...INFO, outcome: undefined }));
check('outcome missing -> template label for the row', [r.writer, rowIn(r.html, 'Outcome', 'Question answered')], ['gpt-4.1-mini', true]);
// V65: a request-first booking is "requested" - a model saying "booked" loses the row
const pendC = compose({ event: 'call_analyzed', call: { ...call, call_id: 'call_render0003', transcript_with_tool_calls: [
  { role: 'tool_call_invocation', tool_call_id: 'q1', name: 'book_appointment', arguments: JSON.stringify({ firstName: 'Test', lastName: 'John', serviceName: 'Couples Massage', startDate: '2026-10-01T13:00:00', endDate: '2026-10-01T14:00:00' }) },
  { role: 'tool_call_result', tool_call_id: 'q1', content: '{"success":true,"status":"PENDING","requested":true}' }] } });
r = render(pendC, gpt({ ...INFO, outcome: 'Couples massage requested' }));
check('requested: the model saying "requested" keeps its row', [r.writer, rowIn(r.html, 'Outcome', 'Couples massage requested')], ['gpt-4.1-mini', true]);
r = render(pendC, gpt({ ...INFO, outcome: 'Appointment booked' }));
check('requested: the model saying "booked" -> the tool result wins', rowIn(r.html, 'Outcome', 'Appointment requested'), true);
r = render(ci, gpt({ ...INFO, they_wanted: 'hear the options, see https://example.com' }));
check('wanted is checked like the paragraphs (a link -> template)', r.writer, 'template');

console.log('\n' + (failed ? 'FAILED ' + failed : 'all passed'));
process.exit(failed ? 1 : 0);
