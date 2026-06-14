# Knight Law — Alice (outbound) · Retell Simulation Test Cases

Test cases for Retell **LLM Simulation Testing** (Agent → Test → Simulation → *Add test*).
Reflects the current logic after the **2026-06-04** year-criteria change:
**≤ 2019 = Bad Lead (Vehicle year) · 2020+ = Continue · year no longer routes to Non-Retainer.**

---

## How to use

This agent is **outbound** (`start_speaker: agent`) so **Alice speaks first**. The persona only has to answer her.
Each test below has three parts to paste into Retell:

- **Dynamic variables** → the `{{Name}}` / `{{Phone}}` / `{{Email}}` / `{{current_time}}` key-values for that run.
- **User Persona** → paste into the test's *User Prompt* (Identity / Goal / Personality).
- **Success Criteria** → paste as the numbered evaluation list.

**Default dynamic variables** (override per-test only where noted):

| Variable | Value |
|---|---|
| `Name` | `John Carter` |
| `Phone` | `+13105551234` |
| `Email` | `john.carter@example.com` |
| `current_time` | `Thursday, June 4, 2026, 10:15 AM PT` |

**Global success criteria** (apply to every test — append to each list):
- The agent stays in character as Alice from Knight Law Group and never reveals internal node names, lead classifications, or routing logic to the caller.
- The agent never says filler like "let me check," "one moment," or "please hold" between steps.
- The conversation ends with the agent calling the `end_call` function.

---

# GROUP A — Retainer leads (should reach the retainer agreement)

## A1 — Perfect retainer (new vehicle)
**Dynamic variables:** defaults.
**User Persona:**
- **Identity:** You are John Carter. You bought a brand-new **2022 Ford F-150** from a Ford dealership **in California**. You still own and possess it. You signed the purchase contract yourself. You have taken it to the dealer for repairs.
- **Goal:** Get help with the ongoing problems with your truck and move your case forward.
- **Personality:** Cooperative and clear. Answer each question directly. Confirm your name, phone, and email are correct when read back.

**Success Criteria:**
1. Alice confirms the vehicle as a 2022 Ford (make/year captured) without re-asking data you already gave.
2. Alice asks whether the vehicle was bought new or used, whether you visited a dealership for repairs, and whether you are the owner — and nothing about mileage, out-of-service days, or number of repair visits.
3. Alice confirms your name, phone, and email, spells your name back letter by letter, and reads your phone number digit by digit.
4. Alice offers to send the **retainer agreement to sign** and tells you that you'll **receive your documents soon**.
5. Alice does NOT ask for a home/street address or mention a consultation booking link.

**Expected Lead Status:** `Retainer Lead`

---

## A2 — CPO retainer at the 2020 boundary  *(validates "2020 continues" fix)*
**Dynamic variables:** `Name = Maria Lopez`, `Phone = +13105552020`, `Email = maria.lopez@example.com`.
**User Persona:**
- **Identity:** You are Maria Lopez. You have a **2020 BMW i4** bought from a BMW dealer **in California**. It was **used but Certified Pre-Owned (CPO)**. You still possess it, you signed the contract, and you've taken it in for repairs.
- **Goal:** Get your lemon vehicle case started.
- **Personality:** Friendly, concise. If asked new or used, say "used, but certified pre-owned."

**Success Criteria:**
1. Alice does NOT disqualify the vehicle for its model year (2020 must be treated as eligible).
2. When you say "used," Alice asks whether it is Certified Pre-Owned, and accepts "yes" as qualifying.
3. Alice asks about repair visits and ownership, then confirms/validates your name, phone, and email.
4. Alice offers to send the **retainer agreement to sign** and says your **documents will arrive soon**.

**Expected Lead Status:** `Retainer Lead`

---

## A3 — Retainer with no possession (exempt manufacturer)
**Dynamic variables:** `Name = David Kim`, `Phone = +13105553031`, `Email = david.kim@example.com`.
**User Persona:**
- **Identity:** You are David Kim. You have a new **2021 BMW X3** bought from a BMW dealer **in California**. You **no longer have possession** of the vehicle. You signed the contract and you took it in for repairs.
- **Goal:** Find out if you still have a case even though you gave the car back.
- **Personality:** Slightly worried you won't qualify; otherwise cooperative.

