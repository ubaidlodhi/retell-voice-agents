# Anti-Patterns and Failure Modes

Field-tested failure modes from production conversation-flow builds. Each entry has a concrete symptom, the root cause, and the fix.

---

## 1. Instructing Silence

**Don't write:**
```
AFTER LAST FIELD — DO NOTHING:
Once the caller has answered question N, STOP IMMEDIATELY.
Do NOT generate ANY further text.
The system transitions automatically.
```

**Why it fails:** when a conditional edge requires the next user turn to evaluate, the agent is forced to produce a turn first. Told to "do nothing", the LLM:
1. Reads the stage direction aloud verbatim ("[No further response. The intake is complete and the system will transition automatically.]")
2. Hallucinates that something has been completed and improvises a closing
3. Reaches for the most recent disclosure and recites it

**Correct pattern:**
```
AFTER LAST FIELD:
Say EXACTLY: "Got it — one moment."
Then STOP.
DO NOT use brackets [ ] in your response — never.
DO NOT deliver any closing or stage directions.
```

The throwaway acknowledgment line gives the LLM a deterministic action and triggers the next edge.

**Generalized rule:** never instruct the LLM to be silent. Either give it a specific line to say, or use `always_edge` / `skip_response_edge` / `branch` to transition without giving the agent a turn.

---

## 2. Anti-Duplicate Prose Guards

**Don't write:**
```
If a ticket has already been created in this call, do not collect again.
Say "Your ticket has already been submitted."
```

**Why it fails:** the guard depends on the LLM correctly reading history. The LLM is unreliable at this — it fires the guard prematurely after any prior agent turn it can't fully parse (a stage-direction read-out, an empathy line, a long disclosure).

**Correct pattern:** prevent re-entry at the **edge level**, not via prose:
- Tighten the Confirmation node's edges so they don't loop back to collection.
- Add an `equation` edge at the **top** of every collection node:
  ```json
  {
    "transition_condition": {
      "type": "equation",
      "equations": [{ "left": "{{ticket_id}}", "operator": "exists" }]
    },
    "destination_node_id": "node-already-submitted"
  }
  ```
  Equations evaluate before prompts, so this short-circuits any prose-based collection logic.
- Or use a `branch` node before the collection node to deterministically route on `{{ticket_id}} exists` / `does not exists`.

**The single biggest win** from understanding equation-based transitions — what used to require fragile prose guardrails is now one deterministic edge.

---

## 3. `always_edge` on Multi-Turn Collection Nodes

**Symptom:** flow exits after the first question, abandoning the rest of the intake.

**Cause:** `always_edge` fires after **every** agent turn at this node. It's only correct on single-purpose nodes like function/code/tool nodes that exit immediately after producing one output.

**Fix:** remove the `always_edge`. Use conditional `edges[]` that match "all fields collected" or "ready to submit."

---

## 4. Inline Conditional Dynamic Variables

**Don't write in agent instructions:**
```
say "Just to confirm — that's {{caller_name}}, right?"
```

**Why it fails:** when `caller_name` is empty, the LLM substitutes literally — caller hears "that's bracket-name-bracket, right?" or whatever STT produced.

**Correct pattern:** fact-style global Caller Context (in the global prompt):
```
CALLER CONTEXT (verify, don't re-collect):
Name: {{caller_name}}
Phone: {{caller_phone}}

Rule: if a value is empty, ask fresh. If present, confirm: "I have your name as [value], is that right?"
```

Push the conditional logic into the LLM's natural reasoning instead of template substitution. Empty variables produce empty facts — the LLM correctly asks fresh.

---

## 5. Loose Edge Conditions

**Don't write:**
```
"Caller wants help"
"Ready to submit"
"Caller indicated yes"
```

**Why it fails:** these match a huge superset of intended cases. The LLM fires the edge on minor agreement noises ("uh-huh"), unrelated affirmations ("yes I did"), or partial answers.

**Correct pattern:** be specific. Add `finetune_transition_examples` for ambiguous prompts.
```
"Caller has explicitly agreed to proceed with booking AND has confirmed the time slot offered"
```

---

## 6. Combining Collection + Closing + Tool Call in One Node

**Symptom:** LLM forgets it already spoke a closing and re-delivers it. Edge fires before closing line is said. Tool call has no clean wait surface.

**Fix:** split into the 4-node Standard Collection Pattern (see [`standard-patterns.md`](standard-patterns.md)):
```
[COLLECTION] → [SUBMIT] → [TOOL] → [CONFIRMATION]
```

Each node has one responsibility. Transitions are deterministic.

---

## 7. Tools with Placeholder URLs

**Symptom:** call breaks at the tool-call point with no clear error.

**Cause:** `url: "https://TODO.example.com/..."` silently fails at runtime.

**Fix:** always use a real URL or remove the tool reference entirely. The validation script catches placeholder-looking URLs.

