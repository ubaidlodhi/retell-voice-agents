"""
Build script for the Sage & Willow Spa n8n workflow.

Single source of truth for the workflow at
https://automation.aiemply.com/webhook/retell-wix.
Running this script writes a fully importable workflow JSON to
`Retell AI ↔ Wix Bookings _ Production v2.json` — no existing file required.

Run:  py -X utf8 _modify_n8n_workflow.py
"""
from __future__ import annotations
import json
from pathlib import Path

WF_PATH = Path(__file__).parent / "Retell AI ↔ Wix Bookings _ Production v2.json"

# n8n credential references (replace if importing into a different n8n instance)
WIX_CREDENTIAL_ID   = 'wLpWbblaihcY4xnw'
WIX_CREDENTIAL_NAME = 'Test: Wix Sage Site'
SMTP_CREDENTIAL_ID  = 'm0mbibKf6il36id5'
SMTP_CREDENTIAL_NAME = 'SMTP account'

# Flag-callback email destination + sender identity
CALLBACK_RECIPIENT = 'engineering@aiemply.com'
FROM_EMAIL         = 'Aria <engineering@aiemply.com>'


# -----------------------------------------------------------------------------
# JS code constants (inlined into Code-type nodes)
# -----------------------------------------------------------------------------

PARSE_RETELL_PAYLOAD_JS = r"""// Retell tool-call webhook normalizer
//
// With `args_at_root: true` (the production-validated default), Retell sends
// LLM-extracted args SPREAD AT THE BODY ROOT — there is no `body.args` wrapper
// and no `body.call` object. Tool routing is via the `tool` HTTP header.
//
// This parser is defensive: it also still handles the older `args_at_root: false`
// shape (`body = { args: {...}, call: {...}, name: "..." }`) so flipping the
// tool flag back doesn't break anything.

const data = $input.first().json;
const headers = data.headers || {};
const body = data.body || {};

// Tool name — header-routed (preferred), fall back to body.name for legacy shape
const tool = headers.tool || body.name || '';

// Args — nested under body.args (args_at_root: false) OR spread at body root (args_at_root: true)
let args;
if (body.args && typeof body.args === 'object' && !Array.isArray(body.args)) {
    args = body.args;
} else {
    // Strip Retell-internal envelope fields; everything else is an arg.
    const { call, name, ...rootArgs } = body;
    args = rootArgs;
}


if (!tool) {
    return [{
        json: {
            tool: '',
            args: {},
            _parseError: 'No tool name found. Expected the `tool` HTTP header (set per-tool in the Retell agent config), or body.name for legacy webhook shape.'
        }
    }];
}

return [{ json: { tool, args } }];
"""

VALIDATE_SLOTS_JS = r"""const inputJson = $input.first().json;
const { args } = inputJson;
const errors = [];

if (!args.serviceId) errors.push('serviceId is required');
if (!args.startDate) errors.push('startDate is required');
if (!args.endDate) errors.push('endDate is required');
if (!args.durationInMinutes) errors.push('durationInMinutes is required');

// Force Wix's strict local ISO format: YYYY-MM-DDThh:mm:ss.sss
function formatForWix(dateStr, isEnd = false) {
    if (!dateStr) return dateStr;
    let cleanStr = String(dateStr).replace('Z', '');
    cleanStr = cleanStr.replace(/[+-]\d{2}:\d{2}$/, '');
    if (cleanStr.length === 10) {
        cleanStr += isEnd ? 'T23:59:59.000' : 'T00:00:00.000';
    }
    return cleanStr;
}

if (args.startDate) {
    if (isNaN(Date.parse(args.startDate))) {
        errors.push('startDate is not a valid date');
    } else {
        args.startDate = formatForWix(args.startDate, false);
    }
}

if (args.endDate) {
    if (isNaN(Date.parse(args.endDate))) {
        errors.push('endDate is not a valid date');
    } else {
        args.endDate = formatForWix(args.endDate, true);
    }
}

// --- NEW: Normalize optional filter args ---

// staffId: trim or null
if (args.staffId === '' || args.staffId === undefined) {
    args.staffId = null;
} else if (args.staffId) {
    args.staffId = String(args.staffId).trim();
}

// timeOfDay: lowercase one of morning/afternoon/evening/any (default any)
const validTOD = ['morning', 'afternoon', 'evening', 'any'];
if (args.timeOfDay) {
    const tod = String(args.timeOfDay).toLowerCase().trim();
    args.timeOfDay = validTOD.includes(tod) ? tod : 'any';
} else {
    args.timeOfDay = 'any';
}

// earliestFirst: coerce to boolean
if (args.earliestFirst === true || String(args.earliestFirst).toLowerCase() === 'true') {
    args.earliestFirst = true;
} else {
    args.earliestFirst = false;
}

// limit: integer 1..50, default 6 (3 if earliestFirst and not set)
if (args.limit !== undefined && args.limit !== null && args.limit !== '') {
    const n = parseInt(args.limit, 10);
    if (!isNaN(n) && n >= 1 && n <= 50) {
        args.limit = n;
    } else {
        args.limit = args.earliestFirst ? 3 : 6;
    }
} else {
    args.limit = args.earliestFirst ? 3 : 6;
}

return [{ json: { ...inputJson, args, _valid: errors.length === 0, _validationError: errors.join('; ') } }];
"""

FORMAT_SLOTS_JS = r"""// Reads Wix's per-slot availableResources (populated because the request
// passes includeResourceTypeIds upstream) and returns therapist names directly
// from Wix — no STAFF_LOOKUP needed.

const raw = $input.first().json;
const { args } = $('Parse Retell Payload').first().json;

const data = Array.isArray(raw) ? raw[0] : raw;

if (!data) return [{ json: { success: false, error: 'Empty response from Wix' } }];
if (data.message || data.details) {
    return [{ json: { success: false, error: data.message || 'Failed to retrieve slots', details: data.details || null } }];
}

const entries = data.timeSlots || [];

const staffFilter = args.staffId || null;
const timeOfDay = (args.timeOfDay || 'any').toLowerCase();
const earliestFirst = args.earliestFirst === true;
const limit = (typeof args.limit === 'number' && args.limit > 0)
    ? args.limit
    : (earliestFirst ? 3 : 6);

function parseLocalDateTime(localDateTime) {
    const [datePart, timePart] = (localDateTime || '').split('T');
    const [hourStr, minuteStr] = (timePart || '00:00:00').split(':');
    return {
        localDate: datePart,
        hour: parseInt(hourStr, 10),
        minute: parseInt(minuteStr, 10)
    };
}

function formatTimeLabel(hour, minute) {
    const suffix = hour >= 12 ? 'PM' : 'AM';
    const h = hour % 12 === 0 ? 12 : hour % 12;
    const m = String(minute).padStart(2, '0');
    return `${h}:${m} ${suffix}`;
}

function inBand(hour, band) {
    if (band === 'morning')   return hour >= 10 && hour < 12;
    if (band === 'afternoon') return hour >= 12 && hour < 17;
    if (band === 'evening')   return hour >= 17 && hour < 20;
    return hour >= 10 && hour < 20;
}

function bandOf(hour) {
    if (hour >= 10 && hour < 12) return 'morning';
    if (hour >= 12 && hour < 17) return 'afternoon';
    if (hour >= 17 && hour < 20) return 'evening';
    return null;
}

// Wix V2 timeSlots returns availableResources as:
//   [{ resourceTypeId, resources: [{ id, name }, ...], hasMoreAvailableResources }]
// (when includeResourceTypeIds is in the request — which we now do via the
// upstream "Wix: Query Resource Types" + "Extract: Staff Resource Type ID"
// nodes).
function extractTherapists(availableResources) {
    if (!Array.isArray(availableResources)) return [];
    const out = [];
    const seen = new Set();
    for (const block of availableResources) {
        const resources = Array.isArray(block?.resources) ? block.resources : [];
        for (const r of resources) {
            const id = r?.id || null;
            const name = r?.name || null;
            if (!id) continue;
            if (seen.has(id)) continue;
            seen.add(id);
            out.push({ name: name || 'Therapist', staffId: id });
        }
    }
    return out;
}

function mergeTherapists(agg, candidate) {
    for (const t of candidate.therapists) {
        const exists = agg.availableTherapists.some(x =>
            (x.staffId && t.staffId && x.staffId === t.staffId) ||
            (!x.staffId && !t.staffId && x.name === t.name)
        );
        if (!exists) agg.availableTherapists.push({ name: t.name, staffId: t.staffId });
    }
}

function buildAgg(s) {
    return {
        time: s.time,
        startDate: s.startDate,
        endDate: s.endDate,
        scheduleId: s.scheduleId,
        // The agent uses the staffId from the chosen entry of availableTherapists
        // when caller picks a specific therapist; OMITS staffId entirely when
        // caller has no preference (Wix auto-assigns at confirmation).
        availableTherapists: s.therapists.map(t => ({ name: t.name, staffId: t.staffId }))
    };
}

// 1. Map Wix slots -> local + extract therapists per slot
let slots = entries
    .filter(e => e.bookable === true)
    .map(e => {
        const startParts = parseLocalDateTime(e.localStartDate);
        const therapists = extractTherapists(e.availableResources);
        return {
            localDate: startParts.localDate,
            time: formatTimeLabel(startParts.hour, startParts.minute),
            hour: startParts.hour,
            minute: startParts.minute,
            startDate: e.localStartDate,
            endDate: e.localEndDate,
            therapists,
            therapistIds: therapists.map(t => t.staffId).filter(Boolean),
            scheduleId: e.scheduleId || null
        };
    });

// 2. No client-side staff filter — Wix's `resourceTypes.resourceIds` filter
// already narrows server-side when a staffId is provided. Re-filtering here
// caused all slots to be dropped when the agent passed a bogus staffId, even
// though Wix returned valid slots for other staff. Trust Wix.

// 3. Apply time-of-day filter
slots = slots.filter(s => inBand(s.hour, timeOfDay));

const filterApplied = { staffId: staffFilter, timeOfDay, earliestFirst, limit };

// 4a. EARLIEST_FIRST
if (earliestFirst) {
    const sorted = slots.slice().sort((a, b) => new Date(a.startDate) - new Date(b.startDate));
    const seen = new Map();
    const order = [];
    for (const s of sorted) {
        const key = `${s.localDate}|${s.time}`;
        if (seen.has(key)) {
            mergeTherapists(seen.get(key), s);
        } else {
            const agg = buildAgg(s);
            seen.set(key, agg);
            order.push(agg);
            if (order.length >= limit) break;
        }
    }
    return [{ json: { success: true, mode: 'earliest_first', count: order.length, filterApplied, slots: order } }];
}

// 4b. GROUPED
const availabilityByDay = {};
slots.forEach(s => {
    const band = bandOf(s.hour);
    if (!band) return;
    if (!availabilityByDay[s.localDate]) {
        availabilityByDay[s.localDate] = { morning: [], afternoon: [], evening: [] };
    }
    const day = availabilityByDay[s.localDate];
    const existing = [...day.morning, ...day.afternoon, ...day.evening].find(x => x.time === s.time);
    if (existing) {
        mergeTherapists(existing, s);
    } else {
        day[band].push(buildAgg(s));
    }
});

// Cap slots per band
let totalReturned = 0;
const sortedDates = Object.keys(availabilityByDay).sort();
for (const date of sortedDates) {
    const day = availabilityByDay[date];
    const activeBands = ['morning', 'afternoon', 'evening'].filter(b => day[b].length > 0);
    const perBand = activeBands.length === 0 ? 0 : Math.max(2, Math.ceil(limit / Math.max(1, activeBands.length)));
    for (const band of ['morning', 'afternoon', 'evening']) {
        day[band].sort((a, b) => new Date(a.startDate) - new Date(b.startDate));
        if (day[band].length > perBand) day[band] = day[band].slice(0, perBand);
        totalReturned += day[band].length;
    }
}

return [{ json: { success: true, mode: 'grouped', count: totalReturned, filterApplied, availabilityByDay } }];"""

