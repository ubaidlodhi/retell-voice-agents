"""
Semantic diff between what the builder defines and a Retell export.

Run:  py -X utf8 compare_export.py [path-to-retell-export.json]
      (defaults to aria_single_prompt.json in this folder)

Why this exists
---------------
Retell's API serializes parts of the agent from hash maps (response_variables,
properties, headers, …) and injects runtime fields (timestamps, version,
base_version, llm_id, …). So a raw `git diff` between the builder output and a
fresh Retell export is full of NOISE — reordered keys and volatile fields that
aren't real changes. You cannot make the builder "match" that, because the map
ordering isn't even stable across exports.

This tool sidesteps all of it: it canonicalizes BOTH sides the same way
(recursively sort every key + strip volatile/runtime fields + drop empty
`required: []` the way Retell does) and prints only the REAL differences. A
clean run means the dashboard and the builder agree.
"""
from __future__ import annotations
import json
import sys
import difflib
from pathlib import Path

import _build_single_prompt_agent as builder

HERE = Path(__file__).parent

# Fields Retell injects/derives at import or that change every export. Stripped
# from both sides before comparing (matched anywhere they appear, by key name).
VOLATILE_KEYS = {
    "last_modification_timestamp",
    "version",
    "base_version",
    "opt_in_signed_url",
    "assigned_tags",
    "is_published",
    "llm_id",
}


def canon(obj):
    """Recursively: sort dict keys, drop volatile keys, drop empty `required`.
    Lists keep their order (array order IS meaningful, e.g. general_tools)."""
    if isinstance(obj, dict):
        out = {}
        for k in sorted(obj):
            if k in VOLATILE_KEYS:
                continue
            if k == "required" and obj[k] == []:  # Retell omits empty required
                continue
            out[k] = canon(obj[k])
        return out
    if isinstance(obj, list):
        return [canon(x) for x in obj]
    return obj


def dump(obj) -> list[str]:
    return json.dumps(canon(obj), indent=2, ensure_ascii=False).splitlines(keepends=True)


def main() -> None:
    export_path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "aria_single_prompt.json"
    export = json.loads(export_path.read_text(encoding="utf-8"))

    expected = dump(builder.AGENT)
    actual = dump(export)

    diff = list(difflib.unified_diff(
        expected, actual,
        fromfile="builder (what the script defines)",
        tofile=f"export ({export_path.name})",
    ))

    if not diff:
        print("✓ No semantic differences — the builder matches the export.")
        return
    sys.stdout.write("".join(diff))
    print(f"\n--- {sum(1 for l in diff if l.startswith(('+', '-')) and not l.startswith(('+++', '---')))} changed line(s) ---")


if __name__ == "__main__":
    main()
