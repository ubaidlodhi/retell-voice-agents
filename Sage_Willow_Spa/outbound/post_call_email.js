// "Compose: Post-Call Email" - n8n Code node body (embedded by
// _build_post_call_callback_workflow.py, exercised by test_post_call_email.js).
//
// One recap e-mail per real conversation, from Aria, for both agents. Machine
// outcomes are skipped on purpose - no answer, busy, voicemail, a line that
// dropped before anyone spoke - so the reader only hears from Aria about calls
// that actually happened (Ubaid, 2026-09-21).
//
// The e-mail is deliberately plain: a recap in Aria's voice, the outcome, the
// booking if one changed hands, the contact, two links. Brand colours from the
// AIEmply palette, inline styles only, no images, no dashes of the long kind,
// nothing that reads like a promotion.

const INBOUND_AGENT_ID = 'agent_eceb7448aa1f37e8f436a63a43';
const OUTBOUND_AGENT_ID = 'agent_4ef8160dc71826818c6fd8122b';
const TO = 'sagewillowspa@gmail.com';          // the spa (Nicky)
const CC = 'engineering@aiemply.com';          // AIEmply engineering, copy only
// Ubaid's own test line: calls to or from it never produce a recap, for anyone.
const TEST_NUMBERS = new Set(['+12532681856']);
const GREETING = 'Hi Nicky,';
const SPA = 'Sage & Willow Spa';
// Client-facing call log (Ubaid, 2026-09-21), not the Retell dashboard.
const DASHBOARD = 'https://app.aiemply.com/dashboard/logs?call=';
const TZ = 'America/Los_Angeles';

const env = $input.first().json;
const body = (env && typeof env.body === 'object' && env.body !== null) ? env.body : env;
const event = body.event;
const call = body.call || {};
const dryRun = body.dryRun === true || body.dryRun === 'true';

const skip = (why) => [{ json: { send: false, skip_reason: why, call_id: call.call_id || null, dryRun } }];
const last10 = (p) => String(p || '').replace(/\D/g, '').slice(-10);
const isTestNumber = (p) => [...TEST_NUMBERS].some(t => last10(t) === last10(p) && last10(p));

// ---- was this a real conversation? -----------------------------------------
if (event !== 'call_analyzed') return skip(`event ${event || 'missing'}`);
const isInbound = call.agent_id === INBOUND_AGENT_ID;
const isOutbound = call.agent_id === OUTBOUND_AGENT_ID;
if (!isInbound && !isOutbound) return skip('not an Aria agent');
if (call.call_type && call.call_type !== 'phone_call') return skip(`call_type ${call.call_type}`);
if (call.call_status && call.call_status !== 'ended') return skip(`call_status ${call.call_status}`);
if (isTestNumber(call.from_number) || isTestNumber(call.to_number)) return skip('test line');

const dr = String(call.disconnection_reason || '');
const analysis = call.call_analysis || {};
const custom = analysis.custom_analysis_data || {};
const NEVER_A_CONVERSATION = new Set([
  'voicemail_reached', 'machine_detected', 'registered_call_timeout', 'invalid_destination',
  'telephony_provider_permission_denied', 'telephony_provider_unavailable', 'sip_routing_error',
  'concurrency_limit_reached', 'no_valid_payment', 'user_declined',
  'error_user_not_joined', 'error_no_audio_received',
]);
if (dr.startsWith('dial_') || NEVER_A_CONVERSATION.has(dr)) return skip(dr);
if (analysis.in_voicemail === true) return skip('voicemail');
if (isOutbound && ['voicemail', 'no_answer'].includes(String(custom.reached_lead || ''))) return skip(`reached_lead ${custom.reached_lead}`);

const turns = Array.isArray(call.transcript_object) ? call.transcript_object : [];
const callerTurns = turns.filter(t => t && t.role === 'user' && typeof t.content === 'string' && t.content.trim()).length;
if (callerTurns === 0) return skip('nobody spoke');

// ---- what happened, from the tools rather than from the model ------------------
const clean = (s) => String(s == null ? '' : s).trim();
const invocations = {};
const results = [];
for (const t of (Array.isArray(call.transcript_with_tool_calls) ? call.transcript_with_tool_calls : [])) {
  if (!t) continue;
  if (t.role === 'tool_call_invocation') {
    let args = {};
    try { args = JSON.parse(t.arguments || '{}'); } catch (e) { args = {}; }
    invocations[t.tool_call_id] = { name: t.name, args };
  } else if (t.role === 'tool_call_result') {
    let out = null;
    try { out = JSON.parse(t.content); } catch (e) { out = { raw: String(t.content || '') }; }
    const inv = invocations[t.tool_call_id] || {};
    results.push({ name: inv.name || t.name || '', args: inv.args || {}, out });
  }
}
const lastOk = (name) => [...results].reverse().find(r => r.name === name && r.out && r.out.success === true) || null;
const booked = lastOk('book_appointment');
const moved = lastOk('reschedule_booking');
const cancelled = lastOk('cancel_booking');
const flagged = lastOk('flag_callback');

