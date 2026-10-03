// "Validate: Flag Callback Args" - n8n Code node body (installed by
// _patch_v68_callback_email.py, exercised by test_flag_callback_email.js).
//
// Checks the flag_callback args and builds the callback e-mail to the spa.
// The e-mail matches the post-call recap (post_call_email.js): same AIEmply
// header, cards, fonts and colours, inline styles only, no images, no long
// dashes (Ubaid, 2026-10-01: "it should be a proper HTML format like we have
// for the post call analyzer email"). It goes out while the call is still
// live, so there is no call link yet - the recap that follows carries it.

const { args, callerPhone } = $input.first().json;
const errors = [];

const reason = (args.reason || '').toString().trim();
if (!reason) errors.push('reason is required');

// Aria sends "unknown" (any case) when the caller never gave a name.
const rawName = (args.callerName || '').toString().trim();
const nameGiven = !!rawName && !/^(unknown|n\/?a|none|not given|caller)$/i.test(rawName);
const callerName = nameGiven ? rawName : 'Unknown';
// Order of trust: what the agent passed, then any other phone-ish arg it used,
// then Retell's own call metadata. Placeholders that survived un-substituted
// ({{user_number}} and friends) are treated as missing rather than emailed to
// the team as literal text.
function realPhone(v) {
    const t = (v || '').toString().trim();
    if (!t) return null;
    if (t.indexOf('{{') !== -1 || t.indexOf('}}') !== -1) return null;
    if (!/\d/.test(t)) return null;
    return t;
}
const phoneToContact = realPhone(args.callerPhone)
    || realPhone(args.phone)
    || realPhone(callerPhone)
    || 'Unknown';
const questionDetail = (args.questionDetail || '').toString().trim();

// +19135269174 -> (913) 526-9174, and a tel: link that dials it.
const digits = phoneToContact.replace(/\D/g, '');
const last10 = digits.length === 11 && digits[0] === '1' ? digits.slice(1) : digits;
const phonePretty = last10.length === 10
    ? `(${last10.slice(0, 3)}) ${last10.slice(3, 6)}-${last10.slice(6)}` : phoneToContact;
const phoneTel = last10.length === 10 ? `+1${last10}` : (digits ? `+${digits}` : '');

const askedAt = new Date().toLocaleString('en-US', { timeZone: 'America/Los_Angeles',
    weekday: 'long', month: 'long', day: 'numeric', hour: 'numeric', minute: '2-digit' });

const undash = (s) => String(s).replace(/\s*[—–]\s*/g, ', ');
const who = nameGiven ? rawName : (phoneToContact !== 'Unknown' ? phonePretty : 'a caller');
const subject = undash(`Callback request: ${[nameGiven ? rawName : '', phoneToContact !== 'Unknown' ? phonePretty : '']
    .filter(Boolean).join(', ') || 'caller'}`);

// ---- plain text (fallback part of the e-mail) ------------------------------------------
const lines = [
    'Hi Nicky,',
    '',
    `${nameGiven ? rawName : 'A caller'} asked for someone from the spa to call them back.`,
    '',
    'Callback request',
    `  Name:    ${nameGiven ? rawName : 'Not given'}`,
    `  Phone:   ${phoneToContact === 'Unknown' ? 'Not available' : phonePretty}`,
    `  Asked:   ${askedAt}`,
    `  Reason:  ${reason}`,
];
if (questionDetail) lines.push('', 'What they asked', `  ${questionDetail}`);
lines.push('', 'A full recap of the call follows once it ends.', '', 'Aria', 'Virtual receptionist, Sage & Willow Spa',
    '', 'Sent by AIEmply for Sage & Willow Spa.');
const body = undash(lines.join('\n'));

// ---- HTML --------------------------------------------------------------------------------
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const FONT = "-apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";
const SPA = 'Sage & Willow Spa';
const PARA = `margin:0 0 14px;font:15px/1.6 ${FONT};color:#0F1729;`;
const rowHtml = (label, valueHtml) =>
    `<tr><td style="padding:6px 0;font:13px/1.5 ${FONT};color:#4E5E73;width:120px;vertical-align:top;">${esc(label)}</td>` +
    `<td style="padding:6px 0;font:14px/1.5 ${FONT};color:#0F1729;vertical-align:top;">${valueHtml}</td></tr>`;