FORMAT_STAFF_JS = r"""const data = $input.first().json;

if (data.message || data.details || !data.staffMembers) {
  return [{ json: { success: false, error: data.message || 'Failed to retrieve staff members' } }];
}

const staff = (data.staffMembers || []).map(s => ({
  id: s.id,
  resourceId: s.resourceId,
  name: s.name,
  // description: s.description ?? null,
  // phone: s.phone ?? null,
  email: s.email ?? null
}));

return [{ json: { success: true, count: staff.length, staff } }];"""

VALIDATE_BOOKING_JS = r"""const { args } = $input.first().json;
const errors = [];

// 1. Slot Context (staffId is optional — caller may have said "no preference")
if (!args.serviceId) errors.push('serviceId is required');
if (!args.scheduleId) errors.push('scheduleId is required');

// 2. Dates
if (!args.startDate) errors.push('startDate is required');
if (!args.endDate) errors.push('endDate is required');

// 3. Customer Details
if (!args.firstName) errors.push('firstName is required');
if (!args.lastName) errors.push('lastName is required');
if (!args.email) errors.push('email is required');
if (!args.phone) errors.push('phone is required');

// Date format checks
if (args.startDate && isNaN(Date.parse(args.startDate))) errors.push('startDate is not a valid date');
if (args.endDate && isNaN(Date.parse(args.endDate))) errors.push('endDate is not a valid date');

// addOns: array of { id, groupId } — both required per entry
if (args.addOns) {
    if (!Array.isArray(args.addOns)) {
        errors.push('addOns must be an array of {id, groupId} objects');
    } else {
        args.addOns.forEach((a, i) => {
            if (!a || typeof a !== 'object') errors.push(`addOns[${i}] must be an object`);
            else {
                if (!a.id) errors.push(`addOns[${i}].id is required`);
                if (!a.groupId) errors.push(`addOns[${i}].groupId is required`);
            }
        });
    }
}

return [{ json: { ...$input.first().json, args, _valid: errors.length === 0, _validationError: errors.join('; ') } }];
"""

FORMAT_BOOKING_JS = r"""const confirmData = $input.first().json;
// Fallback to the create booking data if confirm had issues
const createData = $('Wix: Create Booking').first().json;

const booking = confirmData.booking || createData.booking || {};
const isConfirmed = confirmData.booking?.status === 'CONFIRMED';

if (!booking.id) {
  return [{ json: { success: false, error: confirmData.message || 'Booking confirmation failed' } }];
}

return [{ json: {
  success: true,
  confirmed: isConfirmed,
  bookingId: booking.id,
  status: booking.status,
  startDate: booking.bookedEntity?.slot?.startDate,
  endDate: booking.bookedEntity?.slot?.endDate,
  serviceId: booking.bookedEntity?.slot?.serviceId,
  contact: {
    firstName: booking.contactDetails?.firstName,
    lastName: booking.contactDetails?.lastName,
    phone: booking.contactDetails?.phone,
    email: booking.contactDetails?.email ?? null
  },
  message: `Appointment booked for ${booking.contactDetails?.firstName} ${booking.contactDetails?.lastName} on ${booking.bookedEntity?.slot?.startDate}`
} }];"""

VALIDATE_CANCEL_JS = r"""const { args } = $input.first().json;
const errors = [];

if (!args.bookingId) errors.push('bookingId is required');

return [{ json: { ...$input.first().json, _valid: errors.length === 0, _validationError: errors.join('; ') } }];"""

FORMAT_CANCEL_JS = r"""const data = $input.first().json;

// Wix cancel returns 200 with booking object on success; message+details on error
if (data.message && data.details) {
  return [{ json: {
    success: false,
    cancelFlag: 'no',
    error: data.message || 'Failed to cancel booking. It may have already been cancelled or the cancellation policy prevents it.'
  } }];
}

return [{ json: {
  success: true,
  cancelFlag: 'yes',
  message: 'Booking has been successfully cancelled.',
  bookingId: data.booking?.id ?? $('Validate: Cancel Args').first().json.args.bookingId,
  status: data.booking?.status ?? 'CANCELED'
} }];
"""

VALIDATE_RESCHEDULE_JS = r"""const { args } = $input.first().json;
const errors = [];

// 1. Existing Booking Identifiers
if (!args.bookingId) errors.push('bookingId is required');
// Note: checking strictly for undefined because revision can technically be 0
if (args.revision === undefined || args.revision === null) errors.push('revision is required'); 

// 2. New Slot Context (Required by Wix V2 API)
if (!args.serviceId) errors.push('serviceId is required');
if (!args.scheduleId) errors.push('scheduleId is required');
if (!args.staffId) errors.push('staffId is required');

// 3. New Dates
if (!args.startDate) errors.push('startDate is required (new slot start time)');
if (!args.endDate) errors.push('endDate is required (new slot end time)');

// Date formatting checks
if (args.startDate && isNaN(Date.parse(args.startDate))) errors.push('startDate is not a valid date');
if (args.endDate && isNaN(Date.parse(args.endDate))) errors.push('endDate is not a valid date');

return [{ json: { ...$input.first().json, _valid: errors.length === 0, _validationError: errors.join('; ') } }];"""

FORMAT_RESCHEDULE_JS = r"""const data = $input.first().json;

if (data.message || !data.booking) {
  return [{ json: {
    success: false,
    rescheduleFlag: 'no',
    error: data.message || 'Failed to reschedule the booking. The new slot may not be available or rescheduling is not permitted by the service policy.'
  } }];
}

const booking = data.booking;
const newStart = booking.bookedEntity?.slot?.startDate;

// Day-of-week from local date part — never let the agent compute it.
const DOW = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
let newDayOfWeek = null;
if (newStart) {
  const m = String(newStart).split('T')[0].match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (m) newDayOfWeek = DOW[new Date(Date.UTC(+m[1], +m[2]-1, +m[3])).getUTCDay()];
}

return [{ json: {
  success: true,
  rescheduleFlag: 'yes',
  message: 'Booking successfully rescheduled.',
  bookingId: booking.id,
  newStartDate: newStart,
  newEndDate: booking.bookedEntity?.slot?.endDate,
  newDayOfWeek,
  status: booking.status
} }];
"""

VALIDATE_GET_BOOKING_JS = r"""const { args, callerPhone } = $input.first().json;
const errors = [];

// Resolve inputs
const phoneToSearch = args.phone || callerPhone || null;
const emailToSearch = args.email || null;
const bookingId = args.bookingId || null;

// Determine lookup mode (Email is now Priority #1)
let lookupMode = '';
if (emailToSearch) lookupMode = 'by-email';
else if (bookingId) lookupMode = 'by-id';
else if (phoneToSearch) lookupMode = 'by-phone';
else errors.push('Either bookingId, email, or phone number is required');

return [{ json: {
  ...$input.first().json,
  args: { ...args, _resolvedPhone: phoneToSearch, _resolvedEmail: emailToSearch, _resolvedBookingId: bookingId },
  _valid: errors.length === 0,
  _validationError: errors.join('; '),
  _lookupMode: lookupMode
} }];
"""

FORMAT_GET_BOOKING_JS = r"""const data = $input.first().json;

if (data.message || data.details) {
  return [{ json: { success: false, foundFlag: 'no', error: data.message || 'Failed to retrieve booking' } }];
}

const now = Date.now();

// Compute day-of-week from the LOCAL date part of an ISO string like
// "2026-05-15T10:00:00.000-07:00". new Date(...).getDay() depends on
// server timezone and can return wrong weekday for Pacific dates when
// n8n runs in UTC or any non-Pacific zone — extract the local date
// component directly instead.
const DOW_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
function localDayOfWeek(localIso) {
  if (!localIso) return null;
  const datePart = String(localIso).split('T')[0];
  const m = datePart.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!m) return null;
  const y = +m[1], mo = +m[2], d = +m[3];
  // Date.UTC(y, mo-1, d) anchors to midnight UTC of that calendar date;
  // getUTCDay() then returns the correct weekday for that local date,
  // independent of server timezone.
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
  // Within-24h policy: appointment is in the future but less than 24 hours away
  const within24h = hoursUntilStart !== null && hoursUntilStart > 0 && hoursUntilStart < 24;

  return {
    bookingId: b.id,
    status: b.status,
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
});

// Keep only upcoming bookings (startDate in the future)
const bookings = enriched
  .filter(b => isFinite(b._startMs) && b._startMs > now)
  .map(({ _startMs, ...rest }) => rest);

const found = bookings.length > 0;

return [{ json: {
  success: true,
  foundFlag: found ? 'yes' : 'no',
  count: bookings.length,
  bookings: found ? bookings : [],
  message: found ? undefined : 'No upcoming bookings found for this customer'
} }];
"""

