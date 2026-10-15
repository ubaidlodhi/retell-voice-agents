"""
Post-call workflow (n8n oH5BUxDffDPgpWvb): "Classify Call Outcome" calls OpenAI chat completions directly
with a strict JSON schema, instead of the LangChain AI Agent + Structured Output Parser.

Run:  py -X utf8 Sage_Willow_Spa/outbound/_patch_postcall_classify_direct.py [--dry-run]

2026-10-10 dry-run replays: 3 of 13 verdicts were thrown away as "The AI model returned an empty
response to the Structured Output Parser" - the model's JSON was right (it is in the parser's input),
only the tool-call wrapper the parser expects varied. A thrown-away verdict means no callback. A plain
chat-completions call with response_format json_schema (strict) cannot come back in another shape.
  * "Classify Call Outcome" becomes an HTTP Request node (same name, same wiring in and out).
  * "OpenAI Chat Model" and "Structured Output Parser" are removed with their sub-node links.
  * "Apply Verdict" reads the verdict from choices[0].message.content.
Everything comes from _build_post_call_callback_workflow.py; the snapshot gets the same change.
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
CLASSIFY, VERDICT = "Classify Call Outcome", "Apply Verdict"
REMOVE = ["OpenAI Chat Model", "Structured Output Parser"]

if sys.argv[1:] not in ([], ["--dry-run"]):
    raise SystemExit(__doc__)
dry = sys.argv[1:] == ["--dry-run"]

spec = importlib.util.spec_from_file_location("builder", HERE / "_build_post_call_callback_workflow.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
bn = {x["name"]: x for x in builder.build()["nodes"]}

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
    out = []
    for x in wf["nodes"]:
        if x["name"] in REMOVE:
            continue
        if x["name"] == CLASSIFY:
            n = json.loads(json.dumps(bn[CLASSIFY]))
            n["id"], n["position"] = x["id"], x["position"]
            x = n
        elif x["name"] == VERDICT:
            x["parameters"] = json.loads(json.dumps(bn[VERDICT]["parameters"]))
        out.append(x)
    wf["nodes"] = out
    for name in REMOVE:
        wf["connections"].pop(name, None)
    names = {x["name"] for x in out}
    for src, conns in wf["connections"].items():
        assert src in names, src
        for kind in conns.values():
            for outs in kind:
                for o in outs or []:
                    assert o["node"] in names, f"{src} -> {o['node']}"
    return wf


wf = call("GET", f"/api/v1/workflows/{WF}")
live = {x["name"]: x for x in wf["nodes"]}
print(f'{wf["name"]}: {len(wf["nodes"])} nodes, active={wf.get("active")}')
if live[CLASSIFY]["type"] == "n8n-nodes-base.httpRequest":
    print("Already patched.")
    sys.exit(0)
if live[CLASSIFY]["parameters"]["options"]["systemMessage"] != builder.SYSTEM_MESSAGE:
    raise SystemExit("live system message differs from the builder - reconcile first")
if "item.output" not in live[VERDICT]["parameters"]["jsCode"]:
    raise SystemExit("live Apply Verdict is not the agent version - reconcile first")
out = apply(wf)
print(f"  -> {len(out['nodes'])} nodes; {CLASSIFY} -> HTTP (chat completions, strict schema); "
      f"removed {REMOVE}; {VERDICT} reads choices[0].message.content")
if dry:
    print("Dry run - n8n not modified.")
    sys.exit(0)

backup = Path(tempfile.gettempdir()) / f"n8n_{WF}_before-classify-direct.json"
backup.write_text(json.dumps(wf, indent=1, ensure_ascii=False), encoding="utf-8")
put = {"name": wf["name"], "nodes": out["nodes"], "connections": out["connections"],
       "settings": {k: v for k, v in (wf.get("settings") or {}).items() if k in (
           "executionOrder", "timezone", "saveDataErrorExecution", "saveDataSuccessExecution",
           "saveManualExecutions", "saveExecutionProgress", "errorWorkflow", "callerPolicy")}}
if "staticData" in wf:
    put["staticData"] = wf["staticData"]
back = call("PUT", f"/api/v1/workflows/{WF}", put)
bk = {x["name"]: x for x in back["nodes"]}
assert bk[CLASSIFY]["type"] == "n8n-nodes-base.httpRequest"
assert bk[CLASSIFY]["parameters"] == bn[CLASSIFY]["parameters"]
assert bk[VERDICT]["parameters"] == bn[VERDICT]["parameters"]
assert not set(REMOVE) & set(bk)
for name, x in live.items():
    if name not in REMOVE + [CLASSIFY, VERDICT]:
        assert bk[name]["parameters"] == x["parameters"], f"other node changed: {name}"
print(f'PATCHED: {len(back["nodes"])} nodes, active={back.get("active")} (backup {backup})')
SNAPSHOT.write_text(json.dumps(apply(json.loads(SNAPSHOT.read_text(encoding="utf-8"))), indent=2,
                               ensure_ascii=False), encoding="utf-8")
print(f"snapshot {SNAPSHOT.name} updated the same way")
