"""
Post-call workflow (n8n oH5BUxDffDPgpWvb): never ring back a number that asked not
to be called, and move the Retell look-ups to /v3/list-calls.

Run:  py -X utf8 Sage_Willow_Spa/outbound/_patch_postcall_do_not_call.py [--dry-run]

Ubaid, 2026-10-03: "if someone says don't call me again ... our outbound agent is making
a call back to that person again ... this kind of calls will not get the call back".
  * new "Retell: Asked Not To Call?" - every call (either agent) whose post-call
    analysis has do_not_call = true; Decide matches the number (from_number when they
    rang us, to_number when we rang them), and also reads this call's own analysis.
  * "Retell: Did They Call Back?" / "Retell: Already Called Back?" were on the legacy
    /v2/list-calls (the client gets deprecation e-mails for it) - now /v3 filters.
Only those four nodes and their wiring change; the node code comes from
_build_post_call_callback_workflow.py (source of truth), everything else stays as it is
live - including the two e-mail nodes, which have their own deploy script. The
snapshot post_call_callback_workflow.json gets the same four nodes, so the e-mail
deploy's "live == snapshot" check still holds.
"""
import importlib.util
import json
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

WF = "oH5BUxDffDPgpWvb"
HERE = Path(__file__).parent
REPO = HERE.parents[1]
SNAPSHOT = HERE / "post_call_callback_workflow.json"
NODES = ["Retell: Did They Call Back?", "Retell: Already Called Back?", "Retell: Asked Not To Call?", "Decide"]

if sys.argv[1:] not in ([], ["--dry-run"]):
    raise SystemExit(__doc__)
dry = sys.argv[1:] == ["--dry-run"]

spec = importlib.util.spec_from_file_location("builder", HERE / "_build_post_call_callback_workflow.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
built = builder.build()
bn = {x["name"]: x for x in built["nodes"]}

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


def apply(wf: dict) -> dict:
    """The four nodes from the build, the rest untouched; rewire Already -> DNC -> Decide."""
    wf = json.loads(json.dumps(wf))
    have = {x["name"]: x for x in wf["nodes"]}
    for name in NODES:
        if name in have:
            have[name]["parameters"] = json.loads(json.dumps(bn[name]["parameters"]))
        else:
            wf["nodes"].append(json.loads(json.dumps(bn[name])))
    c = wf["connections"]
    c["Retell: Already Called Back?"] = {"main": [[{"node": "Retell: Asked Not To Call?", "type": "main", "index": 0}]]}
    c["Retell: Asked Not To Call?"] = {"main": [[{"node": "Decide", "type": "main", "index": 0}]]}
    return wf


snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
wf = call("GET", f"/api/v1/workflows/{WF}")
live = {x["name"]: x for x in wf["nodes"]}
sn = {x["name"]: x for x in snap["nodes"]}
print(f'{wf["name"]}: {len(wf["nodes"])} nodes, active={wf.get("active")}')
if "Retell: Asked Not To Call?" in live:
    print("Already patched.")
    sys.exit(0)
def no_comments(params: dict) -> str:
    # Live Decide carries a comment the snapshot lacks (the DEDUP_MS history) - code is the same.
    return "\n".join(l for l in json.dumps(params, sort_keys=True).replace("\\n", "\n").split("\n")
                     if not l.strip().startswith("//"))


for name in ["Retell: Did They Call Back?", "Retell: Already Called Back?", "Decide"]:
    if no_comments(live[name]["parameters"]) != no_comments(sn[name]["parameters"]):
        raise SystemExit(f'live "{name}" differs from the last deployed snapshot - reconcile first')
out = apply(wf)
print(f"  -> {len(out['nodes'])} nodes; changed: {NODES}")
if dry:
    print("Dry run - n8n not modified.")
    sys.exit(0)

backup = Path(tempfile.gettempdir()) / f"n8n_{WF}_before-dnc.json"
backup.write_text(json.dumps(wf, indent=1, ensure_ascii=False), encoding="utf-8")
put = {"name": wf["name"], "nodes": out["nodes"], "connections": out["connections"],
       "settings": {k: v for k, v in (wf.get("settings") or {}).items() if k in (
           "executionOrder", "timezone", "saveDataErrorExecution", "saveDataSuccessExecution",
           "saveManualExecutions", "saveExecutionProgress", "errorWorkflow", "callerPolicy")}}
if "staticData" in wf:
    put["staticData"] = wf["staticData"]
back = call("PUT", f"/api/v1/workflows/{WF}", put)
bk = {x["name"]: x for x in back["nodes"]}
for name in NODES:
    assert bk[name]["parameters"] == bn[name]["parameters"], name
for name, x in live.items():
    if name not in NODES:
        assert bk[name]["parameters"] == x["parameters"], f"other node changed: {name}"
print(f'PATCHED: {len(back["nodes"])} nodes, active={back.get("active")} (backup {backup})')

# Keep the snapshot in step for these four nodes only.
snap = apply(snap)
SNAPSHOT.write_text(json.dumps(snap, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"snapshot {SNAPSHOT.name} updated for the same four nodes")
