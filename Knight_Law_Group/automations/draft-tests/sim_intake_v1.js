// Retell simulation tests for the Alice Intake OUTBOUND draft (conversation_flow_b4e1b9683eaf, version 1, unpublished).
// Ubaid asked for these on 2026-10-19: few tests, broad coverage. Read the transcripts yourself; the judge's pass/fail is not the verdict.
//   node sim_intake_v1.js create            -> creates the 8 definitions + one batch, saves ids to out/sim/run.json
//   node sim_intake_v1.js results           -> waits for the batch, writes every transcript + verdict to out/sim/
//   node sim_intake_v1.js cleanup           -> deletes the 8 definitions
// Both webhooks are mocked, so nothing reaches GHL. Code nodes (hours / callback) read the real clock at run time.
const fs = require('fs');
const path = require('path');
const KEY = fs.readFileSync('D:/tmp/retellkey.txt', 'utf8').trim();
const H = { Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };
const BASE = 'https://api.retellai.com';
const ENGINE = { type: 'conversation-flow', conversation_flow_id: 'conversation_flow_b4e1b9683eaf', version: 1 };
const SIM_MODEL = 'gpt-4.1';
const OUT = path.join(__dirname, 'out', 'sim');
const RUN = path.join(OUT, 'run.json');

const MOCKS = [
  { tool_name: 'send_agreement', input_match_rule: { type: 'any' }, output: '{"status":"Success"}' },
  { tool_name: 'send_consultation_link', input_match_rule: { type: 'any' }, output: '{"status":"Success"}' },
];
const VARS = (name, email) => ({ Name: name, Phone: '+13105550101', Email: email, lead_language: '' });
const PICKUP = 'This is an outbound phone call to you. When it connects, answer the way a person picks up the phone ("Hello?") and wait for Alice to speak. ';
const STYLE = ' Keep every reply short and natural, like a real person on the phone (one sentence, often just a few words). Answer only what she asks unless the script below says otherwise. When the call is clearly over, say goodbye.';
const GLOBAL_METRICS = [
  'Alice never reads stage directions, node names, variable names, lead classifications or routing logic aloud (ignore tool_call / tool_call_result lines, they are not spoken).',
  'Alice never asks for the same piece of information twice after the caller has clearly given it.',
];

