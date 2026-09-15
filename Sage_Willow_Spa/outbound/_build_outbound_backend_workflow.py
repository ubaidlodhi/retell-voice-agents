"""
Replicate the LIVE Sage & Willow n8n backend workflow as an OUTBOUND / DEV copy.

Run:  py -X utf8 outbound/_build_outbound_backend_workflow.py [--update <workflowId>]

What it does
------------
Pulls workflow `s5dWZOMRl0X7PV65` ("Retell AI <-> Wix Bookings | PRODUCTION")
straight from the n8n API and writes a transformed copy:

  * new webhook path            retell-wix  ->  retell-wix-outbound
  * all 18 wixApi credentials   Prod: Sage & Willow Spa Wix account
                                  ->  Test: Wix Sage Site
  * callback email recipient    sagewillowspa@gmail.com -> engineering@aiemply.com
                                (a DEV workflow must never email the client)

Everything else - all 83 nodes, every Code node, the whole Route by Tool
switch - is copied byte-for-byte. Re-run it any time the production workflow
changes and the dev copy re-syncs.

The outbound Retell agent's tools point at the NEW webhook, so outbound test
calls hit the test Wix site and never touch the client's real calendar.
"""

from __future__ import annotations
import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------

N8N_BASE = "https://automation.aiemply.com"
SOURCE_WORKFLOW_ID = "s5dWZOMRl0X7PV65"

TARGET_NAME = "Retell AI <-> Wix Bookings | OUTBOUND (DEV CREDS)"
TARGET_WEBHOOK_PATH = "retell-wix-outbound"
TARGET_WEBHOOK_ID = "retell-wix-outbound-v1"

CRED_PROD = {"id": "poMGaCKgf32bUQQL", "name": "Prod: Sage & Willow Spa Wix account"}
CRED_TEST = {"id": "wLpWbblaihcY4xnw", "name": "Test: Wix Sage Site"}

# A dev workflow must not email the client.
DEV_CALLBACK_RECIPIENT = "engineering@aiemply.com"

OUT_DIR = Path(__file__).parent
SNAPSHOT_PATH = OUT_DIR / "outbound_backend_workflow.json"

# Fields the n8n create/update API rejects or ignores.
STRIP_KEYS = {
    "id", "createdAt", "updatedAt", "active", "isArchived", "versionId",
    "activeVersionId", "versionCounter", "triggerCount", "sourceWorkflowId",
    "shared", "tags", "activeVersion", "meta", "pinData", "staticData",
    "description", "nodeGroups",
}

# The n8n public API rejects any settings key outside this set (400
# "settings must NOT have additional properties"), even though the UI stores
# extras like binaryMode / callerPolicy / availableInMCP on the source workflow.
ALLOWED_SETTINGS = {
    "saveExecutionProgress", "saveManualExecutions", "saveDataErrorExecution",
    "saveDataSuccessExecution", "executionTimeout", "errorWorkflow",
    "timezone", "executionOrder",
}


def api_key() -> str:
    key = os.environ.get("N8N_API_KEY")
    if key:
        return key
    # Fall back to the repo's .mcp.json so the script runs with no env setup.
    mcp = Path(__file__).resolve().parents[2] / ".mcp.json"
    raw = mcp.read_text(encoding="utf-8")
    cfg = json.loads(raw[raw.index("{"):])
    return cfg["mcpServers"]["n8n-mcp"]["env"]["N8N_API_KEY"]


def request(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        f"{N8N_BASE}{path}",
        data=data,
        method=method,
        headers={
            "X-N8N-API-KEY": api_key(),
            "Content-Type": "application/json",
            "Accept": "application/json",
            # The instance's WAF rejects the default Python-urllib agent.
            "User-Agent": "curl/8.0",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise SystemExit(f"n8n API {method} {path} -> {exc.code}: {detail}") from None


# -----------------------------------------------------------------------------
# Transform
# -----------------------------------------------------------------------------

def transform(source: dict) -> tuple[dict, list[str]]:
    """Return (outbound workflow payload, human-readable change log)."""
    wf = {k: v for k, v in source.items() if k not in STRIP_KEYS}
    wf["name"] = TARGET_NAME
    changes: list[str] = []

    swapped_creds = 0
    for node in wf["nodes"]:
        # 1. Webhook path — the outbound agent needs its own entry point.
        if node["type"].endswith(".webhook"):
            node["parameters"]["path"] = TARGET_WEBHOOK_PATH
            node["webhookId"] = TARGET_WEBHOOK_ID
            changes.append(f"webhook path -> /{TARGET_WEBHOOK_PATH}")

        # 2. Wix credentials — production account must never be reachable here.
        creds = node.get("credentials") or {}
        wix = creds.get("wixApi")
        if wix and wix.get("id") == CRED_PROD["id"]:
            creds["wixApi"] = dict(CRED_TEST)
            swapped_creds += 1

        # 3. Callback email — never notify the client from a dev workflow.
        if node["type"].endswith("emailSend"):
            params = node["parameters"]
            params["toEmail"] = DEV_CALLBACK_RECIPIENT
            params.setdefault("options", {})["replyTo"] = DEV_CALLBACK_RECIPIENT
            params["options"].pop("ccEmail", None)
            subject = params.get("subject", "")
            if "[DEV]" not in subject:
                params["subject"] = re.sub(r"^=\{\{", "=[DEV] {{", subject) \
                    if subject.startswith("={{") else f"[DEV] {subject}"
            changes.append(f"callback email -> {DEV_CALLBACK_RECIPIENT}")

    changes.append(f"wixApi credentials swapped to '{CRED_TEST['name']}': {swapped_creds}")

    if swapped_creds == 0:
        raise SystemExit(
            "Refusing to continue: no production wixApi credentials found to swap. "
            "The source workflow may already have been changed."
        )

    return wf, changes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", metavar="WORKFLOW_ID",
                    help="Update an existing dev workflow instead of creating a new one.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Write the JSON snapshot but do not touch n8n.")
    args = ap.parse_args()

    print(f"Fetching source workflow {SOURCE_WORKFLOW_ID} ...")
    source = request("GET", f"/api/v1/workflows/{SOURCE_WORKFLOW_ID}")
    print(f"  source: {source['name']!r} ({len(source['nodes'])} nodes)")

    wf, changes = transform(source)
    SNAPSHOT_PATH.write_text(json.dumps(wf, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote snapshot {SNAPSHOT_PATH}")
    for c in changes:
        print(f"    - {c}")

    if args.dry_run:
        print("Dry run - n8n not modified.")
        return

    payload = {
        "name": wf["name"],
        "nodes": wf["nodes"],
        "connections": wf["connections"],
        "settings": {k: v for k, v in wf.get("settings", {}).items()
                     if k in ALLOWED_SETTINGS} or {"executionOrder": "v1"},
    }

    if args.update:
        result = request("PUT", f"/api/v1/workflows/{args.update}", payload)
        print(f"Updated workflow {result['id']}")
    else:
        result = request("POST", "/api/v1/workflows", payload)
        print(f"Created workflow {result['id']}")

    print(f"  webhook: {N8N_BASE}/webhook/{TARGET_WEBHOOK_PATH}")
    print("  NOTE: created inactive. Activate it in n8n before test calls.")


if __name__ == "__main__":
    main()
