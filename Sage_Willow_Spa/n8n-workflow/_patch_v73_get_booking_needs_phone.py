"""
get_booking sent with no phone answers "send the number" instead of a bare "Error getting booking".

Run:  py -X utf8 Sage_Willow_Spa/n8n-workflow/_patch_v73_get_booking_needs_phone.py <workflow id> [--dry-run]
      (DEV yfbpUaEzZQghelh3 first, then PROD s5dWZOMRl0X7PV65)

call_894e4295 (2026-10-02) and call_d18cc6ab (2026-10-06) called get_booking with {}. Validate
found no phone, the IF sent it to "Error: Getting Booking" - the same reply as a Wix failure - and
Aria told both callers she could not see their booking. V73 makes phone a required argument on the
Retell side; this is the backstop: the invalid-arguments exit gets its own reply that tells the
agent what to do, so it retries with the caller's number instead of giving up.
Only "IF: Get Booking Args Valid" false is rewired; the Wix error exits still use the old reply.
"""
import json
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
IF_NODE = "IF: Get Booking Args Valid"
OLD_ERR = "Error: Getting Booking"
NEW = "Respond: Get Booking Needs Phone"
BODY = ('{\n  "success": false,\n  "error": "No phone number was sent. Call get_booking again with phone set to '
        'the caller\'s number."\n}')

args = sys.argv[1:]
if not args or args[0] not in ("yfbpUaEzZQghelh3", "s5dWZOMRl0X7PV65") or args[1:] not in ([], ["--dry-run"]):
    raise SystemExit(__doc__)
WF, dry = args[0], args[1:] == ["--dry-run"]

raw = (REPO / ".mcp.json").read_text(encoding="utf-8")
env = json.loads(raw[raw.index("{"):])["mcpServers"]["n8n-mcp-aiemply"]["env"]
HDR = {"X-N8N-API-KEY": env["N8N_API_KEY"], "User-Agent": "curl/8.0",
       "Accept": "application/json", "Content-Type": "application/json"}


def call(method, path, body=None):
    r = urllib.request.Request(env["N8N_API_URL"].rstrip("/") + path, method=method, headers=HDR,
                               data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(r, timeout=180) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path} -> {e.code}: {e.read().decode()[:400]}")


wf = call("GET", f"/api/v1/workflows/{WF}")
nodes = {x["name"]: x for x in wf["nodes"]}
print(f'{wf["name"]}: {len(wf["nodes"])} nodes, active={wf.get("active")}')
if NEW in nodes:
    print("Already patched.")
    sys.exit(0)
outs = wf["connections"][IF_NODE]["main"]
if len(outs) != 2 or [o["node"] for o in outs[1]] != [OLD_ERR]:
    raise SystemExit(f"{IF_NODE} false exit is not {OLD_ERR} - reconcile first")
err = nodes[OLD_ERR]
new_node = {
    "parameters": {"respondWith": "json", "responseBody": BODY, "options": {}},
    "id": "respond-get-booking-needs-phone",
    "name": NEW,
    "type": err["type"], "typeVersion": err["typeVersion"],
    "position": [err["position"][0], err["position"][1] + 192],
}
connections = json.loads(json.dumps(wf["connections"]))
connections[IF_NODE]["main"][1] = [{"node": NEW, "type": "main", "index": 0}]
print(f"  + {NEW}; {IF_NODE} false -> {NEW}")
if dry:
    print("Dry run - n8n not modified.")
    sys.exit(0)

backup = Path(tempfile.gettempdir()) / f"n8n_{WF}_before-v73-needs-phone.json"
backup.write_text(json.dumps(wf, indent=1, ensure_ascii=False), encoding="utf-8")
put = {"name": wf["name"], "nodes": wf["nodes"] + [new_node], "connections": connections,
       "settings": {k: v for k, v in (wf.get("settings") or {}).items() if k in (
           "executionOrder", "timezone", "saveDataErrorExecution", "saveDataSuccessExecution",
           "saveManualExecutions", "saveExecutionProgress", "errorWorkflow", "callerPolicy")}}
if "staticData" in wf:
    put["staticData"] = wf["staticData"]
back = call("PUT", f"/api/v1/workflows/{WF}", put)
bk = {x["name"]: x for x in back["nodes"]}
assert bk[NEW]["parameters"]["responseBody"] == BODY
for name, x in nodes.items():
    assert bk[name]["parameters"] == x["parameters"], f"other node changed: {name}"
assert back["connections"][IF_NODE]["main"][1][0]["node"] == NEW
assert back["connections"][IF_NODE]["main"][0] == wf["connections"][IF_NODE]["main"][0]
print(f"PATCHED: {len(back['nodes'])} nodes, active={back.get('active')} (backup {backup})")
