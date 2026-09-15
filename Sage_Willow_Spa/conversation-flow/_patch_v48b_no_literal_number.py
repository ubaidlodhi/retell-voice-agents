"""
V48b - take the literal phone number back out of the phone rule.

Run:  py -X utf8 Sage_Willow_Spa/conversation-flow/_patch_v48b_no_literal_number.py [--dry-run] [--publish]

V48 fixed the readback but explained WHY by quoting "253-268-1856" as the thing
not to write - and that is Ubaid's own number sitting in a live prompt. The
standing rule exists precisely because this keeps happening: a "$499"
pronunciation sample got spoken as a real price, and a "Tuesday at 2 PM" sample
got spoken as a real booking. A real phone number is worse than either, because
a caller has no way to tell it is wrong.

The counter-example does not need a number in it. "Figures make the voice read a
group as one large number" says the same thing with nothing to copy.
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


OLD_RULE_FRAGMENT = (
    "  so a number starting 2-5-3 is written \"two five three, ...\" and never \"253\". "
    "Digit form makes the voice say \"two hundred fifty-three\", which is not a phone "
    "number and forces the caller to ask you to repeat it. Never write the number with "
    "hyphens, brackets or spaces between figures - words only.\n"
)
NEW_RULE_FRAGMENT = (
    "  Each [digit] is that digit's name written out as a word - never a figure, and "
    "never two figures joined together. Figures make the voice read a whole group as one "
    "large number instead of three separate digits, and the caller then has to ask you to "
    "repeat it. No hyphens, no brackets, no spaces between figures - words only.\n"
)

OLD_NODE_FRAGMENT = (
    "Never write it as figures - \"253-268-1856\" comes out of the voice as \"two hundred "
    "fifty-three\" and the caller has to ask you to say it again."
)
NEW_NODE_FRAGMENT = (
    "Never write figures - a group written as figures is read aloud as one large number, "
    "and the caller has to ask you to say it again."
)

# Any run of 7+ digits, or an xxx-xxx-xxxx shape, is a phone number in a prompt.
PHONE_LIKE = re.compile(r"\b\d{3}[-. ]\d{3}[-. ]\d{4}\b|\b\d{7,}\b")


def patch(flow: dict) -> dict:
    flow = json.loads(json.dumps(flow))
    nodes = {n["id"]: n for n in flow["nodes"]}

    if OLD_RULE_FRAGMENT not in flow["global_prompt"]:
        raise SystemExit("V48 phone-rule fragment not found - check the flow version.")
    flow["global_prompt"] = flow["global_prompt"].replace(OLD_RULE_FRAGMENT, NEW_RULE_FRAGMENT)

    node = nodes["node-book-phone"]["instruction"]
    if OLD_NODE_FRAGMENT not in node["text"]:
        raise SystemExit("V48 phone-node fragment not found - check the flow version.")
    node["text"] = node["text"].replace(OLD_NODE_FRAGMENT, NEW_NODE_FRAGMENT)

    # Now hold the whole flow to the rule, with no exception carved out.
    targets = [(flow["global_prompt"], "global_prompt")]
    targets += [(n.get("instruction", {}).get("text", "") or "", n["id"]) for n in flow["nodes"]]
    targets += [(json.dumps(t, ensure_ascii=False), f"tool:{t['name']}") for t in flow["tools"]]
    for blob, label in targets:
        hit = PHONE_LIKE.search(blob)
        if hit:
            raise SystemExit(f"{label} still carries a literal number: {hit.group(0)}")

    # The shape itself must survive - that is the whole point of V48.
    if "[digit] [digit] [digit], [digit] [digit] [digit]" not in flow["global_prompt"]:
        raise SystemExit("The bracketed digit shape went missing from the global prompt.")
    if "[digit] [digit] [digit], [digit] [digit] [digit]" not in node["text"]:
        raise SystemExit("The bracketed digit shape went missing from node-book-phone.")
    return flow


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true")
    args = ap.parse_args()

    live = request("GET", f"/get-conversation-flow/{FLOW_ID}")
    print(f"draft flow v{live.get('version')}")
    patched = patch(live)
    print("  literal numbers remaining anywhere in the flow: none")

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
        print("  NOTE: not live until published.")
        return

    request("POST", f"/publish-agent/{AGENT_ID}")
    vs = sorted(request("GET", f"/list-agent-versions/{AGENT_ID}")["items"],
                key=lambda v: v["version"], reverse=True)
    pub = max(v["version"] for v in vs if v.get("is_published"))
    agent = request("GET", f"/get-agent/{AGENT_ID}?version={pub}")
    served = request("GET", f"/get-conversation-flow/{FLOW_ID}"
                            f"?version={agent['response_engine']['version']}")
    urls = sorted({t.get("url") for t in served["tools"] if t.get("url")})
    blob = json.dumps(served, ensure_ascii=False)
    print(f"PUBLISHED -> agent v{pub} (flow v{agent['response_engine']['version']})")
    print(f"  tools: {urls}")
    print(f"  literal numbers in the served flow: "
          f"{PHONE_LIKE.search(blob).group(0) if PHONE_LIKE.search(blob) else 'none'}")
    if urls != ["https://automation.aiemply.com/webhook/retell-wix"]:
        raise SystemExit("PUBLISHED VERSION IS NOT ON THE PROD BACKEND - fix immediately.")


if __name__ == "__main__":
    main()