VALIDATE_FLAG_CALLBACK_JS = r"""const { args, callerPhone } = $input.first().json;
const errors = [];

const reason = (args.reason || '').toString().trim();
if (!reason) errors.push('reason is required');

const callerName = (args.callerName || '').toString().trim() || 'Unknown';
const phoneToContact = (args.callerPhone || '').toString().trim() || callerPhone || 'Unknown';
const questionDetail = (args.questionDetail || '').toString().trim();

const subject = `New callback request from ${callerName} (${phoneToContact})`;

const lines = [
    `A caller asked Aria for a callback. Please follow up.`,
    ``,
    `Caller name: ${callerName}`,
    `Phone:       ${phoneToContact}`,
    `Reason:      ${reason}`,
];
if (questionDetail) {
    lines.push(``);
    lines.push(`Question / detail:`);
    lines.push(questionDetail);
}
lines.push(``);
lines.push(`— Sent automatically by the Sage & Willow Spa AI receptionist`);

const body = lines.join('\n');

return [{ json: {
    ...$input.first().json,
    args,
    _valid: errors.length === 0,
    _validationError: errors.join('; '),
    _emailSubject: subject,
    _emailBody: body,
    _callerName: callerName,
    _callerPhone: phoneToContact,
    _reason: reason
} }];
"""

FORMAT_FLAG_CALLBACK_RESPONSE_JS = r"""const v = $('Validate: Flag Callback Args').first().json;
return [{ json: {
    success: true,
    flagged: true,
    message: 'Callback request sent to the team — they will follow up with the caller.',
    callerName: v._callerName,
    callerPhone: v._callerPhone,
    reason: v._reason
} }];
"""

VALIDATE_GET_CONTACT_JS = r"""const { args, callerPhone } = $input.first().json;
const errors = [];

const phone = args?.phone || callerPhone || null;
const email = args?.email || null;

if (!phone && !email) {
  errors.push('Either phone or email is required to look up a contact');
}

return [{ json: {
  ...$input.first().json,
  args: { ...args, _resolvedPhone: phone, _resolvedEmail: email },
  _valid: errors.length === 0,
  _validationError: errors.join('; ')
} }];"""

FORMAT_CONTACT_RESPONSE_JS = r"""const data = $input.first().json;

if (data.message || data.details) {
  return [{ json: { success: false, error: data.message || 'Failed to query contact' } }];
}

const contacts = data.contacts || [];

if (contacts.length === 0) {
  return [{ json: { success: true, found: false, message: 'No contact found with this information.' } }];
}

const c = contacts[0];

// Use the root primaryInfo that Wix automatically generates for us
const primaryEmail = c.primaryInfo?.email || c.primaryEmail?.email || null;
const primaryPhone = c.primaryInfo?.phone || c.primaryPhone?.phone || null;

return [{ json: { 
  success: true, 
  found: true,
  contact: {
    contactId: c.id,
    firstName: c.info?.name?.first || null,
    lastName: c.info?.name?.last || null,
    email: primaryEmail,
    phone: primaryPhone
  }
} }];"""

FORMAT_CREATE_CONTACT_JS = r"""const data = $input.first().json;

if (data.message || data.details) {
  return [{ json: { success: false, error: data.message || 'Failed to create contact' } }];
}

return [{ json: { success: true, contactId: data.contact.id, message: 'Contact created successfully' } }];"""

FORMAT_CONTACT_RESPONSE_1_JS = r"""const data = $input.first().json;

if (data.message || data.details) {
  return [{ json: { success: false, error: data.message || 'Failed to query contact' } }];
}

const contacts = data.contacts || [];

if (contacts.length === 0) {
  return [{ json: { success: true, found: false, message: 'No contact found with this information.' } }];
}

const c = contacts[0];

// Use the root primaryInfo that Wix automatically generates for us
const primaryEmail = c.primaryInfo?.email || c.primaryEmail?.email || null;
const primaryPhone = c.primaryInfo?.phone || c.primaryPhone?.phone || null;

return [{ json: { 
  success: true, 
  found: true,
  contact: {
    contactId: c.id,
    firstName: c.info?.name?.first || null,
    lastName: c.info?.name?.last || null,
    email: primaryEmail,
    phone: primaryPhone
  }
} }];"""

EXTRACT_PRICING_IDS_JS = r"""const data = $('Wix: Query Services').first().json;
if (!data.services) return [{ json: { hasVaried: false, serviceId: null } }];

const varied = data.services.filter(s => s.payment?.rateType === 'VARIED');
if (varied.length === 0) return [{ json: { hasVaried: false, serviceId: null } }];

return varied.map(s => ({ json: { hasVaried: true, serviceId: s.id } }));"""

EXTRACT_ADD_ON_IDS_JS = r"""const data = $('Wix: Query Services').first().json;

if (!data.services) {
  return [{ json: { hasAddOns: false } }];
}

// Use a Set to automatically remove duplicates globally
const uniqueAddOnIds = new Set();

data.services.forEach(service => {
  if (service.addOnGroups) {
    service.addOnGroups.forEach(group => {
      if (group.addOnIds) {
        group.addOnIds.forEach(id => uniqueAddOnIds.add(id));
      }
    });
  }
});

if (uniqueAddOnIds.size === 0) {
  return [{ json: { hasAddOns: false } }];
}

// Convert the Set into the flat array format n8n needs for the HTTP node
return Array.from(uniqueAddOnIds).map(id => ({
  json: { 
    hasAddOns: true, 
    addOnId: id 
  }
}));"""

FORMAT_SERVICES_RESPONSE_JS = r"""const servicesData = $('Wix: Query Services').first().json;
const serviceName = $('Webhook — Retell Tool Call').first().json.body.args.serviceName
if (servicesData.message || servicesData.details || !servicesData.services) {
  return [{ json: { success: false, error: servicesData.message || 'Failed to retrieve services' } }];
}
const services = servicesData.services || [];
// 1. Map Pricing Variants
const pricingLookup = {};
try {
  const pricingItems = $('Wix: Get Pricing Variants').all();
  pricingItems.forEach(item => {
    const sv = item.json.serviceVariants || item.json;
    if (sv && sv.serviceId && sv.variants && sv.variants.values) {
      pricingLookup[sv.serviceId] = sv.variants.values.map(v => ({
        id: v.id,
        duration: v.choices?.[0]?.duration?.minutes + " min",
        price: "USD " + (v.price?.value || 0)
      }));
    }
  });
} catch (e) {
  console.error("Pricing map skipped or failed.");
}
// 2. Map Add-ons (Base Details Only: Name, Price, Duration)
const addOnLookup = {};
try {
  const addonItems = $('Wix: Get Add-ons').all();
  for (const item of addonItems) {
    const addon = item.json?.addOn || item.json;
    if (addon?.id) {
      addOnLookup[addon.id] = {
        name: addon.name || "Unknown",
        price: "USD " + (addon.price?.value || 0),
        duration: (addon.durationInMinutes || 0) + " min"
      };
    }
  }
} catch (e) {
  console.error("Error mapping Add-on base details:", e);
}
// 3. Final Lean Mapping (Extracts Group IDs directly from original data)
const formattedServices = services.map(s => {
  let availableAddOns = [];
  if (s.addOnGroups && s.addOnGroups.length > 0) {
    const localGroupMap = {};
    s.addOnGroups.forEach(group => {
      const groupId = group.id;
      const addOnIds = group.addOnIds || [];
      addOnIds.forEach(addOnId => {
        if (!localGroupMap[addOnId]) {
          localGroupMap[addOnId] = [];
        }
        if (!localGroupMap[addOnId].includes(groupId)) {
          localGroupMap[addOnId].push(groupId);
        }
      });
    });
    const uniqueIds = Object.keys(localGroupMap);
    availableAddOns = uniqueIds.map(id => {
      const details = addOnLookup[id] || {
        name: "Unknown",
        price: "USD 0",
        duration: "0 min"
      };
      return {
        id,
        name: details.name,
        price: details.price,
        duration: details.duration,
        groupIds: localGroupMap[id]
      };
    });
  }
  const isVaried = s.payment?.rateType === 'VARIED';
  const pricingVariants = isVaried ? pricingLookup[s.id] : undefined;
  const fixedPrice =
    !isVaried && s.payment?.fixed?.price?.value
      ? "USD " + s.payment.fixed.price.value
      : undefined;
  return {
    id: s.id,
    name: s.name,
    description: s.description,
    price: fixedPrice,
    pricingVariants,
    availableAddOns: availableAddOns.length > 0 ? availableAddOns : undefined
  };
});

// 4. Filter by serviceName if provided and a match exists
const normalizedInput = (serviceName || '').trim().toLowerCase();
const matchedServices = normalizedInput
  ? formattedServices.filter(s => s.name.toLowerCase().includes(normalizedInput))
  : [];

const finalServices = matchedServices.length > 0 ? matchedServices : formattedServices;

return [{ json: { success: true, services: finalServices } }];"""


# -----------------------------------------------------------------------------
# HTTP body templates (inlined into Wix httpRequest nodes)
# -----------------------------------------------------------------------------

WIX_QUERY_TIME_SLOTS_BODY = r"""={
  "serviceId": "{{ $json.args.serviceId }}",
  "fromLocalDate": "{{ $json.args.startDate }}",
  "toLocalDate": "{{ $json.args.endDate }}",
  "timeZone": "America/Los_Angeles"
  {{ $json.args.staffId ? ', "resourceTypes": [{ "resourceTypeId": "1cd44cf8-756f-41c3-bd90-3e2ffcaf1155", "resourceIds": ["' + $json.args.staffId + '"] }]' : ', "includeResourceTypeIds": ["1cd44cf8-756f-41c3-bd90-3e2ffcaf1155"]' }}
  {{ $json.args.durationInMinutes ? ', "customerChoices": { "durationInMinutes": ' + $json.args.durationInMinutes + ' }' : '' }}
}"""

WIX_QUERY_STAFF_BODY = r"""{
  "query": {
    "paging": { "limit": 50 }
  }
}"""

