#!/usr/bin/env python3
"""
Retell Conversation Flow validator.

Run before delivering any conversation-flow JSON. Catches the failure modes
that produce opaque import errors or silent runtime breakage:

   1. JSON parse errors
   2. Duplicate edge IDs (across all edge containers, including nested ones)
   3. Broken destination_node_id references AND self-loops (source == destination)
   4. Missing else_edge on branch / extract_dynamic_variables / code nodes
   5. Tools with speak_during_execution but no execution_message_description
   6. Tools with placeholder URLs (TODO, example.com, REPLACE_WITH_*)
   7. Missing Transfer-failed edge on transfer_call nodes
   8. start_node_id resolves to a real node
   9. Duplicate node IDs
  10. Unknown node `type` (rejected by Retell's oneOf with an opaque error)
  11a. Function nodes missing `tool_type` — required by Retell's import schema.
       Pairs with a warning when `wait_for_result` is unset.
  11b. Subagent nodes using legacy `tools` field — must be `tool_ids` (plural).
       Also validates referenced tool_ids exist in conversationFlow.tools[].
  12. Voice config sanity — warns when `voice_model` is set, since pairing it
      with the wrong voice provider triggers an opaque "voice model not
      supported" import error. Production agents typically omit it.
  13. Tool config sanity — warns when tools lack the production-validated
      defaults `args_at_root: true` and `parameter_type: "form"`.

Exit code 0 = pass, 1 = fail.

Usage:
  python validate_flow.py path/to/agent.json
"""

import json
import sys
from collections import Counter
from pathlib import Path

# Edge container fields where edge IDs can live (singular and array forms).
SINGULAR_EDGE_FIELDS = ("always_edge", "skip_response_edge", "edge", "else_edge",
                        "success_edge", "failed_edge")

# Node types that REQUIRE an else_edge as a fallback.
NODES_REQUIRING_ELSE_EDGE = ("branch", "extract_dynamic_variables", "code")

# Substrings that flag a placeholder URL.
PLACEHOLDER_URL_MARKERS = ("TODO", "REPLACE_WITH", "example.com", "your-domain", "<your", "{{your")

# Node types Retell's import endpoint accepts. A subagent node attaches tools via
# `tool_ids` (plural, array of strings). Putting tools as `tools: [...]` on a subagent
# fails import with an opaque oneOf-mismatch error.
KNOWN_NODE_TYPES = {
    "conversation", "subagent", "function", "transfer_call", "end",
    "press_digit", "branch", "extract_dynamic_variables", "code",
    "sms", "mcp", "agent", "component", "bridge_transfer", "cancel_transfer",
}


def collect_edge_ids(node):
    """Yield every edge ID found on a node, across all edge containers."""
    for edge in node.get("edges", []) or []:
        if isinstance(edge, dict) and edge.get("id"):
            yield edge["id"]
    for field in SINGULAR_EDGE_FIELDS:
        v = node.get(field)
        if isinstance(v, dict) and v.get("id"):
            yield v["id"]


def collect_destination_refs(node):
    """Yield (source_label, destination_node_id) for every edge with a destination."""
    src = node.get("id", "?")
    for edge in node.get("edges", []) or []:
        if isinstance(edge, dict) and edge.get("destination_node_id"):
            yield (f"{src}.edges[{edge.get('id', '?')}]", edge["destination_node_id"])
    for field in SINGULAR_EDGE_FIELDS:
        v = node.get(field)
        if isinstance(v, dict) and v.get("destination_node_id"):
            yield (f"{src}.{field}", v["destination_node_id"])