**Success Criteria:**
1. When you say you are not in possession, Alice asks the make, and because it's a BMW she **continues** instead of disqualifying you.
2. Alice proceeds through the eligibility questions (new/used, repairs, ownership).
3. Alice offers to send the **retainer agreement to sign**.

**Expected Lead Status:** `Retainer Lead`

---

# GROUP B — Non-Retainer leads (should offer a consultation booking link)

## B1 — Wrong make (Honda)
**Dynamic variables:** `Name = Sarah Bennett`, `Phone = +13105554041`, `Email = sarah.bennett@example.com`.
**User Persona:**
- **Identity:** You are Sarah Bennett. You have a **2023 Honda Civic** bought from a Honda dealer **in California**. You still possess it.
- **Goal:** Get help with your car troubles.
- **Personality:** Polite, a little impatient.

**Success Criteria:**
1. Alice does NOT offer to send a retainer agreement to sign.
2. Alice confirms/validates your contact details and tells you that you'll **receive a consultation booking link by text** to speak with an Intake Analyst.
3. Alice does NOT ask for a home/street address.

**Expected Lead Status:** `Non-Retainer Lead`

---

## B2 — Retainer make but no repair attempts
**Dynamic variables:** `Name = Robert Hayes`, `Phone = +13105555051`, `Email = robert.hayes@example.com`.
**User Persona:**
- **Identity:** You are Robert Hayes. You have a new **2022 Kia Sorento** bought **in California**, still in your possession, signed by you. You have **NOT** taken it to a dealership for repairs yet.
- **Goal:** See what your options are.
- **Personality:** Matter-of-fact.

**Success Criteria:**
1. Alice asks whether you've visited a dealership to attempt repairs; when you say no, she does NOT offer a retainer agreement.
2. Alice tells you that you'll receive a **consultation booking link by text**.

**Expected Lead Status:** `Non-Retainer Lead`

---

## B3 — Retainer make but not the owner
**Dynamic variables:** `Name = Emily Stone`, `Phone = +13105556061`, `Email = emily.stone@example.com`.
**User Persona:**
- **Identity:** You are Emily Stone. There's a new **2021 Jeep Gladiator** bought **in California**, in your possession, taken in for repairs. But you did **NOT** sign the sales contract and you are **not** the owner — your brother is.
- **Goal:** Find out if you can do anything about the truck's problems.
- **Personality:** Helpful, honest about not being the owner.

**Success Criteria:**
1. When Alice asks if you are the owner or signed the contract, you say no, and she does NOT offer a retainer agreement.
2. Alice tells you that you'll receive a **consultation booking link by text**.

**Expected Lead Status:** `Non-Retainer Lead`

---

## B4 — No possession + wrong make (exempt manufacturer)
**Dynamic variables:** `Name = Tom Reeves`, `Phone = +13105557071`, `Email = tom.reeves@example.com`.
**User Persona:**
- **Identity:** You are Tom Reeves. You had a **2022 Toyota Yaris** bought **in California**, but you **no longer possess** it.
- **Goal:** See if you still have a claim.
- **Personality:** Brief.

**Success Criteria:**
1. When you say you're not in possession, Alice continues (Toyota is exempt) rather than disqualifying for possession.
2. Because the make is not on the retainer list, Alice does NOT offer a retainer agreement and instead offers a **consultation booking link by text**.

**Expected Lead Status:** `Non-Retainer Lead`

---

# GROUP C — Bad leads (should explain disqualification, then end)

## C1 — Out of state purchase
**Dynamic variables:** `Name = Greg Palmer`, `Phone = +13105558081`, `Email = greg.palmer@example.com`.
**User Persona:**
- **Identity:** You are Greg Palmer. You bought your vehicle from a dealership in **Nevada**, not California.
- **Goal:** Get help with your vehicle issues.
- **Personality:** Cooperative.

**Success Criteria:**
1. When Alice asks if you bought/leased from a California dealership, you say no.
2. Alice apologizes and explains the firm can only handle vehicles purchased **within California**, so she cannot move forward.
3. Alice does NOT continue asking about make, year, repairs, or ownership.

