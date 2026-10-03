// node n8n_patch.js           -> pulls live, writes out/classify_live.js + out/classify_new.js + prompt/payload files
// APPLY=1 node n8n_patch.js   -> also pushes to n8n and verifies
// Safe to push before the Retell publish: the lease/Tesla rules are gated on __leaseFlow (the call went through
// node-extract-lease, or the purchase type is on file), so calls from the currently published flow keep the old rules.
const fs = require('fs');
const path = require('path');
const KEY = fs.readFileSync('D:/tmp/n8nkey.txt', 'utf8').trim();
const BASE = 'https://automations.impleko.ai';
const WF = '8DuNGcG9ybV3wVlv';
const H = { 'X-N8N-API-KEY': KEY, 'Content-Type': 'application/json' };
const OUT = path.join(__dirname, 'out');
fs.mkdirSync(OUT, { recursive: true });
const lf = (s) => String(s).replace(/\r/g, '');

// Replace exactly one occurrence (string or regex), else throw.
function rep(src, find, repl, label) {
  if (find instanceof RegExp) {
    const all = src.match(new RegExp(find.source, find.flags.includes('g') ? find.flags : find.flags + 'g')) || [];
    if (all.length !== 1) throw new Error(label + ': expected 1 match, found ' + all.length);
    return src.replace(find, repl);
  }
  const n = src.split(find).length - 1;
  if (n !== 1) throw new Error(label + ': expected 1 match, found ' + n);
  return src.replace(find, repl);
}

function patchClassify(src) {
  src = rep(src,
    "const toBool = (v) => v === true || ['true','yes','y'].includes(String(v==null?'':v).trim().toLowerCase());",
    "const toBool = (v) => v === true || ['true','yes','y'].includes(String(v==null?'':v).trim().toLowerCase());\n" +
    "// Purchase vs lease (script Q2). Accepts the AI labels, the GHL labels and the Retell enum keys.\n" +
    "const ptLabel = (v) => { const t = String(v==null?'':v).toLowerCase().replace(/[^a-z]/g,''); if (!t || t==='na') return ''; if (t==='leasebuyout' || t.indexOf('leasedthenpurchased')===0 || t.indexOf('buyout')!==-1) return 'Leased, then purchased'; if (t.indexOf('lease')===0) return 'Leased'; if (t.indexOf('purchase')===0 || t==='bought') return 'Purchased'; return ''; };\n" +
    "// Lease / Tesla rules apply ONLY to calls from the flow that asks the lease question (it sets purchase_type_call),\n" +
    "// or to leads whose purchase type is already on file. Calls from the older flow keep the old rules.\n" +
    "const __ptCall = ptLabel((call.collected_dynamic_variables || {}).purchase_type_call);\n" +
    "const __leaseFlow = !!__ptCall || !!ptLabel(seeded.purchase_type);",
    'ptLabel helper');
  src = rep(src, /^(  is_owner:\s+toYN\(f\.is_owner\)\s+\|\| toYN\(seeded\.is_owner\),)$/m,
    "$1\n  purchase_type:     __leaseFlow ? (__ptCall || ptLabel(f.purchase_type) || ptLabel(seeded.purchase_type)) : '',", 'merge purchase_type');
  src = rep(src, /^(const retainerMakes = \[.*\];)$/m,
    "$1\nconst leaseArbitration = ['honda','acura','bmw','mercedesbenz','mini'];\nconst buyoutArbitration = ['honda','acura'];\nconst buyoutNonRetainer = ['bmw','mercedesbenz','mini'];", 'lease make lists');
  src = rep(src, "  if (!makeKey) return { s:'Incomplete Lead', r:'N/A' };",
    "  if (!makeKey) return { s:'Incomplete Lead', r:'N/A' };\n" +
    "  if (x.purchase_type === 'Leased' && leaseArbitration.includes(makeKey)) return { s:'Bad Lead', r:'Requires Arbitration' };\n" +
    "  if (x.purchase_type === 'Leased, then purchased' && buyoutArbitration.includes(makeKey)) return { s:'Bad Lead', r:'Requires Arbitration' };",
    'lease arbitration rules');
  src = rep(src, "  if (year <= 2020) return { s:'Bad Lead', r:'Vehicle year' };",
    "  if (year <= 2020) return { s:'Bad Lead', r:'Vehicle year' };\n" +
    "  if (x.purchase_type === 'Leased, then purchased' && buyoutNonRetainer.includes(makeKey)) return { s:'Non-Retainer Lead', r:'N/A' };\n" +
    "  if (__leaseFlow && makeKey === 'tesla') return { s:'Bad Lead', r:'Requires Arbitration' };",
    'buyout non-retainer + tesla');
  src = rep(src, '  purchase_condition: pc,', '  purchase_type: out(m.purchase_type),\n  purchase_condition: pc,', 'output purchase_type');
  return src;
}

