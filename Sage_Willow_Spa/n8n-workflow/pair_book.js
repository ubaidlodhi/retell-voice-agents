// "Pair: Book Two Guests" - n8n Code node body (installed by
// _patch_pair_booking_and_approval.py, exercised by test_pair_booking.js).
//
// book_appointment with guestFirstName/guestLastName: the caller and their
// guest at the same time, each with their own therapist - both appointments or
// neither (Nicky, 2026-09-27).
//
//   1. Live check of that exact time for each massage (get-slots on this same
//      webhook, one-person path) and a pick of two DIFFERENT therapists.
//   2. Book the caller, then the guest (book-appointment on this same webhook,
//      one-person path - so service/variant/slot resolution, contacts and the
//      request-first handling are the ones every booking already goes through).
//   3. If the guest's booking fails, cancel the caller's again (cancel-booking),
//      so nobody is left with half a booking.
//
// The guest's variant is never passed: the one-person path picks it from the
// slot length, which is the honest signal (see "Resolve: Variant (Booking)").

const SELF = '__SELF_URL__';
// n8n Code nodes expose the request helper as this.helpers (older builds: $helpers).
const helpers = (this && this.helpers && this.helpers.httpRequest) ? this.helpers
  : (typeof $helpers !== 'undefined' ? $helpers : null);
const args = Object.assign({}, $('Parse Retell Payload').first().json.args || {});

const call = (tool, body) => helpers.httpRequest({
  method: 'POST', url: SELF, body, json: true, timeout: 90000,
  headers: { tool, 'Content-Type': 'application/json', 'User-Agent': 'curl/8.0' },
});
const fail = (error, extra) => [{ json: Object.assign({ success: false, guests: 2, error }, extra || {}) }];
const clean = (s) => String(s == null ? '' : s).trim();
const norm = (s) => clean(s).toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
const key = (d) => String(d || '').slice(0, 16);
const minutesBetween = (a, b) => {
  const p = (s) => /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(String(s || ''));
  const pa = p(a), pb = p(b);
  if (!pa || !pb) return null;
  const t = (m) => Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5]) / 60000;
  return Math.round(t(pb) - t(pa));
};

