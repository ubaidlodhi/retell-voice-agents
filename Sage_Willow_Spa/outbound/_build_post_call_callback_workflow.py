"""
Build the "inbound call went nowhere -> Aria rings them back" workflow in n8n.

Run:  py -X utf8 outbound/_build_post_call_callback_workflow.py [--update <id>] [--dry-run]

Flow
----
    Webhook (POST /webhook/sage-willow-post-call)      <- Retell agent webhook, call_analyzed
        -> Prepare Call               (hard facts only: right agent? real caller? transcript?)
        -> IF Classify With AI?
             yes -> Classify Call Outcome   (AI Agent: OpenAI gpt-4.1-mini + structured output)
             no  -> (straight through)
        -> Apply Verdict              (merge the AI verdict with the call facts)
        -> IF Needs Callback?
             no  -> Skip
             yes -> Retell: Did They Call Back?     (inbound calls from that number since)
                 -> Retell: Already Called Back?    (outbound calls TO that number, last few minutes)
                 -> Decide
                 -> IF Still Needed?
                      no  -> Skip
                      yes -> Trigger Outbound Call  (POST /webhook/sage-willow-lead-callout,
                                                     source = missed_call)

Who decides what
----------------
Retell's own post-call analysis variables are NOT used. The judgement "did the
caller actually get what they needed?" is made by an OpenAI gpt-4.1-mini agent
reading the transcript plus the list of tools the inbound agent really invoked
(so "you're all set" with no book_appointment result counts as NOT booked).

Code only handles the things that are facts, not judgement:
  * ignore anything that is not an inbound phone call on the inbound agent
    from a real US number
  * transfers, scam/voicemail detections   -> leave alone
  * platform errors                        -> call back, nothing to read
  * never connected / no transcript        -> call back, nothing to read
Everything with a transcript goes to the model. If the model call fails the
call is NOT rung back (fail closed) and the execution shows why.

The outbound call is placed through the SAME trigger webhook the website form
uses, so the TEST_MODE allowlist there applies here too: while testing, only
allowlisted numbers can ever be rung back.

`dryRun: true` on the incoming payload (only ever set by hand, Retell never
sends it) asks the trigger for a dry run, so the whole chain - including the
model - can be exercised without placing a call.
"""

from __future__ import annotations
import argparse
import json
import os
import urllib.request
from pathlib import Path

N8N_BASE = "https://automation.aiemply.com"
WEBHOOK_PATH = "sage-willow-post-call"
WORKFLOW_NAME = "Sage & Willow | Inbound Post-Call -> Missed-Call Callback (DEV)"

INBOUND_AGENT_ID = "agent_eceb7448aa1f37e8f436a63a43"
OUTBOUND_AGENT_ID = "agent_4ef8160dc71826818c6fd8122b"
SPA_NUMBER = "+16282862281"
CALLOUT_WEBHOOK = f"{N8N_BASE}/webhook/sage-willow-lead-callout"

# Must be a key from the SAME Retell workspace as the Sage & Willow agents. The
# older "AIEmply Retell" credential (4jRLd05k8mKynNRp) is a different workspace:
# list-calls returns [] there and create-phone-call cannot see the agent.
RETELL_BEARER_CRED = {"id": "PCD0SY42490CXB82", "name": "Retell - Sage & Willow workspace"}
OPENAI_CRED = {"id": "TQ8G7IyCTNGZ2HQ3", "name": "AIEmply - Veltro"}
OPENAI_MODEL = "gpt-4.1-mini"

# No grace period: Ubaid's call (2026-09-12) - ring back immediately. The redial
# check below still catches anyone who dialled again while the call was analysed.
# Never ring the same number back more than once in this window. Short on
# purpose: it exists to stop a burst (four abandoned calls in a row -> four
# callbacks), and 24 h blocked Ubaid's retests (exec 1687). Raise at go-live if
# the client wants it.
DEDUP_MINUTES = 5

OUT_DIR = Path(__file__).parent
SNAPSHOT_PATH = OUT_DIR / "post_call_callback_workflow.json"


