# send_agreement Workflow — SMS + Email Bodies

Fires when the Retell **`send_agreement`** tool posts to the GHL inbound webhook (`…/7a7c8e71-…`). Payload carries `full_name`, `phone`, `email`, `lead_language`. The workflow branches on language and delivers the DocuSeal signing link by SMS + email. **One shared body used by every caller of `send_agreement`** — the intake/immediate agent sending the link live on the same call, and the retainer agents (initial send or resend). Wording is deliberately general so it never sounds like the conversation just ended.

**GHL setup**
- **Trigger:** Inbound Webhook. Associate it to the contact (match by `phone` / `email` from the payload) so `{{contact.first_name}}` and contact fields resolve. If you can't match, swap `{{contact.first_name}}` → the payload field `{{inboundWebhookRequest.full_name}}`.
- **Language split:** If/Else on `{{inboundWebhookRequest.lead_language}}` = `English` / `Spanish`.
- **Link:** `{{custom_values.retainer_link_en}}` / `_es` (same custom values as the cadence SMS snippets).
- **Phone shown:** (310) 552-2250 (Client Services) — matches the existing agreement template. *If you'd rather keep the whole retainer flow on the Alice line, swap to (213) 205-3651 (the cadence uses that).*

---

## ENGLISH

### SMS
```
Knight Law Group: Hi {{contact.first_name}}, here's your representation agreement to review and sign: {{custom_values.retainer_link_en}}

Nothing on your case starts until it's signed. Once it is, our Client Services team follows up with the next steps. Questions? Reply here or call (310) 552-2250. Reply STOP to opt out.
```

### Email — Subject
```
Your Representation Agreement — Knight Law Group
```

### Email — Body
```
Hi {{contact.first_name}},

Here is your representation agreement for your California Lemon Law case. The next step is to review and sign it:

Review & sign your agreement: {{custom_values.retainer_link_en}}

Nothing on your case moves forward — including the buyback request to the manufacturer — until the agreement is signed. Once it's signed, our Client Services team will reach out to walk you through the next steps and help you gather the documents we need. The sooner we receive everything, the sooner your case can be filed.

If you have any questions, just reply to this email or call us at (310) 552-2250, Monday–Friday, 8 AM–8 PM Pacific.

Thank you for trusting Knight Law Group.

Warm regards,
Client Services
Knight Law Group
(310) 552-2250
```

---

## SPANISH

### SMS
```
Knight Law Group: Hola {{contact.first_name}}, aquí está su acuerdo de representación para revisar y firmar: {{custom_values.retainer_link_es}}

Nada en su caso comienza hasta que esté firmado. Una vez firmado, nuestro equipo de Servicios al Cliente le dará seguimiento con los siguientes pasos. ¿Preguntas? Responda aquí o llame al (310) 552-2250. Responda STOP para no recibir mensajes.
```

### Email — Subject
```
Su Acuerdo de Representación — Knight Law Group
```

### Email — Body
```
Hola {{contact.first_name}},

Aquí está su acuerdo de representación para su caso bajo la Ley Limón de California. El siguiente paso es revisarlo y firmarlo:

Revise y firme su acuerdo: {{custom_values.retainer_link_es}}

Nada en su caso avanza —incluida la solicitud de recompra al fabricante— hasta que el acuerdo esté firmado. Una vez firmado, nuestro equipo de Servicios al Cliente se comunicará con usted para guiarle en los siguientes pasos y ayudarle a reunir los documentos que necesitamos. Entre más pronto los recibamos, más pronto podremos presentar su caso.

Si tiene alguna pregunta, responda a este correo o llámenos al (310) 552-2250, de lunes a viernes, de 8 AM a 8 PM, hora del Pacífico.

Gracias por confiar en Knight Law Group.

Un cordial saludo,
Servicios al Cliente
Knight Law Group
(310) 552-2250
```

---

## Notes
- **Email button:** if your email step supports a button, use **"Review & Sign Agreement"** / **"Revisar y Firmar Acuerdo"** pointing at the matching link, and drop the inline link line.
- **Opt-out:** SMS keeps "Reply STOP…" for first-contact compliance — remove if GHL/your carrier auto-appends it.
- **Per-contact links:** these use the account-level `{{custom_values.retainer_link_en/es}}`. If DocuSeal issues a **unique link per lead**, replace with the contact custom field that holds it (e.g. `{{contact.retainer_link}}`).
- Content mirrors `representation-agreement-messages.md`; this version updates the link to the custom-value convention.
