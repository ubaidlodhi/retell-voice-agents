# Retainer Follow-Up — Outbound Call Payloads (48-hour cadence)

Retell `create-phone-call` bodies for the retainer **outbound** cadence (Flow B). One call per cadence CALL touch (Call 1–5), each carrying its own `voicemail_script` so the agent leaves the right message on no-answer. English + Spanish variant per call — branch on `lead_language` in GHL (or pull the language-specific values from custom values).

**Endpoint:** `POST https://api.retellai.com/v2/create-phone-call` · header `Authorization: Bearer <RETELL_KEY>` · `Content-Type: application/json`

**Constant across every call**
- `from_number`: `+12132053651`
- `override_agent_id`: `agent_83f8b296e4652030d15a3417e6` (Alice Retainer Outbound)
- `to_number`: `{{number_formatter.1.result}}` (your formatter, same as intake)

**Dynamic variables** (mirrors your intake payload, plus retainer fields)
- `Name` / `first_name` / `Phone` / `Email` — GHL merge fields.
- `contact_id` — `{{contact.id}}`, so the post-call automation can match the contact (per our earlier setup).
- `lead_language` — `English` / `Spanish` (agent stays in this language).
- `call_number` — `1`–`5`; the agent stays light early and goes low-pressure/final on call 5.
- `greeting` — identity check, said verbatim.
- `voicemail_script` — left automatically if the call hits voicemail (VM 1–5 from spec §2.1).

**Cadence (calls only; anchor to T0 = agreement sent; 8 AM–9 PM PT only)**

| Call | Time from send | On no answer |
|---|---|---|
| Call 1 | +2 hrs | Voicemail 1 → continue |
| Call 2 | +6 hrs | Voicemail 2 → continue |
| Call 3 | Day 2 AM (~+20 hrs) | Voicemail 3 → continue |
| Call 4 | Day 2 PM (~+28 hrs) | Voicemail 4 → continue |
| Call 5 | Day 3 AM (~+44 hrs), final | Voicemail 5 → hand to intake |

> **Setup note:** confirm **voicemail detection is enabled on Agent B** — the `voicemail_option` is wired to `{{voicemail_script}}`, but detection must be on for the message to actually be left.

---

## CALL 1 — +2 hrs

**English**
```json
{
  "from_number": "+12132053651",
  "to_number": "{{number_formatter.1.result}}",
  "override_agent_id": "agent_83f8b296e4652030d15a3417e6",
  "retell_llm_dynamic_variables": {
    "Name": "{{contact.name}}",
    "first_name": "{{contact.first_name}}",
    "Phone": "{{number_formatter.1.result}}",
    "Email": "{{contact.email}}",
    "contact_id": "{{contact.id}}",
    "lead_language": "English",
    "call_number": "1",
    "greeting": "Hi, is this {{contact.first_name}}?",
    "voicemail_script": "Hi {{contact.first_name}}, this is Alice calling from Knight Law Group about your vehicle. I just sent over your representation agreement and texted you the link, and I wanted to make sure it reached you. If you have any questions at all, call us back at (213) 205-3651. Thanks!"
  }
}
```

**Spanish**
```json
{
  "from_number": "+12132053651",
  "to_number": "{{number_formatter.1.result}}",
  "override_agent_id": "agent_83f8b296e4652030d15a3417e6",
  "retell_llm_dynamic_variables": {
    "Name": "{{contact.name}}",
    "first_name": "{{contact.first_name}}",
    "Phone": "{{number_formatter.1.result}}",
    "Email": "{{contact.email}}",
    "contact_id": "{{contact.id}}",
    "lead_language": "Spanish",
    "call_number": "1",
    "greeting": "Hola, ¿hablo con {{contact.first_name}}?",
    "voicemail_script": "Hola {{contact.first_name}}, le habla Alice de Knight Law Group sobre su vehículo. Acabo de enviarle su acuerdo de representación y le mandé el enlace por mensaje de texto; quería asegurarme de que le llegó. Si tiene cualquier pregunta, llámenos al (213) 205-3651. ¡Gracias!"
  }
}
```