try {
  if (!helpers) return fail('The backend cannot make the lookup it needs (no request helper). Offer to have the team call them back.');
  const first = clean(args.firstName), last = clean(args.lastName);
  const gFirst = clean(args.guestFirstName), gLast = clean(args.guestLastName);
  const missing = [];
  if (!first) missing.push('firstName');
  if (!last) missing.push('lastName');
  if (!gFirst) missing.push('guestFirstName');
  if (!gLast) missing.push('guestLastName');
  if (!clean(args.phone)) missing.push('phone');
  if (!args.startDate) missing.push('startDate');
  if (!args.endDate) missing.push('endDate');
  if (!args.serviceName && !args.serviceId) missing.push('serviceName');
  if (missing.includes('guestFirstName') || missing.includes('guestLastName')) {
    return fail("Nothing was booked - guest_name_missing: ask for the guest's first and last name, then book again.",
      { code: 'guest_name_missing' });
  }
  if (missing.length) {
    return fail(`Nothing was booked - missing ${missing.join(', ')}. Ask the caller for anything you do not have, then try again.`);
  }
  // A stand-in is not a name (web tests 2026-09-28 booked "Wife Doe", "Guest Guest",
  // "Guest Doe" - the guest was never asked). Send Aria back for the real one.
  const STAND_IN = /^(the |my |your |his |her )?(guest|wife|husband|partner|friend|girlfriend|boyfriend|fianc[eé]e?|spouse|mom|mother|dad|father|sister|brother|son|daughter|unknown|none|n\/a|tbd)$/i;
  if (STAND_IN.test(gFirst) || `${gFirst} ${gLast}`.toLowerCase() === `${first} ${last}`.toLowerCase()) {
    return fail(`Nothing was booked - guest_name_missing: "${gFirst} ${gLast}" is not the guest's name. ` +
      "Ask for the guest's first and last name, then book again.", { code: 'guest_name_missing' });
  }
  const phone = clean(args.phone);
  if (phone.includes('{{') || phone.replace(/\D/g, '').length < 10) {
    return fail('Nothing was booked - the phone number is not a real number.');
  }
  const dur = minutesBetween(args.startDate, args.endDate);
  if (!dur || dur <= 0) return fail('Nothing was booked - startDate and endDate do not make a valid length.');

  const guestNamed = !!(args.guestServiceName || args.guestServiceId);
  const sameMassage = !guestNamed
    || (args.guestServiceId && args.serviceId && args.guestServiceId === args.serviceId)
    || (args.guestServiceName && norm(args.guestServiceName) === norm(args.serviceName));
  const guestDur = Number(args.guestDurationInMinutes) || dur;
  const guestService = sameMassage
    ? { serviceName: args.serviceName, ...(args.serviceId ? { serviceId: args.serviceId } : {}) }
    : { serviceName: args.guestServiceName || undefined, ...(args.guestServiceId ? { serviceId: args.guestServiceId } : {}) };
  const callerService = { serviceName: args.serviceName, ...(args.serviceId ? { serviceId: args.serviceId } : {}) };
  const wanted = args.staffRequested === true && args.staffId ? clean(args.staffId) : null;

  // ---- 1. who is available at that exact time, for each massage --------------------------
  const day = String(args.startDate).slice(0, 10);
  const q = (svc, minutes, extra) => Object.assign({ startDate: day, endDate: day, timeOfDay: 'any', limit: 1000,
    durationInMinutes: minutes }, svc, extra || {});
  const [A, B] = await Promise.all([
    call('get-slots', q(callerService, dur, wanted ? { staffId: wanted } : {})),
    call('get-slots', q(guestService, guestDur)),
  ]);
  if (!A || A.success !== true || !B || B.success !== true) {
    return fail('Nothing was booked - the calendar could not be read just now. Offer to have the team call them back.',
      { details: (A && A.error) || (B && B.error) || null });
  }
  const at = key(args.startDate);
  const sa = (A.slots || []).find((s) => key(s.startDate) === at);
  const sb = (B.slots || []).find((s) => key(s.startDate) === at);
  let pick = null;
  if (sa && sb) {
    for (const x of (sa.availableTherapists || [])) {
      if (pick || !x.staffId || (wanted && x.staffId !== wanted)) continue;
      const y = (sb.availableTherapists || []).find((t) => t.staffId && t.staffId !== x.staffId);
      if (y) pick = [x, y];
    }
  }
  if (!pick) {
    return fail('Nothing was booked - that time does not have two therapists available together any more. ' +
      'Call get_slots again with guests 2 and offer a time it returns, or offer to have the team call them back.');
  }

  // ---- 2. book the caller, then the guest ---------------------------------------------------
  const r1 = await call('book-appointment', Object.assign({}, callerService, {
    variantId: args.variantId || undefined,
    startDate: args.startDate, endDate: args.endDate, scheduleId: sa.scheduleId,
    firstName: first, lastName: last, phone, numberOfParticipants: 1,
    notes: [clean(args.notes), `Booked together with their guest ${gFirst} ${gLast}, same time, separate therapist.`].filter(Boolean).join(' '),
    staffId: pick[0].staffId, staffRequested: true,
    ...(Array.isArray(args.addOns) && args.addOns.length ? { addOns: args.addOns } : {}),
  }));
  if (!r1 || r1.success !== true) {
    return fail(`Nothing was booked - the first appointment did not go through${r1 && r1.error ? `: ${r1.error}` : ''}.`);
  }

  // A thrown call (timeout, network) counts as a failed guest booking, so the
  // caller's is still undone below rather than left behind.
  let r2;
  try {
    r2 = await call('book-appointment', Object.assign({}, guestService, {
      startDate: args.startDate, endDate: sb.endDate, scheduleId: sb.scheduleId,
      firstName: gFirst, lastName: gLast, phone, numberOfParticipants: 1,
      notes: [`Guest of ${first} ${last}, booked together at the same time.`, clean(args.guestNotes)].filter(Boolean).join(' '),
      staffId: pick[1].staffId, staffRequested: true,
      ...(Array.isArray(args.guestAddOns) && args.guestAddOns.length ? { addOns: args.guestAddOns } : {}),
    }));
  } catch (e) {
    r2 = { success: false, error: String(e && e.message || e).slice(0, 160) };
  }

  // ---- 3. both or neither --------------------------------------------------------------------
  if (!r2 || r2.success !== true) {
    let rolledBack = false;
    try {
      const c = await call('cancel-booking', { bookingId: r1.bookingId, phone });
      rolledBack = !!(c && c.success === true);
    } catch (e) { rolledBack = false; }
    return fail(rolledBack
      ? "Nothing was booked - the guest's appointment did not go through, so the caller's was cancelled again. Offer to have the team call them back to set it up."
      : "The guest's appointment did not go through and the caller's could not be undone. Offer to have the team call them back - they need to sort it out.",
      { rolledBack, ...(rolledBack ? {} : { strandedBookingId: r1.bookingId }), guestError: (r2 && r2.error) || null });
  }

  const pending = [r1, r2].some((r) => r.status === 'PENDING');
  return [{ json: {
    success: true,
    guests: 2,
    confirmed: !pending && r1.confirmed === true && r2.confirmed === true,
    status: pending ? 'PENDING' : 'CONFIRMED',
    ...(pending ? { requested: true,
      note: 'At least one of these massages is booked by request - the spa has to approve it. Tell the caller it is a request, never "you\'re all set".' } : {}),
    bookings: [
      { who: 'caller', name: `${first} ${last}`, bookingId: r1.bookingId, status: r1.status, startDate: args.startDate, endDate: args.endDate },
      { who: 'guest', name: `${gFirst} ${gLast}`, bookingId: r2.bookingId, status: r2.status, startDate: args.startDate, endDate: sb.endDate },
    ],
    message: `Booked ${first} ${last} and their guest ${gFirst} ${gLast} side by side at ${sa.time}, each with their own therapist.`,
  } }];
} catch (e) {
  return fail(`Booking for two could not be completed (${String(e && e.message || e).slice(0, 160)}). ` +
    'Check before saying anything is booked - offer to have the team call them back.');
}