---

## 8. Tool Without `execution_message_description`

**Symptom:** during tool wait (5–15s), agent improvises a different filler line every call. Sometimes "submitting now," sometimes "let me check," sometimes a multi-sentence ramble. Inconsistent UX.

**Fix:** pin the line:
```json
"speak_during_execution": true,
"execution_message_description": "Just a moment please, this will only take a second."
```

---

## 9. Duplicate Edge IDs

**Symptom:** opaque import error, often without a clear message.

**Cause:** copy-pasting a node and forgetting to rename its edges. IDs must be unique across the entire flow, including IDs nested inside `always_edge`, `skip_response_edge`, `else_edge`, `edge`, `success_edge`, `failed_edge`.

**Fix:** run [`scripts/validate_flow.py`](../scripts/validate_flow.py) before delivering. It surfaces duplicates immediately.

---

## 10. Loose Global Node Conditions

**Symptom:** global node fires mid-intake on minor frustration, hijacking the flow.

**Cause:** condition like "When user is upset" is too broad.

**Fix:** be specific:
```
"When user expresses acute emotional distress, mentions self-harm, or states they cannot continue the call"
```

Test mid-flow trigger scenarios — make sure routine answers don't accidentally satisfy the condition.

---

## 11. Missing `else_edge` on Branch / Extract / Code Nodes

**Symptom:** silent dead-end — flow stops with no error if no condition matches.

**Cause:** these node types don't fall through to a "default" — they require an explicit `else_edge`.

**Fix:** every `branch`, `extract_dynamic_variables`, `code` node gets an `else_edge` to a sensible fallback (apology + ticket creation, or a re-prompt node).

---

## 12. Equation Edge with Type Mismatch

**Symptom:** equation edge never matches.

**Cause:** numeric operator (`>`, `<`, `>=`, `<=`) on a non-numeric value evaluates to `false`. Or string comparison (`==`) where the expected value has different casing.

**Fix:** verify the variable type. If you're comparing against a number, ensure the variable was set as a number string ("18" not "eighteen"). For string equality, normalize casing in the comparison.

---

## 13. Tool Returns Variable that Tool Schema Doesn't Declare

**Symptom:** `{{ticket_id}}` shows as empty in downstream nodes.

**Cause:** tool's `response_variables` JSONPath doesn't resolve, or the response shape changed.

**Fix:** verify the tool actually returns the JSON shape declared. Test the webhook independently. Use Retell's call-replay UI to inspect tool responses.

---

## 14. Pre-call Variable Passed as Number/Boolean

**Symptom:** variable not injected; flow uses fallback or asks fresh.

**Cause:** `retell_llm_dynamic_variables` requires all values to be **strings**. Numbers, booleans, arrays, objects are rejected.

**Fix:** stringify before passing:
```python
{"caller_age": "42", "is_premium": "true", "balance": "1250.00"}
```

The LLM treats them naturally as their semantic type inside the agent.

---

## Common Failure Modes — Symptom-to-Fix Table

| Symptom | Root cause | Fix |
|---|---|---|
| Agent reads "[stage direction]" aloud | Instruction told it to be silent | Give a concrete line; use `always_edge` for silent transitions |
| Two tickets created | Collection node re-entered post-confirmation | Tighten confirmation edges; equation gate on `{{ticket_id}} exists` |
| Disclosure repeated 3× | No-repetition rule missing | Add explicit "deliver exactly once" rule in global prompt |
| Closing inside collection | Collection had closing prose | Move closing to dedicated submit/end node |
| Stuck after tool call | `always_edge` missing on function node | Add `always_edge` with destination |
| Variables show as `[Name]` literally | Inline conditional in instruction | Switch to fact-style global Caller Context |
| Agent talks over caller | `interruption_sensitivity` too low | Raise to 0.9–1.0 |
| Agent rambles during tool wait | `execution_message_description` empty | Pin the exact filler line |
| Wrong edge fires | Edge condition too loose | Make conditions specific; add `finetune_transition_examples` |
| `skip_response_edge` doesn't fire | Node has too many turns | Single-purpose nodes only |
| Duplicate edge ID import error | Copy-pasted node | Run validation script |
| Global node hijacks intake | Global condition too loose | Refine condition; test mid-flow scenarios |
| Equation edge always misses | Type mismatch (string vs number) | Cast values; check operator semantics |
| Pre-call variable empty | Passed as non-string | Stringify before sending to API |
| Tool variable empty downstream | JSONPath doesn't resolve | Verify webhook response shape; test independently |
| Branch silent dead-end | Missing `else_edge` | Add fallback `else_edge` |
| Transfer fails silently | No `Transfer failed` edge | Wire the singular `edge` to a fallback node |
| IVR mis-routes outbound | Begin message hits IVR | Set `begin_message_delay_ms`; tune `interruption_sensitivity` |
