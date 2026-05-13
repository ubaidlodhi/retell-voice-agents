# Aubrey Training Session — Facilitator Guide

**Duration:** 60 minutes
**Audience:** Keyline team members who will own Retell edits going forward
**Goal:** By the end, at least one person on their side has personally made a small edit, tested it, and published it. They leave knowing where to click for the most common changes.

---

## Before the Meeting (do this today)

- [ ] Confirm every attendee has a working Retell login with edit access to the Aubrey agent.
- [ ] Share the SOP doc (`Keyline_SOP.md`) 1–2 hours before — tell them not to read cover to cover, just skim Sections 4 and 5.
- [ ] Have the Aubrey agent open in your browser **on a published version** so you can do live demos.
- [ ] Have a throwaway change ready in mind (e.g., greeting tweak you can revert) for the live demo.
- [ ] Pull up `Aubrey_Flows_Built.md` in another tab — useful as a visual map of what's in there.
- [ ] Mute Slack, close email, share your screen at the start.

---

## Agenda at a Glance

| Time | Section | Outcome |
| :---- | :---- | :---- |
| 0:00–0:05 | Welcome + what they'll walk away knowing | Set expectations |
| 0:05–0:15 | Retell tour — the lay of the land | They can find anything |
| 0:15–0:30 | Anatomy of a node (live in their flow) | They understand prompts, edges, variables |
| 0:30–0:50 | Live demo + hands-on edits (3 recipes) | Someone on their side publishes a change |
| 0:50–0:55 | Safety net — testing, versions, rollback | They feel safe to experiment |
| 0:55–1:00 | Q&A + when to call us | Clean exit, open door |

---

## 0:00–0:05 — Welcome & Frame

**Say something like:**

> "The goal of the next hour is for at least one of you to actually make a change to Aubrey and publish it — with me on the call. Not in theory. After today you'll be comfortable making the small adjustments yourselves, and you'll know exactly when to loop us in for the bigger stuff."

**Then show:**

- The SOP doc location (so they know where to look later).
- `Aubrey_Flows_Built.md` — quick visual: "this is everything Aubrey can do today."

**Don't:** Spend more than 5 minutes here. Get them into Retell fast.

---

## 0:05–0:15 — Retell Tour (10 min)

Share your screen on the Retell dashboard. Walk through:

**1\.** **The agent list** — show that Aubrey is the production agent. Mention you can create test copies.

**2\.** **The flow editor canvas** — point out:
   - Nodes (the boxes)
   - Edges (the lines connecting them)
   - Node groups (Entry, Routing, Intake, Tickets, Transfers, Global) — match this to `Aubrey_Flows_Built.md`
   - Use Ctrl+F to find a node by name

**3\.** **Right sidebar** — show:
   - **Global Settings** (Agent Handbook, voice, response speed)
   - **Tools** (send_app_link, create_ticket, send_ticket_sms)
   - **Knowledge Base** (FAQ content)
   - **Versions** (their safety net — more on this later)

**4\.** **Top right buttons** — **Test Call** and **Publish**. Emphasize: nothing is live until Publish.

---

## 0:15–0:30 — Anatomy of a Node (15 min)

Click into a real node in their flow — **OPENING** is a good one because it has everything.

Walk through, in order:

**Prompt vs Static Sentence**

- Click into the Prompt tab. Read a few lines aloud. "This is plain English. Aubrey reads these instructions and adapts the wording naturally."
- Then mention Static Sentence: "If you ever need Aubrey to say something word-for-word — a legal disclosure, an exact apology — that's where Static Sentence comes in. Most of the time you'll be in Prompt."

**Dynamic variables**

- Point out `{{caller_name}}` or `{{current_time_America/New_York}}` somewhere in the prompt.
- "These get filled in automatically when the call happens. So `{{caller_name}}` becomes whatever name we looked up from Monday.com."
- Quick reference: pull up Section 4.4 of the SOP for the full list.