// ---- who ---------------------------------------------------------------------------
const dyn = call.retell_llm_dynamic_variables || {};
const noBraces = (s) => (s.includes('{{') ? '' : s);
let first = noBraces(clean(dyn.lead_first_name));
let last = noBraces(clean(dyn.lead_last_name));
if (booked) { first = clean(booked.args.firstName) || first; last = clean(booked.args.lastName) || last; }
if (!first && flagged && clean(flagged.args.callerName)) { first = clean(flagged.args.callerName); last = ''; }
const name = [first, last].filter(Boolean).join(' ');
const phoneRaw = clean(isInbound ? call.from_number : call.to_number);
const prettyPhone = (p) => {
  const m = /^\+1(\d{3})(\d{3})(\d{4})$/.exec(p);
  return m ? `+1 (${m[1]}) ${m[2]}-${m[3]}` : p;
};
const phone = prettyPhone(phoneRaw);
// "Test John at +1 (415) 555-0100", or just the number when no name came through.
const who = name ? `${name}${phone ? ` at ${phone}` : ''}` : (phone || 'the caller');

// ---- dates, durations ----------------------------------------------------------------
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
// Local wall-clock strings from the booking tools ("2026-10-07T10:00:00"): no time zone maths.
const localWhen = (s) => {
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(String(s || ''));
  if (!m) return '';
  const [Y, M, D, h, mi] = m.slice(1).map(Number);
  const d = new Date(Date.UTC(Y, M - 1, D));
  const hour12 = h % 12 === 0 ? 12 : h % 12;
  return `${DAYS[d.getUTCDay()]}, ${MONTHS[M - 1]} ${D} at ${hour12}:${String(mi).padStart(2, '0')} ${h >= 12 ? 'PM' : 'AM'}`;
};
const minutesBetween = (a, b) => {
  const pa = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(String(a || ''));
  const pb = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(String(b || ''));
  if (!pa || !pb) return null;
  const toMin = (p) => Date.UTC(+p[1], +p[2] - 1, +p[3], +p[4], +p[5]) / 60000;
  return Math.round(toMin(pb) - toMin(pa));
};
const durationWords = (n) => ({ 30: 'thirty minutes', 45: 'forty-five minutes', 60: 'one hour', 90: 'ninety minutes', 120: 'two hours' }[n] || (n ? `${n} minutes` : ''));
const callWhen = call.start_timestamp
  ? new Date(call.start_timestamp).toLocaleString('en-US', { timeZone: TZ, weekday: 'long', month: 'long', day: 'numeric', hour: 'numeric', minute: '2-digit' }) + ' Pacific'
  : '';
const durMs = Number(call.duration_ms || 0);
const callLength = durMs ? `${Math.floor(durMs / 60000)} min ${String(Math.round((durMs % 60000) / 1000)).padStart(2, '0')} sec` : '';

// ---- outcome -------------------------------------------------------------------------
const RESOLUTION = {
  booking_created: 'appointment booked', booking_canceled: 'appointment cancelled', booking_rescheduled: 'appointment moved',
  info_provided: 'question answered', callback_flagged: 'callback requested', spam_declined: 'sales call declined',
  inappropriate_deflected: 'request declined', abandoned: 'call ended early', other: 'call completed',
};
const OUTBOUND_OUTCOME = {
  booked: 'appointment booked', callback_scheduled: 'callback requested', not_interested: 'not interested',
  wrong_number: 'wrong number', voicemail_left: 'voicemail left', do_not_call: 'asked not to be called again',
  transferred: 'transferred to the team', other: 'call completed',
};
const INTENT = {
  new_booking: 'book a massage', cancel: 'cancel an appointment', reschedule: 'move an appointment',
  status_check: 'check on an appointment', faq_general: 'ask a question', faq_pricing: 'ask about pricing',
  callback_request: 'ask for a callback', spam: 'sell something', inappropriate: 'an inappropriate request',
  off_topic: 'something unrelated', emergency: 'an emergency', crisis: 'a crisis',
};
let outcome = booked ? 'appointment booked' : cancelled ? 'appointment cancelled' : moved ? 'appointment moved'
  : (isOutbound ? OUTBOUND_OUTCOME[custom.outbound_outcome] : RESOLUTION[custom.resolution_status]) || 'call completed';
