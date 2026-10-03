"""
Two-person bookings + request-first services on a Retell <-> Wix booking workflow.

Run:  py -X utf8 Sage_Willow_Spa/n8n-workflow/_patch_pair_booking_and_approval.py <workflow_id> [--dry-run]

    DEV   yfbpUaEzZQghelh3  (/webhook/retell-wix-outbound, TEST Wix site)
    PROD  s5dWZOMRl0X7PV65  (/webhook/retell-wix, Nicky's real calendar) - only at go-live

What Nicky confirmed (2026-09-27):
  * Two people at once -> two appointments side by side, each with their own
    therapist, only at times when two therapists are available together. Each
    guest may pick their own massage and length. Nothing lines up -> Aria takes
    a request for a callback; no back-to-back appointments.
  * A service set to "request first" in Wix (today: Couples Massage) comes to
    her for approval instead of being booked straight away.

Changes
  1. get-slots with guests: 2          -> "Pair: Slots For Two" (pair_slots.js)
     book-appointment with guest names -> "Pair: Book Two Guests" (pair_book.js)
     Both call this same webhook for the ordinary one-person steps, so every Wix
     detail stays in the chains that are already proven. The one-person path is
     untouched: an IF in front of each chain only diverts two-guest requests.
  2. Resolve: Service (Booking) carries requireManualApproval from the live
     service (Wix onlineBooking.requireManualApproval).
  3. Wix: Confirm Booking calls "Confirm or Decline Booking" for those services
     (status PENDING, waiting for Nicky) and the old "Confirm Booking" (which
     approves on her behalf) for everything else - unchanged for them.
  4. Format: Booking Confirmation reports PENDING as a request and DECLINED
     (slot double-booked meanwhile) as a failure.
  5. Format: Services Response marks request-first services "byRequest": true.
"""

from __future__ import annotations
import argparse
import json
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parents[1]
KNOWN = {"yfbpUaEzZQghelh3": "DEV", "s5dWZOMRl0X7PV65": "PROD"}

PAIR_SLOTS = (HERE / "pair_slots.js").read_text(encoding="utf-8")
PAIR_BOOK = (HERE / "pair_book.js").read_text(encoding="utf-8")

# ---- 2. requireManualApproval on the service resolution -----------------------------------------
OLD_SERVICE_RETURN = """args.serviceId = finalId;
args.serviceName = (resolved || idEntry).name;

return [{ json: Object.assign({}, prev, { args, _serviceResolution: {
    serviceId: finalId, serviceName: args.serviceName, source: source, how: how,
    sentServiceId: sentId, sentServiceIdValid: idValid, mismatch: mismatch } }) }];"""
NEW_SERVICE_RETURN = """args.serviceId = finalId;
args.serviceName = (resolved || idEntry).name;

// "Request first" in Wix (Couples Massage since 2026-09-25): the booking must
// wait for the owner's approval - see "Wix: Confirm Booking".
const finalRaw = services.find(s => s && s.id === finalId) || {};
const requireManualApproval = !!(finalRaw.onlineBooking && finalRaw.onlineBooking.requireManualApproval === true);

return [{ json: Object.assign({}, prev, { args, _serviceResolution: {
    serviceId: finalId, serviceName: args.serviceName, source: source, how: how,
    sentServiceId: sentId, sentServiceIdValid: idValid, mismatch: mismatch,
    requireManualApproval } }) }];"""

# ---- 3. confirm: approve only what does not need the owner -----------------------------------------
OLD_CONFIRM_URL = "=https://www.wixapis.com/bookings/v2/bookings/{{ $json.booking.id }}/confirm"
OLD_CONFIRM_BODY = ('={\n  "participantNotification": {\n    "notifyParticipants": true\n  },\n'
                    '  "revision": {{ $json.booking.revision }}\n}')
