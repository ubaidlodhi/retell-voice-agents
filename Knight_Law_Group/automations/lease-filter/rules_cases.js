// One row per rule. retell = [route, bad_reason] from node-code-classify (in-call).
// n8n = [lead_status, bad_lead_reason] from the n8n Classify Lead node (final, sent to GHL).
const C = (label, make, pt, year, possess, retell, n8n, ptSeed) => ({ label, make, pt, year, possess, retell, n8n, ptSeed: ptSeed || '' });
const RET = ['retainer', 'N/A'], NONRET = ['non_retainer', 'N/A'];
const N_RET = ['Retainer Lead', 'N/A'], N_NON = ['Non-Retainer Lead', 'N/A'];
const ARB = ['Bad Lead', 'Requires Arbitration'];
module.exports = [
  C('leased Honda 2023 -> arbitration', 'Honda', 'leased', 2023, true, ['bad', 'arbitration_lease'], ARB),
  C('leased Acura 2023 -> arbitration', 'Acura', 'leased', 2023, true, ['bad', 'arbitration_lease'], ARB),
  C('leased BMW 2023 -> arbitration', 'BMW', 'leased', 2023, true, ['bad', 'arbitration_lease'], ARB),
  C('leased Mercedes-Benz 2023 -> arbitration', 'Mercedes-Benz', 'leased', 2023, true, ['bad', 'arbitration_lease'], ARB),
  C('leased "Mercedes" alias -> arbitration', 'Mercedes', 'leased', 2023, true, ['bad', 'arbitration_lease'], ARB),
  C('leased MINI 2023 -> arbitration', 'MINI', 'leased', 2023, true, ['bad', 'arbitration_lease'], ARB),
  C('leased Ford 2023 -> retainer', 'Ford', 'leased', 2023, true, RET, N_RET),
  C('leased Toyota 2023 -> non-retainer', 'Toyota', 'leased', 2023, true, NONRET, N_NON),
  C('leased Ford not in possession -> possession', 'Ford', 'leased', 2023, false, ['bad', 'not_in_possession'], ['Bad Lead', 'Not in possession of vehicle']),
  C('leased Honda 2019 -> arbitration beats year', 'Honda', 'leased', 2019, true, ['bad', 'arbitration_lease'], ARB),
  C('buyout Honda 2023 -> arbitration', 'Honda', 'lease_buyout', 2023, true, ['bad', 'arbitration_buyout'], ARB),
  C('buyout Acura 2023 -> arbitration', 'Acura', 'lease_buyout', 2023, true, ['bad', 'arbitration_buyout'], ARB),
  C('buyout BMW 2023 -> non-retainer', 'BMW', 'lease_buyout', 2023, true, NONRET, N_NON),
  C('buyout Mercedes-Benz 2023 -> non-retainer', 'Mercedes-Benz', 'lease_buyout', 2023, true, NONRET, N_NON),
  C('buyout MINI 2023 -> non-retainer', 'MINI', 'lease_buyout', 2023, true, NONRET, N_NON),
  C('buyout BMW 2019 -> year first', 'BMW', 'lease_buyout', 2019, true, ['bad', 'vehicle_year'], ['Bad Lead', 'Vehicle year']),
  C('buyout Ford 2023 -> retainer', 'Ford', 'lease_buyout', 2023, true, RET, N_RET),
  C('purchased BMW 2023 -> retainer (unchanged)', 'BMW', 'purchased', 2023, true, RET, N_RET),
  C('purchased Honda 2023 -> non-retainer (unchanged)', 'Honda', 'purchased', 2023, true, NONRET, N_NON),
  C('purchased Tesla 2023 -> arbitration', 'Tesla', 'purchased', 2023, true, ['bad', 'arbitration_tesla'], ARB),
  C('leased Tesla 2023 -> tesla arbitration', 'Tesla', 'leased', 2023, true, ['bad', 'arbitration_tesla'], ARB),
  C('Tesla 2019 -> year beats tesla', 'Tesla', 'purchased', 2019, true, ['bad', 'vehicle_year'], ['Bad Lead', 'Vehicle year']),
  C('Tesla not in possession -> arbitration (Tesla not opted in)', 'Tesla', 'purchased', 2023, false, ['bad', 'arbitration_tesla'], ARB),
  C('purchase type unknown BMW -> retainer (old behaviour)', 'BMW', '', 2023, true, RET, N_RET),
  C('purchase type unknown Honda -> non-retainer', 'Honda', '', 2023, true, NONRET, N_NON),
  C('only GHL seed "Leased" Honda -> arbitration', 'Honda', '', 2023, true, ['bad', 'arbitration_lease'], ARB, 'Leased'),
  C('call answer beats seed (buyout over Purchased) BMW', 'BMW', 'lease_buyout', 2023, true, NONRET, N_NON, 'Purchased'),
];
