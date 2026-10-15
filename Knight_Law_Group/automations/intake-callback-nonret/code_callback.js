// Retell code node "Callback: Resolve Time" (node-cb-compute). Body only: Retell runs it with `dv` (dynamic variables)
// and maps the returned keys to dynamic variables. Pacific time is computed by hand (US DST rules), no Intl needed.
// Inputs (from node-cb-extract): callback_day, callback_specific_date, callback_in_days, callback_in_minutes,
// callback_time, plus callback_tries from a previous pass.
// callback_status: in_window | out_of_window | need_time | outside_hours | unclear
// callback_next:   confirm | out | reask | giveup   (the only value the branch node reads)
var WINDOW_HOURS = 72; // Micol: the 3-day Alice Qualifying follow-up cadence prevails
var OPEN_HOUR = 8, CLOSE_HOUR = 21; // same calling hours as the n8n callback parser (8 AM - 9 PM PT)
var HOUR = 3600000, DAY = 86400000;

function nthSunday(y, m, n) { var first = (7 - new Date(Date.UTC(y, m, 1)).getUTCDay()) % 7; return 1 + first + 7 * (n - 1); }
function offsetAt(ms) { // -7 (PDT) or -8 (PST)
  var y = new Date(ms).getUTCFullYear();
  var start = Date.UTC(y, 2, nthSunday(y, 2, 2), 10), end = Date.UTC(y, 10, nthSunday(y, 10, 1), 9);
  return (ms >= start && ms < end) ? -7 : -8;
}
function pac(ms) {
  var off = offsetAt(ms), d = new Date(ms + off * HOUR);
  return { y: d.getUTCFullYear(), mo: d.getUTCMonth(), d: d.getUTCDate(), wd: d.getUTCDay(), h: d.getUTCHours(), mi: d.getUTCMinutes(), off: off };
}
function fromPac(y, mo, d, h, mi) { // Pacific wall clock -> epoch ms
  var guess = Date.UTC(y, mo, d, h, mi) + 8 * HOUR;
  return Date.UTC(y, mo, d, h, mi) - offsetAt(guess) * HOUR;
}
function pad(n) { return (n < 10 ? '0' : '') + n; }

var now = Date.now();
var P = pac(now);
var tries = (parseInt(dv.callback_tries, 10) || 0) + 1;
var day = String(dv.callback_day || '').toLowerCase().trim();
var inMin = parseInt(dv.callback_in_minutes, 10) || 0;
var inDays = parseInt(dv.callback_in_days, 10) || 0;
var tm = String(dv.callback_time || '').toLowerCase().match(/(\d{1,2})(?::(\d{2}))?\s*(am|pm|a\.m\.|p\.m\.)?/);
var hour = null, minute = 0;
if (tm) {
  hour = parseInt(tm[1], 10); minute = tm[2] ? parseInt(tm[2], 10) : 0;
  var ap = (tm[3] || '').replace(/\./g, '');
  if (ap === 'pm' && hour < 12) hour += 12; else if (ap === 'am' && hour === 12) hour = 0;
  if (hour > 23 || minute > 59) hour = null;
}

