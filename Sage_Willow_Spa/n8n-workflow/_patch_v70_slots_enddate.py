"""
V70 backend - get_slots with only a startDate searches that one day.

Run:  py -X utf8 Sage_Willow_Spa/n8n-workflow/_patch_v70_slots_enddate.py <workflow_id> [--dry-run]

Web test call_7384b0ad (2026-10-01): moving an appointment "to the next day, same time",
Aria called get_slots with startDate 2026-10-08 and no endDate. The backend answered
"Validation failed: endDate is required", so the new time was never checked - Aria went
ahead and moved it anyway (Wix happened to accept). A one-day search is the obvious
meaning: endDate now defaults to the startDate's day ("Validate: Slots Args").
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
NODE = "Validate: Slots Args"
OLD = "if (!args.endDate) errors.push('endDate is required');"
NEW = ("// Only a startDate (call_7384b0ad, 2026-10-01): search that one day rather than refuse.\n"
       "if (!args.endDate && args.startDate) args.endDate = String(args.startDate).slice(0, 10);\n"
       "if (!args.endDate) errors.push('endDate is required');")


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workflow_id")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    label = KNOWN.get(a.workflow_id, "UNKNOWN")
    wf = call("GET", f"/api/v1/workflows/{a.workflow_id}")
    out = json.loads(json.dumps(wf))
    node = {x["name"]: x for x in out["nodes"]}[NODE]["parameters"]
    if NEW in node["jsCode"]:
        print(f"{label}: already up to date.")
        return
    if node["jsCode"].count(OLD) != 1:
        raise SystemExit(f'"{NODE}" does not look as expected - merge by hand')
    node["jsCode"] = node["jsCode"].replace(OLD, NEW)
    print(f"{label}: {NODE}: endDate defaults to the startDate's day")
    if a.dry_run:
        print("Dry run - n8n not modified.")
        return
    backup = Path(tempfile.gettempdir()) / f"n8n_{a.workflow_id}_before-v70.json"
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
    print(f"PATCHED {label}: active={back.get('active')} (backup {backup}); pinned nodes "
          f"{len(wf.get('pinData') or {})} -> {len(after.get('pinData') or {})}")


if __name__ == "__main__":
    main()
