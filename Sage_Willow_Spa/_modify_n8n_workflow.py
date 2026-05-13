"""
Modify the n8n workflow:

  1. Update `Parse Retell Payload` — handle args_at_root: true (the
     production-validated default — args spread at body root, no body.call).
  2. Update `Validate: Slots Args` — normalize new optional filter args
     (staffId, timeOfDay, earliestFirst, limit).
  3. Update `Format: Time Slots Response` — apply filters, support
     earliestFirst flat mode, and cap slots per band in grouped mode.
  4. Update `Validate: Get Booking Args` — email-based lookup
     (replaces phone-based; phone fallback removed).
  5. Update `Wix: Get Booking` request body — filter on contactDetails.email
     instead of contactDetails.phone.
  6. Add `flag-callback` route — new switch rule + 7 nodes + connections.
     Email goes to engineering@aiemply.com via existing SMTP credential.

Run:  py -X utf8 _modify_n8n_workflow.py
"""

from __future__ import annotations
import json
from pathlib import Path

WF_PATH = Path(__file__).parent / "Retell AI ↔ Wix Bookings _ Production v2.json"

CALLBACK_RECIPIENT = "engineering@aiemply.com"
SMTP_CREDENTIAL_ID = "m0mbibKf6il36id5"
SMTP_CREDENTIAL_NAME = "SMTP account"
FROM_EMAIL = "Aria <contact@aiemply.com>"


# -----------------------------------------------------------------------------
# Replacement JS for the Retell payload parser
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


# -----------------------------------------------------------------------------
# Replacement JS for the slots validator + formatter
# -----------------------------------------------------------------------------

VALIDATE_SLOTS_JS = r"""const inputJson = $input.first().json;
const { args } = inputJson;
const errors = [];

if (!args.serviceId) errors.push('serviceId is required');
if (!args.startDate) errors.push('startDate is required');
if (!args.endDate) errors.push('endDate is required');

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

// Day-of-week from "YYYY-MM-DD" local date (independent of server timezone).
const DOW_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
function localDayOfWeek(localDate) {
    if (!localDate) return null;
    const m = String(localDate).match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (!m) return null;
    return DOW_NAMES[new Date(Date.UTC(+m[1], +m[2] - 1, +m[3])).getUTCDay()];
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
        localDate: s.localDate,
        dayOfWeek: localDayOfWeek(s.localDate),
        time: s.time,
        startDate: s.startDate,
        endDate: s.endDate,
        scheduleId: s.scheduleId,
        // The agent uses the staffId from the chosen entry of availableTherapists
        // when caller picks a specific therapist; OMITS staffId entirely when
        // caller has no preference (Wix auto-assigns at confirmation).
        availableTherapists: s.therapists.map(t => ({ name: t.name, staffId: t.staffId })),
        location: s.location,
        remainingCapacity: s.remainingCapacity,
        totalCapacity: s.totalCapacity
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
            scheduleId: e.scheduleId || null,
            location: e.location || null,
            remainingCapacity: e.remainingCapacity ?? null,
            totalCapacity: e.totalCapacity ?? null
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

return [{ json: { success: true, mode: 'grouped', count: totalReturned, filterApplied, availabilityByDay } }];
"""


# -----------------------------------------------------------------------------
# Resource type lookup (so Wix returns therapist names per slot)
# -----------------------------------------------------------------------------
# Wix's List Availability Time Slots returns availableResources as []
# UNLESS we pass `includeResourceTypeIds`. We can't pass that without first
# knowing the staff_member resource type ID. Solution: query the Resource
# Types V3 endpoint, find the staff_member type, cache in workflow static
# data, and pass it on every subsequent slots query.

# Body shape from the Wix QueryResourceTypes docs (cursorPaging required).
WIX_QUERY_RESOURCE_TYPES_BODY = (
    "{\n"
    "  \"query\": {\n"
    "    \"cursorPaging\": {\n"
    "      \"limit\": 100\n"
    "    }\n"
    "  }\n"
    "}"
)