**Edges**

- Scroll to the Transitions section.
- Read one or two conditions out loud. "These are the rules Aubrey uses to decide where to go next."
- Show that conditions are evaluated **top to bottom**. "If you want a specific case to win over a general one, put it on top."
- Open CASE MANAGER as a second example so they see two edges with different conditions.

**Don't:** Get pulled into theory. Keep returning to "and here's where you'd click to change this."

---

## 0:30–0:50 — Live Demo + Hands-On (20 min) ⭐ MOST IMPORTANT BLOCK

Pick **three recipes from the SOP** and do them live. Suggested set (easy → moderate):

### Demo 1 (you do it) — Recipe 1: Change Aubrey's Greeting

- 5 min total: edit → save → Test Call → revert
- Make a tiny, obviously-different change ("Hi, this is Aubrey from Keyline Home Care Solutions, calling on the warm side today")
- Use Test Call so they hear the new greeting
- Then revert — shows the round trip

### Demo 2 (you do it) — Recipe 2: Update a Transfer Phone Number

- 3 min total: open TRANSFER - PAYROLL TEAM → change the number to your own cell → save (don't publish) → test that the number field accepts it
- Restore the original number before moving on
- Emphasize the E.164 format requirement (`+1` country code)

### Hands-on (THEY do it) — Recipe 3: Add a Banned Word

- This is the safest hands-on for a beginner: it's a global-settings text edit, no graph changes
- Walk one of them through:
  - Open Global Settings → Agent Handbook
  - Add a word to the banned list
  - Save → Publish
- After publish, do a Test Call together and try to provoke the word
- Cheer when it works

**If you have time, add Recipe 4 (change closing line) or Recipe 7 (intake field)** — your call based on energy in the room.

**Skip Recipe 9 for now.** Reference it: "There's a bigger pattern in the SOP for multi-step changes like adding caller types — that's where to look when you want to add a whole new branch."

---

## 0:50–0:55 — Safety Net (5 min)

Three things to hammer home:

**1\.** **Test before Publish, always.** Use the Test Call button in the top right. If your change touches routing, test the happy path AND an adjacent flow.

**2\.** **Versions are your friend.** Right sidebar → Versions. Every Publish creates a snapshot. If you break something, click an older version → Restore. You can always roll back.

**3\.** **When in doubt, don't Publish.** Save your draft, ping us, and we'll look at it with you.

---

## 0:55–1:00 — Q&A + When to Call Us

Open the floor. If there's no question, prompt them with one:

> "Of all the small changes you'd want to make in the next month, which one feels least obvious?"

**Then close with — when to escalate:**

- ✅ **Do yourself:** wording tweaks, banned words, transfer numbers, closing lines, FAQ updates, adding a question to an existing intake
- ⚠️ **Loop us in for:** anything that adds a new node, changes a tool URL, restructures routing logic, or touches more than two nodes at once

**Final line:** "Send us anything you publish in the next two weeks and we'll do a quick check before it goes live a second time. After that, you'll be on autopilot."

---

## After the Meeting

- [ ] Send a 3-line follow-up email: link to the SOP, link to the flows-built doc, and your direct contact for the next two weeks.
- [ ] If they published something during the session, mention it in the follow-up — gives them confidence.
- [ ] Schedule a 30-min check-in 2 weeks out to answer whatever they've run into.

---

## If You Have Extra Time / Buffer Material

If the demo block runs short and you need 10 more minutes of useful content:

- Open the **Tools** sidebar, walk through `create_ticket`'s parameters — show how the field names match what shows up in Monday.com columns.
- Open the **Knowledge Base** and demo adding a one-line FAQ entry.
- Pull up a recent call recording (Call Logs) and show how you'd debug a misrouted call.

If you're running long, **cut Demo 2 (transfer phone number)** — it's the least interactive and easiest to learn from the SOP.
