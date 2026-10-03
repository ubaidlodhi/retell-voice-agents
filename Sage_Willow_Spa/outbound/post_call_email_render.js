// "Render: Recap Email" - n8n Code node body (embedded by
// _build_post_call_callback_workflow.py, exercised by test_post_call_email_render.js).
//
// Input: the OpenAI chat-completions response from "Write: Recap (GPT-4.1-mini)"
// (or an error item - that node continues on error). The composed facts and the
// branded shell come from "Compose: Post-Call Email".
//
// GPT-4.1-mini writes the words - the paragraphs, the subject, and the "Outcome"
// and "They wanted to" rows of the details card; this node decides whether they
// are safe to send.
// Anything it cannot vouch for - no answer, bad JSON, a link, a price, a spam
// word, a time/date/weekday that is not in the facts, a phone number that is not
// the caller's - and Nicky gets the template recap instead. She always gets one.

const compose = $('Compose: Post-Call Email').first().json;
const resp = $input.first().json || {};

const SPAM = /\b(for free|free gift|free trial|guarantee[ds]?|urgent|act now|click here|limited time|winner|congratulations|no obligation|risk[- ]free|100%|buy now|order now|special offer|amazing)\b/i;
const FORBIDDEN = /\b(retell|transcript|recording|language model|ai model|openai|gpt|prompt|chatbot|software)\b/i;
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const undash = (s) => String(s).replace(/\s*[—–]\s*/g, ', ');
const cap = (s) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : s);
const wordCount = (s) => String(s).split(/\s+/).filter(Boolean).length;

const base = {
  write: true,
  send: compose.send === true,
  dryRun: compose.dryRun === true,
  skip_reason: compose.skip_reason || '',
  call_id: compose.call_id,
  direction: compose.direction,
  to: compose.to,
  cc: compose.cc,
  outcome: compose.outcome,
};
const fallback = (why) => [{ json: { ...base, subject: compose.subject, html: compose.html, text: compose.text,
  writer: 'template', writer_note: why } }];

// ---- 1. did the model answer? ---------------------------------------------------------
if (resp.error) return fallback(`model call failed: ${String(resp.error.message || resp.error).slice(0, 160)}`);
const content = resp.choices && resp.choices[0] && resp.choices[0].message && resp.choices[0].message.content;
if (!content) return fallback('model returned no content');
let out;
try { out = JSON.parse(content); } catch (e) { return fallback('model returned something other than JSON'); }

