# Aubrey — Update on Routing Fixes (2026-05-30)

Hi Bernae — here's what we've implemented based on your routing feedback. Everything below is live in the agent and ready for your test calls.

## Routing — your three asks

- **Current clients / active caregivers → Case Support (678-785-7010).** Verified — this routing was already correct.
- **New prospects looking to enroll → live transfer to Eligibility Specialist (678-785-7013) after we collect their info.** Wired up end-to-end: Aubrey now collects the full intake, creates the ticket, reads back the ticket number, then says *"let me connect you with our Eligibility Specialist team to get started"* and transfers live.
- **Referred applicants / status-check callers → Care Team (470-868-4776).** Repointed — the Care Team transfer now dials your new number.

## Smarter prospect handling

- Aubrey now asks one short clarifier when a prospect's intent is ambiguous: *"Are you looking to enroll for the first time, or are you checking on the status of an application you already started?"* — then routes accordingly.

## Bonus fixes — two bugs we caught during testing

- **Aubrey was prematurely saying "Is there anything else?" while creating the ticket.** If the caller said "thanks!" mid-ticket-creation, she'd treat it as call-end. Fixed — she now stays silent through ticket creation and only asks "anything else?" after the ticket number is read.
- **Prospect intake was getting stuck after the last question.** After the final autism/IDD question, Aubrey would say "Got it, one moment" but then sit in silence for 10+ seconds until a "Still with me?" reminder fired. Fixed — she now flows directly into the closing message and ticket creation.

## Other cleanups while we were in there

- Tightened the "I want to talk to a real person" routing so the spoken line matches the actual transfer destination (Case Support).
- Added a guard so a prospect saying "no thanks" to the repeat-offer can't accidentally hang up the call instead of being transferred to Eligibility.
- Fixed misleading wording on the "switch providers" route — no longer says "new enrollments".

## What we need from you next

- **Test calls.** We've prepared a [test plan](test-plan-feedback-02.md) covering all 11 scenarios. If any test fails, we'll see exactly which edge misfired.
- **Confirmation on the number map.** See [transfer-numbers.md](transfer-numbers.md) for the full list of which number Aubrey dials for which scenario. Let us know if any row is wrong.
