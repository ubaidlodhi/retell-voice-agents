// "Format: Get Booking Response" - n8n Code node body (installed by
// _patch_v67_contacts_recent_bookings.py, exercised by test_get_booking_format.js).
//
// Upcoming bookings first (soonest first), then the ones that started in the
// last 24 hours (Ubaid, 2026-10-01: "future bookings but also past 1 day
// bookings as well"). A recent one is marked timing "already happened" so Aria
// can talk about a visit that just took place without offering to cancel or
// move it - the cancel and reschedule paths refuse a booking that has started.

const data = $input.first().json;

if (data.message || data.details) {
  return [{ json: { success: false, foundFlag: 'no', error: data.message || 'Failed to retrieve booking' } }];
}

const now = Date.now();
const RECENT_MS = 24 * 60 * 60 * 1000;

const DOW_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
function localDayOfWeek(localIso) {
  if (!localIso) return null;
  const datePart = String(localIso).split('T')[0];
  const m = datePart.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!m) return null;
  const y = +m[1], mo = +m[2], d = +m[3];
  return DOW_NAMES[new Date(Date.UTC(y, mo - 1, d)).getUTCDay()];
}

const enriched = (data.bookings || []).map(b => {
  const slot = b.bookedEntity?.slot;
  const startDate = slot?.startDate;
  const endDate = slot?.endDate;
  const startMs = startDate ? Date.parse(startDate) : NaN;
  const endMs = endDate ? Date.parse(endDate) : NaN;
  const durationMinutes = (isFinite(startMs) && isFinite(endMs))
    ? Math.round((endMs - startMs) / 60000)
    : null;
  const hoursUntilStart = isFinite(startMs)
    ? Math.round(((startMs - now) / 3600000) * 10) / 10
    : null;
  const within24h = hoursUntilStart !== null && hoursUntilStart > 0 && hoursUntilStart < 24;

  return {
    bookingId: b.id,
    status: b.status,
    timing: startMs > now ? 'upcoming' : 'already happened',
    revision: b.revision,
    serviceId: slot?.serviceId,
    serviceName: b.bookedEntity?.title || null,
    scheduleId: slot?.scheduleId,
    staffId: slot?.resource?.id || null,
    staffName: slot?.resource?.name || null,
    timezone: slot?.timezone,
    locationId: slot?.location?.id,
    locationType: slot?.location?.locationType,
    startDate,
    endDate,
    dayOfWeek: localDayOfWeek(startDate),
    durationMinutes,
    hoursUntilStart,
    withinCancellationWindow: within24h,
    withinCancellationWindowFlag: within24h ? 'yes' : 'no',
    firstName: b.contactDetails?.firstName,
    lastName: b.contactDetails?.lastName,
    phone: b.contactDetails?.phone,
    email: b.contactDetails?.email ?? null,
    createdDate: b.createdDate,
    _startMs: startMs
  };
}).filter(b => isFinite(b._startMs));

const upcoming = enriched.filter(b => b._startMs > now).sort((a, b) => a._startMs - b._startMs);
const recent = enriched.filter(b => b._startMs <= now && b._startMs > now - RECENT_MS)
  .sort((a, b) => b._startMs - a._startMs);
const bookings = [...upcoming, ...recent].map(({ _startMs, ...rest }) => rest);

const found = bookings.length > 0;
let note;
if (recent.length && upcoming.length) {
  note = 'Upcoming bookings come first. The ones with timing "already happened" started in the last 24 hours and are over - '
    + 'never offer to cancel or move them; mention one only if the caller is asking about a recent visit.';
} else if (recent.length) {
  note = 'This customer has NO upcoming booking. The booking listed already happened (it started in the last 24 hours) - '
    + 'say so plainly, never offer to cancel or move it, and offer to book a new appointment if they want one.';
}

return [{ json: {
  success: true,
  foundFlag: found ? 'yes' : 'no',
  count: bookings.length,
  upcomingCount: upcoming.length,
  recentPastCount: recent.length,
  ...(note ? { note } : {}),
  bookings: found ? bookings : [],
  message: found ? undefined : 'No upcoming bookings found for this customer'
} }];
