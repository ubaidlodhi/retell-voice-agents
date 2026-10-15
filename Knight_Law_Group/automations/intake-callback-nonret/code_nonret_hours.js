// Retell code node "Non-Retainer: Business Hours?" (node-nonret-hours). Body only, run by Retell with `dv`.
// Intake Analysts take live transfers Monday-Friday, 8 AM - 8 PM Pacific. Pacific time is computed by hand (US DST rules).
var HOUR = 3600000;
function nthSunday(y, m, n) { var first = (7 - new Date(Date.UTC(y, m, 1)).getUTCDay()) % 7; return 1 + first + 7 * (n - 1); }
function offsetAt(ms) {
  var y = new Date(ms).getUTCFullYear();
  var start = Date.UTC(y, 2, nthSunday(y, 2, 2), 10), end = Date.UTC(y, 10, nthSunday(y, 10, 1), 9);
  return (ms >= start && ms < end) ? -7 : -8;
}
var d = new Date(Date.now() + offsetAt(Date.now()) * HOUR);
var wd = d.getUTCDay(), h = d.getUTCHours();
var open = wd >= 1 && wd <= 5 && h >= 8 && h < 20;
return { nonret_hours: open ? 'open' : 'closed' };
