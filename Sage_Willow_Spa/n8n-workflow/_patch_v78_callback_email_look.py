"""
V78 backend - the callback e-mail stops landing in spam and stops looking like a recap.

Run:  py -X utf8 Sage_Willow_Spa/n8n-workflow/_patch_v78_callback_email_look.py <workflow_id> [--dry-run]

Ubaid, 2026-10-15: every callback e-mail since the revamp went to spam, and it looked
the same as the post-call recap.
  Validate: Flag Callback Args  - flag_callback_email.js: amber "Callback needed" panel with
                                  the name and a large tap-to-call number first; no button;
                                  subject "Callback request: <name>" (number only when no name).
  Send Email: Flag Callback     - PROD only: reply_to engineering@aiemply.com instead of the
                                  spa's gmail.com address (the recap, which lands fine, already
                                  does this). DEV already replies to engineering.
"""

from __future__ import annotations
import argparse
import json
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parents[1]
KNOWN = {"yfbpUaEzZQghelh3": "DEV", "s5dWZOMRl0X7PV65": "PROD"}
CODE = HERE / "flag_callback_email.js"
VALIDATE, SEND = "Validate: Flag Callback Args", "Send Email: Flag Callback"
OLD_REPLY, NEW_REPLY = "reply_to: 'sagewillowspa@gmail.com'", "reply_to: 'engineering@aiemply.com'"


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


def v68_code() -> str:
    """The callback e-mail code as V68 installed it - what the live node must still be."""
    return subprocess.run(["git", "show", "0670862:Sage_Willow_Spa/n8n-workflow/flag_callback_email.js"],
                          cwd=REPO, capture_output=True, check=True).stdout.decode("utf-8")


def patch(wf: dict, label: str) -> tuple[dict, list[str]]:
    wf = json.loads(json.dumps(wf))
    n = {x["name"]: x for x in wf["nodes"]}
    done = []
    v = n[VALIDATE]["parameters"]
    code = CODE.read_text(encoding="utf-8")
    if v["jsCode"] != code:
        if v["jsCode"].replace("\r\n", "\n") != v68_code().replace("\r\n", "\n"):
            raise SystemExit(f'"{VALIDATE}" was edited since V68 - merge by hand')
        v["jsCode"] = code
        done.append(f"{VALIDATE}: callback panel, no button, subject without the number")
    body = n[SEND]["parameters"]["jsonBody"]
    if label == "PROD" and NEW_REPLY not in body:
        if body.count(OLD_REPLY) != 1:
            raise SystemExit(f'"{SEND}" reply_to is not the one this patch was written against')
        n[SEND]["parameters"]["jsonBody"] = body.replace(OLD_REPLY, NEW_REPLY)
        done.append(f"{SEND}: reply_to engineering@aiemply.com")
    return wf, done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workflow_id")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    label = KNOWN.get(a.workflow_id)
    if not label:
        raise SystemExit(f"unknown workflow {a.workflow_id}")
    wf = call("GET", f"/api/v1/workflows/{a.workflow_id}")
    out, done = patch(wf, label)
    print(f"{label}: {wf['name']} - {len(wf['nodes'])} nodes; {done or 'nothing to do'}")
    if a.dry_run or not done:
        print("Dry run - n8n not modified." if a.dry_run else "Already up to date.")
        return
    backup = Path(tempfile.gettempdir()) / f"n8n_{a.workflow_id}_before-v78.json"
    backup.write_text(json.dumps(wf, indent=1, ensure_ascii=False), encoding="utf-8")
    put = {"name": wf["name"], "nodes": out["nodes"], "connections": out["connections"],
           "settings": {k: v for k, v in (wf.get("settings") or {}).items() if k in (
               "executionOrder", "timezone", "saveDataErrorExecution", "saveDataSuccessExecution",
               "saveManualExecutions", "saveExecutionProgress", "errorWorkflow", "callerPolicy")}}
    if "staticData" in wf:
        put["staticData"] = wf["staticData"]
    back = call("PUT", f"/api/v1/workflows/{a.workflow_id}", put)
    want = {x["name"]: x["parameters"] for x in out["nodes"]}
    before = {x["name"]: x["parameters"] for x in wf["nodes"]}
    for x in back["nodes"]:
        assert x["parameters"] == want[x["name"]], f"not saved as sent: {x['name']}"
        if x["name"] not in (VALIDATE, SEND):
            assert x["parameters"] == before[x["name"]], f"other node changed: {x['name']}"
    assert back["connections"] == wf["connections"]
    print(f"PATCHED {label}: {len(back['nodes'])} nodes, active={back.get('active')} (backup {backup})")


if __name__ == "__main__":
    main()