if (dr === 'call_transfer') outcome = 'transferred to the team';
if (isOutbound && custom.reached_lead === 'wrong_person') outcome = 'wrong person answered';

let booking = '';
if (booked) {
  const mins = minutesBetween(booked.args.startDate, booked.args.endDate);
  booking = [clean(booked.args.serviceName), durationWords(mins), localWhen(booked.args.startDate)].filter(Boolean).join(', ');
} else if (moved) {
  booking = ['Moved to', localWhen(moved.args.startDate)].filter(Boolean).join(' ');
} else if (cancelled) {
  booking = 'Cancelled';
}

const sentimentRaw = clean(custom.caller_sentiment || analysis.user_sentiment).toLowerCase();
const sentiment = sentimentRaw && sentimentRaw !== 'unknown' ? sentimentRaw : '';
const intent = isInbound ? (INTENT[custom.caller_intent] || '') : '';
const callbackWanted = custom.callback_required === true;
const callbackReason = clean(custom.callback_reason);
const language = clean(custom.language_used).toLowerCase();
const source = isOutbound ? clean(dyn.lead_source) : '';

// ---- the recap, in Aria's voice --------------------------------------------------------
const noDashes = (s) => s.replace(/\s*[—–]\s*/g, ', ');
const firstPerson = (s) => s
  .replace(/\b(asked|told|thanked|gave|informed|answered|called|reached)\s+the\s+agent\b/gi, '$1 me')
  .replace(/\b(with|to|from|by|for)\s+the\s+agent\b/gi, '$1 me')
  .replace(/\bThe agent's\b/g, 'My').replace(/\bthe agent's\b/g, 'my')
  .replace(/\bThe agent\b/g, 'I').replace(/\bthe agent\b/g, 'I')
  .replace(/\bThe (?:AI|assistant|virtual assistant)\b/g, 'I').replace(/\bthe (?:AI|assistant|virtual assistant)\b/g, 'I')
  .replace(/\bAria's\b/g, 'my').replace(/\bAria\b/g, 'I')
  .replace(/\bThe (?:user|customer|client)\b/g, 'The caller').replace(/\bthe (?:user|customer|client)\b/g, 'the caller')
  .replace(/\bI (was|were) (able|unable)\b/g, 'I was $2');
let summary = noDashes(clean(analysis.call_summary));
summary = firstPerson(summary);
if (summary) summary = summary.charAt(0).toUpperCase() + summary.slice(1);
if (!summary) summary = `We spoke for ${callLength || 'a short while'}.`;

let intro;
if (isInbound) intro = `I just took a call from ${who}. Here is a quick recap.`;
else if (source === 'website_form') intro = `I just called ${who} about the booking form they sent in. Here is a quick recap.`;
else intro = `I just called ${who} back after they rang the spa earlier. Here is a quick recap.`;

const notes = [];
if (callbackWanted) notes.push(`They would like someone from the spa to call them back${callbackReason ? `: ${callbackReason}` : '.'}`);
if (language === 'spanish' || language === 'mixed') notes.push(`We spoke ${language === 'mixed' ? 'partly' : ''} in Spanish.`.replace('  ', ' '));
if (custom.tool_failure === true) notes.push('One of my tools returned an error during this call, so it is worth a look.');
if (custom.do_not_call === true) notes.push('They asked not to be called again.');

// ---- subject ------------------------------------------------------------------------------
const subject = `Call recap: ${name || phone || 'caller'}, ${outcome}`;

// ---- HTML ----------------------------------------------------------------------------------
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const cap = (s) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : s);
const FONT = "-apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";
const rows = [];
rows.push(['Outcome', cap(outcome)]);
if (intent) rows.push(['They wanted to', intent]);
if (booking) rows.push(['Appointment', booking]);
if (sentiment) rows.push(['Mood', cap(sentiment)]);
if (callWhen) rows.push(['When', callWhen]);
if (callLength) rows.push(['Length', callLength]);
const contactRows = [];
if (name) contactRows.push(['Name', name]);
if (phone) contactRows.push(['Phone', phone]);
if (source) contactRows.push(['Came from', source === 'website_form' ? 'the website booking form' : 'a missed call to the spa']);

const rowHtml = (r) =>
  `<tr><td style="padding:6px 0;font:13px/1.5 ${FONT};color:#4E5E73;width:120px;vertical-align:top;">${esc(r[0])}</td>` +
  `<td style="padding:6px 0;font:14px/1.5 ${FONT};color:#0F1729;vertical-align:top;">${esc(r[1])}</td></tr>`;
