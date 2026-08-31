# Retainer Follow-Up — SMS Snippets (48-hour cadence)

Source copy: **Alice Retainer Build Requirements Aug. 2026 §2.2** (client-provided English). Spanish versions translated to match the formal *usted* register used in `representation-agreement-messages.md`.

Ready to paste into **GHL → Snippets**. Ten snippets total (5 English + 5 Spanish), one per SMS touch in the cadence.

**Conventions**
- **Name:** `Retainer Eng SMS One … Five` (English) · `Retainer Esp SMS One … Five` (Spanish). *(`Esp` = Español; say the word if you'd rather use `Spa`.)*
- **Name merge field:** `{{contact.first_name}}` — set a GHL fallback (e.g. "there" / "hola") for missing names.
- **Signing link:** language-specific DocuSeal links (same as `representation-agreement-messages.md`). If your DocuSeal links are **per-contact**, swap the URL for your GHL custom value (e.g. `{{ custom_values.retainer_link_en }}` / `_es`).
  - English → `https://sign.knightlaw.com/d/JU6yZ9Utb5qpG3`
  - Spanish → `https://sign.knightlaw.com/d/ES92PraGmTb2ym`
- **Callback number:** (213) 205-3651 (the Alice line, per the cadence spec).
- **Opt-out:** the client copy has no "Reply STOP" line; add per carrier/GHL compliance if your platform doesn't auto-append it.

**Cadence map** (timings anchor to T0 = agreement sent; all sends obey 8 AM–9 PM PT):

| Snippet | Cadence step | Time from send | Angle |
|---|---|---|---|
| `Retainer Eng/Esp SMS One`   | SMS 1 | +1 hr        | Delivery check + link |
| `Retainer Eng/Esp SMS Two`   | SMS 2 | +8 hrs       | Checking the link came through |
| `Retainer Eng/Esp SMS Three` | SMS 3 | Day 2 AM (~+22 hrs) | Case-stalled advocacy |
| `Retainer Eng/Esp SMS Four`  | SMS 4 | Day 2 eve (~+31 hrs) | Offer a call vs. self-serve |
| `Retainer Eng/Esp SMS Five`  | SMS 5 | Day 3 AM (~+46 hrs) | Final push + human follow-up |

---

## ENGLISH

### Retainer Eng SMS One
```
Hi {{contact.first_name}}, this is Alice from Knight Law Group. Just sent the representation agreement for your vehicle — here's the link: {{custom_values.retainer_link_en}} Nothing starts on your case, including the buyback request to the manufacturer, until it's signed. Questions before you sign? Reply here or call (213) 205-3651.
```

### Retainer Eng SMS Two
```
Hi {{contact.first_name}}, Alice again at Knight Law Group. Wanted to make sure the link came through for your vehicle: {{custom_values.retainer_link_en}} Happy to answer anything first: (213) 205-3651.
```

### Retainer Eng SMS Three
```
Hi {{contact.first_name}}, it's Alice from Knight Law Group. I don't want your case sitting still when we're ready to get started for you. Here's the link again: {{custom_values.retainer_link_en}} Any questions first, I'm right here: (213) 205-3651.
```

### Retainer Eng SMS Four
```
Hi {{contact.first_name}}, Alice at Knight Law Group. Most questions about the agreement take about two minutes to clear up — want me to give you a call, or would you rather knock it out now? Link: {{custom_values.retainer_link_en}} Or reach me at (213) 205-3651.
```

### Retainer Eng SMS Five
```
Hi {{contact.first_name}}, Alice from Knight Law Group again. I want to make sure nothing's holding you up on your vehicle, so someone from our team will follow up with you directly. If you'd like to get it done first, here's the link: {{custom_values.retainer_link_en}} We're looking forward to getting to work for you.
```

---

## SPANISH

### Retainer Esp SMS One
```
Hola {{contact.first_name}}, soy Alice de Knight Law Group. Acabo de enviarle el acuerdo de representación de su vehículo; aquí está el enlace: {{custom_values.retainer_link_es}} Nada comienza en su caso, incluida la solicitud de recompra al fabricante, hasta que esté firmado. ¿Preguntas antes de firmar? Responda aquí o llame al (213) 205-3651.
```

### Retainer Esp SMS Two
```
Hola {{contact.first_name}}, le escribe Alice de Knight Law Group otra vez. Quería asegurarme de que le llegó el enlace de su vehículo: {{custom_values.retainer_link_es}} Con gusto le respondo cualquier duda primero: (213) 205-3651.
```

### Retainer Esp SMS Three
```
Hola {{contact.first_name}}, soy Alice de Knight Law Group. No quiero que su caso se quede detenido cuando estamos listos para comenzar por usted. Aquí está el enlace de nuevo: {{custom_values.retainer_link_es}} Si tiene alguna pregunta primero, aquí estoy: (213) 205-3651.
```

### Retainer Esp SMS Four
```
Hola {{contact.first_name}}, soy Alice de Knight Law Group. La mayoría de las preguntas sobre el acuerdo se aclaran en unos dos minutos. ¿Quiere que le llame, o prefiere resolverlo ahora mismo? Enlace: {{custom_values.retainer_link_es}} O comuníquese conmigo al (213) 205-3651.
```

### Retainer Esp SMS Five
```
Hola {{contact.first_name}}, soy Alice de Knight Law Group nuevamente. Quiero asegurarme de que nada le esté deteniendo con su vehículo, así que alguien de nuestro equipo se comunicará con usted directamente. Si desea completarlo primero, aquí está el enlace: {{custom_values.retainer_link_es}} Esperamos poder comenzar a trabajar por usted.
```
