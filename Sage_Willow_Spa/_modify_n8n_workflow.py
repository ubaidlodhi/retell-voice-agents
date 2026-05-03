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

// Call context — only present when args_at_root: false. Otherwise unavailable
// at the webhook level; the LLM must pass any needed call info as an arg.
const callObj = body.call || {};
const callId = callObj.call_id || 'unknown';
const callerPhone =
    callObj.from_number ||
    callObj.to_number ||
    args.callerPhone ||
    args.phone ||
    null;

if (!tool) {
    return [{
        json: {
            tool: '',
            args: {},
            callId,
            callerPhone,
            _parseError: 'No tool name found. Expected the `tool` HTTP header (set per-tool in the Retell agent config), or body.name for legacy webhook shape.'
        }
    }];
}

return [{ json: { tool, args, callId, callerPhone } }];
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


FORMAT_SLOTS_JS = r"""const data = $input.first().json;
const { args } = $('Parse Retell Payload').first().json;

if (data.message || data.details) {
    return [{ json: { success: false, error: data.message || 'Failed to retrieve slots' } }];
}

const TZ = "America/Los_Angeles";
const entries = data.availabilityEntries || [];

// Filter parameters from the validator
const staffFilter = args.staffId || null;
const timeOfDay = (args.timeOfDay || 'any').toLowerCase();
const earliestFirst = args.earliestFirst === true;
const limit = (typeof args.limit === 'number' && args.limit > 0) ? args.limit : (earliestFirst ? 3 : 6);

// Hour-band predicate (10 AM – 8 PM open hours)
function inBand(hour, band) {
    if (band === 'morning')   return hour >= 10 && hour < 12;
    if (band === 'afternoon') return hour >= 12 && hour < 17;
    if (band === 'evening')   return hour >= 17 && hour < 20;
    return hour >= 10 && hour < 20; // 'any'
}

function bandOf(hour) {
    if (hour >= 10 && hour < 12) return 'morning';
    if (hour >= 12 && hour < 17) return 'afternoon';
    if (hour >= 17 && hour < 20) return 'evening';
    return null;
}

// 1. Map UTC slots to California-local with hour + band
let slots = entries.filter(e => e.bookable === true).map(e => {
    const utcDate = new Date(e.slot.startDate);
    const localDate = utcDate.toLocaleDateString("en-CA", { timeZone: TZ });
    const localHour = parseInt(utcDate.toLocaleString("en-GB", { hour: '2-digit', hour12: false, timeZone: TZ }), 10);
    const timeLabel = utcDate.toLocaleTimeString("en-US", { hour: 'numeric', minute: '2-digit', hour12: true, timeZone: TZ });
    return {
        localDate,
        time: timeLabel,
        hour: localHour,
        startDate: e.slot.startDate,
        endDate: e.slot.endDate,
        staffName: e.slot.resource?.name || 'Therapist',
        staffId: e.slot.resource?.id || null,
        scheduleId: e.slot.scheduleId
    };
});

// 2. Apply staff filter (if provided)
if (staffFilter) {
    slots = slots.filter(s => s.staffId === staffFilter);
}

// 3. Apply time-of-day filter (always — 'any' keeps 10 AM – 8 PM)
slots = slots.filter(s => inBand(s.hour, timeOfDay));

const filterApplied = { staffId: staffFilter, timeOfDay, earliestFirst, limit };

// 4a. EARLIEST-FIRST mode: flatten, sort, dedup same date+time, cap at limit
if (earliestFirst) {
    const sorted = slots.slice().sort((a, b) => new Date(a.startDate) - new Date(b.startDate));
    const seen = new Map(); // key -> aggregated slot
    const order = [];
    for (const s of sorted) {
        const key = `${s.localDate}|${s.time}`;
        if (seen.has(key)) {
            const agg = seen.get(key);
            if (!agg.availableTherapists.includes(s.staffName)) {
                agg.availableTherapists.push(s.staffName);
            }
        } else {
            const agg = {
                localDate: s.localDate,
                time: s.time,
                startDate: s.startDate,
                endDate: s.endDate,
                staffId: s.staffId,
                scheduleId: s.scheduleId,
                availableTherapists: [s.staffName]
            };
            seen.set(key, agg);
            order.push(agg);
            if (order.length >= limit) break;
        }
    }
    return [{ json: {
        success: true,
        mode: 'earliest_first',
        count: order.length,
        filterApplied,
        slots: order
    } }];
}

// 4b. GROUPED mode: by date → morning/afternoon/evening, dedup same time across staff
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
        if (!existing.availableTherapists.includes(s.staffName)) {
            existing.availableTherapists.push(s.staffName);
        }
    } else {
        day[band].push({
            time: s.time,
            startDate: s.startDate,
            endDate: s.endDate,
            staffId: s.staffId,
            scheduleId: s.scheduleId,
            availableTherapists: [s.staffName]
        });
    }
});

// Cap slots per band so the agent doesn't get a wall of options.
// Distribute limit roughly evenly across active bands per day.
let totalReturned = 0;
const sortedDates = Object.keys(availabilityByDay).sort();
for (const date of sortedDates) {
    const day = availabilityByDay[date];
    const activeBands = ['morning', 'afternoon', 'evening'].filter(b => day[b].length > 0);
    const perBand = activeBands.length === 0 ? 0 : Math.max(2, Math.ceil(limit / Math.max(1, activeBands.length)));
    for (const band of ['morning', 'afternoon', 'evening']) {
        // Sort each band by time
        day[band].sort((a, b) => new Date(a.startDate) - new Date(b.startDate));
        if (day[band].length > perBand) {
            day[band] = day[band].slice(0, perBand);
        }
        totalReturned += day[band].length;
    }
}

return [{ json: {
    success: true,
    mode: 'grouped',
    count: totalReturned,
    filterApplied,
    availabilityByDay
} }];
"""


