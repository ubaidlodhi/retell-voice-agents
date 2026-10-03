"""
Put the current post_call_email.js / post_call_email_render.js on the LIVE post-call
workflow (n8n oH5BUxDffDPgpWvb) - those two Code nodes only.

Run:  py -X utf8 Sage_Willow_Spa/outbound/_deploy_post_call_email_code.py [--dry-run]

Safety: the live code of both nodes must equal what post_call_callback_workflow.json
(the last deployed snapshot) holds - so an edit made in the n8n UI is never
overwritten blind. Everything else in the workflow goes back exactly as it is live.
After a successful deploy, re-run _build_post_call_callback_workflow.py --dry-run
to refresh the snapshot.
"""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

WF = "oH5BUxDffDPgpWvb"
HERE = Path(__file__).parent
REPO = HERE.parents[1]
NODES = {"Compose: Post-Call Email": HERE / "post_call_email.js",
         "Render: Recap Email": HERE / "post_call_email_render.js"}
SNAPSHOT = HERE / "post_call_callback_workflow.json"
# Anything but a bare run or --dry-run (a typo, --help) stops here: a real deploy is never a fallback.
if sys.argv[1:] not in ([], ["--dry-run"]):
    raise SystemExit(__doc__)
dry = "--dry-run" in sys.argv

raw = (REPO / ".mcp.json").read_text(encoding="utf-8")
env = json.loads(raw[raw.index("{"):])["mcpServers"]["n8n-mcp-aiemply"]["env"]
BASE = env["N8N_API_URL"].rstrip("/")
HDR = {"X-N8N-API-KEY": env["N8N_API_KEY"], "User-Agent": "curl/8.0",
       "Accept": "application/json", "Content-Type": "application/json"}


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method, headers=HDR)
    try:
        with urllib.request.urlopen(r, timeout=180) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path} -> {e.code}: {e.read().decode()[:400]}")


snap = {n["name"]: n for n in json.loads(SNAPSHOT.read_text(encoding="utf-8"))["nodes"]}
new = {n: f.read_text(encoding="utf-8") for n, f in NODES.items()}
wf = call("GET", f"/api/v1/workflows/{WF}")
live = {n["name"]: n for n in wf["nodes"]}
print(f'{wf["name"]}: {len(wf["nodes"])} nodes, active={wf.get("active")}')
for name in NODES:
    code = live[name]["parameters"].get("jsCode")
    if code != snap[name]["parameters"]["jsCode"]:
        raise SystemExit(f'live "{name}" differs from the last deployed snapshot - reconcile first')
    print(f"  {name}: live == snapshot ({len(code)} chars) -> new {len(new[name])} chars"
          + (" (no change)" if code == new[name] else ""))
if dry:
    print("Dry run - n8n not modified.")
    sys.exit(0)

before = json.loads(json.dumps(wf["nodes"]))
for n in wf["nodes"]:
    if n["name"] in NODES:
        n["parameters"]["jsCode"] = new[n["name"]]
put = {"name": wf["name"], "nodes": wf["nodes"], "connections": wf["connections"],
       "settings": {k: v for k, v in (wf.get("settings") or {}).items() if k in (
           "executionOrder", "timezone", "saveDataErrorExecution", "saveDataSuccessExecution",
           "saveManualExecutions", "saveExecutionProgress", "errorWorkflow", "callerPolicy")}}
if "staticData" in wf:
    put["staticData"] = wf["staticData"]
out = call("PUT", f"/api/v1/workflows/{WF}", put)
back = {n["name"]: n for n in out["nodes"]}
for name in NODES:
    assert back[name]["parameters"]["jsCode"] == new[name], name
strip = lambda n: {k: v for k, v in n.items() if k not in ("position", "webhookId")}
for n in before:
    if n["name"] not in NODES:
        assert strip(back[n["name"]]) == strip(n), f'other node changed: {n["name"]}'
assert out["connections"] == wf["connections"]
print(f'{out["name"]}: {len(out["nodes"])} nodes, active={out.get("active")} - only the two email nodes changed')