**Expected Lead Status / Reason:** `Bad Lead` / **Out of state purchase**

---

## C2 — Vehicle too old (2019)  *(validates new ≤2019 = Bad Lead cutoff)*
**Dynamic variables:** `Name = Nancy Ford`, `Phone = +13105559091`, `Email = nancy.ford@example.com`.
**User Persona:**
- **Identity:** You are Nancy Ford. You have a **2019 Ford Explorer** bought **in California**, still in your possession.
- **Goal:** Get help with your car.
- **Personality:** Cooperative; give the year as "twenty nineteen" if asked.

**Success Criteria:**
1. After learning the vehicle is a 2019, Alice tells you it does **not** qualify because of its **model year**.
2. Alice references that the firm handles **2020 and newer** vehicles.
3. Alice does NOT offer a retainer agreement and does NOT offer a consultation booking link.

**Expected Lead Status / Reason:** `Bad Lead` / **Vehicle year**

---

## C3 — No possession (opted-in manufacturer)
**Dynamic variables:** `Name = Alan Pierce`, `Phone = +13105550102`, `Email = alan.pierce@example.com`.
**User Persona:**
- **Identity:** You are Alan Pierce. You had a **Ford** bought **in California**, but you **no longer possess** the vehicle.
- **Goal:** See if you still have a claim.
- **Personality:** Brief; if asked the make, say "Ford."

**Success Criteria:**
1. When you say you're not in possession, Alice asks the make; because it's a Ford she explains you must **still be in possession** to open a claim and cannot proceed.
2. Alice does NOT continue into year/repairs/ownership questions.

**Expected Lead Status / Reason:** `Bad Lead` / **Not in possession of vehicle**

---

## C4 — Used, non-CPO
**Dynamic variables:** `Name = Olivia Grant`, `Phone = +13105550113`, `Email = olivia.grant@example.com`.
**User Persona:**
- **Identity:** You are Olivia Grant. You have a **2021 Jeep Gladiator** bought **in California**, still in your possession, signed by you. It was bought **used** and it is **NOT** Certified Pre-Owned.
- **Goal:** Get help with the Jeep.
- **Personality:** Cooperative. If asked new/used say "used"; if asked CPO say "no."

**Success Criteria:**
1. Alice asks new or used; on "used" she asks if it's Certified Pre-Owned; on "no" she disqualifies.
2. Alice explains the vehicle was purchased used and is not CPO, so it lacks the original manufacturer warranty needed.
3. Alice does NOT offer a retainer agreement or a consultation link.

**Expected Lead Status / Reason:** `Bad Lead` / **Purchased used non CPO**

---

## C5 — No current issues (non-lemon)
**Dynamic variables:** `Name = Peter Shaw`, `Phone = +13105550124`, `Email = peter.shaw@example.com`.
**User Persona:**
- **Identity:** You are Peter Shaw. Your car is running **fine** — you are not having any problems with it.
- **Goal:** You're not sure why you were called; you have no vehicle issues.
- **Personality:** Friendly but puzzled.

**Success Criteria:**
1. In the opening, when Alice asks if you're experiencing issues with your vehicle, you say no / it's running fine.
2. Alice does NOT start the qualification questions (California, possession, make, year).
3. Alice politely explains there's no active claim to file and invites you to reach out if issues arise later.

**Expected Lead Status / Reason:** `Bad Lead` / **Non lemon law**

---

# GROUP D — Boundary & behavioral tests

## D1 — Spanish language switch
**Dynamic variables:** `Name = Carlos Mendoza`, `Phone = +13105550135`, `Email = carlos.mendoza@example.com`.
**User Persona:**
- **Identity:** Eres Carlos Mendoza. Tienes un **Ford F-150 2022** comprado **en California**, en tu posesión, nuevo, lo llevaste a reparar y eres el dueño.
- **Goal:** Obtener ayuda con tu vehículo. **Responde siempre en español.**
- **Personality:** Amable y directo. Habla únicamente en español durante toda la llamada.

**Success Criteria:**
1. As soon as you reply in Spanish, Alice switches to Spanish and conducts the **entire** remaining conversation in Spanish.
2. Alice never asks which language you prefer.
3. Alice completes qualification and offers to send the retainer agreement (in Spanish).

