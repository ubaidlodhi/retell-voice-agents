"""
V53 - fill the silences, gate the service choice, two plain name questions.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v53_fast_and_frictionless.py [--dry-run] [--publish]

DRAFT ONLY by default. Ubaid's sequencing (2026-09-20): everything lands on the
draft + dev backend first, he tests outbound there, then we publish and port.

Evidence: call_d1fc46c0012c887c86f24ffdb3c (outbound v4, real lead, 2026-09-20).
Booked - but 30 of 98 seconds were dead air, the caller asked "can you hear
me?" four seconds into the first gap, and two things went wrong inside it.

1. SILENT TOOL CALLS                                    (8.1s, 9.1s, 7.9s gaps)
   get_services / get_staff / get_slots ran with speak_during_execution false,
   relying on a typing sound the caller evidently could not hear. The submit
   nodes overrode book_appointment's pinned "Booking that for you now" to
   silence at node level.
   Fix: pinned STATIC lines on get_services and get_slots - generic, short,
   never a name or a service (Ubaid: "checking the availability", not
   "checking Nicky's availability", because most callers name nobody). Static
   rather than prompt-generated: identical result, no extra LLM round trip,
   no chance of a name slipping in. get_staff stays silent (Ubaid's call).
   Node-level speak_during_execution on the four submit/callback nodes so the
   phrases they already carry are actually heard.

2. THE SERVICE WAS INVENTED
   Caller: "I was wondering if Nikki is available at 10."  Aria: "What kind of
   massage...?"  Caller: "Uh, 90 minutes."  -> Aria booked DEEP TISSUE. Nobody
   said deep tissue. Root cause was the catalog arriving empty (backend V53,
   fixed in n8n: the 19KB prod payload tripped Retell's size cap and the model
   received {"success":true,"count":9}); with nothing to offer it guessed.
   Fix: step 1 will not move on without a service named from the menu. A
   duration, a time or a therapist as the answer means ask again with the list.

3. NAME
   "Call. K-A-U-L." / "Last name Book." / she cut in "And your first-" /
   "That is my first name." -> booked firstName Book, lastName Kaul.
   Ubaid's instruction: two plain questions - first name, wait, last name,
   wait. No spelling, no read-back, no confirmation. A slightly wrong name is
   acceptable; the spa fixes those. The goal is the booking. So the V38
   responsiveness override on that node goes too - it was there to survive
   letter-by-letter spelling, which we no longer ask for.

4. TOOL DESCRIPTIONS
   serviceName is a massage type, never a person (the model sent "Nicky").
   get_services now has two modes (catalog / detail) and the description says
   which to call when. get_staff: once per call.
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


# --- 1. what the caller hears while a tool runs -------------------------------
# Generic on purpose. Never a name, never a service.
EXECUTION_LINES = {
    "get_services": "Let me pull that up.",
    "get_slots": "Let me check availability.",
    # get_staff: deliberately silent (Ubaid, 2026-09-20).
}
SPEAKING_NODES = ("node-book-submit", "node-cancel-do", "node-resched-do", "node-handoff-callback")

# --- 4. tool descriptions -------------------------------------------------------
GET_SERVICES_DESC = (
    "The spa's massage menu. With NO serviceName you get the catalog: every service's name, "
    "a one-line description and a price summary - use this to list what we offer or help "
    "someone choose. With a serviceName you get that service's full detail: durations with "
    "prices and variant ids, and its add-ons - call it this way for the chosen service "
    "before get_slots and book_appointment."
)
SERVICE_NAME_DESC = ("A massage type from the menu, e.g. a service name the catalog returned. "
                     "Never a person's name and never a duration.")
GET_STAFF_DESC_SUFFIX = " Call it at most once per call - the answer does not change."

# --- 2. step 1 gate -------------------------------------------------------------
OLD_STEP1_TAIL = (
    "   If they ask what you offer, or you need to list anything: call get_services FIRST, "
    "then say the names it returned in ONE short sentence, all of them, exactly as named. "
    "Do not describe any of them unless they ask. If they are unsure and ask for help "
    "choosing, describe two or three briefly from the descriptions get_services returned."
)
NEW_STEP1_TAIL = (
    "   If they ask what you offer, or you need to list anything: call get_services with NO "
    "serviceName - that returns the menu - then say the names it returned in ONE short "
    "sentence, all of them, exactly as named. Do not describe any of them unless they ask. "
    "If they are unsure and ask for help choosing, describe two or three briefly from the "
    "descriptions it returned.\n"
    "   A duration (\"ninety minutes\"), a time (\"ten AM\") or a therapist's name is NOT a "
    "service. If that is what comes back, keep the detail for later and ask again: \"Sure - "
    "and which massage did you want? I can list them.\" Never pick one for them, never "
    "assume, and do not go to step 2 or call get_slots until they have named a massage from "
    "the menu. Booking a service the caller never chose is the one mistake the readback "
    "cannot reliably catch."
)
OLD_STEP2_HEAD = "2. DURATION AND PRICE. Call get_services for the chosen service, then"
NEW_STEP2_HEAD = ("2. DURATION AND PRICE. Call get_services WITH serviceName set to the chosen "
                  "service - that returns its durations, prices, variant ids and add-ons - then")

# --- 3. name --------------------------------------------------------------------
NAME_INSTRUCTION = """Ask: "Can I get your first name?" Then WAIT.
When they answer, ask: "And your last name?" Then WAIT.

