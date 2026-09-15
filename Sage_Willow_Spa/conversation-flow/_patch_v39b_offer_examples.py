"""
V39b - the last two fabricated clock times left inside the discovery prompt.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v39b_offer_examples.py [--dry-run]

V39 cleared the sample day/time out of every node that STATES a confirmed
outcome. This clears the two that remained in the node that OFFERS times:

    "They're not free then, but I have two PM. Want that?"
    Give two or three of the returned times, spread apart - "ten, noon, or three"

call_f50dc01394bfcfdb4794cefd44d proved the model will read a prompt example
aloud as though it were real ("You're all set for Tuesday at 2 PM" when the
booking was Monday 10 AM). A fabricated availability is the same hazard: the
caller is told a slot exists that was never in get_slots.

The price example in step 2 ("Deep Tissue is ninety for an hour, one thirty for
ninety minutes, one eighty for two hours") is deliberately LEFT ALONE - those
are the real live figures for that service (90 / 130 / 180), so if it ever gets
read aloud verbatim it is still true.
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

REPLACEMENTS = [
    (
        "call get_slots AGAIN without staffId and offer whoever is free: "
        "\"They're not free then, but I have two PM. Want that?\"",
        "call get_slots AGAIN without staffId and offer whoever is free - say they are not "
        "available then, and name a time the second lookup actually returned.",
    ),
    (
        "6. OFFER. Give two or three of the returned times, spread apart - \"ten, noon, or three,\" "
        "never \"ten, ten fifteen, ten thirty.\"",
        "6. OFFER. Give two or three of the times get_slots returned, spread across the day rather "
        "than three in a row - never three slots fifteen minutes apart. Every time you say out loud "
        "must be one the tool returned in this call; there are no example times in these "
        "instructions to fall back on.",
    ),
]


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
    print(f"draft flow v{flow.get('version')} - {len(flow['nodes'])} nodes")
    disc = next(n for n in flow["nodes"] if n["id"] == "node-book-discovery")
    text = disc["instruction"]["text"]
    for old, new in REPLACEMENTS:
        if old not in text:
            raise SystemExit(f"Not found in the discovery instruction: {old[:60]}...")
        text = text.replace(old, new)
    disc["instruction"]["text"] = text

    clock = re.compile(r"\b(two PM|one PM|three PM|ten AM|noon)\b", re.I)
    left = clock.findall(text)
    print(f"  discovery: fabricated clock times remaining -> {left or 'none'}")
    if left:
        raise SystemExit("A sample clock time survived the rewrite.")

    SNAPSHOT.write_text(json.dumps(flow, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"snapshot -> {SNAPSHOT.name}")
    if args.dry_run:
        print("Dry run - Retell not modified.")
        return

    body = {k: v for k, v in flow.items()
            if k not in ("conversation_flow_id", "version",
                         "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    print(f"PATCHED draft flow v{out.get('version')} (NOT published)")


if __name__ == "__main__":
    main()
