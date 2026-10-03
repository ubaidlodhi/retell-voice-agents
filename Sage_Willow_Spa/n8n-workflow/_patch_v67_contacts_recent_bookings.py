"""
V67 backend - every contact on the number, and the last day's appointments.

Run:  py -X utf8 Sage_Willow_Spa/n8n-workflow/_patch_v67_contacts_recent_bookings.py <workflow_id> [--dry-run]

Evidence: the 808-292-4255 caller (2026-09-29, PROD exec 2134). Wix holds two
contacts on that number - "aln peters" (older, one past booking) and "al" (newer,
the booking for the next day). The lookup read only the first contact, found
nothing upcoming, and Aria told the caller she had no appointment. Wahaj fixed
get_booking on PROD by hand (all contacts, 2026-09-30 02:33Z); cancel and
reschedule still read only the first contact.

Changes
  get_booking
    Search Contact                 - up to 50 contacts (Wahaj's PROD edit; brings DEV level)
    Wix: Get Booking (by Contact)  - bookings of ALL those contacts, starting from 24 hours
                                     ago, soonest first, up to 100 (was: newest-created 5,
                                     past ones included - a regular's upcoming booking could
                                     fall off the list)
    Format: Get Booking Response   - get_booking_format.js: upcoming first, then the ones
                                     that started in the last 24 hours, marked
                                     timing "already happened" (Ubaid, 2026-10-01)
  cancel_booking / reschedule_booking
    Resolve: Contact (...)         - up to 50 contacts
    Resolve: Bookings (...)        - bookings of all of them, up to 100
    Resolve: Booking Id (...)      - also notes whether the matched booking has started
    IF: Not Started Yet? (...)     - new; a booking that has started is never cancelled or
    Respond: ... Already Happened    moved - Aria gets a plain "that already happened" instead
Pinned data on the workflow is carried over untouched.
"""

from __future__ import annotations
import argparse
import json
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parents[1]
KNOWN = {"yfbpUaEzZQghelh3": "DEV", "s5dWZOMRl0X7PV65": "PROD"}
FORMAT_JS = HERE / "get_booking_format.js"

GET_BOOKING_BODY = """={
  "query": {
    "filter": {
      "contactDetails.contactId": { "$in": {{ JSON.stringify($json.contacts.map(c => c.id)) }} },
      "status": { "$in": ["CONFIRMED", "PENDING_APPROVAL", "CREATED", "PENDING"] },
      "startDate": { "$gte": "{{ new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString() }}" }
    },
    "sort": [{ "fieldName": "startDate", "order": "ASC" }],
    "paging": { "limit": 100 }
  }
}"""

OLD_IDS = """"contactDetails.contactId": { "$in": ["{{ ($json.contacts && $json.contacts[0] && $json.contacts[0].id) || '00000000-0000-0000-0000-000000000000' }}"] },"""
NEW_IDS = """"contactDetails.contactId": { "$in": {{ JSON.stringify(($json.contacts || []).map(c => c.id).filter(Boolean).length ? $json.contacts.map(c => c.id).filter(Boolean) : ['00000000-0000-0000-0000-000000000000']) }} },"""

OLD_CANDIDATES = "  .map(b => ({ id: String(b.id || ''), revision: b.revision }))"
NEW_CANDIDATES = ("  .map(b => ({ id: String(b.id || ''), revision: b.revision,\n"
                  "    start: (b.bookedEntity && b.bookedEntity.slot && b.bookedEntity.slot.startDate) || b.startDate || null }))")
OLD_RETURN = "return [{ json: { ...orig, args, _resolution: how, _claimedBookingId: claimed } }];"
NEW_RETURN = """// V67: get_booking also lists the last day's appointments now. One that has
// started is over - cancelling or moving it would erase a visit (or a no-show)
// from the books, so "IF: Not Started Yet?" stops it.
const startMs = hit.start ? Date.parse(hit.start) : NaN;
const alreadyStarted = isFinite(startMs) && startMs <= Date.now();
const startedAt = alreadyStarted ? new Date(startMs).toLocaleString('en-US', { timeZone: 'America/Los_Angeles',
  weekday: 'long', month: 'long', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : null;

return [{ json: { ...orig, args, _resolution: how, _claimedBookingId: claimed,
  _alreadyStarted: alreadyStarted, _startedAt: startedAt } }];"""