---

## CALL 2 — +6 hrs

**English**
```json
{
  "from_number": "+12132053651",
  "to_number": "{{number_formatter.1.result}}",
  "override_agent_id": "agent_83f8b296e4652030d15a3417e6",
  "retell_llm_dynamic_variables": {
    "Name": "{{contact.name}}",
    "first_name": "{{contact.first_name}}",
    "Phone": "{{number_formatter.1.result}}",
    "Email": "{{contact.email}}",
    "contact_id": "{{contact.id}}",
    "lead_language": "English",
    "call_number": "2",
    "greeting": "Hi, is this {{contact.first_name}}?",
    "voicemail_script": "Hi {{contact.first_name}}, Alice again at Knight Law Group. Just circling back on your vehicle — the agreement link is in your texts whenever you have a minute. Any questions before you sign, I'm right here: (213) 205-3651. Talk soon."
  }
}
```

**Spanish**
```json
{
  "from_number": "+12132053651",
  "to_number": "{{number_formatter.1.result}}",
  "override_agent_id": "agent_83f8b296e4652030d15a3417e6",
  "retell_llm_dynamic_variables": {
    "Name": "{{contact.name}}",
    "first_name": "{{contact.first_name}}",
    "Phone": "{{number_formatter.1.result}}",
    "Email": "{{contact.email}}",
    "contact_id": "{{contact.id}}",
    "lead_language": "Spanish",
    "call_number": "2",
    "greeting": "Hola, ¿hablo con {{contact.first_name}}?",
    "voicemail_script": "Hola {{contact.first_name}}, soy Alice de Knight Law Group otra vez. Solo doy seguimiento sobre su vehículo: el enlace del acuerdo está en sus mensajes cuando tenga un minuto. Si tiene alguna pregunta antes de firmar, aquí estoy: (213) 205-3651. Hablamos pronto."
  }
}
```

---

## CALL 3 — Day 2 AM (~+20 hrs)

**English**
```json
{
  "from_number": "+12132053651",
  "to_number": "{{number_formatter.1.result}}",
  "override_agent_id": "agent_83f8b296e4652030d15a3417e6",
  "retell_llm_dynamic_variables": {
    "Name": "{{contact.name}}",
    "first_name": "{{contact.first_name}}",
    "Phone": "{{number_formatter.1.result}}",
    "Email": "{{contact.email}}",
    "contact_id": "{{contact.id}}",
    "lead_language": "English",
    "call_number": "3",
    "greeting": "Hi, is this {{contact.first_name}}?",
    "voicemail_script": "Hi {{contact.first_name}}, it's Alice at Knight Law Group again. I still haven't received your signed agreement, and I don't want your case sitting still — everything on our end is ready to go the moment it's back. The link is in your texts, or I'm happy to walk you through it over the phone. Give me a call at (213) 205-3651. Talk soon."
  }
}
```

**Spanish**
```json
{
  "from_number": "+12132053651",
  "to_number": "{{number_formatter.1.result}}",
  "override_agent_id": "agent_83f8b296e4652030d15a3417e6",
  "retell_llm_dynamic_variables": {
    "Name": "{{contact.name}}",
    "first_name": "{{contact.first_name}}",
    "Phone": "{{number_formatter.1.result}}",
    "Email": "{{contact.email}}",
    "contact_id": "{{contact.id}}",
    "lead_language": "Spanish",
    "call_number": "3",
    "greeting": "Hola, ¿hablo con {{contact.first_name}}?",
    "voicemail_script": "Hola {{contact.first_name}}, soy Alice de Knight Law Group nuevamente. Todavía no he recibido su acuerdo firmado y no quiero que su caso se quede detenido; todo de nuestro lado está listo para avanzar en cuanto lo recibamos. El enlace está en sus mensajes, o con gusto le explico todo por teléfono. Llámeme al (213) 205-3651. Hablamos pronto."
  }
}
```

---

## CALL 4 — Day 2 PM (~+28 hrs)

