# Retell Conversation Flow — Edges and Transitions

The single biggest source of stuck/looping bugs is picking the wrong edge primitive or writing a too-loose transition condition. This reference covers all four primitives, both condition types, the verified evaluation order, and how to use few-shot examples to disambiguate edges.

---

## The four edge primitives

| Primitive | Fires when | Use for |
|---|---|---|
| `edges[]` | After the next user turn, LLM evaluates each edge's condition and picks the matching one | Multi-turn collection, branching on caller answer |
| `always_edge` | After every agent turn at this node | Function/code/tool nodes; one-shot transitions |
| `skip_response_edge` | When agent's response is "Skip response", fires silently | Single-line submit nodes that don't need a user turn |
| `else_edge` | When no other edge matches | **Required** on `branch`, `extract_dynamic_variables`, `code` nodes |

### Picking the right primitive

```
Multi-turn collection node?           → conditional edges[]
Single-line "submit" before tool?     → skip_response_edge
Function/code/MCP node, exit after?   → always_edge
Branch / extract / code node?         → edges[] + mandatory else_edge
Variable-driven routing, no agent?    → branch (with edges[] + else_edge)
```

### Pitfalls

- **`always_edge` on a multi-turn collection node** fires after the first question, abandoning the flow. Conditional `edges[]` only.
- **`skip_response_edge` on a multi-turn node** doesn't reliably fire — only single-purpose nodes with one short line.
- **Missing `else_edge`** on a branch/extract/code node = silent dead-end if no condition matches.

---

## Transition condition types

Every edge has a `transition_condition` object with a `type` field. There are exactly two types.

### `type: "prompt"` — LLM-evaluated natural language

```json
{
  "transition_condition": {
    "type": "prompt",
    "prompt": "Caller has provided their date of birth and zip code"
  }
}
```

The LLM checks whether the prompt matches the conversation history and picks the matching edge. **Be specific** — loose prompts ("if caller wants help") match too many cases.

### `type: "equation"` — Programmatic condition (deterministic)

```json
{
  "transition_condition": {
    "type": "equation",
    "equations": [
      { "left": "{{age}}", "operator": ">=", "right": "18" },
      { "left": "{{state}}", "operator": "==", "right": "CA" }
    ],
    "operator": "&&"
  }
}
```

#### Verified operator list (from official Retell docs)

> **These are the EXACT literal strings Retell's import schema accepts — copy them verbatim.** The full allowed enum is `==, !=, >, >=, <, <=, contains, not_contains, exists, not_exist`. Anything else fails import with an opaque `oneOf` error. `validate_flow.py` now checks this — run it before delivering.
>
> ⚠️ **UI label ≠ JSON value.** Retell's public docs (and the dashboard equation editor) show these as human-readable labels — `CONTAINS`, `NOT CONTAINS`, `does not exist`, `Not Equal`. Those are **display labels, not the JSON the import API takes.** When you hand-author flow JSON, use the lowercase snake_case forms above (`contains`, `not_contains`, `not_exist`, `!=`). Don't copy the operator strings out of the docs verbatim — they're the UI form.

| Operator | Type | Notes |
|---|---|---|
| `==` | String comparison | Case-sensitive equality |
| `!=` | String comparison | Inverse of `==` |
| `>` / `>=` / `<` / `<=` | Numeric only | If either side isn't a number, evaluates to `false` |
| `contains` | String | Substring match (lowercase). **Direction matters:** `left contains right` checks if `right` is a substring of `left` — e.g. `{{bad_lead_reason}} contains "possession"`. |
| `not_contains` | String | Inverse of `contains` |
| `exists` | Variable presence | True when variable is defined and has a value. Takes only a left operand (no `right`). |
| `not_exist` | Variable presence | True when variable is undefined or empty (singular — **no** trailing `s`). Takes only a left operand. |

#### Combiner operators

- `AND` (`&&`) — all equations must be true (visual editor: "ALL")
- `OR` (`||`) — any one equation true (visual editor: "ANY")

#### Examples

```
{{user_age}} > 18
{{current_hour_America/Los_Angeles}} >= 8 AND {{current_hour_America/Los_Angeles}} < 20
{{user_location}} == "New York"
{{bad_lead_reason}} contains "possession"
{{name}} exists
{{ticket_id}} not_exist
```

> **Single-equation edges still need the top-level combiner.** Even one equation requires `"operator": "&&"` on the `transition_condition`. For an OR across two existence checks, prefer two single-equation edges to the same destination over one `||` edge — simpler and unambiguous at import.

> **Hours-gating tip:** `{{current_time}}` is a formatted **string** ("Thursday, March 28, 2024 at 11:46 PM PST") — numeric `>`/`<` on it always evaluates false. For business-hours checks use `{{current_hour_<IANA_TZ>}}`, a **numeric 24h fraction** (`8` = 8:00 AM, `19.5` = 7:30 PM). Day-of-week is **not** a system variable — pass it as a dynamic variable, or gate weekdays with a prompt edge.

---

## Evaluation order — critical rule