function patchPrompt(sys, user) {
  sys = rep(sys, '- ca_purchase: Yes / No / N/A (was the vehicle bought or leased from a California dealership)',
    '- ca_purchase: Yes / No / N/A (was the vehicle bought or leased from a California dealership)\n' +
    '- purchase_type: Purchased / Leased / Leased, then purchased / N/A. How the caller got the vehicle, from their answer to "Did you purchase the vehicle, or lease it?" and the follow-up "is it still leased, or did you later buy it out?". Purchased = they bought it (cash, loan or financing). Leased = it is on a lease now (Spanish "arrendado", "arrendé", "rentado", "lo rento"). Leased, then purchased = it started as a lease and they later bought it out. Treat close-sounding mis-transcriptions of lease ("liz", "list", "lists", "leave it" / "I\'ll leave it" for "I leased it", "Rendée", "renté") as lease. Never return Leased or Leased, then purchased unless the caller actually said the vehicle is or was leased. N/A if not discussed.',
    'prompt purchase_type');
  sys = rep(sys, '- new_or_used: New / Used / N/A (was it purchased new or used)',
    '- new_or_used: New / Used / N/A (was the vehicle new or used when they got it, whether bought or leased)', 'prompt new_or_used');
  sys = rep(sys, '(issue, ca_purchase, in_possession, new_or_used, is_cpo, repairs_attempted, is_owner)',
    '(issue, ca_purchase, purchase_type, in_possession, new_or_used, is_cpo, repairs_attempted, is_owner)', 'prompt voicemail list');
  user = rep(user, '(issue, ca_purchase, in_possession, vehicle_year,', '(issue, ca_purchase, purchase_type, in_possession, vehicle_year,', 'user msg retainer-only list');
  return { sys, user };
}

function patchPayload(src) {
  return rep(src, "  'Purchase Condition': c.purchase_condition,", "  'Purchase Condition': c.purchase_condition,\n  'Purchase Type': c.purchase_type,", 'payload Purchase Type');
}

(async () => {
  const wf = await (await fetch(`${BASE}/api/v1/workflows/${WF}`, { headers: H })).json();
  const cl = wf.nodes.find((n) => n.name === 'Classify Lead');
  const ai = wf.nodes.find((n) => n.name === 'AI - Post-Call Extract');
  const bp = wf.nodes.find((n) => n.name === 'Build Payload');
  const live = { classify: lf(cl.parameters.jsCode), sys: lf(ai.parameters.messages.values[0].content), user: lf(ai.parameters.messages.values[1].content), payload: lf(bp.parameters.jsCode) };
  const next = { classify: patchClassify(live.classify), payload: patchPayload(live.payload), ...patchPrompt(live.sys, live.user) };
  fs.writeFileSync(path.join(OUT, 'classify_live.js'), live.classify);
  fs.writeFileSync(path.join(OUT, 'classify_new.js'), next.classify);
  fs.writeFileSync(path.join(OUT, 'ai_system_live.txt'), live.sys);
  fs.writeFileSync(path.join(OUT, 'ai_system_new.txt'), next.sys);
  fs.writeFileSync(path.join(OUT, 'ai_user_new.txt'), next.user);
  fs.writeFileSync(path.join(OUT, 'build_payload_new.js'), next.payload);
  new Function('$input', '$', next.classify); new Function('$input', '$', next.payload); // syntax check
  console.log('patched: classify ' + live.classify.length + ' -> ' + next.classify.length + ', system prompt ' + live.sys.length + ' -> ' + next.sys.length + ', payload ' + live.payload.length + ' -> ' + next.payload.length);
  if (process.env.APPLY !== '1') { console.log('DRY RUN: nothing pushed'); return; }

  cl.parameters.jsCode = next.classify;
  ai.parameters.messages.values[0].content = next.sys;
  ai.parameters.messages.values[1].content = next.user;
  bp.parameters.jsCode = next.payload;
  const put = await fetch(`${BASE}/api/v1/workflows/${WF}`, { method: 'PUT', headers: H, body: JSON.stringify({ name: wf.name, nodes: wf.nodes, connections: wf.connections, settings: { executionOrder: 'v1' } }) });
  console.log('PUT ' + put.status + (put.ok ? ' OK' : ' ' + (await put.text()).slice(0, 400)));
  const v = await (await fetch(`${BASE}/api/v1/workflows/${WF}`, { headers: H })).json();
  const g = (name) => v.nodes.find((n) => n.name === name).parameters;
  const checks = {
    active: v.active === true,
    classify: lf(g('Classify Lead').jsCode) === next.classify,
    system: lf(g('AI - Post-Call Extract').messages.values[0].content) === next.sys,
    user: lf(g('AI - Post-Call Extract').messages.values[1].content) === next.user,
    payload: lf(g('Build Payload').jsCode) === next.payload,
  };
  console.log('verify: ' + JSON.stringify(checks));
  fs.writeFileSync('D:/tmp/classify_known_good.js', next.classify);
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
