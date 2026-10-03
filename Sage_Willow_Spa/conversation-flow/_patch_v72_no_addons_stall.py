"""
V72 - no dead air after the time is agreed for a massage with no enhancements. DRAFT ONLY.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v72_no_addons_stall.py [--dry-run]

call_4ce5b76f (outbound v15, live, 2026-10-01): Couples Massage, caller said "Yes" to
3:30. Discovery -> Add-ons. Couples Massage has NO add-ons in Wix (nor do Prenatal,
Lymphatic Drainage and Eastern Therapeutic Ritual), and the Add-ons step said "If
get_services returned no add-ons for this service, skip this entirely and move on
without mentioning them." So Aria said "Alright, 3:30 PM it is." - no question - and
waited. A step cannot move on by itself: its exits are judged on the caller's next turn,
and the caller was waiting for Aria. 20.7 s of silence (public log: nothing between
21:08:12 and the caller's "Hello?" at 21:08:36). After "Hello?" she asked about
enhancements anyway, for a massage that has none.
  -> Discovery gets its own exit for "time agreed + this massage has no enhancements",
     straight to the name step (the Add-ons step is never entered for those).
  -> If the Add-ons step is reached anyway, it asks a real question instead of going
     quiet: "[Time] it is - shall I go ahead and take your details?"
Same call: "260 for 45 minutes" - Wix lists 90 min at USD 260; the price was right, the
length was misspoken. -> one line in the length-and-price step: the length is the one
listed beside that price.

No --publish flag on purpose. Tools are left where they are.
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

NOADDONS_EDGE = {
    "id": "e-book-slot-picked-noaddons",
    "destination_node_id": "node-book-name",
    "transition_condition": {"type": "prompt", "prompt": (
        "The caller has agreed to a specific appointment time that get_slots returned, AND the massage has no "
        "enhancements to offer - get_services returned no availableAddOns for it (for example Couples Massage, "
        "Prenatal Massage, Lymphatic Drainage Massage, Eastern Therapeutic Ritual). If they named a therapist, "
        "that person must already have been confirmed free at that time.")},
}
PICKED_ADD = (" Not when the massage has no enhancements to offer (get_services returned no availableAddOns for it)"
              " - that goes straight on to the name.")

OLD_SKIP = "If get_services returned no add-ons for this service, skip this entirely and move on without mentioning them."
NEW_SKIP = ("If get_services returned no add-ons for this service, there is nothing to offer - do not mention "
            "enhancements. Still end on a question, never a bare statement: \"[Time] it is - shall I go ahead and "
            "take your details?\"")

OLD_NAME = ("If you come here straight after the caller agreed a time for two people, open with the time: "
            "\"[Time] it is for both of you. Can you spell your first name for me?\"")
NEW_NAME = ("If you come here straight after the caller agreed a time - no enhancements question in between - open "
            "with the time: \"[Time] it is. Can you spell your first name for me?\" (for two people: \"[Time] it is "
            "for both of you. Can you spell your first name for me?\")")

OLD_LEN = "Speak durations as hours, never raw minutes."
NEW_LEN = ("Speak durations as hours, never raw minutes. Each [length] is the duration listed beside that price "
           "(60 min = an hour, 90 min = an hour and a half, 120 min = two hours) - never any other length.")


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


def swap(text: str, old: str, new: str, where: str) -> str:
    if new in text:
        return text
    if text.count(old) != 1:
        raise SystemExit(f"{where}: expected one {old[:50]!r} - merge by hand")
    return text.replace(old, new)


def patch(flow: dict) -> tuple[dict, list[str]]:
    flow = json.loads(json.dumps(flow))
    n = {x["id"]: x for x in flow["nodes"]}
    done = []

    d = n["node-book-discovery"]
    ids = [e["id"] for e in d["edges"]]
    if NOADDONS_EDGE["id"] not in ids:
        if "e-book-slot-picked" not in ids:
            raise SystemExit("discovery: e-book-slot-picked missing - merge by hand")
        d["edges"].insert(ids.index("e-book-slot-picked"), json.loads(json.dumps(NOADDONS_EDGE)))
        done.append("discovery: exit for a time agreed on a massage with no enhancements -> name")
    picked = [e for e in d["edges"] if e["id"] == "e-book-slot-picked"][0]["transition_condition"]
    if PICKED_ADD not in picked["prompt"]:
        picked["prompt"] += PICKED_ADD
        done.append("discovery: e-book-slot-picked excludes no-enhancement massages")

    a = n["node-book-addons"]["instruction"]
    new = swap(a["text"], OLD_SKIP, NEW_SKIP, "add-ons")
    if new != a["text"]:
        a["text"] = new
        done.append("add-ons: no bare statement when there is nothing to offer")

    nm = n["node-book-name"]["instruction"]
    new = swap(nm["text"], OLD_NAME, NEW_NAME, "name")
    if new != nm["text"]:
        nm["text"] = new
        done.append("name: opens with the agreed time when it comes straight from the time")

    s = n["node-book-service"]["instruction"]
    new = swap(s["text"], OLD_LEN, NEW_LEN, "service & length")
    if new != s["text"]:
        s["text"] = new
        done.append("service & length: length is the one listed beside the price")
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
    eids = [e["id"] for e in on["node-book-discovery"]["edges"]]
    assert eids.index(NOADDONS_EDGE["id"]) < eids.index("e-book-slot-picked")
    assert NEW_SKIP in on["node-book-addons"]["instruction"]["text"]
    assert NEW_LEN in on["node-book-service"]["instruction"]["text"]
    assert not out.get("is_published")
    print(f"PATCHED draft flow v{out['version']} - NOT published")


if __name__ == "__main__":
    main()
