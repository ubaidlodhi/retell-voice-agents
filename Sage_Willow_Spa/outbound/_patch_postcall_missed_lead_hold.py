"""
Post-call workflow (n8n oH5BUxDffDPgpWvb): a "Missed lead" e-mail waits 10 minutes and goes only if
the person has not reached us since.

Run:  py -X utf8 Sage_Willow_Spa/outbound/_patch_postcall_missed_lead_hold.py [--dry-run]

2026-10-04 and 2026-10-06: Hilda and Karen rang the spa and booked minutes after Aria's callback
reached their voicemail. Nicky got "Missed lead, please call them back" and "appointment booked"
for the same person. "IF: Missed Lead?" true now goes Wait: 10 Minutes -> Retell: Reached Us Since?
(inbound calls from the number we rang) -> Decide: Still Missed? (missed_lead_hold.js, harness
test_missed_lead_hold.js) -> IF: Still Missed? -> Send Email / Skip: Reached Us Since.
Node code and wiring come from _build_post_call_callback_workflow.py; everything else stays as it is
live. The snapshot gets the same changes.
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
SET_NODES = ["Wait: 10 Minutes", "Retell: Reached Us Since?", "Decide: Still Missed?", "IF: Still Missed?",
             "Skip: Reached Us Since"]
SET_LINKS = ["IF: Missed Lead?", "Wait: 10 Minutes", "Retell: Reached Us Since?", "Decide: Still Missed?",
             "IF: Still Missed?"]
GUARD = ["Compose: Post-Call Email", "IF: Missed Lead?", "Send Email: Post-Call Recap"]

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
    wf = json.loads(json.dumps(wf))
    have = {x["name"]: x for x in wf["nodes"]}
    for name in SET_NODES:
        if name in have:
            have[name]["parameters"] = json.loads(json.dumps(bn[name]["parameters"]))
        else:
            wf["nodes"].append(json.loads(json.dumps(bn[name])))
    for src in SET_LINKS:
        wf["connections"][src] = json.loads(json.dumps(built["connections"][src]))
    names = {x["name"] for x in wf["nodes"]}
    for src, conns in wf["connections"].items():
        assert src in names, src
        for outs in conns.get("main", []):
            for o in outs or []:
                assert o["node"] in names, f"{src} -> {o['node']}"
    return wf


snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
sn = {x["name"]: x for x in snap["nodes"]}
wf = call("GET", f"/api/v1/workflows/{WF}")
live = {x["name"]: x for x in wf["nodes"]}
print(f'{wf["name"]}: {len(wf["nodes"])} nodes, active={wf.get("active")}')
if "Decide: Still Missed?" in live:
    print("Already patched.")
    sys.exit(0)
# The nodes this chain hangs off must be the ones last deployed (n8n drops default values such as
# the webhook's responseMode on save, so other nodes are not compared - they are left as they are).
for name in GUARD:
    if live[name]["parameters"] != sn[name]["parameters"] or live[name]["parameters"] != bn[name]["parameters"]:
        raise SystemExit(f'live "{name}" differs from the snapshot/builder - reconcile first')
if wf["connections"]["IF: Missed Lead?"] != snap["connections"]["IF: Missed Lead?"]:
    raise SystemExit("IF: Missed Lead? wiring differs from the snapshot - reconcile first")
out = apply(wf)
print(f"  -> {len(out['nodes'])} nodes; set: {SET_NODES}; rewired: {SET_LINKS}")
if dry:
    print("Dry run - n8n not modified.")
    sys.exit(0)

backup = Path(tempfile.gettempdir()) / f"n8n_{WF}_before-missed-lead-hold.json"
backup.write_text(json.dumps(wf, indent=1, ensure_ascii=False), encoding="utf-8")
put = {"name": wf["name"], "nodes": out["nodes"], "connections": out["connections"],
       "settings": {k: v for k, v in (wf.get("settings") or {}).items() if k in (
           "executionOrder", "timezone", "saveDataErrorExecution", "saveDataSuccessExecution",
           "saveManualExecutions", "saveExecutionProgress", "errorWorkflow", "callerPolicy")}}
if "staticData" in wf:
    put["staticData"] = wf["staticData"]
back = call("PUT", f"/api/v1/workflows/{WF}", put)
bk = {x["name"]: x for x in back["nodes"]}
for name in SET_NODES:
    assert bk[name]["parameters"] == bn[name]["parameters"], name
for name, x in live.items():
    assert bk[name]["parameters"] == x["parameters"], f"other node changed: {name}"
for src in SET_LINKS:
    assert back["connections"][src] == built["connections"][src], src
print(f'PATCHED: {len(back["nodes"])} nodes, active={back.get("active")} (backup {backup})')
SNAPSHOT.write_text(json.dumps(apply(snap), indent=2, ensure_ascii=False), encoding="utf-8")
print(f"snapshot {SNAPSHOT.name} updated the same way")