def api_key() -> str:
    key = os.environ.get("N8N_API_KEY")
    if key:
        return key
    mcp = Path(__file__).resolve().parents[2] / ".mcp.json"
    raw = mcp.read_text(encoding="utf-8")
    cfg = json.loads(raw[raw.index("{"):])
    return cfg["mcpServers"]["n8n-mcp"]["env"]["N8N_API_KEY"]


def request(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        f"{N8N_BASE}{path}", data=data, method=method,
        headers={
            "X-N8N-API-KEY": api_key(),
            "Content-Type": "application/json",
            "User-Agent": "curl/8.0",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise SystemExit(
            f"n8n API {method} {path} -> {exc.code}: {exc.read().decode('utf-8', 'replace')}"
        ) from None


# -----------------------------------------------------------------------------
# 1. Prepare Call - facts only, no judgement
# -----------------------------------------------------------------------------

PREPARE_CODE = r"""
const INBOUND_AGENT_ID = '%(inbound_agent)s';
const SPA_NUMBER = '%(spa_number)s';

const env = $input.first().json;
const body = (env && typeof env.body === 'object' && env.body !== null) ? env.body : env;
const event = body.event;
const call = body.call || {};
const dryRun = body.dryRun === true || body.dryRun === 'true';

const durationMs = Number(call.duration_ms ?? ((call.end_timestamp || 0) - (call.start_timestamp || 0)));
const dr = String(call.disconnection_reason || '');

// route: 'skip' (leave alone), 'callback' (nothing to read, ring back), 'classify' (ask the model)
const out = (route, why, extra) => [{ json: {
  route,
  route_reason: why,
  call_id: call.call_id || null,
  from_number: call.from_number || null,
  dryRun,
  started_at: call.start_timestamp ? new Date(call.start_timestamp).toISOString() : new Date().toISOString(),
  ended_at_ms: Number(call.end_timestamp || call.start_timestamp || Date.now()),
  duration_ms: durationMs,
  disconnection_reason: dr,
  llm_input: '',
  ...(extra || {}),
}}];

if (event !== 'call_analyzed') return out('skip', `event ${event || 'missing'}`);
if (call.agent_id && call.agent_id !== INBOUND_AGENT_ID) return out('skip', 'not the inbound agent');
if (call.direction !== 'inbound') return out('skip', `direction ${call.direction || 'missing'}`);
if (call.call_type && call.call_type !== 'phone_call') return out('skip', `call_type ${call.call_type}`);

const from = String(call.from_number || '');
if (!/^\+1\d{10}$/.test(from)) return out('skip', 'no usable caller number');
if (from === SPA_NUMBER) return out('skip', 'caller is the spa line');

// Hard facts about how the call ended.
if (dr === 'call_transfer') return out('skip', 'transferred to the team');
if (['scam_detected', 'machine_detected', 'voicemail_reached'].includes(dr)) return out('skip', dr);
if (dr.startsWith('error')) return out('callback', `platform error (${dr})`);

// Rebuild the conversation. Prefer the structured transcript; fall back to the text one.
const turns = [];
if (Array.isArray(call.transcript_object) && call.transcript_object.length) {
  for (const t of call.transcript_object) {
    if (!t || typeof t.content !== 'string' || !t.content.trim()) continue;
    turns.push(`${t.role === 'agent' ? 'Aria' : 'Caller'}: ${t.content.trim()}`);
  }
} else if (typeof call.transcript === 'string' && call.transcript.trim()) {
  for (const line of call.transcript.split('\n')) {
    const s = line.trim();
    if (s) turns.push(s.replace(/^Agent:/, 'Aria:').replace(/^User:/, 'Caller:'));
  }
}

// What the inbound agent actually did - the model must not trust Aria's words alone.
const tools = [];
if (Array.isArray(call.transcript_with_tool_calls)) {
  // Results only carry tool_call_id; map it back to the invocation's name.
  const nameById = {};
  for (const t of call.transcript_with_tool_calls) {
    if (t && t.role === 'tool_call_invocation' && t.tool_call_id) nameById[t.tool_call_id] = t.name;
  }
  for (const t of call.transcript_with_tool_calls) {
    if (!t) continue;
    if (t.role === 'tool_call_invocation') tools.push(`invoked ${t.name}(${String(t.arguments || '').slice(0, 200)})`);
    if (t.role === 'tool_call_result') tools.push(`result of ${t.name || nameById[t.tool_call_id] || 'tool'}: ${String(t.content || '').slice(0, 300)}`);
  }
}

if (call.call_status === 'not_connected' || durationMs < 5000 || !turns.length) {
  return out('callback', 'never connected / nothing said');
}

const callerTurns = turns.filter(t => t.startsWith('Caller:')).length;
// Only Aria's greeting on the tape: they reached out and never got a word in. Nothing to judge.
if (!callerTurns) return out('callback', 'caller never spoke');

const llmInput = [
  `Call length: ${Math.round(durationMs / 1000)} seconds. Ended by: ${dr || 'unknown'}. Caller turns: ${callerTurns}.`,
  '',
  'Tools the receptionist actually invoked during the call:',
  tools.length ? tools.map(t => '- ' + t).join('\n') : '- none',
  '',
  'Transcript:',
  turns.join('\n'),
].join('\n');

return out('classify', 'has transcript', { llm_input: llmInput, caller_turns: callerTurns, tools_invoked: tools.length });
""" % {
    "inbound_agent": INBOUND_AGENT_ID,
    "spa_number": SPA_NUMBER,
}


# -----------------------------------------------------------------------------
# 2. The model
# -----------------------------------------------------------------------------

SYSTEM_MESSAGE = """You review transcripts of inbound phone calls to Sage & Willow Spa, a massage spa. The receptionist on the call is an AI named Aria. Your job: decide whether the caller got what they rang for, or whether the call ended incomplete and the spa should ring them back.

Return ONLY a JSON object matching the schema you are given. No prose.

Definitions of "outcome":
- booking_made: a new appointment was actually created.
- booking_changed: an existing appointment was actually rescheduled.
- booking_cancelled: an existing appointment was actually cancelled.
- question_answered: the caller asked something (hours, prices, services, directions, availability) and got a real answer. Counts even if they hung up abruptly afterwards.
- message_taken: Aria took a message or callback request for the team, or confirmed the team would ring them. The team handles it - no callback from you.
- transferred: the caller was handed to a person.
- leave_alone: spam, sales pitch, robocall, wrong number or misdial, inappropriate or sexual request, medical emergency or crisis, an obvious test call, off-topic, or the caller said not to call them.
- incomplete: the caller wanted something (to book, change, cancel, check, ask, or reach someone) and did NOT get it. Includes: hung up or was cut off mid-flow, silence or noise then a hang-up, Aria looped, misunderstood, or failed, a tool error, the caller gave up.

Hard rules:
1. needs_callback is true ONLY when outcome is "incomplete". For every other outcome it is false.
2. Never take Aria's word for a booking, change, or cancellation. "You're all set", "I've booked that", "it's confirmed" are only true if the tools list shows the matching tool (book_appointment, reschedule_booking, cancel_booking) returning a successful result. A claimed booking with no successful tool result is "incomplete" and needs a callback - the caller believes they are booked and they are not.
3. get_slots, get_services, get_staff, get_booking are lookups, not outcomes. flag_callback with a successful result means message_taken.
4. A call where the caller barely spoke (hello, silence, noise) and then the line dropped is "incomplete" - they reached out and got nothing.
5. caller_first_name: only a name the CALLER gave for themselves, exactly as said. Never "Aria". Empty string if none.
6. caller_wanted: a short phrase in plain English describing what they were after, e.g. "booking a deep tissue massage", "moving Saturday's appointment", "asking about prices". Empty if unclear.
7. reason: one short sentence a spa employee would understand."""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "outcome": {
            "type": "string",
            "enum": ["booking_made", "booking_changed", "booking_cancelled", "question_answered",
                     "message_taken", "transferred", "leave_alone", "incomplete"],
        },
        "needs_callback": {"type": "boolean"},
        "reason": {"type": "string"},
        "caller_first_name": {"type": "string"},
        "caller_wanted": {"type": "string"},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
    },
    "required": ["outcome", "needs_callback", "reason", "caller_first_name", "caller_wanted", "confidence"],
    "additionalProperties": False,
}


