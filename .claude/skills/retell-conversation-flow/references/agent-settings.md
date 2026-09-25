# Agent-Level Settings, Versions and Publishing

The conversation flow is only half the agent. These fields live on the **agent object**, not in `conversationFlow`, and they decide how the call *feels* — when the agent speaks, when it gives up, what it does when a machine answers. A perfect graph with bad agent settings still produces bad calls.

Set them in the same script that builds the flow, never by hand in the dashboard, or they drift (see [Dashboard drift](#dashboard-drift)).

---

## The settings that matter

| Field | House default | Why |
|---|---|---|
| `enable_backchannel` | **`false` — always** | See below. Non-negotiable. |
| `interruption_sensitivity` | `0.8` agent-wide, **`0` on the opening node** | Nobody legitimately barges into a 4-second greeting, and line echo does (see anti-pattern 15). |
| `responsiveness` | `0.9`–`1.0` | How fast the agent takes its turn. Lower only for deliberate/elderly callers. |
| `end_call_after_silence_ms` | `30000`–`50000` | Platform defaults are far too generous. Do the dead-air arithmetic below. |
| `reminder_trigger_ms` / `reminder_max_count` | `20000` / `2` | The nudges before the silence timeout. |
| `ring_duration_ms` | `30000` | Outbound only: how long an unanswered call rings before it ends as `dial_no_answer`. |
| `begin_message_delay_ms` | `400` inbound, unused outbound | Inbound, the caller is already waiting. Outbound, use `start_speaker: "user"` instead. |
| `stt_mode` | `"fast"` | `"accurate"` buys letter-perfect transcription at roughly a couple hundred ms per turn. Worth it only if the agent spells things back. |
| `denoising_mode` | `"noise-cancellation"` | Callers ring from cars and lobbies. |
| `boosted_keywords` | brand, product, staff names | The cheapest accuracy win there is. |
| `voicemail_option` | static text | See [Answering machines](#answering-machines). |
| `max_call_duration_ms` | `600000` | A runaway call is a billing event. |
| `webhook_url` + `webhook_events` | `["call_analyzed"]` | The only event carrying the summary and the analysis fields. |
| `post_call_analysis_data` | per flow | See `post-call-analysis.md`. |

### `enable_backchannel` — keep it `false`

Backchanneling makes the agent inject "mm-hm" / "right" while the caller is talking. **Set it to `false` and leave it there.** It is deprecated in practice: modern Retell voices already carry acknowledgement in their delivery, and the injected tokens land on the wrong beat — over a caller mid-sentence, or in a pause the caller was about to fill — which reads as interrupting, not attentive. It also gives the STT more of the agent's own audio to mistake for caller speech.

Do not set `backchannel_frequency` or `backchannel_words` either. If a build inherits `enable_backchannel: true` from an older agent or an exported JSON, strip it. `validate_flow.py` errors on it.

### Dead-air arithmetic

Reminders and the silence timeout **stack**; the timeout clock starts after the last agent turn, which is the last reminder. So:

```
worst-case dead air  ≈  reminder_trigger_ms × reminder_max_count  +  end_call_after_silence_ms
20 s × 2  +  89 s   =   ~129 s   ← what a 90-second platform default actually costs
20 s × 2  +  30 s   =   ~70 s    ← a sane setting
```

Measure it on a real call before quoting a number to a client: a caller who went quiet at 0:20 hearing the line close at 2:29 is the complaint you will receive. Don't go below ~30 s: a caller who says "hold on" while they find their diary needs that room.

### Answering machines

Two mechanisms, and they must agree:

1. **Platform** — `voicemail_option: {action: {type: "static_text", text: "..."}}`. Retell detects the machine and plays this after the tone. Static text, not a prompt, so no variable can leak into a recorded message.
2. **Flow** — the opening node needs a rule that a recorded greeting is *not* a person: stay silent (`NO_RESPONSE_NEEDED`), and never restart the opener because a recording talked over it. Without this the agent opens over the greeting and restarts two or three times before detection fires. See Pattern 9 in `standard-patterns.md`.

---

## Versions and publishing

This is where "I fixed it" and "the caller still hears the bug" diverge.

- Editing a flow or an agent writes to the **draft**. Real calls do not see the draft.
- `publish-agent` freezes the current draft as a published version **N** and opens a new draft **N+1**. So a freshly published agent always reports `is_published: false` on its newest version — that is the new draft, not a failure.
- A phone number binds to `latest_published` (or a pinned integer). Publishing is what moves live traffic.
- `create-phone-call` takes `override_agent_version`: `"latest"` (the draft), `"latest_published"`, or an integer. This is how you test a draft on a real phone without exposing it to real callers.
- The agent's `response_engine.version` pins which **flow version** that agent version runs. Publishing the agent is what carries the flow change live.

**Always read back what you published**, in the same script, before you tell anyone it is fixed:

```python
pub = max(v["version"] for v in get(f"/get-agent-versions/{agent_id}") if v["is_published"])
agent = get(f"/get-agent/{agent_id}?version={pub}")
flow  = get(f"/get-conversation-flow/{agent['response_engine']['conversation_flow_id']}"
            f"?version={agent['response_engine']['version']}")
assert "the sentence you just added" in flow["nodes"][...]["instruction"]["text"]
assert sorted({t["url"] for t in flow["tools"]}) == [PROD_WEBHOOK]   # never ship dev tools live
```

The tool-URL assertion has caught more near-misses than any other check: a flow built for testing points at a sandbox backend, and publishing it sends real callers to a backend with no real data.

> Retell's list endpoints are inconsistent about envelopes — some return a bare list, some `{"items": [...]}`. Write `vs = r.get("items", r) if isinstance(r, dict) else r` or your verification crashes *after* the publish succeeded.

---

## Dashboard drift

Clients and colleagues edit agents in the dashboard: a rename, `start_speaker`, responsiveness, a voice change. A rebuild from your script silently reverts all of it, and the next call sounds wrong for reasons nobody can trace.

Rules:
1. Carry every human-set value explicitly in the builder (a `carry` list of keys copied from the live agent), and set the ones you own on purpose.
2. Assert the human-set values survive the build — abort rather than publish a regression.
3. When you change something in the dashboard to test it, port it into the builder the same day.

---

## Building a sibling agent: transform, don't fork

When a second agent (outbound twin of an inbound flow, Spanish twin of an English one) must stay in step, **do not copy the JSON**. Write a build script that pulls the source flow from the API on every run and re-applies a declared patch set: renamed nodes, replaced instructions, extra nodes, rewired edges. Fix the source, re-run, and the fix ports over.

Make the script paranoid — every assumption gets an assertion, because an inherited flow changes shape without telling you:

- the edge you are about to rewire still exists and points where you think
- the paragraph you are about to string-replace occurs exactly once
- every variable that means something different on the twin (a caller-ID variable is *the caller* inbound but *your own outbound line* outbound) is gone from nodes, tool schemas **and** the global prompt
- earlier fixes are still present in the source (guard on a distinctive sentence from each)

A build that aborts is cheap. A published twin that books appointments against the wrong phone number is not.
