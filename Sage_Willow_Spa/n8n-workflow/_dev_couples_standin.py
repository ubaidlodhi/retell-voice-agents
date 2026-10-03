"""
DEV ONLY - a "Couples Massage" that behaves as request-first, for testing Aria.

Run:  py -X utf8 Sage_Willow_Spa/n8n-workflow/_dev_couples_standin.py          (install)
      py -X utf8 Sage_Willow_Spa/n8n-workflow/_dev_couples_standin.py --remove (restore)
      add --dry-run to either to see what would change

Why: the TEST Wix site has no Couples Massage and no request-first service, and
Ubaid (2026-09-29) did not want Wix changed for the test. So the DEV workflow
fakes both, without touching Wix:
  * get_services lists a "Couples Massage" (the test site's Prenatal Massage under
    another name) marked "byRequest": true.
  * get_slots / book_appointment for "Couples Massage" run on Prenatal Massage.
  * The booking result comes back "status": "PENDING" - what the real Couples
    Massage returns in production, where Nicky set it to request first.
The test Wix site itself ends up with an ordinary Prenatal booking.

Refuses to run on anything but the DEV workflow. --remove puts the four nodes
back exactly as they were (from _dev_couples_standin_backup.json).
"""
import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path

DEV = "yfbpUaEzZQghelh3"
HERE = Path(__file__).parent
REPO = HERE.parents[1]
BACKUP = HERE / "_dev_couples_standin_backup.json"
MARK = "DEV STAND-IN"

PARSE_OLD = "return [{ json: { tool, args, callerPhone } }];"
PARSE_NEW = """// >>> DEV STAND-IN (test site has no Couples Massage) - remove with _dev_couples_standin.py --remove
if (args && typeof args.serviceName === 'string' && /couple/i.test(args.serviceName)) {
    args._standIn = 'Couples Massage';
    args.serviceName = 'Prenatal Massage';
}
// <<< DEV STAND-IN

return [{ json: { tool, args, callerPhone } }];"""

SERVICES_OLD = "return [{ json: {\n  success: true,\n  count: payload.length,"
SERVICES_NEW = """// >>> DEV STAND-IN: "Couples Massage" = the test site's Prenatal Massage, request-first
const _standIn = ($('Parse Retell Payload').first().json.args || {})._standIn;
if (_standIn) {
  for (const s of payload) if (s.name === 'Prenatal Massage') { s.name = _standIn; s.byRequest = true; }
} else if (catalog) {
  const p = payload.find(s => s.name === 'Prenatal Massage');
  if (p) payload.push(Object.assign({}, p, { name: 'Couples Massage',
    description: 'Relax together, side by side in our couples room.', byRequest: true }));
}
// <<< DEV STAND-IN

return [{ json: {
  success: true,
  count: payload.length,"""

RESOLVE_OLD = "const requireManualApproval = !!(finalRaw.onlineBooking && finalRaw.onlineBooking.requireManualApproval === true);"
RESOLVE_NEW = """let requireManualApproval = !!(finalRaw.onlineBooking && finalRaw.onlineBooking.requireManualApproval === true);
// >>> DEV STAND-IN
if (($('Parse Retell Payload').first().json.args || {})._standIn) requireManualApproval = true;
// <<< DEV STAND-IN"""

FORMAT_OLD = "const status = booking.status || '';"
FORMAT_NEW = """let status = booking.status || '';
// >>> DEV STAND-IN: Wix confirms the Prenatal booking; production would hold a Couples Massage as PENDING
if (($('Parse Retell Payload').first().json.args || {})._standIn && status === 'CONFIRMED') status = 'PENDING';
// <<< DEV STAND-IN"""

EDITS = {
    "Parse Retell Payload": (PARSE_OLD, PARSE_NEW),
    "Format: Services Response": (SERVICES_OLD, SERVICES_NEW),
    "Resolve: Service (Booking)": (RESOLVE_OLD, RESOLVE_NEW),
    "Format: Booking Confirmation": (FORMAT_OLD, FORMAT_NEW),
}


def api(method, path, body=None):
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


def put(wf, nodes):
    body = {"name": wf["name"], "nodes": nodes, "connections": wf["connections"],
            "settings": {k: v for k, v in (wf.get("settings") or {}).items() if k in (
                "executionOrder", "timezone", "saveDataErrorExecution", "saveDataSuccessExecution",
                "saveManualExecutions", "saveExecutionProgress", "errorWorkflow", "callerPolicy")}}
    if "staticData" in wf:
        body["staticData"] = wf["staticData"]
    return api("PUT", f"/api/v1/workflows/{DEV}", body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--remove", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    wf = api("GET", f"/api/v1/workflows/{DEV}")
    if "DEV" not in wf["name"]:
        raise SystemExit(f"refusing: {wf['name']!r} is not the DEV workflow")
    n = {x["name"]: x for x in wf["nodes"]}

    if a.remove:
        saved = json.loads(BACKUP.read_text(encoding="utf-8"))
        for name in EDITS:
            if MARK not in n[name]["parameters"]["jsCode"]:
                raise SystemExit(f"{name} has no stand-in - nothing to remove")
            n[name]["parameters"]["jsCode"] = saved[name]
        print("restoring", list(EDITS))
    else:
        if any(MARK in n[name]["parameters"]["jsCode"] for name in EDITS):
            raise SystemExit("stand-in already installed")
        saved = {}
        for name, (old, new) in EDITS.items():
            code = n[name]["parameters"]["jsCode"]
            if code.count(old) != 1:
                raise SystemExit(f"{name}: anchor not found once - changed since V65?")
            saved[name] = code
            n[name]["parameters"]["jsCode"] = code.replace(old, new)
        print("installing stand-in in", list(EDITS))
    if a.dry_run:
        print("Dry run - n8n not modified.")
        return
    if not a.remove:
        BACKUP.write_text(json.dumps(saved, indent=1, ensure_ascii=False), encoding="utf-8")
    out = put(wf, wf["nodes"])
    back = {x["name"]: x for x in out["nodes"]}
    for name in EDITS:
        assert (MARK in back[name]["parameters"]["jsCode"]) != a.remove, name
    print(f"{'REMOVED' if a.remove else 'INSTALLED'} on {out['name']} ({len(out['nodes'])} nodes)")


if __name__ == "__main__":
    main()
