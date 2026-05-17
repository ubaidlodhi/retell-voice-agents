"""
Generator: reads the current n8n workflow JSON and emits a fully
self-contained _modify_n8n_workflow.py that can rebuild the workflow from
scratch.

Use this whenever the n8n workflow has been hand-edited in the UI and the
build script needs to be re-synced. The build script itself does not depend
on this generator at runtime — they are independent files.

Run:  py -X utf8 _generate_build_script.py

Inputs:  Retell AI ↔ Wix Bookings _ Production v2.json (canonical workflow)
Outputs: _modify_n8n_workflow.py (writes the canonical workflow when executed)
"""
from __future__ import annotations
import copy
import json
import pprint
import re
from pathlib import Path

HERE = Path(__file__).parent
WF_PATH = HERE / "Retell AI ↔ Wix Bookings _ Production v2.json"
OUT_PATH = HERE / "_modify_n8n_workflow.py"

# Credentials we want parameterized as constants (vs. inlined in node dicts).
WIX_CRED_ID = "wLpWbblaihcY4xnw"
WIX_CRED_NAME = "Test: Wix Sage Site"
SMTP_CRED_ID = "m0mbibKf6il36id5"
SMTP_CRED_NAME = "SMTP account"

# Email config — already parameterized in the prior script.
TO_EMAIL_VALUE = "sagewillowspa@gmail.com"
FROM_EMAIL_VALUE = "Aria <engineering@aiemply.com>"

# Map Code-type node names -> Python constant names (so big JS blobs land in
# named constants at the top of the script, not inlined inside the NODES list).
JS_CONST_BY_NAME = {
    "Parse Retell Payload":              "PARSE_RETELL_PAYLOAD_JS",
    "Validate: Slots Args":              "VALIDATE_SLOTS_JS",
    "Format: Time Slots Response":       "FORMAT_SLOTS_JS",
    "Format: Staff Response":            "FORMAT_STAFF_JS",
    "Validate: Booking Args":            "VALIDATE_BOOKING_JS",
    "Format: Booking Confirmation":      "FORMAT_BOOKING_JS",
    "Validate: Cancel Args":             "VALIDATE_CANCEL_JS",
    "Format: Cancel Response":           "FORMAT_CANCEL_JS",
    "Validate: Reschedule Args":         "VALIDATE_RESCHEDULE_JS",
    "Format: Reschedule Response":       "FORMAT_RESCHEDULE_JS",
    "Validate: Get Booking Args":        "VALIDATE_GET_BOOKING_JS",
    "Format: Get Booking Response":      "FORMAT_GET_BOOKING_JS",
    "Validate: Flag Callback Args":      "VALIDATE_FLAG_CALLBACK_JS",
    "Format: Flag Callback Response":    "FORMAT_FLAG_CALLBACK_RESPONSE_JS",
    "Validate: Get Contact":             "VALIDATE_GET_CONTACT_JS",
    "Format: Contact Response":          "FORMAT_CONTACT_RESPONSE_JS",
    "Format: Create Contact":            "FORMAT_CREATE_CONTACT_JS",
    "Format: Contact Response1":         "FORMAT_CONTACT_RESPONSE_1_JS",
    "Extract Pricing IDs":               "EXTRACT_PRICING_IDS_JS",
    "Extract Add-on IDs":                "EXTRACT_ADD_ON_IDS_JS",
    "Format: Services Response":         "FORMAT_SERVICES_RESPONSE_JS",
}

# Map httpRequest node names -> Python constant names for their JSON body
# template (when present).
HTTP_CONST_BY_NAME = {
    "Wix: Query Time Slots":     "WIX_QUERY_TIME_SLOTS_BODY",
    "Wix: Query Staff Members":  "WIX_QUERY_STAFF_BODY",
    "Wix: Create Booking":       "WIX_CREATE_BOOKING_BODY",
    "Wix: Confirm Booking":      "WIX_CONFIRM_BOOKING_BODY",
    "Wix: Cancel Booking":       "WIX_CANCEL_BOOKING_BODY",
    "Wix: Reschedule Booking":   "WIX_RESCHEDULE_BOOKING_BODY",
    "Wix: Get Booking":          "WIX_GET_BOOKING_BODY",
    "Wix: Search Contact":       "WIX_SEARCH_CONTACT_BODY",
    "Wix: Search Contact1":      "WIX_SEARCH_CONTACT_1_BODY",
    "Wix: Create Contact":       "WIX_CREATE_CONTACT_BODY",
    "Wix: Query Services":       "WIX_QUERY_SERVICES_BODY",
    "Wix: Get Pricing Variants": "WIX_GET_PRICING_VARIANTS_BODY",
    "Wix: Get Add-ons":          "WIX_GET_ADD_ONS_BODY",
}


