// Creates the n8n workflow "Retell — Knight Law Draft Test Caller (latest version)" on automations.impleko.ai:
// a form (your number + which agent) that calls you on the agent's LATEST CREATED version (the draft while one exists).
//   node create_n8n_test_caller.js          -> builds it and runs the two code nodes locally with stub data
//   CREATE=1 node create_n8n_test_caller.js -> also creates + activates it in n8n and prints the form URL
const fs = require('fs');
const crypto = require('crypto');
const KEY = fs.readFileSync('D:/tmp/n8nkey.txt', 'utf8').trim();
const BASE = 'https://automations.impleko.ai';
const RETELL_CRED = { httpHeaderAuth: { id: 'SDIeyviXSjiuK28X', name: 'Retell API (Knight Law)' } };

const MAP_AGENT = `// Which agent to call with. Test contacts must have "test" in the name (GHL / reporting filters).
const f = $input.first().json;
const AGENTS = {
  'Intake (Outbound)': { id: 'agent_de01f772a9de26ecf4387115a9', kind: 'intake' },
  'Retainer Outbound': { id: 'agent_83f8b296e4652030d15a3417e6', kind: 'retainer_outbound' },
  'Retainer Immediate': { id: 'agent_7540b5be1e12d28fe1e937a832', kind: 'retainer_immediate' },
};
const a = AGENTS[f['Agent']];
if (!a) throw new Error('Unknown agent: ' + f['Agent']);
let to = String(f['Phone Number'] || '').trim();
const digits = to.split('').filter((ch) => ch >= '0' && ch <= '9').join('');
to = to.startsWith('+') ? '+' + digits : (digits.length === 10 ? '+1' + digits : '+' + digits);
if (to.length < 12) throw new Error('Phone number looks wrong: ' + f['Phone Number']);
// "Test" goes at the END so the agents still greet the caller by their real first name.
let name = String(f['Name'] || '').trim() || 'John';
if (name.toLowerCase().indexOf('test') === -1) name = name + ' Test';
const lang = String(f['Language'] || '');
return [{ json: {
  agent_id: a.id, kind: a.kind, to_number: to, name: name, email: String(f['Email'] || '').trim(),
  language: lang === 'Spanish' ? 'Spanish' : (lang === 'English' ? 'English' : ''),
  version_override: String(f['Version (blank = latest)'] || '').trim(),
} }];`;

const BUILD_CALL = `// Picks the LATEST CREATED version (highest number, published or not) unless a version was typed in the form,
// then builds the create-phone-call body with the dynamic variables that agent expects.
const m = $('Map Agent').first().json;
let versions = [];
for (const it of $input.all()) {
  const j = it.json;
  if (Array.isArray(j)) versions = versions.concat(j);
  else if (Array.isArray(j.items)) versions = versions.concat(j.items);
  else if (j && j.version !== undefined) versions.push(j);
}
if (!versions.length) throw new Error('Retell returned no versions for ' + m.agent_id);
const latest = versions.reduce((a, b) => (Number(b.version) > Number(a.version) ? b : a));
const version = m.version_override !== '' ? Number(m.version_override) : Number(latest.version);
const picked = versions.find((v) => Number(v.version) === version);
if (!picked) throw new Error('Version ' + version + ' does not exist for ' + m.agent_id);

const first = m.name.split(' ')[0];
const es = m.language === 'Spanish';
let dyn;
if (m.kind === 'intake') {
  // Same three fields the GHL dialer sends; empty lead_language = Alice picks the language from your pickup words.
  dyn = { Name: m.name, Phone: m.to_number, Email: m.email, lead_language: m.language };
} else if (m.kind === 'retainer_outbound') {
  dyn = { first_name: first, full_name: m.name, phone: m.to_number, email: m.email, lead_language: m.language || 'English',
    greeting: es ? 'Hola, ¿hablo con ' + first + '?' : 'Hi, is this ' + first + '?', call_number: '1',
    voicemail_script: es
      ? 'Hola ' + first + ', le habla Alice de Knight Law Group sobre su acuerdo de representación. Llámenos al (213) 205-3651. ¡Gracias!'
      : 'Hi ' + first + ', this is Alice with Knight Law Group about your representation agreement. Call us back at (213) 205-3651. Thanks!' };
} else {
  dyn = { first_name: first, full_name: m.name, phone: m.to_number, email: m.email, lead_language: m.language || 'English', entry_mode: 'immediate_handoff',
    greeting: es
      ? 'Muy bien, ' + first + ' — su acuerdo de representación acaba de salir a su teléfono y a su correo. ¿Le explico los puntos principales?'
      : 'Okay ' + first + " — that agreement just went out to your phone and email. Want me to walk you through the main points?" };
}
return [{ json: {
  body: { from_number: '+12132053651', to_number: m.to_number, override_agent_id: m.agent_id, override_agent_version: version, retell_llm_dynamic_variables: dyn },
  picked_version: version, picked_is_published: !!picked.is_published,
} }];`;

