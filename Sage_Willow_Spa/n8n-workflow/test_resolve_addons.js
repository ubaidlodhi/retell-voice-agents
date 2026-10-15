// node Sage_Willow_Spa/n8n-workflow/test_resolve_addons.js
// Runs resolve_addons.js (the "Resolve: Add-ons (Booking)" Code node) with $(), $input and
// this.helpers.httpRequest stubbed. Catalog and add-on names are the live Deep Tissue ones
// (execution 2559, 2026-10-14). No network.
const fs = require('fs');
const path = require('path');
const SRC = fs.readFileSync(path.join(__dirname, 'resolve_addons.js'), 'utf8').replace('__SELF_URL__', 'https://self.test/webhook/x');
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;

const DEEP = 'c81dcbf4-8545-49f0-a53b-cb0cdf858556';
const GROUP = '38a3158c-3d46-4e9a-b4f0-c91b1eebdf71';
const AROMA = '29159dc3-cb4b-4bd4-b250-a0e43944bc75', FOOT = '96590711-db71-4405-bac4-e0e62bf88b50';
const HOT = '19225223-333c-4480-a650-1e62c3573707', EYE = '87baf30b-629f-4289-b979-3daa96388840';
const HERBAL = '27409857-3047-44a6-a2ad-62d76b28142a';
const CATALOG = { services: [
  { id: DEEP, name: 'Deep Tissue Massage', addOnGroups: [{ id: GROUP, name: 'add-ons', addOnIds: [AROMA, FOOT, HOT, EYE, HERBAL] }] },
  { id: 'prenatal', name: 'Prenatal Massage', addOnGroups: [] },
] };
const GET_SERVICES = { success: true, count: 1, services: [{ id: DEEP, name: 'Deep Tissue Massage', availableAddOns: [
  { id: AROMA, name: 'Aromatherapy', groupIds: [GROUP] }, { id: FOOT, name: 'Foot Scrub', groupIds: [GROUP] },
  { id: HOT, name: 'Hot Stone Enhancement ', groupIds: [GROUP] }, { id: EYE, name: 'Steam Eye Mask', groupIds: [GROUP] },
  { id: HERBAL, name: 'Herbal Therapy Enhancement', groupIds: [GROUP] },
] }] };

async function run(args, opts = {}) {
  const calls = [];
  const helpers = { httpRequest: async (req) => {
    calls.push(req.headers.tool);
    if (opts.getServicesFails) throw new Error('timeout');
    return GET_SERVICES;
  } };
  const prev = { tool: 'book-appointment', _valid: true, args: Object.assign({ serviceName: 'Deep Tissue Massage', serviceId: DEEP }, args) };
  const $ = (name) => { if (name !== 'Wix: Services (Booking)') throw new Error(name); return { first: () => ({ json: opts.catalog || CATALOG }) }; };
  const out = await new AsyncFunction('$input', '$', SRC).call({ helpers }, { first: () => ({ json: opts.prev || prev }) }, $);
  return { j: out[0].json, calls };
}

let failed = 0;
const check = (label, ok, got) => { if (!ok) failed++; console.log(`${ok ? 'ok  ' : 'FAIL'} ${label}${ok ? '' : '\n       got ' + JSON.stringify(got).slice(0, 400)}`); };

