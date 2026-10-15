"""
Post-call workflow (n8n oH5BUxDffDPgpWvb): a caller who heard the open times and said no is not rung back.

Run:  py -X utf8 Sage_Willow_Spa/outbound/_patch_postcall_declined_not_incomplete.py [--dry-run]

call_88121ba3 (2026-10-09): offered 1, 2 or 3 PM -> "No." -> "another time or day?" -> "No." -> "want the team
to call you?" -> "No." Two minutes later Aria rang them back (call_bd8b1255) with the same times. Same on
call_17652e99 -> call_70ea8fb9. "Classify Call Outcome" filed both as "incomplete" because its definition
included "the caller gave up". Now: turning down real options / a callback / "I'll call back" is
question_answered (no callback; Nicky gets the recap), and "gave up" means Aria could not help them.
Only the system message changes - it comes from _build_post_call_callback_workflow.py. The snapshot gets the
same change.
"""
import importlib.util
import json
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

WF = "oH5BUxDffDPgpWvb"
NODE = "Classify Call Outcome"
HERE = Path(__file__).parent
REPO = HERE.parents[1]
SNAPSHOT = HERE / "post_call_callback_workflow.json"
MARK = "they heard the options, and ringing them back changes nothing"

if sys.argv[1:] not in ([], ["--dry-run"]):
    raise SystemExit(__doc__)
dry = sys.argv[1:] == ["--dry-run"]

spec = importlib.util.spec_from_file_location("builder", HERE / "_build_post_call_callback_workflow.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
NEW = builder.SYSTEM_MESSAGE
assert MARK in NEW

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


ADDITIONS = [
    (" Also when Aria offered real open times and the caller turned them all down, said they will call "
     "back or look elsewhere, or said no to a call from the team - they heard the options, and ringing them "
     "back changes nothing."),
    " because Aria could not help them (not because the times she offered did not suit them)",
    ("\n8. If the tools list shows get_slots returned open times, Aria offered them, and the caller declined them or "
     "said they cannot make them (\"no\", \"I can't do this\", \"I'll look elsewhere\"), the outcome is "
     "question_answered, never incomplete - a callback would only offer the same times again."),
    # call_e3d02f48 replay: told "closed", heard no open time, hung up - must still be rung back.
    " Only when open times were actually offered - a caller who hung up without hearing any open time is incomplete.",
]


def earlier_messages(new: str) -> list:
    """Every text this patch may find live: the original, and each step of it applied so far."""
    for a in ADDITIONS:
        assert new.count(a) == 1, a[:40]
    out = []
    for k in range(len(ADDITIONS)):
        t = new
        for a in ADDITIONS[k:]:
            t = t.replace(a, "")
        out.append(t)
    return out


wf = call("GET", f"/api/v1/workflows/{WF}")
nodes = {x["name"]: x for x in wf["nodes"]}
live_msg = nodes[NODE]["parameters"]["options"]["systemMessage"]
print(f'{wf["name"]}: {len(wf["nodes"])} nodes, active={wf.get("active")}')
if live_msg == NEW:
    print("Already patched.")
    sys.exit(0)
if live_msg not in earlier_messages(NEW):
    raise SystemExit(f"live {NODE} system message is not the one this patch was written against - reconcile first")
print(f"  {NODE}: system message updated ({len(live_msg)} -> {len(NEW)} chars)")
if dry:
    print("Dry run - n8n not modified.")
    sys.exit(0)

backup = Path(tempfile.gettempdir()) / f"n8n_{WF}_before-declined-not-incomplete.json"
backup.write_text(json.dumps(wf, indent=1, ensure_ascii=False), encoding="utf-8")
out_nodes = json.loads(json.dumps(wf["nodes"]))
for x in out_nodes:
    if x["name"] == NODE:
        x["parameters"]["options"]["systemMessage"] = NEW
put = {"name": wf["name"], "nodes": out_nodes, "connections": wf["connections"],
       "settings": {k: v for k, v in (wf.get("settings") or {}).items() if k in (
           "executionOrder", "timezone", "saveDataErrorExecution", "saveDataSuccessExecution",
           "saveManualExecutions", "saveExecutionProgress", "errorWorkflow", "callerPolicy")}}
if "staticData" in wf:
    put["staticData"] = wf["staticData"]
back = call("PUT", f"/api/v1/workflows/{WF}", put)
bk = {x["name"]: x for x in back["nodes"]}
assert bk[NODE]["parameters"]["options"]["systemMessage"] == NEW
for name, x in nodes.items():
    if name != NODE:
        assert bk[name]["parameters"] == x["parameters"], f"other node changed: {name}"
assert back["connections"] == wf["connections"]
print(f'PATCHED: {len(back["nodes"])} nodes, active={back.get("active")} (backup {backup})')
snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
for x in snap["nodes"]:
    if x["name"] == NODE:
        x["parameters"]["options"]["systemMessage"] = NEW
SNAPSHOT.write_text(json.dumps(snap, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"snapshot {SNAPSHOT.name} updated the same way")
