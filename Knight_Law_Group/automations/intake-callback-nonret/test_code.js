// Runs the two Retell code-node bodies with a frozen clock and stub dynamic variables, and checks the results
// (Pacific conversions are cross-checked with luxon). node test_code.js
const fs = require('fs');
const path = require('path');
const { DateTime } = require('../lease-filter/node_modules/luxon');
const CB = fs.readFileSync(path.join(__dirname, 'code_callback.js'), 'utf8');
const HRS = fs.readFileSync(path.join(__dirname, 'code_nonret_hours.js'), 'utf8');

function run(code, dv, nowIso) {
  const now = DateTime.fromISO(nowIso, { zone: 'America/Los_Angeles' }).toMillis();
  const RealDate = Date;
  class FakeDate extends RealDate { constructor(...a) { super(...(a.length ? a : [now])); } static now() { return now; } }
  return new Function('dv', 'Date', code)(dv, FakeDate);
}
let fails = 0;
function check(label, got, want) {
  const bad = Object.keys(want).filter((k) => got[k] !== want[k]);
  if (bad.length) { fails++; console.log('FAIL ' + label + '\n  got  ' + JSON.stringify(got) + '\n  want ' + JSON.stringify(want)); }
  else console.log('ok   ' + label + '  ' + (got.callback_when_en || got.callback_status || got.nonret_hours) + (got.callback_at_iso ? '  ' + got.callback_at_iso : ''));
}

// Thursday 2026-10-15 10:00 AM PDT
const T = '2026-10-15T10:00';
const C = (dv, now) => run(CB, dv, now || T);
check('tomorrow 17:00', C({ callback_day: 'tomorrow', callback_time: '17:00' }),
  { callback_status: 'in_window', callback_next: 'confirm', callback_when_en: 'tomorrow at 5 PM', callback_when_es: 'mañana a las 5 de la tarde', callback_at_iso: '2026-10-16T17:00:00.000-07:00', callback_at_pacific: '10-16-2026 05:00 PM', callback_tries: '1' });
check('today 1:30 pm', C({ callback_day: 'today', callback_time: '1:30 pm' }),
  { callback_status: 'in_window', callback_when_en: 'today at 1:30 PM', callback_when_es: 'hoy a la 1:30 de la tarde' });
