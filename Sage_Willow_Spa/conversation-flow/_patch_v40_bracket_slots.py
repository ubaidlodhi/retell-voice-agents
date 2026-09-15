"""
V40 - put the example lines back, but as bracketed slots instead of invented values.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v40_bracket_slots.py [--dry-run]

Ubaid's call (2026-09-14): show the shape with placeholders -

    "You're all set for [Day of the week/Date] at [Time]. Anything else I can help with?"

V39 had deleted the examples outright because the model read the invented one
aloud ("You're all set for Tuesday at 2 PM" when the booking was Monday 10 AM).
Deleting them left the model with no shape to copy; a bracketed slot gives it
the shape back with nothing fabricated to grab. If it ever does copy the example
verbatim, the caller hears an obviously broken placeholder rather than a
confident, wrong appointment - a loud failure instead of a silent one.

Guard added to the global prompt: square brackets mark a slot to fill from real
data and are never read aloud, mirroring the existing rule for curly braces.

Covers every line where Aria states or offers something concrete:
  node-book-confirm, node-resched-done, node-cancel-done, node-book-readback,
  and the two offer lines in node-book-discovery.
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


# -----------------------------------------------------------------------------

CONFIRM = """The booking went through. Say ONE short line, exactly this shape:

    "You're all set for [Day of the week/Date] at [Time].  Anything else I can help with?"

Fill both slots from the booking the tool just confirmed. Nothing else goes in that line - no service, no price, no phone number, no booking ID.

If the caller asks you to repeat it, say the SAME day and time again, word for word. Never a different one."""

RESCHED_DONE = """The move went through. Say ONE short line, exactly this shape:

    "You're moved to [Day of the week/Date] at [Time].  Anything else I can help with?"

Fill both slots from the new appointment the reschedule tool just returned - the new day and time only, nothing about the old one.

If the caller asks you to repeat it, repeat the SAME day and time. Never a different one."""

CANCEL_DONE = """The cancellation went through. Say ONE short line:

    "All set - that's cancelled.  Anything else I can help with?"

Do not re-read the appointment you just cancelled, and never name a day or time here."""

READBACK = """Read the booking back ONCE, in one sentence, exactly this shape:

    "So that's a [Service] for [Duration in hours], [Day of the week/Date] at [Time], [Add-ons if any], [Total] dollars - sound good?"

Fill every slot from what the caller agreed to and what the tools returned in this call. Leave a slot out entirely if you do not have it - never guess at one. Drop the add-ons slot when there are none.

Name the therapist only if the caller specifically asked for one. Do not repeat the phone number - it is already confirmed."""

DISCOVERY_REPLACEMENTS = [
    (
        "call get_slots AGAIN without staffId and offer whoever is free - say they are not "
        "available then, and name a time the second lookup actually returned.",
        "call get_slots AGAIN without staffId and offer whoever is free: "
        "\"They're not free then, but I have [Time from the new lookup]. Want that?\"",
    ),
    (
        "6. OFFER. Give two or three of the times get_slots returned, spread across the day rather "
        "than three in a row - never three slots fifteen minutes apart. Every time you say out loud "
        "must be one the tool returned in this call; there are no example times in these "
        "instructions to fall back on.",
        "6. OFFER. Give two or three of the times get_slots returned, spread across the day - "
        "\"[Time], [Time], or [Time]\" - never three slots fifteen minutes apart. Every time you "
        "say out loud must be one the tool returned in this call.",
    ),
]

OLD_BRACE_RULE = (
    "If a variable ever appears with literal curly braces, treat it as unset. Never read braces or "
    "variable names aloud, and never invent a value for one."
)
NEW_BRACE_RULE = OLD_BRACE_RULE + (
    "\n\nSquare brackets in your instructions mark a slot to fill in, never words to say. "
    "\"[Time]\" means say the actual clock time; it does not mean say \"time\" or \"bracket time\". "
    "If you do not have a real value for a slot, leave it out of the sentence - never read the "
    "bracket, and never put a made-up value in it."
)


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    nodes = {n["id"]: n for n in flow["nodes"]}

    for node_id, text in (("node-book-confirm", CONFIRM),
                          ("node-resched-done", RESCHED_DONE),
                          ("node-cancel-done", CANCEL_DONE),
                          ("node-book-readback", READBACK)):
        if node_id not in nodes:
            raise SystemExit(f"{node_id} missing from the flow.")
        nodes[node_id]["instruction"] = {"type": "prompt", "text": text}

    disc = nodes["node-book-discovery"]["instruction"]
    for old, new in DISCOVERY_REPLACEMENTS:
        if old not in disc["text"]:
            raise SystemExit(f"Discovery text not found: {old[:60]}...")
        disc["text"] = disc["text"].replace(old, new)

    if OLD_BRACE_RULE not in flow["global_prompt"]:
        raise SystemExit("Curly-brace rule not found in the global prompt.")
    flow["global_prompt"] = flow["global_prompt"].replace(OLD_BRACE_RULE, NEW_BRACE_RULE)

    # No invented weekday or clock time may survive anywhere Aria states or offers something.
    bad = re.compile(r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|"
                     r"two PM|one PM|three PM|ten AM|March seventh)\b", re.I)
    for node_id in ("node-book-confirm", "node-resched-done", "node-cancel-done",
                    "node-book-readback", "node-book-discovery"):
        hit = bad.search(nodes[node_id]["instruction"]["text"])
        if hit:
            raise SystemExit(f"{node_id} still carries a fabricated value: {hit.group(0)}")
    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft flow v{live.get('version')} - {len(live['nodes'])} nodes")
    patched = patch(live)
    nodes = {n["id"]: n for n in patched["nodes"]}
    for nid in ("node-book-confirm", "node-resched-done", "node-cancel-done",
                "node-book-readback"):
        line = [l.strip() for l in nodes[nid]["instruction"]["text"].split("\n")
                if l.strip().startswith('"')]
        print(f"  {nid:22s} {line[0][:95] if line else '(no sample line)'}")
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


if __name__ == "__main__":
    main()
