"""
Aria's notification e-mails go out through Resend (https://resend.com/docs/api-reference/emails/send-email)
from the notifications.aiemply.com domain, with engineering on CC (Ubaid, 2026-10-04).

One place for the sender, the CC and the n8n node shape, shared by
_patch_resend_email.py (Wix backends) and outbound/_build_post_call_callback_workflow.py.
"""

RESEND_URL = "https://api.resend.com/emails"
FROM = "Aria AI Employee <aria@notifications.aiemply.com>"
ENGINEERING = "engineering@aiemply.com"
SPA = "sagewillowspa@gmail.com"
# n8n "Bearer Auth" credential holding the Resend API key (token = re_...).
CRED_NAME = "Resend - notifications.aiemply.com"


def body_expr(fields: str) -> str:
    """n8n expression for the JSON body; `fields` is the rest of a JS object literal."""
    return "={{ JSON.stringify({ from: " + repr(FROM) + ", " + fields + " }) }}"


def resend_node(id_, name, pos, fields, idempotency, cred_id, on_error):
    """HTTP Request node: POST /emails. `idempotency` is an n8n expression ("=...")."""
    return {
        "id": id_, "name": name, "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2,
        "position": pos,
        "parameters": {
            "method": "POST",
            "url": RESEND_URL,
            "authentication": "genericCredentialType",
            "genericAuthType": "httpBearerAuth",
            "sendHeaders": True,
            "headerParameters": {"parameters": [{"name": "Idempotency-Key", "value": idempotency}]},
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": body_expr(fields),
            "options": {"timeout": 30000},
        },
        "credentials": {"httpBearerAuth": {"id": cred_id, "name": CRED_NAME}},
        "retryOnFail": True, "maxTries": 3, "waitBetweenTries": 2000,
        "onError": on_error,
    }