# Sentinel markers — substituted into the data during dump, then replaced
# with bare Python identifiers in the output text. Must be printable ASCII
# (pprint escapes non-printables like null bytes, which would break the
# string-level substitution pass below).
SENTINEL_PREFIX = "@@SUBST_PY_"
SENTINEL_SUFFIX = "_END@@"

def _sentinel(token: str) -> str:
    return f"{SENTINEL_PREFIX}{token}{SENTINEL_SUFFIX}"


def substitute_node(node: dict) -> dict:
    """Walk a node and replace big string blobs / credentials / well-known
    values with sentinel placeholders. The placeholders are swapped for
    real Python constant references in a final text pass."""
    n = copy.deepcopy(node)
    params = n.get("parameters", {})

    # JS code
    name = n.get("name")
    if name in JS_CONST_BY_NAME and "jsCode" in params:
        params["jsCode"] = _sentinel(JS_CONST_BY_NAME[name])

    # HTTP body
    if name in HTTP_CONST_BY_NAME and "jsonBody" in params:
        params["jsonBody"] = _sentinel(HTTP_CONST_BY_NAME[name])

    # Credentials (Wix / SMTP)
    creds = n.get("credentials")
    if creds:
        for cred_key, cred_val in list(creds.items()):
            cid = cred_val.get("id")
            if cid == WIX_CRED_ID:
                creds[cred_key] = {"_REPLACE_": "WIX_CRED"}
            elif cid == SMTP_CRED_ID:
                creds[cred_key] = {"_REPLACE_": "SMTP_CRED"}

    # Email config (only in Send Email node)
    if params.get("fromEmail") == FROM_EMAIL_VALUE:
        params["fromEmail"] = _sentinel("FROM_EMAIL")
    if params.get("toEmail") == TO_EMAIL_VALUE:
        params["toEmail"] = _sentinel("CALLBACK_RECIPIENT")

    return n


def emit_constants(out_lines: list[str], pairs: list[tuple[str, str]], header: str) -> None:
    out_lines.append("# " + "-" * 77)
    out_lines.append("# " + header)
    out_lines.append("# " + "-" * 77)
    out_lines.append("")
    for const, value in pairs:
        # Prefer raw triple-quoted strings; fall back to repr if value contains
        # the triple-quote delimiter or stray carriage returns that break the
        # raw-string form.
        if '"""' not in value and "\r" not in value:
            out_lines.append(f'{const} = r"""{value}"""')
        else:
            out_lines.append(f"{const} = {value!r}")
        out_lines.append("")


def python_literal(obj) -> str:
    """Convert a Python object (already JSON-parsed) into a Python literal
    string suitable for embedding in source code. Handles substituting our
    sentinel placeholders with bare identifier references."""
    text = pprint.pformat(obj, indent=4, width=120, sort_dicts=False)

    # Replace sentinel markers — they were emitted as single-quoted Python
    # strings by pprint (e.g. "'\x00__SUBST__VALIDATE_SLOTS_JS__\x00'") which
    # we strip down to the bare identifier.
    pattern = re.compile(re.escape("'" + SENTINEL_PREFIX) + r"(\w+)" + re.escape(SENTINEL_SUFFIX + "'"))
    text = pattern.sub(lambda m: m.group(1), text)

    # Replace credential placeholders.
    text = text.replace("{'_REPLACE_': 'WIX_CRED'}", "{'id': WIX_CREDENTIAL_ID, 'name': WIX_CREDENTIAL_NAME}")
    text = text.replace("{'_REPLACE_': 'SMTP_CRED'}", "{'id': SMTP_CREDENTIAL_ID, 'name': SMTP_CREDENTIAL_NAME}")

    return text


