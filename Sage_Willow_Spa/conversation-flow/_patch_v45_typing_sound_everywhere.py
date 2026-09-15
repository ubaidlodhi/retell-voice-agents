"""
V45 - typing sound on for every tool, and on every node that calls one.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v45_typing_sound_everywhere.py [--dry-run]

Ubaid, 2026-09-14: "make sure all tools have typing sound ON."

Audit before this patch:

    get_services         typing ON    silent during execution
    get_staff            typing OFF   silent during execution   <- dead air
    get_slots            typing ON    silent during execution
    book_appointment     typing ON    "Booking that for you now."
    get_booking          typing ON    "Let me find that booking."
    cancel_booking       typing ON    "Cancelling that now."
    reschedule_booking   typing ON    "Moving that appointment now."
    flag_callback        typing ON    "Passing that to the team now."

get_staff was the only one with nothing at all - no keyboard, no spoken filler -
so a caller asking for a specific therapist heard flat silence while Wix was
queried. Every tool now has it.

The tool-calling NODES are handled too. All six function nodes already had it;
the six subagent nodes (which is where get_services, get_slots and get_booking
actually get invoked) never had the field set. This script writes it on them and
then reads the flow back to see whether Retell kept it - subagent nodes are not
documented as carrying the flag, so the read-back is the only honest way to know
whether it took. If Retell drops it, the tool-level setting is what governs
there and the printed summary will say so rather than claiming a fix that is not
real.
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

# Node types that invoke a tool and could therefore want the keyboard sound.
TOOL_NODE_TYPES = ("function", "subagent", "mcp")


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


def patch(flow: dict) -> tuple[dict, list[str], list[str]]:
    flow = json.loads(json.dumps(flow))
    tools_changed, nodes_changed = [], []

    for tool in flow["tools"]:
        if tool.get("enable_typing_sound") is not True:
            tools_changed.append(f"{tool['name']} ({tool.get('enable_typing_sound')!r} -> True)")
        tool["enable_typing_sound"] = True

    for node in flow["nodes"]:
        if node["type"] not in TOOL_NODE_TYPES:
            continue
        if not (node.get("tool_id") or node.get("tool_ids")):
            continue
        if node.get("enable_typing_sound") is not True:
            nodes_changed.append(f"{node['id']} ({node.get('enable_typing_sound')!r} -> True)")
        node["enable_typing_sound"] = True

    off = [t["name"] for t in flow["tools"] if t.get("enable_typing_sound") is not True]
    if off:
        raise SystemExit(f"Tools still silent after patching: {off}")
    return flow, tools_changed, nodes_changed


def report(flow: dict, label: str) -> None:
    print(f"  {label}")
    for tool in flow["tools"]:
        print(f"    tool {tool['name']:22s} typing={tool.get('enable_typing_sound')}")
    for node in flow["nodes"]:
        if node["type"] in TOOL_NODE_TYPES and (node.get("tool_id") or node.get("tool_ids")):
            print(f"    node {node['id']:28s} {node['type']:9s} "
                  f"typing={node.get('enable_typing_sound')}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft flow v{live.get('version')} - {len(live['nodes'])} nodes, "
          f"{len(live['tools'])} tools")
    patched, tools_changed, nodes_changed = patch(live)
    print(f"  tools switched on: {tools_changed or '(all were already on)'}")
    print(f"  nodes switched on: {nodes_changed or '(all were already on)'}")

    SNAPSHOT.write_text(json.dumps(patched, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"snapshot -> {SNAPSHOT.name}")
    if args.dry_run:
        print("Dry run - Retell not modified.")
        return

    body = {k: v for k, v in patched.items()
            if k not in ("conversation_flow_id", "version",
                         "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    print(f"PATCHED draft flow v{out.get('version')} (NOT published)\n")

    # Read back from the API, not from what we sent - subagent nodes may not
    # carry this field at all, and a silently dropped write must not be reported
    # as a fix.
    live_after = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    report(live_after, "LIVE after patch:")

    still_off = [t["name"] for t in live_after["tools"]
                 if t.get("enable_typing_sound") is not True]
    dropped = [n["id"] for n in live_after["nodes"]
               if n["type"] in TOOL_NODE_TYPES and (n.get("tool_id") or n.get("tool_ids"))
               and n.get("enable_typing_sound") is not True]
    print()
    if still_off:
        raise SystemExit(f"FAIL: tools still without typing sound: {still_off}")
    print("  every tool: typing sound ON (confirmed live)")
    if dropped:
        print(f"  note: Retell did not keep enable_typing_sound on {dropped} - "
              f"those are subagent nodes, where the tool-level setting governs.")
    else:
        print("  every tool-calling node: typing sound ON (confirmed live)")


if __name__ == "__main__":
    main()
