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
- Or use a `branch` node before the collection node to deterministically route on `{{ticket_id}} exists` / `not_exist` (literal operators — `not_exist` is singular).

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

**Related — global node loops on repeated phrasing.** Even a well-scoped global (e.g. "talk to a human", FAQ) re-fires every turn if the caller keeps saying the trigger phrase, so the agent answers → returns → re-triggers → answers, never progressing. **Fix at the platform level, not with prose:** enable the global node's **Prevent Immediate Re-Trigger** (`prevent_immediate_re_trigger` — pauses the node for N node-steps after it fires; default 3), and use **Go back to previous node** with `go_back_conditions` so the flow resumes where it left off instead of restarting. Prose hacks like "don't repeat the number" are a weaker band-aid; the re-trigger lock is the documented cure for the human-request/FAQ loop class.

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

## 15. Line Echo — the agent answers itself

**Symptom:** on the greeting, the transcript shows a "caller" turn that is the agent's own opening line, chopped or garbled into other words — often a name that was never said. The agent's greeting is cut off, it replies to the echo, and the real caller hears a non-sequitur or silence.

**Cause:** some phone paths play the agent's own audio back on the caller channel about a second late, at low volume. STT transcribes it as a user turn. It happens almost exclusively **on the first turn** — network echo cancellers converge within a few seconds — and it is indistinguishable from a real interruption at the audio layer. (Confirm it by cross-correlating the two channels of the stereo recording: a strong peak at a ~0.5–1.5 s lag is echo, not a caller.)

**Fix, both halves:**
1. `interruption_sensitivity: 0` **on the opening node only**. Nobody legitimately barges into a four-second greeting, and echo always does.
2. An echo rule in the global prompt's Turn-Taking section: if the "caller" turn is something only you would say — your own name, your introduction, your question asked back at you — it is the line, not a person. Reply `NO_RESPONSE_NEEDED`. If it cut you off, say your sentence again from the start. Anything that could be an answer to your question is the caller: take it.

---

## 16. A Turn That Ends in a Statement

**Symptom:** the agent says something true and reasonable, then the call sits in silence until the reminder fires. Transcript looks fine; the caller simply had nothing to answer.

**Cause:** prompt transitions are judged on **the caller's next turn**. A node that ends its turn with a statement ("Two o'clock it is. Let me get that set up.") has given the caller nothing to say, so no edge can fire, so the node speaks again only when the reminder timer forces it.

**Fix:** every conversation node's turn ends with a question. Where a node must acknowledge something before moving on, put the acknowledgement at the **top of the next node's** instruction ("Two o'clock it is — would you like to add anything?"), where it is followed by a question. And never let a node decide on the caller's behalf: a bare "yeah, sure" answering a list of three times is not a choice — ask which one.

---

## 17. Writing a Stronger Sentence Instead of Changing the Graph

**Symptom:** the same misbehaviour survives three rounds of increasingly emphatic prose ("NEVER pick a service for them", "You MUST ask first", in caps, with examples).

**Cause:** the node has both the instruction *and* the capability. A node that can call the lookup tool will call it, because that is the path of least resistance to finishing the task.

**Fix:** make it structurally impossible. Split the step into its own node that carries **only** the tool it is allowed to use (e.g. a "choose the service" node with the catalogue tool and nothing else), and route every entry into the flow through it. Move the global trigger onto that node so no edge can reach the tool-bearing node early. Prose is a hint; node shape and `tool_ids` are the enforcement.

Rule of thumb: if a rule has failed twice in prose, it is a graph problem.

---

## 18. Re-asking Instead of Giving the Caller Something to Work With

**Symptom:** the agent asks the same question three times in a row and the caller hangs up. Common when the caller answered a *different* attribute than the one asked for (a duration, when asked which product).

**Cause:** the instruction says "if they did not answer, ask again."

**Fix:** keep what they gave you, and put the options in front of them in the same turn: *"Sure, ninety minutes. Which one did you want? We have [read the list the tool returned]."* Then add `finetune_transition_examples` for the near-miss: one example where a partial answer **stays** in the node, one where a real answer leaves it.

---

## 19. `exists` on a Variable That May Be Empty

**Symptom:** a branch takes the "we already have it" path on a call where the value was never supplied, and the agent greets a lead by an empty name — or reads literal curly braces aloud.

