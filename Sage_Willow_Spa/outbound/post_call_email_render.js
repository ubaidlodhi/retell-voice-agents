// "Render: Recap Email" - n8n Code node body (embedded by
// _build_post_call_callback_workflow.py, exercised by test_post_call_email_render.js).
//
// Input: the OpenAI chat-completions response from "Write: Recap (GPT-4.1-mini)"
// (or an error item - that node continues on error). The composed facts and the
// branded shell come from "Compose: Post-Call Email".
//
// GPT-4.1-mini writes the words; this node decides whether they are safe to send.
// Anything it cannot vouch for - no answer, bad JSON, a link, a price, a spam
// word, a time/date/weekday that is not in the facts, a phone number that is not
// the caller's - and Nicky gets the template recap instead. She always gets one.

const compose = $('Compose: Post-Call Email').first().json;
const resp = $input.first().json || {};

const SPAM = /\b(for free|free gift|free trial|guarantee[ds]?|urgent|act now|click here|limited time|winner|congratulations|no obligation|risk[- ]free|100%|buy now|order now|special offer|amazing)\b/i;
const FORBIDDEN = /\b(retell|transcript|recording|language model|ai model|openai|gpt|prompt|chatbot|software)\b/i;
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const undash = (s) => String(s).replace(/\s*[—–]\s*/g, ', ');

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
let subject = tidy(out.subject);
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
const all = [subject, ...paras].join('\n');
const words = paras.join(' ').split(/\s+/).filter(Boolean).length;
if (paras.length < 1 || paras.length > 5) return fallback(`model wrote ${paras.length} paragraphs`);
if (words < 12 || words > 220) return fallback(`model wrote ${words} words`);
if (!subject || subject.length > 90) subject = compose.subject;
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

// ---- 4. fill the shell -----------------------------------------------------------------------------
const style = compose.para_style || 'margin:0 0 14px;';
const bodyHtml = paras.map((p) => `<p style="${style}">${esc(p)}</p>`).join('');
const html = undash(String(compose.html_shell).replace('<!--ARIA_BODY-->', bodyHtml));
const text = undash(String(compose.text_shell).replace('{{ARIA_BODY}}', paras.join('\n\n')));
if (html === String(compose.html_shell) || !html.includes(bodyHtml.slice(0, 40))) return fallback('shell had no body marker');

return [{ json: { ...base, subject: undash(subject), html, text, writer: 'gpt-4.1-mini', writer_note: '' } }];
