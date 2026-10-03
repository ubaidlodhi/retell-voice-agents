"""
Post-call workflow (n8n oH5BUxDffDPgpWvb): e-mails only where a person needs to act,
and "did we already call them?" looks at the last 10 minutes.

Run:  py -X utf8 Sage_Willow_Spa/outbound/_patch_postcall_missed_lead.py [--dry-run]

Ubaid, 2026-10-03:
  * An inbound call that gets rung back sends no recap - the callback owns the lead.
    The e-mail chain now starts from "IF: Needs Callback?" = false (via "Pass: Call
    Payload", which hands Compose the webhook item), instead of fanning out from the
    webhook beside the callback chain.
  * The callback's own outcome decides: a conversation -> the normal recap; never reached
    them (voicemail, no answer, busy, screener, a hang-up on "Hello?") -> one "Missed lead,
    please call them back" e-mail (post_call_email.js, no model) via "IF: Missed Lead?".
  * Callback skipped because they rang back / were already called / asked not to be
    called -> nothing (another call covers it).
  * Dedup window 15 -> 10 minutes ("Retell: Already Called Back?" + Decide).
Also deploys the two e-mail Code nodes from post_call_email.js / post_call_email_render.js
(they include the V65 two-guest and "appointment requested" lines that were never deployed).
Node code and wiring come from _build_post_call_callback_workflow.py; everything else stays
as it is live. The snapshot gets the same changes.
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
SET_NODES = ["Compose: Post-Call Email", "Render: Recap Email", "Retell: Already Called Back?", "Decide",
             "Pass: Call Payload", "IF: Missed Lead?"]
SET_LINKS = ["Webhook - Retell call_analyzed", "IF: Needs Callback?", "Pass: Call Payload",
             "IF: Real Conversation?", "IF: Missed Lead?"]
GUARD = ["Compose: Post-Call Email", "Render: Recap Email", "Retell: Already Called Back?", "Decide"]

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
if "IF: Missed Lead?" in live:
    print("Already patched.")
    sys.exit(0)
for name in GUARD:
    if live[name]["parameters"] != sn[name]["parameters"]:
        raise SystemExit(f'live "{name}" differs from the last deployed snapshot - reconcile first')
out = apply(wf)
print(f"  -> {len(out['nodes'])} nodes; set: {SET_NODES}; rewired: {SET_LINKS}")
if dry:
    print("Dry run - n8n not modified.")
    sys.exit(0)

backup = Path(tempfile.gettempdir()) / f"n8n_{WF}_before-missed-lead.json"
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
    if name not in SET_NODES:
        assert bk[name]["parameters"] == x["parameters"], f"other node changed: {name}"
for src in SET_LINKS:
    assert back["connections"][src] == built["connections"][src], src
print(f'PATCHED: {len(back["nodes"])} nodes, active={back.get("active")} (backup {backup})')
SNAPSHOT.write_text(json.dumps(apply(snap), indent=2, ensure_ascii=False), encoding="utf-8")
print(f"snapshot {SNAPSHOT.name} updated the same way")