(async () => {
  // 1. The Mari call: one character dropped, no name (what the published agent sends today).
  let { j, calls } = await run({ addOns: [{ id: '29159dc3-cb4b-4bd-b250-a0e43944bc75', groupId: GROUP }] });
  check('call_dde463dd id is corrected to Aromatherapy', j._valid !== false && JSON.stringify(j.args.addOns) === JSON.stringify([{ id: AROMA, groupId: GROUP }]), j);
  check('  ...by closest id, 1 edit', j._addOnResolution.resolved[0].how === 'id:closest' && j._addOnResolution.resolved[0].edits === 1, j._addOnResolution);

  // 2. Exact id, no name: nothing to fix, no extra lookup.
  ({ j, calls } = await run({ addOns: [{ id: EYE, groupId: GROUP }] }));
  check('exact id passes, no get-services call', j.args.addOns[0].id === EYE && calls.length === 0, { j, calls });

  // 3. Name wins over a valid-but-wrong id (caller said aromatherapy, id copied from Foot Scrub).
  ({ j } = await run({ addOns: [{ name: 'Aromatherapy', id: FOOT, groupId: GROUP }] }));
  check('name wins over a wrong id', j.args.addOns[0].id === AROMA && j._addOnResolution.resolved[0].idCorrected === true, j);

  // 4. Name only, loose wording.
  ({ j } = await run({ addOns: [{ name: 'hot stone' }, { name: 'herbal therapy' }] }));
  check('loose names resolve, groupId filled', JSON.stringify(j.args.addOns) === JSON.stringify([{ id: HOT, groupId: GROUP }, { id: HERBAL, groupId: GROUP }]), j);

  // 5. Wrong groupId copied: replaced by the service's own group.
  ({ j } = await run({ addOns: [{ name: 'Foot Scrub', id: FOOT, groupId: '38a3158c-3d46-4e9a-b4f0-c91b1eebdf7' }] }));
  check('bad groupId replaced', j.args.addOns[0].groupId === GROUP, j);

  // 6. Same add-on twice: booked once.
  ({ j } = await run({ addOns: [{ name: 'Aromatherapy', id: AROMA, groupId: GROUP }, { id: AROMA, groupId: GROUP }] }));
  check('duplicate collapsed', j.args.addOns.length === 1, j);

  // 7. Garbage id, no name: error naming the real add-ons (Aria offers the callback, as before).
  ({ j } = await run({ addOns: [{ id: GROUP, groupId: GROUP }] }));
  check('unmatchable -> invalid with real names', j._valid === false && /Aromatherapy, Foot Scrub/.test(j._validationError) && /Nothing was booked/.test(j._validationError), j._validationError);

  // 8. Unknown name.
  ({ j } = await run({ addOns: [{ name: 'Cupping', id: '' }] }));
  check('unknown name -> invalid', j._valid === false && /"Cupping"/.test(j._validationError), j._validationError);

  // 9. get-services down: the id slip is still corrected from the catalog alone.
  ({ j } = await run({ addOns: [{ id: '29159dc3-cb4b-4bd-b250-a0e43944bc75', groupId: GROUP }] }, { getServicesFails: true }));
  check('lookup down: id slip still corrected', j.args.addOns[0].id === AROMA && j._addOnResolution.namesFrom === 'get-services failed', j);

  // 10. Catalog and lookup both unavailable: untouched, Wix judges (old behaviour).
  ({ j } = await run({ addOns: [{ id: 'x', groupId: 'y' }] }, { catalog: { message: 'down' }, getServicesFails: true }));
  check('both sources down: passes through untouched', j._valid !== false && j.args.addOns[0].id === 'x', j);

  // 11. No add-ons / already invalid: untouched.
  ({ j, calls } = await run({}));
  check('no add-ons: untouched, no call', !j._addOnResolution && calls.length === 0, j);
  ({ j } = await run({}, { prev: { _valid: false, _validationError: 'earlier', args: { addOns: [{ id: 'x' }] } } }));
  check('earlier failure passes straight through', j._valid === false && j._validationError === 'earlier', j);

  // 12. A service with no add-ons, add-on sent anyway: the catalog says none, the lookup says none.
  ({ j } = await run({ serviceName: 'Prenatal Massage', serviceId: 'prenatal', addOns: [{ name: 'Aromatherapy', id: AROMA }] }, { getServicesFails: true }));
  check('service without add-ons: untouched for Wix to judge', j._valid !== false && j._addOnResolution.source === 'catalog-unavailable', j);

  console.log(failed ? `${failed} FAILED` : 'all passed');
  process.exit(failed ? 1 : 0);
})();
