import base64

from odoo import http
from odoo.http import request


class InterntionWebsiteForms(http.Controller):
    @staticmethod
    def _source_detail(post):
        values = [post.get(key) for key in ("utm_source", "utm_medium", "utm_campaign", "source_page")]
        return " / ".join(value for value in values if value)

    @staticmethod
    def _campaign(post):
        name = (post.get("utm_campaign") or "").strip()
        if not name:
            return False
        return request.env["utm.campaign"].sudo().search([("name", "=", name)], limit=1).id or False

    @staticmethod
    def _team_lead(team_xmlid):
        team = request.env.ref(team_xmlid).sudo()
        user = team.user_id or request.env.user
        return team, user

    @http.route("/interntion/apply", type="http", auth="public", methods=["POST"], csrf=True)
    def student_application(self, **post):
        team, user = self._team_lead("interntion_crm.crm_team_interntion")
        vals = {
            "name": "Student application: %s" % (post.get("name") or "Unknown student"),
            "partner_name": post.get("name"),
            "email_from": post.get("email"),
            "phone": post.get("phone"),
            "description": post.get("message") or "Application submitted through the student application form.",
            "team_id": team.id,
            "user_id": user.id,
            "type": "opportunity",
            "interntion_side": "student",
            "x_course_stream": post.get("course_stream"),
            "lead_source_detail": self._source_detail(post),
            "campaign_id": self._campaign(post),
        }
        lead = request.env["crm.lead"].sudo().create(vals)
        upload = request.httprequest.files.get("cv")
        if upload:
            content = upload.read()
            if len(content) > 5 * 1024 * 1024:
                return request.redirect("/?application_error=cv_too_large")
            lead.sudo().write({
                "x_cv_file": base64.b64encode(content),
                "x_cv_filename": upload.filename,
            })
        return request.redirect("/?application_submitted=1")

    @http.route("/interntion/partner-enquiry", type="http", auth="public", methods=["POST"], csrf=True)
    def partner_enquiry(self, **post):
        team, user = self._team_lead("interntion_crm.team_corporate_partnerships")
        name = "%s %s" % (post.get("first_name", ""), post.get("last_name", ""))
        request.env["crm.lead"].sudo().create({
            "name": "Partnership enquiry: %s" % (post.get("company_name") or name),
            "partner_name": post.get("company_name") or name,
            "email_from": post.get("email"),
            "phone": post.get("phone"),
            "description": post.get("message") or "Corporate partnership enquiry.",
            "team_id": team.id,
            "user_id": user.id,
            "type": "opportunity",
            "interntion_side": "partner",
            "company_industry_sector": post.get("industry_sector"),
            "partnership_interest_type": post.get("partnership_interest"),
            "partner_country": post.get("partner_country", "uk"),
            "lead_source_detail": self._source_detail(post),
            "campaign_id": self._campaign(post),
        })
        return request.redirect("/partner-with-us.html?submitted=1")

    @http.route("/interntion/express-interest", type="http", auth="public", methods=["POST"], csrf=True)
    def express_interest(self, **post):
        team, user = self._team_lead("interntion_crm.crm_team_interntion")
        company = post.get("partner_company")
        request.env["crm.lead"].sudo().create({
            "name": "Express interest: %s" % (post.get("name") or "Student"),
            "partner_name": post.get("name"),
            "email_from": post.get("email"),
            "phone": post.get("phone"),
            "description": "Interested in partner/company: %s" % (company or post.get("industry")),
            "team_id": team.id,
            "user_id": user.id,
            "type": "opportunity",
            "interntion_side": "student",
            "lead_source_detail": self._source_detail(post),
            "campaign_id": self._campaign(post),
        })
        return request.redirect("/partner-with-us.html?interest_submitted=1")

    @http.route("/interntion/call-me", type="http", auth="public", methods=["POST"], csrf=True)
    def call_me(self, **post):
        phone = (post.get("phone") or "").strip()
        if not phone or post.get("consent") not in ("1", "on", "true", True):
            return request.redirect("/?call_error=phone_and_consent_required")
        lead = request.env["crm.lead"].sudo().search([("phone", "=", phone)], limit=1)
        if not lead:
            team, user = self._team_lead("interntion_crm.crm_team_interntion")
            lead = request.env["crm.lead"].sudo().create({
                "name": "Call me request: %s" % (post.get("name") or phone),
                "partner_name": post.get("name") or "Website caller",
                "email_from": post.get("email"),
                "phone": phone,
                "team_id": team.id,
                "user_id": user.id,
                "type": "opportunity",
                "interntion_side": "student",
                "description": "Requested a callback from the Interntion website.",
            })
        lead.sudo().write({"ai_call_consent": True, "ai_call_status": "requested"})
        request.env["interntion.call.log"].sudo().create({
            "lead_id": lead.id,
            "call_direction": "out",
            "call_status": "requested",
            "outcome": "Callback Requested",
            "consent_captured": True,
            "callback_requested": True,
            "notes": "Website callback request received.",
        })
        return request.redirect("/?call_requested=1")

    @http.route("/interntion/voice/webhook", type="jsonrpc", auth="public", methods=["POST"], csrf=False)
    def voice_webhook(self, **payload):
        provider_call_id = payload.get("provider_call_id") or payload.get("call_id")
        agent = request.env["interntion.ai.agent"].sudo().search([("active", "=", True)], limit=1)
        if not agent or not provider_call_id or (agent.webhook_secret and payload.get("secret") != agent.webhook_secret):
            return {"ok": False, "error": "unauthorized"}
        call = request.env["interntion.call.log"].sudo().process_provider_webhook(payload)
        return {"ok": bool(call), "call_log_id": call.id if call else False}
