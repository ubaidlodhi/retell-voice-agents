// node Sage_Willow_Spa/n8n-workflow/test_get_booking_format.js
// Runs get_booking_format.js (the "Format: Get Booking Response" Code node) on stub Wix data.
const fs = require('fs');
const path = require('path');
const src = fs.readFileSync(path.join(__dirname, 'get_booking_format.js'), 'utf8');

const H = 3600 * 1000;
const iso = (ms) => new Date(ms).toISOString();
const bk = (id, offsetH, extra) => Object.assign({
  id, status: 'CONFIRMED', revision: '2', createdDate: iso(Date.now() - 48 * H),
  bookedEntity: { title: 'Signature Massage', slot: {
    serviceId: 's1', scheduleId: 'sc1', startDate: iso(Date.now() + offsetH * H),
    endDate: iso(Date.now() + (offsetH + 1) * H), resource: { id: 'st1', name: 'winnie' } } },
  contactDetails: { firstName: 'Jane', lastName: 'Doe', phone: '+14155550100' },
}, extra || {});

function run(json) {
  const fn = new Function('$input', `return (async () => {${src}\n})();`);
  return fn({ first: () => ({ json }) }).then(r => r[0].json);
}

let fails = 0;
const check = (name, ok, got) => { if (!ok) fails++; console.log(`${ok ? 'PASS' : 'FAIL'} ${name}${ok ? '' : ' -> ' + JSON.stringify(got)}`); };

(async () => {
  // upcoming out of order, one 5h ago, one 30h ago (too old), one 2 weeks away
  let r = await run({ bookings: [bk('far', 24 * 14), bk('old', -30), bk('recent', -5), bk('soon', 3)] });
  check('ids: upcoming soonest first, then recent; >24h dropped', JSON.stringify(r.bookings.map(b => b.bookingId)) === '["soon","far","recent"]', r.bookings.map(b => b.bookingId));
  check('timing labels', r.bookings.map(b => b.timing).join('|') === 'upcoming|upcoming|already happened', r.bookings.map(b => b.timing));
  check('counts', r.count === 3 && r.upcomingCount === 2 && r.recentPastCount === 1 && r.foundFlag === 'yes', r);
  check('mixed note present', /Upcoming bookings come first/.test(r.note || ''), r.note);
  check('recent not in cancellation window', r.bookings[2].withinCancellationWindowFlag === 'no', r.bookings[2]);
  check('soon in cancellation window', r.bookings[0].withinCancellationWindowFlag === 'yes', r.bookings[0]);
  check('no _startMs leak', r.bookings.every(b => !('_startMs' in b)), r.bookings[0]);

  r = await run({ bookings: [bk('recent', -2)] });
  check('only recent: found, NO upcoming note', r.foundFlag === 'yes' && r.upcomingCount === 0 && /NO upcoming booking/.test(r.note || ''), r);

  r = await run({ bookings: [bk('old', -25)] });
  check('only >24h old: not found, original message', r.foundFlag === 'no' && r.count === 0 && r.message === 'No upcoming bookings found for this customer' && !r.note, r);

  r = await run({ bookings: [bk('soon', 3)] });
  check('only upcoming: no note (same as before)', r.foundFlag === 'yes' && r.count === 1 && !('note' in r), r);

  r = await run({ bookings: [] });
  check('empty (Mock Empty Bookings)', r.foundFlag === 'no' && r.count === 0, r);

  r = await run({ message: 'boom', details: {} });
  check('Wix error passes through', r.success === false && r.error === 'boom', r);

  r = await run({ bookings: [bk('nodate', 3, { bookedEntity: { title: 'X', slot: {} } })] });
  check('booking without a start is dropped', r.count === 0, r);

  console.log(fails ? `${fails} FAILED` : 'all passed');
  process.exit(fails ? 1 : 0);
})();
