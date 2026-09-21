"""
V58 - both names spelled, no read-back; a silent line ends after 50 s.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v58_spell_names.py [--dry-run] [--publish]

DRAFT ONLY by default. --publish also publishes the inbound agent.

Evidence (Nicky, 2026-09-22, "still need train for the names"):
call_d1fc46c0012c887c86f24ffdb3c (outbound v4, real lead, 2026-09-20 09:42 PT)
    Aria:   Can you spell your first and last name for me?
    Caller: Call. K-A-U-L.
    Caller: Last name Book.
    Aria:   And your first
    Caller: That is my first name.
    -> book_appointment firstName "Book", lastName "Kaul"   (swapped)
One question for two names invites exactly that. V53 split it into two plain
questions with no spelling; Ubaid now wants the spelling asked for on each -
"spell your first name", then "spell your last name" - and still no
confirmation read-back (2026-09-22).

Also (Nicky: "no need to wait almost 3 mins"): call_b004eecd765b2feed08836f06a3
sat for 149 s - echo (fixed in V54) plus two reminders plus the 89 s
end_call_after_silence_ms. Ubaid: 50 s, then 30 s later the same day. That is an AGENT setting, not a flow
one, so this script sets it on the inbound agent draft; the outbound builder
sets the same value itself.
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
NAME_NODE = "node-book-name"
NEXT_NODE = "node-book-phone"   # inbound: name -> phone. Outbound rewires this.
SILENCE_MS = 30000
PROD_URL = "https://automation.aiemply.com/webhook/retell-wix"


def api_key() -> str:
    key = os.environ.get("RETELL_API_KEY")
    if key:
        return key
    raw = (Path(__file__).resolve().parents[2] / ".mcp.json").read_text(encoding="utf-8")
    cfg = json.loads(raw[raw.index("{"):])
    blob = json.dumps(cfg["mcpServers"]["retell-sage"])
    match = re.search(r"key_[a-f0-9]+", blob)
    if not match:
        raise SystemExit("No Retell key found (RETELL_API_KEY or .mcp.json retell-sage).")
    return match.group(0)


def request(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(RETELL_BASE + path, data=data, method=method, headers={
        "Authorization": f"Bearer {api_key()}", "Content-Type": "application/json",
        "User-Agent": "curl/8.0"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            text = resp.read().decode()
            return json.loads(text) if text.strip() else {}
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path} -> {e.code}: {e.read().decode()[:600]}")


# The V53 wording, verbatim - the patch refuses to run against anything else.
OLD_NAME_TEXT = """Ask: "Can I get your first name?" Then WAIT.
When they answer, ask: "And your last name?" Then WAIT.

Take whatever they give for each. If they spell it, join the letters into the word (J-O-H-N is John); if they just say it, write it the way it sounds. Do NOT ask them to spell it, do NOT read it back, do NOT ask them to confirm it. A name that is slightly off is fine - the spa tidies those up. A caller asked about their name three times hangs up.

If they give both names in one breath, take both and move on without asking the second question. Two questions at most, then on to the next step."""

NEW_NAME_TEXT = """Ask: "Can you spell your first name for me?" Then WAIT.
When they have spelled it, ask: "Thanks. And your last name - could you spell that as well?" Then WAIT.

