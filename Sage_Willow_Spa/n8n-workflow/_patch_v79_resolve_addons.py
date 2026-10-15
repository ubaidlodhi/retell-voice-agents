"""
V79 backend - add-on ids are settled server-side, like service, variant and booking ids.

Run:  py -X utf8 Sage_Willow_Spa/n8n-workflow/_patch_v79_resolve_addons.py <workflow_id> [--dry-run]

call_dde463dd1cad472c17e1b8e1c46 (2026-10-14): Aria copied the Aromatherapy add-on id with one
character missing, Wix refused the booking ("bookedAddOns id is not a valid GUID"). Ubaid: use the
same flow as service ids.
  Resolve: Add-ons (Booking)  - NEW, between "Resolve: Therapist (Booking)" and "IF: Booking Args
                                Valid": resolve_addons.js (name -> exact id -> closest id; groupId
                                from the service).
  Validate: Booking Args      - an add-on entry needs a name or an id; groupId is no longer required
                                (the resolver fills it).
"""

from __future__ import annotations
import argparse
import json
import tempfile
import urllib.error
import urllib.request
import uuid
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parents[1]
SELF = {"yfbpUaEzZQghelh3": ("DEV", "https://automation.aiemply.com/webhook/retell-wix-outbound"),
        "s5dWZOMRl0X7PV65": ("PROD", "https://automation.aiemply.com/webhook/retell-wix")}
CODE = HERE / "resolve_addons.js"
NEW, THERAPIST, IF_VALID, VALIDATE = ("Resolve: Add-ons (Booking)", "Resolve: Therapist (Booking)",
                                      "IF: Booking Args Valid", "Validate: Booking Args")

VALIDATE_SWAPS = [
    ("// addOns: array of { id, groupId } — both required per entry",
     "// addOns: array of { name, id, groupId } - a name or an id per entry; \"Resolve: Add-ons\n"
     "// (Booking)\" settles the real id and groupId from the service itself."),
    ("errors.push('addOns must be an array of {id, groupId} objects');",
     "errors.push('addOns must be an array of {name, id, groupId} objects');"),
    ("                if (!a.id) errors.push(`addOns[${i}].id is required`);\n"
     "                if (!a.groupId) errors.push(`addOns[${i}].groupId is required`);",
     "                if (!a.id && !a.name) errors.push(`addOns[${i}] needs the add-on name`);"),
]


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


def patch(wf: dict, self_url: str) -> tuple[dict, list[str]]:
    wf = json.loads(json.dumps(wf))
    n = {x["name"]: x for x in wf["nodes"]}
    done = []
    code = CODE.read_text(encoding="utf-8").replace("__SELF_URL__", self_url)
    assert "__SELF_URL__" not in code

    v = n[VALIDATE]["parameters"]
    if VALIDATE_SWAPS[-1][1] not in v["jsCode"]:
        for old, new in VALIDATE_SWAPS:
            if v["jsCode"].count(old) != 1:
                raise SystemExit(f'"{VALIDATE}" changed since - merge by hand ({old[:50]!r})')
            v["jsCode"] = v["jsCode"].replace(old, new)
        done.append(f"{VALIDATE}: add-on needs a name or an id")

    if NEW in n:
        if n[NEW]["parameters"]["jsCode"] != code:
            n[NEW]["parameters"]["jsCode"] = code
            done.append(f"{NEW}: code updated")
    else:
        if wf["connections"].get(THERAPIST) != {"main": [[{"node": IF_VALID, "type": "main", "index": 0}]]}:
            raise SystemExit(f'"{THERAPIST}" is not wired straight to "{IF_VALID}" - merge by hand')
        tx, ty = n[THERAPIST]["position"]
        wf["nodes"].append({
            "id": str(uuid.uuid4()), "name": NEW, "type": "n8n-nodes-base.code", "typeVersion": 2,
            "position": [tx + 112, ty + 176], "parameters": {"jsCode": code},
        })
        wf["connections"][THERAPIST] = {"main": [[{"node": NEW, "type": "main", "index": 0}]]}
        wf["connections"][NEW] = {"main": [[{"node": IF_VALID, "type": "main", "index": 0}]]}
        done.append(f"{NEW}: added between {THERAPIST} and {IF_VALID}")
    return wf, done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workflow_id")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.workflow_id not in SELF:
        raise SystemExit(f"unknown workflow {a.workflow_id}")
    label, self_url = SELF[a.workflow_id]
    wf = call("GET", f"/api/v1/workflows/{a.workflow_id}")
    out, done = patch(wf, self_url)
    print(f"{label}: {wf['name']} - {len(wf['nodes'])} nodes; {done or 'nothing to do'}")
    if a.dry_run or not done:
        print("Dry run - n8n not modified." if a.dry_run else "Already up to date.")
        return
    backup = Path(tempfile.gettempdir()) / f"n8n_{a.workflow_id}_before-v79.json"
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
        if x["name"] not in (NEW, VALIDATE):
            assert x["parameters"] == before[x["name"]], f"other node changed: {x['name']}"
    assert back["connections"] == out["connections"]
    print(f"PATCHED {label}: {len(back['nodes'])} nodes, active={back.get('active')} (backup {backup})")


if __name__ == "__main__":
    main()
