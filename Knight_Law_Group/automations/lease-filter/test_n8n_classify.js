const fs = require('fs');
const path = require('path');
const CASES = require('./rules_cases');
const OUT = path.join(__dirname, 'out');
const NEW = fs.readFileSync(path.join(OUT, 'classify_new.js'), 'utf8');
const LIVE = fs.readFileSync(path.join(OUT, 'classify_live.js'), 'utf8');
const LABEL = { purchased: 'Purchased', leased: 'Leased', lease_buyout: 'Leased, then purchased' };

function run(src, ai, call) {
  const $input = { first: () => ({ json: { message: { content: JSON.stringify(ai) } } }) };
  const $ = () => ({ first: () => ({ json: { body: { call } } }) });
  return new Function('$input', '$', src)($input, $)[0].json;
}
const EN = 'User: Yes.\nUser: I bought it from a dealership here in California, it is a used vehicle.\nUser: Yes, I still have the car.\nUser: Okay, that is fine, thanks.';
const ai = (c) => ({ lead_language: 'English', opt_out: 'No', is_voicemail: 'No', requested_human: 'No', declined_ai: 'No', issue: 'Yes', ca_purchase: 'Yes', purchase_type: c.pt ? LABEL[c.pt] : 'N/A', in_possession: c.possess ? 'Yes' : 'No', vehicle_year: String(c.year), vehicle_make: c.make, vehicle_model: 'N/A', new_or_used: 'New', is_cpo: 'N/A', repairs_attempted: 'Yes', is_owner: 'Yes', full_name: 'N/A', confirmed_email: 'N/A', contact_consent: 'Yes', call_dnd: false, sms_dnd: false, email_dnd: false, call_summary: 'x' });
// New-flow calls carry the in-call answer in collected_dynamic_variables.purchase_type_call (Retell enum key).
const call = (c, over) => Object.assign({ call_id: 'c', start_timestamp: 1000000, end_timestamp: 1300000, disconnection_reason: 'user_hangup', transcript: EN, retell_llm_dynamic_variables: Object.assign({ Name: 'John Doe', Phone: '+15555550100', Email: 'jane@acme.ai', lead_language: 'English' }, c && c.ptSeed ? { purchase_type: c.ptSeed } : {}), collected_dynamic_variables: c && c.pt ? { purchase_type_call: c.pt } : {} }, over || {});

let fail = 0;
console.log('== rule cases ==');
for (const c of CASES) {
  const o = run(NEW, ai(c), call(c));
  const wantPt = c.pt ? LABEL[c.pt] : (c.ptSeed || 'N/A');
  const ok = o.lead_status === c.n8n[0] && o.bad_lead_reason === c.n8n[1] && o.purchase_type === wantPt;
  if (!ok) fail++;
  console.log((ok ? '  ok   ' : '  FAIL ') + c.label.padEnd(60) + ' -> ' + o.lead_status + ' / ' + o.bad_lead_reason + ' / ' + o.purchase_type + (ok ? '' : '   WANT ' + c.n8n.join(' / ') + ' / ' + wantPt));
}

console.log('\n== gate: calls from the currently published flow (no purchase_type_call, nothing on file) keep the old rules ==');
const oldFlow = (make, aiPt) => { const c = { make, year: 2023, possess: true, pt: '' }; const a = Object.assign(ai(c), { purchase_type: aiPt }); return [run(NEW, a, call(c)), run(LIVE, a, call(c))]; };
for (const [label, make, aiPt, want] of [
  ['old flow, Tesla, AI heard "Purchased" -> live result', 'Tesla', 'Purchased', 'Non-Retainer Lead'],
  ['old flow, Honda, AI heard "Leased" -> live result', 'Honda', 'Leased', 'Non-Retainer Lead'],
  ['old flow, BMW, AI heard "Leased" -> live result', 'BMW', 'Leased', 'Retainer Lead'],
]) {
  const [a, b] = oldFlow(make, aiPt);
  const ok = a.lead_status === want && a.lead_status === b.lead_status && a.bad_lead_reason === b.bad_lead_reason && a.purchase_type === 'N/A';
  if (!ok) fail++;
  console.log((ok ? '  ok   ' : '  FAIL ') + label.padEnd(60) + ' -> ' + a.lead_status + ' / ' + a.bad_lead_reason + ' / ' + a.purchase_type + ' (live: ' + b.lead_status + ')');
}
{ // in-call answer wins over the transcript AI, so the status matches what Alice said on the call
  const c = { make: 'Honda', year: 2023, possess: true, pt: 'purchased' };
  const o = run(NEW, Object.assign(ai(c), { purchase_type: 'Leased' }), call(c));
  const ok = o.lead_status === 'Non-Retainer Lead' && o.purchase_type === 'Purchased';
  if (!ok) fail++;
  console.log((ok ? '  ok   ' : '  FAIL ') + 'in-call "purchased" beats AI "Leased" (Honda)'.padEnd(60) + ' -> ' + o.lead_status + ' / ' + o.purchase_type);
}

console.log('\n== regression: no purchase type, must equal live on every existing field ==');
const MAKES = ['Acura','Audi','BMW','Buick','Cadillac','Chevrolet','Chrysler','Dodge','FIAT','Ford','Genesis','GMC','Honda','HUMMER','Hyundai','INFINITI','Jaguar','Jeep','Kia','Land Rover','Lexus','Lincoln','Mazda','Mercedes-Benz','MINI','Mitsubishi','Nissan','Porsche','Ram','Subaru','Tesla','Toyota','Volkswagen','Volvo','Rivian','Lucid'];
let reg = 0, n = 0;
for (const make of MAKES) for (const year of [2019, 2020, 2021, 2024]) for (const possess of [true, false]) {
  const c = { make, year, possess, pt: '' }; n++;
  const a = run(NEW, ai(c), call(c)), b = run(LIVE, ai(c), call(c));
  for (const k of Object.keys(b)) if (JSON.stringify(a[k]) !== JSON.stringify(b[k])) { reg++; console.log('  DIFF ' + make + ' ' + year + ' possess=' + possess + ' ' + k + ': ' + JSON.stringify(b[k]) + ' -> ' + JSON.stringify(a[k])); }
}
console.log('  ' + n + ' combinations, ' + reg + ' differences');

console.log('\n== Lead Language word count still splits on whitespace (fixed live 2026-09-28) ==');
const ES_FEW_S = 'User: Bueno, claro.\nUser: Lo compré nuevo aquí en California.\nUser: Tengo el carro, el Ford nuevo, del año pasado.';
const base = Object.assign(ai({ make: 'Ford', year: 2024, possess: true, pt: 'purchased' }), { lead_language: 'Spanish' });
const langNew = run(NEW, base, call(null, { transcript: ES_FEW_S })).lead_language;
const langOk = langNew === 'Spanish';
if (!langOk) fail++;
console.log((langOk ? '  ok   ' : '  FAIL ') + 'real 5-min Spanish call, English on file -> ' + langNew);

console.log('\nfailures: ' + fail + ' | regressions: ' + reg);
process.exit(fail + reg ? 1 : 0);
