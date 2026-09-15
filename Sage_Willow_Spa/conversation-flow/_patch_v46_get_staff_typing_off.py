"""
V46 - typing sound back OFF for get_staff only.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v46_get_staff_typing_off.py [--dry-run]

Ubaid, 2026-09-14, immediately after V45 turned it on everywhere: "turn off on
this one: get_staff."

Tool-level only. get_staff is invoked from node-book-discovery, which also calls
get_services and get_slots - those two keep their keyboard sound, so the node
flag stays ON and only the tool flag goes off.
"""

from __future__ import annotations
import argparse
import json
import os
import re
import urllib.request
from pathlib import Path

RETELL_BASE = "https://api.retellai.com"
FLOW_ID = "conversation_flow_bdb1968b28ed"
SNAPSHOT = Path(__file__).parent / "aria_conversation_flow.json"
TOOL = "get_staff"


def api_key() -> str:
    key = os.environ.get("RETELL_API_KEY")
    if key:
        return key
    raw = (Path(__file__).resolve().parents[2] / ".mcp.json").read_text(encoding="utf-8")
    cfg = json.loads(raw[raw.index("{"):])
    blob = json.dumps(cfg["mcpServers"]["retell-sage"])
    match = re.search(r"key_[a-f0-9]+", blob)
    if not match:
        raise SystemExit("No Retell key in the retell-sage MCP server entry.")
    return match.group(0)


def request(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        f"{RETELL_BASE}{path}", data=data, method=method,
        headers={"Authorization": f"Bearer {api_key()}",
                 "Content-Type": "application/json", "User-Agent": "curl/8.0"})
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"Retell {method} {path} -> {exc.code}: "
                         f"{exc.read().decode('utf-8', 'replace')}") from None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    flow = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft flow v{flow.get('version')} - {len(flow['tools'])} tools")

    tools = {t["name"]: t for t in flow["tools"]}
    if TOOL not in tools:
        raise SystemExit(f"{TOOL} is not in this flow.")
    print(f"  {TOOL}: {tools[TOOL].get('enable_typing_sound')} -> False")
    tools[TOOL]["enable_typing_sound"] = False

    others = [t["name"] for t in flow["tools"]
              if t["name"] != TOOL and t.get("enable_typing_sound") is not True]
    if others:
        raise SystemExit(f"Other tools lost their typing sound: {others}")

    SNAPSHOT.write_text(json.dumps(flow, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"snapshot -> {SNAPSHOT.name}")
    if args.dry_run:
        print("Dry run - Retell not modified.")
        return

    body = {k: v for k, v in flow.items()
            if k not in ("conversation_flow_id", "version",
                         "last_modification_timestamp", "is_published")}
    request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)

    after = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"PATCHED draft flow v{after.get('version')} (NOT published)\n")
    for t in after["tools"]:
        print(f"    tool {t['name']:22s} typing={t.get('enable_typing_sound')}")
    live = {t["name"]: t.get("enable_typing_sound") for t in after["tools"]}
    if live[TOOL] is not False:
        raise SystemExit(f"FAIL: {TOOL} typing sound is still {live[TOOL]!r}")
    left_on = sorted(n for n, v in live.items() if n != TOOL and v is not True)
    if left_on:
        raise SystemExit(f"FAIL: these lost their typing sound too: {left_on}")
    print(f"\n  {TOOL}: OFF (confirmed live). Every other tool still ON.")


if __name__ == "__main__":
    main()
