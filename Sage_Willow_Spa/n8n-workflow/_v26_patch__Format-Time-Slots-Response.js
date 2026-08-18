// Reads Wix's per-slot availableResources (populated because the request
// passes includeResourceTypeIds upstream) and returns therapist names directly
// from Wix — no STAFF_LOOKUP needed.
//
// V26 CHANGE — fixes the "2 PM is not available" false negative:
// Previously grouped mode did `day[band].slice(0, perBand)`, which kept only the
// EARLIEST N slots and silently discarded everything later in the day. A caller
// asking for 2 PM was told no such slot existed because the response was cut off
// at 1:15 PM. Selection is now:
//   1. preferredTime given  -> return the slots NEAREST that time
//   2. earliestFirst        -> return the soonest N (unchanged)
//   3. neither              -> return an EVENLY SPREAD sample across the window
// The response also now reports totalAvailable / truncated / requestedTimeAvailable
// so the agent can never mistake a truncated list for the full picture.

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
const preferredTime = args.preferredTime || null;   // normalized "HH:MM" or null
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
        availableTherapists: s.therapists.map(t => ({ name: t.name, staffId: t.staffId })),
        // internal sort keys — stripped before returning
        _date: s.localDate,
        _min: s.hour * 60 + s.minute
    };
}

function strip(agg) {
    const { _date, _min, ...clean } = agg;
    return clean;
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
// already narrows server-side when a staffId is provided.

// 3. Apply time-of-day filter
slots = slots.filter(s => inBand(s.hour, timeOfDay));

// 4. Dedupe by (date, time), merging therapists — chronological order
const seenKey = new Map();
const allSlots = [];
for (const s of slots.slice().sort((a, b) => new Date(a.startDate) - new Date(b.startDate))) {
    const key = `${s.localDate}|${s.time}`;
    if (seenKey.has(key)) {
        mergeTherapists(seenKey.get(key), s);
    } else {
        const agg = buildAgg(s);
        seenKey.set(key, agg);
        allSlots.push(agg);
    }
}

const totalAvailable = allSlots.length;

// Did the caller's exact requested time survive? (checked against the FULL set)
let requestedTimeAvailable = null;
let prefMin = null;
if (preferredTime) {
    const [ph, pm] = preferredTime.split(':').map(Number);
    prefMin = ph * 60 + pm;
    requestedTimeAvailable = allSlots.some(s => s._min === prefMin);
}

const filterApplied = { staffId: staffFilter, timeOfDay, earliestFirst, preferredTime, limit };

// 5. Zero results — tell the agent explicitly so it widens instead of dead-ending
if (totalAvailable === 0) {
    return [{
        json: {
            success: true,
            mode: preferredTime ? 'nearest' : (earliestFirst ? 'earliest_first' : 'spread'),
            count: 0,
            totalAvailable: 0,
            truncated: false,
            requestedTimeAvailable,
            noSlotsReason: staffFilter
                ? 'No availability for the requested therapist in this window. Retry WITHOUT staffId to see who else is free.'
                : 'No availability for this service in this window. Try a different day or a wider date range.',
            filterApplied,
            slots: [],
            availabilityByDay: {}
        }
    }];
}

// 6. SELECT which slots to return
let chosen;

if (preferredTime) {
    // Nearest to the caller's requested time, then re-sorted chronologically.
    chosen = allSlots
        .slice()
        .sort((a, b) => Math.abs(a._min - prefMin) - Math.abs(b._min - prefMin)
                     || new Date(a.startDate) - new Date(b.startDate))
        .slice(0, limit)
        .sort((a, b) => new Date(a.startDate) - new Date(b.startDate));
} else if (earliestFirst) {
    chosen = allSlots.slice(0, limit);
} else if (totalAvailable <= limit) {
    chosen = allSlots.slice();
} else {
    // Evenly spread across the whole window so the caller hears real choice
    // (12 PM / 1:30 / 3 PM / 4:30) instead of four near-identical early slots.
    const idx = [];
    for (let i = 0; i < limit; i++) {
        idx.push(Math.round((i * (totalAvailable - 1)) / (limit - 1)));
    }
    chosen = [...new Set(idx)].map(i => allSlots[i]);
}

// 7. Group the CHOSEN slots by day/band (backwards-compatible shape)
const availabilityByDay = {};
for (const agg of chosen) {
    const band = bandOf(Math.floor(agg._min / 60));
    if (!band) continue;
    if (!availabilityByDay[agg._date]) {
        availabilityByDay[agg._date] = { morning: [], afternoon: [], evening: [] };
    }
    availabilityByDay[agg._date][band].push(strip(agg));
}

return [{
    json: {
        success: true,
        mode: preferredTime ? 'nearest' : (earliestFirst ? 'earliest_first' : 'spread'),
        count: chosen.length,
        totalAvailable,
        truncated: chosen.length < totalAvailable,
        requestedTimeAvailable,
        filterApplied,
        slots: chosen.map(strip),
        availabilityByDay
    }
}];