# -----------------------------------------------------------------------------
# Staff resource type ID — set once, baked literally into slots + booking bodies.
# -----------------------------------------------------------------------------
# To get the value: import the workflow, open the `Wix: Query Resource Types`
# node (standalone — not wired in), click "Execute Node", and look for the
# entry in `resourceTypes[]` whose `name` is "staff_member" (Wix default for
# the staff resource type). Copy its `id`. Paste it as the value below.
#
# When empty, the slots query omits `includeResourceTypeIds` (so
# availableResources will be []) and the booking body omits
# `resourceSelections` entirely.
STAFF_RESOURCE_TYPE_ID = "1cd44cf8-756f-41c3-bd90-3e2ffcaf1155"  # from your pinned data

# Wix V2 LIST timeSlots filter rules:
#   - `includeResourceTypeIds` adds response detail (populates availableResources)
#     but does NOT filter slots.
#   - `resourceTypes: [{ resourceTypeId, resourceIds: [...] }]` filters slots
#     server-side to only those served by the listed resources.
#   - A loose `resourceId` at the body root is silently ignored.
#
# So: when staffId is provided, use `resourceTypes` for server-side narrowing.
# When not, use `includeResourceTypeIds` so the response still carries staff
# names per slot.
WIX_QUERY_TIME_SLOTS_BODY = (
    "={\n"
    "  \"serviceId\": \"{{ $json.args.serviceId }}\",\n"
    "  \"fromLocalDate\": \"{{ $json.args.startDate }}\",\n"
    "  \"toLocalDate\": \"{{ $json.args.endDate }}\",\n"
    "  \"timeZone\": \"America/Los_Angeles\"\n"
    + (
        "  {{ $json.args.staffId "
        f"? ', \"resourceTypes\": [{{ \"resourceTypeId\": \"{STAFF_RESOURCE_TYPE_ID}\", \"resourceIds\": [\"' + $json.args.staffId + '\"] }}]' "
        f": ', \"includeResourceTypeIds\": [\"{STAFF_RESOURCE_TYPE_ID}\"]' }}}}\n"
        if STAFF_RESOURCE_TYPE_ID else ""
    )
    + "}"
)


# -----------------------------------------------------------------------------
# Booking — staffId optional + addOns now array of {id, groupId} objects
# -----------------------------------------------------------------------------

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
if (!args.variantId) errors.push('variantId is required for this service');

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

# Build the resourceSelections fragment from the Python constant. When
# STAFF_RESOURCE_TYPE_ID is set, the booking always includes a
# resourceSelections entry — SPECIFIC_RESOURCE when caller named a therapist,
# ANY_RESOURCE when they had no preference. When the constant is empty, the
# entire fragment is omitted (Wix falls back to its default behavior).
_RS_FRAGMENT = ""
if STAFF_RESOURCE_TYPE_ID:
    _RS_FRAGMENT = (
        "        {{ $('IF: Booking Args Valid').item.json.args.staffId "
        f"? ',\"resourceSelections\": [{{ \"resourceTypeId\": \"{STAFF_RESOURCE_TYPE_ID}\", \"selectionMethod\": \"SPECIFIC_RESOURCE\" }}]' "
        f": ',\"resourceSelections\": [{{ \"resourceTypeId\": \"{STAFF_RESOURCE_TYPE_ID}\", \"selectionMethod\": \"ANY_RESOURCE\" }}]' }}}}\n"
    )