WIX_CREATE_BOOKING_BODY = r"""={
  "booking": {
    "bookedEntity": {
      {{ $('IF: Booking Args Valid').item.json.args.variantId ? '"variantId": "' + $('IF: Booking Args Valid').item.json.args.variantId + '",' : '' }}
      "slot": {
        "serviceId": "{{ $('IF: Booking Args Valid').item.json.args.serviceId }}",
        "scheduleId": "{{ $('IF: Booking Args Valid').item.json.args.scheduleId }}",
        "startDate": "{{ $('IF: Booking Args Valid').item.json.args.startDate }}",
        "endDate": "{{ $('IF: Booking Args Valid').item.json.args.endDate }}",
        "timezone": "America/Los_Angeles",
        "location": {
          "locationType": "OWNER_BUSINESS",
          "id": "a345d3c7-2a89-4816-ad3a-277ea40730a7"
        }
        {{ $('IF: Booking Args Valid').item.json.args.staffId ? ',"resource": { "id": "' + $('IF: Booking Args Valid').item.json.args.staffId + '" }' : '' }}
        {{ $('IF: Booking Args Valid').item.json.args.staffId ? ',"resourceSelections": [{ "resourceTypeId": "1cd44cf8-756f-41c3-bd90-3e2ffcaf1155", "selectionMethod": "SPECIFIC_RESOURCE" }]' : ',"resourceSelections": [{ "resourceTypeId": "1cd44cf8-756f-41c3-bd90-3e2ffcaf1155", "selectionMethod": "ANY_RESOURCE" }]' }}
      }
    },
    "contactDetails": {
      "firstName": "{{ $('IF: Booking Args Valid').item.json.args.firstName }}",
      "lastName": "{{ $('IF: Booking Args Valid').item.json.args.lastName }}",
      "email": "{{ $('IF: Booking Args Valid').item.json.args.email || 'sagewillowspa@gmail.com' }}",
      "phone": "{{ $('IF: Booking Args Valid').item.json.args.phone }}"
    },
    "numberOfParticipants": 1
    {{ $('IF: Booking Args Valid').item.json.args.notes ? ',"additionalFields": { "fields": [{ "fieldId": "field:note", "value": { "stringValue": "' + $('IF: Booking Args Valid').item.json.args.notes + '" } }] }' : '' }}
    {{ $('IF: Booking Args Valid').item.json.args.addOns?.length > 0 ? ',"bookedAddOns": ' + JSON.stringify($('IF: Booking Args Valid').item.json.args.addOns.map(a => ({ id: a.id, groupId: a.groupId, quantity: 1 }))) : '' }}
  },
  "flowControlSettings": {
    "withoutPayment": true
  }
}"""

WIX_CONFIRM_BOOKING_BODY = r"""={
  "participantNotification": {
    "notifyParticipants": true
  },
  "revision": {{ $json.booking.revision }}
}"""

WIX_CANCEL_BOOKING_BODY = r"""={
  "revision": "{{ $json.args.revision }}",
  "participantNotification": {
    "notifyParticipants": true
  }
}"""

WIX_RESCHEDULE_BOOKING_BODY = r"""={
  "slot": {
    "serviceId": "{{ $json.args.serviceId }}",
    "scheduleId": "{{ $json.args.scheduleId }}",
    "startDate": "{{ $json.args.startDate }}",
    "endDate": "{{ $json.args.endDate }}",
    "timezone": "America/Los_Angeles",
    "resource": {
      "id": "{{ $json.args.staffId }}"
    },
    "location": {
      "locationType": "OWNER_BUSINESS",
      "id": "a345d3c7-2a89-4816-ad3a-277ea40730a7"
    }
  },
  "revision": {{ $json.args.revision }},
  "participantNotification": {
    "notifyParticipants": true
  }
}"""

WIX_GET_BOOKING_BODY = r"""={
  "query": {
    "filter": {
      {{ 
        $json._lookupMode === 'by-id' ? '"id": { "$in": ["' + $json.args._resolvedBookingId + '"]}' : 
        $json._lookupMode === 'by-email' ? '"contactDetails.email": "' + $json.args._resolvedEmail + '"' : 
        '"contactDetails.phone": "' + $json.args._resolvedPhone + '"' 
      }},
      "status": { "$in": ["CONFIRMED", "PENDING_APPROVAL", "CREATED", "PENDING"] }
    },
    "sort": [{ "fieldName": "createdDate", "order": "DESC" }],
    "paging": { "limit": 5 }
  }
}"""

WIX_SEARCH_CONTACT_BODY = r"""={
  "query": {
    "filter": {
      {{ $json.args._resolvedEmail ? '"info.emails.email": "' + $json.args._resolvedEmail + '"' : '"info.phones.phone": "' + $json.args._resolvedPhone + '"' }}
    },
    "paging": {
      "limit": 1
    }
  }
}"""

WIX_CREATE_CONTACT_BODY = r"""={
  "info": {
    "name": {
      "first": "{{ $('IF: Booking Args Valid').item.json.args.firstName }}",
      "last": "{{ $('IF: Booking Args Valid').item.json.args.lastName || '' }}"
    },
    "emails": {
      "items": [
        {
          "tag": "MAIN",
          "email": "{{ $('IF: Booking Args Valid').item.json.args.email }}"
        }
      ]
    },
    "phones": {
      "items": [
        {
          "tag": "MAIN",
          "phone": "{{ $('IF: Booking Args Valid').item.json.args.phone }}"
        }
      ]
    }
  }
}"""

WIX_SEARCH_CONTACT_1_BODY = r"""={
  "query": {
    "filter": {
      {{ $json.args.email ? '"info.emails.email": "' + $json.args.email + '"' : '"info.phones.phone": "' + $json.args.phone + '"' }}
    },
    "paging": {
      "limit": 1
    }
  }
}"""

WIX_QUERY_SERVICES_BODY = r"""{
  "query": {
    "filter": {
      "type": ["APPOINTMENT", "CLASS"]
    },
    "paging": {
      "limit": 100
    }
  }
}"""


# -----------------------------------------------------------------------------
# Nodes (every node in the workflow — full canonical state)
# -----------------------------------------------------------------------------

