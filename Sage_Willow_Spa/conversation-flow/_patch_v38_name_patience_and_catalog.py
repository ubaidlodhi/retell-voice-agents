"""
V38 - stop cutting the caller off mid-spelling, and stop reciting a service
catalog the agent has not looked up.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v38_name_patience_and_catalog.py [--dry-run]

Evidence: call_1dd2cfefe7984784ff302c4b2e3 (2026-09-14, agent v6)

1. NAME SPELLING CUT OFF
   Aria: "Can you spell your first and last name for me?"   113.18 - 115.69
   Ubaid: "Yeah, it's U-B-A-I-D."                           118.23 - 119.67
   Ubaid: "Uh, T-E-S-T,"                                    121.11 - 122.34
   Ubaid: "Ubaid test."                                     122.34 - 122.55
   Aria:  "And is your number 253-268-1856?"                124.27
   The node transition fired at t=122.70 - the agent had already decided the
   turn was over while the last phrase was still being said. Cause: the agent's
   `responsiveness` is 0.8 (high = short wait before replying). Spelling comes
   out in chunks with pauses, so a high setting clips it.
   Fix: conversation-flow nodes accept per-node overrides, so the name node
   alone gets `responsiveness: 0.25` - patient where it matters, without
   slowing every other turn of the call.

2. SERVICE CATALOG RECITED FROM MEMORY, WITH AN INVENTED SERVICE
   Aria at t=9.83: "We have Swedish, deep tissue, sports, prenatal, and
   lymphatic drainage." get_services was not called until t=34.5.
   The real catalog is Signature, Swedish, Deep Tissue, Hot Stone, Prenatal,
   Lymphatic Drainage, 30-Minute Focus. So "sports" does not exist, and four
   real services were left out. A caller can book nothing called "sports," and
   Signature is the spa's most popular service.
   Fix: the discovery node and the global prompt now forbid saying ANY service
   name before get_services has returned in this call.

3. UNSOLICITED DESCRIPTION
   Ubaid: "Um, damn fatty drainage."  (garbled)
   Aria: "Did you mean lymphatic drainage? It's a gentle massage focused on
   reducing swelling and boosting circulation."
   He asked for a massage, not a definition. The global prompt already says
   "Never volunteer information," but the garbled-word rule did not say the
   confirmation must be the whole turn.
   Fix: the garbled-service rule now ends the turn at the question mark.
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

NAME_RESPONSIVENESS = 0.25


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


# -----------------------------------------------------------------------------

NAME_INSTRUCTION = """Ask: "Can you spell your first and last name for me?" Then WAIT.

People spell in chunks with gaps - first name, a pause, then the last name, and often the whole name said normally afterwards. Let them finish. Never start your next sentence while they are still spelling, and never treat the first chunk as the whole answer.

You need BOTH a first and a last name. If they gave only one, ask "And your last name?" once, then wait again.

Join spelled letters into the word: U-B-A-I-D is Ubaid. Capture what you hear and move on - do NOT read the name back and do NOT ask them to confirm the spelling."""

OLD_SERVICE_STEP = (
    "1. SERVICE. If they already named one, take it. If they ask what you offer, call get_services "
    "and say the names in ONE short sentence - do not describe any of them unless they ask. If they "
    "are unsure and ask for help choosing, describe two or three briefly from the descriptions "
    "get_services returns."
)
NEW_SERVICE_STEP = (
    "1. SERVICE. If they already named one, take it.\n"
    "   NEVER say a service name aloud until get_services has returned in THIS call. You do not know "
    "the catalog - it is whatever the tool says today, no more and no less. Reciting it from memory "
    "invents services we do not sell and leaves out ones we do.\n"
    "   If they ask what you offer, or you need to list anything: call get_services FIRST, then say "
    "the names it returned in ONE short sentence, all of them, exactly as named. Do not describe any "
    "of them unless they ask. If they are unsure and ask for help choosing, describe two or three "
    "briefly from the descriptions get_services returned."
)

OLD_GARBLED = (
    '- Garbled service -> "Did you mean the Deep Tissue Massage?" ("dip tissue"); '
    '"Did you mean Lymphatic Drainage?" ("lim-pa-tic," "post-op massage").'
)
NEW_GARBLED = (
    '- Garbled service -> name your best guess and STOP: "Did you mean the Deep Tissue Massage?" '
    '("dip tissue"); "Did you mean Lymphatic Drainage?" ("lim-pa-tic," "post-op massage"). '
    'The question is the whole turn - do not explain what the massage is, what it helps with, or '
    'what it costs. They asked for a massage, not a definition. Only guess at a name get_services '
    'actually returned.'
)


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    nodes = {n["id"]: n for n in flow["nodes"]}

    # 1. patience on the name node only
    name = nodes["node-book-name"]
    name["instruction"] = {"type": "prompt", "text": NAME_INSTRUCTION}
    name["responsiveness"] = NAME_RESPONSIVENESS

    # 2. never recite the catalog
    disc = nodes["node-book-discovery"]["instruction"]
    if OLD_SERVICE_STEP not in disc["text"]:
        raise SystemExit("Discovery step 1 not found - the instruction changed shape.")
    disc["text"] = disc["text"].replace(OLD_SERVICE_STEP, NEW_SERVICE_STEP)

    # 3. confirming a garbled name is the whole turn
    if OLD_GARBLED not in flow["global_prompt"]:
        raise SystemExit("Garbled-service line not found in the global prompt.")
    flow["global_prompt"] = flow["global_prompt"].replace(OLD_GARBLED, NEW_GARBLED)

    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft flow v{live.get('version')} - {len(live['nodes'])} nodes")
    patched = patch(live)

    nn = next(n for n in patched["nodes"] if n["id"] == "node-book-name")
    print(f"  node-book-name responsiveness: {nn.get('responsiveness')} "
          f"(agent default stays 0.8)")
    print(f"  discovery step 1 rewritten, garbled-service rule tightened")
    print(f"  global_prompt {len(live['global_prompt'])} -> {len(patched['global_prompt'])} chars")

    SNAPSHOT.write_text(json.dumps(patched, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"snapshot -> {SNAPSHOT.name}")
    if args.dry_run:
        print("Dry run - Retell not modified.")
        return

    body = {k: v for k, v in patched.items()
            if k not in ("conversation_flow_id", "version",
                         "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    print(f"PATCHED draft flow v{out.get('version')} (NOT published)")
    saved = next(n for n in out["nodes"] if n["id"] == "node-book-name")
    print(f"  read back: node-book-name responsiveness = {saved.get('responsiveness')}")


if __name__ == "__main__":
    main()