# -----------------------------------------------------------------------------
# 3. Apply Verdict - merge the model's answer with the facts
# -----------------------------------------------------------------------------

VERDICT_CODE = r"""
const prep = $('Prepare Call').first().json;
const item = $input.first().json;

// The AI Agent wraps the parsed JSON in `output`; on the no-model path the item IS prep.
const llm = item && typeof item.output === 'object' && item.output !== null ? item.output : null;

const base = {
  call_id: prep.call_id,
  from_number: prep.from_number,
  dryRun: prep.dryRun,
  started_at: prep.started_at,
  ended_at_ms: prep.ended_at_ms,
  duration_ms: prep.duration_ms,
  disconnection_reason: prep.disconnection_reason,
  route: prep.route,
  first_name: '',
  inbound_intent: '',
  outcome: '',
  confidence: '',
};

const done = (needsCallback, why) => [{ json: {
  ...base, needsCallback, reason: needsCallback ? why : '', skipReason: needsCallback ? '' : why,
}}];

if (prep.route === 'skip') return done(false, prep.route_reason);
if (prep.route === 'callback') return done(true, prep.route_reason);

// route === 'classify'
if (!llm) {
  const err = item && item.error ? (item.error.message || JSON.stringify(item.error)) : 'no model output';
  return done(false, `classifier failed: ${String(err).slice(0, 200)}`);
}

let firstName = String(llm.caller_first_name || '').trim();
if (!/^[A-Za-z][A-Za-z'\-]{0,29}$/.test(firstName) || /^(unknown|none|n\/a|caller|aria)$/i.test(firstName)) firstName = '';

base.first_name = firstName;
base.inbound_intent = String(llm.caller_wanted || '').trim().slice(0, 80);
base.outcome = String(llm.outcome || '');
base.confidence = String(llm.confidence || '');

const needs = llm.needs_callback === true && llm.outcome === 'incomplete';
return done(needs, `${llm.outcome}: ${String(llm.reason || '').trim()}`);
"""


