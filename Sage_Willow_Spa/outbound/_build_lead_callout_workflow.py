"""
Build the Sage & Willow website-form -> outbound-call trigger workflow in n8n.

Run:  py -X utf8 outbound/_build_lead_callout_workflow.py [--update <id>] [--dry-run]

Flow
----
    Webhook (POST /webhook/sage-willow-lead-callout)
        -> CONFIG - Test Mode Allowlist   (TEST_MODE + ALLOWED_NUMBERS, edit in n8n)
        -> Normalize Lead        (accepts almost any form payload shape)
        -> IF Lead Valid?
             no  -> Respond 400
             yes -> IF Dry Run?
                      yes -> Respond with the normalized payload, no call placed
                      no  -> IF Allowed Number?
                               no  -> Respond 200 {skipped: test_mode_allowlist}
                               yes -> Retell: Create Phone Call -> Respond 200

Two callers feed this webhook:
  * the website booking form            -> source = "website_form" (default)
  * the inbound post-call automation     -> source = "missed_call"
Both end up dialling the same outbound agent; `lead_source` is handed to the
agent as a dynamic variable so the opening line fits the reason for the call.

TESTING GUARD: while TEST_MODE is true the outbound agent can only ever dial a
number in ALLOWED_NUMBERS. Everything else is acknowledged and dropped. Both
values live in the "CONFIG - Test Mode Allowlist" Set node so they can be
flipped in the n8n UI without a rebuild. Set TEST_MODE to false at go-live.

No dialling-hours gate: a submission dials immediately, around the clock.
That was an explicit product decision - if it needs to change later, it is one
IF node between "Lead Valid?" and "Dry Run?".

The `dryRun` flag exists so the normalizer can be exercised end to end without
placing a real phone call.

`agent_version` picks which outbound version to dial: "latest" (draft),
"latest_published" (the default - what every real lead gets) or a version
number. Anything else is ignored. Used by outbound/outbound_test_dialer.html.
"""

from __future__ import annotations
import argparse
import json
import os
import urllib.request
from pathlib import Path

N8N_BASE = "https://automation.aiemply.com"
WEBHOOK_PATH = "sage-willow-lead-callout"
WORKFLOW_NAME = "Sage & Willow | Website Lead -> Outbound Call (DEV)"

RETELL_FROM_NUMBER = "+16282862281"          # the spa's Retell DID
OUTBOUND_AGENT_ID = "agent_4ef8160dc71826818c6fd8122b"
# Must be a key from the SAME Retell workspace as the Sage & Willow agents. The
# older "AIEmply Retell" credential (4jRLd05k8mKynNRp) is a different workspace:
# list-calls returns [] there and create-phone-call cannot see the agent.
RETELL_BEARER_CRED = {"id": "PCD0SY42490CXB82", "name": "Retell - Sage & Willow workspace"}

# Testing guard defaults. These seed the CONFIG Set node; the live values are
# whatever that node says in n8n, so a rebuild resets them to these.
TEST_MODE = True
ALLOWED_NUMBERS = ["+12532681856"]           # Ubaid's test line

OUT_DIR = Path(__file__).parent
SNAPSHOT_PATH = OUT_DIR / "lead_callout_workflow.json"

ALLOWED_SETTINGS = {"executionOrder", "timezone"}


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
            "User-Agent": "curl/8.0",  # the WAF rejects the default urllib agent
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
# Normalizer
# -----------------------------------------------------------------------------
# The real Wix form does not exist yet, so this accepts the shapes such forms
# actually arrive in: flat JSON, a nested data/body/payload wrapper, a Wix
# `submissions` array of {fieldName, value}, or a `fields` array of
# {label, value}. Whatever turns up, it emits the four dynamic variables the
# outbound agent expects.