WIX_CREATE_BOOKING_BODY = (
    "={\n"
    "  \"booking\": {\n"
    "    \"bookedEntity\": {\n"
    "      \"variantId\": \"{{ $('IF: Booking Args Valid').item.json.args.variantId }}\",\n"
    "      \"slot\": {\n"
    "        \"serviceId\": \"{{ $('IF: Booking Args Valid').item.json.args.serviceId }}\",\n"
    "        \"scheduleId\": \"{{ $('IF: Booking Args Valid').item.json.args.scheduleId }}\",\n"
    "        \"startDate\": \"{{ $('IF: Booking Args Valid').item.json.args.startDate }}\",\n"
    "        \"endDate\": \"{{ $('IF: Booking Args Valid').item.json.args.endDate }}\",\n"
    "        \"timezone\": \"America/Los_Angeles\",\n"
    "        \"location\": {\n"
    "          \"locationType\": \"OWNER_BUSINESS\",\n"
    "          \"id\": \"a345d3c7-2a89-4816-ad3a-277ea40730a7\"\n"
    "        }\n"
    "        {{ $('IF: Booking Args Valid').item.json.args.staffId ? ',\"resource\": { \"id\": \"' + $('IF: Booking Args Valid').item.json.args.staffId + '\" }' : '' }}\n"
    + _RS_FRAGMENT +
    "      }\n"
    "    },\n"
    "    \"contactDetails\": {\n"
    "      \"firstName\": \"{{ $('IF: Booking Args Valid').item.json.args.firstName }}\",\n"
    "      \"lastName\": \"{{ $('IF: Booking Args Valid').item.json.args.lastName }}\",\n"
    "      \"email\": \"{{ $('IF: Booking Args Valid').item.json.args.email }}\",\n"
    "      \"phone\": \"{{ $('IF: Booking Args Valid').item.json.args.phone }}\"\n"
    "    },\n"
    "    \"numberOfParticipants\": 1\n"
    "    {{ $('IF: Booking Args Valid').item.json.args.notes ? ',\"additionalFields\": { \"fields\": [{ \"fieldId\": \"field:note\", \"value\": { \"stringValue\": \"' + $('IF: Booking Args Valid').item.json.args.notes + '\" } }] }' : '' }}\n"
    "    {{ $('IF: Booking Args Valid').item.json.args.addOns?.length > 0 ? ',\"bookedAddOns\": ' + JSON.stringify($('IF: Booking Args Valid').item.json.args.addOns.map(a => ({ id: a.id, groupId: a.groupId, quantity: 1 }))) : '' }}\n"
    "  },\n"
    "  \"flowControlSettings\": {\n"
    "    \"withoutPayment\": true\n"
    "  }\n"
    "}"
)


# -----------------------------------------------------------------------------
# Get-Booking: email (primary) / id / phone (fallback)
# -----------------------------------------------------------------------------

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

WIX_GET_BOOKING_BODY = "={\n  \"query\": {\n    \"filter\": {\n      {{ \n        $json._lookupMode === 'by-id' ? '\"id\": { \"$in\": [\"' + $json.args._resolvedBookingId + '\"]}' : \n        $json._lookupMode === 'by-email' ? '\"contactDetails.email\": \"' + $json.args._resolvedEmail + '\"' : \n        '\"contactDetails.phone\": \"' + $json.args._resolvedPhone + '\"' \n      }},\n      \"status\": { \"$in\": [\"CONFIRMED\", \"PENDING_APPROVAL\", \"CREATED\", \"PENDING\"] }\n    },\n    \"sort\": [{ \"fieldName\": \"createdDate\", \"order\": \"DESC\" }],\n    \"paging\": { \"limit\": 5 }\n  }\n}"


# -----------------------------------------------------------------------------
# Explicit string flags ("yes"/"no") on Get-Booking / Cancel / Reschedule
# responses so Retell branch + prompt logic doesn't have to interpret booleans
# or compare numeric values (the equation engine has been flaky with both).
# -----------------------------------------------------------------------------

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


# -----------------------------------------------------------------------------
# Flag-callback nodes
# -----------------------------------------------------------------------------

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


# -----------------------------------------------------------------------------
# Mutation
# -----------------------------------------------------------------------------

with open(WF_PATH, "r", encoding="utf-8") as f:
    wf = json.load(f)

nodes = wf["nodes"]
nodes_by_name = {n["name"]: n for n in nodes}
connections = wf["connections"]


# 0. Update Parse Retell Payload (handle args_at_root: true)
nodes_by_name["Parse Retell Payload"]["parameters"]["jsCode"] = PARSE_RETELL_PAYLOAD_JS

