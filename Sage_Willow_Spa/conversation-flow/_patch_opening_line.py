"""
Patch the INBOUND Aria flow's opening line to an assumptive booking question.

Run:  py -X utf8 conversation-flow/_patch_opening_line.py [--dry-run]

    was:  "Hi, this is Aria from Sage and Willow Spa. How can I help you today?"
    now:  "Hi, this is Aria from Sage and Willow Spa. Are you looking to book a massage today?"

Why the greeting needed more than a one-line swap
-------------------------------------------------
"How can I help you today?" is open, so the caller's first turn always names an
intent and the routing edges have something to match on. An assumptive question
invites a bare "yes" or "no", which those edges were never written to catch:

  * "yes" has to reach node-book-discovery, so the booking edge now says so
    explicitly. Without this the model can sit in the greeting re-asking.
  * "no" has to fall back to an open question rather than dead-ending, so the
    instruction handles it in one turn.

node-book-discovery opens with "SERVICE. If they already named one, take it."
so a caller who answers with a service name is not asked twice.

This edits the flow DRAFT. The DID serves the published agent version, so
nothing changes for live callers until the agent is republished in the
dashboard.
"""

from __future__ import annotations
import argparse
import json
import os
import urllib.request
from pathlib import Path

RETELL_BASE = "https://api.retellai.com"
FLOW_ID = "conversation_flow_bdb1968b28ed"
FLOW_VERSION = 3

OLD_LINE = '"Hi, this is Aria from Sage and Willow Spa. How can I help you today?"'
NEW_LINE = '"Hi, this is Aria from Sage and Willow Spa. Are you looking to book a massage today?"'

OLD_HEARME = '-> "Yep, I can hear you - what can I do for you?"'
NEW_HEARME = '-> "Yep, I can hear you - are you looking to book a massage today?"'

ANCHOR = ("After that you have already introduced yourself. NEVER say that line "
          "again, in whole or in part. Repeating it makes you sound broken.")

ANSWER_HANDLING = """

The opening is a yes/no question, so handle both answers here:
- **Yes**, or any affirmative - go straight to booking. Do NOT then ask "what can I do for you?"; they have already told you.
- **They name a massage** - that IS a yes. Take it straight to booking; do not confirm it back first.
- **No, or they want something else** - ask once, plainly: "Sure - what can I do for you?" Then route on their answer.
- **They ask a question instead of answering** - answer it, then carry on. Do not repeat the opening question at them."""

OLD_BOOK_EDGE = ("Caller wants to book, make, or set up a massage appointment - "
                 "including a couples massage.")
NEW_BOOK_EDGE = ("Caller wants to book, make, or set up a massage appointment - "
                 "including a couples massage. This ALSO fires on a bare yes or any "
                 "other affirmative reply to the opening question about booking a "
                 "massage today, and on a reply that simply names a massage.")


def api_key() -> str:
    key = os.environ.get("RETELL_API_KEY")
    if key:
        return key
    mcp = Path(__file__).resolve().parents[2] / ".mcp.json"
    if mcp.exists():
        raw = mcp.read_text(encoding="utf-8")
        cfg = json.loads(raw[raw.index("{"):])
        for arg in cfg.get("mcpServers", {}).get("retell", {}).get("args", []):
            if arg.startswith("Authorization:Bearer "):
                return arg.split("Bearer ", 1)[1].strip()
    raise SystemExit("No Retell API key. Set RETELL_API_KEY or configure .mcp.json.")


def request(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        f"{RETELL_BASE}{path}", data=data, method=method,
        headers={"Authorization": f"Bearer {api_key()}",
                 "Content-Type": "application/json", "User-Agent": "curl/8.0"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise SystemExit(
            f"Retell API {method} {path} -> {exc.code}: {exc.read().decode('utf-8','replace')}"
        ) from None


def patch(flow: dict) -> dict:
    for key in ("conversation_flow_id", "version", "last_modification_timestamp", "is_published"):
        flow.pop(key, None)

    nodes = {n["id"]: n for n in flow["nodes"]}
    greeting = nodes["node-greeting"]
    text = greeting["instruction"]["text"]

    for needle in (OLD_LINE, OLD_HEARME, ANCHOR):
        if needle not in text:
            raise SystemExit(f"Greeting no longer contains expected text: {needle[:60]!r}")

    text = text.replace(OLD_LINE, NEW_LINE)
    text = text.replace(OLD_HEARME, NEW_HEARME)
    text = text.replace(ANCHOR, ANCHOR + ANSWER_HANDLING, 1)
    greeting["instruction"]["text"] = text

    booking_edges = [e for e in greeting["edges"]
                     if e["destination_node_id"] == "node-book-discovery"]
    if len(booking_edges) != 1:
        raise SystemExit(f"Expected 1 booking edge off the greeting, found {len(booking_edges)}.")
    if booking_edges[0]["transition_condition"]["prompt"] != OLD_BOOK_EDGE:
        raise SystemExit("Booking edge condition is not the expected text.")
    booking_edges[0]["transition_condition"]["prompt"] = NEW_BOOK_EDGE

    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    flow = request("GET", f"/get-conversation-flow/{FLOW_ID}?version={FLOW_VERSION}")
    print(f"Fetched inbound flow v{FLOW_VERSION} ({len(flow['nodes'])} nodes)")

    flow = patch(flow)
    out = Path(__file__).parent / "aria_inbound_flow_patched.json"
    out.write_text(json.dumps(flow, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote {out.name}")
    print(f"  new opening: {NEW_LINE}")

    if args.dry_run:
        print("Dry run - Retell not modified.")
        return

    result = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", flow)
    print(f"Updated flow {result['conversation_flow_id']} v{result['version']}")
    print("  DRAFT ONLY - the DID serves the published agent version.")
    print("  Publish the inbound agent in the dashboard to put this live.")


if __name__ == "__main__":
    main()