const formId = crypto.randomUUID();
const wf = {
  name: 'Retell — Knight Law Draft Test Caller (latest version)',
  settings: { executionOrder: 'v1', saveDataErrorExecution: 'all', saveDataSuccessExecution: 'all', saveManualExecutions: true },
  nodes: [
    { id: crypto.randomUUID(), name: 'Test Call Form', type: 'n8n-nodes-base.formTrigger', typeVersion: 2.2, position: [0, 0], webhookId: formId,
      parameters: {
        formTitle: 'Knight Law — Draft Test Call',
        formDescription: 'Calls your phone from (213) 205-3651 using the LATEST CREATED version of the agent you pick (the draft while one exists). The live number is not affected. Intake calls can send a real representation agreement: use your own email.',
        formFields: { values: [
          { fieldLabel: 'Phone Number', fieldType: 'text', placeholder: '+1XXXXXXXXXX', requiredField: true },
          { fieldLabel: 'Agent', fieldType: 'dropdown', requiredField: true, fieldOptions: { values: [{ option: 'Intake (Outbound)' }, { option: 'Retainer Outbound' }, { option: 'Retainer Immediate' }] } },
          { fieldLabel: 'Name', fieldType: 'text', placeholder: 'Your first and last name', requiredField: false },
          { fieldLabel: 'Email', fieldType: 'email', placeholder: 'you@example.com', requiredField: true },
          { fieldLabel: 'Language', fieldType: 'dropdown', requiredField: false, fieldOptions: { values: [{ option: 'Auto (from how I pick up)' }, { option: 'English' }, { option: 'Spanish' }] } },
          { fieldLabel: 'Version (blank = latest)', fieldType: 'number', requiredField: false },
        ] },
        responseMode: 'onReceived',
        options: { respondWithOptions: { values: { formSubmittedText: 'Calling you now on the latest version. Check the execution in n8n for the version number.' } } },
      } },
    { id: crypto.randomUUID(), name: 'Map Agent', type: 'n8n-nodes-base.code', typeVersion: 2, position: [220, 0], parameters: { jsCode: MAP_AGENT } },
    { id: crypto.randomUUID(), name: 'Get Agent Versions', type: 'n8n-nodes-base.httpRequest', typeVersion: 4.3, position: [440, 0], credentials: RETELL_CRED,
      parameters: { method: 'GET', url: '={{ "https://api.retellai.com/list-agent-versions/" + $json.agent_id }}', authentication: 'genericCredentialType', genericAuthType: 'httpHeaderAuth', options: {} } },
    { id: crypto.randomUUID(), name: 'Pick Latest Version', type: 'n8n-nodes-base.code', typeVersion: 2, position: [660, 0], parameters: { jsCode: BUILD_CALL } },
    { id: crypto.randomUUID(), name: 'Retell Create Phone Call', type: 'n8n-nodes-base.httpRequest', typeVersion: 4.3, position: [880, 0], credentials: RETELL_CRED,
      parameters: { method: 'POST', url: 'https://api.retellai.com/v2/create-phone-call', authentication: 'genericCredentialType', genericAuthType: 'httpHeaderAuth',
        sendBody: true, contentType: 'json', specifyBody: 'json', jsonBody: '={{ JSON.stringify($json.body) }}', options: {} } },
  ],
  connections: {
    'Test Call Form': { main: [[{ node: 'Map Agent', type: 'main', index: 0 }]] },
    'Map Agent': { main: [[{ node: 'Get Agent Versions', type: 'main', index: 0 }]] },
    'Get Agent Versions': { main: [[{ node: 'Pick Latest Version', type: 'main', index: 0 }]] },
    'Pick Latest Version': { main: [[{ node: 'Retell Create Phone Call', type: 'main', index: 0 }]] },
  },
};

// ---------- run both code nodes locally with stub data (the HTTP node splits a JSON array into one item per element) ----------
function run(code, input, nodes) {
  const $input = { first: () => input[0], all: () => input };
  const $ = (n) => ({ first: () => ({ json: nodes[n] }) });
  return new Function('$input', '$', code)($input, $)[0].json;
}
const RK = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
(async () => {
  const cases = [
    { Agent: 'Intake (Outbound)', 'Phone Number': '(555) 555-0123', Name: 'John Doe', Email: 'jane@acme.ai', Language: 'Auto (from how I pick up)', 'Version (blank = latest)': '' },
    { Agent: 'Retainer Outbound', 'Phone Number': '+15555550123', Name: '', Email: 'jane@acme.ai', Language: 'Spanish', 'Version (blank = latest)': '' },
    { Agent: 'Retainer Immediate', 'Phone Number': '5555550123', Name: 'Test Imm', Email: 'jane@acme.ai', Language: 'English', 'Version (blank = latest)': '3' },
  ];
  for (const f of cases) {
    const m = run(MAP_AGENT, [{ json: f }], {});
    const vs = await (await fetch('https://api.retellai.com/list-agent-versions/' + m.agent_id, { headers: { Authorization: 'Bearer ' + RK } })).json();
    const items = (Array.isArray(vs) ? vs : vs.items || []).map((v) => ({ json: v }));
    const out = run(BUILD_CALL, items, { 'Map Agent': m });
    console.log(f.Agent + ' -> v' + out.picked_version + ' (published=' + out.picked_is_published + ') ' + JSON.stringify(out.body).slice(0, 260));
  }
  if (process.env.CREATE !== '1') { console.log('DRY RUN: workflow not created'); return; }
  const H = { 'X-N8N-API-KEY': KEY, 'Content-Type': 'application/json' };
  const r = await fetch(BASE + '/api/v1/workflows', { method: 'POST', headers: H, body: JSON.stringify(wf) });
  const j = await r.json();
  if (!r.ok) throw new Error('create ' + r.status + ' ' + JSON.stringify(j).slice(0, 400));
  const act = await fetch(BASE + '/api/v1/workflows/' + j.id + '/activate', { method: 'POST', headers: H });
  console.log('created ' + j.id + ', activate ' + act.status + (act.ok ? '' : ' ' + (await act.text()).slice(0, 300)));
  console.log('form: ' + BASE + '/form/' + formId);
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