# 1. Update Validate: Slots Args
nodes_by_name["Validate: Slots Args"]["parameters"]["jsCode"] = VALIDATE_SLOTS_JS

# 2. Update Format: Time Slots Response
nodes_by_name["Format: Time Slots Response"]["parameters"]["jsCode"] = FORMAT_SLOTS_JS

# 2a. Update Wix: Query Time Slots body — adds includeResourceTypeIds so Wix
#     populates availableResources per slot.
nodes_by_name["Wix: Query Time Slots"]["parameters"]["jsonBody"] = WIX_QUERY_TIME_SLOTS_BODY

# 2b. Update Validate: Booking Args — staffId now optional, addOns is array of {id, groupId}.
nodes_by_name["Validate: Booking Args"]["parameters"]["jsCode"] = VALIDATE_BOOKING_JS

# 2c. Update Wix: Create Booking body — resource is conditional on staffId,
#     addOns now passed as full {id, groupId, quantity} objects.
nodes_by_name["Wix: Create Booking"]["parameters"]["jsonBody"] = WIX_CREATE_BOOKING_BODY

# 2d. Update Validate: Get Booking Args (email-based)
nodes_by_name["Validate: Get Booking Args"]["parameters"]["jsCode"] = VALIDATE_GET_BOOKING_JS

# 2e. Update Wix: Get Booking request body (filter on contactDetails.email)
nodes_by_name["Wix: Get Booking"]["parameters"]["jsonBody"] = WIX_GET_BOOKING_BODY

# 2e-flag. Apply explicit-flag formatters to Get Booking / Cancel / Reschedule
# responses so Retell branch logic can rely on a single string field instead of
# numeric counts or boolean coercion.
nodes_by_name["Format: Get Booking Response"]["parameters"]["jsCode"] = FORMAT_GET_BOOKING_JS
nodes_by_name["Format: Cancel Response"]["parameters"]["jsCode"] = FORMAT_CANCEL_JS
nodes_by_name["Format: Reschedule Response"]["parameters"]["jsCode"] = FORMAT_RESCHEDULE_JS

# 2f. Add STANDALONE `Wix: Query Resource Types` node — not wired into the
#     execution flow. User runs it once manually to discover the staff
#     resource type ID, then hardcodes it in STAFF_RESOURCE_TYPE_ID above.
RESOURCE_LOOKUP_NODES = [
    {
        "parameters": {
            "method": "POST",
            "url": "https://www.wixapis.com/bookings/v2/resources/resource-types/query",
            "authentication": "predefinedCredentialType",
            "nodeCredentialType": "wixApi",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": WIX_QUERY_RESOURCE_TYPES_BODY,
            "options": {},
        },
        "id": "node-wix-query-resource-types",
        "name": "Wix: Query Resource Types",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.1,
        "position": [-1008, 800],
        "credentials": {
            "wixApi": {
                "id": "wLpWbblaihcY4xnw",
                "name": "Test: Wix Sage Site",
            }
        },
    },
]
for new in RESOURCE_LOOKUP_NODES:
    nm = new["name"]
    if nm in nodes_by_name:
        idx = next(i for i, n in enumerate(nodes) if n["name"] == nm)
        nodes[idx] = new
    else:
        nodes.append(new)
    nodes_by_name[nm] = new

# 2g. Remove the old Extract: Staff Resource Type ID node and its wiring
#     (no longer needed — STAFF_RESOURCE_TYPE_ID constant is baked literally
#     into the slots + booking bodies above).
extract_name = "Extract: Staff Resource Type ID"
if extract_name in nodes_by_name:
    nodes[:] = [n for n in nodes if n["name"] != extract_name]
    del nodes_by_name[extract_name]
if extract_name in connections:
    del connections[extract_name]

# 2h. Restore the original wiring:
#     Parse Retell Payload -> Route by Tool (direct)
#     IF: Slots Args Valid (true) -> Wix: Query Time Slots (direct)
#     Wix: Query Resource Types is standalone (no connections in or out).
parse_main = connections.setdefault("Parse Retell Payload", {}).setdefault("main", [])
if not parse_main:
    parse_main.append([])
