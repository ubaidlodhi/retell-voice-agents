"""
V61 - a re-checked time or therapist must not change the price in the readback.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v61_readback_price.py [--dry-run]

Evidence (V59 mocked run, therapist raised at the enhancements question): after
the detour back to discovery the readback said "five PM with Nicky, one hundred
thirty dollars" for a ONE-hour Signature Massage - $130 is the ninety-minute
price; book_appointment itself carried the 60-minute variant. Only the re-entry
path did this. One sentence in the readback node pins where the total comes from.
Draft only; published together with V59 + V60.
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

OLD = 'Write the total as words with "dollars" on the end'
NEW = ('The total is the price get_services gave for the length they chose, plus any add-ons they took - '
       're-checking the time or the therapist never changes it.\n\n' + OLD)


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
    with urllib.request.urlopen(req, timeout=120) as resp:
        text = resp.read().decode()
        return json.loads(text) if text.strip() else {}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    flow = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    node = next(n for n in flow["nodes"] if n["id"] == "node-book-readback")
    text = node["instruction"]["text"]
    if "re-checking the time or the therapist never changes it" in text:
        raise SystemExit("already applied")
    if text.count(OLD) != 1:
        raise SystemExit("readback total sentence changed shape")
    node["instruction"]["text"] = text.replace(OLD, NEW)
    if "Do you want to book a massage?" not in json.dumps(flow["nodes"]):
        raise SystemExit("V59 not on the draft")
    SNAPSHOT.write_text(json.dumps(flow, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"draft v{flow['version']}: readback gains the price rule")
    if args.dry_run:
        return
    body = {k: v for k, v in flow.items()
            if k not in ("conversation_flow_id", "version", "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    back = next(n for n in out["nodes"] if n["id"] == "node-book-readback")["instruction"]["text"]
    if NEW not in back:
        raise SystemExit("read-back mismatch")
    print(f"PATCHED draft flow v{out['version']} (not published)")


if __name__ == "__main__":
    main()