PAST_MSG = (" - that appointment already happened (it started ' + $json._startedAt + '). "
            "A past appointment cannot be cancelled or moved. Tell the caller plainly, and offer to book "
            "a new appointment or have the team call them back.'")
PATHS = {
    "Cancel": {"resolver": "Resolve: Booking Id (Cancel)", "wix": "Wix: Cancel Booking",
               "body": "={{ { success: false, cancelFlag: 'no', alreadyHappened: true, error: 'Nothing was cancelled" + PAST_MSG + " } }}"},
    "Reschedule": {"resolver": "Resolve: Booking Id (Reschedule)", "wix": "Wix: Reschedule Booking",
                   "body": "={{ { success: false, rescheduleFlag: 'no', alreadyHappened: true, error: 'Nothing was moved" + PAST_MSG + " } }}"},
}


def call(method, path, body=None):
    raw = (REPO / ".mcp.json").read_text(encoding="utf-8")
    env = json.loads(raw[raw.index("{"):])["mcpServers"]["n8n-mcp-aiemply"]["env"]
    hdr = {"X-N8N-API-KEY": env["N8N_API_KEY"], "User-Agent": "curl/8.0",
           "Accept": "application/json", "Content-Type": "application/json"}
    req = urllib.request.Request(env["N8N_API_URL"].rstrip("/") + path, method=method, headers=hdr,
                                 data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path} -> {e.code}: {e.read().decode()[:400]}")


def swap(node, key, old, new, done, label):
    """Replace old with new in node.parameters[key]; fine if already new, abort if neither."""
    cur = node["parameters"][key]
    if new in cur:
        return
    if old not in cur:
        raise SystemExit(f'"{node["name"]}" does not look as expected ({label}) - merge by hand')
    node["parameters"][key] = cur.replace(old, new, 1)
    done.append(f"{node['name']}: {label}")


