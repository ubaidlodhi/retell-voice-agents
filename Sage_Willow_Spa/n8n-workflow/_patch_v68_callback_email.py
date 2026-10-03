"""
V68 backend - the callback e-mail in the same HTML design as the post-call recap.

Run:  py -X utf8 Sage_Willow_Spa/n8n-workflow/_patch_v68_callback_email.py <workflow_id> [--dry-run]

Ubaid, 2026-10-01: the recap e-mail is proper HTML, the callback e-mail was a raw
text block. Changes:
  Validate: Flag Callback Args  - flag_callback_email.js: same checks as before, plus an
                                  HTML body (AIEmply header, "Callback request" card with a
                                  tap-to-call number, "What they asked" card, a "Call X back"
                                  button) and a plain-text part. Subject "Callback request:
                                  <name>, <phone>". "unknown" as a name reads as not given.
  Send Email: Flag Callback     - sends both parts (HTML + text). Recipient, sender, CC,
                                  reply-to and the DEV "[DEV]" subject prefix stay as they are.
"""

from __future__ import annotations
import argparse
import json
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parents[1]
KNOWN = {"yfbpUaEzZQghelh3": "DEV", "s5dWZOMRl0X7PV65": "PROD"}
CODE = HERE / "flag_callback_email.js"
OLD_MARK = "A caller asked Aria for a callback. Please follow up."


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


def patch(wf: dict) -> tuple[dict, list[str]]:
    wf = json.loads(json.dumps(wf))
    n = {x["name"]: x for x in wf["nodes"]}
    done = []
    v = n["Validate: Flag Callback Args"]["parameters"]
    code = CODE.read_text(encoding="utf-8")
    if v["jsCode"] != code:
        if OLD_MARK not in v["jsCode"]:
            raise SystemExit('"Validate: Flag Callback Args" was edited since - merge by hand')
        v["jsCode"] = code
        done.append("Validate: Flag Callback Args: HTML + text e-mail")
    s = n["Send Email: Flag Callback"]["parameters"]
    if s.get("emailFormat") != "both" or s.get("html") != "={{ $json._emailHtml }}":
        if s.get("emailFormat") != "text" or s.get("text") != "={{ $json._emailBody }}":
            raise SystemExit('"Send Email: Flag Callback" was edited since - merge by hand')
        s["emailFormat"] = "both"
        s["html"] = "={{ $json._emailHtml }}"
        done.append("Send Email: Flag Callback: HTML + text parts")
    return wf, done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workflow_id")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    label = KNOWN.get(a.workflow_id, "UNKNOWN")
    wf = call("GET", f"/api/v1/workflows/{a.workflow_id}")
    out, done = patch(wf)
    print(f"{label}: {wf['name']} - {len(wf['nodes'])} nodes; {done or 'nothing to do'}")
    if a.dry_run or not done:
        print("Dry run - n8n not modified." if a.dry_run else "Already up to date.")
        return
    backup = Path(tempfile.gettempdir()) / f"n8n_{a.workflow_id}_before-v68.json"
    backup.write_text(json.dumps(wf, indent=1, ensure_ascii=False), encoding="utf-8")
    put = {"name": wf["name"], "nodes": out["nodes"], "connections": out["connections"],
           "settings": {k: v for k, v in (wf.get("settings") or {}).items() if k in (
               "executionOrder", "timezone", "saveDataErrorExecution", "saveDataSuccessExecution",
               "saveManualExecutions", "saveExecutionProgress", "errorWorkflow", "callerPolicy")}}
    if "staticData" in wf:
        put["staticData"] = wf["staticData"]
    back = call("PUT", f"/api/v1/workflows/{a.workflow_id}", put)
    want = {x["name"]: x["parameters"] for x in out["nodes"]}
    for x in back["nodes"]:
        assert x["parameters"] == want[x["name"]], f"not saved as sent: {x['name']}"
    after = call("GET", f"/api/v1/workflows/{a.workflow_id}")
    pins_before, pins_after = sorted((wf.get("pinData") or {}).keys()), sorted((after.get("pinData") or {}).keys())
    print(f"PATCHED {label}: {len(back['nodes'])} nodes, active={back.get('active')} (backup {backup})")
    print(f"  pinned nodes before {len(pins_before)}, after {len(pins_after)}"
          + ("" if pins_before == pins_after else "  <- pins changed"))


if __name__ == "__main__":
    main()