check('time only, still ahead -> today', C({ callback_day: 'unspecified', callback_time: '16:00' }), { callback_status: 'in_window', callback_when_en: 'today at 4 PM' });
check('time only, passed -> tomorrow', C({ callback_day: '', callback_time: '09:00' }), { callback_status: 'in_window', callback_when_en: 'tomorrow at 9 AM', callback_when_es: 'mañana a las 9 de la mañana' });
check('saturday noon (inside 72h)', C({ callback_day: 'saturday', callback_time: '12:00' }), { callback_status: 'in_window', callback_when_en: 'Saturday at 12 PM', callback_when_es: 'el sábado a las 12 del mediodía' });
check('sunday 9am (71h ahead)', C({ callback_day: 'sunday', callback_time: '09:00' }), { callback_status: 'in_window' });
check('sunday 11am (73h ahead)', C({ callback_day: 'sunday', callback_time: '11:00' }), { callback_status: 'out_of_window', callback_next: 'out' });
check('monday', C({ callback_day: 'monday', callback_time: '17:00' }), { callback_status: 'out_of_window', callback_next: 'out', callback_at_iso: '' });
check('thursday = next week', C({ callback_day: 'thursday', callback_time: '17:00' }), { callback_status: 'out_of_window' });
check('next_week', C({ callback_day: 'next_week' }), { callback_status: 'out_of_window', callback_next: 'out' });
check('in 2 days, no time', C({ callback_day: 'in_days', callback_in_days: '2' }), { callback_status: 'need_time', callback_next: 'reask' });
check('in 5 days, no time', C({ callback_day: 'in_days', callback_in_days: '5' }), { callback_status: 'out_of_window' });
check('specific date 10-17 18:30', C({ callback_day: 'specific_date', callback_specific_date: '10-17', callback_time: '18:30' }), { callback_status: 'in_window', callback_when_en: 'Saturday at 6:30 PM', callback_when_es: 'el sábado a las 6:30 de la tarde' });
check('specific date 10-30', C({ callback_day: 'specific_date', callback_specific_date: '10-30', callback_time: '10:00' }), { callback_status: 'out_of_window' });
check('specific date passed -> next year', C({ callback_day: 'specific_date', callback_specific_date: '10-01', callback_time: '10:00' }), { callback_status: 'out_of_window' });
check('in 120 minutes', C({ callback_in_minutes: '120' }), { callback_status: 'in_window', callback_when_en: 'today at 12 PM' });
check('in 7 min rounds to 5', C({ callback_in_minutes: '7' }, '2026-10-15T10:01'), { callback_status: 'in_window', callback_when_en: 'today at 10:10 AM' });
check('in 3 hours at 7pm -> 10pm', C({ callback_in_minutes: '180' }, '2026-10-15T19:00'), { callback_status: 'outside_hours', callback_next: 'reask' });
check('tomorrow 7am', C({ callback_day: 'tomorrow', callback_time: '07:00' }), { callback_status: 'outside_hours', callback_next: 'reask' });
check('tomorrow 21:00', C({ callback_day: 'tomorrow', callback_time: '21:00' }), { callback_status: 'outside_hours' });
check('tomorrow 20:30 ok', C({ callback_day: 'tomorrow', callback_time: '20:30' }), { callback_status: 'in_window', callback_when_es: 'mañana a las 8:30 de la noche' });
check('tomorrow no time', C({ callback_day: 'tomorrow' }), { callback_status: 'need_time', callback_next: 'reask' });
check('today 9am passed', C({ callback_day: 'today', callback_time: '09:00' }), { callback_status: 'unclear', callback_next: 'reask' });
check('nothing -> first ask', C({}), { callback_status: 'unclear', callback_next: 'reask', callback_ask_en: "No problem at all. What's a good day and time for us to give you a call back?" });
check('nothing, 2nd try -> ask again', C({ callback_tries: '1' }), { callback_next: 'reask', callback_ask_en: 'Sorry, what day and time would work best for us to call you back?' });
check('day only, 2nd try -> ask time', C({ callback_tries: '1', callback_day: 'tomorrow' }), { callback_next: 'reask', callback_ask_en: 'Sure. And what time works best that day?' });
check('nothing, 3rd try -> giveup', C({ callback_tries: '2' }), { callback_status: 'unclear', callback_next: 'giveup', callback_tries: '3', callback_ask_en: '' });
check('outside hours ask', C({ callback_day: 'tomorrow', callback_time: '06:00' }), { callback_ask_es: 'Hacemos llamadas entre las 8 de la mañana y las 9 de la noche, hora del Pacífico. ¿Qué hora en ese horario le funciona?' });
check('confirm has no ask', C({ callback_day: 'tomorrow', callback_time: '10:00' }), { callback_ask_en: '' });
check('2nd try, valid -> confirm', C({ callback_tries: '1', callback_day: 'tomorrow', callback_time: '10:00' }), { callback_next: 'confirm' });
check('2nd try, out -> out', C({ callback_tries: '1', callback_day: 'next_week' }), { callback_next: 'out' });
check('garbage time', C({ callback_day: 'tomorrow', callback_time: 'whenever' }), { callback_status: 'need_time' });
// DST edges
check('PST: Nov 30 -> tomorrow 5pm', C({ callback_day: 'tomorrow', callback_time: '17:00' }, '2026-11-30T10:00'), { callback_at_iso: '2026-12-01T17:00:00.000-08:00' });
check('across DST end (Sat Oct 31 -> Mon Nov 2)', C({ callback_day: 'monday', callback_time: '09:00' }, '2026-10-31T10:00'), { callback_status: 'in_window', callback_at_iso: '2026-11-02T09:00:00.000-08:00' });
check('across DST start (Sat Mar 13 -> Sun Mar 14 2027)', C({ callback_day: 'tomorrow', callback_time: '10:00' }, '2027-03-13T10:00'), { callback_at_iso: '2027-03-14T10:00:00.000-07:00' });
check('before DST start (Mon Mar 8 2027 is still PST)', C({ callback_day: 'tomorrow', callback_time: '10:00' }, '2027-03-07T10:00'), { callback_at_iso: '2027-03-08T10:00:00.000-08:00' });
check('late night 11pm, time only 10:00 -> tomorrow', C({ callback_time: '10:00' }, '2026-10-15T23:00'), { callback_when_en: 'tomorrow at 10 AM', callback_at_iso: '2026-10-16T10:00:00.000-07:00' });

// cross-check every in_window ISO against luxon for a sweep of clocks
for (let i = 0; i < 400; i++) {
  const nowDt = DateTime.fromISO('2026-01-01T00:00', { zone: 'America/Los_Angeles' }).plus({ hours: i * 22 + 7 });
  const r = run(CB, { callback_day: 'tomorrow', callback_time: '15:45' }, nowDt.toISO({ includeOffset: false }));
  const want = nowDt.plus({ days: 1 }).set({ hour: 15, minute: 45, second: 0, millisecond: 0 }).toISO();
  if (r.callback_at_iso !== want) { fails++; console.log('FAIL sweep ' + nowDt.toISO() + ' got ' + r.callback_at_iso + ' want ' + want); }
}
console.log('sweep: 400 clocks cross-checked with luxon');

// business hours
const H = (iso) => run(HRS, {}, iso);
check('hours Thu 10:00', H('2026-10-15T10:00'), { nonret_hours: 'open' });
check('hours Thu 07:59', H('2026-10-15T07:59'), { nonret_hours: 'closed' });
check('hours Thu 08:00', H('2026-10-15T08:00'), { nonret_hours: 'open' });
check('hours Thu 19:59', H('2026-10-15T19:59'), { nonret_hours: 'open' });
check('hours Thu 20:00', H('2026-10-15T20:00'), { nonret_hours: 'closed' });
check('hours Fri 19:30', H('2026-10-16T19:30'), { nonret_hours: 'open' });
check('hours Sat 12:00', H('2026-10-17T12:00'), { nonret_hours: 'closed' });
check('hours Sun 12:00', H('2026-10-18T12:00'), { nonret_hours: 'closed' });
check('hours Mon 08:30 PST', H('2026-11-02T08:30'), { nonret_hours: 'open' });
check('hours Mon 07:30 PST', H('2026-11-02T07:30'), { nonret_hours: 'closed' });
check('hours Fri 17:00 (UTC already Sat)', H('2026-10-16T17:30'), { nonret_hours: 'open' });
console.log(fails ? '\n' + fails + ' FAILURES' : '\nall passed');
process.exit(fails ? 1 : 0);