Join the letters into the word (K-A-U-L is Kaul, B-O-O-K is Book). Letters may come with pauses, "as in" words, or a repeat - take the letters and ignore the rest.
If they say a name instead of spelling it, ask once, for that name only: "Could you spell that for me?" If they still do not spell it, take it the way it sounds and move on. Never a third ask for the same name.
Do NOT read either name back and do NOT ask them to confirm it. The spelling is the confirmation.
First name first, then last name: the answer to the first question is the first name and the answer to the second is the last name, whatever order the words come out in. If they label one themselves ("last name Book"), believe the label.
If they spell both names in one breath, take both and skip the second question."""

OLD_EDGE_PROMPT = "The caller has given their name."
NEW_EDGE_PROMPT = ("The caller has given BOTH a first name and a last name, spelled or said. "
                   "Never after the first name alone.")

Q1 = "Can you spell your first name for me?"
Q2 = "Thanks. And your last name - could you spell that as well?"
TRANSITION_EXAMPLES = [
    # stay: first name only
    {"id": "ft-name-first-only", "transcript": [
        {"role": "agent", "content": Q1},
        {"role": "user", "content": "K-A-U-L."}]},
    {"id": "ft-name-first-said", "transcript": [
        {"role": "agent", "content": Q1},
        {"role": "user", "content": "It's Kaul."}]},
    # go: last name given
    {"id": "ft-name-last-spelled", "destination_node_id": NEXT_NODE, "transcript": [
        {"role": "agent", "content": Q1},
        {"role": "user", "content": "K-A-U-L."},
        {"role": "agent", "content": Q2},
        {"role": "user", "content": "B-O-O-K."}]},
    {"id": "ft-name-both-at-once", "destination_node_id": NEXT_NODE, "transcript": [
        {"role": "agent", "content": Q1},
        {"role": "user", "content": "Kaul Book. K-A-U-L, B-O-O-K."}]},
]


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    nodes = {n["id"]: n for n in flow["nodes"]}
    node = nodes[NAME_NODE]

    if node["instruction"]["text"] != OLD_NAME_TEXT:
        raise SystemExit("node-book-name is not the V53 wording - re-read it before patching.")
    node["instruction"]["text"] = NEW_NAME_TEXT

    edges = node.get("edges", [])
    if len(edges) != 1 or edges[0]["destination_node_id"] != NEXT_NODE \
            or edges[0]["transition_condition"].get("prompt") != OLD_EDGE_PROMPT:
        raise SystemExit(f"name node edges changed shape: {edges}")
    edges[0]["transition_condition"]["prompt"] = NEW_EDGE_PROMPT
    if node.get("finetune_transition_examples"):
        raise SystemExit("name node already has transition examples - merge by hand.")
    node["finetune_transition_examples"] = TRANSITION_EXAMPLES

    # guards
    t = node["instruction"]["text"]
    for must in (Q1, Q2, "Do NOT read either name back", "believe the label", "Never a third ask"):
        if must not in t:
            raise SystemExit(f"new name wording missing: {must!r}")
    if "Can I get your first name?" in t or "Do NOT ask them to spell it" in t:
        raise SystemExit("old name wording survived")
    if len(t.split()) > 190:
        raise SystemExit(f"name node grew to {len(t.split())} words - keep it short")
    if re.search(r"[–—]", t):
        raise SystemExit("long dash in the node text")
    for ex in TRANSITION_EXAMPLES:
        if ex.get("destination_node_id") not in (None, NEXT_NODE):
            raise SystemExit("transition example points somewhere odd")
    # earlier work that must survive
    if nodes["node-greeting"].get("interruption_sensitivity") != 0:
        raise SystemExit("V54 greeting sensitivity gone")
    if "plays your own voice back to you" not in flow["global_prompt"]:
        raise SystemExit("V54 echo rule gone")
    if nodes["node-book-service"]["tool_ids"] != ["get_services"]:
        raise SystemExit("V55 service node changed")
    if "We have [every name it returned]" not in nodes["node-book-service"]["instruction"]["text"]:
        raise SystemExit("V56 wording gone")
    if "Never choose for them" not in nodes["node-book-discovery"]["instruction"]["text"]:
        raise SystemExit("V57 wording gone")
    if flow.get("start_speaker") != "user" or flow.get("begin_after_user_silence_ms") != 6000:
        raise SystemExit("Ubaid's start_speaker/user + 6000ms dashboard edit is not intact.")
    if sorted({tool["url"] for tool in flow["tools"]}) != [PROD_URL]:
        raise SystemExit("inbound draft tools are not all on the PROD backend")
    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true")
    args = ap.parse_args()

    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    agent = request("GET", f"/get-agent/{AGENT_ID}")
    print(f"draft flow v{live.get('version')} - {len(live['nodes'])} nodes; "
          f"agent draft v{agent.get('version')} silence={agent.get('end_call_after_silence_ms')} ms")
    patched = patch(live)
    node = next(n for n in patched["nodes"] if n["id"] == NAME_NODE)
    print(f"  name node: {len(node['instruction']['text'].split())} words, "
          f"{len(node['finetune_transition_examples'])} transition examples")

    SNAPSHOT.write_text(json.dumps(patched, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"snapshot -> {SNAPSHOT.name}")
    if args.dry_run:
        print("Dry run - Retell not modified.")
        return

    body = {k: v for k, v in patched.items()
            if k not in ("conversation_flow_id", "version",
                         "last_modification_timestamp", "is_published")}
    out = request("PATCH", f"/update-conversation-flow/{FLOW_ID}", body)
    back = next(n for n in out["nodes"] if n["id"] == NAME_NODE)
    if back["instruction"]["text"] != NEW_NAME_TEXT \
            or back["edges"][0]["transition_condition"]["prompt"] != NEW_EDGE_PROMPT \
            or len(back.get("finetune_transition_examples", [])) != len(TRANSITION_EXAMPLES):
        raise SystemExit("read-back mismatch after PATCH")
    print(f"PATCHED draft flow v{out.get('version')}")

    if agent.get("end_call_after_silence_ms") != SILENCE_MS:
        a = request("PATCH", f"/update-agent/{AGENT_ID}", {"end_call_after_silence_ms": SILENCE_MS})
        if a.get("end_call_after_silence_ms") != SILENCE_MS:
            raise SystemExit("agent silence timeout did not stick")
        print(f"  agent draft v{a.get('version')}: end_call_after_silence_ms -> {SILENCE_MS}")

    if not args.publish:
        print("  Draft only - real callers still get latest_published.")
        return
    request("POST", f"/publish-agent/{AGENT_ID}")
    versions = request("GET", f"/get-agent-versions/{AGENT_ID}")
    versions = versions.get("items", versions) if isinstance(versions, dict) else versions
    pub = max(v["version"] for v in versions if v.get("is_published"))
    pa = request("GET", f"/get-agent/{AGENT_ID}?version={pub}")
    pf = request("GET", f"/get-conversation-flow/{FLOW_ID}?version={pa['response_engine']['version']}")
    pn = next(n for n in pf["nodes"] if n["id"] == NAME_NODE)
    ok = (pn["instruction"]["text"] == NEW_NAME_TEXT and pa.get("end_call_after_silence_ms") == SILENCE_MS
          and sorted({t["url"] for t in pf["tools"]}) == [PROD_URL])
    print(f"PUBLISHED inbound agent v{pub} -> flow v{pf['version']}; silence={pa.get('end_call_after_silence_ms')}; "
          f"name node + prod tools verified={ok}")
    if not ok:
        raise SystemExit("published version is not what was intended")


if __name__ == "__main__":
    main()
