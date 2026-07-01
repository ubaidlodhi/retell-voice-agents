# Knight Law — Lead Classification Flows (plain-English guide)

> **What this is:** how every call gets turned into a final **Lead Status**. The voice agent (Alice) asks the questions; after the call, the **n8n Post-Call (Voice AI Review)** workflow reads the transcript, fills in any gaps from the seeded form data, and applies the rules below. The same rules are mirrored inside the agent so the live call and the post-call result agree.
>
> **Where the facts come from:** the AI reads the transcript and reports only what the caller actually said on this call (everything else = `N/A`). For anything the caller didn't cover, we fall back to the **seeded** values from their original web form. We never "force" a Yes/No.

---

## The 5 possible results

| Result | One-line meaning |
|---|---|
| **Retainer Lead** | Qualifies — we email a retainer agreement to sign. |
| **Non-Retainer Lead** | Doesn't qualify for a retainer, but we may still help — booking link / consultation follow-up. |
| **Bad Lead** | Disqualified — falls outside California Lemon Law criteria. |
| **Opt-Out Consent** | Caller asked not to be contacted — added to do-not-contact. |
| **Incomplete Lead** | Call ended before we learned enough to decide — we follow up to finish. |

---

## How a lead is decided (the order matters)

The checks run **top to bottom**. The **first** one that matches wins — so an earlier rule always beats a later one.

```
1.  Asked to stop / not be contacted?            → Opt-Out Consent
2.  Said NO vehicle issues?                      → Bad Lead  (Non lemon law)
3.  NOT bought/leased in California?              → Bad Lead  (Out of state purchase)
4.  No vehicle MAKE captured?                     → Incomplete Lead
5.  No longer has it AND make needs possession?  → Bad Lead  (Not in possession)
6.  No/!unknown model YEAR?                       → Incomplete Lead
7.  Year is 2020 or older?                        → Bad Lead  (Vehicle year)
8.  Make is on the RETAINER list?
        new/used not known?                       → Incomplete Lead
        used AND not CPO?                         → Bad Lead  (Purchased used non-CPO)
        used AND CPO unknown?                     → Incomplete Lead
        (new, or used+CPO) →
              no repairs attempted?               → Non-Retainer Lead
              repairs unknown?                    → Incomplete Lead
              not the owner?                      → Non-Retainer Lead
              owner unknown?                      → Incomplete Lead
              owner = yes                         → Retainer Lead
9.  Make NOT on the retainer list (passed 1–7)   → Non-Retainer Lead
```

> Note on step 2: we only disqualify if the caller **explicitly says there are no issues**. If issues simply weren't discussed, we don't block on it.

---

## Retainer Lead — the full qualifying path

A caller becomes a **Retainer Lead** only when **all** of these are true:

1. They **have vehicle issues** (didn't say "no problems").
2. Bought/leased **in California**.
3. The **make is on the Retainer list** (see below).
4. The **model year is 2021 or newer**.
5. Purchase condition is **New**, *or* **Used but Certified Pre-Owned (CPO)**.
6. They **attempted a repair** at a dealership.
7. They are the **owner, signed the sales contract, or are a co-buyer**.

**Example:** "2022 Ford F-150, bought new in California, still have it, took it to the dealer for repairs, I'm the owner." → **Retainer Lead.**

**What happens next:** Alice offers to email the **representation agreement** (this is the caller-facing wording — the internal status stays `Retainer Lead` and GHL fields/tags are unchanged); GHL fires the Zapier → Salesforce → DocuSign chain and stamps the `retainer-sent` tag.

---

## Non-Retainer Lead — "we may still help"

A caller lands here in any of these ways:

- **Make is NOT on the Retainer list** (but they passed the issue / California / year / possession checks). *Example: "2021 Toyota Camry, bought new in California, having issues."* → Non-Retainer.
- **Retainer-make, but they have NOT attempted a repair yet.** *Example: "2023 Kia, brand new, haven't taken it in for repair."* → Non-Retainer.
- **Retainer-make, but they are NOT the owner / didn't sign.** → Non-Retainer.

**What happens next:** Alice closes warmly ("we may still be able to help"); GHL enrolls them in the booking-link drip (EN/ES) and stamps `non-retainer-followup`.

---

## Bad Lead — the 5 disqualifiers

Disqualified because the situation is outside California Lemon Law criteria. The **reason** is recorded so the team and reporting know why:

| Reason | Plain meaning | Example |
|---|---|---|
| **Non lemon law** | Caller says the car is **running fine / no issues**. | "No, the car's been great." |
| **Out of state purchase** | Vehicle was **not** bought/leased from a **California** dealership. | "I bought it in Arizona." |
| **Not in possession** | They **no longer have the vehicle**, *and* the make is one that **requires possession** to file. | "I traded in my Kia last month." |
| **Vehicle year** | Model year is **2020 or older** (firm handles 2021+). | "It's a 2019 Honda." |
| **Purchased used non-CPO** | A retainer-make bought **used** that is **not Certified Pre-Owned** (no original manufacturer warranty). | "Used 2022 Jeep, not certified." |

**What happens next:** Alice closes politely ("I'll keep your details on file"); GHL logs it as a lost opportunity. *(Returning Bad Leads on the inbound line are simply greeted and offered a transfer — never re-qualified.)*

---

## Opt-Out Consent

At **any point** the caller says they're not interested, to stop calling, to be removed, or not to be contacted again. This **overrides everything else** — even if they'd otherwise qualify.

**What happens next:** Alice acknowledges respectfully and ends; GHL adds them to do-not-contact (DND) and removes them from active workflows.

---

## Incomplete Lead

The call ended (hang-up, drive-off, "call me later") **before** we learned enough to decide. Specifically, one of these was never established:

- the vehicle **make**, or
- the model **year**, or
- whether it was bought **new or used**, or
- (if used) whether it's **CPO**, or
- whether a **repair** was attempted, or
- whether they're the **owner**.

**What happens next:** they go into the Incomplete follow-up. On a return call, the inbound agent **resumes** — it recaps what's already on file and only asks for what's still missing.

---

## The two make lists (why the same brand can go different ways)

**Retainer-track makes** (step 8 — eligible for a retainer agreement):
Acura · Audi · BMW · Buick · Cadillac · Chevrolet · Chrysler · Dodge · Ford · GMC · Hyundai · INFINITI · Jaguar · Jeep · Kia · Land Rover · Lincoln · Mazda · Mercedes-Benz · Nissan · Ram · Volkswagen

**Possession-required makes** (step 5 — must still have the vehicle to file):
Alfa Romeo · Buick · Cadillac · Chevrolet · Chrysler · Dodge · FIAT · Ford · Genesis · GMC · HUMMER · Hyundai · INFINITI · Jaguar · Jeep · Kia · Land Rover · Lincoln · Maserati · Mercedes-Benz · Mercury · Mitsubishi · Nissan · Pontiac · Ram · Saturn · smart · Subaru · VinFast

> A make **not** on the Retainer list (e.g. Toyota, Honda, Lexus, Tesla) can still be a **Non-Retainer Lead** — it just can't reach the retainer agreement. A make **not** on the possession-required list won't be disqualified for selling the car.

---

## Returning callers — the "no-downgrade" rule

If someone was **already** classified as Retainer / Non-Retainer / Bad / Opt-Out, and a later call adds **no new qualifying facts**, the workflow **keeps the existing status** rather than re-deciding from a short call. This prevents a quick "just checking in" call from accidentally wiping a good Retainer lead back to Incomplete. If the later call **does** add new facts (e.g. they finally give the vehicle), it re-classifies normally.

---

## At a glance

```
                         ┌─ asked to stop? ───────────────→ Opt-Out Consent
                         ├─ no issues? ───────────────────→ Bad (Non lemon law)
                         ├─ not California? ──────────────→ Bad (Out of state)
   every call ──────────►├─ no make? ─────────────────────→ Incomplete
                         ├─ gone + possession-make? ──────→ Bad (Not in possession)
                         ├─ no year? ─────────────────────→ Incomplete
                         ├─ year ≤ 2020? ─────────────────→ Bad (Vehicle year)
                         ├─ retainer make? ──┬─ used+noCPO → Bad (used non-CPO)
                         │                   ├─ no repairs → Non-Retainer
                         │                   ├─ not owner ─→ Non-Retainer
                         │                   ├─ missing q ─→ Incomplete
                         │                   └─ all yes ───→ Retainer Lead
                         └─ other make ───────────────────→ Non-Retainer Lead
```