# -----------------------------------------------------------------------------
# 4. Decide - using live Retell history
# -----------------------------------------------------------------------------

DECIDE_CODE = r"""
const OUTBOUND_AGENT_ID = '%(outbound_agent)s';
const DEDUP_MS = %(dedup_ms)d;

const ev = $('Apply Verdict').first().json;
const asList = (name) => {
  const items = $(name).all().map(i => i.json);
  // The HTTP node returns one item per call, or a single item wrapping the array.
  if (items.length === 1 && Array.isArray(items[0])) return items[0];
  if (items.length === 1 && items[0] && Array.isArray(items[0].data)) return items[0].data;
  return items.filter(c => c && c.call_id);
};

// Did they ring us back themselves after that call ended?
const redials = asList('Retell: Did They Call Back?')
  .filter(c => c.call_id !== ev.call_id && c.from_number === ev.from_number
            && Number(c.start_timestamp || 0) > ev.ended_at_ms);

// Has Aria already rung this number back recently?
const since = Date.now() - DEDUP_MS;
const priorCallbacks = asList('Retell: Already Called Back?')
  .filter(c => c.to_number === ev.from_number && c.agent_id === OUTBOUND_AGENT_ID
            && Number(c.start_timestamp || 0) > since);

let skipReason = '';
if (redials.length) skipReason = `caller rang back themselves (${redials[0].call_id})`;
else if (priorCallbacks.length) skipReason = `already called back within window (${priorCallbacks[0].call_id})`;

return [{ json: {
  ...ev,
  stillNeeded: !skipReason,
  skipReason,
  redials: redials.length,
  priorCallbacks: priorCallbacks.length,
}}];
""" % {
    "outbound_agent": OUTBOUND_AGENT_ID,
    "dedup_ms": DEDUP_MINUTES * 60 * 1000,
}


# -----------------------------------------------------------------------------
# Workflow
# -----------------------------------------------------------------------------

def node(id_, name, type_, tv, pos, params, **extra):
    n = {"id": id_, "name": name, "type": type_, "typeVersion": tv,
         "position": pos, "parameters": params}
    n.update(extra)
    return n


def bool_if(id_, name, pos, field):
    return node(id_, name, "n8n-nodes-base.if", 2, pos,
                {"conditions": {
                    "options": {"caseSensitive": True, "leftValue": "",
                                "typeValidation": "strict", "version": 2},
                    "conditions": [{
                        "id": f"c-{id_}",
                        "operator": {"type": "boolean", "operation": "true", "singleValue": True},
                        "leftValue": f"={{{{ $json.{field} }}}}", "rightValue": ""}],
                    "combinator": "and"},
                 "options": {}})


