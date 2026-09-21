// Test harness for outbound_test_dialer.html.
//
//   node outbound/test_dialer.js
//
// The page keeps its DOM-free logic in <script id="core">; that block is read
// out of the HTML and evaluated here so the tests can never drift from the
// page. The second half cross-checks the DOM script against the markup: every
// element id it asks for must exist.

const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, 'outbound_test_dialer.html'), 'utf8');
const coreMatch = html.match(/<script id="core">([\s\S]*?)<\/script>/);
if (!coreMatch) throw new Error('<script id="core"> not found');
const mod = { exports: {} };
new Function('module', coreMatch[1])(mod);
const { WEBHOOK_URL, normalizePhone, formatPhone, buildPayload, describeResponse } = mod.exports;

let failed = 0;
const check = (label, got, want) => {
  const g = JSON.stringify(got), w = JSON.stringify(want);
  if (g === w) console.log(`ok    ${label}`);
  else { failed++; console.log(`FAIL  ${label}\n        expected ${w}\n        got      ${g}`); }
};

check('webhook is the LIVE trigger', WEBHOOK_URL, 'https://automation.aiemply.com/webhook/sage-willow-lead-callout');

// ---- phone -----------------------------------------------------------------
check('formatted US number', normalizePhone('(253) 268-1856'), '+12532681856');
check('dotted', normalizePhone('253.268.1856'), '+12532681856');
check('eleven digits with 1', normalizePhone('1 253 268 1856'), '+12532681856');
check('already E.164', normalizePhone('+12532681856'), '+12532681856');
check('too short is rejected', normalizePhone('268-1856'), '');
check('non-US is rejected', normalizePhone('+44 20 7946 0958'), '');
check('empty is rejected', normalizePhone(''), '');
check('formatPhone', formatPhone('+12532681856'), '+1 (253) 268-1856');
check('formatPhone passes junk through', formatPhone('nope'), 'nope');

// ---- payload ---------------------------------------------------------------
const base = { number: '+12532681856', version: 'latest', versionNumber: '', source: 'missed_call', firstName: '', lastName: '', intent: '', dryRun: false };

check('draft, missed call, no name', buildPayload(base),
  { payload: { phone: '+12532681856', source: 'missed_call', agent_version: 'latest' } });
check('published', buildPayload({ ...base, version: 'latest_published' }),
  { payload: { phone: '+12532681856', source: 'missed_call', agent_version: 'latest_published' } });
check('specific version is sent as a number', buildPayload({ ...base, version: 'specific', versionNumber: '4' }),
  { payload: { phone: '+12532681856', source: 'missed_call', agent_version: 4 } });
check('specific version 0 is allowed', buildPayload({ ...base, version: 'specific', versionNumber: '0' }),
  { payload: { phone: '+12532681856', source: 'missed_call', agent_version: 0 } });
check('specific version with spaces', buildPayload({ ...base, version: 'specific', versionNumber: ' 5 ' }),
  { payload: { phone: '+12532681856', source: 'missed_call', agent_version: 5 } });
check('specific version empty -> error', buildPayload({ ...base, version: 'specific', versionNumber: '' }),
  { error: 'Enter the version number (a whole number, e.g. 4).' });
check('specific version decimal -> error', buildPayload({ ...base, version: 'specific', versionNumber: '4.5' }),
  { error: 'Enter the version number (a whole number, e.g. 4).' });
check('specific version negative -> error', buildPayload({ ...base, version: 'specific', versionNumber: '-1' }),
  { error: 'Enter the version number (a whole number, e.g. 4).' });
check('bad number -> error', buildPayload({ ...base, number: '12345' }), { error: 'Pick a US number to call.' });
check('unknown version choice -> error', buildPayload({ ...base, version: 'nope' }), { error: 'Pick an agent version.' });