def main() -> None:
    wf = json.loads(WF_PATH.read_text(encoding="utf-8"))
    nodes = wf["nodes"]
    connections = wf["connections"]
    meta = wf.get("meta", {})

    # Extract JS constants (preserving node order so the section reads top-down)
    js_pairs: list[tuple[str, str]] = []
    seen_js = set()
    for node in nodes:
        const = JS_CONST_BY_NAME.get(node["name"])
        if const and const not in seen_js and "jsCode" in node.get("parameters", {}):
            js_pairs.append((const, node["parameters"]["jsCode"]))
            seen_js.add(const)

    # Extract HTTP body constants
    http_pairs: list[tuple[str, str]] = []
    seen_http = set()
    for node in nodes:
        const = HTTP_CONST_BY_NAME.get(node["name"])
        if const and const not in seen_http and "jsonBody" in node.get("parameters", {}):
            http_pairs.append((const, node["parameters"]["jsonBody"]))
            seen_http.add(const)

    # Substitute markers into nodes
    substituted_nodes = [substitute_node(n) for n in nodes]

    # Emit the script
    lines: list[str] = []
    lines.append('"""')
    lines.append("Build script for the Sage & Willow Spa n8n workflow.")
    lines.append("")
    lines.append("Single source of truth for the workflow at")
    lines.append("https://automation.aiemply.com/webhook/retell-wix.")
    lines.append("Running this script writes a fully importable workflow JSON to")
    lines.append("`Retell AI ↔ Wix Bookings _ Production v2.json` — no existing file required.")
    lines.append("")
    lines.append("Run:  py -X utf8 _modify_n8n_workflow.py")
    lines.append('"""')
    lines.append("from __future__ import annotations")
    lines.append("import json")
    lines.append("from pathlib import Path")
    lines.append("")
    lines.append('WF_PATH = Path(__file__).parent / "Retell AI ↔ Wix Bookings _ Production v2.json"')
    lines.append("")
    lines.append("# n8n credential references (replace if importing into a different n8n instance)")
    lines.append(f'WIX_CREDENTIAL_ID   = {WIX_CRED_ID!r}')
    lines.append(f'WIX_CREDENTIAL_NAME = {WIX_CRED_NAME!r}')
    lines.append(f'SMTP_CREDENTIAL_ID  = {SMTP_CRED_ID!r}')
    lines.append(f'SMTP_CREDENTIAL_NAME = {SMTP_CRED_NAME!r}')
    lines.append("")
    lines.append("# Flag-callback email destination + sender identity")
    lines.append(f'CALLBACK_RECIPIENT = {TO_EMAIL_VALUE!r}')
    lines.append(f'FROM_EMAIL         = {FROM_EMAIL_VALUE!r}')
    lines.append("")
    lines.append("")

    emit_constants(lines, js_pairs,
                   "JS code constants (inlined into Code-type nodes)")
    lines.append("")
    emit_constants(lines, http_pairs,
                   "HTTP body templates (inlined into Wix httpRequest nodes)")
    lines.append("")
    lines.append("# " + "-" * 77)
    lines.append("# Nodes (every node in the workflow — full canonical state)")
    lines.append("# " + "-" * 77)
    lines.append("")
    lines.append("NODES = " + python_literal(substituted_nodes))
    lines.append("")
    lines.append("")
    lines.append("# " + "-" * 77)
    lines.append("# Connections (full canonical wiring)")
    lines.append("# " + "-" * 77)
    lines.append("")
    lines.append("CONNECTIONS = " + python_literal(connections))
    lines.append("")
    lines.append("")
    lines.append("# " + "-" * 77)
    lines.append("# Meta + pinData")
    lines.append("# " + "-" * 77)
    lines.append("")
    lines.append(f"META = {meta!r}")
    lines.append("")
    lines.append("PIN_DATA = {}")
    lines.append("")
    lines.append("")
    lines.append("# " + "-" * 77)
    lines.append("# Main")
    lines.append("# " + "-" * 77)
    lines.append("")
    lines.append("def main():")
    lines.append("    wf = {")
    lines.append('        "nodes": NODES,')
    lines.append('        "connections": CONNECTIONS,')
    lines.append('        "pinData": PIN_DATA,')
    lines.append('        "meta": META,')
    lines.append("    }")
    lines.append('    WF_PATH.write_text(')
    lines.append('        json.dumps(wf, indent=2, ensure_ascii=False),')
    lines.append('        encoding="utf-8",')
    lines.append("    )")
    lines.append('    print(f"Wrote {WF_PATH}")')
    lines.append('    print(f"  Nodes: {len(NODES)}")')
    lines.append("    route_rules = next(")
    lines.append("        (n['parameters']['rules']['values']")
    lines.append("         for n in NODES if n.get('name') == 'Route by Tool'),")
    lines.append("        [],")
    lines.append("    )")
    lines.append('    print(f"  Switch rules: {len(route_rules)}")')
    lines.append('    print(f"  Flag-callback recipient: {CALLBACK_RECIPIENT}")')
    lines.append("")
    lines.append("")
    lines.append('if __name__ == "__main__":')
    lines.append("    main()")
    lines.append("")

    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"  JS constants:   {len(js_pairs)}")
    print(f"  HTTP constants: {len(http_pairs)}")
    print(f"  Nodes:          {len(substituted_nodes)}")


if __name__ == "__main__":
    main()
