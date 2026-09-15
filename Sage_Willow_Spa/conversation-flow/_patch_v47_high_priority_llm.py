"""
V47 - put the flow on Retell's high-priority LLM pool.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v47_high_priority_llm.py [--dry-run|--revert]

Ubaid, 2026-09-14, on call_8bf77109baa4d0ddb466bd83a05: the pause before
"Let me find that booking" felt like 6-8 seconds and he wants it faster.

What the log actually shows (call starts 12:10:16.359):

    t=09.75 - 14.91   caller speaking: "Um, it's in the I-I want to cancel-"
    t=15.46           first LLM call   (+0.55s: endpointing + ASR finalise)
    t=17.60           second LLM call  (+2.14s)  <- the whole delay is here
    t=18.15           audio starts: "Let me find that booking."

So the gap between the caller stopping and Aria starting is 3.24s, matching
Retell's own e2e figure of 3240ms for that turn - not 6-8. Roughly five of the
seconds he felt were his own hesitating speech. Endpointing is already fast at
0.55s, so `responsiveness` is not the lever here and raising it would only make
her talk over that kind of hesitation.

The 2.14s is one LLM round trip: the routing pass that weighs the turn against
14 global-node conditions and their 40 finetune examples. Every later turn in
the same call ran that pass in ~0.5s (e2e 1720-1821ms), which points at a cold
prompt cache on the first substantive turn rather than anything in the flow.

`high_priority` gives that pass more dedicated capacity and is the one lever
that costs no behaviour: same model, same prompts, same routing. NOTE it may
carry a premium on the Retell plan - `--revert` puts it back.

Not done here, because it is a judgement call and not mine to make: moving off
gpt-4.1. gpt-4.1-mini or gemini-3.5-flash would cut both passes considerably,
but every prompt in this flow has been tuned against gpt-4.1's behaviour over
many calls, so it needs a deliberate decision and a round of testing.
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
    ap.add_argument("--revert", action="store_true",
                    help="put high_priority back to false")
    args = ap.parse_args()

    want = not args.revert

    flow = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft flow v{flow.get('version')}")
    choice = dict(flow.get("model_choice") or {})
    if not choice.get("model"):
        raise SystemExit("No model_choice on this flow - nothing to tune.")
    print(f"  before: {json.dumps(choice)}")

    # The model itself is deliberately untouched.
    model_before = choice["model"]
    choice["high_priority"] = want
    flow["model_choice"] = choice
    print(f"  after:  {json.dumps(choice)}")

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
    live = after.get("model_choice") or {}
    print(f"PATCHED draft flow v{after.get('version')} (NOT published)")
    print(f"  read back: {json.dumps(live)}")
    if live.get("high_priority") is not want:
        raise SystemExit(f"FAIL: Retell did not keep high_priority={want} "
                         f"(got {live.get('high_priority')!r})")
    if live.get("model") != model_before:
        raise SystemExit(f"FAIL: the model changed from {model_before} to {live.get('model')}")
    print(f"  high_priority = {want} (confirmed live), model unchanged: {live['model']}")


if __name__ == "__main__":
    main()
