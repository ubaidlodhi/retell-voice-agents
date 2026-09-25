# Backend Contract — what the webhook side owes the agent

A conversation flow is only as good as the endpoints behind it. These rules come from production calls that went wrong on the backend, not in the graph.

---

## 1. Keep tool results small

**Retell silently drops a tool result that is too large.** The agent then behaves as if the tool returned nothing — it apologises, or invents. Observed threshold: somewhere around **12–19 KB**; treat **10 KB as the budget** and leave headroom.

The fix is two response shapes behind one tool, not a smaller `limit`:

| Call | Returns |
|---|---|
| `get_services` with no filter | **catalog**: name + one-line description + a price summary string, for all items |
| `get_services` with a name | **detail**: that one item, with durations, prices, variant IDs, add-ons |

The agent reads the catalog aloud, the caller picks, the second call brings the detail needed to book. Strip everything the agent will never say: media URLs, locale blocks, SEO fields, timestamps, internal flags. A raw upstream API response is almost never a safe tool result — reshape it in the workflow.

Log the serialized byte length of every tool response while developing. A payload that grows with the client's catalog will cross the threshold months after you ship.

---

## 2. Resolve IDs server-side — never make the model carry a UUID

LLMs garble long opaque strings: a digit changes, a block is dropped, a plausible-looking ID is invented outright. Any flow where the model reads a UUID from one tool result and passes it to the next tool **will** produce corrupted bookings.

So the tool schema should take **what a human said**, and the backend resolves it:

| Model sends | Backend resolves |
|---|---|
| service name + duration in minutes | the variant/price ID |
| the time the caller agreed to | the schedule/slot ID, from the live availability response |
| the caller's phone | their contact record, and their booking, and its revision |
| "no preference" for staff | an available person for that slot |

Where the model must pass an ID, **validate it against that caller's own records** before acting, and fail loudly if it does not belong to them. Have the backend return a clean, human-scale envelope (`success`, a short message, the few fields the agent will actually say) so the flow's edges can key off simple values.

---

## 3. Retry transient failures before the caller hears about them

A single DNS blip or a dropped TCP connection on the host running your workflow surfaces to the caller as "I can't pull that up right now" — on a call that was otherwise going fine.

- Enable node-level retry on **every** outbound HTTP node: 3 attempts, ~1 s apart. It sits *in front of* your error branch, so graceful failure handling still works, it just stops firing on the first stumble.
- Keep `timeout_ms: 120000` on the Retell tool for cold-start backends, and pair it with `speak_during_execution` so the caller hears a pinned filler line rather than silence.
- Retrying a **write** (create/cancel/reschedule) can duplicate if the upstream applied the first attempt and only the response was lost. Either make the write idempotent (dedupe key, or look up before creating), or accept the risk knowingly — and tell whoever owns the calendar which you chose.

---

## 4. Fail honestly

A failed tool must produce a truthful envelope the flow can route on, and the node that handles it must not guess:

```
"I can't pull up the exact rates right now, but someone from the team can confirm and get back to you.
 Want me to set that up?"
```

Never let a failure path invent a value, and never let it read an error code or a URL aloud. Pair every tool node with a failure destination — collect a callback, or hand to a human — and make sure `tool_failure` is a post-call analysis field so these calls are findable later.

---

## 5. Post-call webhook: build the record from tool results, not from the model

Subscribe to `call_analyzed` (it is the only event carrying the summary and the analysis fields) and derive the outcome from **what the tools actually returned**, in this order of trust:

1. a successful `book_appointment` / `cancel_booking` result → that is what happened
2. the post-call analysis enum
3. the free-text summary

The model's own label drifts; a tool result does not. Then suppress the noise before anyone is notified:

- machine outcomes: `dial_no_answer`, `dial_busy`, `dial_failed`, `voicemail_reached`, `in_voicemail`, `call_status != ended`
- calls with **zero caller turns** (the greeting played, they hung up)
- internal test numbers, matched on the **last ten digits** so formatting never defeats the check

Everything else is a real conversation and worth a notification.

---

## 6. Test the backend with dummy data before a live call

Fire each tool at the real endpoint with a realistic payload — curl, or a replay of a previous request — and read the response. "The workflow contains the right strings" is not a test; an edit that breaks a field name passes that check and fails on a customer call.

Where the backend writes to a real calendar or CRM, keep the read-only probes (catalogue, availability, lookup by an unused test number) as a smoke test you can run any time, and keep the write path for a deliberate end-to-end test whose bookings you then clean up.
