# Post-Call Analysis

Retell runs an LLM after the call to extract structured data. Configured at agent level. The output appears in Retell's call history and can be filtered/exported.

---

## Configuration

```json
"post_call_analysis_model": "gpt-4.1",
"post_call_analysis_data": [
  {
    "name": "Caller intent",
    "type": "enum",
    "choices": ["booking", "cancellation", "info_request", "complaint", "other"],
    "description": "Primary purpose of the call"
  },
  {
    "name": "Resolution status",
    "type": "enum",
    "choices": ["resolved", "transferred", "ticket_created", "abandoned"]
  },
  {
    "name": "Caller sentiment",
    "type": "enum",
    "choices": ["positive", "neutral", "frustrated", "angry"]
  },
  {
    "name": "Number of escalation attempts",
    "type": "number"
  },
  {
    "name": "Was AI disclosure made",
    "type": "boolean"
  },
  {
    "name": "Call summary",
    "type": "string",
    "description": "Two-sentence summary of what happened on the call"
  }
]
```

---

## Field types (verified)

| Type | Purpose | Example use |
|---|---|---|
| `enum` (with `choices: []`) | Constrained selection from fixed list | Issue type, resolution status, sentiment bucket |
| `number` | Quantitative measurements | Transaction amount, satisfaction score, ticket count |
| `string` | Free-form textual extraction | Call summary, action items, intent description |
| `boolean` | Yes/no determinations | First-time caller, escalation needed, deal closed |

---

## Important constraint

> "We will not populate custom post-call analysis fields for calls that were not connected or where no conversation took place." — Retell docs

Always check field existence before reading. Filter out unconnected calls in your downstream pipeline.

---

## Use cases

### Quality scoring
- "Was AI disclosure made" (boolean)
- "Did agent follow opening script" (boolean)
- "Was caller sentiment positive at end of call" (boolean)

### Pipeline analytics
- "Caller intent" (enum) — volume by use case
- "Resolution status" (enum) — first-call resolution rate
- "Was caller routed to human" (boolean) — escalation rate

### Downstream automations
- "CRM update needed" (boolean) — gates a webhook to your CRM
- "Lead score" (number) — sales prioritization
- "Compliance flag" (boolean) — surfaces calls needing audit

### Content extraction
- "Call summary" (string) — for transcripts in CRM
- "Action items" (string) — for follow-up tracking

---

## Filtering and dashboards

Retell's dashboard supports filtering call/chat history by custom post-call analysis fields (enum, boolean, number types). Configure thoughtfully — well-named enum fields become powerful slicers for analytics.

---

## IVR navigation fields (outbound only)

For agents that traverse IVR systems, configure these 9 dedicated fields. They're critical for debugging — without them you can't tell why a campaign failed.

```json
{ "name": "hit_ivr",            "type": "boolean", "description": "Did the agent encounter an IVR" },
{ "name": "reached_human",      "type": "boolean", "description": "Did the agent eventually reach a human" },
{ "name": "ivr_loop",           "type": "boolean", "description": "Did the IVR send the agent in a loop" },
{ "name": "ivr_type",           "type": "string",  "description": "Voice-prompt vs DTMF-only vs hybrid" },
{ "name": "ivr_outcome",        "type": "enum",    "choices": ["reached_target", "wrong_company", "voicemail", "abandoned"] },
{ "name": "ivr_steps_count",    "type": "number",  "description": "Number of IVR menu choices made" },
{ "name": "ivr_retries_count",  "type": "number",  "description": "Number of times agent had to repeat or back out" },
{ "name": "ivr_path",           "type": "string",  "description": "Sequence of choices, e.g., 1 -> 3 -> 2" },
{ "name": "ivr_notes",          "type": "string",  "description": "Free-form observations" },
{ "name": "ivr_tree_text",      "type": "string",  "description": "Reconstructed IVR menu tree" }
```

---

## Configuration tips

1. **Configure early.** Adding fields incrementally during build is much cheaper than retrofitting after launch. Even rough field names get refined fast.
2. **Use enums liberally.** They're the most useful for filtering. A `string` field of free-form sentiment is much weaker than an enum bucket.
3. **Add a `call_summary` string.** Always useful in CRM / handoff contexts.
4. **Pair with webhooks.** The post-call payload can be webhooked to your backend to drive automations (CRM updates, alerting, follow-up scheduling).
5. **Beware of overcounting.** If you set `Number of escalation attempts` (number) on every call, calls that didn't escalate at all will return `null` or `0` — make sure your pipeline handles both.