Take whatever they give for each. If they spell it, join the letters into the word (J-O-H-N is John); if they just say it, write it the way it sounds. Do NOT ask them to spell it, do NOT read it back, do NOT ask them to confirm it. A name that is slightly off is fine - the spa tidies those up. A caller asked about their name three times hangs up.

If they give both names in one breath, take both and move on without asking the second question. Two questions at most, then on to the next step."""


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    nodes = {n["id"]: n for n in flow["nodes"]}
    tools = {t["name"]: t for t in flow["tools"]}

    # 1. execution messages
    for name, line in EXECUTION_LINES.items():
        t = tools[name]
        t["speak_during_execution"] = True
        t["execution_message_type"] = "static_text"
        t["execution_message_description"] = line
    tools["get_staff"]["speak_during_execution"] = False
    for nid in SPEAKING_NODES:
        nodes[nid]["speak_during_execution"] = True

    # 4. descriptions
    tools["get_services"]["description"] = GET_SERVICES_DESC
    tools["get_services"]["parameters"]["properties"]["serviceName"]["description"] = SERVICE_NAME_DESC
    if not tools["get_staff"]["description"].endswith(GET_STAFF_DESC_SUFFIX):
        tools["get_staff"]["description"] = tools["get_staff"]["description"].rstrip() + GET_STAFF_DESC_SUFFIX

    # 2. service gate
    disc = nodes["node-book-discovery"]["instruction"]
    for old, new, where in ((OLD_STEP1_TAIL, NEW_STEP1_TAIL, "step 1 tail"),
                            (OLD_STEP2_HEAD, NEW_STEP2_HEAD, "step 2 head")):
        if old not in disc["text"]:
            raise SystemExit(f"{where} not found - the discovery instruction changed shape.")
        disc["text"] = disc["text"].replace(old, new, 1)

    # 3. name
    name = nodes["node-book-name"]
    name["instruction"] = {"type": "prompt", "text": NAME_INSTRUCTION}
    name.pop("responsiveness", None)

    # guards
    for nm in ("get_services", "get_slots"):
        t = tools[nm]
        line = t["execution_message_description"]
        if re.search(r"\b(nicky|rocky|winnie|lily|deep tissue|swedish)\b", line, re.I):
            raise SystemExit(f"{nm} execution line names a person or service: {line!r}")
        if len(line.split()) > 6:
            raise SystemExit(f"{nm} execution line is not short: {line!r}")
    if "spell" in NAME_INSTRUCTION.split("Do NOT ask them to spell")[0].lower().replace("if they spell it", ""):
        raise SystemExit("name node still asks for spelling")
    weekday = re.compile(r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b")
    if weekday.search(disc["text"]) or weekday.search(NAME_INSTRUCTION):
        raise SystemExit("fabricated weekday in a node prompt")
    # Dashboard edits that must survive.
    if flow.get("start_speaker") != "user" or flow.get("begin_after_user_silence_ms") != 6000:
        raise SystemExit("Ubaid's start_speaker/user + 6000ms dashboard edit is not intact.")
    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true")
    args = ap.parse_args()

    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft flow v{live.get('version')} - {len(live['nodes'])} nodes")
    patched = patch(live)
    tools = {t["name"]: t for t in patched["tools"]}
    for nm in ("get_services", "get_staff", "get_slots", "book_appointment"):
        t = tools[nm]
        print(f"  tool {nm:18s} speaks={t.get('speak_during_execution')!s:5s} "
              f"{t.get('execution_message_description')!r}")
    nodes = {n["id"]: n for n in patched["nodes"]}
    print(f"  submit/callback nodes speak: "
          f"{[nodes[n].get('speak_during_execution') for n in SPEAKING_NODES]}")
    print(f"  name node responsiveness override: {nodes['node-book-name'].get('responsiveness')}")
    print(f"  discovery: service gate {'present' if 'is NOT a service' in nodes['node-book-discovery']['instruction']['text'] else 'MISSING'}")

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
    if not args.publish:
        print("  Draft only - real callers still get latest_published.")
        return
    request("POST", f"/publish-agent/{AGENT_ID}")
    print("PUBLISHED")


if __name__ == "__main__":
    main()
