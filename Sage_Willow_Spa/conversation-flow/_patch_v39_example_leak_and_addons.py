"""
V39 - stop the prompt's own examples being spoken as if they were the booking,
and answer "what are those?" instead of repeating the question.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v39_example_leak_and_addons.py [--dry-run]

Evidence: call_f50dc01394bfcfdb4794cefd44d (2026-09-14, agent v6)

1. THE CONFIRMATION READ THE PROMPT'S EXAMPLE ALOUD  (serious)
   Aria: "You're all set for Monday at 10 AM. Anything else I can help with?"
   Ubaid: "Uh, what was that?"
   Aria: "You're all set for TUESDAY AT 2 PM. Anything else I can help with?"
   The booking is Monday 2026-09-14 10:00 (book_appointment returned it).
   node-book-confirm's instruction literally said:
       Say ONE short line - "You're all set for Tuesday at two PM."
   Asked to repeat itself, the model reached for the example instead of the
   booking. The caller now believes a different appointment exists.
   Same failure class as the "$499" pronunciation sample that became a spoken
   price on a live call.
   Fix: every instruction that tells Aria to state a confirmed day, time or
   price now describes the SHAPE in words and carries no concrete values that
   could be read out as fact. Plus an explicit rule: a repeat says the same
   thing, never something new.

2. "WHAT ARE THOSE?" WAS ANSWERED WITH THE SAME QUESTION
   Aria:  "Did you want to add any enhancements?"
   Ubaid: "Um, all right. So what are those?"
   Aria:  "Do you want to add any enhancements?"        <- stonewalled
   Ubaid: "Yeah. So tell me about them."
   Aria:  "You can add aromatherapy, a foot scrub, ..."
   node-book-addons said "Do NOT name a single enhancement until they say yes",
   and the model read a question as not-a-yes.
   Fix: asking what they are IS the cue to name them.

3. THE PRICE LIST WAS READ TWICE
   The log shows "Recovering from false VAD interruption (no ASR words)" at
   t=45 - background noise clipped Aria mid-sentence ("Which length works
   for"), and she then restarted the whole price list even though the caller
   had already said "two hours". He had to answer twice.
   Fix: a turn-taking rule not to restart a clipped turn when the caller has
   already answered, and a lower interruption_sensitivity on the discovery node
   (where the long price and slot readouts happen) so noise clips her less.
   The agent-level default stays at 0.8 for the rest of the call.
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

DISCOVERY_INTERRUPTION_SENSITIVITY = 0.5


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
# Replacements. Each is (node_id or None for global_prompt, old, new).
# None of the new text contains a day, time or price that could be read aloud
# as though it were this caller's booking.
# -----------------------------------------------------------------------------

CONFIRM_NEW = """The booking went through. Say ONE short line: "You're all set for" then the day and the clock time the booking tool just confirmed - nothing else. No service, no price, no phone number, no booking ID. Then ask "Anything else I can help with?"

The day and time come from the tool result you just received. There is no example day or time anywhere in these instructions for you to copy - if you cannot see the confirmed values, say "you're all set" and stop rather than naming a day.

If the caller asks you to repeat it, say the SAME day and time again, word for word. Never a different one."""

RESCHED_DONE_NEW = """The move went through. One short line: "You're moved to" then the new day and clock time the reschedule tool just returned - nothing else. Then ask "Anything else I can help with?"

Those values come from the tool result. There is no example day or time here to copy. If the caller asks you to repeat it, repeat the SAME day and time - never a different one."""

READBACK_NEW = """Read the booking back ONCE, in one sentence, in this order: the service, the duration as hours, the day, the clock time, any add-ons, then the total in dollars. End with "sound good?"

Every one of those values comes from what the caller agreed to and what the tools returned in this call. There are no example values here to copy - if you are missing one, leave it out rather than inventing it.

Name the therapist only if the caller specifically asked for one. Do not repeat the phone number - it is already confirmed."""

ADDONS_NEW = """Ask exactly: "Would you like to add any enhancements?" then STOP and wait.

If they ask what the enhancements are - "what are those?", "like what?", "tell me about them" - that is a question, not a refusal. ANSWER IT: name the ones get_services returned for this service, without prices. Never answer a question by repeating your own question.

Do not name them before they ask or accept. When they pick one, give just that one's price and confirm before adding it. If they decline, or the answer is ambiguous, move on - do not loop.

If get_services returned no add-ons for this service, skip this entirely and move on without mentioning them."""

OLD_TURN_TAKING = (
    'If the caller says "hold on," "give me a moment," "let me check," or "one second" - reply '
    "NO_RESPONSE_NEEDED and stay quiet. Do not say \"okay\" or \"take your time.\""
)
NEW_TURN_TAKING = OLD_TURN_TAKING + (
    "\n\nIf a noise or a stray word cuts you off mid-sentence and the caller then answers the "
    "question you were part-way through asking, TAKE THE ANSWER. Do not start that turn again from "
    "the beginning, and never make them give you the same answer twice - they already said it."
)


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    nodes = {n["id"]: n for n in flow["nodes"]}

    for node_id, text in (
        ("node-book-confirm", CONFIRM_NEW),
        ("node-resched-done", RESCHED_DONE_NEW),
        ("node-book-readback", READBACK_NEW),
        ("node-book-addons", ADDONS_NEW),
    ):
        if node_id not in nodes:
            raise SystemExit(f"{node_id} missing from the flow.")
        nodes[node_id]["instruction"] = {"type": "prompt", "text": text}

    if OLD_TURN_TAKING not in flow["global_prompt"]:
        raise SystemExit("Turn-taking block not found in the global prompt.")
    flow["global_prompt"] = flow["global_prompt"].replace(OLD_TURN_TAKING, NEW_TURN_TAKING)

    nodes["node-book-discovery"]["interruption_sensitivity"] = DISCOVERY_INTERRUPTION_SENSITIVITY

    # No instruction that states a confirmed outcome may carry a sample day/time.
    leak = re.compile(r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b", re.I)
    for node_id in ("node-book-confirm", "node-resched-done", "node-book-readback",
                    "node-cancel-done", "node-book-addons"):
        text = nodes[node_id].get("instruction", {}).get("text", "")
        if leak.search(text):
            raise SystemExit(f"{node_id} still contains a sample weekday: "
                             f"{leak.search(text).group(0)}")
    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft flow v{live.get('version')} - {len(live['nodes'])} nodes")
    patched = patch(live)

    nodes = {n["id"]: n for n in patched["nodes"]}
    print("  node-book-confirm    : example day/time removed")
    print("  node-resched-done    : example day/time removed")
    print("  node-book-readback   : example line removed")
    print("  node-book-addons     : answers \"what are those?\"")
    print(f"  node-book-discovery  : interruption_sensitivity = "
          f"{nodes['node-book-discovery'].get('interruption_sensitivity')} (agent default 0.8)")
    print(f"  node-book-name       : responsiveness = "
          f"{nodes['node-book-name'].get('responsiveness')} (unchanged, from V38)")
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
    back = {n["id"]: n for n in out["nodes"]}
    print(f"  read back: discovery interruption_sensitivity = "
          f"{back['node-book-discovery'].get('interruption_sensitivity')}, "
          f"name responsiveness = {back['node-book-name'].get('responsiveness')}")


if __name__ == "__main__":
    main()