**Cause:** Retell's `exists` is **true for an empty string**, and a variable that was never injected renders as the literal `{{name}}` text in the prompt.

**Fix:** branch on an exact sentinel the caller's system sets on purpose (`{{name_known}} == "yes"`), not on `exists`. Make the else-path the safe one: a call placed with no dynamic variables at all should land in the branch that asks, never in the one that assumes. And keep a defensive line in the global prompt: never read a variable name or curly braces aloud.

---

## 20. Agent-First Openings on Outbound Calls

**Symptom:** the agent's opener collides with the callee's "Hello?", the model reads the collision as confirmation and skips to "what can I help you with", and the person hangs up never having heard why you rang.

**Cause:** inbound is agent-first because the caller dialled you and is waiting. Outbound is the reverse — the callee speaks first.

**Fix:** `start_speaker: "user"` with `begin_after_user_silence_ms` around 4000 (they picked up and said nothing). Tune `begin_message_delay_ms` only for the inbound case. Also add the answering-machine guard (Pattern 9) — a recorded greeting is the other thing that "answers" an outbound call.

---

## 21. Dangling `finetune_transition_examples` After a Refactor

**Symptom:** import succeeds, the edge misfires, and nothing in the graph looks wrong.

**Cause:** a transition example carries its own `destination_node_id`. Delete or rename the destination node — common when a twin agent drops a node the source flow had — and the example now points at a node that does not exist. Omitting `destination_node_id` means "stay in this node", which is a legitimate and useful case, so an empty value is not a bug but a stale one is.

**Fix:** remap examples whenever you rewire edges, and validate. `validate_flow.py` resolves every example destination and flags duplicates.

---

## 22. Confirming the Same Thing Three Times

**Symptom:** callers get audibly impatient during the readback; some hang up before the booking is submitted.

**Cause:** stacking verification: ask, read back, ask to confirm, then read the whole summary back again.

**Fix:** one readback, at the point of commitment, covering everything at once. For values where accuracy actually matters (names), ask for the **spelling** instead of a read-back — spelling is itself the confirmation and costs one turn instead of two. Ask for each field separately ("spell your first name" → wait → "and your last name?") rather than both in one question, which is what produces swapped first/last names.

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
| Agent answers its own greeting; a name nobody said appears as a caller turn | Line echo transcribed as speech | `interruption_sensitivity: 0` on the opening node + echo rule in Turn-Taking (15) |
| Long silence after a perfectly good agent line | That turn ended in a statement, so no edge could fire | End every turn with a question; move acknowledgements to the top of the next node (16) |
| Rule ignored no matter how forcefully it is written | Node has the instruction *and* the tool | Split into a node that only carries the allowed tool; route all entries through it (17) |
| Same question asked three times, caller hangs up | "If they did not answer, ask again" | Keep their partial answer and read the options in the same turn (18) |
| Branch takes the "already known" path on an empty value | `exists` is true for an empty string | Branch on an exact sentinel string; make the else-path the safe one (19) |
| Outbound opener collides with "Hello?" | Agent-first start on an outbound call | `start_speaker: "user"` + `begin_after_user_silence_ms` (20) |
| Agent talks over an answering machine and restarts | Opener fires on the recorded greeting | Recording-is-not-a-person rule + `voicemail_option` (Pattern 9) |
| First and last name swapped in the booking | Both names asked in one question | Ask each separately, request the spelling, no read-back (22) |
| Edge misfires after a refactor, graph looks fine | Stale `destination_node_id` in a transition example | Remap examples when rewiring; run the validator (21) |
| Agent behaves as if the tool returned nothing | Tool result over Retell's size limit, silently dropped | Catalog/detail response shapes, ~10 KB budget (`backend-contract.md` §1) |
| Booking lands against a mangled or invented ID | Model carried a UUID between tool calls | Resolve IDs server-side from human-scale values (`backend-contract.md` §2) |
| "I can't pull that up" on an otherwise healthy call | One transient network failure, no retry | 3 retries ~1 s apart on every outbound HTTP node (`backend-contract.md` §3) |
| Fix published but callers still hear the bug | Draft edited, agent never published, or number pinned | Publish, then read the published version back and assert (`agent-settings.md`) |
| Dead line stays open for two minutes | Reminders and `end_call_after_silence_ms` stack | Do the dead-air arithmetic; 30–50 s total (`agent-settings.md`) |
