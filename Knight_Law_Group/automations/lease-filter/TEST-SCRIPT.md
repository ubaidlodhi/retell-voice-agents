# Lease + Tesla filter: quick test script (4 calls)

Four outbound calls to your own phone, on the **draft** intake agent. The live number stays on the published version, so real leads are not affected. Each call covers several changes at once. The 27 routing rules (every make, lease type and year combination) are already covered by the automated tests, so these calls only check what a real conversation can break: the wording, the question order, the language and the hand-off.

**Before you start**
- The draft exists and has the lease patch (plan Task 0 Step 5 + Task 7 Step 4).
- For the n8n checks: n8n is running again and the n8n lease patch is pushed. Without them the call checks still work and the n8n lines show `SKIP`.
- Call D really sends the representation agreement, so use your own phone and email.

**How to run each call**
```bash
cd D:/retell-voice-agents/Knight_Law_Group/automations/lease-filter
node test_call.js call A --to +1XXXXXXXXXX --email you@example.com
# answer, follow the script below, hang up at the end
node test_call.js check <call_id printed above> A
```

---

## A. English: lease said up front, Honda (lease arbitration)

| Alice | You say |
|---|---|
| (you pick up) | "Hello?" |
| New greeting: "...calling about the lemon law inquiry... I'm an AI assistant... Mind if I ask you a couple of quick questions about the car?" | "Sure." |
| "Are you having any issues with the vehicle?" | "Yes, the transmission." |
| "Did you purchase or lease your vehicle from a dealership in California?" | **"Yes, I leased it in LA."** |
| Should skip "purchase or lease" and ask only: "Is it still leased, or did you later buy it out?" | "Still leased." |
| Possession, then year / make / model | "Yes" / **"2023 Honda Civic"** / confirm |
| **Lease arbitration line:** "Since your vehicle is leased, the manufacturer is actually a party to your lease agreement..." | "Okay." (hang up after the goodbye) |

**Pass:** new greeting · lease question NOT asked again · lease line said · in-call `bad_reason = arbitration_lease` · n8n `Bad Lead / Requires Arbitration / Leased`.

## B. Spanish: pick up with "¿Bueno?", leased then bought, Acura (buyout arbitration)

| Alice | You say |
|---|---|
| (you pick up) | **"¿Bueno?"** |
| Spanish greeting: "Hola, le habla Alice, de Knight Law Group..." | "Sí, claro." |
| "¿Está teniendo problemas con su vehículo?" | "Sí, el motor." |
| "¿Lo compró o lo arrendó en un concesionario de California?" | "Sí, en California." |
| **"¿Usted compró el vehículo, o lo arrendó?"** | **"Lo arrendé y después lo compré."** |
| Possession, then year / make / model | "Sí" / **"2022 Acura RDX"** / confirm |
| **Buyout line in Spanish:** "Como su vehículo comenzó como un arrendamiento..." | "Está bien." |

**Pass:** Spanish greeting from the pickup word · question in Spanish · buyout line (not the plain lease line) · `bad_reason = arbitration_buyout` · n8n `Leased, then purchased`.

## C. English: bought, Tesla (Tesla arbitration)

| Alice | You say |
|---|---|
| Greeting / issues / California | "Sure" / "Yes, the screen keeps failing" / "Yes, in San Diego." |
| **"Did you purchase the vehicle, or lease it?"** | **"I bought it."** |
| Possession, then year / make / model | "Yes" / **"2024 Tesla Model 3"** / confirm |
| **Tesla line:** "Tesla's purchase and lease agreements include a clause requiring disputes to go through arbitration..." | "Okay." |

**Pass:** Tesla line (NOT "since your vehicle is leased") · `bad_reason = arbitration_tesla` · n8n `Bad Lead / Requires Arbitration / Purchased`.

## D. English: "financed" is a lease, Ford, full retainer path (name, new/used, AI hand-off)

| Alice | You say |
|---|---|
| Greeting / issues / California | "Sure" / "Yes, brakes" / "Yes, in Los Angeles." |
| "Did you purchase the vehicle, or lease it?" | **"It's financed."** |
| Should ask once: "Is that a lease, or a loan to buy it?" | **"A lease."** |
| "Is it still leased, or did you later buy it out?" | "Still leased." |
| Possession, then year / make / model | "Yes" / **"2023 Ford F-150"** / confirm |
| New wording: **"Was the vehicle new or used when you got it?"** | **"Used."** |
| "Is it certified pre-owned?" / repairs / owner | "Yes" / "Yes" / "Yes, I signed the lease." |
| "I've got your name as Test Retainer Ford, is that the same as your driver's license?" | **"No."** |
| "Could you spell your full name?" | **"J-O-N, D-O-E."** |
| Should just say "Thank you, I've got it" with **no spelling back**, then ask about email + text/email permission | "Yes, that's fine." |
| **AI hand-off line:** "Great, we can move forward. I'll text and email you the representation agreement..." then the retainer agent greets you as **"Jon"** | Hang up after the retainer agent's first line. |

**Pass:** lease-or-loan asked once · new/used wording · Alice spelled the name 0 times · `confirmed_name` captured and used in the hand-off greeting · hand-off line said · `route = retainer` · n8n `Retainer Lead / Leased`.

---

If a check fails, `check` prints the full transcript. Paste the output here and I'll fix and re-run only that scenario.