check('names and intent ride along on a missed call',
  buildPayload({ ...base, firstName: ' Jane ', lastName: 'Doe', intent: ' booking a massage ' }),
  { payload: { phone: '+12532681856', source: 'missed_call', agent_version: 'latest', first_name: 'Jane', last_name: 'Doe', inbound_intent: 'booking a massage' } });
check('website form needs a first name', buildPayload({ ...base, source: 'website_form' }),
  { error: 'A website-form lead needs at least a first name.' });
check('website form drops the intent', buildPayload({ ...base, source: 'website_form', firstName: 'Jane', intent: 'x' }),
  { payload: { phone: '+12532681856', source: 'website_form', agent_version: 'latest', first_name: 'Jane' } });
check('dry run flag', buildPayload({ ...base, dryRun: true }),
  { payload: { phone: '+12532681856', source: 'missed_call', agent_version: 'latest', dryRun: true } });

// ---- responses ---------------------------------------------------------------
const queued = describeResponse({ ok: true, call_id: 'call_abc', to: '+12532681856', agent_version: 5 }, 'latest');
check('queued call is ok', [queued.kind, queued.title, queued.body, queued.callId], ['ok', 'Calling +1 (253) 268-1856 now', 'Agent version 5.', 'call_abc']);

const queuedOld = describeResponse({ ok: true, call_id: 'call_abc', to: '+12532681856' }, 4);
check('queued call without a version echo still works', [queuedOld.kind, queuedOld.callId, queuedOld.agentVersion],
  ['ok', 'call_abc', undefined]);

const mismatch = describeResponse({ ok: true, call_id: 'call_abc', to: '+12532681856', agent_version: 4 }, 9);
check('requested v9 but got v4 -> warn', [mismatch.kind, mismatch.body], ['warn', 'You asked for v9 but Retell is dialling v4. Does that version exist?']);

const dry = describeResponse({ ok: true, dryRun: true, wouldCall: { to_number: '+12532681856', agent_version: 3, lead_source: 'missed_call', lead_name_known: 'no' } }, 3);
check('dry run is a warning, nothing dialled', [dry.kind, dry.title, dry.body],
  ['warn', 'Dry run - nothing was dialled', 'n8n would call +1 (253) 268-1856 on the v3 version as a missed_call lead with no name.']);

const dryNamed = describeResponse({ ok: true, dryRun: true, wouldCall: { to_number: '+12532681856', agent_version: 'latest', lead_source: 'website_form', lead_name_known: 'yes', lead_first_name: 'Jane', lead_last_name: 'Doe' } }, 'latest');
check('dry run names the lead', dryNamed.body, 'n8n would call +1 (253) 268-1856 on the latest draft version as a website_form lead named Jane Doe.');

check('rejected lead', describeResponse({ ok: false, errors: ['missing name'] }).body, 'missing name');
check('allowlist block', describeResponse({ ok: false, skipped: 'test_mode_allowlist', to: '+1415' }).kind, 'bad');
check('retell error', describeResponse({ ok: false, error: 'retell_create_call_failed', detail: { x: 1 } }).body, 'retell_create_call_failed');
check('garbage', describeResponse('nope').kind, 'bad');

// ---- markup <-> script cross-check ----------------------------------------------
const domScript = html.slice(html.indexOf('</script>', html.indexOf('<script id="core">')) + 9);
const wanted = new Set([...domScript.matchAll(/\$\('([A-Za-z0-9_-]+)'\)/g)].map(m => m[1]));
const present = new Set([...html.matchAll(/\bid="([A-Za-z0-9_-]+)"/g)].map(m => m[1]));
// ids the script creates itself at runtime
present.add('clearHistory');
const missing = [...wanted].filter(id => !present.has(id));
check('every element id the script uses exists in the markup', missing, []);

// no leftover `history` global shadowing (window.history) in the DOM script
check('DOM script does not declare a `history` variable', /\b(let|const|var)\s+history\b/.test(domScript), false);

console.log(`\n${failed ? 'FAILED ' + failed : 'all passed'}`);
process.exit(failed ? 1 : 0);