APPROVAL = "$('IF: Booking Args Valid').item.json._serviceResolution?.requireManualApproval === true"
NEW_CONFIRM_URL = ("={{ " + APPROVAL + " ? 'https://www.wixapis.com/bookings/v2/confirmation/' + $json.booking.id + "
                   "':confirmOrDecline' : 'https://www.wixapis.com/bookings/v2/bookings/' + $json.booking.id + '/confirm' }}")
# The non-approval body is byte-for-byte what the node sent before.
NEW_CONFIRM_BODY = ("={{ " + APPROVAL + " ? '{\"paymentStatus\": \"NOT_PAID\"}' : "
                    "'{\\n  \"participantNotification\": {\\n    \"notifyParticipants\": true\\n  },\\n  \"revision\": ' "
                    "+ $json.booking.revision + '\\n}' }}")

# ---- 4. the booking result ---------------------------------------------------------------------------
OLD_FORMAT_HEAD = "const confirmData = $input.first().json;\n// Fallback to the create booking data if confirm had issues"
NEW_FORMAT = """const confirmData = $input.first().json;
// Fallback to the create booking data if confirm had issues
const createData = $('Wix: Create Booking').first().json;

const booking = confirmData.booking || createData.booking || {};
const status = booking.status || '';

if (!booking.id) {
  return [{ json: { success: false, error: confirmData.message || 'Booking confirmation failed' } }];
}

// Confirm or Decline Booking (request-first services) declines when the slot was
// double-booked in the meantime - that is a failed booking, not a request.
if (status === 'DECLINED') {
  return [{ json: { success: false, bookingId: booking.id, status,
    error: 'That time was just taken, so it could not be booked. Call get_slots again and offer the caller another time.' } }];
}

// PENDING = a service set to "request first" in Wix: the owner still has to approve it.
const pending = status === 'PENDING';
const who = `${booking.contactDetails?.firstName} ${booking.contactDetails?.lastName}`;
const when = booking.bookedEntity?.slot?.startDate;

return [{ json: {
  success: true,
  confirmed: status === 'CONFIRMED',
  bookingId: booking.id,
  status,
  ...(pending ? { requested: true,
    note: 'This massage is booked by request - the spa has to approve it before it is confirmed. Tell the caller it is a request and the team will confirm it with them. Never say "you\\'re all set".' } : {}),
  serviceId: booking.bookedEntity?.slot?.serviceId,
  contact: {
    firstName: booking.contactDetails?.firstName,
    lastName: booking.contactDetails?.lastName,
    phone: booking.contactDetails?.phone
  },
  message: pending ? `Request sent for ${who} on ${when} - waiting for the spa to approve it` : `Appointment booked for ${who} on ${when}`
} }];"""

# ---- 5. byRequest on get_services --------------------------------------------------------------------
OLD_SVC_MAP = """  return {
    id: s.id,
    name: s.name,
    description: s.description,"""
NEW_SVC_MAP = """  return {
    id: s.id,
    name: s.name,
    // Set to "request first" in Wix: a booking goes to the spa for approval.
    byRequest: s.onlineBooking?.requireManualApproval === true ? true : undefined,
    description: s.description,"""
OLD_SVC_CATALOG = "return { id: s.id, name: s.name, description: oneLine(s.description), pricing: priceSummary(s) };"
NEW_SVC_CATALOG = ("return { id: s.id, name: s.name, description: oneLine(s.description), pricing: priceSummary(s),\n"
                   "      ...(s.byRequest ? { byRequest: true } : {}) };")

NEW_NODE_NAMES = ["IF: Two Guests? (Slots)", "Pair: Slots For Two", "Respond: Pair Slots",
                  "IF: Two Guests? (Booking)", "Pair: Book Two Guests", "Respond: Pair Booking"]


def n8n_env() -> tuple[str, dict]:
    raw = (REPO / ".mcp.json").read_text(encoding="utf-8")
    env = json.loads(raw[raw.index("{"):])["mcpServers"]["n8n-mcp-aiemply"]["env"]
    return env["N8N_API_URL"].rstrip("/"), {"X-N8N-API-KEY": env["N8N_API_KEY"], "User-Agent": "curl/8.0",
                                            "Accept": "application/json", "Content-Type": "application/json"}


