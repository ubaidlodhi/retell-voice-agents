// "Resolve: Add-ons (Booking)" - n8n Code node body (installed by
// _patch_v79_resolve_addons.py, exercised by test_resolve_addons.js).
//
// call_dde463dd1cad472c17e1b8e1c46 (2026-10-14): Aria sent the Aromatherapy add-on as
// "29159dc3-cb4b-4bd-b250-..." for a real "29159dc3-cb4b-4bd4-b250-..." - one character
// dropped. Wix refused the whole booking ("bookedAddOns id is not a valid GUID") and a
// caller who had agreed to everything was handed to a callback. Same failure class as
// service, variant and booking ids: a model does not copy 36-character ids reliably.
//
// Same order of trust as "Resolve: Service (Booking)":
//   1. the add-on NAME Aria sends (the caller's own words), against this service's
//      add-ons: exact -> substring -> fuzzy;
//   2. an id that really is one of this service's add-ons;
//   3. the closest real id - a copy slip (a character or two dropped, added or swapped)
//      is a few edits away, every other add-on id about thirty;
//   otherwise an error naming this service's real add-ons.
// groupId always comes from the service itself, never from the copy.
//
// Ids and groups come from the catalog this booking already fetched. Names need
// get-services on this same webhook - asked only when a name was sent or an id is not
// exact, so a clean booking pays nothing extra. If neither source answers, the add-ons
// pass through untouched and Wix judges them, as before.

const SELF = '__SELF_URL__';
// n8n Code nodes expose the request helper as this.helpers (older builds: $helpers).
const helpers = (this && this.helpers && this.helpers.httpRequest) ? this.helpers
  : (typeof $helpers !== 'undefined' ? $helpers : null);

const prev = $input.first().json;
if (prev._valid === false) return [{ json: prev }];
const args = Object.assign({}, prev.args || {});
const sent = Array.isArray(args.addOns) ? args.addOns.filter((a) => a && typeof a === 'object') : [];
if (!sent.length) return [{ json: prev }];

const clean = (s) => String(s == null ? '' : s).trim();
const norm = (s) => clean(s).toLowerCase().replace(/[^a-z0-9 ]+/g, ' ').replace(/\s+/g, ' ').trim();
const STOP = ['enhancement', 'add', 'on', 'addon', 'the', 'a', 'an', 'with', 'extra'];
const tokens = (s) => norm(s).split(' ').filter((t) => t && !STOP.includes(t));

// ---- this service's add-ons: id -> { id, name, groupIds } ------------------------------
const known = {};
const learn = (id, groupIds, name) => {
  if (!id) return;
  const k = known[id] || (known[id] = { id, name: '', groupIds: [] });
  for (const g of groupIds || []) if (g && !k.groupIds.includes(g)) k.groupIds.push(g);
  if (name && !k.name) k.name = clean(name);
};
let catalog = null;
try { catalog = $('Wix: Services (Booking)').first().json; } catch (e) { catalog = null; }
const services = ((Array.isArray(catalog) ? catalog[0] : catalog) || {}).services || [];
const svc = services.find((s) => s && s.id === args.serviceId) || null;
for (const g of (svc && svc.addOnGroups) || []) for (const id of g.addOnIds || []) learn(id, [g.id]);

const needNames = sent.some((a) => clean(a.name) || !known[clean(a.id)]);
let namesFrom = 'none';
if (needNames && helpers) {
  try {
    const r = await helpers.httpRequest({
      method: 'POST', url: SELF, json: true, timeout: 30000,
      headers: { tool: 'get-services', 'Content-Type': 'application/json', 'User-Agent': 'curl/8.0' },
      body: { args: { serviceName: args.serviceName } },
    });
    const list = (r && Array.isArray(r.services)) ? r.services : [];
    const s = list.find((x) => x && x.id === args.serviceId) || (list.length === 1 ? list[0] : null);
    for (const a of (s && s.availableAddOns) || []) learn(a.id, a.groupIds, a.name);
    if (s) namesFrom = 'get-services';
  } catch (e) { namesFrom = 'get-services failed'; }
}

const real = Object.values(known);
if (!real.length) {
  return [{ json: Object.assign({}, prev, { _addOnResolution: { source: 'catalog-unavailable', namesFrom } }) }];
}

// ---- matching ------------------------------------------------------------------------------
function byName(wanted) {
  const w = norm(wanted);
  if (!w) return null;
  const named = real.filter((r) => r.name);
  const exact = named.find((r) => norm(r.name) === w);
  if (exact) return { hit: exact, how: 'name:exact' };
  const subs = named.filter((r) => norm(r.name).includes(w) || w.includes(norm(r.name)));
  if (subs.length === 1) return { hit: subs[0], how: 'name:substring' };
  const wt = tokens(wanted);
  let best = null, bestScore = 0, tie = false;
  for (const r of named) {
    const rt = tokens(r.name);
    if (!rt.length || !wt.length) continue;
    const hits = wt.filter((t) => rt.some((x) => x.slice(0, 4) === t.slice(0, 4))).length;
    const score = hits / Math.max(wt.length, rt.length);
    if (score > bestScore) { best = r; bestScore = score; tie = false; } else if (score === bestScore && score > 0) tie = true;
  }
  return best && bestScore >= 0.5 && !tie ? { hit: best, how: 'name:fuzzy' } : null;
}

function edits(a, b) {
  const m = a.length, n = b.length;
  let row = Array.from({ length: n + 1 }, (_, j) => j);
  for (let i = 1; i <= m; i++) {
    const next = [i];
    for (let j = 1; j <= n; j++) {
      next[j] = Math.min(row[j] + 1, next[j - 1] + 1, row[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    }
    row = next;
  }
  return row[n];
}
function nearestId(id) {
  const s = clean(id).toLowerCase();
  if (s.length < 20) return null;
  const ranked = real.map((r) => ({ r, d: edits(s, r.id.toLowerCase()) })).sort((x, y) => x.d - y.d);
  const [best, second] = ranked;
  if (best.d <= 6 && (!second || second.d - best.d >= 8)) return { hit: best.r, how: 'id:closest', edits: best.d };
  return null;
}

const resolved = [];
const report = [];
const unmatched = [];
for (const a of sent) {
  const name = clean(a.name), id = clean(a.id), group = clean(a.groupId);
  let m = byName(name);
  if (!m && known[id]) m = { hit: known[id], how: 'id:exact' };
  if (!m) m = nearestId(id);
  if (!m) { unmatched.push(name || id || '(empty)'); continue; }
  const hit = m.hit;
  const groupId = hit.groupIds.includes(group) ? group : hit.groupIds[0];
  report.push({ sentName: name || null, sentId: id || null, how: m.how, id: hit.id, name: hit.name || null,
    ...(m.edits != null ? { edits: m.edits } : {}), ...(name && id && id !== hit.id ? { idCorrected: true } : {}) });
  if (!resolved.some((x) => x.id === hit.id)) resolved.push({ id: hit.id, groupId });
}

if (unmatched.length) {
  const names = real.map((r) => r.name).filter(Boolean);
  const reason = `add-on ${unmatched.map((u) => `"${u}"`).join(', ')} is not an add-on for ${args.serviceName || 'this service'}.` +
    (names.length ? ` Its add-ons are: ${names.join(', ')}.` : '') +
    ' Nothing was booked.';
  return [{ json: Object.assign({}, prev, { args, _valid: false, _validationError: reason,
    _addOnResolution: { resolved: report, unmatched, namesFrom } }) }];
}

args.addOns = resolved;
return [{ json: Object.assign({}, prev, { args, _addOnResolution: { resolved: report, namesFrom } }) }];
