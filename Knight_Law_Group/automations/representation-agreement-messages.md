# Representation Agreement — SMS + Email Templates (Retainer flow)

> Sent when a lead reaches **Retainer** (representation agreement offered). Signing is now via **DocuSeal** (DocuSign retired).
> Send the **matching language** by `lead_language`. `{{contact.first_name}}` is the GHL merge field — set a fallback (e.g. "there" / "hola") for missing names.

**Signing links (DocuSeal):**
- English → `https://sign.knightlaw.com/d/JU6yZ9Utb5qpG3`
- Spanish → `https://sign.knightlaw.com/d/ES92PraGmTb2ym`

---

## ENGLISH

### SMS
```
Knight Law Group: Hi {{contact.first_name}}, thanks for speaking with us. Please review and sign your representation agreement here: https://sign.knightlaw.com/d/JU6yZ9Utb5qpG3

Once it's signed, our Client Services team will reach out with the next steps. Questions? Call (310) 552-2250. Reply STOP to opt out.
```

### Email — Subject
```
Your Representation Agreement — Knight Law Group
```

### Email — Body
```
Hi {{contact.first_name}},

Thank you for speaking with us about your vehicle. We're ready to move forward with your California Lemon Law case.

The next step is to review and sign your representation agreement:

👉 Review & sign your agreement: https://sign.knightlaw.com/d/JU6yZ9Utb5qpG3

Once your agreement is signed, our Client Services team will reach out to walk you through the next steps and help you gather the documents we need to move your case forward. The sooner we receive everything, the sooner your case can be filed.

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
Knight Law Group: Hola {{contact.first_name}}, gracias por hablar con nosotros. Por favor revise y firme su acuerdo de representación aquí: https://sign.knightlaw.com/d/ES92PraGmTb2ym

Una vez firmado, nuestro equipo de Servicios al Cliente se comunicará con usted con los siguientes pasos. ¿Preguntas? Llame al (310) 552-2250. Responda STOP para no recibir mensajes.
```

### Email — Subject
```
Su Acuerdo de Representación — Knight Law Group
```

### Email — Body
```
Hola {{contact.first_name}},

Gracias por hablar con nosotros sobre su vehículo. Estamos listos para avanzar con su caso bajo la Ley Limón de California.

El siguiente paso es revisar y firmar su acuerdo de representación:

👉 Revise y firme su acuerdo: https://sign.knightlaw.com/d/ES92PraGmTb2ym

Una vez firmado su acuerdo, nuestro equipo de Servicios al Cliente se comunicará con usted para guiarle en los siguientes pasos y ayudarle a reunir los documentos que necesitamos para avanzar con su caso. Entre más pronto los recibamos, más pronto podremos presentar su caso.

Si tiene alguna pregunta, responda a este correo o llámenos al (310) 552-2250, de lunes a viernes, de 8 AM a 8 PM, hora del Pacífico.

Gracias por confiar en Knight Law Group.

Un cordial saludo,
Servicios al Cliente
Knight Law Group
(310) 552-2250
```

---

## Notes
- **Language routing:** send the EN set to English leads and the ES set to Spanish leads (branch on `lead_language`). The two DocuSeal links are language-specific.
- **Email button:** if your email step supports a button, use label **"Review & Sign Agreement"** / **"Revisar y Firmar Acuerdo"** pointing at the matching link, and you can drop the inline `👉` line.
- **Opt-out:** SMS includes "Reply STOP…" for carrier compliance; remove if your platform appends it automatically.
- **Merge field:** shown as GHL `{{contact.first_name}}` — swap to your platform's syntax if different.
