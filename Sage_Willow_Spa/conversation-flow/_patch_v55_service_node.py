"""
V55 - the caller names the massage: its own node, with no availability tool.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v55_service_node.py [--dry-run] [--publish]

DRAFT ONLY by default.

Evidence: call_5a05aadf29737a3139238e776d1 (outbound draft v5 = V13, Ubaid's
test, 2026-09-20 17:13 PT). Aria asked "Which massage did you want with Lily?
I can list the options if you're not sure." - the caller said "Uh, 90 minutes."
- and five seconds later she called get_services(serviceName="Swedish
Massage"), then get_slots, and booked a 90-minute Swedish without ever saying
the word to the caller. That is the exact case V53's rule was written for
("a duration is NOT a service ... never pick one for them"), and the model
walked straight past it. The rule sat in step 1 of an 1,100-word instruction
on a node that also owns get_slots, so nothing stopped it from assuming.

Fix: split the discovery node.
  node-book-service   (NEW, subagent, tools: get_services only)
      steps 1-2: which massage, which length/price. Short instruction, the
      rule at the top. It has no get_slots, so it cannot look anything up,
      and its exit edge requires that the CALLER named the massage - with
      finetune examples: "90 minutes" alone stays put.
  node-book-discovery (tools: get_services, get_staff, get_slots)
      steps 3-6 as before: day, part of day, therapist, get_slots, offer.
The "new booking" global trigger and the greeting / FAQ / human "wants to
book" edges now land on the service node. "Try a different time" from the
failure node still goes straight to discovery - the massage is known there.

The outbound builder inherits the new node from the source flow; its own two
booking edges (bad-time-continue, no-form-book) are retargeted in the builder.
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
AGENT_ID = "agent_eceb7448aa1f37e8f436a63a43"
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


SERVICE_NODE = "node-book-service"
DISCOVERY_NODE = "node-book-discovery"

# --- the new node ------------------------------------------------------------
SERVICE_INSTRUCTION = """Find out which massage the caller wants and how long. Warm, brief, two sentences a turn.

THE RULE OF THIS STEP: the caller names the massage - you never do. A length ("ninety minutes"), a time ("ten AM"), a day, a therapist's name or "whatever you recommend" is NOT a massage. If that is what you get, keep the detail for later and ask again: "Sure - and which massage did you want? I can list them." There is no default massage - not Swedish, not anything - and nothing moves forward until they have said one from the menu. Booking a massage the caller never chose is the one mistake the readback cannot reliably catch.

1. SERVICE. If they already named one, take it - do not ask again.
   If they have NOT named one, ask and offer help in the same breath: "What kind of massage are you looking for? I can go over the options if you're not sure." Never the bare question on its own - someone who does not know the menu has to hear that you can read it to them.
   NEVER say a service name aloud until get_services has returned in THIS call. The catalog is whatever the tool says today, no more and no less - reciting it from memory invents services we do not sell.
   If they ask what you offer, or you need to list anything: call get_services with NO serviceName - that returns the menu - then say the names it returned in ONE short sentence, all of them, exactly as named. Do not describe any of them unless they ask. If they are unsure and ask for help choosing, describe two or three briefly from the descriptions it returned.
   Garbled name -> your best guess as a question, then STOP: "Did you mean the Deep Tissue Massage?" A yes to that counts as them choosing it.

2. LENGTH AND PRICE. Once they have named a massage, call get_services WITH serviceName set to it - that returns its durations, prices, variant ids and add-ons - then offer the durations and prices in ONE line and ask which: "Deep Tissue is ninety for an hour, one thirty for ninety minutes, one eighty for two hours - which works?" Speak durations as hours, never raw minutes. NEVER ask whether they already know the length. NEVER mention add-ons here. If they gave the length before the massage, confirm that length's price in a few words instead of asking again.

COUPLES MASSAGE: one massage, for the caller only. Mention we have a dedicated couples room. You may ask ONCE "any preference for your partner's massage?" - whatever they say, acknowledge in three words and remember it for the notes.