// ---- 2. tidy what is harmless to tidy ----------------------------------------------------
const tidy = (s) => undash(String(s == null ? '' : s))
  .replace(/\*\*|__|`/g, '')          // markdown emphasis
  .replace(/^\s*(?:[-*•]|\d+[.)])\s+/, '')   // a list marker at the start
  .replace(/\s+/g, ' ')
  .trim();
// The two detail rows: short phrases, no full stop, no "They wanted to" repeated inside the value.
const phrase = (s) => tidy(s).replace(/[.!]+$/, '');
let outcomeLine = phrase(out.outcome);
let wanted = phrase(out.they_wanted).replace(/^they wanted to\s+/i, '').replace(/^to\s+/i, '');
let paras = (Array.isArray(out.paragraphs) ? out.paragraphs : [])
  .map(tidy)
  .filter(Boolean)
  // the greeting and the signature are ours - drop the model's if it wrote them anyway
  .filter((p) => !/^(hi|hello|hey|dear)\b[^.!?]{0,20}[,!.]?$/i.test(p))
  .filter((p) => !/^(best|thanks|thank you|cheers|warmly|regards|kind regards)?[,!]?\s*(aria)?\.?$/i.test(p));
if (paras.length && /^(hi|hello|hey|dear)\s+nicky[,!.]?\s+/i.test(paras[0])) paras[0] = paras[0].replace(/^(hi|hello|hey|dear)\s+nicky[,!.]?\s+/i, '');
if (paras.length && /\s*(best|thanks|cheers|warmly|regards)[,!]?\s*aria\.?$/i.test(paras[paras.length - 1])) {
  paras[paras.length - 1] = paras[paras.length - 1].replace(/\s*(best|thanks|cheers|warmly|regards)[,!]?\s*aria\.?$/i, '').trim();
}
paras = paras.filter(Boolean);

// ---- 3. checks - any failure means the template goes out instead -------------------------------
const all = [outcomeLine, wanted, ...paras].join('\n');
const words = paras.join(' ').split(/\s+/).filter(Boolean).length;
if (paras.length < 1 || paras.length > 5) return fallback(`model wrote ${paras.length} paragraphs`);
if (words < 12 || words > 220) return fallback(`model wrote ${words} words`);
if (/https?:\/\/|www\.|\b[\w.-]+@[\w-]+\.\w+|\.com\b/i.test(all)) return fallback('model wrote a link or an address');
if (SPAM.test(all)) return fallback(`spam-like word: ${all.match(SPAM)[0]}`);
if (FORBIDDEN.test(all)) return fallback(`mentions ${all.match(FORBIDDEN)[0]}`);
if (/\$\s?\d|\bdollars?\b|\bUSD\b/i.test(all)) return fallback('model mentioned a price');

// Every time, date, weekday and phone number it states must come from the facts.
const factText = JSON.stringify(compose.facts || {}) + ' ' + String(compose.subject || '');
const normTime = (h, m, ap) => `${Number(h)}:${m || '00'} ${ap.replace(/\./g, '').toUpperCase()}`;
const timesIn = (s) => [...String(s).matchAll(/\b(1[0-2]|0?[1-9])(?::([0-5]\d))?\s?(a\.?m\.?|p\.?m\.?)(?![a-z])/gi)]
  .map((m) => normTime(m[1], m[2], m[3]));
const allowedTimes = new Set(timesIn(factText));
const badTime = timesIn(all).find((t) => !allowedTimes.has(t));
if (badTime) return fallback(`time not in the facts: ${badTime}`);

const MONTHS = 'January|February|March|April|May|June|July|August|September|October|November|December';
const datesIn = (s) => [...String(s).matchAll(new RegExp(`\\b(${MONTHS})\\s+(\\d{1,2})(?:st|nd|rd|th)?\\b`, 'gi'))]
  .map((m) => `${m[1].toLowerCase()} ${Number(m[2])}`);
const allowedDates = new Set(datesIn(factText));
const badDate = datesIn(all).find((d) => !allowedDates.has(d));
if (badDate) return fallback(`date not in the facts: ${badDate}`);

const WEEKDAYS = /\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b/gi;
const allowedDays = new Set((factText.match(WEEKDAYS) || []).map((d) => d.toLowerCase()));
const badDay = (all.match(WEEKDAYS) || []).map((d) => d.toLowerCase()).find((d) => !allowedDays.has(d));
if (badDay) return fallback(`weekday not in the facts: ${badDay}`);

const digits = (s) => String(s || '').replace(/\D/g, '');
const callerDigits = digits((compose.facts || {}).caller_phone).slice(-10);
const badPhone = [...all.matchAll(/(?:\+?\d[\d\s().-]{6,}\d)/g)].map((m) => digits(m[0]))
  .find((d) => d.length >= 7 && !(callerDigits && callerDigits.endsWith(d.slice(-10))));
if (badPhone) return fallback('phone number not in the facts');

// ---- 4. the Outcome / They wanted to rows -------------------------------------------------------------
// The tools have the last word on what changed hands: with a booking, move, cancel,
// transfer or wrong number on record the outcome must say so; without one it may
// not claim one.
const notes = [];
const verified = String(compose.verified_outcome || '');
const SAYS = {
  'appointment booked': /\bbook/i, 'appointment requested': /\brequest/i,
  'appointment cancelled': /\bcancel/i, 'appointment moved': /\b(mov|reschedul)/i,
  'transferred to the team': /\btransfer/i, 'wrong person answered': /\bwrong\b/i,
};
if (verified) {
  if (!outcomeLine || outcomeLine.length > 60 || wordCount(outcomeLine) > 8 || !(SAYS[verified] || /./).test(outcomeLine)) {
    notes.push(`outcome "${outcomeLine}" replaced by the tool result`);
    outcomeLine = cap(verified);
  }
} else {
  if (/\b(booked|rescheduled|moved|cancell?ed|transferred)\b/i.test(outcomeLine)
      && !/\b(not|no|never|didn'?t|wasn'?t|without)\b/i.test(outcomeLine)) {
    return fallback(`outcome claims what no tool did: ${outcomeLine}`);
  }
  if (!outcomeLine || outcomeLine.length > 60 || wordCount(outcomeLine) > 8) {
    notes.push('outcome missing or too long, template label used');
    outcomeLine = cap(compose.outcome || 'call completed');
  }
}
outcomeLine = cap(outcomeLine);
if (wanted && (wanted.length > 80 || wordCount(wanted) > 12)) { notes.push('they_wanted too long, left out'); wanted = ''; }
if (wanted) wanted = wanted.charAt(0).toLowerCase() + wanted.slice(1);

// The subject carries the same outcome as the card, in one fixed shape (the model's own
// subjects came back in Title Case): "Call recap: Matt Jones, appointment booked".
const facts = compose.facts || {};
let subject = `Call recap: ${facts.caller_name || facts.caller_phone || 'caller'}, ${outcomeLine.charAt(0).toLowerCase()}${outcomeLine.slice(1)}`;
if (subject.length > 90) subject = compose.subject;

// ---- 5. fill the shell -----------------------------------------------------------------------------
// split/join, not replace: a "$" in the model's words must not act as a replacement pattern.
const fill = (shell, mark, value) => String(shell).split(mark).join(value);
const style = compose.para_style || 'margin:0 0 14px;';
const bodyHtml = paras.map((p) => `<p style="${style}">${esc(p)}</p>`).join('');
const row = (label, value) => String(compose.row_tpl || '').split('%%LABEL%%').join(esc(label)).split('%%VALUE%%').join(esc(value));
const topHtml = row('Outcome', outcomeLine) + (wanted ? row('They wanted to', wanted) : '');
const topText = [`  Outcome: ${outcomeLine}`, ...(wanted ? [`  They wanted to: ${wanted}`] : [])].join('\n');
const html = undash(fill(fill(compose.html_shell, '<!--ARIA_BODY-->', bodyHtml), '<!--ARIA_TOP_ROWS-->', topHtml));
const text = undash(fill(fill(compose.text_shell, '{{ARIA_BODY}}', paras.join('\n\n')), '{{ARIA_TOP_ROWS}}', topText));
if (!String(compose.html_shell).includes('<!--ARIA_BODY-->') || !html.includes(bodyHtml.slice(0, 40))) return fallback('shell had no body marker');
if (!compose.row_tpl || !String(compose.html_shell).includes('<!--ARIA_TOP_ROWS-->') || /ARIA_TOP_ROWS|%%LABEL%%|%%VALUE%%/.test(html + text)) {
  return fallback('shell had no detail-row marker');
}

return [{ json: { ...base, outcome: outcomeLine, subject: undash(subject), html, text, writer: 'gpt-4.1-mini', writer_note: notes.join('; ') } }];
