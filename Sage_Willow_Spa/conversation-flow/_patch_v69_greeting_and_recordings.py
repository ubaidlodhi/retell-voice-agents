"""
V69 - greet right away, and stay quiet through a recording. DRAFT ONLY.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v69_greeting_and_recordings.py [--dry-run]

Nicky's requests (e-mail, 2026-09-30):
  1. "Greet the caller immediately rather than waiting 10 seconds to speak."
     Aria's first word lands ~7 s into every inbound call (calls 2026-09-29/30:
     6.9-8.2 s). Cause: the flow lets the caller speak first and waits for
     begin_after_user_silence_ms = 6000 of silence before the greeting (Ubaid's
     dashboard edit, v13), plus TTS start. Ringing on the Mint line before it
     forwards comes on top and is not ours.
     -> 6000 -> 1000. The caller still gets to speak first: a "hello?" is answered
        at once, silence gets the greeting after one second.
  2. "If she answers an automated recording, wait until the recording finishes."
     Because the caller speaks first, a recording that is already playing holds the
     greeting back. What was missing is what to do with the recording's words once
     they arrive as a turn: Aria would answer them.
     -> global rule beside the "hold on" one: a recorded or automated message is
        not a person - NO_RESPONSE_NEEDED until it ends, then answer whoever speaks.
     The greeting stays uninterruptible (interruption_sensitivity 0, V54 line echo).

No --publish flag on purpose (Ubaid: keep it draft). Tools are left where they are.
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
OLD_SILENCE, NEW_SILENCE = 6000, 1000

HOLD_ON = ("If the caller says \"hold on,\" \"give me a moment,\" \"let me check,\" or \"one second\" - "
           "reply NO_RESPONSE_NEEDED and stay quiet. Do not say \"okay\" or \"take your time.\"")
RECORDING = ("\n\nIf what you hear is a recorded or automated message, not a person - an announcement, "
             "\"this call may be recorded,\" a phone menu (\"press 1 for...\"), a voicemail greeting, or a "
             "recorded sales pitch - reply NO_RESPONSE_NEEDED and stay quiet until it has finished. Do not "
             "talk over it or answer it. When a real person speaks, answer them as usual.")


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
    done = []
    if flow.get("start_speaker") != "user":
        raise SystemExit(f"start_speaker is {flow.get('start_speaker')!r}, expected 'user' - check by hand")
    if flow.get("begin_after_user_silence_ms") != NEW_SILENCE:
        if flow.get("begin_after_user_silence_ms") != OLD_SILENCE:
            raise SystemExit(f"begin_after_user_silence_ms is {flow.get('begin_after_user_silence_ms')} - check by hand")
        flow["begin_after_user_silence_ms"] = NEW_SILENCE
        done.append(f"begin_after_user_silence_ms {OLD_SILENCE} -> {NEW_SILENCE}")
    g = flow["global_prompt"]
    if RECORDING.strip() not in g:
        if g.count(HOLD_ON) != 1:
            raise SystemExit("global prompt: the 'hold on' rule is not where expected - merge by hand")
        flow["global_prompt"] = g.replace(HOLD_ON, HOLD_ON + RECORDING)
        done.append("global prompt: recorded/automated message -> NO_RESPONSE_NEEDED until it ends")
    greet = [x for x in flow["nodes"] if x["id"] == "node-greeting"][0]
    assert greet.get("interruption_sensitivity") == 0, "greeting interruption_sensitivity changed"
    return flow, done


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    if live.get("is_published"):
        raise SystemExit(f"latest flow v{live['version']} is PUBLISHED - make a draft first, never patch the live one")
    patched, done = patch(live)
    print(f"draft flow v{live['version']}: {done or 'nothing to do'}")
    if args.dry_run or not done:
        print("Dry run - Retell not modified." if args.dry_run else "Already up to date.")
        return
    body = {k: v for k, v in patched.items()
            if k not in ("conversation_flow_id", "version", "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    assert out["begin_after_user_silence_ms"] == NEW_SILENCE and RECORDING.strip() in out["global_prompt"]
    assert not out.get("is_published")
    print(f"PATCHED draft flow v{out['version']} - NOT published")


if __name__ == "__main__":
    main()
