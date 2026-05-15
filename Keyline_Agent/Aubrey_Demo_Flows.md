# Aubrey — Demo Flows for the Training Session

Three test calls to run live with the team. Use the **Test Call** button in the Retell flow editor. As Aubrey moves, the editor highlights the active node — tell the team to **watch the canvas light up** so they can see the navigation happen.

All three assume an **unrecognized caller** (a normal Test Call), so Aubrey always asks the caller-type question first.

---

## Flow 1 — Pay Issue → Transfer (short, ~1 min)

**Shows:** topic routing + a straight transfer. Good warm-up.

**You say (caller side):**
1. *"Hi, I think there's a problem with my paycheck."*
2. (Aubrey asks caller type) → *"I'm a caregiver."*
3. (Aubrey asks state) → *"Georgia."*

**Watch it travel:**
```
OPENING  →  (caller-type question)  →  PAY ISSUE - TRANSFER  →  TRANSFER - PAYROLL TEAM
```

**Point out:**
- Aubrey asks the caller-type question *before* routing — even though "paycheck problem" already implies the topic.
- `PAY ISSUE - TRANSFER` does no intake — it's empathy + immediate handoff. That's a design choice they can see in the node.
- The transfer node has a `Transfer failed` edge to `CLOSE CALL` — the safety net if the line doesn't pick up.

---

## Flow 2 — Missed Clock-Out → Ticket Created (full pattern, ~3 min)

**Shows:** the most common pattern in the whole agent — collect fields → submit → create ticket → send SMS → confirm → close.

**You say (caller side):**
1. *"I forgot to clock out yesterday."*
2. (caller type) → *"Caregiver."*  (state) → *"Georgia."*
3. Then answer Aubrey's questions one at a time — she'll ask ~5: your name, the client, the date, the times, and whether it was an app or non-app issue. Make up simple answers.

**Watch it travel:**
```
OPENING  →  (caller-type question)  →  MISSED CLOCK OUT  →  MCO SUBMIT
        →  Create Ticket  →  Send Ticket SMS  →  Ticket Confirmation  →  CLOSE CALL  →  END CALL
```

**Point out:**
- `MISSED CLOCK OUT` collects **one question per turn** — that's written into its prompt.
- `MCO SUBMIT` → `Create Ticket` happens automatically (a "Skip response" edge) — no caller turn needed.
- `Create Ticket` is a **function node** — it calls the n8n webhook and gets back a ticket number.
- `Ticket Confirmation` reads that number **once**. This is where `{{ticket_id}}` gets used.
- This same shape (collect → submit → function → confirm) repeats for Travel, Incident, Income Letter, etc. Learn it once, recognize it everywhere.

---

## Flow 3 — Case Manager → Branched Transfer (shows branching, ~2 min)

**Shows:** conditional routing — the same node sends callers to *different* places based on their answer. This is the recent change the client requested.

**You say (caller side):**
1. *"Hi, I'm calling about one of my clients."*
2. (caller type) → *"I'm a case manager."*
3. (Aubrey asks for the client's name) → *"Jane Smith."*
4. (Aubrey asks for the caregiver's name) → *"Bob Jones."*
5. (Aubrey asks about status) → **try it twice:**
   - First run: *"They've already started services."* → goes to **Case Support**
   - Second run: *"They're looking to switch providers."* → goes to **Care Team**

**Watch it travel:**
```
OPENING  →  caller-type question  →  CASE MANAGER  →  (collects 2 names, asks status)
                                                   ├─ "already started"  →  TRANSFER - CASE SUPPORT
                                                   └─ "starting / switching"  →  TRANSFER - CARE TEAM
```

**Point out:**
- One node, two outcomes. Open `CASE MANAGER` and show them the **two edges** — each with a different condition.
- This is exactly the pattern from **Recipe 9** in the SOP. Tell them: "If you ever need a 'ask a question, then branch' change, this is the template."
- Aubrey collects both names *before* transferring — the prompt says "do not transfer until both names are collected."

---

## Demo Data (fake — safe to use on test calls)

Use the same fake persona across all demos so it's consistent and obviously not a real caregiver:

| Field | Value |
| :---- | :---- |
| Caller name | Jordan Avery |
| Phone | (555) 010-7788 |
| Email | jordan.avery@example.com |
| Address | 142 Birchwood Avenue, Apt 3B, Albany, NY 12203 |
| Client / patient name | Pat Morgan |
| Caregiver name (for case-manager demo) | Bob Jones |
| State calling from | Georgia |

*All fabricated. The 555-01xx phone range and example.com email are reserved for fake/demo use, so nothing real gets texted or ticketed.*

---

## Suggested Order in the Meeting

Run them **1 → 2 → 3**: short transfer first to build confidence, then the full ticket pattern, then branching as the finale. After Flow 3, segue straight into the live-edit demos (Recipes 1–3).
