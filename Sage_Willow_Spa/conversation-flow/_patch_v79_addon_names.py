"""
V79 - book_appointment sends each add-on's NAME as well as its id. DRAFT ONLY.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v79_addon_names.py [--dry-run]

call_dde463dd1cad472c17e1b8e1c46 (2026-10-14): the Aromatherapy id went out one character short and
Wix refused the booking. The backend now settles add-ons itself ("Resolve: Add-ons (Booking)", live
in both n8n workflows): name first, then an exact id, then the closest id - the same order as
services. The closest-id step already works for the published agent; this gives the backend the
name, so a wrong-but-real id (another add-on's) is also caught.
  book_appointment.addOns / guestAddOns items: + "name" (required).

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

NAME_PROP = {"type": "string", "description": "The add-on's name exactly as get_services listed it."}
DESCRIPTIONS = {
    "addOns": "Only if chosen. Each entry: the add-on's name, id and groupId from get_services.",
    "guestAddOns": ("Two people at once: add-ons the guest chose, from get_services for the guest's massage. "
                    "Each entry: the add-on's name, id and groupId."),
}


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
    tool = [t for t in flow["tools"] if t["name"] == "book_appointment"][0]
    done = []
    for key, desc in DESCRIPTIONS.items():
        p = tool["parameters"]["properties"][key]
        items = p["items"]
        if "name" in items["properties"]:
            continue
        if set(items["properties"]) != {"id", "groupId"}:
            raise SystemExit(f"book_appointment.{key} items changed since - merge by hand")
        items["properties"] = {"name": NAME_PROP, **items["properties"]}
        items["required"] = ["name", "id", "groupId"]
        p["description"] = desc
        done.append(f"book_appointment.{key}: each entry carries the add-on name")
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
    tool = [t for t in out["tools"] if t["name"] == "book_appointment"][0]
    for key in DESCRIPTIONS:
        assert tool["parameters"]["properties"][key]["items"]["required"] == ["name", "id", "groupId"]
    assert not out.get("is_published")
    print(f"PATCHED draft flow v{out['version']} - NOT published")


if __name__ == "__main__":
    main()