var cbStatus = '', target = null, dayOffset = null;
if (inMin > 0) {
  target = now + inMin * 60000;
  target = Math.ceil(target / 300000) * 300000; // next 5 minutes
} else {
  var WD = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
  var wi = WD.indexOf(day);
  if (day === 'today') dayOffset = 0;
  else if (day === 'tomorrow') dayOffset = 1;
  else if (day === 'day_after_tomorrow') dayOffset = 2;
  else if (day === 'in_days' && inDays > 0) dayOffset = inDays;
  else if (wi !== -1) { dayOffset = (wi - P.wd + 7) % 7; if (dayOffset === 0) dayOffset = 7; }
  else if (day === 'next_week') cbStatus = 'out_of_window';
  else if (day === 'specific_date') {
    var sd = String(dv.callback_specific_date || '').match(/(\d{1,2})\D+(\d{1,2})/);
    if (sd) {
      var mo = parseInt(sd[1], 10) - 1, dd = parseInt(sd[2], 10);
      var t0 = Date.UTC(P.y, P.mo, P.d), t1 = Date.UTC(P.y, mo, dd);
      if (t1 < t0) t1 = Date.UTC(P.y + 1, mo, dd);
      dayOffset = Math.round((t1 - t0) / DAY);
    }
  }
  if (!cbStatus) {
    if (dayOffset === null && hour !== null) { // a time with no day: today if still ahead, else tomorrow
      dayOffset = (hour * 60 + minute > P.h * 60 + P.mi) ? 0 : 1;
    }
    if (dayOffset === null) cbStatus = 'unclear';
    else {
      var base = new Date(Date.UTC(P.y, P.mo, P.d + dayOffset));
      var by = base.getUTCFullYear(), bm = base.getUTCMonth(), bd = base.getUTCDate();
      if (fromPac(by, bm, bd, OPEN_HOUR, 0) > now + WINDOW_HOURS * HOUR) cbStatus = 'out_of_window';
      else if (hour === null) cbStatus = 'need_time';
      else if (hour < OPEN_HOUR || hour >= CLOSE_HOUR) cbStatus = 'outside_hours';
      else {
        target = fromPac(by, bm, bd, hour, minute);
        if (target <= now) { target = null; cbStatus = 'unclear'; } // e.g. "today at 2" when it is already 3
      }
    }
  }
}
if (target !== null && !cbStatus) {
  var T = pac(target);
  if (T.h < OPEN_HOUR || T.h >= CLOSE_HOUR) cbStatus = 'outside_hours';
  else if (target > now + WINDOW_HOURS * HOUR) cbStatus = 'out_of_window';
  else cbStatus = 'in_window';
}

var whenEn = '', whenEs = '', iso = '', pacific = '';
if (cbStatus === 'in_window') {
  var Q = pac(target);
  var off = Math.round((Date.UTC(Q.y, Q.mo, Q.d) - Date.UTC(P.y, P.mo, P.d)) / DAY);
  var h12 = Q.h % 12 === 0 ? 12 : Q.h % 12;
  var clock = h12 + (Q.mi ? ':' + pad(Q.mi) : '');
  var DEN = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  var DES = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'];
  whenEn = (off === 0 ? 'today' : off === 1 ? 'tomorrow' : DEN[Q.wd]) + ' at ' + clock + ' ' + (Q.h < 12 ? 'AM' : 'PM');
  var part = Q.h < 12 ? 'de la mañana' : Q.h === 12 ? 'del mediodía' : Q.h < 19 ? 'de la tarde' : 'de la noche';
  whenEs = (off === 0 ? 'hoy' : off === 1 ? 'mañana' : 'el ' + DES[Q.wd]) + (h12 === 1 ? ' a la ' : ' a las ') + clock + ' ' + part;
  var oh = -Q.off;
  iso = Q.y + '-' + pad(Q.mo + 1) + '-' + pad(Q.d) + 'T' + pad(Q.h) + ':' + pad(Q.mi) + ':00.000-' + pad(oh) + ':00';
  pacific = pad(Q.mo + 1) + '-' + pad(Q.d) + '-' + Q.y + ' ' + pad(h12) + ':' + pad(Q.mi) + ' ' + (Q.h < 12 ? 'AM' : 'PM');
}
// At most two questions: "when?" and then "what time?" (or a second "when?").
var next = cbStatus === 'in_window' ? 'confirm' : cbStatus === 'out_of_window' ? 'out' : (tries < 3 ? 'reask' : 'giveup');
var askEn = '', askEs = '';
if (next === 'reask') {
  if (cbStatus === 'need_time') { askEn = 'Sure. And what time works best that day?'; askEs = 'Claro. ¿Y a qué hora le queda mejor ese día?'; }
  else if (cbStatus === 'outside_hours') { askEn = 'We make calls between 8 AM and 9 PM Pacific. What time in that window works for you?'; askEs = 'Hacemos llamadas entre las 8 de la mañana y las 9 de la noche, hora del Pacífico. ¿Qué hora en ese horario le funciona?'; }
  else if (tries === 1) { askEn = "No problem at all. What's a good day and time for us to give you a call back?"; askEs = 'No hay problema. ¿Qué día y a qué hora le podemos volver a llamar?'; }
  else { askEn = 'Sorry, what day and time would work best for us to call you back?'; askEs = 'Disculpe, ¿qué día y a qué hora le conviene que le llamemos?'; }
}
return {
  callback_status: cbStatus,
  callback_next: next,
  callback_tries: String(tries),
  callback_ask_en: askEn,
  callback_ask_es: askEs,
  callback_when_en: whenEn,
  callback_when_es: whenEs,
  callback_at_iso: iso,
  callback_at_pacific: pacific
};