NODES = [   {   'parameters': {'httpMethod': 'POST', 'path': 'retell-wix', 'responseMode': 'responseNode', 'options': {}},
        'id': '2ebbfda4-ff8c-499c-80a9-d9f5e9d34267',
        'name': 'Webhook — Retell Tool Call',
        'type': 'n8n-nodes-base.webhook',
        'typeVersion': 1,
        'position': [64, 5904],
        'webhookId': 'retell-wix-prod-v2'},
    {   'parameters': {'jsCode': PARSE_RETELL_PAYLOAD_JS},
        'id': '6f960a23-57e1-447e-95cf-8b9d9521a7b5',
        'name': 'Parse Retell Payload',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [288, 5904]},
    {   'parameters': {'jsCode': VALIDATE_SLOTS_JS},
        'id': 'b90db447-2267-4408-956b-829d8acdfcbd',
        'name': 'Validate: Slots Args',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [736, 4656]},
    {   'parameters': {'conditions': {'boolean': [{'value1': '={{ $json._valid }}', 'value2': True}]}},
        'id': '82c4e2d3-8caf-47d4-a833-c3c568c85d05',
        'name': 'IF: Slots Args Valid',
        'type': 'n8n-nodes-base.if',
        'typeVersion': 1,
        'position': [960, 4656]},
    {   'parameters': {   'method': 'POST',
                          'url': 'https://www.wixapis.com/_api/service-availability/v2/time-slots',
                          'authentication': 'predefinedCredentialType',
                          'nodeCredentialType': 'wixApi',
                          'sendBody': True,
                          'specifyBody': 'json',
                          'jsonBody': WIX_QUERY_TIME_SLOTS_BODY,
                          'options': {}},
        'id': 'efd7602a-a098-4a2f-8d50-e1d0f7be581b',
        'name': 'Wix: Query Time Slots',
        'type': 'n8n-nodes-base.httpRequest',
        'typeVersion': 4.1,
        'position': [1184, 4560],
        'credentials': {'wixApi': {'id': WIX_CREDENTIAL_ID, 'name': WIX_CREDENTIAL_NAME}},
        'continueOnFail': True,
        'onError': 'continueErrorOutput'},
    {   'parameters': {'jsCode': FORMAT_SLOTS_JS},
        'id': '6cb356ab-005b-492f-8508-2957f99598df',
        'name': 'Format: Time Slots Response',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [1408, 4464]},
    {   'parameters': {   'respondWith': 'json',
                          'responseBody': "={{ { success: false, error: 'Validation failed: ' + $json._validationError "
                                          '} }}',
                          'options': {}},
        'id': '803fec28-814e-460b-9544-b9593573d089',
        'name': 'Respond: Slots Validation Error',
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1,
        'position': [1184, 4752]},
    {   'parameters': {   'method': 'POST',
                          'url': 'https://www.wixapis.com/bookings/v1/staff-members/query',
                          'authentication': 'predefinedCredentialType',
                          'nodeCredentialType': 'wixApi',
                          'sendBody': True,
                          'specifyBody': 'json',
                          'jsonBody': WIX_QUERY_STAFF_BODY,
                          'options': {}},
        'id': 'b29980f3-4985-4192-989e-68298f235284',
        'name': 'Wix: Query Staff Members',
        'type': 'n8n-nodes-base.httpRequest',
        'typeVersion': 4.1,
        'position': [736, 5040],
        'credentials': {'wixApi': {'id': WIX_CREDENTIAL_ID, 'name': WIX_CREDENTIAL_NAME}},
        'continueOnFail': True,
        'onError': 'continueErrorOutput'},
    {   'parameters': {'jsCode': FORMAT_STAFF_JS},
        'id': '5ebb1ce2-c33a-476e-b5d6-6b8179784450',
        'name': 'Format: Staff Response',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [960, 4944]},
    {   'parameters': {'jsCode': VALIDATE_BOOKING_JS},
        'id': '41516601-6d7a-421b-ad7b-544249a9b9aa',
        'name': 'Validate: Booking Args',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [736, 5328]},
    {   'parameters': {'conditions': {'boolean': [{'value1': '={{ $json._valid }}', 'value2': True}]}},
        'id': 'b6acd95c-2b46-4763-b93f-394f3a9003fe',
        'name': 'IF: Booking Args Valid',
        'type': 'n8n-nodes-base.if',
        'typeVersion': 1,
        'position': [960, 5328]},
    {   'parameters': {   'method': 'POST',
                          'url': 'https://www.wixapis.com/bookings/v2/bookings',
                          'authentication': 'predefinedCredentialType',
                          'nodeCredentialType': 'wixApi',
                          'sendBody': True,
                          'specifyBody': 'json',
                          'jsonBody': WIX_CREATE_BOOKING_BODY,
                          'options': {}},
        'id': '55d5dc78-c645-4b60-b51b-f93518edae3a',
        'name': 'Wix: Create Booking',
        'type': 'n8n-nodes-base.httpRequest',
        'typeVersion': 4.1,
        'position': [2304, 5168],
        'credentials': {'wixApi': {'id': WIX_CREDENTIAL_ID, 'name': WIX_CREDENTIAL_NAME}},
        'continueOnFail': True,
        'onError': 'continueErrorOutput'},
    {   'parameters': {   'conditions': {   'string': [   {   'value1': "={{ $json.booking?.id ?? '' }}",
                                                              'operation': 'isNotEmpty'}]}},
        'id': '1281e87c-1b99-4b01-bf1c-06c040c86b39',
        'name': 'IF: Booking Created OK',
        'type': 'n8n-nodes-base.if',
        'typeVersion': 1,
        'position': [2528, 5088]},
    {   'parameters': {   'method': 'POST',
                          'url': '=https://www.wixapis.com/bookings/v2/bookings/{{ $json.booking.id }}/confirm',
                          'authentication': 'predefinedCredentialType',
                          'nodeCredentialType': 'wixApi',
                          'sendBody': True,
                          'specifyBody': 'json',
                          'jsonBody': WIX_CONFIRM_BOOKING_BODY,
                          'options': {}},
        'id': '790fed11-5054-4ccd-b9b6-4e93aee97754',
        'name': 'Wix: Confirm Booking',
        'type': 'n8n-nodes-base.httpRequest',
        'typeVersion': 4.1,
        'position': [2752, 5024],
        'credentials': {'wixApi': {'id': WIX_CREDENTIAL_ID, 'name': WIX_CREDENTIAL_NAME}},
        'continueOnFail': True,
        'onError': 'continueErrorOutput'},
    {   'parameters': {'jsCode': FORMAT_BOOKING_JS},
        'id': 'b71a199b-e86f-469f-b376-cd67c99d0a7a',
        'name': 'Format: Booking Confirmation',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [2976, 4976]},
    {   'parameters': {   'respondWith': 'json',
                          'responseBody': "={{ { success: false, error: 'Validation failed: ' + $json._validationError "
                                          '} }}',
                          'options': {}},
        'id': '2a76a541-a727-46b7-b88e-0380ae5e9bb5',
        'name': 'Respond: Booking Validation Error',
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1,
        'position': [1184, 5424]},
    {   'parameters': {'jsCode': VALIDATE_CANCEL_JS},
        'id': '99fa7bb6-678e-4254-8301-795772ecb937',
        'name': 'Validate: Cancel Args',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [736, 5712]},
    {   'parameters': {'conditions': {'boolean': [{'value1': '={{ $json._valid }}', 'value2': True}]}},
        'id': '487df482-1065-4b45-bcee-31709131a918',
        'name': 'IF: Cancel Args Valid',
        'type': 'n8n-nodes-base.if',
        'typeVersion': 1,
        'position': [960, 5712]},
    {   'parameters': {   'method': 'POST',
                          'url': '=https://www.wixapis.com/bookings/v2/bookings/{{ $json.args.bookingId }}/cancel',
                          'authentication': 'predefinedCredentialType',
                          'nodeCredentialType': 'wixApi',
                          'sendBody': True,
                          'specifyBody': 'json',
                          'jsonBody': WIX_CANCEL_BOOKING_BODY,
                          'options': {}},
        'id': 'a6ba0920-fb42-4a22-97b0-7233be2a89db',
        'name': 'Wix: Cancel Booking',
        'type': 'n8n-nodes-base.httpRequest',
        'typeVersion': 4.1,
        'position': [1184, 5616],
        'credentials': {'wixApi': {'id': WIX_CREDENTIAL_ID, 'name': WIX_CREDENTIAL_NAME}},
        'continueOnFail': True,
        'onError': 'continueErrorOutput'},
    {   'parameters': {'jsCode': FORMAT_CANCEL_JS},
        'id': '18a56924-a194-438f-876c-b0df5307c8af',
        'name': 'Format: Cancel Response',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [1408, 5504]},
    {   'parameters': {   'respondWith': 'json',
                          'responseBody': "={{ { success: false, error: 'Validation failed: ' + $json._validationError "
                                          '} }}',
                          'options': {}},
        'id': 'd363c3ef-e65b-4fd6-bef5-3921454f4f42',
        'name': 'Respond: Cancel Validation Error',
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1,
        'position': [1184, 5808]},
    {   'parameters': {'jsCode': VALIDATE_RESCHEDULE_JS},
        'id': '27447d0a-5cba-48e7-af4f-959584ffbad1',
        'name': 'Validate: Reschedule Args',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [736, 6096]},
    {   'parameters': {'conditions': {'boolean': [{'value1': '={{ $json._valid }}', 'value2': True}]}},
        'id': '44d4e628-564a-4401-9104-9b93f00cbceb',
        'name': 'IF: Reschedule Args Valid',
        'type': 'n8n-nodes-base.if',
        'typeVersion': 1,
        'position': [960, 6096]},
    {   'parameters': {   'method': 'POST',
                          'url': '=https://www.wixapis.com/bookings/v2/bookings/{{ $json.args.bookingId }}/reschedule',
                          'authentication': 'predefinedCredentialType',
                          'nodeCredentialType': 'wixApi',
                          'sendBody': True,
                          'specifyBody': 'json',
                          'jsonBody': WIX_RESCHEDULE_BOOKING_BODY,
                          'options': {}},
        'id': '3b4ad430-de13-493b-b833-9c82f99b6950',
        'name': 'Wix: Reschedule Booking',
        'type': 'n8n-nodes-base.httpRequest',
        'typeVersion': 4.1,
        'position': [1184, 6000],
        'credentials': {'wixApi': {'id': WIX_CREDENTIAL_ID, 'name': WIX_CREDENTIAL_NAME}},
        'continueOnFail': True,
        'onError': 'continueErrorOutput'},
    {   'parameters': {'jsCode': FORMAT_RESCHEDULE_JS},
        'id': '4c53f885-118b-49f1-81ec-722182df3fa1',
        'name': 'Format: Reschedule Response',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [1408, 5904]},
    {   'parameters': {   'respondWith': 'json',
                          'responseBody': "={{ { success: false, error: 'Validation failed: ' + $json._validationError "
                                          '} }}',
                          'options': {}},
        'id': '3f28cefa-b0b8-48ba-939d-6c1d44239ac3',
        'name': 'Respond: Reschedule Validation Error',
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1,
        'position': [1184, 6192]},
    {   'parameters': {'jsCode': VALIDATE_GET_BOOKING_JS},
        'id': 'edce2227-92f9-4d84-87c7-ac96fcd9f29a',
        'name': 'Validate: Get Booking Args',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [736, 6864]},
    {   'parameters': {'conditions': {'boolean': [{'value1': '={{ $json._valid }}', 'value2': True}]}},
        'id': '33db63b8-08b4-4d1a-9f00-6c904c5a8033',
        'name': 'IF: Get Booking Args Valid',
        'type': 'n8n-nodes-base.if',
        'typeVersion': 1,
        'position': [960, 6864]},
    {   'parameters': {   'method': 'POST',
                          'url': 'https://www.wixapis.com/bookings/v2/bookings/query',
                          'authentication': 'predefinedCredentialType',
                          'nodeCredentialType': 'wixApi',
                          'sendBody': True,
                          'specifyBody': 'json',
                          'jsonBody': WIX_GET_BOOKING_BODY,
                          'options': {}},
        'id': '490a098d-ce3e-4fd2-bfe6-e0addd17e94e',
        'name': 'Wix: Get Booking',
        'type': 'n8n-nodes-base.httpRequest',
        'typeVersion': 4.1,
        'position': [1184, 6768],
        'credentials': {'wixApi': {'id': WIX_CREDENTIAL_ID, 'name': WIX_CREDENTIAL_NAME}},
        'continueOnFail': True,
        'onError': 'continueErrorOutput'},
    {   'parameters': {'jsCode': FORMAT_GET_BOOKING_JS},
        'id': '7ac1f25c-fa4f-4afd-b803-f578ffe1e4b5',
        'name': 'Format: Get Booking Response',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [1408, 6672]},
    {   'parameters': {   'respondWith': 'json',
                          'responseBody': "={{ { success: false, error: 'Validation failed: ' + $json._validationError "
                                          '} }}',
                          'options': {}},
        'id': '57bb8241-bcea-41ba-89ce-2d20af90d890',
        'name': 'Respond: Get Booking Validation Error',
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1,
        'position': [1184, 6960]},
    {   'parameters': {   'respondWith': 'json',
                          'responseBody': '={{ { success: false, error: \'Unknown tool: "\' + $json.tool + \'". Valid '
                                          'tools are: get-services, get-slots, get-staff, book-appointment, '
                                          "cancel-booking, reschedule-booking, get-booking' } }}",
                          'options': {}},
        'id': '3a4a697b-14c1-431a-9615-f43753dbeac3',
        'name': 'Respond: Unknown Tool Error',
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1,
        'position': [736, 6288]},
    {   'parameters': {   'respondWith': 'json',
                          'responseBody': '{\n  "success": false,\n  "error": "Error getting slots"\n}',
                          'options': {}},
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1.5,
        'position': [1408, 4848],
        'id': '2a937dbb-25c5-4c5d-8e24-da89628866e9',
        'name': 'Error: Get Slots'},
    {   'parameters': {   'respondWith': 'json',
                          'responseBody': '{\n  "success": false,\n  "error": "Error getting staff"\n}',
                          'options': {}},
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1.5,
        'position': [960, 5136],
        'id': 'c07856aa-d435-412b-93e3-dd737394c23b',
        'name': 'Error: Get Staff'},
    {   'parameters': {   'respondWith': 'json',
                          'responseBody': '{\n  "success": false,\n  "error": "Error booking service"\n}',
                          'options': {}},
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1.5,
        'position': [2976, 5328],
        'id': 'ff6822d5-b9d9-4e0f-9d8d-0ac92fc6e438',
        'name': 'Error: Create Booking'},
    {   'parameters': {   'respondWith': 'json',
                          'responseBody': '{\n  "success": false,\n  "error": "Error cancelling booking"\n}',
                          'options': {}},
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1.5,
        'position': [1408, 5712],
        'id': '2fd21723-696d-4066-b996-ced2695584f5',
        'name': 'Error: Cancel Booking'},
    {   'parameters': {   'respondWith': 'json',
                          'responseBody': '{\n  "success": false,\n  "error": "Error rescheduling booking"\n}',
                          'options': {}},
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1.5,
        'position': [1408, 6096],
        'id': '70d7a2cf-93c3-4935-85a1-59e9cd3c0cea',
        'name': 'Error: Rescheduling'},
    {   'parameters': {   'respondWith': 'json',
                          'responseBody': '{\n  "success": false,\n  "error": "Error getting booking"\n}',
                          'options': {}},
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1.5,
        'position': [1408, 6864],
        'id': '88fe355f-448f-4fec-9463-e375cae3ffe0',
        'name': 'Error: Getting Booking'},
    {   'parameters': {   'respondWith': 'json',
                          'responseBody': '={{ { success: $json.success, mode: $json.mode, count: $json.count, '
                                          'availabilityByDay: $json.availabilityByDay } }}',
                          'options': {}},
        'id': '92a48d76-8c33-4a30-9b95-919790e34690',
        'name': 'Respond: Get Slots',
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1,
        'position': [1632, 4464]},
    {   'parameters': {'respondWith': 'json', 'responseBody': '={{ $json }}', 'options': {}},
        'id': 'a9520b53-c86e-41d4-ac9a-f5eb687d6eff',
        'name': 'Respond: Get Staff',
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1,
        'position': [1184, 4944]},
    {   'parameters': {'respondWith': 'json', 'responseBody': '={{ $json }}', 'options': {}},
        'id': 'ce7fcba6-2aad-45dd-9cd7-40a6ffc5fc8b',
        'name': 'Respond: Cancel Booking',
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1,
        'position': [1632, 5504]},
    {   'parameters': {'respondWith': 'json', 'responseBody': '={{ $json }}', 'options': {}},
        'id': 'b420b431-959e-4c66-9200-c731c69e8fcd',
        'name': 'Respond: Book Appointment',
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1,
        'position': [3200, 4976]},
    {   'parameters': {'respondWith': 'json', 'responseBody': '={{ $json }}', 'options': {}},
        'id': '05bcacb9-44d7-419c-b6a3-e621d64f76be',
        'name': 'Respond: Reschedule Booking',
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1,
        'position': [1632, 5904]},
    {   'parameters': {'respondWith': 'json', 'responseBody': '={{ $json }}', 'options': {}},
        'id': '4dafdc84-685f-402c-b6c0-5eaf6839e349',
        'name': 'Respond: Get Booking',
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1,
        'position': [1632, 6672]},
    {   'parameters': {'jsCode': VALIDATE_FLAG_CALLBACK_JS},
        'id': '2c141283-2106-40ed-bc3c-be9ab2b9343d',
        'name': 'Validate: Flag Callback Args',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [736, 6480]},
    {   'parameters': {'conditions': {'boolean': [{'value1': '={{ $json._valid }}', 'value2': True}]}},
        'id': '950e1daa-0800-4bd2-a6ba-bd5e3c32a48e',
        'name': 'IF: Flag Callback Args Valid',
        'type': 'n8n-nodes-base.if',
        'typeVersion': 1,
        'position': [960, 6480]},
    {   'parameters': {   'fromEmail': FROM_EMAIL,
                          'toEmail': CALLBACK_RECIPIENT,
                          'subject': '={{ $json._emailSubject }}',
                          'emailFormat': 'text',
                          'text': '={{ $json._emailBody }}',
                          'options': {'appendAttribution': False, 'replyTo': 'info@aiemply.com'}},
        'id': '4052c464-3506-4078-8e30-98e86a166a5c',
        'name': 'Send Email: Flag Callback',
        'type': 'n8n-nodes-base.emailSend',
        'typeVersion': 2.1,
        'position': [1184, 6384],
        'webhookId': '942f20a6-9eb5-4c9e-b5b4-033da4dc7f25',
        'credentials': {'smtp': {'id': SMTP_CREDENTIAL_ID, 'name': SMTP_CREDENTIAL_NAME}},
        'onError': 'continueErrorOutput'},
    {   'parameters': {'jsCode': FORMAT_FLAG_CALLBACK_RESPONSE_JS},
        'id': 'da511f6c-ac89-455d-a5ab-5c48dfc97b0d',
        'name': 'Format: Flag Callback Response',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [1408, 6288]},
    {   'parameters': {'respondWith': 'json', 'responseBody': '={{ $json }}', 'options': {}},
        'id': 'fdc2e822-d689-41c9-bc90-1ef9c32c8b96',
        'name': 'Respond: Flag Callback',
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1,
        'position': [1632, 6288]},
    {   'parameters': {   'respondWith': 'json',
                          'responseBody': "={{ { success: false, error: 'Validation failed: ' + $json._validationError "
                                          '} }}',
                          'options': {}},
        'id': '2b1d4056-faba-4393-8c8a-1f140f574e55',
        'name': 'Respond: Flag Callback Validation Error',
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1,
        'position': [1184, 6576]},
    {   'parameters': {   'respondWith': 'json',
                          'responseBody': '{\n'
                                          '  "success": false,\n'
                                          '  "error": "Failed to send callback notification email"\n'
                                          '}',
                          'options': {}},
        'id': '8238f8c8-57a2-4f53-ab5e-db79afee2c37',
        'name': 'Error: Flag Callback',
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1.5,
        'position': [1408, 6480]},
    {   'parameters': {'jsCode': VALIDATE_GET_CONTACT_JS},
        'id': '82e2b80f-55f7-408a-b296-16f81b08400c',
        'name': 'Validate: Get Contact',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [736, 7232]},
    {   'parameters': {'conditions': {'boolean': [{'value1': '={{ $json._valid }}', 'value2': True}]}},
        'id': 'e5b453f8-9bd1-4087-b040-fb8bc3c3abf3',
        'name': 'IF: Contact Args Valid',
        'type': 'n8n-nodes-base.if',
        'typeVersion': 1,
        'position': [960, 7232]},
    {   'parameters': {   'method': 'POST',
                          'url': 'https://www.wixapis.com/contacts/v4/contacts/query',
                          'authentication': 'predefinedCredentialType',
                          'nodeCredentialType': 'wixApi',
                          'sendBody': True,
                          'specifyBody': 'json',
                          'jsonBody': WIX_SEARCH_CONTACT_BODY,
                          'options': {}},
        'id': 'e5215f99-d5ea-4014-9544-70456b6615d2',
        'name': 'Wix: Search Contact',
        'type': 'n8n-nodes-base.httpRequest',
        'typeVersion': 4.1,
        'position': [1184, 7152],
        'credentials': {'wixApi': {'id': WIX_CREDENTIAL_ID, 'name': WIX_CREDENTIAL_NAME}},
        'continueOnFail': True,
        'onError': 'continueErrorOutput'},
    {   'parameters': {'jsCode': FORMAT_CONTACT_RESPONSE_JS},
        'id': '37c17857-4462-4bd7-b4f1-fb11fc28450a',
        'name': 'Format: Contact Response',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [1408, 7056]},
    {   'parameters': {'respondWith': 'json', 'responseBody': '={{ $json }}', 'options': {}},
        'id': '91f08f82-16d8-4a74-a8f8-0678d7ae3fc5',
        'name': 'Respond: Get Contact',
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1,
        'position': [1632, 7056]},
    {   'parameters': {   'respondWith': 'json',
                          'responseBody': "={{ { success: false, error: 'Validation failed: ' + $json._validationError "
                                          '} }}',
                          'options': {}},
        'id': 'd56384bb-86a7-42e1-a18c-ae99634bed69',
        'name': 'Respond: Contact Error',
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1,
        'position': [1408, 7328]},
    {   'parameters': {   'method': 'POST',
                          'url': 'https://www.wixapis.com/contacts/v4/contacts',
                          'authentication': 'predefinedCredentialType',
                          'nodeCredentialType': 'wixApi',
                          'sendBody': True,
                          'specifyBody': 'json',
                          'jsonBody': WIX_CREATE_CONTACT_BODY,
                          'options': {}},
        'id': 'da6a04ba-870c-4a54-b8b5-8eb8a6d09c37',
        'name': 'Wix: Create Contact',
        'type': 'n8n-nodes-base.httpRequest',
        'typeVersion': 4.1,
        'position': [1856, 5312],
        'credentials': {'wixApi': {'id': WIX_CREDENTIAL_ID, 'name': WIX_CREDENTIAL_NAME}},
        'continueOnFail': True,
        'onError': 'continueErrorOutput'},
    {   'parameters': {'jsCode': FORMAT_CREATE_CONTACT_JS},
        'id': 'ed3b5e00-0d91-449b-9c5a-b36817707a3a',
        'name': 'Format: Create Contact',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [2080, 5232]},
    {   'parameters': {   'method': 'POST',
                          'url': 'https://www.wixapis.com/contacts/v4/contacts/query',
                          'authentication': 'predefinedCredentialType',
                          'nodeCredentialType': 'wixApi',
                          'sendBody': True,
                          'specifyBody': 'json',
                          'jsonBody': WIX_SEARCH_CONTACT_1_BODY,
                          'options': {}},
        'id': 'd39cd711-35f2-4a0a-9512-e25c453ec74c',
        'name': 'Wix: Search Contact1',
        'type': 'n8n-nodes-base.httpRequest',
        'typeVersion': 4.1,
        'position': [1184, 5232],
        'credentials': {'wixApi': {'id': WIX_CREDENTIAL_ID, 'name': WIX_CREDENTIAL_NAME}},
        'continueOnFail': True,
        'onError': 'continueErrorOutput'},
    {   'parameters': {'jsCode': FORMAT_CONTACT_RESPONSE_1_JS},
        'id': '8f721862-b202-4b2b-bc9c-de102ed636d6',
        'name': 'Format: Contact Response1',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [1408, 5040]},
    {   'parameters': {   'conditions': {   'options': {   'caseSensitive': True,
                                                           'leftValue': '',
                                                           'typeValidation': 'strict',
                                                           'version': 3},
                                            'conditions': [   {   'id': '6f49af7b-0308-4dad-90b9-d80823256087',
                                                                  'leftValue': '={{ $json.found }}',
                                                                  'rightValue': True,
                                                                  'operator': {   'type': 'boolean',
                                                                                  'operation': 'equals'}}],
                                            'combinator': 'and'},
                          'options': {}},
        'type': 'n8n-nodes-base.if',
        'typeVersion': 2.3,
        'position': [1632, 5040],
        'id': '5adaf0f6-057b-41ff-bd1a-1a89f680cd65',
        'name': 'If: Contact Found'},
    {   'parameters': {   'method': 'POST',
                          'url': 'https://www.wixapis.com/bookings/v2/services/query',
                          'authentication': 'predefinedCredentialType',
                          'nodeCredentialType': 'wixApi',
                          'sendBody': True,
                          'specifyBody': 'json',
                          'jsonBody': WIX_QUERY_SERVICES_BODY,
                          'options': {}},
        'id': '3ccf9c7e-2def-4adf-8bd9-fa87015f1a6b',
        'name': 'Wix: Query Services',
        'type': 'n8n-nodes-base.httpRequest',
        'typeVersion': 4.1,
        'position': [736, 4112],
        'credentials': {'wixApi': {'id': WIX_CREDENTIAL_ID, 'name': WIX_CREDENTIAL_NAME}},
        'continueOnFail': True,
        'onError': 'continueErrorOutput'},
    {   'parameters': {'jsCode': EXTRACT_PRICING_IDS_JS},
        'id': '3c65717b-f1f1-4900-b90e-7e9fb2b2323d',
        'name': 'Extract Pricing IDs',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [960, 4016]},
    {   'parameters': {'conditions': {'boolean': [{'value1': '={{ $json.hasVaried }}', 'value2': True}]}},
        'id': '6c581580-5ea9-49c9-81fb-17dea298e5a2',
        'name': 'IF: Has Varied',
        'type': 'n8n-nodes-base.if',
        'typeVersion': 1,
        'position': [1184, 4016]},
    {   'parameters': {   'url': '=https://www.wixapis.com/bookings/v1/serviceOptionsAndVariants/service_id/{{ '
                                 '$json.serviceId }}',
                          'authentication': 'predefinedCredentialType',
                          'nodeCredentialType': 'wixApi',
                          'options': {}},
        'id': '14b40d9f-4584-4878-b73c-02cb4d62da40',
        'name': 'Wix: Get Pricing Variants',
        'type': 'n8n-nodes-base.httpRequest',
        'typeVersion': 4.1,
        'position': [1408, 3936],
        'credentials': {'wixApi': {'id': WIX_CREDENTIAL_ID, 'name': WIX_CREDENTIAL_NAME}},
        'continueOnFail': True,
        'onError': 'continueErrorOutput'},
    {   'parameters': {'jsCode': EXTRACT_ADD_ON_IDS_JS},
        'id': 'ec2344b4-48f6-4d09-a6eb-6269e08e52d6',
        'name': 'Extract Add-on IDs',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [1632, 4016]},
    {   'parameters': {'conditions': {'boolean': [{'value1': '={{ $json.hasAddOns }}', 'value2': True}]}},
        'id': '20726950-5780-4eaf-b1e1-37b9c88b7e3c',
        'name': 'IF: Has Add-ons',
        'type': 'n8n-nodes-base.if',
        'typeVersion': 1,
        'position': [1856, 4016]},
    {   'parameters': {   'url': '=https://manage.wix.com/_api/add-ons-service/v1/add-ons/{{ $json.addOnId }}',
                          'authentication': 'predefinedCredentialType',
                          'nodeCredentialType': 'wixApi',
                          'options': {}},
        'id': '67139663-d54b-4f14-8894-d3cf48b581d4',
        'name': 'Wix: Get Add-ons',
        'type': 'n8n-nodes-base.httpRequest',
        'typeVersion': 4.4,
        'position': [2080, 3936],
        'credentials': {'wixApi': {'id': WIX_CREDENTIAL_ID, 'name': WIX_CREDENTIAL_NAME}},
        'continueOnFail': True},
    {   'parameters': {'jsCode': FORMAT_SERVICES_RESPONSE_JS},
        'id': 'a09d7308-f609-4506-bb8a-c5aa6f17d549',
        'name': 'Format: Services Response',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [2304, 4016]},
    {   'parameters': {   'respondWith': 'json',
                          'responseBody': '{\n  "success": false,\n  "error": "Error getting services"\n}',
                          'options': {}},
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1.5,
        'position': [1632, 4208],
        'id': 'd13422bc-1323-427e-87fe-b968491b37f1',
        'name': 'Error: Get Services'},
    {   'parameters': {'respondWith': 'json', 'responseBody': '={{ $json }}', 'options': {}},
        'id': '2f163724-97c9-4651-b00c-583aa273c9ac',
        'name': 'Respond: Get Services',
        'type': 'n8n-nodes-base.respondToWebhook',
        'typeVersion': 1,
        'position': [2528, 4016]},
    {   'parameters': {   'rules': {   'values': [   {   'conditions': {   'options': {   'caseSensitive': True,
                                                                                          'leftValue': '',
                                                                                          'typeValidation': 'strict',
                                                                                          'version': 3},
                                                                           'conditions': [   {   'id': 'rule-get-services',
                                                                                                 'leftValue': '={{ '
                                                                                                              '$json.tool '
                                                                                                              '}}',
                                                                                                 'rightValue': 'get-services',
                                                                                                 'operator': {   'type': 'string',
                                                                                                                 'operation': 'equals',
                                                                                                                 'name': 'filter.operator.equals'}}],
                                                                           'combinator': 'and'},
                                                         'renameOutput': True,
                                                         'outputKey': 'Get Services'},
                                                     {   'conditions': {   'options': {   'caseSensitive': True,
                                                                                          'leftValue': '',
                                                                                          'typeValidation': 'strict',
                                                                                          'version': 3},
                                                                           'conditions': [   {   'id': 'rule-get-slots',
                                                                                                 'leftValue': '={{ '
                                                                                                              '$json.tool '
                                                                                                              '}}',
                                                                                                 'rightValue': 'get-slots',
                                                                                                 'operator': {   'type': 'string',
                                                                                                                 'operation': 'equals',
                                                                                                                 'name': 'filter.operator.equals'}}],
                                                                           'combinator': 'and'},
                                                         'renameOutput': True,
                                                         'outputKey': 'Get Slots'},
                                                     {   'conditions': {   'options': {   'caseSensitive': True,
                                                                                          'leftValue': '',
                                                                                          'typeValidation': 'strict',
                                                                                          'version': 3},
                                                                           'conditions': [   {   'id': 'rule-get-staff',
                                                                                                 'leftValue': '={{ '
                                                                                                              '$json.tool '
                                                                                                              '}}',
                                                                                                 'rightValue': 'get-staff',
                                                                                                 'operator': {   'type': 'string',
                                                                                                                 'operation': 'equals',
                                                                                                                 'name': 'filter.operator.equals'}}],
                                                                           'combinator': 'and'},
                                                         'renameOutput': True,
                                                         'outputKey': 'Get Staff'},
                                                     {   'conditions': {   'options': {   'caseSensitive': True,
                                                                                          'leftValue': '',
                                                                                          'typeValidation': 'strict',
                                                                                          'version': 3},
                                                                           'conditions': [   {   'id': 'rule-book-appointment',
                                                                                                 'leftValue': '={{ '
                                                                                                              '$json.tool '
                                                                                                              '}}',
                                                                                                 'rightValue': 'book-appointment',
                                                                                                 'operator': {   'type': 'string',
                                                                                                                 'operation': 'equals',
                                                                                                                 'name': 'filter.operator.equals'}}],
                                                                           'combinator': 'and'},
                                                         'renameOutput': True,
                                                         'outputKey': 'Book Appointment'},
                                                     {   'conditions': {   'options': {   'caseSensitive': True,
                                                                                          'leftValue': '',
                                                                                          'typeValidation': 'strict',
                                                                                          'version': 3},
                                                                           'conditions': [   {   'id': 'rule-cancel-booking',
                                                                                                 'leftValue': '={{ '
                                                                                                              '$json.tool '
                                                                                                              '}}',
                                                                                                 'rightValue': 'cancel-booking',
                                                                                                 'operator': {   'type': 'string',
                                                                                                                 'operation': 'equals',
                                                                                                                 'name': 'filter.operator.equals'}}],
                                                                           'combinator': 'and'},
                                                         'renameOutput': True,
                                                         'outputKey': 'Cancel Booking'},
                                                     {   'conditions': {   'options': {   'caseSensitive': True,
                                                                                          'leftValue': '',
                                                                                          'typeValidation': 'strict',
                                                                                          'version': 3},
                                                                           'conditions': [   {   'id': 'rule-reschedule-booking',
                                                                                                 'leftValue': '={{ '
                                                                                                              '$json.tool '
                                                                                                              '}}',
                                                                                                 'rightValue': 'reschedule-booking',
                                                                                                 'operator': {   'type': 'string',
                                                                                                                 'operation': 'equals',
                                                                                                                 'name': 'filter.operator.equals'}}],
                                                                           'combinator': 'and'},
                                                         'renameOutput': True,
                                                         'outputKey': 'Reschedule Booking'},
                                                     {   'conditions': {   'options': {   'caseSensitive': True,
                                                                                          'leftValue': '',
                                                                                          'typeValidation': 'strict',
                                                                                          'version': 3},
                                                                           'conditions': [   {   'id': 'rule-get-booking',
                                                                                                 'leftValue': '={{ '
                                                                                                              '$json.tool '
                                                                                                              '}}',
                                                                                                 'rightValue': 'get-booking',
                                                                                                 'operator': {   'type': 'string',
                                                                                                                 'operation': 'equals',
                                                                                                                 'name': 'filter.operator.equals'}}],
                                                                           'combinator': 'and'},
                                                         'renameOutput': True,
                                                         'outputKey': 'Get Booking'},
                                                     {   'conditions': {   'options': {   'caseSensitive': True,
                                                                                          'leftValue': '',
                                                                                          'typeValidation': 'strict',
                                                                                          'version': 3},
                                                                           'conditions': [   {   'id': 'rule-flag-callback',
                                                                                                 'leftValue': '={{ '
                                                                                                              '$json.tool '
                                                                                                              '}}',
                                                                                                 'rightValue': 'flag-callback',
                                                                                                 'operator': {   'type': 'string',
                                                                                                                 'operation': 'equals',
                                                                                                                 'name': 'filter.operator.equals'}}],
                                                                           'combinator': 'and'},
                                                         'renameOutput': True,
                                                         'outputKey': 'Flag Callback'},
                                                     {   'conditions': {   'options': {   'caseSensitive': True,
                                                                                          'leftValue': '',
                                                                                          'typeValidation': 'strict',
                                                                                          'version': 3},
                                                                           'conditions': [   {   'id': '0138ed3c-4efc-4ce4-a7a9-cef8e1fc01de',
                                                                                                 'leftValue': '={{ '
                                                                                                              '$json.tool '
                                                                                                              '}}',
                                                                                                 'rightValue': 'get-contact',
                                                                                                 'operator': {   'type': 'string',
                                                                                                                 'operation': 'equals',
                                                                                                                 'name': 'filter.operator.equals'}}],
                                                                           'combinator': 'and'},
                                                         'renameOutput': True,
                                                         'outputKey': 'Get Contact'}]},
                          'options': {'fallbackOutput': 'extra', 'renameFallbackOutput': 'Fallback'}},
        'id': '8bbdac8e-7499-413d-8fbd-35b2a4887336',
        'name': 'Route by Tool',
        'type': 'n8n-nodes-base.switch',
        'typeVersion': 3.4,
        'position': [512, 5776]}]


