// "Decide: Still Missed?" - n8n Code node body (embedded by
// _build_post_call_callback_workflow.py, exercised by test_missed_lead_hold.js).
//
// A "Missed lead, please call them back" e-mail waits 10 minutes ("Wait: 10 Minutes") and
// then goes only if the person has not reached us since. On 2026-10-04 and 2026-10-06 Hilda
// and Karen rang the spa and booked within minutes of our callback reaching their voicemail,
// and Nicky got "please call them back" and "appointment booked" for the same person.
//
// Reached us = an inbound call from the number we rang, started after our call began (2-minute
// margin: they can dial us while ours is still ringing), that
//   * is still going on (they are talking to Aria right now - that call reports itself), or
//   * ended with an outcome Nicky hears about anyway: booked, cancelled, rescheduled, a
//     question answered (those get their own recap) or a message for the team (its own e-mail).
// A hang-up, or a half-finished call, does not count: that call is not rung back while ours is
// recent, so this e-mail is the only word Nicky gets. If the look-up fails, the e-mail goes.

const SERVED = new Set(['booking_created', 'booking_canceled', 'booking_rescheduled',
                        'info_provided', 'callback_flagged']);
const MARGIN_MS = 2 * 60 * 1000;

const email = $('Compose: Post-Call Email').first().json;
const call = (($('Webhook - Retell call_analyzed').first().json.body || {}).call) || {};

const asList = (name) => {
  const items = $(name).all().map(i => i.json);
  if (items.length === 1 && Array.isArray(items[0])) return items[0];
  if (items.length === 1 && items[0] && Array.isArray(items[0].items)) return items[0].items;
  return items.filter(c => c && c.call_id);
};

const lead = String(call.to_number || '');
// A missed-call callback was triggered by an inbound call - that one is not "since".
const triggeredBy = String((call.metadata || {}).inbound_call_id || '');
const since = Number(call.start_timestamp || 0) - MARGIN_MS;

const later = asList('Retell: Reached Us Since?').filter(c =>
  c.call_id !== call.call_id && c.call_id !== triggeredBy && c.direction === 'inbound'
  && lead && c.from_number === lead && Number(c.start_timestamp || 0) > since);

const outcome = (c) => String((((c.call_analysis || {}).custom_analysis_data) || {}).resolution_status || '');
const live = later.find(c => ['registered', 'ongoing'].includes(c.call_status));
const served = later.find(c => SERVED.has(outcome(c)));

let reachedUs = '';
if (live) reachedUs = `on a call with us now (${live.call_id})`;
else if (served) reachedUs = `rang us since: ${outcome(served)} (${served.call_id})`;

return [{ json: {
  ...email,
  missed: email.missed === true && !reachedUs,
  reached_us: reachedUs,
  later_inbound_calls: later.length,
} }];
