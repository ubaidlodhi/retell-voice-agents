# GHL "Retainer Post-Call Router" — Build Guide

The GHL workflow that receives the n8n retainer decision (`DU0LE0flap97hU3W`) and routes each call outcome. This is the **decision/router** (Workflow #1); the **48-hour cadence** is a separate workflow (Workflow #2, `retainer-followup-cadence-workflow-guide.md`).

**Inbound webhook URL (this workflow's trigger):**
`https://services.leadconnectorhq.com/hooks/vHHnJlFVorkeBvqgaqqA/webhook-trigger/e290d737-a396-42d2-bda6-7a6422892aa2`

Samples for every action + callback phrasing have already been fired through it, so the fields are captured for mapping.

---

## Payload fields (reference as `{{inboundWebhookRequest.<field>}}`)

| Field | Notes |
|---|---|
| `contact.contact_id` | GHL contact id — use to match the contact |
| `contact.full_name` / `contact.first_name` / `contact.phone` / `contact.email` | contact details |
| `action` | the routing key (7 values below) |
| `agent` | `immediate` or `outbound` — gates enrollment |
| `callback_datetime` | caller's own words ("tomorrow around 6pm") |
| `callback_datetime_iso` | **absolute ISO 8601, PT offset** — use in "Wait until" |
| `callback_datetime_pacific` | California local time, `MM-DD-YYYY HH:MM AM/PM` (e.g. `08-26-2026 09:00 AM`) |
| `callback_parse_failed` | `true` when the time couldn't be parsed → route to a human task |
| `objection` | plain-English description of the caller's hesitation, or empty |
| `objection_branch` | `A`–`E`, `Other`, or empty — which scripted branch the objection maps to |
| `call_id` / `recording_url` / `transcript` | pass `recording_url` + `transcript` to Zapier for Repair Notes |
| `call_attempt` | outbound cadence attempt 1–5 (empty for immediate) |
| `lead_language` | English / Spanish |
| `retainer_outcome` | reporting detail behind `action` (see below) — do **not** route on this |
| `answered_by` | `Human` / `Voicemail` / `AutomatedSystem` / `NoAnswer` |
| `opt_out_flag` | `true` if a genuine stop request was made, even on a call whose `action` is `signed` — honor it for DND |
| `call_summary` | 1–3 sentence summary of the call |

### `retainer_outcome` values (reporting only)
`signed_on_call` · `already_signed` · `opt_out` · `warm_transfer` · `confirmed_decline` · `callback_scheduled` · `no_answer_voicemail_left` · `automated_no_contact` · `no_answer` · `not_client` · `bad_time` · `callback_requested_no_time` · `no_clear_outcome`

> **Where these facts come from (changed Aug 25, 2026):** `action` and every field above are now derived from a **GPT analysis of the transcript** inside n8n (`AI - Retainer Extract` → `Decide Action`), the same pattern the intake post-call workflow uses. Retell's own post-call analysis variables are **no longer used** for routing — they were mislabeling outcomes (a signer marked `Opt-Out Consent`, an automated "please hold" pickup marked `not_client`, `objection` always blank).

---

## Trigger setup
1. Trigger = **Inbound Webhook** (the URL above).
2. **Associate the contact** by `contact.contact_id` (preferred) or `contact.phone` / `contact.email`, so contact-scoped actions apply to the right person.

## Router = Switch on `{{inboundWebhookRequest.action}}`
Add one branch per `action`. Two families of behavior:

- **Enroll** (start the 48h cadence): ONLY from the Immediate agent, when the lead didn't sign — `agent == immediate` AND `action == continue`.
- **Stop / handle**: remove from cadence + action-specific handling. **The outbound cadence's own calls NEVER enroll.**

Keep **"Allow Re-Entry" OFF** on the cadence workflow so a duplicate Add is a safe no-op.

| `action` | GHL steps |
|---|---|
| `signed` | Remove from **Retainer Cadence** · tag "Retainer Signed" · **→ Zapier** (POST `recording_url`+`transcript`+`contact_id` → SF Repair Notes). No SF status change. |
| `already_signed_pending` | Remove/Pause cadence · **Create Task** "Verify signature" (human) · optional → Zapier |
| `schedule_callback` | Remove from cadence · **If `callback_parse_failed` = true → Create Task** "Call back — time unclear: {{callback_datetime}}". **Else → Wait until `{{...callback_datetime_iso}}`** → then place the callback (Custom Webhook → Retell create-phone-call, outbound retainer agent) |
| `declined` | Remove from cadence · save `objection` to a note · tag "Retainer Declined" · optional human-review task |
| `opt_out` | **DND all channels** · Remove from all workflows · apply your existing opt-out handling (Burnt Lead status + reason) |
| `human_requested` | Remove from cadence · notify/assign the intake team (intake owns it) |
| `continue` | The catch-all "keep the cadence running" bucket — covers no-decisive-outcome, **busy/no specific time (`bad_time`)**, **wrong number (`not_client`)**, and **voicemail/no answer (`no_answer`)**. **If `agent` = immediate → Add to Retainer Cadence** (finished walkthrough, didn't sign → start 48h cadence). If `agent` = outbound → no-op (cadence keeps running on schedule). |

> **Enrollment note:** the `continue` branch also catches an immediate-handoff lead who was busy with no specific time (agent `bad_time` → `continue`), so the `agent = immediate → Add to Cadence` step covers them — no separate branch needed.

## Callback call (inside `schedule_callback`, after the Wait)
Use a **Custom Webhook** action → `POST https://api.retellai.com/v2/create-phone-call` with the outbound retainer agent body (see `retainer-followup-call-payloads.md`), `override_agent_id = agent_83f8b296e4652030d15a3417e6`. This dials the lead at the committed time.

## Zapier / Repair Notes (inside `signed`, `already_signed_pending`)
Per the client design, recording + transcript go to the SF **"Repair Notes"** field via the **existing Zapier**. Fire a webhook to your Zapier catch hook with: `contact_id`, `full_name`, `phone`, `email`, `recording_url`, `transcript`, `call_id`. Nothing is stored on the GHL contact.

## What this workflow does NOT do
- Does **not** change the Salesforce Lead Status for retainer outcomes (signed/callback/decline/already-signed) — it stays as-is. Only `opt_out` (→ Burnt Lead) and `human_requested` use the existing Lead Status plumbing.
- Does **not** store recording/transcript on the contact — passed straight to Zapier.
