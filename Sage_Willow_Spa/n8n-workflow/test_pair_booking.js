// Harness for pair_slots.js and pair_book.js (the two-guest Code nodes).
//
//   node Sage_Willow_Spa/n8n-workflow/test_pair_booking.js
//
// Runs both node bodies with n8n's $() and this.helpers.httpRequest stubbed:
// the stub plays the one-person get-slots / book-appointment / cancel-booking
// paths of the same webhook. No network.
const fs = require('fs');
const path = require('path');

const load = (f) => fs.readFileSync(path.join(__dirname, f), 'utf8').replace('__SELF_URL__', 'https://self.test/webhook/x');
const SLOTS = load('pair_slots.js');
const BOOK = load('pair_book.js');
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;

let failed = 0;
const check = (label, got, want) => {
  const g = JSON.stringify(got), w = JSON.stringify(want);
  if (g === w) console.log('ok    ' + label);
  else { failed++; console.log('FAIL  ' + label + '\n        expected ' + w + '\n        got      ' + g); }
};

// ---- a fake calendar ---------------------------------------------------------------------
const W = { staffId: 's-winnie', name: 'winnie' }, N = { staffId: 's-nicky', name: 'Nicky' }, R = { staffId: 's-rocky', name: 'Rocky' };
const slot = (hhmm, therapists, dur = 90, sched = 'sch-deep') => {
  const [h, m] = hhmm.split(':').map(Number);
  const end = h * 60 + m + dur;
  const fmt = (x) => `${String(Math.floor(x / 60)).padStart(2, '0')}:${String(x % 60).padStart(2, '0')}`;
  const label = `${h % 12 === 0 ? 12 : h % 12}:${String(m).padStart(2, '0')} ${h >= 12 ? 'PM' : 'AM'}`;
  return { time: label, startDate: `2026-09-26T${hhmm}:00`, endDate: `2026-09-26T${fmt(end)}:00`, scheduleId: sched, availableTherapists: therapists };
};
// Deep Tissue 90: noon only Winnie (the Matt case), 2:00 Winnie + Nicky, 3:45 Winnie
const DEEP90 = [slot('12:00', [W]), slot('14:00', [W, N]), slot('14:45', [W, N]), slot('15:45', [W])];
// Swedish 60 for the guest: noon Rocky, 2:00 Nicky only, 3:45 Rocky
const SWED60 = [slot('12:00', [R], 60, 'sch-swed'), slot('14:00', [N], 60, 'sch-swed'), slot('15:45', [R], 60, 'sch-swed')];

function makeHelpers(opts = {}) {
  const log = [];
  const helpers = {
    httpRequest: async (req) => {
      const tool = req.headers.tool, b = req.body;
      log.push({ tool, body: b });
      if (tool === 'get-slots') {
        if (opts.slotsDown) return { success: false, error: 'Wix down' };
        let list = /swedish/i.test(b.serviceName || '') ? SWED60 : DEEP90;
        if (b.staffId) list = list.map((s) => ({ ...s, availableTherapists: s.availableTherapists.filter((t) => t.staffId === b.staffId) }))
          .filter((s) => s.availableTherapists.length);
        return { success: true, slots: list };
      }
      if (tool === 'book-appointment') {
        const n = log.filter((l) => l.tool === 'book-appointment').length;
        if (opts.guestFails && n === 2) return { success: false, error: 'Error booking service' };
        if (opts.guestThrows && n === 2) throw new Error('ETIMEDOUT');
        return { success: true, confirmed: !opts.pending, status: opts.pending ? 'PENDING' : 'CONFIRMED', bookingId: `bk-${n}` };
      }
      if (tool === 'cancel-booking') return { success: !opts.cancelFails };
      if (tool === 'get-services') {
        if (opts.pricesDown) throw new Error('ETIMEDOUT');
        const table = { 'deep tissue massage': [['60 min', 'USD 90'], ['90 min', 'USD 130']], 'swedish massage': [['60 min', 'USD 85'], ['90 min', 'USD 125']] };
        const rows = table[String(b.serviceName || '').toLowerCase()];
        return rows ? { success: true, catalog: false, services: [{ name: b.serviceName, pricingVariants: rows.map(([duration, price]) => ({ duration, price })) }] }
                    : { success: true, catalog: true, services: [] };
      }
      throw new Error('unexpected tool ' + tool);
    },
  };
  return { helpers, log };
}
const run = async (code, args, opts) => {
  const { helpers, log } = makeHelpers(opts);
  const $ = () => ({ first: () => ({ json: { args } }) });
  const out = await new AsyncFunction('$', code).call({ helpers }, $);
  return { out: out[0].json, log };
};