# -----------------------------------------------------------------------------
# Get-Booking by EMAIL (replaces phone-based lookup)
# -----------------------------------------------------------------------------

VALIDATE_GET_BOOKING_JS = r"""const { args } = $input.first().json;
const errors = [];

const emailRaw = (args.email || '').toString().trim();
const email = emailRaw ? emailRaw.toLowerCase() : null;
const bookingId = args.bookingId || null;

if (!bookingId && !email) {
    errors.push('Either bookingId or email is required to look up a booking');
}

return [{ json: {
    ...$input.first().json,
    args: { ...args, _resolvedEmail: email, _resolvedBookingId: bookingId },
    _valid: errors.length === 0,
    _validationError: errors.join('; '),
    _lookupMode: bookingId ? 'by-id' : 'by-email'
} }];
"""

WIX_GET_BOOKING_BODY = "={\n  \"query\": {\n    \"filter\": {\n      {{ $json._lookupMode === 'by-id' \n        ? '\"id\": { \"$in\": [\"' + $json.args._resolvedBookingId + '\"]}' \n        : '\"contactDetails.email\": \"' + $json.args._resolvedEmail + '\"' \n      }},\n      \"status\": { \"$in\": [\"CONFIRMED\", \"PENDING_APPROVAL\", \"CREATED\", \"PENDING\"] }\n    },\n    \"sort\": [{ \"fieldName\": \"createdDate\", \"order\": \"DESC\" }],\n    \"paging\": { \"limit\": 5 }\n  }\n}"


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

# 2a. Update Validate: Get Booking Args (email-based)
nodes_by_name["Validate: Get Booking Args"]["parameters"]["jsCode"] = VALIDATE_GET_BOOKING_JS

# 2b. Update Wix: Get Booking request body (filter on contactDetails.email)
nodes_by_name["Wix: Get Booking"]["parameters"]["jsonBody"] = WIX_GET_BOOKING_BODY

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
