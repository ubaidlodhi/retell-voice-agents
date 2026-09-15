"""
Point the INBOUND agent's 8 tools at the dev or the production n8n backend.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_switch_tool_env.py dev  [--dry-run]
      py -X utf8 Sage_Willow_Spa/conversation-flow/_switch_tool_env.py prod [--dry-run]

dev   -> https://automation.aiemply.com/webhook/retell-wix-outbound
         n8n yfbpUaEzZQghelh3, all 18 wixApi nodes on "Test: Wix Sage Site".
         Bookings land on the TEST Wix site (Rocky / Lily). Callback emails go
         to engineering@aiemply.com with a [DEV] subject prefix.

prod  -> https://automation.aiemply.com/webhook/retell-wix
         n8n s5dWZOMRl0X7PV65, all 18 wixApi nodes on the client's real Wix
         account. Bookings land on Nicky's real calendar.

This only ever edits the agent's DRAFT conversation flow and never publishes.
Which callers are affected therefore depends on the phone number binding:

  * number bound to "latest_published" -> real callers are NOT affected
  * number bound to "latest"           -> real callers ARE affected immediately

`+16282862281` was bound to "latest" on 2026-09-14 at Ubaid's request so the
dev backend could be exercised over the real phone line overnight (US night,
no real traffic expected). SWITCH BACK TO prod BEFORE US MORNING, or rebind the
number to latest_published.
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
AGENT_ID = "agent_eceb7448aa1f37e8f436a63a43"
PHONE_NUMBER = "+16282862281"

URLS = {
    "dev": "https://automation.aiemply.com/webhook/retell-wix-outbound",
    "prod": "https://automation.aiemply.com/webhook/retell-wix",
}
EXPECTED_TOOLS = 8


def api_key() -> str:
    """Key for the Sage & Willow Retell workspace.

    Read from the `retell-sage` MCP server entry specifically - the repo's
    .mcp.json also holds keys for other workspaces, and a blind grep picks the
    wrong one.
    """
    key = os.environ.get("RETELL_API_KEY")
    if key:
        return key
    raw = (Path(__file__).resolve().parents[2] / ".mcp.json").read_text(encoding="utf-8")
    cfg = json.loads(raw[raw.index("{"):])
    blob = json.dumps(cfg["mcpServers"]["retell-sage"])
    match = re.search(r"key_[a-f0-9]+", blob)
    if not match:
        raise SystemExit("No Retell key found in the retell-sage MCP server entry.")
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
    ap.add_argument("env", choices=["dev", "prod"])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    target = URLS[args.env]
    other = URLS["prod" if args.env == "dev" else "dev"]

    flow = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft flow v{flow.get('version')} - {len(flow['nodes'])} nodes, "
          f"{len(flow['tools'])} tools")

    changed = []
    for tool in flow["tools"]:
        url = tool.get("url")
        if url in (target, other):
            if url != target:
                changed.append(tool["name"])
            tool["url"] = target
        elif url:
            raise SystemExit(f"Tool {tool['name']} has an unexpected URL: {url}")

    on_target = [t["name"] for t in flow["tools"] if t.get("url") == target]
    if len(on_target) != EXPECTED_TOOLS:
        raise SystemExit(f"Expected {EXPECTED_TOOLS} tools on {target}, found {len(on_target)}.")

    print(f"target: {target}")
    print(f"  {len(changed)} switched: {changed or '(already there)'}")
    print(f"  {len(on_target)} tools now on the {args.env} backend")

    if args.dry_run:
        print("Dry run - Retell not modified.")
        return

    body = {k: v for k, v in flow.items()
            if k not in ("conversation_flow_id", "version",
                         "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    print(f"PATCHED draft flow v{out.get('version')} (NOT published)")

    number = request("GET", f"/get-phone-number/{PHONE_NUMBER}")
    binding = number.get("inbound_agents")
    print(f"{PHONE_NUMBER} inbound binding: {binding}")
    if binding and any(a.get("agent_version") == "latest" for a in binding):
        print(f"  -> the number serves the DRAFT, so real callers hit the "
              f"{args.env.upper()} backend right now.")
    else:
        print("  -> the number serves a published version, so this draft edit "
              "does not reach real callers until it is published.")


if __name__ == "__main__":
    main()
