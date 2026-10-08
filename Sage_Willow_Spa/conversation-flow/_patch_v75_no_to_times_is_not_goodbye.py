"""
V75 - a "no" to the times offered keeps the booking going. DRAFT ONLY.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v75_no_to_times_is_not_goodbye.py [--dry-run]

call_828c388a (inbound v28, 2026-10-07): "Today at eleven AM" -> "11 AM isn't open today. What about
1:30, 3, or 6:30?" -> "No. Thank you." The Close global node ("no thanks" = finished) fired from
Discovery and Aria hung up - the caller was turning down three times, not leaving.
  -> Close: a no to something just offered is not a goodbye (condition + 2 negative examples).
  -> Discovery: after a no to the times, ask for another time or day; its give-up exit says so too.

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

CLOSE_ADD = (" Not a \"no\" to a time, day or option you just offered - that turns the offer down; it does not end "
             "the call.")
CLOSE_NEGATIVES = [
    {"transcript": [{"role": "agent", "content": "11 AM isn't open today. What about 1:30, 3, or 6:30?"},
                    {"role": "user", "content": "No. Thank you."}]},
    {"transcript": [{"role": "agent", "content": "I have five this evening open. Does that work?"},
                    {"role": "user", "content": "No, thanks."}]},
]
DISC_ANCHOR = "- A time they name that is open in availabilityByDay: offer it back as a question"
DISC_ADD = ("- A no to the times you offered is not a goodbye: ask what would work instead - \"No problem - is there "
            "another time or day that suits you better?\"\n")
GIVEUP_ADD = " A no to the times offered is not this - ask about another time or day first."


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
    n = {x["id"]: x for x in flow["nodes"]}
    done = []

    g = n["node-close"]["global_node_setting"]
    if CLOSE_ADD not in g["condition"]:
        g["condition"] += CLOSE_ADD
        negs = g.setdefault("negative_finetune_examples", [])
        negs.extend(json.loads(json.dumps(CLOSE_NEGATIVES)))
        done.append("close: a no to an offer is not a goodbye (+2 negative examples)")

    d = n["node-book-discovery"]
    if DISC_ADD not in d["instruction"]["text"]:
        if d["instruction"]["text"].count(DISC_ANCHOR) != 1:
            raise SystemExit("discovery: offer-back line moved - merge by hand")
        d["instruction"]["text"] = d["instruction"]["text"].replace(DISC_ANCHOR, DISC_ADD + DISC_ANCHOR)
        done.append("discovery: after a no to the times, ask for another time or day")
    gu = [e for e in d["edges"] if e["id"] == "e-book-giveup"][0]["transition_condition"]
    if GIVEUP_ADD not in gu["prompt"]:
        gu["prompt"] += GIVEUP_ADD
        done.append("discovery: give-up exit is not a no to the times")
    return flow, done


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
    on = {x["id"]: x for x in out["nodes"]}
    assert CLOSE_ADD in on["node-close"]["global_node_setting"]["condition"]
    assert DISC_ADD in on["node-book-discovery"]["instruction"]["text"]
    assert not out.get("is_published")
    print(f"PATCHED draft flow v{out['version']} - NOT published")


if __name__ == "__main__":
    main()