Once the massage and the length are both settled, ask what day they want to come in - "What day works for you?" - and stop there. No morning-or-afternoon question, no name, no number: you have no availability tool and no booking tool in this step."""

CHOSEN_CONDITION = (
    "The caller has chosen a massage from the menu AND a length. The massage must come from the "
    "caller - they said its name, or said yes when the agent asked \"did you mean the X massage?\". "
    "A length alone, a time, a day, a therapist's name or \"whatever you recommend\" is NOT a chosen "
    "massage, and the agent naming one on the caller's behalf does not count."
)
GIVEUP_CONDITION = "The caller says they no longer want to book anything right now."

ASK = "What kind of massage are you looking for? I can go over the options if you're not sure."
PRICES = "Deep Tissue is ninety for an hour, one thirty for ninety minutes, one eighty for two hours - which works?"
TRANSITION_EXAMPLES = [
    # -> discovery: named it, picked a length
    {"id": "ft-svc-named-and-length", "destination_node_id": DISCOVERY_NODE, "transcript": [
        {"role": "agent", "content": ASK},
        {"role": "user", "content": "Deep tissue."},
        {"role": "agent", "content": PRICES},
        {"role": "user", "content": "The ninety minutes."}]},
    # -> discovery: both in one breath
    {"id": "ft-svc-both-at-once", "destination_node_id": DISCOVERY_NODE, "transcript": [
        {"role": "user", "content": "Can I book a ninety minute deep tissue for Monday?"}]},
    # -> discovery: yes to the agent's best guess counts as naming it
    {"id": "ft-svc-confirmed-guess", "destination_node_id": DISCOVERY_NODE, "transcript": [
        {"role": "agent", "content": "Did you mean the Deep Tissue Massage?"},
        {"role": "user", "content": "Yes, for an hour."}]},
    # stay: a length is not a massage
    {"id": "ft-svc-length-only", "transcript": [
        {"role": "agent", "content": ASK},
        {"role": "user", "content": "Uh, ninety minutes."}]},
    # stay: a therapist and a time are not a massage
    {"id": "ft-svc-therapist-time", "transcript": [
        {"role": "agent", "content": ASK},
        {"role": "user", "content": "I was wondering if Lily is available at ten."}]},
    # stay: asking for the menu
    {"id": "ft-svc-menu", "transcript": [
        {"role": "agent", "content": ASK},
        {"role": "user", "content": "What do you have?"}]},
    # stay: named but no length yet
    {"id": "ft-svc-named-no-length", "transcript": [
        {"role": "agent", "content": ASK},
        {"role": "user", "content": "The hot stone one."}]},
]

# --- discovery: steps 1-2 come out ---------------------------------------------------
OLD_DISCOVERY_HEAD_START = "1. SERVICE. If they already named one, take it."
OLD_DISCOVERY_HEAD_END = "\n\n3. DAY AND TIME."
NEW_DISCOVERY_HEAD = (
    "The massage and the length were settled in the previous step - take them from the "
    "conversation exactly as the caller chose them, and call get_services WITH that serviceName "
    "if you still need its serviceId or variant. If the caller changes their mind, switch only "
    "to a massage they name themselves - never pick one for them."
)
RENUMBER = [
    ("\n\n3. DAY AND TIME.", "\n\n1. DAY AND TIME."),
    ("\n\n4. THERAPIST.", "\n\n2. THERAPIST."),
    ("\n\n5. LOOK UP TIMES.", "\n\n3. LOOK UP TIMES."),
    ("\n\n6. OFFER.", "\n\n4. OFFER."),
    ("Clock times come later, at step 6, after they have chosen one.",
     "Clock times come later, at step 4, after they have chosen one."),
    ("A re-check request is covered by the RE-CHECK RULE in step 5.",
     "A re-check request is covered by the RE-CHECK RULE in step 3."),
]
OLD_COUPLES = (
    "COUPLES MASSAGE: book ONE appointment, for the caller only. One service, one slot search, "
    "one booking. Mention we have a dedicated couples room. You may ask ONCE \"any preference for "
    "your partner's massage?\" - whatever they say, acknowledge in three words and remember it for "
    "the notes. Never run a second get_slots, never book twice, and never say \"each guest can pick "
    "any massage type.\" Report only the search you actually ran."
)
NEW_COUPLES = (
    "COUPLES MASSAGE: ONE appointment, for the caller only - one slot search, one booking. Never "
    "run a second get_slots, never book twice, and never say \"each guest can pick any massage "
    "type.\" Report only the search you actually ran."
)

# --- edges that used to start a booking at discovery -------------------------------
RETARGET = {"e-greet-book", "e-faq-book", "e-human-book"}

# --- tool descriptions: the decision point itself ---------------------------------
GET_SERVICES_SERVICE_NAME = (
    "The massage the caller chose, by name, in this call - e.g. a service name the catalog "
    "returned. Leave it out to get the menu. Never a person's name, never a duration, and never "
    "a guess: if the caller has not named a massage yet, ask them."
)
GET_SLOTS_SERVICE_NAME = (
    "The massage the caller chose by name in this call, spoken naturally (e.g. 'Deep Tissue "
    "Massage'). The backend resolves this against the live catalog, so slight wording differences "
    "are fine. Never one you picked for them."
)


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    nodes = {n["id"]: n for n in flow["nodes"]}
    if SERVICE_NODE in nodes:
        raise SystemExit(f"{SERVICE_NODE} already exists - V55 applied already?")
    disc = nodes[DISCOVERY_NODE]
    if disc["type"] != "subagent" or "global_node_setting" not in disc:
        raise SystemExit("discovery node changed shape (expected a subagent with the booking trigger).")

    # 1. the new node, placed one column left of discovery
    pos = disc["display_position"]
    service = {
        "id": SERVICE_NODE,
        "name": "Booking - Service & Length",
        "type": "subagent",
        "tool_ids": ["get_services"],
        "instruction": {"type": "prompt", "text": SERVICE_INSTRUCTION},
        "interruption_sensitivity": disc.get("interruption_sensitivity", 0.5),
        "enable_typing_sound": True,
        "skippable": False,
        "display_position": {"x": pos["x"] - 520, "y": pos["y"]},
        "edges": [
            {"id": "e-service-chosen", "destination_node_id": DISCOVERY_NODE,
             "transition_condition": {"type": "prompt", "prompt": CHOSEN_CONDITION}},
            {"id": "e-service-giveup", "destination_node_id": "node-greeting",
             "transition_condition": {"type": "prompt", "prompt": GIVEUP_CONDITION}},
        ],
        "finetune_transition_examples": TRANSITION_EXAMPLES,
        # The "new booking" trigger moves here, examples and all.
        "global_node_setting": disc.pop("global_node_setting"),
    }
    flow["nodes"].append(service)
    nodes[SERVICE_NODE] = service

    # 2. discovery loses steps 1-2
    text = disc["instruction"]["text"]
    a = text.find(OLD_DISCOVERY_HEAD_START)
    b = text.find(OLD_DISCOVERY_HEAD_END)
    if a < 0 or b < 0 or b < a:
        raise SystemExit("discovery steps 1-2 not where expected - instruction changed shape.")
    text = text[:a] + NEW_DISCOVERY_HEAD + text[b:]
    for old, new in RENUMBER:
        if text.count(old) != 1:
            raise SystemExit(f"renumber anchor not found exactly once: {old[:50]!r}")
        text = text.replace(old, new)
    if text.count(OLD_COUPLES) != 1:
        raise SystemExit("couples paragraph changed shape")
    text = text.replace(OLD_COUPLES, NEW_COUPLES)
    disc["instruction"]["text"] = text

    # 3. bookings start at the service node
    hit = set()
    for n in flow["nodes"]:
        for e in n.get("edges", []):
            if e["id"] in RETARGET:
                if e["destination_node_id"] != DISCOVERY_NODE:
                    raise SystemExit(f"{e['id']} no longer points at discovery")
                e["destination_node_id"] = SERVICE_NODE
                hit.add(e["id"])
    if hit != RETARGET:
        raise SystemExit(f"booking edges missing: {RETARGET - hit}")

    # 4. tool descriptions
    tools = {t["name"]: t for t in flow["tools"]}
    tools["get_services"]["parameters"]["properties"]["serviceName"]["description"] = GET_SERVICES_SERVICE_NAME
    tools["get_slots"]["parameters"]["properties"]["serviceName"]["description"] = GET_SLOTS_SERVICE_NAME

    # guards
    ids = [n["id"] for n in flow["nodes"]]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate node id")
    edge_ids = []
    for n in flow["nodes"]:
        edge_ids += [e["id"] for e in n.get("edges", [])]
        edge_ids += [n[k]["id"] for k in ("else_edge", "always_edge", "skip_response_edge", "edge") if n.get(k)]
    if len(edge_ids) != len(set(edge_ids)):
        raise SystemExit("duplicate edge id")
    for n in flow["nodes"]:
        for e in n.get("edges", []) + [n[k] for k in ("else_edge", "always_edge", "skip_response_edge", "edge") if n.get(k)]:
            if e["destination_node_id"] not in nodes:
                raise SystemExit(f"dangling edge {e['id']} -> {e['destination_node_id']}")
    for ex in TRANSITION_EXAMPLES:
        if ex.get("destination_node_id") not in (None, DISCOVERY_NODE):
            raise SystemExit("transition example points somewhere odd")
    if "get_slots" in service["tool_ids"] or "book_appointment" in service["tool_ids"]:
        raise SystemExit("the service node must not be able to look up or book")
    if "global_node_setting" in disc:
        raise SystemExit("discovery still carries the booking trigger")
    d = disc["instruction"]["text"]
    if "1. SERVICE." in d or "2. DURATION AND PRICE." in d or "1. DAY AND TIME." not in d or "4. OFFER." not in d:
        raise SystemExit("discovery instruction did not renumber cleanly")
    if re.search(r"\bstep [56]\b", d):
        raise SystemExit("stale step reference in discovery")
    weekday = re.compile(r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b")
    if weekday.search(SERVICE_INSTRUCTION):
        raise SystemExit("fabricated weekday in the service node")
    if len(SERVICE_INSTRUCTION.split()) > 520:
        raise SystemExit("service instruction is getting long")
    # Earlier work that must survive.
    if flow.get("start_speaker") != "user" or flow.get("begin_after_user_silence_ms") != 6000:
        raise SystemExit("Ubaid's start_speaker/user + 6000ms dashboard edit is not intact.")
    if nodes["node-greeting"].get("interruption_sensitivity") != 0:
        raise SystemExit("V54 greeting setting missing")
    if "plays your own voice back to you" not in flow["global_prompt"]:
        raise SystemExit("V54 echo rule missing")
    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true")
    args = ap.parse_args()

    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft flow v{live.get('version')} - {len(live['nodes'])} nodes")
    patched = patch(live)
    nodes = {n["id"]: n for n in patched["nodes"]}
    print(f"  {len(patched['nodes'])} nodes; {SERVICE_NODE} tools={nodes[SERVICE_NODE]['tool_ids']}, "
          f"{len(TRANSITION_EXAMPLES)} transition examples")
    print(f"  discovery tools={nodes[DISCOVERY_NODE]['tool_ids']}, "
          f"instruction {len(live['nodes'][[n['id'] for n in live['nodes']].index(DISCOVERY_NODE)]['instruction']['text'])} -> "
          f"{len(nodes[DISCOVERY_NODE]['instruction']['text'])} chars")
    starts = [(n["id"], e["id"]) for n in patched["nodes"] for e in n.get("edges", []) if e["destination_node_id"] == SERVICE_NODE]
    print(f"  booking now starts from: {starts}")

    SNAPSHOT.write_text(json.dumps(patched, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"snapshot -> {SNAPSHOT.name}")
    if args.dry_run:
        print("Dry run - Retell not modified.")
        return

    body = {k: v for k, v in patched.items()
            if k not in ("conversation_flow_id", "version",
                         "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    back = {n["id"]: n for n in out["nodes"]}
    if SERVICE_NODE not in back or back[SERVICE_NODE]["tool_ids"] != ["get_services"] \
            or "global_node_setting" in back[DISCOVERY_NODE] \
            or len(back[SERVICE_NODE].get("finetune_transition_examples", [])) != len(TRANSITION_EXAMPLES):
        raise SystemExit("read-back mismatch after PATCH")
    print(f"PATCHED draft flow v{out.get('version')} (NOT published)")
    if not args.publish:
        print("  Draft only - real callers still get latest_published.")
        return
    request("POST", f"/publish-agent/{AGENT_ID}")
    print("PUBLISHED")


if __name__ == "__main__":
    main()