const TESTS = [
  {
    name: 'INTAKE-V1 T1 retainer path, skip known answers, FAQ check-in',
    vars: VARS('John Test', 'john.test@acme.ai'),
    prompt: PICKUP + 'You are John Test. You filled in a form on the Knight Law Group website about your truck: a 2023 Ford F-150. '
      + 'When Alice asks whether you have issues with the vehicle, say in one go: "Yeah, the transmission keeps slipping, and it\'s been at the dealer three times already." '
      + 'When she asks about California, say: "Yes, I bought it brand new in Los Angeles." '
      + 'If she asks whether you still have it, say: "It\'s at the dealer right now, actually." Give the year, make and model when asked and confirm her read-back. '
      + 'The FIRST time she asks whether you are the owner or the one who signed the contract, do not answer yet: ask "Wait, how much is this going to cost me?" '
      + 'After her answer ask "How long does the whole thing take?" After that answer say, in one breath: "No, that\'s all. And yes, it\'s my truck." If she still asks about the owner, say "Yes." '
      + 'Your name is John Test; your email john.test@acme.ai is correct; texts and emails are fine. If she spells your name, say yes. '
      + 'When she says she is sending the agreement, say "Okay, sounds good."' + STYLE,
    metrics: [
      'Alice does NOT ask whether the vehicle was purchased or leased, whether it was new or used, or whether it has been taken to the dealer for repairs, because the caller already said he bought it brand new and it has been at the dealer three times.',
      'During the intake part (before the agreement is sent), on cost Alice says the caller pays nothing / the manufacturer pays the attorney fees, and does not say fees come out of the caller\'s recovery or call it a contingency fee. (Later, a 50/50 split of money ABOVE the buyback is the firm\'s real term and is correct.)',
      'After EACH of the caller\'s two questions, Alice ends her answer with a short check-in question ("does that help?" / "anything else?"), worded differently the second time.',
      'After the caller says "that\'s all, and yes, it\'s my truck", Alice does not ask the owner question again and her next turn ends with a question (she moves on to the name / contact step).',
      'Before the call is handed off, Alice says she will text and email the representation agreement, and the send_agreement tool is called (the lead is qualified as a retainer lead).',
      'After the hand-off, the agent never thanks the caller for signing or says it is done unless the caller actually said they signed or submitted it, and never speaks an internal note such as "call ended" or "closing the call".',
    ],
  },
  {
    name: 'INTAKE-V1 T2 non-retainer, neutral re-ask, unclear CPO, after hours',
    vars: VARS('Jane Test', 'jane.test@acme.ai'),
    prompt: PICKUP + 'You are Jane Test. Your car is a 2022 Nissan Altima. When asked about issues say: "Yes, the car keeps shutting off on the freeway." '
      + 'California: "Yes, I bought it in Fresno." If asked purchase or lease: "I bought it." You still have it. Give year, make, model and confirm. '
      + 'When she asks whether it was new or used, answer only "No." (you misheard). When she asks again, say "Used." '
      + 'When she asks if it is certified pre-owned / CPO, say "Hmm, it came with some kind of warranty, I think." If she asks again, say "Honestly, I\'m not sure." '
      + 'Answer the rest of her questions with yes, it was taken in for repairs, and you are the owner. Your name is Jane Test, email jane.test@acme.ai is right, texts and emails are fine. '
      + 'If she offers to connect you with someone now, say "No, not right now, just send me the link."' + STYLE,
    metrics: [
      'After the caller answers "No" to the new-or-used question, Alice asks again neutrally (e.g. "sorry, was it new or used?") and does NOT assume "new" or "used".',
      'On the unclear CPO answers ("some kind of warranty", "not sure") Alice explains CPO or asks again, and does NOT tell the caller she doesn\'t qualify.',
      'The lead is treated as a NON-RETAINER lead: no agreement is sent and she is not disqualified. The call ends with Alice saying a consultation booking link will be texted (if she first offers to connect the caller to an Intake Analyst, the caller declines and she then gives the booking-link close).',
      'Alice does not ask the dealer-repairs or owner questions after the CPO answer, and asks for the name and the text/email permission in separate turns.',
    ],
  },
  {
    name: 'INTAKE-V1 T3 lease buyout BMW, follow-up required, non-retainer',
    vars: VARS('Mark Test', 'mark.test@acme.ai'),
    prompt: PICKUP + 'You are Mark Test with a 2022 BMW X5. Issues: "The screen keeps going black while I drive." California: "Yes." '
      + 'When asked whether you purchased or leased it, say ONLY "I leased it." and stop. If she then asks whether it is still leased or you bought it out, say "I bought it out last year." '
      + 'You still have it. Give year, make, model and confirm. Your name is Mark Test, email mark.test@acme.ai is right, texts and emails are fine. '
      + 'If she offers to connect you to someone now, say "Yes, please."' + STYLE,
    metrics: [
      'After the bare answer "I leased it", Alice asks whether it is still leased or was bought out, BEFORE moving on to other questions.',
      'Alice does NOT read an arbitration explanation and does NOT tell the caller the case can\'t be taken (a BMW lease buyout is not an arbitration case).',
      'Alice does not ask the retainer-only questions (new or used, CPO, dealer repairs, owner) and ends on the consultation booking-link close.',
    ],
  },
  {
    name: 'INTAKE-V1 T4 callback from the opening: out-of-hours ask, then change',
    vars: VARS('Paul Test', 'paul.test@acme.ai'),
    prompt: PICKUP + 'You are Paul Test and you are driving. As soon as Alice introduces herself, say: "I\'m driving right now, can you call me back?" '
      + 'When she asks when, say: "Tomorrow morning, like 7." If she says that time doesn\'t work, say: "Okay, 5 PM then." '
      + 'After she confirms 5 PM, say: "Actually, make it 6." After she confirms again, say "Great, thanks, bye."' + STYLE,
    metrics: [
      'Alice asks for a day and time instead of just ending the call.',
      'For "tomorrow at 7 AM" Alice explains calls are made between 8 AM and 9 PM Pacific and asks for a time in that window; she does not confirm 7 AM.',
      'Alice confirms "tomorrow at 5 PM", then after the change confirms "tomorrow at 6 PM" (not 5 PM, not another day).',
      'Alice does not start the qualification questions and the call ends politely.',
    ],
  },
  {
    name: 'INTAKE-V1 T5 callback mid-call, next week (outside window)',
    vars: VARS('Lisa Test', 'lisa.test@acme.ai'),
    prompt: PICKUP + 'You are Lisa Test. Issues: "Yes, the brakes are making a loud grinding noise." California: "Yes." If asked purchase or lease: "I bought it." '
      + 'At the NEXT question after that, say: "Sorry, I can\'t talk right now, I\'m at work. Can you call me next week?" '
      + 'If she asks for a specific day or time, say "Just sometime next week." Then say goodbye.' + STYLE,
    metrics: [
      'Alice does NOT confirm a specific callback day or time for next week; she says the team will contact the caller soon (or similar) and wraps up.',
      'Alice stops the qualification questions once the caller says she can\'t talk, and does not push to continue.',
    ],
  },
  {
    name: 'INTAKE-V1 T6 making payments -> loan, Tesla arbitration, pushback',
    vars: VARS('Ryan Test', 'ryan.test@acme.ai'),
    prompt: PICKUP + 'You are Ryan Test with a 2024 Tesla Model Y. Issues: "The screen keeps turning off." California: "Yes, in San Diego." '
      + 'When asked whether you purchased or leased it, say: "I\'m making payments on it." If she asks lease or loan, say: "A loan." '
      + 'You still have it. Give year, make, model and confirm. After she explains why the case can\'t be taken, say: "Are you sure? There\'s no other way?" '
      + 'After her reply say "Okay, thanks."' + STYLE,
    metrics: [
      'After "I\'m making payments on it", Alice asks whether it is a lease or a loan to buy it.',
      'Alice says this line word for word: "Tesla\'s purchase and lease agreements include a clause requiring disputes to go through arbitration instead of a lawsuit. Our firm only handles cases through the court system, so unfortunately this isn\'t one we are able to take on."',
      'When the caller pushes back, Alice answers in new words without repeating that whole line again, does not restart qualification, and the call ends politely.',
    ],
  },
  {
    name: 'INTAKE-V1 T7 still-leased Mercedes, then corrects to buyout',
    vars: VARS('Kevin Test', 'kevin.test@acme.ai'),
    prompt: PICKUP + 'You are Kevin Test with a 2022 Mercedes-Benz C300. Issues: "The engine light keeps coming on and it stalls." California: "Yes." '
      + 'When asked purchase or lease, say "I leased it." If she asks still leased or bought out, say "Still leasing it." You still have it. Give year, make, model and confirm. '
      + 'When she says the case can\'t be taken because of the lease, say: "Oh wait, sorry, I actually bought it out last year. It\'s not leased anymore." '
      + 'Then keep answering: your name is Kevin Test, email kevin.test@acme.ai is right, texts and emails are fine. '
      + 'If she offers to connect you to someone now, say "Sure."' + STYLE,
    metrics: [
      'After the caller corrects himself (bought out the lease), Alice does NOT repeat or reaffirm the rejection; she continues the intake.',
      'After the bare answer "I leased it", Alice asks whether it is still leased or was bought out before moving on.',
      'The lead ends as a NON-RETAINER lead (Mercedes-Benz lease buyout): either the consultation booking-link close, or Alice offers to connect the caller to an Intake Analyst now and the caller accepts. It does not end on a disqualification and no agreement is sent.',
    ],
  },
  {
    name: 'INTAKE-V1 T8 Spanish, still-leased Honda, arbitration line in Spanish',
    vars: VARS('Juan Test', 'juan.test@acme.ai'),
    prompt: 'Esta es una llamada telefónica saliente hacia usted. Usted solo habla español. Cuando conteste, diga "¿Bueno?" y espere a que Alice hable. '
      + 'Usted es Juan Test y tiene un Honda Civic 2023. Problemas: "Sí, el carro se apaga solo en la calle." California: "Sí, en Los Ángeles." '
      + 'Si le pregunta si lo compró o lo arrendó: "Lo tengo en lease, lo estoy rentando." Si pregunta si todavía es arrendado o lo compró después: "Todavía lo estoy rentando." '
      + 'Todavía lo tiene. Dé año, marca y modelo y confirme. Cuando le explique que no pueden tomar el caso, diga "Ah, bueno, gracias." y despídase. '
      + 'Respuestas cortas y naturales, como una persona real por teléfono. Nunca hable en inglés.',
    metrics: [
      'Alice speaks Spanish for the whole call (Latin American: uses "usted"; never "vale" or "coche").',
      'Alice says this Spanish line word for word: "Como su vehículo es arrendado, el fabricante en realidad forma parte de su contrato de arrendamiento, y ese contrato incluye una cláusula que exige que las disputas se resuelvan por arbitraje en lugar de una demanda. Nuestra firma solo lleva casos a través de los tribunales, así que lamentablemente este no es un caso que podamos aceptar."',
      'The call ends politely without restarting qualification.',
    ],
  },
  {
    name: 'INTAKE-V1 T9 Spanish, vehicle given early, 2019 -> model-year bad lead',
    vars: VARS('Luis Test', 'luis.test@acme.ai'),
    prompt: 'Esta es una llamada telefónica saliente hacia usted. Usted solo habla español. Cuando conteste, diga "¿Bueno?" y espere a que Alice hable. '
      + 'Usted es Luis Test. Cuando le pregunte si tiene problemas con el vehículo, diga de una vez: "Sí, mi Chevrolet Silverado 2019 se apaga solo en la carretera." '
      + 'California: "Sí, lo compré en Fresno." Todavía lo tiene: "Sí, todavía lo tengo." Si le vuelve a preguntar el año, la marca o el modelo, conteste con paciencia. '
      + 'Si le confirma el vehículo, diga "Sí, correcto." Cuando le explique que no pueden tomar el caso, pregunte una vez: "¿Y no hay nada que puedan hacer?" y luego diga "Bueno, gracias." y despídase. '
      + 'Respuestas cortas y naturales, como una persona real por teléfono. Nunca hable en inglés.',
    metrics: [
      'Alice speaks Spanish for the whole call (Latin American: "usted", "carro"; never "vale" or "coche").',
      'Alice does NOT ask "did you purchase or lease it?" separately (the caller already said "lo compré") and does NOT ask for the year, make and model as a new question; at most she reads the vehicle back ONCE to confirm it, and she does not confirm it twice.',
      'The lead is disqualified because of the model year: Alice explains the firm handles model year 2021 and newer and a 2019 is outside the criteria. She sends no agreement and gives no booking link.',
      'When the caller asks if nothing can be done, Alice answers kindly in fresh words without repeating her explanation word for word and without restarting qualification, and the call ends politely.',
    ],
  },
  {
    name: 'INTAKE-V1 T10 opt-out mid-call',
    vars: VARS('Nina Test', 'nina.test@acme.ai'),
    prompt: PICKUP + 'You are Nina Test. Issues: "Yeah, the AC stopped working and the engine makes a weird noise." California: "Yes." If asked purchase or lease: "I bought it." '
      + 'At the NEXT question after that, say: "You know what, I\'m not interested anymore. Please take me off your list and don\'t call me again." '
      + 'If she says anything else after that, just say "Bye."' + STYLE,
    metrics: [
      'Right after the opt-out request, Alice acknowledges it respectfully and briefly, confirms the caller will be taken off the list / not contacted again, and ends the call.',
      'After the opt-out request Alice does not argue, does not try to re-qualify, does not ask any further qualification question, does not offer a callback, and does not say a booking link or agreement will be sent.',
    ],
  },
];

