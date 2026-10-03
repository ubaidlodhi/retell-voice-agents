"""
V66 backend - confirm retry on a stale revision, and the latest two-guest code.

Run:  py -X utf8 Sage_Willow_Spa/n8n-workflow/_patch_v66_confirm_retry.py <workflow_id> [--dry-run]
      (PROD at go-live: run _patch_pair_booking_and_approval.py first, then this.)

Evidence: web test call_c754d384c5a80d556a19d41931b (2026-09-28, DEV exec 2090). The
guest's booking was CREATED, then "Wix: Confirm Booking" failed with
    "Outdated revision for entity id"
- Wix had updated the new booking (revision 1 -> 2) in the moment between create and
confirm, and the confirm sent the revision from the create response. Its three
retries resent the same stale revision. Nothing about this is specific to two guests:
any booking can lose that race, get "Error booking service", and leave an invisible
CREATED booking behind while Aria says she is having trouble.

Changes
  1. Wix: Confirm Booking no longer retries blindly (a stale revision never heals).
     Its error output goes to:
       Wix: Refresh Booking      - reads the booking as Wix holds it now
       Check: Refreshed Booking  - already CONFIRMED/PENDING? then it is done
       IF: Already Confirmed?    - yes -> Format: Booking Confirmation
       Wix: Confirm Booking (Retry) - same confirm, fresh revision
     and only a failed retry reaches "Error: Create Booking".
  2. The two Pair Code nodes are re-synced from pair_slots.js / pair_book.js
     (prices for two; guest_name_missing; one participant per booking).
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
PAIR_CODE = {"Pair: Slots For Two": HERE / "pair_slots.js", "Pair: Book Two Guests": HERE / "pair_book.js"}
NEW = ["Wix: Refresh Booking", "Check: Refreshed Booking", "IF: Already Confirmed?", "Wix: Confirm Booking (Retry)"]

APPROVAL = "$('IF: Booking Args Valid').first().json._serviceResolution?.requireManualApproval === true"
RETRY_URL = ("={{ " + APPROVAL + " ? 'https://www.wixapis.com/bookings/v2/confirmation/' + $json.booking.id + "
             "':confirmOrDecline' : 'https://www.wixapis.com/bookings/v2/bookings/' + $json.booking.id + '/confirm' }}")
RETRY_BODY = ("={{ " + APPROVAL + " ? '{\"paymentStatus\": \"NOT_PAID\"}' : "
              "'{\"participantNotification\": {\"notifyParticipants\": true}, \"revision\": ' + $json.booking.revision + '}' }}")
REFRESH_BODY = ('={\n  "query": {\n    "filter": { "id": { "$in": ["{{ $(\'Wix: Create Booking\').first().json.booking.id }}"] } },\n'
                '    "paging": { "limit": 1 }\n  }\n}')
CHECK_CODE = """// After a failed confirm: the booking as Wix holds it now, with its current revision.
// Already CONFIRMED / PENDING (the first confirm went through after all) -> done.
const b = (($input.first().json.bookings) || [])[0] || null;
const done = !!b && ['CONFIRMED', 'PENDING'].includes(b.status);
return [{ json: { booking: b || {}, _alreadyDone: done } }];"""


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


def patch(wf: dict) -> tuple[dict, list[str]]:
    wf = json.loads(json.dumps(wf))
    n = {x["name"]: x for x in wf["nodes"]}
    done = []
    if not all(k in n for k in PAIR_CODE):
        raise SystemExit("two-guest nodes missing - run _patch_pair_booking_and_approval.py first")
    self_url = f"https://automation.aiemply.com/webhook/{n['Webhook — Retell Tool Call']['parameters']['path']}"
    for name, f in PAIR_CODE.items():
        code = f.read_text(encoding="utf-8").replace("__SELF_URL__", self_url)
        if n[name]["parameters"]["jsCode"] != code:
            n[name]["parameters"]["jsCode"] = code
            done.append(f"synced {name}")

    if not any(k in n for k in NEW):
        conf = n["Wix: Confirm Booking"]
        c = wf["connections"]
        if c["Wix: Confirm Booking"]["main"][1][0]["node"] != "Error: Create Booking":
            raise SystemExit("Wix: Confirm Booking error output changed - merge by hand")
        conf["retryOnFail"] = False
        conf.pop("maxTries", None)
        conf.pop("waitBetweenTries", None)
        x, y = conf["position"]
        cred = conf["credentials"]
        wf["nodes"] += [
            {"name": "Wix: Refresh Booking", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.1,
             "position": [x + 220, y + 260], "credentials": cred, "retryOnFail": True, "maxTries": 3,
             "waitBetweenTries": 1000, "onError": "continueErrorOutput",
             "parameters": {"method": "POST", "url": "https://www.wixapis.com/bookings/v2/bookings/query",
                            "authentication": "predefinedCredentialType", "nodeCredentialType": "wixApi",
                            "sendBody": True, "specifyBody": "json", "jsonBody": REFRESH_BODY, "options": {}}},
            {"name": "Check: Refreshed Booking", "type": "n8n-nodes-base.code", "typeVersion": 2,
             "position": [x + 440, y + 260], "parameters": {"jsCode": CHECK_CODE}},
            {"name": "IF: Already Confirmed?", "type": "n8n-nodes-base.if", "typeVersion": 1,
             "position": [x + 660, y + 260],
             "parameters": {"conditions": {"boolean": [{"value1": "={{ $json._alreadyDone === true }}", "value2": True}]}}},
            {"name": "Wix: Confirm Booking (Retry)", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.1,
             "position": [x + 880, y + 360], "credentials": cred, "onError": "continueErrorOutput",
             "parameters": {"method": "POST", "url": RETRY_URL, "authentication": "predefinedCredentialType",
                            "nodeCredentialType": "wixApi", "sendBody": True, "specifyBody": "json",
                            "jsonBody": RETRY_BODY, "options": {}}},
        ]
        link = lambda node: [{"node": node, "type": "main", "index": 0}]
        c["Wix: Confirm Booking"]["main"][1] = link("Wix: Refresh Booking")
        c["Wix: Refresh Booking"] = {"main": [link("Check: Refreshed Booking"), link("Error: Create Booking")]}
        c["Check: Refreshed Booking"] = {"main": [link("IF: Already Confirmed?")]}
        c["IF: Already Confirmed?"] = {"main": [link("Format: Booking Confirmation"), link("Wix: Confirm Booking (Retry)")]}
        c["Wix: Confirm Booking (Retry)"] = {"main": [link("Format: Booking Confirmation"), link("Error: Create Booking")]}
        done.append("confirm retry path installed")

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
    print(f"{label}: {wf['name']} - {len(wf['nodes'])} -> {len(out['nodes'])} nodes; {done or 'nothing to do'}")
    if a.dry_run or not done:
        print("Dry run - n8n not modified." if a.dry_run else "Already up to date.")
        return
    backup = Path(tempfile.gettempdir()) / f"n8n_{a.workflow_id}_before-v66.json"
    backup.write_text(json.dumps(wf, indent=1, ensure_ascii=False), encoding="utf-8")
    put = {"name": wf["name"], "nodes": out["nodes"], "connections": out["connections"],
           "settings": {k: v for k, v in (wf.get("settings") or {}).items() if k in (
               "executionOrder", "timezone", "saveDataErrorExecution", "saveDataSuccessExecution",
               "saveManualExecutions", "saveExecutionProgress", "errorWorkflow", "callerPolicy")}}
    if "staticData" in wf:
        put["staticData"] = wf["staticData"]
    back = call("PUT", f"/api/v1/workflows/{a.workflow_id}", put)
    bn = {x["name"]: x for x in back["nodes"]}
    assert all(k in bn for k in NEW)
    for name in PAIR_CODE:
        assert bn[name]["parameters"]["jsCode"] == {x["name"]: x for x in out["nodes"]}[name]["parameters"]["jsCode"]
    after = call("GET", f"/api/v1/workflows/{a.workflow_id}")
    pins_before, pins_after = sorted((wf.get("pinData") or {}).keys()), sorted((after.get("pinData") or {}).keys())
    print(f"PATCHED {label}: {len(back['nodes'])} nodes, active={back.get('active')} (backup {backup})")
    print(f"  pinned nodes before {len(pins_before)}, after {len(pins_after)}"
          + ("" if pins_before == pins_after else "  <- pins changed"))


if __name__ == "__main__":
    main()