**English**
```json
{
  "from_number": "+12132053651",
  "to_number": "{{number_formatter.1.result}}",
  "override_agent_id": "agent_83f8b296e4652030d15a3417e6",
  "retell_llm_dynamic_variables": {
    "Name": "{{contact.name}}",
    "first_name": "{{contact.first_name}}",
    "Phone": "{{number_formatter.1.result}}",
    "Email": "{{contact.email}}",
    "contact_id": "{{contact.id}}",
    "lead_language": "English",
    "call_number": "4",
    "greeting": "Hi, is this {{contact.first_name}}?",
    "voicemail_script": "Hi {{contact.first_name}}, Alice from Knight Law Group. I keep just missing you on your vehicle. Most of what people ask about takes about two minutes to clear up on a quick call — so if anything's holding you up, let's knock it out together. Reach me at (213) 205-3651, or sign through the link in your texts. Thanks!"
  }
}
```

**Spanish**
```json
{
  "from_number": "+12132053651",
  "to_number": "{{number_formatter.1.result}}",
  "override_agent_id": "agent_83f8b296e4652030d15a3417e6",
  "retell_llm_dynamic_variables": {
    "Name": "{{contact.name}}",
    "first_name": "{{contact.first_name}}",
    "Phone": "{{number_formatter.1.result}}",
    "Email": "{{contact.email}}",
    "contact_id": "{{contact.id}}",
    "lead_language": "Spanish",
    "call_number": "4",
    "greeting": "Hola, ¿hablo con {{contact.first_name}}?",
    "voicemail_script": "Hola {{contact.first_name}}, soy Alice de Knight Law Group. Sigo sin poder localizarle sobre su vehículo. La mayoría de las dudas se aclaran en unos dos minutos por teléfono, así que si algo le detiene, resolvámoslo juntos. Comuníquese conmigo al (213) 205-3651, o firme con el enlace que está en sus mensajes. ¡Gracias!"
  }
}
```

---

## CALL 5 — Day 3 AM (~+44 hrs) · FINAL

**English**
```json
{
  "from_number": "+12132053651",
  "to_number": "{{number_formatter.1.result}}",
  "override_agent_id": "agent_83f8b296e4652030d15a3417e6",
  "retell_llm_dynamic_variables": {
    "Name": "{{contact.name}}",
    "first_name": "{{contact.first_name}}",
    "Phone": "{{number_formatter.1.result}}",
    "Email": "{{contact.email}}",
    "contact_id": "{{contact.id}}",
    "lead_language": "English",
    "call_number": "5",
    "greeting": "Hi, is this {{contact.first_name}}?",
    "voicemail_script": "Hi {{contact.first_name}}, Alice from Knight Law Group. I've tried you a few times because I want to make sure nothing in the agreement is giving you pause — that's really common, and it's usually a two-minute conversation to clear up. Call me back at (213) 205-3651 — that's (213) 205-3651 — or just sign through the link in your texts and we'll get straight to work on your vehicle. After today, someone from our team will follow up with you directly. Looking forward to it."
  }
}
```

**Spanish**
```json
{
  "from_number": "+12132053651",
  "to_number": "{{number_formatter.1.result}}",
  "override_agent_id": "agent_83f8b296e4652030d15a3417e6",
  "retell_llm_dynamic_variables": {
    "Name": "{{contact.name}}",
    "first_name": "{{contact.first_name}}",
    "Phone": "{{number_formatter.1.result}}",
    "Email": "{{contact.email}}",
    "contact_id": "{{contact.id}}",
    "lead_language": "Spanish",
    "call_number": "5",
    "greeting": "Hola, ¿hablo con {{contact.first_name}}?",
    "voicemail_script": "Hola {{contact.first_name}}, soy Alice de Knight Law Group. Le he llamado varias veces porque quiero asegurarme de que nada en el acuerdo le esté causando dudas; eso es muy común y normalmente se aclara en una conversación de dos minutos. Llámeme al (213) 205-3651 — es el (213) 205-3651 — o simplemente firme con el enlace de sus mensajes y comenzaremos de inmediato con su vehículo. Después de hoy, alguien de nuestro equipo se comunicará con usted directamente. Quedo al pendiente."
  }
}
```