def string_eq_if(id_, name, pos, field, value):
    return node(id_, name, "n8n-nodes-base.if", 2, pos,
                {"conditions": {
                    "options": {"caseSensitive": True, "leftValue": "",
                                "typeValidation": "strict", "version": 2},
                    "conditions": [{
                        "id": f"c-{id_}",
                        "operator": {"type": "string", "operation": "equals"},
                        "leftValue": f"={{{{ $json.{field} }}}}", "rightValue": value}],
                    "combinator": "and"},
                 "options": {}})


def retell_list_calls(id_, name, pos, filter_expr):
    return node(id_, name, "n8n-nodes-base.httpRequest", 4.2, pos,
                {"method": "POST",
                 "url": "https://api.retellai.com/v2/list-calls",
                 "authentication": "genericCredentialType",
                 "genericAuthType": "httpBearerAuth",
                 "sendBody": True,
                 "specifyBody": "json",
                 "jsonBody": filter_expr,
                 "options": {}},
                credentials={"httpBearerAuth": RETELL_BEARER_CRED},
                alwaysOutputData=True,
                executeOnce=True,
                onError="continueRegularOutput")


def build() -> dict:
    ev = "$('Apply Verdict').first().json"

    nodes = [
        node("wh-postcall", "Webhook - Retell call_analyzed", "n8n-nodes-base.webhook", 2,
             [-1100, 300],
             {"httpMethod": "POST", "path": WEBHOOK_PATH,
              "responseMode": "onReceived", "options": {}},
             webhookId="sage-willow-post-call-v1"),

        node("prepare", "Prepare Call", "n8n-nodes-base.code", 2,
             [-880, 300], {"jsCode": PREPARE_CODE}),

        string_eq_if("if-classify", "IF: Classify With AI?", [-660, 300], "route", "classify"),

        # ---- the model -------------------------------------------------------
        node("classify", "Classify Call Outcome", "@n8n/n8n-nodes-langchain.agent", 3.1,
             [-420, 160],
             {"promptType": "define",
              "text": "={{ $json.llm_input }}",
              "hasOutputParser": True,
              "options": {"systemMessage": SYSTEM_MESSAGE}},
             retryOnFail=True, maxTries=2, waitBetweenTries=2000,
             onError="continueRegularOutput"),

        node("openai", "OpenAI Chat Model", "@n8n/n8n-nodes-langchain.lmChatOpenAi", 1.3,
             [-460, 380],
             {"model": {"__rl": True, "mode": "id", "value": OPENAI_MODEL},
              "responsesApiEnabled": False,
              "options": {"temperature": 0}},
             credentials={"openAiApi": OPENAI_CRED}),

        node("parser", "Structured Output Parser", "@n8n/n8n-nodes-langchain.outputParserStructured", 1.3,
             [-260, 380],
             {"schemaType": "manual",
              "inputSchema": json.dumps(OUTPUT_SCHEMA, indent=2),
              # autoFix needs a second model wired to the parser itself; the agent's
              # retryOnFail already covers a malformed answer.
              "autoFix": False}),

        node("verdict", "Apply Verdict", "n8n-nodes-base.code", 2,
             [-40, 300], {"jsCode": VERDICT_CODE}),

        bool_if("if-needs", "IF: Needs Callback?", [180, 300], "needsCallback"),

        retell_list_calls(
            "redial", "Retell: Did They Call Back?", [620, 200],
            "={{ JSON.stringify({\n"
            "  filter_criteria: {\n"
            f"    from_number: [{ev}.from_number],\n"
            "    direction: ['inbound'],\n"
            f"    start_timestamp: {{ lower_threshold: {ev}.ended_at_ms + 1 }}\n"
            "  },\n"
            "  limit: 5, sort_order: 'descending'\n"
            "}) }}"),

        retell_list_calls(
            "dedup", "Retell: Already Called Back?", [840, 200],
            "={{ JSON.stringify({\n"
            "  filter_criteria: {\n"
            f"    agent_id: ['{OUTBOUND_AGENT_ID}'],\n"
            f"    to_number: [{ev}.from_number],\n"
            f"    start_timestamp: {{ lower_threshold: Date.now() - {DEDUP_MINUTES * 60 * 1000} }}\n"
            "  },\n"
            "  limit: 5, sort_order: 'descending'\n"
            "}) }}"),

        node("decide", "Decide", "n8n-nodes-base.code", 2,
             [1060, 200], {"jsCode": DECIDE_CODE}, executeOnce=True),

        bool_if("if-still", "IF: Still Needed?", [1280, 200], "stillNeeded"),

        node("trigger", "Trigger Outbound Call", "n8n-nodes-base.httpRequest", 4.2,
             [1500, 100],
             {"method": "POST",
              "url": CALLOUT_WEBHOOK,
              "sendBody": True,
              "specifyBody": "json",
              "jsonBody": (
                  "={{ JSON.stringify({\n"
                  "  source: 'missed_call',\n"
                  "  first_name: $json.first_name,\n"
                  "  phone: $json.from_number,\n"
                  "  submitted_at: $json.started_at,\n"
                  "  inbound_intent: $json.inbound_intent,\n"
                  "  inbound_call_id: $json.call_id,\n"
                  "  dryRun: $json.dryRun\n"
                  "}) }}"),
              "options": {}},
             onError="continueRegularOutput"),

        node("skip-1", "Skip: Nothing To Do", "n8n-nodes-base.noOp", 1, [400, 420], {}),
        node("skip-2", "Skip: Resolved Itself", "n8n-nodes-base.noOp", 1, [1500, 320], {}),
    ]

    def link(src, outputs):
        return {src: {"main": [[{"node": d, "type": "main", "index": 0} for d in outs]
                               for outs in outputs]}}

    connections = {}
    connections.update(link("Webhook - Retell call_analyzed", [["Prepare Call"]]))
    connections.update(link("Prepare Call", [["IF: Classify With AI?"]]))
    # true -> the model; false -> straight to the verdict (skip / callback routes)
    connections.update(link("IF: Classify With AI?", [["Classify Call Outcome"], ["Apply Verdict"]]))
    connections.update(link("Classify Call Outcome", [["Apply Verdict"]]))
    connections.update(link("Apply Verdict", [["IF: Needs Callback?"]]))
    connections.update(link("IF: Needs Callback?", [["Retell: Did They Call Back?"], ["Skip: Nothing To Do"]]))
    connections.update(link("Retell: Did They Call Back?", [["Retell: Already Called Back?"]]))
    connections.update(link("Retell: Already Called Back?", [["Decide"]]))
    connections.update(link("Decide", [["IF: Still Needed?"]]))
    connections.update(link("IF: Still Needed?", [["Trigger Outbound Call"], ["Skip: Resolved Itself"]]))

    # AI sub-node wiring: model and parser plug INTO the agent.
    connections["OpenAI Chat Model"] = {"ai_languageModel": [[
        {"node": "Classify Call Outcome", "type": "ai_languageModel", "index": 0}]]}
    connections["Structured Output Parser"] = {"ai_outputParser": [[
        {"node": "Classify Call Outcome", "type": "ai_outputParser", "index": 0}]]}

    return {
        "name": WORKFLOW_NAME,
        "nodes": nodes,
        "connections": connections,
        "settings": {"executionOrder": "v1", "timezone": "America/Los_Angeles"},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", metavar="WORKFLOW_ID")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    wf = build()
    SNAPSHOT_PATH.write_text(json.dumps(wf, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {SNAPSHOT_PATH.name} ({len(wf['nodes'])} nodes)")

    if args.dry_run:
        print("Dry run - n8n not modified.")
        return

    if args.update:
        result = request("PUT", f"/api/v1/workflows/{args.update}", wf)
        print(f"Updated workflow {result['id']}")
    else:
        result = request("POST", "/api/v1/workflows", wf)
        print(f"Created workflow {result['id']}")
    print(f"  webhook: {N8N_BASE}/webhook/{WEBHOOK_PATH}")
    print("  Activate it in n8n, then point the inbound agent's webhook_url at it.")


if __name__ == "__main__":
    main()
