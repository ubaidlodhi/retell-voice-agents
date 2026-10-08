"""
Move Aria's notification e-mails from SMTP (engineering@aiemply.com) to Resend:
sender "Aria AI Employee <aria@notifications.aiemply.com>", engineering on CC (Ubaid, 2026-10-04).

Run:  py -X utf8 Sage_Willow_Spa/n8n-workflow/_patch_resend_email.py --cred <n8n credential id> [dev|prod|postcall ...] [--dry-run]

  dev       DEV backend yfbpUaEzZQghelh3   "Send Email: Flag Callback"   -> engineering only, [DEV] subject
  prod      PROD backend s5dWZOMRl0X7PV65  "Send Email: Flag Callback"   -> the spa, CC engineering
  postcall  post-call wf oH5BUxDffDPgpWvb  "Send Email: Post-Call Recap" -> the spa, CC engineering
  (no target given = all three)

The credential is an n8n "Bearer Auth" credential whose token is the Resend API key.
Each node is swapped in place for an HTTP Request (POST https://api.resend.com/emails): same
name, id, position and wiring, same error behaviour (callback: error output -> "Error: Flag
Callback"; recap: continue). Subject, HTML and text come from the same fields as before.
An Idempotency-Key (execution id / call id) means a retry never sends the e-mail twice.
"""
import importlib.util
import json
import re
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
import resend_email as R  # noqa: E402

args = sys.argv[1:]
dry = "--dry-run" in args
if "--cred" not in args or args.index("--cred") + 1 >= len(args):
    raise SystemExit(__doc__)
CRED = args[args.index("--cred") + 1]
targets = [a for a in args if a in ("dev", "prod", "postcall")] or ["dev", "prod", "postcall"]
if set(args) - set(targets) - {"--dry-run", "--cred", CRED}:
    raise SystemExit(__doc__)

CALLBACK_FIELDS = {
    "prod": ("to: [" + repr(R.SPA) + "], cc: [" + repr(R.ENGINEERING) + "], reply_to: " + repr(R.SPA) + ", "
             "subject: $json._emailSubject, html: $json._emailHtml, text: $json._emailBody"),
    "dev": ("to: [" + repr(R.ENGINEERING) + "], reply_to: " + repr(R.ENGINEERING) + ", "
            "subject: '[DEV] ' + $json._emailSubject, html: $json._emailHtml, text: $json._emailBody"),
}
# What each live node must look like before we touch it.
EXPECT_TO = {"prod": R.SPA, "dev": R.ENGINEERING, "postcall": "={{ $json.to }}"}

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


def load_builder():
    spec = importlib.util.spec_from_file_location(
        "builder", REPO / "Sage_Willow_Spa" / "outbound" / "_build_post_call_callback_workflow.py")
    b = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b)
    b.RESEND_CRED_ID = CRED
    return b


def new_node(target, old):
    if target == "postcall":
        b = load_builder()
        n = next(x for x in b.build()["nodes"] if x["name"] == "Send Email: Post-Call Recap")
        n["credentials"]["httpBearerAuth"]["id"] = CRED
        n["position"] = old["position"]
        return n
    idem = "=aria-callback-{{ $execution.id }}" if target == "prod" else "=aria-dev-callback-{{ $execution.id }}"
    return R.resend_node(old["id"], old["name"], old["position"], CALLBACK_FIELDS[target], idem, CRED,
                         old.get("onError", "continueErrorOutput"))


WF = {"dev": ("yfbpUaEzZQghelh3", "Send Email: Flag Callback"),
      "prod": ("s5dWZOMRl0X7PV65", "Send Email: Flag Callback"),
      "postcall": ("oH5BUxDffDPgpWvb", "Send Email: Post-Call Recap")}

for t in targets:
    wf_id, name = WF[t]
    wf = call("GET", f"/api/v1/workflows/{wf_id}")
    nodes = {x["name"]: x for x in wf["nodes"]}
    old = nodes[name]
    print(f"[{t}] {wf['name']}: {len(wf['nodes'])} nodes, active={wf.get('active')}")
    if old["type"] == "n8n-nodes-base.httpRequest" and R.RESEND_URL == old["parameters"].get("url"):
        print("   already on Resend - skipped")
        continue
    if old["type"] != "n8n-nodes-base.emailSend" or old["parameters"].get("toEmail") != EXPECT_TO[t]:
        raise SystemExit(f'   live "{name}" is not the SMTP node we expect - reconcile first')
    nn = new_node(t, old)
    print("   body:", nn["parameters"]["jsonBody"])
    print("   idempotency:", nn["parameters"]["headerParameters"]["parameters"][0]["value"], "| onError:", nn["onError"])
    if dry:
        continue
    backup = Path(tempfile.gettempdir()) / f"n8n_{wf_id}_before-resend.json"
    backup.write_text(json.dumps(wf, indent=1, ensure_ascii=False), encoding="utf-8")
    out_nodes = [nn if x["name"] == name else x for x in wf["nodes"]]
    put = {"name": wf["name"], "nodes": out_nodes, "connections": wf["connections"],
           "settings": {k: v for k, v in (wf.get("settings") or {}).items() if k in (
               "executionOrder", "timezone", "saveDataErrorExecution", "saveDataSuccessExecution",
               "saveManualExecutions", "saveExecutionProgress", "errorWorkflow", "callerPolicy")}}
    if "staticData" in wf:
        put["staticData"] = wf["staticData"]
    back = call("PUT", f"/api/v1/workflows/{wf_id}", put)
    bk = {x["name"]: x for x in back["nodes"]}
    assert bk[name]["type"] == "n8n-nodes-base.httpRequest" and bk[name]["parameters"] == nn["parameters"], name
    assert bk[name]["credentials"]["httpBearerAuth"]["id"] == CRED
    for n, x in nodes.items():
        if n != name:
            assert bk[n]["parameters"] == x["parameters"], f"other node changed: {n}"
    assert back["connections"] == wf["connections"]
    print(f"   PATCHED: {len(back['nodes'])} nodes, active={back.get('active')} (backup {backup})")
    if t == "postcall":
        snap_path = REPO / "Sage_Willow_Spa" / "outbound" / "post_call_callback_workflow.json"
        snap = json.loads(snap_path.read_text(encoding="utf-8"))
        snap["nodes"] = [nn if x["name"] == name else x for x in snap["nodes"]]
        snap_path.write_text(json.dumps(snap, indent=2, ensure_ascii=False), encoding="utf-8")
        bpath = REPO / "Sage_Willow_Spa" / "outbound" / "_build_post_call_callback_workflow.py"
        src = bpath.read_text(encoding="utf-8")
        bpath.write_text(re.sub(r'RESEND_CRED_ID = "[^"]*"', f'RESEND_CRED_ID = "{CRED}"', src), encoding="utf-8")
        print("   snapshot + builder credential id updated")