**Equation conditions evaluate first, top to bottom. Then prompt conditions evaluate.** The agent transitions on the **first** matching condition.

This means:
- Put hard-deterministic checks (variable comparisons) as `equation` edges at the top.
- Use `prompt` edges only for cases requiring LLM reasoning (intent detection, free-form caller statements).
- A `prompt` edge will never fire if a higher-priority `equation` edge already matched — useful for short-circuit logic.

### Practical pattern

```json
"edges": [
  {
    "id": "edge-already-submitted",
    "transition_condition": {
      "type": "equation",
      "equations": [{ "left": "{{ticket_id}}", "operator": "exists" }]
    },
    "destination_node_id": "node-already-submitted-explanation"
  },
  {
    "id": "edge-distress",
    "transition_condition": {
      "type": "prompt",
      "prompt": "Caller expresses acute emotional distress, mentions self-harm, or says they cannot continue"
    },
    "destination_node_id": "node-escalate-distress"
  },
  {
    "id": "edge-collected",
    "transition_condition": {
      "type": "prompt",
      "prompt": "Caller has provided all required fields"
    },
    "destination_node_id": "node-submit"
  }
]
```

The equation edge short-circuits the duplicate-submission case before any prompt edges fire.

---

## When to use equation vs prompt

| Use case | Choose |
|---|---|
| Variable value comparison | `equation` — deterministic, free, instant |
| Caller intent detection | `prompt` — LLM understands paraphrasing |
| "Already submitted" gate | `equation` on `{{ticket_id}} exists` |
| "Caller agreed" routing | `prompt` ("if customer agreed") |
| Time-of-day branching | `equation` on `{{current_hour_<TZ>}}` (numeric fraction, e.g. `14.5` = 2:30 PM) — **not** `{{current_time}}` (a string) |
| Sentiment/tone routing | `prompt` ("if caller sounds frustrated") |
| Tier-based routing | `equation` on `{{customer_tier}} == "VIP"` |
| Confirmation rejection | `prompt` ("caller said no, that's wrong, or asked to correct") |

Mix both freely — equations short-circuit cheap deterministic cases; prompts handle the rest.

---

## Edge UI metadata

```json
{
  "id": "edge-collected",
  "condition": "All fields collected",
  "transition_condition": { "type": "prompt", "prompt": "Caller has provided all required fields" },
  "destination_node_id": "node-submit",
  "finetune_transition_examples": [ ... ]
}
```

The `condition` field is a UI label — actual matching is `transition_condition.prompt`. Keep them aligned.

---

## `finetune_transition_examples` — Few-shot edge teaching

Attach example transcripts to teach the LLM exactly when to fire an edge. Dramatically improves accuracy on ambiguous prompt conditions.

```json
"finetune_transition_examples": [
  {
    "destination_node_id": "node-yes-path",
    "transcript": [
      { "role": "user", "content": "Yes, please proceed." },
      { "role": "agent", "content": "" }
    ],
    "id": "fe-1"
  },
  {
    "destination_node_id": "node-yes-path",
    "transcript": [
      { "role": "user", "content": "Sure, that sounds good." },
      { "role": "agent", "content": "" }
    ],
    "id": "fe-2"
  },
  {
    "destination_node_id": "node-no-path",
    "transcript": [
      { "role": "user", "content": "No, I don't want to." },
      { "role": "agent", "content": "" }
    ],
    "id": "fe-3"
  },
  {
    "destination_node_id": "node-no-path",
    "transcript": [
      { "role": "user", "content": "Not right now, maybe later." },
      { "role": "agent", "content": "" }
    ],
    "id": "fe-4"
  }
]
```

Three or four examples per ambiguous edge typically resolves most issues. Use these on edges that misfire in testing — a near-miss positive and a near-miss negative is the right minimum.

---

## Edge ID uniqueness

**Every edge ID across the entire flow must be unique** — including IDs nested inside `always_edge`, `skip_response_edge`, `else_edge`, `edge`, `success_edge`, `failed_edge`. Duplicates cause opaque import errors.

Common cause: copy-pasting a node and forgetting to rename. Run [`scripts/validate_flow.py`](../scripts/validate_flow.py) before every commit.

---

## Magic strings

Retell recognizes specific literal strings:

| String | Where | Effect |
|---|---|---|
| `"Skip response"` | `skip_response_edge.transition_condition.prompt` | Silent transition after a single-line node |
| `"Always"` | `always_edge.transition_condition.prompt` | Fires after every agent turn |
| `"Else"` | `else_edge.transition_condition.prompt` | Fires when no other edge matches |
| `"Transfer failed"` | `transfer_call` node's `edge.transition_condition.prompt` | Routes to fallback when transfer dial fails |
| `end_call` | Function callable from agent | Terminates the call (e.g., when an IVR routes wrong) |
| `NO_RESPONSE_NEEDED` | LLM output (in agent text) | Suppresses TTS for that turn — agent stays silent |

Variable-existence syntax (in equation conditions only):
- `{{var}} exists` / `{{var}} not_exist`  (literal operator strings; `not_exist` is singular)
