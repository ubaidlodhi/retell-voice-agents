"""
V76 - "let me connect you" never strands the caller. DRAFT ONLY.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v76_transfer_on_their_answer.py [--dry-run]

call_70ea8fb9 (outbound v19, 2026-10-07): "Can I speak to a person?" -> "Sure, let me connect you." and
nothing happened; later "I would like to speak to someone." -> "Sure, hold on." -> 30 s of silence ->
the call ended for inactivity. No transfer was ever attempted.
The step's exit to the transfer is judged on the caller's NEXT turn (it is not checked when the step
is entered), and its instruction told it to say "Sure - hold on, let me connect you" - so it promised
the transfer and then waited for the caller, who was waiting for the transfer.
  -> the step never promises the connection; on a repeat ask it asks "shall I connect you now?",
     and a yes to that is a transfer.

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

OLD = "If they clearly insist on a real person, say \"Sure - hold on, let me connect you\" and hand off."
NEW = ("Never say you are connecting them - the transfer starts on their next answer, not on your words. If they "
       "already asked for a person earlier in this call, ask: \"Sure - shall I connect you to the team now?\"")
EDGE_ADD = " Or they say yes to being connected."


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
    h = {x["id"]: x for x in flow["nodes"]}["node-global-human"]
    done = []
    text = h["instruction"]["text"]
    if NEW not in text:
        if text.count(OLD) != 1:
            raise SystemExit("wants-a-person: the connect line moved - merge by hand")
        h["instruction"]["text"] = text.replace(OLD, NEW)
        done.append("wants a person: never promises the connection; repeat ask -> 'shall I connect you now?'")
    tc = [e for e in h["edges"] if e["id"] == "e-human-transfer"][0]["transition_condition"]
    if EDGE_ADD not in tc["prompt"]:
        tc["prompt"] += EDGE_ADD
        done.append("wants a person: a yes to being connected is a transfer")
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
    h = {x["id"]: x for x in out["nodes"]}["node-global-human"]
    assert NEW in h["instruction"]["text"] and OLD not in h["instruction"]["text"]
    assert not out.get("is_published")
    print(f"PATCHED draft flow v{out['version']} - NOT published")


if __name__ == "__main__":
    main()