NORMALIZE_CODE = r"""
const raw = $('Webhook - Website Lead Form').first().json;
const cfg = $input.first().json;   // CONFIG - Test Mode Allowlist

// n8n wraps a webhook request as {headers, params, query, body}. Drop that
// envelope, then walk whatever the form actually sent - a flat object, a
// data/payload wrapper, a Wix `submissions` array, or a `fields` list - and
// collect every scalar into one flat, lowercased bag.
const start = (raw && typeof raw.body === 'object' && raw.body !== null) ? raw.body : raw;

const bag = {};
const seen = new Set();
const collect = (obj, depth) => {
  if (!obj || typeof obj !== 'object' || depth > 5 || seen.has(obj)) return;
  seen.add(obj);
  if (Array.isArray(obj)) {
    for (const entry of obj) {
      if (!entry || typeof entry !== 'object') continue;
      // Key/value pair styles: Wix submissions, generic field lists.
      const key = entry.fieldName ?? entry.label ?? entry.name ?? entry.key ?? entry.title;
      const val = entry.value ?? entry.answer ?? entry.fieldValue;
      if (key != null && val != null && typeof val !== 'object') {
        bag[String(key).toLowerCase().trim()] = val;
      } else {
        collect(entry, depth + 1);
      }
    }
    return;
  }
  for (const [k, v] of Object.entries(obj)) {
    if (v === null || v === undefined) continue;
    if (typeof v === 'object') collect(v, depth + 1);
    else bag[String(k).toLowerCase().trim()] = v;
  }
};
collect(start, 0);

const pick = (...names) => {
  for (const n of names) {
    const v = bag[n];
    if (v !== undefined && String(v).trim() !== '') return String(v).trim();
  }
  return '';
};

// ---- name -------------------------------------------------------------
let first = pick('first_name', 'firstname', 'first', 'given_name', 'fname');
let last  = pick('last_name', 'lastname', 'last', 'surname', 'family_name', 'lname');

if (!first) {
  const full = pick('name', 'full_name', 'fullname', 'your_name', 'contact_name', 'client_name');
  if (full) {
    const parts = full.split(/\s+/).filter(Boolean);
    first = parts.shift() ?? '';
    // A single-token name leaves lastName empty on purpose: the agent is told
    // to ask for a spelling only when the variable comes through empty.
    if (!last) last = parts.join(' ');
  }
}

// ---- phone ------------------------------------------------------------
const toE164 = (value) => {
  let digits = String(value || '').replace(/[^\d+]/g, '');
  if (digits.startsWith('+')) return '+' + digits.slice(1).replace(/\D/g, '');
  digits = digits.replace(/\D/g, '');
  if (digits.length === 10) return '+1' + digits;
  if (digits.length === 11 && digits.startsWith('1')) return '+' + digits;
  if (digits.length > 11) return '+' + digits;
  return '';
};

const rawPhone = pick('phone', 'phone_number', 'phonenumber', 'mobile', 'tel',
                      'telephone', 'cell', 'contact_number');
const e164 = toE164(rawPhone);

// Retell only dials US destinations from a Retell-purchased number.
const phoneValid = /^\+1\d{10}$/.test(e164);

// ---- submitted at -----------------------------------------------------
const submittedRaw = pick('submitted_at', 'submittedat', 'created_at', 'createdat', 'timestamp', 'date');
const when = submittedRaw ? new Date(submittedRaw) : new Date();
const submittedAt = isNaN(when.getTime())
  ? ''
  : when.toLocaleString('en-US', {
      timeZone: 'America/Los_Angeles',
      weekday: 'long', month: 'long', day: 'numeric',
      hour: 'numeric', minute: '2-digit',
    });

// ---- where this lead came from ----------------------------------------
// "website_form" (default) - they filled out the booking form.
// "missed_call"            - the inbound post-call automation saw an
//                            incomplete call and wants Aria to ring back.
const source = pick('source', 'lead_source') === 'missed_call' ? 'missed_call' : 'website_form';
const inboundIntent = pick('inbound_intent');
const inboundCallId = pick('inbound_call_id');

// ---- which outbound version to dial -----------------------------------
// Real leads never send this, and get the PUBLISHED version - exactly what the
// inbound number does. A test payload (the dialer page, a curl) may ask for:
//   "latest"           - the current draft
//   "latest_published" - the same as sending nothing
//   a version number   - one specific version, e.g. 3 or "3"
// Anything else falls back to latest_published, so a typo can never select
// an arbitrary version or reach the draft by accident.
const versionRaw = String(bag['agent_version'] ?? '').trim().toLowerCase();
const agentVersion = versionRaw === 'latest' ? 'latest'
  : /^\d{1,4}$/.test(versionRaw) ? Number(versionRaw)
  : 'latest_published';

// ---- testing guard ----------------------------------------------------
// While TEST_MODE is on, only numbers in ALLOWED_NUMBERS may be dialled.
const testMode = cfg.TEST_MODE === true || cfg.TEST_MODE === 'true';
// Comma / semicolon / newline separated, any formatting - "(628) 682-8010" is fine.
const allowList = String(cfg.ALLOWED_NUMBERS || '')
  .split(/[,;\n]+/)
  .map(toE164)
  .filter(Boolean);
const allowed = !testMode || allowList.includes(e164);

const errors = [];
if (!phoneValid) errors.push(`unusable phone: ${JSON.stringify(rawPhone)}`);
// A missed inbound call often has no name - the agent handles an empty one.
if (!first && source === 'website_form') errors.push('missing name');

return [{
  json: {
    valid: errors.length === 0,
    errors,
    dryRun: bag['dryrun'] === true || bag['dryrun'] === 'true',
    allowed,
    test_mode: testMode,
    blocked_reason: allowed ? '' : 'test_mode_allowlist',
    to_number: e164,
    // Retell requires every dynamic variable to be a string.
    lead_first_name: first,
    lead_last_name: last,
    lead_phone: e164,
    lead_submitted_at: submittedAt,
    // "yes" only when BOTH names are present. The agent's name gate keys off this
    // string - Retell's `exists` treats an empty string as existing.
    lead_name_known: first && last ? 'yes' : 'no',
    lead_source: source,
    inbound_intent: inboundIntent,
    inbound_call_id: inboundCallId,
    agent_version: agentVersion,
  },
}];
"""


