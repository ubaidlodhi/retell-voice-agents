// "Pair: Slots For Two" - n8n Code node body (installed by
// _patch_pair_booking_and_approval.py, exercised by test_pair_booking.js).
//
// get_slots with guests: 2 - two people at the same time, each with their own
// therapist (Nicky, 2026-09-27: "Option 1"; no back-to-back, a request instead
// when nothing lines up). Only times when two DIFFERENT therapists are
// available together come back: one who does the caller's massage, another who
// does the guest's.
//
// It asks this same webhook for the ordinary one-person availability of each
// massage (tool get-slots, no guests arg, so the call takes the normal path),
// then pairs the two lists up. All the Wix handling - service resolution,
// durations, therapists per slot - stays in the one-person chain.

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
const norm = (s) => String(s || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();

// "14:00", "2 PM", "2:30pm" -> "HH:MM" (same rules as Validate: Slots Args)
function normalizePreferredTime(v) {
  if (v === undefined || v === null || v === '') return null;
  const s = String(v).trim().toLowerCase();
  let m = s.match(/^(\d{1,2})(?::(\d{2}))?\s*([ap])\.?\s*m\.?$/);
  if (m) {
    let h = parseInt(m[1], 10);
    const mi = m[2] ? parseInt(m[2], 10) : 0;
    if (h < 1 || h > 12 || mi > 59) return null;
    if (h === 12) h = 0;
    if (m[3] === 'p') h += 12;
    return `${String(h).padStart(2, '0')}:${String(mi).padStart(2, '0')}`;
  }
  m = s.match(/^(\d{1,2}):(\d{2})(?::\d{2})?$/);
  if (m) {
    const h = parseInt(m[1], 10), mi = parseInt(m[2], 10);
    if (h > 23 || mi > 59) return null;
    return `${String(h).padStart(2, '0')}:${String(mi).padStart(2, '0')}`;
  }
  return null;
}
const inBand = (hour, band) => band === 'morning' ? hour >= 10 && hour < 12
  : band === 'afternoon' ? hour >= 12 && hour < 17
  : band === 'evening' ? hour >= 17 && hour < 20
  : hour >= 10 && hour < 20;
const bandOf = (hour) => hour >= 10 && hour < 12 ? 'morning' : hour >= 12 && hour < 17 ? 'afternoon'
  : hour >= 17 && hour < 20 ? 'evening' : null;
const key = (d) => String(d || '').slice(0, 16);   // "2026-09-26T12:00"
const minuteOf = (d) => { const m = /T(\d{2}):(\d{2})/.exec(String(d || '')); return m ? Number(m[1]) * 60 + Number(m[2]) : null; };

try {
  if (!helpers) return fail('The backend cannot make the lookup it needs (no request helper). Offer to have the team call them back.');
  const missing = [];
  if (!args.serviceName && !args.serviceId) missing.push('serviceName');
  if (!args.startDate) missing.push('startDate');
  if (!args.endDate) missing.push('endDate');
  const dur = Number(args.durationInMinutes);
  if (!dur) missing.push('durationInMinutes');
  if (missing.length) return fail(`Missing ${missing.join(', ')}.`);

  const guestDur = Number(args.guestDurationInMinutes) || dur;
  const guestNamed = !!(args.guestServiceName || args.guestServiceId);
  const sameMassage = !guestNamed
    || (args.guestServiceId && args.serviceId && args.guestServiceId === args.serviceId)
    || (args.guestServiceName && norm(args.guestServiceName) === norm(args.serviceName));
  const sameAsCaller = sameMassage && guestDur === dur;

  const base = { startDate: args.startDate, endDate: args.endDate, timeOfDay: 'any', limit: 1000 };
  const callerQ = Object.assign({}, base, { serviceName: args.serviceName, durationInMinutes: dur },
    args.serviceId ? { serviceId: args.serviceId } : {}, args.staffId ? { staffId: args.staffId } : {});
  const guestQ = Object.assign({}, base, { durationInMinutes: guestDur },
    sameMassage ? { serviceName: args.serviceName, ...(args.serviceId ? { serviceId: args.serviceId } : {}) }
                : { serviceName: args.guestServiceName || undefined, ...(args.guestServiceId ? { serviceId: args.guestServiceId } : {}) });
  // One lookup does for both when the massages match and nobody asked for a therapist.
  const oneLookup = sameAsCaller && !args.staffId;

  // Prices come back with the times so Aria reads a total instead of adding one up
  // (web tests 2026-09-28: Deep Tissue + Swedish, an hour each, came out 215 instead
  // of 175 - the model picked the wrong length's price). A failed price lookup only
  // drops the prices; it never blocks the times.
  const priceOf = async (serviceName, minutes) => {
    if (!serviceName) return null;
    try {
      const r = await call('get-services', { serviceName });
      const s = r && r.success && !r.catalog && Array.isArray(r.services) ? r.services[0] : null;
      if (!s) return null;
      const v = (s.pricingVariants || []).find((x) => String(x.duration) === `${minutes} min`);
      const label = v ? v.price : (s.price || null);
      const num = label ? Number(String(label).replace(/[^0-9.]/g, '')) : NaN;
      return isFinite(num) && num > 0 ? { label: `USD ${num}`, num } : null;
    } catch (e) { return null; }
  };
  const guestServiceName = sameMassage ? args.serviceName : args.guestServiceName;

  const [A, B0, pCaller, pGuest] = await Promise.all([
    call('get-slots', callerQ),
    oneLookup ? Promise.resolve(null) : call('get-slots', guestQ),
    priceOf(args.serviceName, dur),
    sameAsCaller ? Promise.resolve(null) : priceOf(guestServiceName, guestDur),
  ]);
  const B = oneLookup ? A : B0;
  const pG = sameAsCaller ? pCaller : pGuest;
  const prices = pCaller && pG
    ? { you: pCaller.label, guest: pG.label, total: `USD ${pCaller.num + pG.num}`,
        note: 'Massages only - add any add-ons on top. Read this total; never add it up yourself.' }
    : null;
  if (!A || A.success !== true) return fail((A && A.error) || 'Could not read availability for the first massage.');
  if (!B || B.success !== true) return fail((B && B.error) || "Could not read availability for the guest's massage.");

  const bByTime = new Map((B.slots || []).map((s) => [key(s.startDate), s]));
  const pairs = [];
  for (const s of (A.slots || [])) {
    const g = bByTime.get(key(s.startDate));
    if (!g) continue;
    const ta = (s.availableTherapists || []).map((t) => t.staffId).filter(Boolean);
    const tb = (g.availableTherapists || []).map((t) => t.staffId).filter(Boolean);
    if (!ta.some((x) => tb.some((y) => y !== x))) continue;   // no two different therapists
    pairs.push({
      time: s.time, startDate: s.startDate, endDate: s.endDate, scheduleId: s.scheduleId,
      guestEndDate: g.endDate, guestScheduleId: g.scheduleId,
      _date: String(s.startDate).slice(0, 10), _min: minuteOf(s.startDate),
    });
  }
  pairs.sort((x, y) => String(x.startDate).localeCompare(String(y.startDate)));

  const timeOfDay = ['morning', 'afternoon', 'evening'].includes(String(args.timeOfDay || '').toLowerCase())
    ? String(args.timeOfDay).toLowerCase() : 'any';
  const earliestFirst = args.earliestFirst === true || String(args.earliestFirst).toLowerCase() === 'true';
  const preferredTime = normalizePreferredTime(args.preferredTime);
  const limit = Number(args.limit) > 0 ? Number(args.limit) : (earliestFirst ? 3 : 6);

  const inWindow = pairs.filter((p) => inBand(Math.floor(p._min / 60), timeOfDay));
  let requestedTimeAvailable = null, prefMin = null;
  if (preferredTime) {
    const [ph, pm] = preferredTime.split(':').map(Number);
    prefMin = ph * 60 + pm;
    requestedTimeAvailable = pairs.some((p) => p._min === prefMin);
  }
  let chosen;
  if (!inWindow.length) chosen = [];
  else if (preferredTime) {
    chosen = inWindow.slice().sort((x, y) => Math.abs(x._min - prefMin) - Math.abs(y._min - prefMin)
      || String(x.startDate).localeCompare(String(y.startDate))).slice(0, limit)
      .sort((x, y) => String(x.startDate).localeCompare(String(y.startDate)));
  } else if (earliestFirst || inWindow.length <= limit) chosen = inWindow.slice(0, limit);
  else {
    const idx = [];
    for (let i = 0; i < limit; i++) idx.push(Math.round((i * (inWindow.length - 1)) / (limit - 1)));
    chosen = [...new Set(idx)].map((i) => inWindow[i]);
  }
  const strip = ({ _date, _min, ...clean }) => clean;

  // Census: every paired time, by day and part of day (times only - small).
  const availabilityByDay = {};
  for (const p of pairs) {
    const band = bandOf(Math.floor(p._min / 60));
    if (!band) continue;
    if (!availabilityByDay[p._date]) availabilityByDay[p._date] = { morning: [], afternoon: [], evening: [], complete: true };
    availabilityByDay[p._date][band].push({ time: p.time, startDate: p.startDate });
  }

  let noSlotsReason;
  if (!pairs.length) {
    noSlotsReason = 'No time in this window has two therapists available together. Do not offer back-to-back times. ' +
      'Offer to have the team call them to set it up, or look at another day they want.';
  } else if (!inWindow.length) {
    noSlotsReason = `Nothing in the ${timeOfDay} for two, but ${pairs.length} time(s) elsewhere in the day - offer from availabilityByDay.`;
  }

  return [{ json: {
    success: true,
    guests: 2,
    note: 'Two appointments side by side. Every time listed has two different therapists available together, one for each guest.',
    mode: preferredTime ? 'nearest' : (earliestFirst ? 'earliest_first' : 'spread'),
    count: chosen.length,
    totalAvailable: inWindow.length,
    totalAvailableAllBands: pairs.length,
    truncated: chosen.length < inWindow.length,
    requestedTimeAvailable,
    ...(noSlotsReason ? { noSlotsReason } : {}),
    filterApplied: { timeOfDay, earliestFirst, preferredTime, limit, staffId: args.staffId || null,
      guestService: sameMassage ? 'same as caller' : (args.guestServiceName || args.guestServiceId), guestDurationInMinutes: guestDur },
    slots: chosen.map(strip),
    slotsAreSample: chosen.length < inWindow.length,
    availabilityByDay,
    availabilityByDayComplete: true,
    ...(prices ? { prices } : {}),
  } }];
} catch (e) {
  return fail(`Could not check times for two: ${String(e && e.message || e).slice(0, 200)}`);
}