(async () => {
  // ---- slots for two -----------------------------------------------------------------------
  const base = { serviceName: 'Deep Tissue Massage', startDate: '2026-09-26', endDate: '2026-09-26', durationInMinutes: 90, guests: 2 };
  let { out, log } = await run(SLOTS, base);
  check('same massage: only times with two therapists', out.slots.map((s) => s.time), ['2:00 PM', '2:45 PM']);
  check('same massage: one lookup is enough', log.filter((l) => l.tool === 'get-slots').length, 1);
  check('same massage: census matches', out.availabilityByDay['2026-09-26'].afternoon.map((s) => s.time), ['2:00 PM', '2:45 PM']);
  check('noon (only one therapist) is not offered', out.slots.some((s) => s.time === '12:00 PM'), false);
  check('shape: success, guests 2, note', [out.success, out.guests, !!out.note], [true, 2, true]);
  check('no therapist names handed back', JSON.stringify(out).includes('winnie'), false);

  ({ out } = await run(SLOTS, { ...base, preferredTime: '12:00' }));
  check('asked for noon: honest "not available" + nearest', [out.requestedTimeAvailable, out.slots[0].time], [false, '2:00 PM']);

  ({ out, log } = await run(SLOTS, { ...base, guestServiceName: 'Swedish Massage', guestDurationInMinutes: 60 }));
  check('different massages: noon works (Winnie + Rocky), 2:00 does (Winnie + Nicky), 3:45 (Winnie + Rocky)', out.slots.map((s) => s.time), ['12:00 PM', '2:00 PM', '3:45 PM']);
  check('different massages: guest end time from the guest massage', out.slots[0].guestEndDate, '2026-09-26T13:00:00');
  check('different massages: two lookups', log.filter((l) => l.tool === 'get-slots').map((l) => l.body.serviceName), ['Deep Tissue Massage', 'Swedish Massage']);

  ({ out } = await run(SLOTS, { ...base, staffId: 's-nicky' }));
  check('caller asked for Nicky: her times with someone else free', out.slots.map((s) => s.time), ['2:00 PM', '2:45 PM']);

  ({ out } = await run(SLOTS, { ...base, startDate: '2026-09-26', timeOfDay: 'morning' }));
  check('nothing in the morning: says so, rest of day counted', [out.count, out.totalAvailableAllBands, /elsewhere/.test(out.noSlotsReason)], [0, 2, true]);

  ({ out } = await run(SLOTS, { ...base, guestServiceName: 'Swedish Massage', guestDurationInMinutes: 60, staffId: 's-rocky' }));
  check('nobody pairs up: no back-to-back, offer the team', [out.count, /back-to-back/.test(out.noSlotsReason)], [0, true]);

  ({ out } = await run(SLOTS, base));
  check('prices: same 90-minute massage twice, total from the tool', out.prices && [out.prices.you, out.prices.guest, out.prices.total], ['USD 130', 'USD 130', 'USD 260']);
  ({ out } = await run(SLOTS, { ...base, durationInMinutes: 60, guestServiceName: 'Swedish Massage', guestDurationInMinutes: 60 }));
  check('prices: Deep Tissue + Swedish an hour each = 175 (the web test said 215)', out.prices && out.prices.total, 'USD 175');
  ({ out } = await run(SLOTS, base, { pricesDown: true }));
  check('prices lookup down: times still come back, no prices', [out.success, out.count > 0, 'prices' in out], [true, true, false]);

  ({ out } = await run(SLOTS, base, { slotsDown: true }));
  check('calendar down: honest failure', [out.success, out.error], [false, 'Wix down']);
  ({ out } = await run(SLOTS, { guests: 2, startDate: '2026-09-26' }));
  check('missing args: failure, not a throw', out.success, false);

  // ---- booking for two -----------------------------------------------------------------------
  const bk = { serviceName: 'Deep Tissue Massage', startDate: '2026-09-26T14:00:00', endDate: '2026-09-26T15:30:00',
    firstName: 'John', lastName: 'Doe', guestFirstName: 'Jane', guestLastName: 'Doe', phone: '+14155550100', notes: 'Two deep tissue.' };
  ({ out, log } = await run(BOOK, bk));
  const books = log.filter((l) => l.tool === 'book-appointment').map((l) => l.body);
  check('both booked', [out.success, out.status, out.bookings.map((b) => b.bookingId)], [true, 'CONFIRMED', ['bk-1', 'bk-2']]);
  check('two different therapists', [books[0].staffId, books[1].staffId, books[0].staffRequested, books[1].staffRequested], ['s-winnie', 's-nicky', true, true]);
  check('guest booked under the guest name, caller phone', [books[1].firstName, books[1].lastName, books[1].phone], ['Jane', 'Doe', '+14155550100']);
  check('guest variant left to the slot length', 'variantId' in books[1], false);
  check('notes tie the two together', [/guest Jane Doe/.test(books[0].notes), /Guest of John Doe/.test(books[1].notes)], [true, true]);
  check('no guest args leak into the one-person calls', books.some((b) => 'guestFirstName' in b), false);

  ({ out, log } = await run(BOOK, { ...bk, startDate: '2026-09-26T12:00:00', endDate: '2026-09-26T13:30:00' }));
  check('noon for two (Matt case): refused, nothing booked', [out.success, log.some((l) => l.tool === 'book-appointment')], [false, false]);

  ({ out, log } = await run(BOOK, bk, { guestFails: true }));
  check("guest fails: caller's booking cancelled again", [out.success, out.rolledBack, log.find((l) => l.tool === 'cancel-booking').body.bookingId], [false, true, 'bk-1']);
  ({ out } = await run(BOOK, bk, { guestThrows: true }));
  check('guest call throws: still rolled back', [out.success, out.rolledBack], [false, true]);
  ({ out } = await run(BOOK, bk, { guestFails: true, cancelFails: true }));
  check('rollback fails: says so, names the stranded booking', [out.success, out.rolledBack, out.strandedBookingId], [false, false, 'bk-1']);

  ({ out } = await run(BOOK, bk, { pending: true }));
  check('request-first service: PENDING, told not to say all set', [out.success, out.status, out.requested, /never/.test(out.note)], [true, 'PENDING', true, true]);

  ({ out, log } = await run(BOOK, { ...bk, startDate: '2026-09-26T12:00:00', endDate: '2026-09-26T13:30:00', guestServiceName: 'Swedish Massage', guestDurationInMinutes: 60 }));
  const b2 = log.filter((l) => l.tool === 'book-appointment').map((l) => l.body);
  check('different massages at noon: Winnie + Rocky, guest ends at 1', [out.success, b2[0].staffId, b2[1].staffId, b2[1].serviceName, b2[1].endDate],
    [true, 's-winnie', 's-rocky', 'Swedish Massage', '2026-09-26T13:00:00']);

  ({ out, log } = await run(BOOK, { ...bk, staffId: 's-nicky', staffRequested: true }));
  const b3 = log.filter((l) => l.tool === 'book-appointment').map((l) => l.body);
  check('caller asked for Nicky: caller gets Nicky, guest someone else', [b3[0].staffId, b3[1].staffId], ['s-nicky', 's-winnie']);

  check('each one-person booking says one participant (no "undefined Participant(s)")', books.map((b) => b.numberOfParticipants), [1, 1]);
  for (const [gf, gl] of [['Wife', 'Doe'], ['Guest', 'Guest'], ['my partner', 'Doe'], ['John', 'Doe']]) {
    ({ out, log } = await run(BOOK, { ...bk, guestFirstName: gf, guestLastName: gl }));
    check(`stand-in guest name "${gf} ${gl}": nothing booked, sent back for the name`, [out.success, out.code, log.length], [false, 'guest_name_missing', 0]);
  }
  ({ out, log } = await run(BOOK, { ...bk, guestLastName: '' }));
  check('missing guest last name: nothing booked, same code', [out.success, out.code, log.length], [false, 'guest_name_missing', 0]);
  ({ out } = await run(BOOK, { ...bk, phone: '{{lead_phone}}' }));
  check('template phone: nothing booked', out.success, false);

  console.log('\n' + (failed ? 'FAILED ' + failed : 'all passed'));
  process.exit(failed ? 1 : 0);
})();
