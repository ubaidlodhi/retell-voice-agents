# Knight Law Group — Lemon Law Intake

AI intake agents (voice + Meta DM) and CRM automation for Knight Law Group's California Lemon Law qualification.

## Folder structure

| Path | What's inside |
|---|---|
| `agents/multi-prompt/` | Current Retell **voice** agent (multi-prompt) — `multi-prompt-agent.json` |
| `agents/conversation-flow/` | New Retell **conversation-flow** voice agent (efficient rebuild) |
| `agents/meta-dm/` | Meta (FB/IG) **DM chatbot** prompt run in GoHighLevel — `meta-dm-chatbot.md` |
| `kb/` | Knowledge base for FAQs (`knight-law-faqs.md`) — attach to Retell at flow level |
| `ghl-setup/` | GoHighLevel automation: `incomplete-leads-followup.md` (cadence spec), `workflows.md` |
| `test-cases/` | `retell-simulation-tests.md`, `knight-law-test-cases.csv`, and `results/` (simulation run outputs) |
| `client/` | Client-facing deliverables (`client-update-summary.md`) |

## Qualification logic (current)

- **Outbound** agent "Alice"; auto-switches **EN/ES**; assumes `{{Name}}/{{Phone}}/{{Email}}` are pre-populated.
- **Vehicle year:** `≤ 2019 → Bad Lead (Vehicle year)` · `2020+ → continue`.
- **Outcomes:** Retainer (qualifies → retainer agreement) · Non-Retainer (consultation link) · Bad Lead (disqualified, with reason) · Incomplete (didn't finish → follow-up cadence).
- Manufacturer lists (opted-in / retainer) are identical across the voice and Meta agents.

## Lead handoff

Lead Status (Retainer / Non-Retainer / Bad / Incomplete) is written to the CRM, driving the Contact smart lists and the **Incomplete Leads follow-up cadence** (EN/ES) in `ghl-setup/`.
