const inputJson = $input.first().json;
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

// --- Normalize optional filter args ---

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

// --- NEW (V26): preferredTime -> normalized "HH:MM" 24-hour, or null ---
// Accepts "14:00", "14:00:00", "2 PM", "2pm", "2:30 PM", "2:30pm".
// When present, the formatter returns the slots NEAREST this time instead of
// blindly returning the earliest N — this is what caused the agent to claim
// "no 2 PM slot" when 2 PM existed but fell outside the first 6 results.
function normalizePreferredTime(v) {
    if (v === undefined || v === null || v === '') return null;
    const s = String(v).trim().toLowerCase();

    // 12-hour form first ("2 pm", "2:30 pm", "2pm")
    let m = s.match(/^(\d{1,2})(?::(\d{2}))?\s*([ap])\.?\s*m\.?$/);
    if (m) {
        let h = parseInt(m[1], 10);
        const mi = m[2] ? parseInt(m[2], 10) : 0;
        if (h < 1 || h > 12 || mi > 59) return null;
        if (h === 12) h = 0;
        if (m[3] === 'p') h += 12;
        return `${String(h).padStart(2, '0')}:${String(mi).padStart(2, '0')}`;
    }

    // 24-hour form ("14:00", "14:00:00", "09:30")
    m = s.match(/^(\d{1,2}):(\d{2})(?::\d{2})?$/);
    if (m) {
        const h = parseInt(m[1], 10);
        const mi = parseInt(m[2], 10);
        if (h > 23 || mi > 59) return null;
        return `${String(h).padStart(2, '0')}:${String(mi).padStart(2, '0')}`;
    }

    return null;
}
args.preferredTime = normalizePreferredTime(args.preferredTime);

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