**Expected Lead Status:** `Retainer Lead` · **Lead Language:** `Spanish`

---

## D2 — Compound answer capture
**Dynamic variables:** defaults (`John Carter`).
**User Persona:**
- **Identity:** You are John Carter with a **2022 Ford F-150**, bought new **in California**, in your possession, taken in for repairs, and you're the owner.
- **Goal:** Move quickly. In your **first answer about the vehicle**, volunteer everything at once: "It's a 2022 Ford F-150, I bought it new in California, I still have it, and I took it to the dealer for repairs."
- **Personality:** Fast-talking, gives lots of detail up front.

**Success Criteria:**
1. After your compound answer, Alice does NOT re-ask the year, make, or model you already provided.
2. Alice briefly acknowledges the captured details (e.g., "Got it, a 2022 Ford") and only asks for what's still missing.
3. The call still reaches the retainer agreement offer.

**Expected Lead Status:** `Retainer Lead`

---

## D3 — Hesitation / asks for a human  *(send_consultation_link should fire)*
**Dynamic variables:** defaults (`John Carter`).
**User Persona:**
- **Identity:** You are John Carter with a **2022 Ford F-150** (CA, possessed, new, repaired, owner).
- **Goal:** Early in the qualification — right after the California question — get frustrated and say: "Honestly, can I just talk to a real person? Am I even talking to a human right now?"
- **Personality:** Skeptical and a bit frustrated, but you do continue answering once reassured.

**Success Criteria:**
1. When you ask for a human / suspect an AI, Alice acknowledges your concern, tells you a booking link has been sent so you can speak with an Intake Analyst, and gives the alternate number **(310) 552-2250**.
2. Alice then **resumes the qualification script** rather than ending the call.
3. (Reviewer check) The `send_consultation_link` function was triggered once.

**Expected Lead Status:** `Retainer Lead`

---

## D4 — Incomplete (busy, call back later)
**Dynamic variables:** defaults (`John Carter`).
**User Persona:**
- **Identity:** You are John Carter, driving and busy.
- **Goal:** End the call quickly. After Alice's greeting, say: "I'm driving right now, can you call me back later?"
- **Personality:** Rushed, polite.

**Success Criteria:**
1. Alice does NOT push through the qualification questions.
2. Alice ends politely and does NOT state a lead classification or a disqualification reason to you.

**Expected Lead Status:** `Incomplete Lead`

---

## Scorecard

| # | Test | Verifies | Expected |
|---|------|----------|----------|
| A1 | Perfect retainer (Ford 2022) | Full retainer happy path | Retainer Lead |
| A2 | CPO @ 2020 (BMW i4) | **2020 now continues** + CPO branch | Retainer Lead |
| A3 | No-possession exempt (BMW 2021) | Not-Opted-In possession waiver | Retainer Lead |
| B1 | Wrong make (Honda 2023) | Make-based non-retainer | Non-Retainer |
| B2 | No repairs (Kia 2022) | Eligibility downgrade (repairs) | Non-Retainer |
| B3 | Not owner (Jeep 2021) | Eligibility downgrade (owner) | Non-Retainer |
| B4 | No-poss + wrong make (Toyota) | Exempt continue → wrong make | Non-Retainer |
| C1 | Out of state | Step-1 short-circuit | Bad — Out of state |
| C2 | Year 2019 | **New ≤2019 cutoff** | Bad — Vehicle year |
| C3 | No-poss opted-in (Ford) | Opted-In possession disqualify | Bad — Not in possession |
| C4 | Used non-CPO (Jeep) | CPO disqualify | Bad — Used non CPO |
| C5 | No issues | Intro non-lemon branch | Bad — Non lemon law |
| D1 | Spanish switch | Auto language switch | Retainer · Spanish |
| D2 | Compound capture | No re-asking captured data | Retainer Lead |
| D3 | Hesitation / human | `send_consultation_link` fires + resumes | Retainer Lead |
| D4 | Busy / call back | Graceful incomplete close | Incomplete Lead |

**Boundary bracket for the year change:** **C2 (2019 → Bad)** and **A2 (2020 → Retainer)** together prove the new cutoff. Optionally add a 2020 Ford run to double-confirm the clean retainer-make lower edge.
