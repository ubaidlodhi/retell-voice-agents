// node Sage_Willow_Spa/n8n-workflow/test_flag_callback_email.js [--preview <dir>]
// Runs flag_callback_email.js (the "Validate: Flag Callback Args" Code node) on stub payloads.
const fs = require('fs');
const path = require('path');
const src = fs.readFileSync(path.join(__dirname, 'flag_callback_email.js'), 'utf8');
const previewDir = process.argv[2] === '--preview' ? process.argv[3] : null;

function run(json) {
  const fn = new Function('$input', `return (() => {${src}\n})();`);
  return fn({ first: () => ({ json }) })[0].json;
}

let fails = 0;
const check = (name, ok, got) => { if (!ok) fails++; console.log(`${ok ? 'PASS' : 'FAIL'} ${name}${ok ? '' : ' -> ' + JSON.stringify(got).slice(0, 300)}`); };

// 1. The Zach call (2026-09-29): name, phone, reason, question.
let r = run({ tool: 'flag-callback', callerPhone: null, args: { callerPhone: '+19135269174', callerName: 'Zach',
  reason: 'Caller wants to know if there are any current specials or discounts for new clients.',
  questionDetail: 'Do you have the 20% off new client deal?' } });
check('valid', r._valid === true && r._validationError === '', r);
check('subject', r._emailSubject === 'Callback request: Zach, (913) 526-9174', r._emailSubject);
check('html has tel link + button', r._emailHtml.includes('href="tel:+19135269174"') && r._emailHtml.includes('Call Zach back'), '');
check('html has reason + question', r._emailHtml.includes('current specials or discounts') && r._emailHtml.includes('20% off new client deal'), '');
check('html greeting + sign-off', r._emailHtml.includes('Hi Nicky,') && r._emailHtml.includes('Virtual receptionist'), '');
check('text part', r._emailBody.includes('Phone:   (913) 526-9174') && r._emailBody.includes('What they asked'), r._emailBody);
check('no long dashes anywhere', !/[—–]/.test(r._emailHtml + r._emailBody + r._emailSubject), '');
check('callerName back to Aria', r._callerName === 'Zach' && r._callerPhone === '+19135269174', r);
if (previewDir) fs.writeFileSync(path.join(previewDir, 'callback_email_zach.html'), r._emailHtml);

// 2. Transfer failed, no name (call_680c374e, 2026-09-30): Aria sent "unknown".
r = run({ tool: 'flag-callback', args: { callerPhone: '+14157707596', callerName: 'unknown',
  reason: 'Caller wants to speak with a customer service person about tipping options and possibly gift cards.' } });
check('unknown name -> subject is the phone only', r._emailSubject === 'Callback request: (415) 770-7596', r._emailSubject);
check('unknown name -> "A caller" + "Not given"', r._emailHtml.includes('A caller asked') && r._emailHtml.includes('Not given'), '');
check('no question card when no detail', !r._emailHtml.includes('What they asked'), '');
check('button uses the number', r._emailHtml.includes('Call (415) 770-7596 back'), '');
if (previewDir) fs.writeFileSync(path.join(previewDir, 'callback_email_noname.html'), r._emailHtml);

// 3. HTML injection in model text is escaped.
r = run({ args: { callerPhone: '+14155550100', callerName: 'Jane <b>Doe</b>', reason: 'x & <script>alert(1)</script>' } });
check('escaped', !r._emailHtml.includes('<script>') && r._emailHtml.includes('&lt;script&gt;') && r._emailHtml.includes('Jane &lt;b&gt;Doe&lt;/b&gt;'), '');

// 4. Placeholder phone, Retell metadata fallback.
r = run({ callerPhone: '+14155550101', args: { callerPhone: '{{user_number}}', callerName: 'Jane', reason: 'rebook' } });
check('placeholder phone falls back to call metadata', r._callerPhone === '+14155550101' && r._emailHtml.includes('tel:+14155550101'), r._callerPhone);

// 5. No phone at all.
r = run({ args: { callerName: 'Jane', reason: 'rebook' } });
check('no phone: no tel link, no button, says Not available', !r._emailHtml.includes('tel:') && r._emailHtml.includes('Not available') && r._emailSubject === 'Callback request: Jane', r._emailSubject);

// 6. Missing reason is still invalid (unchanged behaviour).
r = run({ args: { callerName: 'Jane', callerPhone: '+14155550100' } });
check('missing reason invalid', r._valid === false && /reason is required/.test(r._validationError), r._validationError);

// 7. Long dash in the model's reason is removed.
r = run({ args: { callerName: 'Jane', callerPhone: '+14155550100', reason: 'Gift card — for her mom' } });
check('long dash replaced', r._emailHtml.includes('Gift card, for her mom') && r._emailBody.includes('Gift card, for her mom'), '');

console.log(fails ? `${fails} FAILED` : 'all passed');
process.exit(fails ? 1 : 0);
