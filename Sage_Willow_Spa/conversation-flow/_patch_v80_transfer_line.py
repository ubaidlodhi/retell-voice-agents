"""
V80 - Aria says a hold line before every transfer. DRAFT ONLY.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v80_transfer_line.py [--dry-run]

call_c303348e (2026-10-10): "Customer service." -> straight into the transfer, not a word from Aria.
A transfer_call node never speaks its instruction unless speak_during_execution is on, so
"Connecting you now." was never heard. Ubaid: say something like "hold on a minute while I
transfer your call" first.
  node-handoff-transfer: speak_during_execution on, fixed line (static text).

No --publish flag on purpose.
"""

from __future__ import annotations
import argparse
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

RETELL_BASE = "https://api.retellai.com"
FLOW_ID = "conversation_flow_bdb1968b28ed"
NODE = "node-handoff-transfer"
OLD = {"type": "prompt", "text": "Say \"Connecting you now.\""}
NEW = {"type": "static_text", "text": "Sure, hold on a moment while I transfer your call."}


def api_key() -> str:
    key = os.environ.get("RETELL_API_KEY")
    if key:
        return key
    raw = (Path(__file__).resolve().parents[2] / ".mcp.json").read_text(encoding="utf-8")
    cfg = json.loads(raw[raw.index("{"):])
    return re.search(r"key_[a-f0-9]+", json.dumps(cfg["mcpServers"]["retell-sage"])).group(0)


def request(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(RETELL_BASE + path, data=data, method=method, headers={
        "Authorization": f"Bearer {api_key()}", "Content-Type": "application/json", "User-Agent": "curl/8.0"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            text = resp.read().decode()
            return json.loads(text) if text.strip() else {}
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Retell {method} {path} -> {e.code}: {e.read().decode()[:600]}")


def patch(flow: dict) -> tuple[dict, list[str]]:
    flow = json.loads(json.dumps(flow))
    n = {x["id"]: x for x in flow["nodes"]}[NODE]
    if n["instruction"] == NEW and n.get("speak_during_execution") is True:
        return flow, []
    if n["instruction"] != OLD:
        raise SystemExit(f"{NODE} instruction changed since - merge by hand: {n['instruction']}")
    n["instruction"] = NEW
    n["speak_during_execution"] = True
    return flow, [f"{NODE}: says \"{NEW['text']}\" before transferring"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    if live.get("is_published"):
        raise SystemExit(f"latest flow v{live['version']} is PUBLISHED - make a draft first, never patch the live one")
    patched, done = patch(live)
    print(f"draft flow v{live['version']}:")
    for x in done or ["nothing to do"]:
        print("  " + x)
    if args.dry_run or not done:
        print("Dry run - Retell not modified." if args.dry_run else "Already up to date.")
        return
    body = {k: v for k, v in patched.items()
            if k not in ("conversation_flow_id", "version", "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    n = {x["id"]: x for x in out["nodes"]}[NODE]
    assert n["instruction"] == NEW and n.get("speak_during_execution") is True, n
    assert not out.get("is_published")
    print(f"PATCHED draft flow v{out['version']} - NOT published")


if __name__ == "__main__":
    main()
