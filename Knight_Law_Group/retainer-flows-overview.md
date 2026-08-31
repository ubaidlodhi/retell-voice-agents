# Alice Retainer — Flows Overview

Quick reference for the new retainer agents: what happens on each call, what tag lands on the GHL contact, and what the Salesforce status becomes.

---

## 1. Situation tags

Set by the **Retainer Post-Call Router** in GHL, from the `action` sent by n8n.

| Tag | Set when | Means |
|---|---|---|
| `signed (source: retainer agent)` | `action = signed` | Caller signed **live on the call** with Alice. Verified. |
| `signed (source: user claims)` | `action = already_signed_pending` | Caller **says** they already signed. **Unverified** — still needs a check against DocuSeal. |
| `retainer declined (source: retainer agent)` | `action = declined` | Caller confirmed they do **not** want to proceed, after one value restatement. |

Only tags starting with **`signed`** stop a caller reaching the retainer agent on a call-back. See §5.

---

## 2. Status mapping (GHL → Salesforce)

| GHL Lead Status | Salesforce Status |
|---|---|
| Retainer Lead | **HF Retainer Sent** |
| Non-Retainer Lead | HF Appointment |
| Bad Lead | Bad Lead |
| Opt-Out Consent | **Burnt Lead** |
| Human Requested | HF Appointment + note: *"did not communicate due to AI issue"* |
| Incomplete Lead | *(retry, no SF push)* |

`HF Appointment` is a **Salesforce-only** status — never set it as a GHL `lead_status`.

Note: signing does **not** change the status. A signed lead stays `Retainer Lead` / `HF Retainer Sent`; the tag is what records the signature.

---

## 3. Outbound intake agent — the retainer hand-off

Qualification is unchanged. This is only what happens **after** the caller qualifies for a retainer:

```
… caller qualifies for retainer
   └─ Contact details      confirm name spelling, email, text/email consent
   └─ Confirm + pause      "we can move forward — give me a second to send
                            your agreement and pull everything up"
   └─ send_agreement       tool → GHL → SMS + email with the DocuSeal link
   └─ Hand-off prep        builds the greeting, entry_mode = immediate_handoff
   └─ AGENT SWAP ─────────► Immediate Retainer Agent   (same call, same voice)
                            └─ if the swap fails → normal retainer close
```

The caller never hangs up and never gets called back — the agreement arrives while they are still on the line, and Alice walks them through it immediately.

Post-call, the contact is set to `Retainer Lead` → **HF Retainer Sent**, and `Retainer Sent At` is stamped. That timestamp starts the 48-hour window in §5.

---

## 4. Immediate Retainer Agent — what it does and what it produces

Opens with the hand-off line, waits for a go-ahead, then walks the four points in one continuous explanation: **buyback → manufacturer-paid fees → 50/50 on additional damages → mileage offset**. Then answers questions and drives to signing.

| Outcome on the call | `action` | Tag added | GHL status | Salesforce |
|---|---|---|---|---|
| Signed while on the line | `signed` | `signed (source: retainer agent)` | Retainer Lead | HF Retainer Sent |
| "I already signed it" | `already_signed_pending` | `signed (source: user claims)` | Retainer Lead | HF Retainer Sent |
| Confirmed they won't proceed | `declined` | `retainer declined (source: retainer agent)` | Retainer Lead | HF Retainer Sent |
| Asked for a human / legal question | `human_requested` | — | Human Requested | HF Appointment + AI note |
| "Stop contacting me" | `opt_out` | — | Opt-Out Consent | **Burnt Lead** |
| Gave a specific call-back time | `schedule_callback` | — | unchanged | unchanged |
| Anything else (busy, no time, no clear answer) | `continue` | — | unchanged | unchanged |

`signed`, `already_signed_pending`, `declined` and `opt_out` all **stop the follow-up cadence**. `schedule_callback` pauses it until the requested time. `continue` leaves it running.

---

## 5. Inbound agent — who reaches the retainer agent

Before the phone even rings, a pre-call lookup reads the contact and decides. Three things must **all** be true to reach the retainer agent:

1. Status is a retainer status (`Retainer Lead` **or** `Retainer Pending`)
2. `Retainer Sent At` is **less than 48 hours** ago
3. **No** `signed …` tag on the contact

| Caller's situation | What happens |
|---|---|
| Retainer lead, sent **< 48h** ago, not signed | **→ Immediate Retainer Agent** — "I've got your agreement right here, want me to walk you through it?" |
| Retainer lead, **already signed** (either signed tag) | → normal cold transfer to a human on the intake team |
| Retainer lead, sent **more than 48h** ago | → normal cold transfer to a human |
| Retainer lead, but `Retainer Sent At` empty or malformed | → normal cold transfer to a human *(fails safe)* |
| Non-Retainer Lead / Bad Lead | → normal cold transfer to a human |
| Opt-Out Consent | → opt-out close, no pitch |
| Incomplete Lead with answers already on file | → resumes intake where it stopped |
| Unrecognised caller, or a brand-new status | → fresh qualification from the start |

A caller who **qualifies on this inbound call** follows exactly the same hand-off as §3 — agreement sent live, then straight to the retainer agent.

Everything except the first row is unchanged from how the line behaved before.

---

## 6. Outbound retainer follow-up (cadence)

For leads who were sent the agreement but haven't signed. GHL dials them on the cadence; Alice removes the objection and drives to a signature, or locks a specific call-back time.

Outcomes, tags and statuses are the **same table as §4** — the only differences are that the call is outbound, it carries an attempt number (1–5), and it leaves a voicemail if nobody answers.

---

## Open point

The `retainer declined` tag is recorded but **does not currently block routing**. A lead who declined and then calls back within the 48-hour window will still reach the retainer agent and be pitched again.

That may well be what you want — they called *us*, so they may have changed their mind. But if a declined lead should instead go to a human, say so and it's a one-line change to the pre-call check.
