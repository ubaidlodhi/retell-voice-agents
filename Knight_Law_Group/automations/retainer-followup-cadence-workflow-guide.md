# Retainer Follow-Up Cadence — GHL Workflow Build Guide

Builds the 48-hour outbound cadence (Alice Retainer, Flow B) from spec **§2**. Content lives in:
- SMS → `retainer-followup-sms-snippets.md` (Retainer Eng/Esp SMS One–Five)
- Calls → `retainer-followup-call-payloads.md` (Call 1–5 bodies, voicemail included)

**T0 = agreement sent.** All timings anchor to T0; GHL Wait steps are deltas from the previous step.

## Exact step sequence (per language branch)

| # | Add this step | Value |
|---|---|---|
| — | **Trigger** | Agreement sent / status `HF Retainer Sent` |
| 1 | Wait | **1 hour** |
| 2 | Send SMS | **Retainer …SMS One** |
| 3 | Wait | **1 hour** |
| 4 | Webhook (Retell call) | **Call 1** body (`call_number:"1"`) |
| 5 | Wait | **4 hours** |
| 6 | Webhook (Retell call) | **Call 2** (`call_number:"2"`) |
| 7 | Wait | **2 hours** |
| 8 | Send SMS | **Retainer …SMS Two** |
| 9 | Wait | **12 hours** |
| 10 | Webhook (Retell call) | **Call 3** (`call_number:"3"`) |
| 11 | Wait | **2 hours** |
| 12 | Send SMS | **Retainer …SMS Three** |
| 13 | Wait | **6 hours** |
| 14 | Webhook (Retell call) | **Call 4** (`call_number:"4"`) |
| 15 | Wait | **3 hours** |
| 16 | Send SMS | **Retainer …SMS Four** |
| 17 | Wait | **13 hours** |
| 18 | Webhook (Retell call) | **Call 5** final (`call_number:"5"`) |
| 19 | Wait | **2 hours** |
| 20 | Send SMS | **Retainer …SMS Five** |
| 21 | Wait | **2 hours** |
| 22 | Handoff | assign to human intake queue / set status |

Cumulative check: 1, 2, 6, 8, 20, 22, 28, 31, 44, 46, 48 hrs. ✔

## Build steps

1. **Trigger.** Workflow trigger = the agreement-sent event (status/stage → `HF Retainer Sent`, or a `retainer_sent` tag). In workflow settings enable **"Stop on response"** is NOT enough on its own — see Stop conditions below.

2. **Language split (do this once, first).** Add an **If/Else** on `lead_language`:
   - **English** branch → the full 22-step sequence using the **Eng** SMS snippets + **English** call bodies.
   - **Spanish** branch → the same sequence using **Esp** snippets + **Spanish** call bodies.
   Mirroring once at the top keeps every send single-language and avoids per-step branching.

3. **SMS steps.** Use **Send SMS** action; paste the matching snippet (or reference the GHL Snippet by name). `{{contact.first_name}}` and `{{custom_values.retainer_link_en/es}}` resolve automatically.

4. **Call steps.** GHL has no native Retell call, so each call is a **Custom Webhook** action:
   - Method `POST` · URL `https://api.retellai.com/v2/create-phone-call`
   - Headers: `Authorization: Bearer <RETELL_KEY>`, `Content-Type: application/json`
   - Body: the matching **Call N** JSON from `retainer-followup-call-payloads.md`.
   Retell handles voicemail itself (detection + `{{voicemail_script}}`) — no separate VM step.

5. **TCPA window (8 AM–9 PM PT).** On **every Wait step**, enable the advanced option **"continue only within a window"** = 08:00–21:00, timezone `America/Los_Angeles` (or contact timezone). Any step that would land outside rolls to the next window open; the 48-hr clock keeps running. This satisfies the doc's permitted-hours rule without separate logic.

6. **Voicemail detection.** Confirm **voicemail detection is ON for Agent B** (`agent_83f8b296…`) — the `voicemail_option` is wired to `{{voicemail_script}}`, but detection must be enabled for the VM to actually be left.

## Stop conditions (halt the cadence)

The post-call decision workflow (`n8n → GHL`, action key) drives these. In GHL, on the relevant status/tag change, run **"Remove from Workflow" → this cadence** for:
- `signed` — signed on the call
- `already_signed_pending` — pause pending verification
- `opt_out` — do-not-contact
- `declined` — confirmed decline
- `human_requested` — warm transfer completed
- `schedule_callback` — remove from cadence and schedule the callback at the stated time

Keep in cadence: `not_client` (wrong number) and `reschedule` (bad time, no specific time) — just continue.

## Auto-handoff

At **+48 hrs** (final step) any lead still in the workflow (not stopped above) is routed to the human intake queue with call history + logged objections.
