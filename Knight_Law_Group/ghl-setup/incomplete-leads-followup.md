# Workflow: Incomplete Leads — Follow-up Cadence (EN / ES)

**Purpose:** Re-engage leads marked **Incomplete** by Retell (didn't answer, no time to talk, or hung up mid-qualification). The firm keeps **calling on its own schedule**, so the SMS/email here are *nudges to pick up / call us back* — **not** booking requests. No vehicle details are referenced, so the same templates work for every lead.

**Client cadence implemented:**
- Trigger when a lead is **Incomplete** and stays unresponsive for **24 hours**.
- **Days 1–3 (daily):** 2 calls/day (AM + evening) + 1 SMS + 1 email each day.
- **Day 4 onward:** same bundle **every other day**, until the lead **opts out or responds**.
- **All touches only fire 8 AM–9 PM PST.**

> Note: the voicemail script says the team is available until **8 PM PT**, but you asked for a **9 PM PST** send window for this cadence — I used 9 PM here. Flag if you want them aligned.

---

## 1. GHL Workflow build

### Workflow Settings
- **Timezone:** `Account` → set the sub-account timezone to **America/Los_Angeles (PST/PDT)** so every Wait/window uses California time. (Use *Contact timezone* only if you'd rather respect each lead's local time — but the client asked for CA time, so use Account.)
- **Stop on Response: ON** → any reply (SMS/email) auto-ends the cadence for that contact ("respond" exit).
- **Allow Re-Entry: OFF** (a lead shouldn't be in the cadence twice).

### Trigger
- **Trigger:** `Contact Changed` (or `Custom Field Updated`) → **Filter:** `Lead Status` **is** `Incomplete Lead`.
  - `Lead Status` is the field your Retell post-call webhook writes (values: Retainer Lead / Non-Retainer Lead / Bad Lead / **Incomplete Lead** / Opt-Out Consent). Make sure that webhook maps `Lead Status` → a GHL **custom field**.

### Step A — 24-hour unresponsive gate
1. **Wait Step** → `Time Delay` = **24 hours**.
   - With **Stop on Response ON**, anyone who replies or is re-qualified inside 24h drops out automatically before the cadence starts. This is the "unresponsive during 24 hours → trigger cadence" rule.

### Step B — Language split
2. **If/Else** → Condition: `Lead Language` (Retell field) **is** `Spanish`.
   - **Yes →** ES branch. **No / else →** EN branch.
   - (Everything below is per-branch; build it once in EN, duplicate the branch and swap in the ES templates.)

### Step C — "Still Incomplete?" guard (reused before every day-block)
Before each day's touches, add:
3. **If/Else** → `Lead Status` **is** `Incomplete Lead` **AND** `DND` (SMS/Call/Email) **is** `false`.
   - **No / else →** **Remove from Workflow** (covers "they responded / got re-qualified / opted out").

### Step D — Day 1 (and same shape for Day 2, Day 3)
4. **Wait Step** → "Wait until a specific time of day" = **9:00 AM**, **window 08:00–21:00**, days Mon–Sun, timezone Account.
5. **Custom Webhook** → *Retell re-call (AM)* — see §1.1 below.
6. **Wait Step** → 2 minutes (let the call attempt start before texting).
7. **Send SMS** → `SMS Day 1` (EN or ES).
8. **Send Email** → `Email Day 1` (EN or ES).
9. **Wait Step** → "Wait until a specific time of day" = **6:00 PM**, same window/timezone.
10. **Custom Webhook** → *Retell re-call (Evening)*.
- **Repeat Steps 3–10** for **Day 2** (`SMS Day 2` / `Email Day 2`) and **Day 3** (`SMS Day 3` / `Email Day 3`). The "wait until 9:00 AM" naturally lands on the next day each time.

### Step E — Phase 2: every-other-day loop (Day 4+)
11. **If/Else** guard (same as Step C). Else → Remove from Workflow.
12. **Wait Step** → `Time Delay` = **2 days**, **with delivery window 08:00–21:00 PST** (Advanced → "only release during this window"), release time **9:00 AM**.
13. **Custom Webhook** → *Retell re-call (AM)*.
14. **Wait** 2 min → **Send SMS** `SMS Recurring` → **Send Email** `Email Recurring`.
15. **Wait Step** → until **6:00 PM** (window-bound) → **Custom Webhook** *Retell re-call (Evening)*.
16. **Go To** → **Step 11**. This loops every other day until Stop-on-Response, DND/opt-out, or the Lead Status guard removes them.

### Exit conditions (summary)
| Exit | How it's handled |
|---|---|
| Lead **responds** (texts/emails back) | **Stop on Response = ON** ends the workflow |
| Lead **answers a call** & gets re-qualified | Retell rewrites `Lead Status` → the Step C/E **If/Else guard** removes them |
| Lead **opts out** (replies STOP) | GHL auto-sets **DND**; the guard's `DND = false` check removes them. (Also catch `Lead Status = Opt-Out Consent`.) |
| Safety cap (optional) | Add a counter custom field or a hard "after 14 days → Remove from Workflow" if you don't want a true infinite loop |

### 1.1 — The "Call" step (Retell re-dial via Custom Webhook)
GHL's native **Call** action dials the contact and bridges to a *user/number*, not your AI agent. To re-run the **Retell** outbound agent, use a **Custom Webhook** action:

- **Method:** `POST`
- **URL:** `https://api.retellai.com/v2/create-phone-call`
- **Headers:** `Authorization: Bearer <YOUR_RETELL_API_KEY>`, `Content-Type: application/json`
- **Body (JSON):**
```json
{
  "from_number": "+12132053651",
  "to_number": "{{contact.phone}}",
  "override_agent_id": "<your_published_agent_id>",
  "retell_llm_dynamic_variables": {
    "Name": "{{contact.first_name}} {{contact.last_name}}",
    "Phone": "{{contact.phone}}",
    "Email": "{{contact.email}}"
  }
}
```
- `from_number` = the agent's outbound number **(213) 205-3651**. `override_agent_id` = your published Knight Law agent. (If you already trigger Retell via your existing LeadConnector hook, you can reuse that instead of this webhook.)

---

## 2. SMS templates

Merge field: `{{contact.first_name}}` (set a default like "there" in GHL so it never renders blank). All include opt-out language. No vehicle data, no "pick a time."

### English
**SMS Day 1**
```
Hi {{contact.first_name}}, this is Alice from Knight Law Group. We tried to reach you about your vehicle inquiry but couldn't connect. We'll try you again soon — or call us back anytime at (310) 552-2250. Reply STOP to opt out.
```
**SMS Day 2**
```
Hi {{contact.first_name}}, Alice from Knight Law Group again. We'd still love to help with your vehicle matter. We'll give you another call today — or reach us directly at (310) 552-2250. Reply STOP to opt out.
```
**SMS Day 3**
```
Hi {{contact.first_name}}, just checking in from Knight Law Group. We haven't been able to reach you yet. A quick call is all it takes — call us at (310) 552-2250 whenever works for you. Reply STOP to opt out.
```
**SMS Recurring (Day 4+)**
```
Hi {{contact.first_name}}, Knight Law Group here. We're still trying to connect about your vehicle inquiry. When you have a moment, give us a call at (310) 552-2250. Reply STOP to opt out.
```

### Spanish
**SMS Día 1**
```
Hola {{contact.first_name}}, le saluda Alice de Knight Law Group. Intentamos comunicarnos con usted sobre su consulta de vehículo pero no pudimos. Lo intentaremos de nuevo pronto, o llámenos al (310) 552-2250. Responda STOP para no recibir más mensajes.
```
**SMS Día 2**
```
Hola {{contact.first_name}}, le escribe Alice de Knight Law Group otra vez. Aún queremos ayudarle con su asunto del vehículo. Le llamaremos de nuevo hoy, o comuníquese al (310) 552-2250. Responda STOP para cancelar.
```
**SMS Día 3**
```
Hola {{contact.first_name}}, le saludamos de Knight Law Group. Todavía no hemos podido comunicarnos con usted. Una llamada breve es suficiente: llámenos al (310) 552-2250 cuando guste. Responda STOP para cancelar.
```
**SMS Recurrente (Día 4+)**
```
Hola {{contact.first_name}}, le contactamos de Knight Law Group. Seguimos intentando comunicarnos sobre su consulta de vehículo. Cuando pueda, llámenos al (310) 552-2250. Responda STOP para cancelar.
```

---

## 3. Email templates (HTML)

Paste each into a GHL email step using the **"Custom Code / HTML"** element. From name **Knight Law Group**, from email **alicep@h.knightlaw.com**. `{{unsubscribe_link}}` is GHL's merge field — swap for your account's exact unsubscribe token if different.

### English

**Email Day 1 — Subject: `We tried to reach you — Knight Law Group`**
```html
<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
<span style="display:none!important;visibility:hidden;opacity:0;color:transparent;height:0;width:0;overflow:hidden;">We tried to reach you about your vehicle inquiry.</span>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:8px;overflow:hidden;">
<tr><td style="background:#0b2a4a;padding:20px 32px;"><span style="color:#ffffff;font-size:20px;font-weight:bold;letter-spacing:.5px;">KNIGHT LAW GROUP</span></td></tr>
<tr><td style="padding:32px;color:#333333;font-size:16px;line-height:1.6;">
<p style="margin:0 0 16px;">Hi {{contact.first_name}},</p>
<p style="margin:0 0 16px;">This is Alice from <strong>Knight Law Group</strong>. We recently tried to reach you about your vehicle inquiry but weren't able to connect.</p>
<p style="margin:0 0 24px;">No action is needed on your part — we'll try you again shortly. If you'd like to reach us sooner, we're happy to help whenever it's convenient for you.</p>
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 24px;"><tr><td style="border-radius:6px;background:#0b6b3a;"><a href="tel:+13105522250" style="display:inline-block;padding:14px 28px;color:#ffffff;font-size:16px;font-weight:bold;text-decoration:none;">Call us: (310) 552-2250</a></td></tr></table>
<p style="margin:0;">Warm regards,<br><strong>Alice</strong><br>Knight Law Group</p>
</td></tr>
<tr><td style="padding:20px 32px;background:#f0f0f3;color:#888888;font-size:12px;line-height:1.5;">
<p style="margin:0 0 8px;">Knight Law Group &middot; Serving clients across California &middot; (310) 552-2250</p>
<p style="margin:0;">You're receiving this because you contacted us about a vehicle matter. <a href="{{unsubscribe_link}}" style="color:#888888;">Unsubscribe</a> or reply STOP to any text.</p>
</td></tr></table></td></tr></table></body></html>
```

**Email Day 2 — Subject: `Still hoping to connect about your vehicle`**
```html
<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
<span style="display:none!important;visibility:hidden;opacity:0;color:transparent;height:0;width:0;overflow:hidden;">We'd still love to help with your vehicle matter.</span>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:8px;overflow:hidden;">
<tr><td style="background:#0b2a4a;padding:20px 32px;"><span style="color:#ffffff;font-size:20px;font-weight:bold;letter-spacing:.5px;">KNIGHT LAW GROUP</span></td></tr>
<tr><td style="padding:32px;color:#333333;font-size:16px;line-height:1.6;">
<p style="margin:0 0 16px;">Hi {{contact.first_name}},</p>
<p style="margin:0 0 16px;">We tried you again today and still weren't able to reach you. We'd genuinely like to help you understand your options regarding your vehicle.</p>
<p style="margin:0 0 24px;">There's nothing you need to prepare — just a short conversation when you're ready. We'll keep trying, or you can reach us directly below.</p>
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 24px;"><tr><td style="border-radius:6px;background:#0b6b3a;"><a href="tel:+13105522250" style="display:inline-block;padding:14px 28px;color:#ffffff;font-size:16px;font-weight:bold;text-decoration:none;">Call us: (310) 552-2250</a></td></tr></table>
<p style="margin:0;">Warm regards,<br><strong>Alice</strong><br>Knight Law Group</p>
</td></tr>
<tr><td style="padding:20px 32px;background:#f0f0f3;color:#888888;font-size:12px;line-height:1.5;">
<p style="margin:0 0 8px;">Knight Law Group &middot; Serving clients across California &middot; (310) 552-2250</p>
<p style="margin:0;">You're receiving this because you contacted us about a vehicle matter. <a href="{{unsubscribe_link}}" style="color:#888888;">Unsubscribe</a> or reply STOP to any text.</p>
</td></tr></table></td></tr></table></body></html>
```

**Email Day 3 — Subject: `A quick call is all it takes`**
```html
<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
<span style="display:none!important;visibility:hidden;opacity:0;color:transparent;height:0;width:0;overflow:hidden;">A quick call is all it takes to get started.</span>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:8px;overflow:hidden;">
<tr><td style="background:#0b2a4a;padding:20px 32px;"><span style="color:#ffffff;font-size:20px;font-weight:bold;letter-spacing:.5px;">KNIGHT LAW GROUP</span></td></tr>
<tr><td style="padding:32px;color:#333333;font-size:16px;line-height:1.6;">
<p style="margin:0 0 16px;">Hi {{contact.first_name}},</p>
<p style="margin:0 0 16px;">We've been trying to reach you over the past few days and haven't connected yet. We don't want you to miss the chance to have your situation reviewed.</p>
<p style="margin:0 0 24px;">It only takes a short call. We'll try you again, or reach us anytime at the number below.</p>
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 24px;"><tr><td style="border-radius:6px;background:#0b6b3a;"><a href="tel:+13105522250" style="display:inline-block;padding:14px 28px;color:#ffffff;font-size:16px;font-weight:bold;text-decoration:none;">Call us: (310) 552-2250</a></td></tr></table>
<p style="margin:0;">Warm regards,<br><strong>Alice</strong><br>Knight Law Group</p>
</td></tr>
<tr><td style="padding:20px 32px;background:#f0f0f3;color:#888888;font-size:12px;line-height:1.5;">
<p style="margin:0 0 8px;">Knight Law Group &middot; Serving clients across California &middot; (310) 552-2250</p>
<p style="margin:0;">You're receiving this because you contacted us about a vehicle matter. <a href="{{unsubscribe_link}}" style="color:#888888;">Unsubscribe</a> or reply STOP to any text.</p>
</td></tr></table></td></tr></table></body></html>
```

**Email Recurring (Day 4+) — Subject: `We're still here to help`**
```html
<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
<span style="display:none!important;visibility:hidden;opacity:0;color:transparent;height:0;width:0;overflow:hidden;">We're still here to help whenever you're ready.</span>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:8px;overflow:hidden;">
<tr><td style="background:#0b2a4a;padding:20px 32px;"><span style="color:#ffffff;font-size:20px;font-weight:bold;letter-spacing:.5px;">KNIGHT LAW GROUP</span></td></tr>
<tr><td style="padding:32px;color:#333333;font-size:16px;line-height:1.6;">
<p style="margin:0 0 16px;">Hi {{contact.first_name}},</p>
<p style="margin:0 0 16px;">We're still here whenever you're ready to talk about your vehicle. There's no pressure and no obligation — just a quick conversation to see how we can help.</p>
<p style="margin:0 0 24px;">We'll continue to reach out periodically, but feel free to call us anytime at the number below.</p>
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 24px;"><tr><td style="border-radius:6px;background:#0b6b3a;"><a href="tel:+13105522250" style="display:inline-block;padding:14px 28px;color:#ffffff;font-size:16px;font-weight:bold;text-decoration:none;">Call us: (310) 552-2250</a></td></tr></table>
<p style="margin:0;">Warm regards,<br><strong>Alice</strong><br>Knight Law Group</p>
</td></tr>
<tr><td style="padding:20px 32px;background:#f0f0f3;color:#888888;font-size:12px;line-height:1.5;">
<p style="margin:0 0 8px;">Knight Law Group &middot; Serving clients across California &middot; (310) 552-2250</p>
<p style="margin:0;">You're receiving this because you contacted us about a vehicle matter. <a href="{{unsubscribe_link}}" style="color:#888888;">Unsubscribe</a> or reply STOP to any text.</p>
</td></tr></table></td></tr></table></body></html>
```

### Spanish

**Email Día 1 — Asunto: `Intentamos comunicarnos con usted — Knight Law Group`**
```html
<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
<span style="display:none!important;visibility:hidden;opacity:0;color:transparent;height:0;width:0;overflow:hidden;">Intentamos comunicarnos con usted sobre su vehículo.</span>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:8px;overflow:hidden;">
<tr><td style="background:#0b2a4a;padding:20px 32px;"><span style="color:#ffffff;font-size:20px;font-weight:bold;letter-spacing:.5px;">KNIGHT LAW GROUP</span></td></tr>
<tr><td style="padding:32px;color:#333333;font-size:16px;line-height:1.6;">
<p style="margin:0 0 16px;">Hola {{contact.first_name}},</p>
<p style="margin:0 0 16px;">Le saluda Alice de <strong>Knight Law Group</strong>. Recientemente intentamos comunicarnos con usted sobre su consulta de vehículo, pero no pudimos localizarle.</p>
<p style="margin:0 0 24px;">No necesita hacer nada — lo intentaremos de nuevo en breve. Si prefiere comunicarse antes, con gusto le atendemos cuando le sea conveniente.</p>
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 24px;"><tr><td style="border-radius:6px;background:#0b6b3a;"><a href="tel:+13105522250" style="display:inline-block;padding:14px 28px;color:#ffffff;font-size:16px;font-weight:bold;text-decoration:none;">Llámenos: (310) 552-2250</a></td></tr></table>
<p style="margin:0;">Cordialmente,<br><strong>Alice</strong><br>Knight Law Group</p>
</td></tr>
<tr><td style="padding:20px 32px;background:#f0f0f3;color:#888888;font-size:12px;line-height:1.5;">
<p style="margin:0 0 8px;">Knight Law Group &middot; Al servicio de clientes en toda California &middot; (310) 552-2250</p>
<p style="margin:0;">Recibe este mensaje porque nos contactó sobre un asunto de vehículo. <a href="{{unsubscribe_link}}" style="color:#888888;">Cancelar suscripción</a> o responda STOP a cualquier texto.</p>
</td></tr></table></td></tr></table></body></html>
```

**Email Día 2 — Asunto: `Aún queremos comunicarnos sobre su vehículo`**
```html
<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
<span style="display:none!important;visibility:hidden;opacity:0;color:transparent;height:0;width:0;overflow:hidden;">Aún queremos ayudarle con su asunto del vehículo.</span>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:8px;overflow:hidden;">
<tr><td style="background:#0b2a4a;padding:20px 32px;"><span style="color:#ffffff;font-size:20px;font-weight:bold;letter-spacing:.5px;">KNIGHT LAW GROUP</span></td></tr>
<tr><td style="padding:32px;color:#333333;font-size:16px;line-height:1.6;">
<p style="margin:0 0 16px;">Hola {{contact.first_name}},</p>
<p style="margin:0 0 16px;">Intentamos comunicarnos de nuevo hoy y aún no logramos localizarle. De verdad nos gustaría ayudarle a conocer sus opciones respecto a su vehículo.</p>
<p style="margin:0 0 24px;">No necesita preparar nada — solo una breve conversación cuando esté listo. Seguiremos intentando, o puede comunicarse directamente aquí abajo.</p>
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 24px;"><tr><td style="border-radius:6px;background:#0b6b3a;"><a href="tel:+13105522250" style="display:inline-block;padding:14px 28px;color:#ffffff;font-size:16px;font-weight:bold;text-decoration:none;">Llámenos: (310) 552-2250</a></td></tr></table>
<p style="margin:0;">Cordialmente,<br><strong>Alice</strong><br>Knight Law Group</p>
</td></tr>
<tr><td style="padding:20px 32px;background:#f0f0f3;color:#888888;font-size:12px;line-height:1.5;">
<p style="margin:0 0 8px;">Knight Law Group &middot; Al servicio de clientes en toda California &middot; (310) 552-2250</p>
<p style="margin:0;">Recibe este mensaje porque nos contactó sobre un asunto de vehículo. <a href="{{unsubscribe_link}}" style="color:#888888;">Cancelar suscripción</a> o responda STOP a cualquier texto.</p>
</td></tr></table></td></tr></table></body></html>
```

**Email Día 3 — Asunto: `Una llamada breve es todo lo que se necesita`**
```html
<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
<span style="display:none!important;visibility:hidden;opacity:0;color:transparent;height:0;width:0;overflow:hidden;">Una llamada breve es todo lo que se necesita.</span>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:8px;overflow:hidden;">
<tr><td style="background:#0b2a4a;padding:20px 32px;"><span style="color:#ffffff;font-size:20px;font-weight:bold;letter-spacing:.5px;">KNIGHT LAW GROUP</span></td></tr>
<tr><td style="padding:32px;color:#333333;font-size:16px;line-height:1.6;">
<p style="margin:0 0 16px;">Hola {{contact.first_name}},</p>
<p style="margin:0 0 16px;">Hemos intentado comunicarnos con usted estos últimos días y aún no lo logramos. No queremos que pierda la oportunidad de que revisemos su situación.</p>
<p style="margin:0 0 24px;">Solo toma una llamada breve. Lo intentaremos de nuevo, o comuníquese cuando guste al número de abajo.</p>
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 24px;"><tr><td style="border-radius:6px;background:#0b6b3a;"><a href="tel:+13105522250" style="display:inline-block;padding:14px 28px;color:#ffffff;font-size:16px;font-weight:bold;text-decoration:none;">Llámenos: (310) 552-2250</a></td></tr></table>
<p style="margin:0;">Cordialmente,<br><strong>Alice</strong><br>Knight Law Group</p>
</td></tr>
<tr><td style="padding:20px 32px;background:#f0f0f3;color:#888888;font-size:12px;line-height:1.5;">
<p style="margin:0 0 8px;">Knight Law Group &middot; Al servicio de clientes en toda California &middot; (310) 552-2250</p>
<p style="margin:0;">Recibe este mensaje porque nos contactó sobre un asunto de vehículo. <a href="{{unsubscribe_link}}" style="color:#888888;">Cancelar suscripción</a> o responda STOP a cualquier texto.</p>
</td></tr></table></td></tr></table></body></html>
```

**Email Recurrente (Día 4+) — Asunto: `Seguimos aquí para ayudarle`**
```html
<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
<span style="display:none!important;visibility:hidden;opacity:0;color:transparent;height:0;width:0;overflow:hidden;">Seguimos aquí para ayudarle cuando esté listo.</span>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:8px;overflow:hidden;">
<tr><td style="background:#0b2a4a;padding:20px 32px;"><span style="color:#ffffff;font-size:20px;font-weight:bold;letter-spacing:.5px;">KNIGHT LAW GROUP</span></td></tr>
<tr><td style="padding:32px;color:#333333;font-size:16px;line-height:1.6;">
<p style="margin:0 0 16px;">Hola {{contact.first_name}},</p>
<p style="margin:0 0 16px;">Seguimos aquí para cuando esté listo para hablar sobre su vehículo. Sin presión y sin compromiso — solo una breve conversación para ver cómo podemos ayudarle.</p>
<p style="margin:0 0 24px;">Seguiremos comunicándonos de vez en cuando, pero puede llamarnos cuando guste al número de abajo.</p>
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 24px;"><tr><td style="border-radius:6px;background:#0b6b3a;"><a href="tel:+13105522250" style="display:inline-block;padding:14px 28px;color:#ffffff;font-size:16px;font-weight:bold;text-decoration:none;">Llámenos: (310) 552-2250</a></td></tr></table>
<p style="margin:0;">Cordialmente,<br><strong>Alice</strong><br>Knight Law Group</p>
</td></tr>
<tr><td style="padding:20px 32px;background:#f0f0f3;color:#888888;font-size:12px;line-height:1.5;">
<p style="margin:0 0 8px;">Knight Law Group &middot; Al servicio de clientes en toda California &middot; (310) 552-2250</p>
<p style="margin:0;">Recibe este mensaje porque nos contactó sobre un asunto de vehículo. <a href="{{unsubscribe_link}}" style="color:#888888;">Cancelar suscripción</a> o responda STOP a cualquier texto.</p>
</td></tr></table></td></tr></table></body></html>
```

---

## 4. Setup checklist
- [ ] Confirm Retell post-call webhook writes `Lead Status` **and** `Lead Language` to GHL custom fields.
- [ ] Set sub-account timezone to **America/Los_Angeles**.
- [ ] Turn **Stop on Response = ON** in Workflow Settings.
- [ ] Add your **Retell API key** + published **agent_id** to the Custom Webhook step.
- [ ] Verify SMS sender number is A2P-registered (so the 6 daily-ish texts deliver).
- [ ] Set a default value ("there" / "") for `{{contact.first_name}}` so it never renders blank.
- [ ] (Optional) add a hard cap (e.g., 14 days) so the every-other-day loop isn't truly infinite.