const card = (title, list) =>
  `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F8FAFC;border:1px solid #E1E7EF;border-radius:10px;margin:0 0 16px;">` +
  `<tr><td style="padding:14px 18px 10px;">` +
  `<div style="font:600 11px/1.4 ${FONT};letter-spacing:.08em;text-transform:uppercase;color:#4E5E73;margin:0 0 4px;">${esc(title)}</div>` +
  `<table role="presentation" cellpadding="0" cellspacing="0" width="100%">${list.map(rowHtml).join('')}</table>` +
  `</td></tr></table>`;
// One link only: the AIEmply call log, which has the recording and the
// transcript. No raw recording URL (Ubaid, 2026-09-21).
const links = [];
if (call.call_id) links.push(`<a href="${esc(DASHBOARD + call.call_id)}" style="color:#144EB8;text-decoration:none;font:600 13px ${FONT};">Open the call</a>`);

let html = `<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>${esc(subject)}</title></head>` +
  `<body style="margin:0;padding:0;background:#F3F6F9;">` +
  `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F3F6F9;"><tr><td align="center" style="padding:28px 16px;">` +
  `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#FFFFFF;border:1px solid #E1E7EF;border-radius:12px;">` +
  // header
  `<tr><td style="padding:18px 28px;border-bottom:1px solid #EBF1F7;">` +
  `<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>` +
  `<td style="font:700 16px/1 ${FONT};color:#1563E0;letter-spacing:-.01em;">AIEmply</td>` +
  `<td align="right" style="font:12px/1 ${FONT};color:#4E5E73;">Aria for ${esc(SPA)}</td>` +
  `</tr></table></td></tr>` +
  // body
  `<tr><td style="padding:26px 28px 8px;">` +
  `<p style="margin:0 0 14px;font:15px/1.6 ${FONT};color:#0F1729;">${esc(GREETING)}</p>` +
  `<p style="margin:0 0 14px;font:15px/1.6 ${FONT};color:#0F1729;">${esc(intro)}</p>` +
  `<p style="margin:0 0 22px;font:15px/1.6 ${FONT};color:#1C2740;">${esc(summary)}</p>` +
  notes.map(n => `<p style="margin:0 0 14px;font:15px/1.6 ${FONT};color:#0F1729;">${esc(n)}</p>`).join('') +
  card('Call details', rows) +
  (contactRows.length ? card('Contact', contactRows) : '') +
  (links.length ? `<p style="margin:4px 0 20px;">${links.join(`<span style="color:#D1DAE5;padding:0 10px;">|</span>`)}</p>` : '') +
  `<p style="margin:0 0 4px;font:15px/1.6 ${FONT};color:#0F1729;">Aria</p>` +
  `<p style="margin:0 0 22px;font:13px/1.5 ${FONT};color:#4E5E73;">Virtual receptionist, ${esc(SPA)}</p>` +
  `</td></tr>` +
  // footer
  `<tr><td style="padding:14px 28px 18px;border-top:1px solid #EBF1F7;">` +
  `<p style="margin:0;font:11px/1.6 ${FONT};color:#A0ABBA;">Sent by AIEmply for ${esc(SPA)}.${call.call_id ? ` Call ID ${esc(call.call_id)}.` : ''}</p>` +
  `</td></tr>` +
  `</table></td></tr></table></body></html>`;

const textLines = [GREETING, '', intro, '', summary, ''];
for (const n of notes) textLines.push(n, '');
textLines.push('Call details');
for (const r of rows) textLines.push(`  ${r[0]}: ${r[1]}`);
if (contactRows.length) { textLines.push('', 'Contact'); for (const r of contactRows) textLines.push(`  ${r[0]}: ${r[1]}`); }
if (call.call_id) textLines.push('', `Open the call: ${DASHBOARD}${call.call_id}`);
textLines.push('', 'Aria', `Virtual receptionist, ${SPA}`, '', `Sent by AIEmply for ${SPA}.`);
let text = textLines.join('\n');

// Belt and braces: nothing long-dashed leaves this node.
html = html.replace(/[—–]/g, ', ');
text = text.replace(/[—–]/g, ', ');

return [{ json: {
  send: !dryRun,
  dryRun,
  skip_reason: dryRun ? 'dry run (composed, not sent)' : '',
  call_id: call.call_id || null,
  direction: isInbound ? 'inbound' : 'outbound',
  to: TO,
  cc: CC,
  subject: subject.replace(/[—–]/g, ', '),
  html,
  text,
  outcome,
  name,
  phone: phoneRaw,
} }];