def patch(wf: dict) -> tuple[dict, list[str]]:
    wf = json.loads(json.dumps(wf))
    n = {x["name"]: x for x in wf["nodes"]}
    c = wf["connections"]
    done: list[str] = []

    # ---- get_booking ------------------------------------------------------------------
    swap(n["Search Contact"], "jsonBody", '"paging": {\n      "limit": 1\n    }',
         '"paging": {\n      "limit": 50\n    }', done, "50 contacts")
    gb = n["Wix: Get Booking (by Contact)"]["parameters"]
    if gb["jsonBody"] != GET_BOOKING_BODY:
        if "contactDetails.contactId" not in gb["jsonBody"] or '"limit": 5 }' not in gb["jsonBody"]:
            raise SystemExit('"Wix: Get Booking (by Contact)" does not look as expected - merge by hand')
        gb["jsonBody"] = GET_BOOKING_BODY
        done.append("Wix: Get Booking (by Contact): all contacts, from 24h ago, soonest first")
    code = FORMAT_JS.read_text(encoding="utf-8")
    fmt = n["Format: Get Booking Response"]["parameters"]
    if fmt["jsCode"] != code:
        if "No upcoming bookings found for this customer" not in fmt["jsCode"]:
            raise SystemExit('"Format: Get Booking Response" does not look as expected - merge by hand')
        fmt["jsCode"] = code
        done.append("Format: Get Booking Response: upcoming + last 24h")

    # ---- cancel / reschedule ----------------------------------------------------------
    for kind, p in PATHS.items():
        swap(n[f"Resolve: Contact ({kind})"], "jsonBody", '"paging": { "limit": 1 }',
             '"paging": { "limit": 50 }', done, "50 contacts")
        swap(n[f"Resolve: Bookings ({kind})"], "jsonBody", OLD_IDS, NEW_IDS, done, "all contacts")
        swap(n[f"Resolve: Bookings ({kind})"], "jsonBody", '"paging": { "limit": 20 }',
             '"paging": { "limit": 100 }', done, "100 bookings")
        swap(n[p["resolver"]], "jsCode", OLD_CANDIDATES, NEW_CANDIDATES, done, "keep start time")
        swap(n[p["resolver"]], "jsCode", OLD_RETURN, NEW_RETURN, done, "flag started booking")

        gate, stop = f"IF: Not Started Yet? ({kind})", f"Respond: {kind} Already Happened"
        if gate not in n:
            if c[p["resolver"]]["main"][0] != [{"node": p["wix"], "type": "main", "index": 0}]:
                raise SystemExit(f'"{p["resolver"]}" no longer feeds "{p["wix"]}" directly - merge by hand')
            x, y = n[p["wix"]]["position"]
            wf["nodes"] += [
                {"name": gate, "type": "n8n-nodes-base.if", "typeVersion": 1, "position": [x - 110, y - 200],
                 "parameters": {"conditions": {"boolean": [
                     {"value1": "={{ $json._alreadyStarted !== true }}", "value2": True}]}}},
                {"name": stop, "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1,
                 "position": [x + 110, y - 200],
                 "parameters": {"respondWith": "json", "responseBody": p["body"], "options": {}}},
            ]
            link = lambda node: [{"node": node, "type": "main", "index": 0}]
            c[p["resolver"]]["main"][0] = link(gate)
            c[gate] = {"main": [link(p["wix"]), link(stop)]}
            done.append(f"{gate} + {stop} added")

    names = [x["name"] for x in wf["nodes"]]
    assert len(names) == len(set(names))
    for src, conns in wf["connections"].items():
        assert src in names, src
        for outs in conns["main"]:
            for o in outs or []:
                assert o["node"] in names, f"{src} -> {o['node']}"
    return wf, done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workflow_id")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    label = KNOWN.get(a.workflow_id, "UNKNOWN")
    wf = call("GET", f"/api/v1/workflows/{a.workflow_id}")
    out, done = patch(wf)
    print(f"{label}: {wf['name']} - {len(wf['nodes'])} -> {len(out['nodes'])} nodes")
    for d in done or ["nothing to do"]:
        print("  " + d)
    if a.dry_run or not done:
        print("Dry run - n8n not modified." if a.dry_run else "Already up to date.")
        return
    backup = Path(tempfile.gettempdir()) / f"n8n_{a.workflow_id}_before-v67.json"
    backup.write_text(json.dumps(wf, indent=1, ensure_ascii=False), encoding="utf-8")
    put = {"name": wf["name"], "nodes": out["nodes"], "connections": out["connections"],
           "settings": {k: v for k, v in (wf.get("settings") or {}).items() if k in (
               "executionOrder", "timezone", "saveDataErrorExecution", "saveDataSuccessExecution",
               "saveManualExecutions", "saveExecutionProgress", "errorWorkflow", "callerPolicy")}}
    if "staticData" in wf:
        put["staticData"] = wf["staticData"]
    back = call("PUT", f"/api/v1/workflows/{a.workflow_id}", put)
    want = {x["name"]: x["parameters"] for x in out["nodes"]}
    for x in back["nodes"]:
        assert x["parameters"] == want[x["name"]], f"not saved as sent: {x['name']}"
    after = call("GET", f"/api/v1/workflows/{a.workflow_id}")
    pins_before, pins_after = sorted((wf.get("pinData") or {}).keys()), sorted((after.get("pinData") or {}).keys())
    print(f"PATCHED {label}: {len(back['nodes'])} nodes, active={back.get('active')} (backup {backup})")
    print(f"  pinned nodes before {len(pins_before)}, after {len(pins_after)}"
          + ("" if pins_before == pins_after else "  <- pins changed"))


if __name__ == "__main__":
    main()