# Strip any old wiring to the resource-types lookup
parse_main[0] = [t for t in parse_main[0] if t.get("node") != "Wix: Query Resource Types"]
if not any(t.get("node") == "Route by Tool" for t in parse_main[0]):
    parse_main[0].append({"node": "Route by Tool", "type": "main", "index": 0})

# Remove any outbound edges from Wix: Query Resource Types (standalone)
if "Wix: Query Resource Types" in connections:
    del connections["Wix: Query Resource Types"]

# Restore IF: Slots Args Valid (true) -> Wix: Query Time Slots
if_slots_main = connections.setdefault("IF: Slots Args Valid", {}).setdefault("main", [])
while len(if_slots_main) < 2:
    if_slots_main.append([])
if_slots_main[0] = [t for t in if_slots_main[0] if t.get("node") != "Wix: Query Resource Types"]
if not any(t.get("node") == "Wix: Query Time Slots" for t in if_slots_main[0]):
    if_slots_main[0].append({"node": "Wix: Query Time Slots", "type": "main", "index": 0})

# 3. Add new switch rule for flag-callback (output index 7, after the 7 existing rules)
route_node = nodes_by_name["Route by Tool"]
rules = route_node["parameters"]["rules"]["values"]
flag_callback_rule = {
    "conditions": {
        "options": {
            "caseSensitive": True,
            "leftValue": "",
            "typeValidation": "strict",
            "version": 3,
        },
        "conditions": [
            {
                "id": "rule-flag-callback",
                "leftValue": "={{ $json.tool }}",
                "rightValue": "flag-callback",
                "operator": {
                    "type": "string",
                    "operation": "equals",
                    "name": "filter.operator.equals",
                },
            }
        ],
        "combinator": "and",
    },
    "renameOutput": True,
    "outputKey": "Flag Callback",
}
# Avoid double-adding if script is re-run
existing_ids = [
    cond["id"]
    for r in rules
    for cond in r["conditions"]["conditions"]
]
if "rule-flag-callback" not in existing_ids:
    rules.append(flag_callback_rule)


# 4. Add new flag-callback nodes (idempotent — replace if present)

NEW_NODES = [
    {
        "parameters": {"jsCode": VALIDATE_FLAG_CALLBACK_JS},
        "id": "node-validate-flag-callback",
        "name": "Validate: Flag Callback Args",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [-800, 3000],
    },
    {
        "parameters": {
            "conditions": {
                "boolean": [
                    {"value1": "={{ $json._valid }}", "value2": True}
                ]
            }
        },
        "id": "node-if-flag-callback-valid",
        "name": "IF: Flag Callback Args Valid",
        "type": "n8n-nodes-base.if",
        "typeVersion": 1,
        "position": [-576, 3000],
    },
    {
        "parameters": {
            "fromEmail": FROM_EMAIL,
            "toEmail": CALLBACK_RECIPIENT,
            "subject": "={{ $json._emailSubject }}",
            "emailFormat": "text",
            "text": "={{ $json._emailBody }}",
            "options": {
                "appendAttribution": False,
                "replyTo": "contact@aiemply.com",
            },
        },
        "id": "node-send-flag-callback-email",
        "name": "Send Email: Flag Callback",
        "type": "n8n-nodes-base.emailSend",
        "typeVersion": 2.1,
        "position": [-352, 2960],
        "credentials": {
            "smtp": {
                "id": SMTP_CREDENTIAL_ID,
                "name": SMTP_CREDENTIAL_NAME,
            }
        },
        "onError": "continueErrorOutput",
    },
    {
        "parameters": {"jsCode": FORMAT_FLAG_CALLBACK_RESPONSE_JS},
        "id": "node-format-flag-callback-response",
        "name": "Format: Flag Callback Response",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [-128, 2960],
    },
    {
        "parameters": {
            "respondWith": "json",
            "responseBody": "={{ $json }}",
            "options": {},
        },
        "id": "node-respond-flag-callback",
        "name": "Respond: Flag Callback",
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1,
        "position": [96, 2960],
    },
    {
        "parameters": {
            "respondWith": "json",
            "responseBody": "={{ { success: false, error: 'Validation failed: ' + $json._validationError } }}",
            "options": {},
        },
        "id": "node-respond-flag-callback-validation-error",
        "name": "Respond: Flag Callback Validation Error",
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1,
        "position": [-352, 3140],
    },
    {
        "parameters": {
            "respondWith": "json",
            "responseBody": "{\n  \"success\": false,\n  \"error\": \"Failed to send callback notification email\"\n}",
            "options": {},
        },
        "id": "node-error-flag-callback",
        "name": "Error: Flag Callback",
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1.5,
        "position": [-128, 3120],
    },
]