def validate(path):
    errors = []
    warnings = []

    # 1. JSON parse
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return [f"File not found: {path}"], []
    except json.JSONDecodeError as e:
        return [f"JSON parse error: {e}"], []

    cf = data.get("conversationFlow")
    if not cf:
        return ["No 'conversationFlow' object at root"], []

    nodes = cf.get("nodes", [])
    if not nodes:
        return ["No nodes in conversationFlow"], []

    nodes_by_id = {n["id"]: n for n in nodes if "id" in n}

    # 2. Duplicate edge IDs
    all_edge_ids = []
    for n in nodes:
        all_edge_ids.extend(collect_edge_ids(n))
    dupes = [eid for eid, c in Counter(all_edge_ids).items() if c > 1]
    if dupes:
        errors.append(f"Duplicate edge IDs (causes opaque import error): {dupes}")

    # 3. Broken destination references + self-loops
    for n in nodes:
        src_id = n.get("id")
        for src_label, dest in collect_destination_refs(n):
            if dest not in nodes_by_id:
                errors.append(f"Broken edge reference: {src_label} -> {dest} (node not found)")
            if dest == src_id:
                errors.append(
                    f"Self-loop edge on {src_label}: destination_node_id == source node id. "
                    f"Retell rejects edges where source == destination — conversation/subagent nodes "
                    f"already wait for the next user turn, no self-edge needed."
                )

    # 4. Missing else_edge on required node types
    for n in nodes:
        if n.get("type") in NODES_REQUIRING_ELSE_EDGE:
            if not isinstance(n.get("else_edge"), dict):
                errors.append(
                    f"Node {n.get('id')} (type={n.get('type')}) is missing required else_edge — "
                    f"will silently dead-end if no condition matches"
                )

    # 5. Function-style nodes with speak_during_execution but no execution_message_description
    # This applies to tools defined in conversationFlow.tools[]
    tools = cf.get("tools", []) or []
    for tool in tools:
        if tool.get("speak_during_execution") and not tool.get("execution_message_description"):
            warnings.append(
                f"Tool '{tool.get('name', '?')}' has speak_during_execution=true but no "
                f"execution_message_description. The LLM will improvise a different filler line "
                f"every call. Pin the phrase explicitly."
            )

    # 6. Placeholder URLs in tools
    for tool in tools:
        url = tool.get("url", "")
        if any(marker.lower() in url.lower() for marker in PLACEHOLDER_URL_MARKERS):
            errors.append(
                f"Tool '{tool.get('name', '?')}' has a placeholder URL ({url}). "
                f"Will silently fail at runtime — set a real URL or remove the tool."
            )

    # 7. Transfer nodes without Transfer-failed edge
    for n in nodes:
        if n.get("type") == "transfer_call":
            edge = n.get("edge")
            if not isinstance(edge, dict):
                warnings.append(
                    f"Transfer node {n.get('id')} has no 'edge' for Transfer-failed fallback. "
                    f"Failed dials will silently dead-end."
                )
            else:
                prompt = (edge.get("transition_condition") or {}).get("prompt", "")
                if "transfer failed" not in prompt.lower():
                    warnings.append(
                        f"Transfer node {n.get('id')} edge.transition_condition.prompt does not "
                        f"contain 'Transfer failed' (got: {prompt!r}). The fallback may not fire."
                    )

    # 8. Sanity: starting node exists
    start_id = cf.get("start_node_id")
    if start_id and start_id not in nodes_by_id:
        errors.append(f"start_node_id '{start_id}' does not match any node")

    # 9. Sanity: all node IDs are unique
    node_ids = [n.get("id") for n in nodes if "id" in n]
    node_dupes = [nid for nid, c in Counter(node_ids).items() if c > 1]
    if node_dupes:
        errors.append(f"Duplicate node IDs: {node_dupes}")

    # 10. Unknown node types (Retell's oneOf rejects with a noisy error)
    for n in nodes:
        t = n.get("type")
        if t and t not in KNOWN_NODE_TYPES:
            errors.append(
                f"Node {n.get('id')} has unknown type {t!r}. "
                f"Retell accepts: {sorted(KNOWN_NODE_TYPES)}"
            )

    # 11a. Function nodes must declare `tool_type`. Retell's import schema rejects
    # function nodes without it — the most common values are "local" (custom tool
    # defined in conversationFlow.tools[]) and "end_call" (built-in).
    for n in nodes:
        if n.get("type") != "function":
            continue
        if not n.get("tool_type"):
            errors.append(
                f"Function node {n.get('id')} is missing required field `tool_type`. "
                f"Use `\"tool_type\": \"local\"` for custom tools defined in conversationFlow.tools[]."
            )
        if "wait_for_result" not in n:
            warnings.append(
                f"Function node {n.get('id')} has no `wait_for_result` set. "
                f"Almost always you want `\"wait_for_result\": true` so downstream nodes can read the response."
            )

    # 11b. Subagent nodes must use `tool_ids` (plural), not `tools`. Common bug —
    # the `tools` field on a subagent makes Retell's import oneOf fail because
    # the subagent schema has no such property.
    for n in nodes:
        if n.get("type") != "subagent":
            continue
        if "tools" in n:
            errors.append(
                f"Subagent node {n.get('id')} has a `tools` field — Retell expects "
                f"`tool_ids` (plural, array of tool_id strings). Rename `tools` to `tool_ids`."
            )
        tool_ids = n.get("tool_ids")
        if tool_ids is not None:
            if not isinstance(tool_ids, list):
                errors.append(
                    f"Subagent node {n.get('id')}.tool_ids must be a list of strings, got {type(tool_ids).__name__}."
                )
            else:
                tool_registry_ids = {t.get("tool_id") for t in (cf.get("tools") or []) if isinstance(t, dict)}
                for tid in tool_ids:
                    if not isinstance(tid, str):
                        errors.append(
                            f"Subagent node {n.get('id')}.tool_ids must contain strings, got {type(tid).__name__}: {tid!r}"
                        )
                    elif tool_registry_ids and tid not in tool_registry_ids:
                        warnings.append(
                            f"Subagent node {n.get('id')}.tool_ids references {tid!r} but no tool with that "
                            f"tool_id exists in conversationFlow.tools[]."
                        )

    # 12. Voice config — voice_model paired with the wrong voice provider triggers
    # an opaque import error ("Selected voice model X is not supported for this
    # voice provider"). Production agents (e.g. Aubrey) omit voice_model and let
    # Retell pick the provider's default. Warn when it's set.
    if data.get("voice_model"):
        warnings.append(
            f"Agent has voice_model={data['voice_model']!r} set. If the voice provider "
            f"doesn't support that model, import fails with a noisy error. Consider "
            f"omitting voice_model and letting Retell pick the provider default."
        )

    # 13. Tool config — production-validated defaults are args_at_root: true and
    # parameter_type: "form". Tools without these still import but the webhook
    # contract may surprise you (args nested under `args:{}` vs spread at root).
    for tool in tools:
        if tool.get("type") != "custom":
            continue
        if "args_at_root" not in tool:
            warnings.append(
                f"Tool '{tool.get('name','?')}' has no `args_at_root` set. The default may "
                f"differ from your webhook's expectation. Production agents use "
                f"`args_at_root: true` (LLM args spread at body root)."
            )
        if "parameter_type" not in tool:
            warnings.append(
                f"Tool '{tool.get('name','?')}' has no `parameter_type` set. Production "
                f"agents use `\"parameter_type\": \"form\"`."
            )

    return errors, warnings


def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_flow.py <path/to/agent.json>", file=sys.stderr)
        sys.exit(2)

    path = Path(sys.argv[1])
    print(f"Validating: {path}")

    errors, warnings = validate(path)

    if warnings:
        print("\n--- WARNINGS ---")
        for w in warnings:
            print(f"  ! {w}")

    if errors:
        print("\n--- ERRORS ---")
        for e in errors:
            print(f"  X {e}")
        print(f"\nFAIL: {len(errors)} error(s), {len(warnings)} warning(s)")
        sys.exit(1)

    print(f"\nPASS: 0 errors, {len(warnings)} warning(s)")
    sys.exit(0)


if __name__ == "__main__":
    main()
