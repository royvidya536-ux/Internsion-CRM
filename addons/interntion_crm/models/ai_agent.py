import json
from urllib import request as url_request
from urllib.error import HTTPError, URLError

from odoo import fields, models
from odoo.exceptions import UserError


class InterntionAIAgent(models.Model):
    _name = "interntion.ai.agent"
    _description = "Interntion External Calling Agent"

    name = fields.Char(required=True, default="Primary calling agent")
    endpoint = fields.Char(string="Provider endpoint", required=True)
    api_key = fields.Char(string="API key", groups="base.group_system")
    active = fields.Boolean(default=True)
    provider = fields.Selection([
        ("generic", "Generic JSON provider"),
        ("twilio", "Twilio-compatible gateway"),
    ], default="generic", required=True)
    default_language = fields.Char(string="Default language", default="en-GB")
    webhook_secret = fields.Char(string="Webhook secret", groups="base.group_system", copy=False)

    def action_test_connection(self):
        self.ensure_one()
        try:
            response = self._send_request({"event": "connection_test"})
        except (HTTPError, URLError, OSError) as error:
            raise UserError("Calling provider connection failed: %s" % error) from error
        return {"type": "ir.actions.client", "tag": "display_notification", "params": {
            "title": "Calling provider connected",
            "message": "Provider replied with HTTP %s." % response,
            "type": "success",
            "sticky": False,
        }}

    def call_lead(self, lead):
        self.ensure_one()
        if not lead.phone:
            raise UserError("Add a phone number to the lead before starting an AI call.")
        payload = {
            "event": "lead_call_requested",
            "lead_id": lead.id,
            "name": lead.partner_name or lead.name,
            "phone": lead.phone,
            "email": lead.email_from or "",
            "side": lead.interntion_side or "student",
            "language": self.default_language or "en-GB",
            "consent_captured": bool(lead.ai_call_consent),
        }
        response_status = self._send_request(payload)
        self.env["interntion.call.log"].create({
            "lead_id": lead.id,
            "call_direction": "out",
            "call_status": "requested",
            "outcome": "Callback Requested",
            "provider_call_id": "pending-%s" % lead.id,
            "language": self.default_language or "en-GB",
            "consent_captured": bool(lead.ai_call_consent),
            "notes": "AI voice call requested from provider (HTTP %s)." % response_status,
        })
        lead.message_post(body="External calling agent accepted a call request for %s." % lead.phone)
        lead.write({"ai_call_status": "requested", "ai_call_agent_id": self.id})

    def _send_request(self, payload):
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = "Bearer %s" % self.api_key
        request = url_request.Request(
            self.endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
        )
        with url_request.urlopen(request, timeout=15) as response:
            response.read()
            return response.status
