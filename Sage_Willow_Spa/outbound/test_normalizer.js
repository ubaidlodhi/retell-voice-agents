// Test harness for the "Normalize Lead" code node in the lead-callout workflow.
//
//   node outbound/test_normalizer.js
//
// The node body is read straight out of _build_lead_callout_workflow.py so the
// harness can never drift from what gets deployed. Cases are wrapped the way
// n8n actually delivers a webhook request: {headers, params, query, body}.

const fs = require('fs');
const path = require('path');

const src = fs.readFileSync(path.join(__dirname, '_build_lead_callout_workflow.py'), 'utf8');
const m = src.match(/NORMALIZE_CODE = r"""([\s\S]*?)"""/);
if (!m) throw new Error('NORMALIZE_CODE not found in _build_lead_callout_workflow.py');
const NORMALIZE_CODE = m[1];

const env = (b) => ({ headers: { 'content-type': 'application/json' }, params: {}, query: {}, body: b });

const CFG_TEST = { TEST_MODE: true, ALLOWED_NUMBERS: '+12532681856' };
const CFG_LIVE = { TEST_MODE: false, ALLOWED_NUMBERS: '+12532681856' };
const CFG_MULTI = { TEST_MODE: true, ALLOWED_NUMBERS: '+12532681856, (628) 682-8010' };

// [label, webhook payload, config, expected subset of the output]
const CASES = [
  ['wix nested + dryRun', env({ dryRun: true, data: { submissions: [
      { fieldName: 'Name', value: 'Jane Doe' },
      { fieldName: 'Phone', value: '(628) 555-0142' }] } }), CFG_TEST,
    { valid: true, dryRun: true, lead_first_name: 'Jane', lead_last_name: 'Doe', lead_phone: '+16285550142',
      allowed: false, blocked_reason: 'test_mode_allowlist', lead_source: 'website_form', lead_name_known: 'yes' }],

  ['flat name + phone', env({ name: 'Maria Lopez-Ruiz', phone: '628-555-0199' }), CFG_TEST,
    { valid: true, lead_first_name: 'Maria', lead_last_name: 'Lopez-Ruiz', lead_phone: '+16285550199', allowed: false }],

  ['split first/last', env({ first_name: 'Ana', last_name: 'Perez', mobile: '16285550177' }), CFG_TEST,
    { valid: true, lead_first_name: 'Ana', lead_last_name: 'Perez', lead_phone: '+16285550177' }],

  ['single-token name leaves last empty', env({ fields: [
      { label: 'full_name', value: 'Bob' }, { label: 'tel', value: '6285550123' }] }), CFG_TEST,
    { valid: true, lead_first_name: 'Bob', lead_last_name: '', lead_phone: '+16285550123', lead_name_known: 'no' }],

  ['deep payload wrapper', env({ payload: { contact: {
      full_name: 'Chris Nguyen', phone_number: '+1 628 555 0188' } } }), CFG_TEST,
    { valid: true, lead_first_name: 'Chris', lead_last_name: 'Nguyen', lead_phone: '+16285550188' }],

  ['unusable phone rejected', env({ name: 'Sam Smith', phone: '12345' }), CFG_TEST,
    { valid: false, lead_phone: '' }],

  ['missing name rejected on a form lead', env({ phone: '6285550101' }), CFG_TEST,
    { valid: false, lead_first_name: '' }],

  ['non-US number rejected', env({ name: 'Ola Nordmann', phone: '+4791234567' }), CFG_TEST,
    { valid: false }],

  ['no envelope (direct invocation)', { name: 'Direct Caller', phone: '6285550101' }, CFG_TEST,
    { valid: true, lead_first_name: 'Direct', lead_last_name: 'Caller', lead_phone: '+16285550101' }],

  // ---- testing guard ---------------------------------------------------
  ['allowlisted number passes in test mode', env({ name: 'Ubaid Lodhi', phone: '253-268-1856' }), CFG_TEST,
    { valid: true, allowed: true, test_mode: true, blocked_reason: '', lead_phone: '+12532681856' }],

  ['non-allowlisted number blocked in test mode', env({ name: 'Real Customer', phone: '415-419-4572' }), CFG_TEST,
    { valid: true, allowed: false, test_mode: true, blocked_reason: 'test_mode_allowlist' }],

  ['everything allowed once TEST_MODE is off', env({ name: 'Real Customer', phone: '415-419-4572' }), CFG_LIVE,
    { valid: true, allowed: true, test_mode: false, blocked_reason: '' }],

  ['allowlist accepts several formatted numbers', env({ name: 'Mint Line', phone: '6286828010' }), CFG_MULTI,
    { valid: true, allowed: true }],

  ['TEST_MODE as a string "true" still guards', env({ name: 'Real Customer', phone: '415-419-4572' }),
    { TEST_MODE: 'true', ALLOWED_NUMBERS: '+12532681856' },
    { allowed: false }],

  // ---- missed-call source ------------------------------------------------
  ['missed call with no name is still valid', env({
      source: 'missed_call', phone: '+12532681856', inbound_intent: 'booking a massage',
      inbound_call_id: 'call_abc', submitted_at: '2026-09-11T18:30:00Z' }), CFG_TEST,
    { valid: true, allowed: true, lead_source: 'missed_call', lead_first_name: '', lead_name_known: 'no',
      inbound_intent: 'booking a massage', inbound_call_id: 'call_abc' }],

  ['missed call with a name keeps it', env({
      source: 'missed_call', first_name: 'Dana', phone: '2532681856' }), CFG_TEST,
    { valid: true, lead_source: 'missed_call', lead_first_name: 'Dana', lead_last_name: '' }],

  ['unknown source falls back to website_form', env({ source: 'sms', name: 'X Y', phone: '2532681856' }), CFG_TEST,
    { lead_source: 'website_form' }],
];

const normalize = (raw, cfg) => {
  const $input = { first: () => ({ json: cfg }) };
  const $ = (name) => {
    if (name !== 'Webhook - Website Lead Form') throw new Error(`unexpected node ref ${name}`);
    return { first: () => ({ json: raw }) };
  };
  return new Function('$input', '$', NORMALIZE_CODE)($input, $)[0].json;
};

let failed = 0;
for (const [label, raw, cfg, expected] of CASES) {
  const got = normalize(raw, cfg);
  const bad = Object.entries(expected).filter(([k, v]) => got[k] !== v);
  if (bad.length) {
    failed++;
    console.log(`FAIL  ${label}`);
    for (const [k, v] of bad) console.log(`        ${k}: expected ${JSON.stringify(v)}, got ${JSON.stringify(got[k])}`);
  } else {
    console.log(`ok    ${label}`);
  }
}
console.log(`
${CASES.length - failed}/${CASES.length} passed`);
process.exit(failed ? 1 : 0);
