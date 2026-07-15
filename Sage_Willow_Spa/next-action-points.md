# Aria — Next Action Points (Pre Go-Live)

Live status: V24 built and deployed to Retell for testing. Two critical bugs surfaced in the last simulator run (see Engineering below). Zoom scheduled with Nicky to set a go-live target date.

---

## Client Side (Nicky / Sage & Willow Spa)

### Setup / configuration
- [ ] **AT&T call forwarding** — route the main spa line to Aria's Retell number
- [ ] **Wix booking calendar** — confirm any remaining calendar-side configuration:
  - Staff availability windows correct for both existing + new therapist
  - New full-time therapist (started 2026-06-01) added in Wix so Aria's `get_staff` picks them up automatically
  - Couples-massage room capacity honored when `numberOfParticipants: 2` is passed

### Content sign-off
- [ ] Reply to our email with any edits on the remaining service descriptions (Swedish, Deep Tissue, Hot Stone, Lymphatic Drainage, 30-Minute Focus)
- [ ] **Wix dashboard — Signature Massage** — remove "hot stone" from blend wording
- [ ] **Wix dashboard — Prenatal Massage** — add "Available from the second trimester onward (after 12 weeks)"

### Decisions still open
- [ ] Confirm **go-live target date** (subject of tomorrow's Zoom)
- [ ] Prenatal booking — inform-only vs. hard-gate on "past 12 weeks?" (our recommendation: inform-only)

---

## Our Side (Engineering)

### Critical bugs from V24 simulator run — must fix before go-live
- [ ] **D1** — Spanish language switch not triggering on full Spanish first turn (prompt rule needs tightening)
- [ ] **B4** — `flag_callback` sending `callerPhone: "Unknown"` instead of `{{user_number}}` (default not being applied)

### Minor bugs — worth fixing this iteration
- [ ] **B2** — Reschedule flow listed 6 slots instead of 2–3 (add `limit: 3` in `get_slots` call or prompt nudge)
- [ ] **C2** — Closing line skipped on some deflection-based endings (reinforce in Closing / Escalations section)

### n8n backend
- [ ] Wire `args.numberOfParticipants: 2` through to Wix Create Booking for couples massage (block double capacity for the slot)
- [ ] Persist `args.notes` on the Wix booking record (additionalFields / notes)
- [ ] Verify phone-based `get_booking` / `cancel_booking` / `reschedule_booking` end-to-end

### Configuration swaps before go-live
- [ ] Replace temporary transfer number `+14064764193` (currently Ubaid's personal) with the spa's real forwarding number
- [ ] Replace temporary callback email recipient `engineering@aiemply.com` with `sagewillowspa@gmail.com`
- [ ] Re-upload finalized KB files (business_facts.md, service_descriptions.md, faqs.md) to Retell Knowledge Base after client sign-off on descriptions

### Final QA
- [ ] Re-run the 20-test simulator suite after D1 + B4 fixes are in (V25)
- [ ] Live test call with Nicky end-to-end
- [ ] Confirm post-call analysis dashboard is capturing all 10 fields

---

## Coordination / Meetings
- [ ] **Zoom with Nicky — tomorrow at 9:30 AM PT** (or 9:00 AM if she prefers a full hour) — set go-live date
- [ ] Agree parallel-testing window vs. hard cutover before flipping AT&T forwarding