# -----------------------------------------------------------------------------
# Connections (full canonical wiring)
# -----------------------------------------------------------------------------

CONNECTIONS = {   'Webhook — Retell Tool Call': {'main': [[{'node': 'Parse Retell Payload', 'type': 'main', 'index': 0}]]},
    'Parse Retell Payload': {'main': [[{'node': 'Route by Tool', 'type': 'main', 'index': 0}]]},
    'Validate: Slots Args': {'main': [[{'node': 'IF: Slots Args Valid', 'type': 'main', 'index': 0}]]},
    'IF: Slots Args Valid': {   'main': [   [{'node': 'Wix: Query Time Slots', 'type': 'main', 'index': 0}],
                                            [{'node': 'Respond: Slots Validation Error', 'type': 'main', 'index': 0}]]},
    'Wix: Query Time Slots': {   'main': [   [{'node': 'Format: Time Slots Response', 'type': 'main', 'index': 0}],
                                             [{'node': 'Error: Get Slots', 'type': 'main', 'index': 0}]]},
    'Format: Time Slots Response': {'main': [[{'node': 'Respond: Get Slots', 'type': 'main', 'index': 0}]]},
    'Wix: Query Staff Members': {   'main': [   [{'node': 'Format: Staff Response', 'type': 'main', 'index': 0}],
                                                [{'node': 'Error: Get Staff', 'type': 'main', 'index': 0}]]},
    'Format: Staff Response': {'main': [[{'node': 'Respond: Get Staff', 'type': 'main', 'index': 0}]]},
    'Validate: Booking Args': {'main': [[{'node': 'IF: Booking Args Valid', 'type': 'main', 'index': 0}]]},
    'IF: Booking Args Valid': {   'main': [   [{'node': 'Wix: Search Contact1', 'type': 'main', 'index': 0}],
                                              [   {   'node': 'Respond: Booking Validation Error',
                                                      'type': 'main',
                                                      'index': 0}]]},
    'Wix: Create Booking': {   'main': [   [{'node': 'IF: Booking Created OK', 'type': 'main', 'index': 0}],
                                           [{'node': 'Error: Create Booking', 'type': 'main', 'index': 0}]]},
    'IF: Booking Created OK': {   'main': [   [{'node': 'Wix: Confirm Booking', 'type': 'main', 'index': 0}],
                                              [{'node': 'Error: Create Booking', 'type': 'main', 'index': 0}]]},
    'Wix: Confirm Booking': {   'main': [   [{'node': 'Format: Booking Confirmation', 'type': 'main', 'index': 0}],
                                            [{'node': 'Error: Create Booking', 'type': 'main', 'index': 0}]]},
    'Format: Booking Confirmation': {'main': [[{'node': 'Respond: Book Appointment', 'type': 'main', 'index': 0}]]},
    'Validate: Cancel Args': {'main': [[{'node': 'IF: Cancel Args Valid', 'type': 'main', 'index': 0}]]},
    'IF: Cancel Args Valid': {   'main': [   [{'node': 'Wix: Cancel Booking', 'type': 'main', 'index': 0}],
                                             [   {   'node': 'Respond: Cancel Validation Error',
                                                     'type': 'main',
                                                     'index': 0}]]},
    'Wix: Cancel Booking': {   'main': [   [{'node': 'Format: Cancel Response', 'type': 'main', 'index': 0}],
                                           [{'node': 'Error: Cancel Booking', 'type': 'main', 'index': 0}]]},
    'Format: Cancel Response': {'main': [[{'node': 'Respond: Cancel Booking', 'type': 'main', 'index': 0}]]},
    'Validate: Reschedule Args': {'main': [[{'node': 'IF: Reschedule Args Valid', 'type': 'main', 'index': 0}]]},
    'IF: Reschedule Args Valid': {   'main': [   [{'node': 'Wix: Reschedule Booking', 'type': 'main', 'index': 0}],
                                                 [   {   'node': 'Respond: Reschedule Validation Error',
                                                         'type': 'main',
                                                         'index': 0}]]},
    'Wix: Reschedule Booking': {   'main': [   [{'node': 'Format: Reschedule Response', 'type': 'main', 'index': 0}],
                                               [{'node': 'Error: Rescheduling', 'type': 'main', 'index': 0}]]},
    'Format: Reschedule Response': {'main': [[{'node': 'Respond: Reschedule Booking', 'type': 'main', 'index': 0}]]},
    'Validate: Get Booking Args': {'main': [[{'node': 'IF: Get Booking Args Valid', 'type': 'main', 'index': 0}]]},
    'IF: Get Booking Args Valid': {   'main': [   [{'node': 'Wix: Get Booking', 'type': 'main', 'index': 0}],
                                                  [   {   'node': 'Respond: Get Booking Validation Error',
                                                          'type': 'main',
                                                          'index': 0}]]},
    'Wix: Get Booking': {   'main': [   [{'node': 'Format: Get Booking Response', 'type': 'main', 'index': 0}],
                                        [{'node': 'Error: Getting Booking', 'type': 'main', 'index': 0}]]},
    'Format: Get Booking Response': {'main': [[{'node': 'Respond: Get Booking', 'type': 'main', 'index': 0}]]},
    'Validate: Flag Callback Args': {'main': [[{'node': 'IF: Flag Callback Args Valid', 'type': 'main', 'index': 0}]]},
    'IF: Flag Callback Args Valid': {   'main': [   [{'node': 'Send Email: Flag Callback', 'type': 'main', 'index': 0}],
                                                    [   {   'node': 'Respond: Flag Callback Validation Error',
                                                            'type': 'main',
                                                            'index': 0}]]},
    'Send Email: Flag Callback': {   'main': [   [   {   'node': 'Format: Flag Callback Response',
                                                         'type': 'main',
                                                         'index': 0}],
                                                 [{'node': 'Error: Flag Callback', 'type': 'main', 'index': 0}]]},
    'Format: Flag Callback Response': {'main': [[{'node': 'Respond: Flag Callback', 'type': 'main', 'index': 0}]]},
    'Validate: Get Contact': {'main': [[{'node': 'IF: Contact Args Valid', 'type': 'main', 'index': 0}]]},
    'IF: Contact Args Valid': {   'main': [   [{'node': 'Wix: Search Contact', 'type': 'main', 'index': 0}],
                                              [{'node': 'Respond: Contact Error', 'type': 'main', 'index': 0}]]},
    'Wix: Search Contact': {   'main': [   [{'node': 'Format: Contact Response', 'type': 'main', 'index': 0}],
                                           [{'node': 'Respond: Contact Error', 'type': 'main', 'index': 0}]]},
    'Format: Contact Response': {'main': [[{'node': 'Respond: Get Contact', 'type': 'main', 'index': 0}]]},
    'Wix: Create Contact': {   'main': [   [{'node': 'Format: Create Contact', 'type': 'main', 'index': 0}],
                                           [{'node': 'Error: Create Booking', 'type': 'main', 'index': 0}]]},
    'Format: Create Contact': {'main': [[{'node': 'Wix: Create Booking', 'type': 'main', 'index': 0}]]},
    'Wix: Search Contact1': {   'main': [   [{'node': 'Format: Contact Response1', 'type': 'main', 'index': 0}],
                                            [{'node': 'Wix: Create Contact', 'type': 'main', 'index': 0}]]},
    'Format: Contact Response1': {'main': [[{'node': 'If: Contact Found', 'type': 'main', 'index': 0}]]},
    'If: Contact Found': {   'main': [   [{'node': 'Wix: Create Booking', 'type': 'main', 'index': 0}],
                                         [{'node': 'Wix: Create Contact', 'type': 'main', 'index': 0}]]},
    'Wix: Query Services': {   'main': [   [{'node': 'Extract Pricing IDs', 'type': 'main', 'index': 0}],
                                           [{'node': 'Error: Get Services', 'type': 'main', 'index': 0}]]},
    'Extract Pricing IDs': {'main': [[{'node': 'IF: Has Varied', 'type': 'main', 'index': 0}]]},
    'IF: Has Varied': {   'main': [   [{'node': 'Wix: Get Pricing Variants', 'type': 'main', 'index': 0}],
                                      [{'node': 'Extract Add-on IDs', 'type': 'main', 'index': 0}]]},
    'Wix: Get Pricing Variants': {   'main': [   [{'node': 'Extract Add-on IDs', 'type': 'main', 'index': 0}],
                                                 [{'node': 'Error: Get Services', 'type': 'main', 'index': 0}]]},
    'Extract Add-on IDs': {'main': [[{'node': 'IF: Has Add-ons', 'type': 'main', 'index': 0}]]},
    'IF: Has Add-ons': {   'main': [   [{'node': 'Wix: Get Add-ons', 'type': 'main', 'index': 0}],
                                       [{'node': 'Format: Services Response', 'type': 'main', 'index': 0}]]},
    'Wix: Get Add-ons': {'main': [[{'node': 'Format: Services Response', 'type': 'main', 'index': 0}]]},
    'Format: Services Response': {'main': [[{'node': 'Respond: Get Services', 'type': 'main', 'index': 0}]]},
    'Route by Tool': {   'main': [   [{'node': 'Wix: Query Services', 'type': 'main', 'index': 0}],
                                     [{'node': 'Validate: Slots Args', 'type': 'main', 'index': 0}],
                                     [{'node': 'Wix: Query Staff Members', 'type': 'main', 'index': 0}],
                                     [{'node': 'Validate: Booking Args', 'type': 'main', 'index': 0}],
                                     [{'node': 'Validate: Cancel Args', 'type': 'main', 'index': 0}],
                                     [{'node': 'Validate: Reschedule Args', 'type': 'main', 'index': 0}],
                                     [{'node': 'Validate: Get Booking Args', 'type': 'main', 'index': 0}],
                                     [{'node': 'Validate: Flag Callback Args', 'type': 'main', 'index': 0}],
                                     [{'node': 'Validate: Get Contact', 'type': 'main', 'index': 0}],
                                     [{'node': 'Respond: Unknown Tool Error', 'type': 'main', 'index': 0}]]}}


# -----------------------------------------------------------------------------
# Meta + pinData
# -----------------------------------------------------------------------------

META = {'instanceId': 'ac196cde23a3d6ef70e5e219252c1746cd31eed638b30f72c27ae62726c49a9f'}

PIN_DATA = {}


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    wf = {
        "nodes": NODES,
        "connections": CONNECTIONS,
        "pinData": PIN_DATA,
        "meta": META,
    }
    WF_PATH.write_text(
        json.dumps(wf, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Wrote {WF_PATH}")
    print(f"  Nodes: {len(NODES)}")
    route_rules = next(
        (n['parameters']['rules']['values']
         for n in NODES if n.get('name') == 'Route by Tool'),
        [],
    )
    print(f"  Switch rules: {len(route_rules)}")
    print(f"  Flag-callback recipient: {CALLBACK_RECIPIENT}")


if __name__ == "__main__":
    main()
