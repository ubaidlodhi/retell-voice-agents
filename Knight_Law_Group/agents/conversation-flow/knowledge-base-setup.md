# Knight Law — Knowledge Base Attachment (Outbound + Inbound)

> **Why this is a manual dashboard step:** Retell **strips KB IDs on export** (`knowledge_base_ids: []` in the JSON). Re-importing an agent JSON does **not** carry KB attachments — you must (re)attach them in the dashboard after every import. This file is the source of truth for *what attaches where*.

---

## Principles (apply to both agents)

- **Use node-level KB, not agent-level.** Agent-level KB retrieves on **every turn** (slower, and it makes the agent over-answer / pull facts where it shouldn't). Node-level scopes retrieval to only the nodes that need it.
- **Detach both KBs from the agent level** if they were ever attached there, then attach per the tables below.
- The **"Configure Knowledge Base Instruction"** field is a **retrieval-focus hint** (tells the retriever *what* to look for) — it is **not** agent behavior. Keep it to one short line.
- After import, re-attach KBs **every time** (they don't survive export/import).

---

## KB 1 — `knight-law-faqs`

General Q&A about the firm, fees, the lemon law, process, and timelines.

- **Retrieval instruction:** `Answers about the firm, fees, California Lemon Law, the process, and case timelines.`

| Agent | Attach to node |
|---|---|
| Outbound | `GLOBAL - FAQ Handler` |
| Inbound | `GLOBAL - FAQ Handler` |

- The FAQ handler is the **only** node that should pull general firm/legal answers — that's exactly why it's a global node. Attaching here (and nowhere else) keeps the qualification questions from triggering KB retrieval.

---

## KB 2 — `Correct Vehicle Make and Model Spellings`

Correct spelling/formatting of vehicle makes and models, so the agent captures and reads them back cleanly.

- **Retrieval instruction:** `Correct spelling and formatting of vehicle makes and models.`

| Agent | Attach to node | Priority |
|---|---|---|
| Outbound | `Q: Vehicle Year/Make/Model` | **Required** |
| Outbound | `Reprompt Vehicle` | Recommended |
| Inbound | `Q: Vehicle Year/Make/Model` | **Required** |
| Inbound | `Reprompt Vehicle` | Recommended |
| Inbound | `Inbound: Resume (Incomplete)` | Recommended |
| Inbound | `Inbound: Bad Re-check (possession)` | Optional |

- Attach where the **caller speaks or restates the vehicle** — that's where correct capture/read-back matters.
- The **make** is already constrained by the canonical make enum on the `Extract Vehicle Vars` node (with transcription-error correction baked in, e.g. `Fard → Ford`), so this KB mainly helps the free-text **model** and clean read-backs.
- Do **not** attach it to `Extract Vehicle Vars` — extract nodes don't converse, so they don't retrieve.
- Inbound extras: `Inbound: Resume` reads the vehicle back in the recap (and the caller may correct it), and `Inbound: Bad Re-check` is where a returning caller may restate the vehicle — hence the optional attachments.

---

## Quick checklist (do after each import)

- [ ] Detach `knight-law-faqs` and `Correct Vehicle Make and Model Spellings` from **agent level** (if present).
- [ ] Outbound: attach FAQ KB → `GLOBAL - FAQ Handler`; spelling KB → `Q: Vehicle Year/Make/Model` (+ `Reprompt Vehicle`).
- [ ] Inbound: attach FAQ KB → `GLOBAL - FAQ Handler`; spelling KB → `Q: Vehicle Year/Make/Model` (+ `Reprompt Vehicle`, `Inbound: Resume (Incomplete)`).
- [ ] Set each KB's retrieval instruction (one line, from above).
- [ ] `kb_config` stays `top_k: 3`, `filter_score: 0.6` (default, already in both JSONs).