for new in NEW_NODES:
    nm = new["name"]
    if nm in nodes_by_name:
        # Replace existing entry in the nodes list
        idx = next(i for i, n in enumerate(nodes) if n["name"] == nm)
        nodes[idx] = new
    else:
        nodes.append(new)
    nodes_by_name[nm] = new


# 5. Wire connections
def add_conn(source: str, target: str, source_index: int = 0):
    """Add a connection from source.main[source_index] -> target.main[0], avoiding duplicates."""
    conn = connections.setdefault(source, {}).setdefault("main", [])
    while len(conn) <= source_index:
        conn.append([])
    bucket = conn[source_index]
    if not any(t.get("node") == target for t in bucket):
        bucket.append({"node": target, "type": "main", "index": 0})


# Route by Tool — output 7 (the new 8th rule, 0-indexed) → Validate.
# The switch has fallbackOutput: "extra", which creates a dedicated extra output
# AFTER all numbered rule outputs. Before this script ran, the fallback was at
# index 7 (Respond: Unknown Tool Error). Adding an 8th rule must shift the
# fallback to index 8.
route_main = connections.setdefault("Route by Tool", {}).setdefault("main", [])
# Strip the Unknown-Tool-Error fallback wherever it currently lives so we can
# reattach it to the correct (now index 8) extra output.
fallback_targets = []
for i, bucket in enumerate(route_main):
    keep = []
    for t in bucket:
        if t.get("node") == "Respond: Unknown Tool Error":
            fallback_targets.append(t)
        else:
            keep.append(t)
    route_main[i] = keep
# Make sure the rule output (index 7) and fallback output (index 8) exist
while len(route_main) < 9:
    route_main.append([])
add_conn("Route by Tool", "Validate: Flag Callback Args", source_index=7)
# Reattach fallback to extra output at index 8
existing_fb = [t["node"] for t in route_main[8]]
if fallback_targets:
    for fb in fallback_targets:
        if fb["node"] not in existing_fb:
            route_main[8].append(fb)
            existing_fb.append(fb["node"])
elif "Respond: Unknown Tool Error" not in existing_fb:
    route_main[8].append({"node": "Respond: Unknown Tool Error", "type": "main", "index": 0})

# Linear chain
add_conn("Validate: Flag Callback Args", "IF: Flag Callback Args Valid")
# IF: true branch (index 0) → Send Email
add_conn("IF: Flag Callback Args Valid", "Send Email: Flag Callback", source_index=0)
# IF: false branch (index 1) → Validation error response
add_conn("IF: Flag Callback Args Valid", "Respond: Flag Callback Validation Error", source_index=1)
# Send Email: success (index 0) → Format
add_conn("Send Email: Flag Callback", "Format: Flag Callback Response", source_index=0)
# Send Email: error (index 1) → Error response
add_conn("Send Email: Flag Callback", "Error: Flag Callback", source_index=1)
# Format → Respond success
add_conn("Format: Flag Callback Response", "Respond: Flag Callback")


# 6. Save
with open(WF_PATH, "w", encoding="utf-8") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)

print(f"Wrote {WF_PATH}")
print(f"Total nodes: {len(nodes)}")
print(f"Switch rules: {len(rules)}")
print(f"Email recipient: {CALLBACK_RECIPIENT}")