def node(id_, name, type_, tv, pos, params, **extra):
    n = {"id": id_, "name": name, "type": type_, "typeVersion": tv,
         "position": pos, "parameters": params}
    n.update(extra)
    return n


def build() -> dict:
    nodes = [
        node("wh-lead", "Webhook - Website Lead Form", "n8n-nodes-base.webhook", 2,
             [-460, 300],
             {"httpMethod": "POST", "path": WEBHOOK_PATH,
              "responseMode": "responseNode", "options": {}},
             webhookId="sage-willow-lead-callout-v1"),

        # Editable in the n8n UI. TEST_MODE=false lifts the allowlist.
        node("config", "CONFIG - Test Mode Allowlist", "n8n-nodes-base.set", 3.4,
             [-350, 300],
             {"assignments": {"assignments": [
                 {"id": "cfg-test-mode", "name": "TEST_MODE",
                  "value": TEST_MODE, "type": "boolean"},
                 {"id": "cfg-allow", "name": "ALLOWED_NUMBERS",
                  "value": ", ".join(ALLOWED_NUMBERS), "type": "string"},
             ]},
              "includeOtherFields": False,
              "options": {}}),

        node("normalize", "Normalize Lead", "n8n-nodes-base.code", 2,
             [-240, 300],
             {"jsCode": NORMALIZE_CODE}),

        node("if-valid", "IF: Lead Valid?", "n8n-nodes-base.if", 2,
             [-20, 300],
             {"conditions": {
                 "options": {"caseSensitive": True, "leftValue": "",
                             "typeValidation": "strict", "version": 2},
                 "conditions": [{
                     "id": "c-valid",
                     "operator": {"type": "boolean", "operation": "true", "singleValue": True},
                     "leftValue": "={{ $json.valid }}", "rightValue": ""}],
                 "combinator": "and"},
              "options": {}}),

        node("if-dry", "IF: Dry Run?", "n8n-nodes-base.if", 2,
             [200, 200],
             {"conditions": {
                 "options": {"caseSensitive": True, "leftValue": "",
                             "typeValidation": "strict", "version": 2},
                 "conditions": [{
                     "id": "c-dry",
                     "operator": {"type": "boolean", "operation": "true", "singleValue": True},
                     "leftValue": "={{ $json.dryRun }}", "rightValue": ""}],
                 "combinator": "and"},
              "options": {}}),

        node("if-allowed", "IF: Allowed Number?", "n8n-nodes-base.if", 2,
             [420, 280],
             {"conditions": {
                 "options": {"caseSensitive": True, "leftValue": "",
                             "typeValidation": "strict", "version": 2},
                 "conditions": [{
                     "id": "c-allowed",
                     "operator": {"type": "boolean", "operation": "true", "singleValue": True},
                     "leftValue": "={{ $json.allowed }}", "rightValue": ""}],
                 "combinator": "and"},
              "options": {}}),

        node("retell-call", "Retell: Create Phone Call", "n8n-nodes-base.httpRequest", 4.2,
             [640, 280],
             {"method": "POST",
              "url": "https://api.retellai.com/v2/create-phone-call",
              "authentication": "genericCredentialType",
              "genericAuthType": "httpBearerAuth",
              "sendBody": True,
              "specifyBody": "json",
              "jsonBody": (
                  "={{ JSON.stringify({\n"
                  f"  from_number: '{RETELL_FROM_NUMBER}',\n"
                  "  to_number: $json.to_number,\n"
                  f"  override_agent_id: '{OUTBOUND_AGENT_ID}',\n"
                  "  // LIVE since 2026-09-19: real leads dial the most recently PUBLISHED\n"
                  "  // version, exactly as the inbound number does. Draft edits never reach a\n"
                  "  // lead until someone publishes them. \"Normalize Lead\" resolves\n"
                  "  // agent_version ('latest' / 'latest_published' / a number) and only a\n"
                  "  // test payload can move it off latest_published.\n"
                  "  override_agent_version: typeof $json.agent_version === 'number' ? $json.agent_version : ($json.agent_version || 'latest_published'),\n"
                  "  retell_llm_dynamic_variables: {\n"
                  "    lead_first_name: $json.lead_first_name,\n"
                  "    lead_last_name: $json.lead_last_name,\n"
                  "    lead_phone: $json.lead_phone,\n"
                  "    lead_submitted_at: $json.lead_submitted_at,\n"
                  "    lead_name_known: $json.lead_name_known,\n"
                  "    lead_source: $json.lead_source,\n"
                  "    inbound_intent: $json.inbound_intent\n"
                  "  },\n"
                  "  metadata: { source: $json.lead_source, inbound_call_id: $json.inbound_call_id }\n"
                  "}) }}"),
              "options": {}},
             credentials={"httpBearerAuth": RETELL_BEARER_CRED},
             onError="continueErrorOutput"),

        node("resp-blocked", "Respond: Blocked (Test Mode)", "n8n-nodes-base.respondToWebhook", 1.1,
             [640, 480],
             {"respondWith": "json",
              "responseBody": (
                  "={{ JSON.stringify({ ok: false, skipped: $json.blocked_reason, "
                  "to: $json.to_number, source: $json.lead_source }) }}"),
              "options": {}}),

        node("resp-queued", "Respond: Call Queued", "n8n-nodes-base.respondToWebhook", 1.1,
             [860, 180],
             {"respondWith": "json",
              "responseBody": "={{ JSON.stringify({ ok: true, call_id: $json.call_id, to: $json.to_number, agent_version: $json.agent_version }) }}",
              "options": {}}),

        node("resp-dry", "Respond: Dry Run", "n8n-nodes-base.respondToWebhook", 1.1,
             [640, 60],
             {"respondWith": "json",
              "responseBody": "={{ JSON.stringify({ ok: true, dryRun: true, wouldCall: $json }) }}",
              "options": {}}),

        node("resp-invalid", "Respond: Invalid Lead", "n8n-nodes-base.respondToWebhook", 1.1,
             [200, 440],
             {"respondWith": "json",
              "responseCode": 400,
              "responseBody": "={{ JSON.stringify({ ok: false, errors: $json.errors }) }}",
              "options": {}}),

        node("resp-error", "Respond: Retell Error", "n8n-nodes-base.respondToWebhook", 1.1,
             [860, 400],
             {"respondWith": "json",
              "responseCode": 502,
              "responseBody": "={{ JSON.stringify({ ok: false, error: 'retell_create_call_failed', detail: $json }) }}",
              "options": {}}),
    ]

    def link(src, outputs):
        return {src: {"main": [[{"node": d, "type": "main", "index": 0} for d in outs]
                               for outs in outputs]}}

    connections = {}
    connections.update(link("Webhook - Website Lead Form", [["CONFIG - Test Mode Allowlist"]]))
    connections.update(link("CONFIG - Test Mode Allowlist", [["Normalize Lead"]]))
    connections.update(link("Normalize Lead", [["IF: Lead Valid?"]]))
    connections.update(link("IF: Lead Valid?", [["IF: Dry Run?"], ["Respond: Invalid Lead"]]))
    connections.update(link("IF: Dry Run?", [["Respond: Dry Run"], ["IF: Allowed Number?"]]))
    connections.update(link("IF: Allowed Number?",
                            [["Retell: Create Phone Call"], ["Respond: Blocked (Test Mode)"]]))
    connections.update(link("Retell: Create Phone Call",
                            [["Respond: Call Queued"], ["Respond: Retell Error"]]))

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


if __name__ == "__main__":
    main()