def call(method: str, path: str, body: dict | None = None) -> dict:
    base, hdr = n8n_env()
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method, headers=hdr)
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path} -> {e.code}: {e.read().decode()[:400]}")


def once(text: str, old: str, new: str, where: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"{where}: expected one match for {old[:60]!r}, found {text.count(old)}")
    return text.replace(old, new)


def if_node(name: str, expr: str, pos: list[int]) -> dict:
    return {"parameters": {"conditions": {"boolean": [{"value1": expr, "value2": True}]}},
            "name": name, "type": "n8n-nodes-base.if", "typeVersion": 1, "position": pos}


def code_node(name: str, code: str, pos: list[int]) -> dict:
    return {"parameters": {"jsCode": code}, "name": name, "type": "n8n-nodes-base.code", "typeVersion": 2,
            "position": pos, "onError": "continueRegularOutput"}


def respond_node(name: str, pos: list[int]) -> dict:
    return {"parameters": {"respondWith": "json", "responseBody": "={{ $json }}", "options": {}},
            "name": name, "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1, "position": pos}


def patch(wf: dict) -> dict:
    wf = json.loads(json.dumps(wf))
    n = {x["name"]: x for x in wf["nodes"]}
    if set(NEW_NODE_NAMES) & set(n):
        raise SystemExit("already patched - the two-guest nodes exist")

    path = n["Webhook — Retell Tool Call"]["parameters"]["path"]
    self_url = f"https://automation.aiemply.com/webhook/{path}"

    p = n["Resolve: Service (Booking)"]["parameters"]
    p["jsCode"] = once(p["jsCode"], OLD_SERVICE_RETURN, NEW_SERVICE_RETURN, "Resolve: Service (Booking)")

    p = n["Wix: Confirm Booking"]["parameters"]
    if p.get("url") != OLD_CONFIRM_URL or p.get("jsonBody") != OLD_CONFIRM_BODY:
        raise SystemExit("Wix: Confirm Booking changed shape - merge by hand")
    p["url"], p["jsonBody"] = NEW_CONFIRM_URL, NEW_CONFIRM_BODY

    p = n["Format: Booking Confirmation"]["parameters"]
    if not p["jsCode"].startswith(OLD_FORMAT_HEAD) or "PENDING" in p["jsCode"]:
        raise SystemExit("Format: Booking Confirmation changed shape - merge by hand")
    p["jsCode"] = NEW_FORMAT

    p = n["Format: Services Response"]["parameters"]
    p["jsCode"] = once(p["jsCode"], OLD_SVC_MAP, NEW_SVC_MAP, "Format: Services Response (map)")
    p["jsCode"] = once(p["jsCode"], OLD_SVC_CATALOG, NEW_SVC_CATALOG, "Format: Services Response (catalog)")

    # ---- two-guest branches in front of the one-person chains ------------------------------------------
    route = wf["connections"]["Route by Tool"]["main"]
    if [o[0]["node"] for o in route[:4]] != ["Wix: Query Services", "Validate: Slots Args",
                                             "Wix: Query Staff Members", "Validate: Booking Args"]:
        raise SystemExit("Route by Tool outputs changed - merge by hand")
    vs, vb = n["Validate: Slots Args"]["position"], n["Validate: Booking Args"]["position"]
    wf["nodes"] += [
        if_node("IF: Two Guests? (Slots)", "={{ Number($json.args && $json.args.guests) === 2 }}", [vs[0] - 220, vs[1] - 200]),
        code_node("Pair: Slots For Two", PAIR_SLOTS.replace("__SELF_URL__", self_url), [vs[0], vs[1] - 380]),
        respond_node("Respond: Pair Slots", [vs[0] + 220, vs[1] - 380]),
        if_node("IF: Two Guests? (Booking)",
                "={{ !!($json.args && ($json.args.guestFirstName || $json.args.guestLastName)) }}", [vb[0] - 220, vb[1] - 200]),
        code_node("Pair: Book Two Guests", PAIR_BOOK.replace("__SELF_URL__", self_url), [vb[0], vb[1] - 380]),
        respond_node("Respond: Pair Booking", [vb[0] + 220, vb[1] - 380]),
    ]
    link = lambda node: [{"node": node, "type": "main", "index": 0}]
    route[1] = link("IF: Two Guests? (Slots)")
    route[3] = link("IF: Two Guests? (Booking)")
    c = wf["connections"]
    c["IF: Two Guests? (Slots)"] = {"main": [link("Pair: Slots For Two"), link("Validate: Slots Args")]}
    c["Pair: Slots For Two"] = {"main": [link("Respond: Pair Slots")]}
    c["IF: Two Guests? (Booking)"] = {"main": [link("Pair: Book Two Guests"), link("Validate: Booking Args")]}
    c["Pair: Book Two Guests"] = {"main": [link("Respond: Pair Booking")]}

    names = [x["name"] for x in wf["nodes"]]
    assert len(names) == len(set(names))
    for src, conns in c.items():
        assert src in names, src
        for outs in conns["main"]:
            for o in outs or []:
                assert o["node"] in names, f"{src} -> {o['node']}"
    if "__SELF_URL__" in json.dumps(wf):
        raise SystemExit("self URL placeholder left in a node")
    return wf


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("workflow_id")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    label = KNOWN.get(a.workflow_id, "UNKNOWN")
    wf = call("GET", f"/api/v1/workflows/{a.workflow_id}")
    print(f"{label}: {wf['name']} - {len(wf['nodes'])} nodes, active={wf.get('active')}")
    out = patch(wf)
    print(f"  staged: {len(out['nodes'])} nodes (+{len(out['nodes']) - len(wf['nodes'])}); "
          f"self URL {out and [x for x in out['nodes'] if x['name'] == 'Webhook — Retell Tool Call'][0]['parameters']['path']}")
    if a.dry_run:
        print("Dry run - n8n not modified.")
        return
    backup = Path(tempfile.gettempdir()) / f"n8n_{a.workflow_id}_before-pair.json"
    backup.write_text(json.dumps(wf, indent=1, ensure_ascii=False), encoding="utf-8")
    put = {"name": wf["name"], "nodes": out["nodes"], "connections": out["connections"],
           "settings": {k: v for k, v in (wf.get("settings") or {}).items() if k in (
               "executionOrder", "timezone", "saveDataErrorExecution", "saveDataSuccessExecution",
               "saveManualExecutions", "saveExecutionProgress", "errorWorkflow", "callerPolicy")}}
    if "staticData" in wf:
        put["staticData"] = wf["staticData"]
    back = call("PUT", f"/api/v1/workflows/{a.workflow_id}", put)
    bn = {x["name"]: x for x in back["nodes"]}
    assert all(k in bn for k in NEW_NODE_NAMES)
    assert bn["Wix: Confirm Booking"]["parameters"]["url"] == NEW_CONFIRM_URL
    assert back["connections"]["Route by Tool"]["main"][1][0]["node"] == "IF: Two Guests? (Slots)"
    strip = lambda x: {k: v for k, v in x.items() if k not in ("position", "webhookId")}
    changed = {"Resolve: Service (Booking)", "Wix: Confirm Booking", "Format: Booking Confirmation", "Format: Services Response"}
    for x in wf["nodes"]:
        if x["name"] not in changed:
            assert strip(bn[x["name"]]) == strip(x), f"untouched node changed: {x['name']}"
    print(f"PATCHED {label}: {len(back['nodes'])} nodes, active={back.get('active')} (backup {backup})")


if __name__ == "__main__":
    main()