async function api(method, p, body) {
  const r = await fetch(BASE + p, { method, headers: H, body: body ? JSON.stringify(body) : undefined });
  const t = await r.text();
  if (!r.ok) throw new Error(method + ' ' + p + ' -> ' + r.status + ' ' + t.slice(0, 400));
  return t ? JSON.parse(t) : {};
}

function transcriptText(ts) {
  const arr = Array.isArray(ts) ? ts : (ts && (ts.transcript_object || ts.transcript || ts.utterances)) || [];
  if (typeof arr === 'string') return arr;
  return arr.map((u) => {
    if (u.role === 'tool_call_invocation') return '  [tool ' + u.name + ' ' + (u.arguments || '') + ']';
    if (u.role === 'tool_call_result') return '  [result ' + String(u.content || '').slice(0, 120) + ']';
    if (u.role === 'node_transition') return '  [node -> ' + (u.new_node_name || u.new_node_id || '?') + ']';
    return (u.role || '?') + ': ' + (u.content || '');
  }).join('\n');
}

(async () => {
  const mode = process.argv[2];
  fs.mkdirSync(OUT, { recursive: true });
  if (mode === 'create') {
    const f = await api('GET', '/get-conversation-flow/' + ENGINE.conversation_flow_id + '?version=' + ENGINE.version);
    if (f.is_published) throw new Error('flow v' + ENGINE.version + ' is published; these tests are meant for the draft');
    const ids = [];
    for (const t of TESTS) {
      const r = await api('POST', '/create-test-case-definition', {
        name: t.name, response_engine: ENGINE, user_prompt: t.prompt, metrics: [...t.metrics, ...GLOBAL_METRICS],
        dynamic_variables: t.vars, tool_mocks: MOCKS, llm_model: SIM_MODEL,
      });
      ids.push(r.test_case_definition_id);
      console.log('created', r.test_case_definition_id, t.name);
    }
    const b = await api('POST', '/create-batch-test', { test_case_definition_ids: ids, response_engine: ENGINE });
    fs.writeFileSync(RUN, JSON.stringify({ created: new Date().toISOString(), engine: ENGINE, ids, batch: b.test_case_batch_job_id }, null, 2));
    console.log('batch', b.test_case_batch_job_id, '->', RUN);
  } else if (mode === 'suite') {
    // node sim_intake_v1.js suite T1,T2,T6  -> updates the existing definitions from TESTS (or creates missing ones), then one batch
    const run = JSON.parse(fs.readFileSync(RUN, 'utf8'));
    const picks = (process.argv[3] || '').split(',').map((t) => Number(t.replace(/^T/i, '')));
    if (!picks.length || picks.some((n) => !TESTS[n - 1])) throw new Error('usage: suite T1,T2,... (T1..T' + TESTS.length + ')');
    const ids = [];
    for (const n of picks) {
      const t = TESTS[n - 1];
      const body = { name: t.name, response_engine: ENGINE, user_prompt: t.prompt, metrics: [...t.metrics, ...GLOBAL_METRICS], dynamic_variables: t.vars, tool_mocks: MOCKS, llm_model: SIM_MODEL };
      if (run.ids[n - 1]) { await api('PUT', '/update-test-case-definition/' + run.ids[n - 1], body); console.log('updated', run.ids[n - 1], t.name); }
      else { run.ids[n - 1] = (await api('POST', '/create-test-case-definition', body)).test_case_definition_id; console.log('created', run.ids[n - 1], t.name); }
      ids.push(run.ids[n - 1]);
    }
    const b = await api('POST', '/create-batch-test', { test_case_definition_ids: ids, response_engine: ENGINE });
    run.batch = b.test_case_batch_job_id;
    run.dir = 'suite-' + run.batch;
    fs.writeFileSync(RUN, JSON.stringify(run, null, 2));
    console.log('batch', run.batch, 'for', process.argv[3]);
  } else if (mode === 'rerun') {
    // node sim_intake_v1.js rerun T1,T2  -> new batch on the existing definitions; results go to out/sim/rerun-<batch>/
    const run = JSON.parse(fs.readFileSync(RUN, 'utf8'));
    const pick = (process.argv[3] || '').split(',').map((t) => run.ids[Number(t.replace(/^T/i, '')) - 1]).filter(Boolean);
    if (!pick.length) throw new Error('usage: rerun T1,T2,...');
    const b = await api('POST', '/create-batch-test', { test_case_definition_ids: pick, response_engine: ENGINE });
    run.batch = b.test_case_batch_job_id;
    run.dir = 'rerun-' + run.batch;
    fs.writeFileSync(RUN, JSON.stringify(run, null, 2));
    console.log('batch', run.batch, 'for', process.argv[3]);
  } else if (mode === 'results') {
    const run = JSON.parse(fs.readFileSync(RUN, 'utf8'));
    const OUTD = path.join(OUT, run.dir || '');
    fs.mkdirSync(OUTD, { recursive: true });
    let b;
    for (let i = 0; i < 90; i++) {
      b = await api('GET', '/get-batch-test/' + run.batch);
      if (b.status === 'complete') break;
      await new Promise((r) => setTimeout(r, 10000));
    }
    console.log('batch', run.batch, b.status, 'pass', b.pass_count, 'fail', b.fail_count, 'error', b.error_count, 'total', b.total_count);
    const runs = (await api('GET', '/v2/list-test-runs/' + run.batch + '?limit=100')).items || [];
    for (const x of runs) {
      const full = await api('GET', '/get-test-run/' + x.test_case_job_id).catch(() => x);
      const name = ((full.test_case_definition_snapshot || {}).name || x.test_case_job_id);
      const file = path.join(OUTD, name.split(' ')[1] + '.txt');
      fs.writeFileSync(path.join(OUTD, name.split(' ')[1] + '.json'), JSON.stringify(full, null, 2));
      fs.writeFileSync(file, name + '\nJUDGE: ' + full.status + '\n' + (full.result_explanation || '') + '\n\n' + transcriptText(full.transcript_snapshot) + '\n');
      console.log(String(full.status).padEnd(8), name, '->', file);
    }
  } else if (mode === 'cleanup') {
    const run = JSON.parse(fs.readFileSync(RUN, 'utf8'));
    for (const id of run.ids) { await api('DELETE', '/delete-test-case-definition/' + id); console.log('deleted', id); }
  } else {
    console.log('usage: node sim_intake_v1.js create | results | cleanup');
  }
})().catch((e) => { console.error('ERROR ' + e.message); process.exit(1); });
