// Usage: node test_retell_classify.js [code-file]   (default: retell_classify.js)
const fs = require('fs');
const path = require('path');
const CASES = require('./rules_cases');
const src = fs.readFileSync(path.resolve(__dirname, process.argv[2] || 'retell_classify.js'), 'utf8');
const run = (dv) => new Function('dv', src)(dv);
let fail = 0;
for (const c of CASES) {
  const dv = { vehicle_make: c.make, vehicle_year: String(c.year), in_possession: String(c.possess) };
  if (c.pt) dv.purchase_type_call = c.pt;
  if (c.ptSeed) dv.purchase_type = c.ptSeed;
  const got = run(dv);
  const ok = got.route === c.retell[0] && got.bad_reason === c.retell[1];
  if (!ok) fail++;
  console.log((ok ? '  ok   ' : '  FAIL ') + c.label.padEnd(60) + ' -> ' + got.route + ' / ' + got.bad_reason + (ok ? '' : '   WANT ' + c.retell.join(' / ')));
}
console.log('\nfailures: ' + fail + ' / ' + CASES.length);
process.exit(fail ? 1 : 0);