const card = (title, inner) =>
    `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F8FAFC;border:1px solid #E1E7EF;border-radius:10px;margin:0 0 16px;">` +
    `<tr><td style="padding:14px 18px 10px;">` +
    `<div style="font:600 11px/1.4 ${FONT};letter-spacing:.08em;text-transform:uppercase;color:#4E5E73;margin:0 0 4px;">${esc(title)}</div>` +
    inner + `</td></tr></table>`;

const phoneHtml = phoneTel
    ? `<a href="tel:${esc(phoneTel)}" style="color:#144EB8;text-decoration:none;font-weight:600;">${esc(phonePretty)}</a>`
    : esc('Not available');
const details = card('Callback request',
    `<table role="presentation" cellpadding="0" cellspacing="0" width="100%">` +
    rowHtml('Name', esc(nameGiven ? rawName : 'Not given')) +
    rowHtml('Phone', phoneHtml) +
    rowHtml('Asked', esc(askedAt)) +
    rowHtml('Reason', esc(reason)) +
    `</table>`);
const asked = questionDetail
    ? card('What they asked', `<p style="margin:2px 0 6px;font:14px/1.6 ${FONT};color:#0F1729;">${esc(questionDetail)}</p>`)
    : '';
const button = phoneTel
    ? `<table role="presentation" cellpadding="0" cellspacing="0" style="margin:4px 0 22px;"><tr>` +
      `<td style="background:#1563E0;border-radius:8px;">` +
      `<a href="tel:${esc(phoneTel)}" style="display:inline-block;padding:11px 20px;font:600 14px/1 ${FONT};color:#FFFFFF;text-decoration:none;">Call ${esc(who)} back</a>` +
      `</td></tr></table>`
    : '';

const html = undash(`<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>${esc(subject)}</title></head>` +
    `<body style="margin:0;padding:0;background:#F3F6F9;">` +
    `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F3F6F9;"><tr><td align="center" style="padding:28px 16px;">` +
    `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#FFFFFF;border:1px solid #E1E7EF;border-radius:12px;">` +
    `<tr><td style="padding:18px 28px;border-bottom:1px solid #EBF1F7;">` +
    `<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>` +
    `<td style="font:700 16px/1 ${FONT};color:#1563E0;letter-spacing:-.01em;">AIEmply</td>` +
    `<td align="right" style="font:12px/1 ${FONT};color:#4E5E73;">Aria for ${esc(SPA)}</td>` +
    `</tr></table></td></tr>` +
    `<tr><td style="padding:26px 28px 8px;">` +
    `<p style="${PARA}">Hi Nicky,</p>` +
    `<p style="${PARA}">${esc(nameGiven ? rawName : 'A caller')} asked for someone from the spa to call them back.</p>` +
    `<div style="height:8px;line-height:8px;">&nbsp;</div>` +
    details + asked + button +
    `<p style="margin:0 0 4px;font:15px/1.6 ${FONT};color:#0F1729;">Aria</p>` +
    `<p style="margin:0 0 22px;font:13px/1.5 ${FONT};color:#4E5E73;">Virtual receptionist, ${esc(SPA)}</p>` +
    `</td></tr>` +
    `<tr><td style="padding:14px 28px 18px;border-top:1px solid #EBF1F7;">` +
    `<p style="margin:0;font:11px/1.6 ${FONT};color:#A0ABBA;">Sent by AIEmply for ${esc(SPA)}. A full recap of the call follows once it ends.</p>` +
    `</td></tr>` +
    `</table></td></tr></table></body></html>`);

return [{ json: {
    ...$input.first().json,
    args,
    _valid: errors.length === 0,
    _validationError: errors.join('; '),
    _emailSubject: subject,
    _emailBody: body,
    _emailHtml: html,
    _callerName: callerName,
    _callerPhone: phoneToContact,
    _reason: reason
} }];
