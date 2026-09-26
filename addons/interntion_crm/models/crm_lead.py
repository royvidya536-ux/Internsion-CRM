import base64
import re
from datetime import datetime

from odoo import fields, models, api
from odoo.exceptions import UserError
from .employer import SECTOR_SELECTION

APPLICATION_SOURCE_SELECTION = [
    ("website", "Website Application Form"),
    ("referral", "Student Referral"),
    ("partner_university", "Partner University"),
    ("career_fair", "Career Fair"),
    ("social_media", "Social Media"),
    ("other", "Other"),
]


class CrmLead(models.Model):
    """Extends the standard CRM pipeline to manage Interntion's
    student -> internship placement journey end to end."""

    _inherit = "crm.lead"

    x_course_stream = fields.Char(string="Course / Stream", help="e.g. B.Tech CSE, MBA Marketing")
    x_industry_sector = fields.Selection(SECTOR_SELECTION, string="Preferred Sector")
    x_application_source = fields.Selection(
        APPLICATION_SOURCE_SELECTION, string="Application Source", default="website"
    )

    x_internship_id = fields.Many2one("interntion.internship", string="Internship Opportunity")
    x_employer_id = fields.Many2one(
        "interntion.employer",
        string="Industry Partner",
        related="x_internship_id.employer_id",
        store=True,
        readonly=False,
    )
    x_mentor_id = fields.Many2one("interntion.mentor", string="Assigned Mentor")

    x_is_paid_internship = fields.Boolean(string="Paid Internship", default=True)
    x_cv_file = fields.Binary(string="CV / Resume", attachment=True)
    x_cv_filename = fields.Char(string="CV Filename")

    x_cv_reviewed = fields.Boolean(string="CV Reviewed")
    resume_summary = fields.Text(string="Resume summary", copy=False)
    resume_skills = fields.Char(string="Extracted skills", copy=False)
    resume_education = fields.Char(string="Education", copy=False)
    resume_experience = fields.Char(string="Experience", copy=False)
    resume_parsed_at = fields.Datetime(string="Resume parsed at", copy=False)
    resume_match_score = fields.Integer(string="Resume match score (%)", copy=False)
    x_mock_interview_done = fields.Boolean(string="Mock Interview Done")
    x_certificate_issued = fields.Boolean(string="Certificate Issued")
    call_log_ids = fields.One2many("interntion.call.log", "lead_id", string="Call Logs")
    call_count = fields.Integer(compute="_compute_call_metrics", string="Call count")
    last_call_date = fields.Datetime(compute="_compute_call_metrics", string="Last call date")
    ai_call_status = fields.Selection([
        ("not_requested", "Not requested"),
        ("requested", "Call requested"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ], default="not_requested", copy=False)
    ai_call_consent = fields.Boolean(string="Consent to AI call", copy=False)
    ai_call_agent_id = fields.Many2one("interntion.ai.agent", string="Calling agent", copy=False)

    @api.depends("call_log_ids", "call_log_ids.call_datetime")
    def _compute_call_metrics(self):
        for rec in self:
            rec.call_count = len(rec.call_log_ids)
            rec.last_call_date = rec.call_log_ids and max(rec.call_log_ids.mapped("call_datetime") or [False]) or False

    def action_log_call(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "interntion.call.log.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_lead_id": self.id},
        }

    def action_view_call_logs(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Calls",
            "res_model": "interntion.call.log",
            "view_mode": "tree,form",
            "domain": [("lead_id", "=", self.id)],
            "context": {"default_lead_id": self.id},
        }

    def action_find_matching_campaigns(self):
        self.ensure_one()
        matches = self.env["interntion.lead.match"].create_matches_for_lead(self.id)
        campaigns = self.env["utm.campaign"].search([
            ("target_sector", "=", self.x_industry_sector),
        ])
        return {
            "type": "ir.actions.act_window",
            "name": "Matching Campaigns",
            "res_model": "utm.campaign",
            "view_mode": "list,form",
            "domain": [("id", "in", campaigns.ids)],
            "context": {"default_target_sector": self.x_industry_sector},
        }

    @api.onchange("x_internship_id")
    def _onchange_x_internship_id(self):
        for rec in self:
            if rec.x_internship_id:
                rec.x_industry_sector = rec.x_internship_id.sector
                rec.x_is_paid_internship = rec.x_internship_id.is_paid

    def action_parse_resume(self):
        self.ensure_one()
        if not self.x_cv_file:
            raise UserError("Upload a CV or resume before parsing it.")
        raw = base64.b64decode(self.x_cv_file)
        text = self._resume_text(raw)
        if not text.strip():
            raise UserError("No readable text was found in this resume. Upload a text-based PDF or DOC export.")
        email = re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", text)
        phone = re.search(r"(?:\+?\d[\d ()-]{7,}\d)", text)
        skills = self._section(text, ("skills", "technical skills", "skills & tools"))
        education = self._section(text, ("education", "academic background"))
        experience = self._section(text, ("experience", "work experience", "employment"))
        values = {
            "resume_summary": " ".join(text.split())[:2000],
            "resume_skills": skills[:500] or False,
            "resume_education": education[:500] or False,
            "resume_experience": experience[:500] or False,
            "resume_parsed_at": datetime.utcnow(),
            "resume_match_score": self._match_score(text),
        }
        if email and not self.email_from:
            values["email_from"] = email.group(0)
        if phone and not self.phone:
            values["phone"] = phone.group(0).strip()
        self.write(values)
        return {"type": "ir.actions.client", "tag": "display_notification", "params": {
            "title": "Resume parsed",
            "message": "Profile fields and a transparent match score were updated.",
            "type": "success",
            "sticky": False,
        }}

    def action_request_ai_call(self):
        self.ensure_one()
        if not self.ai_call_consent:
            raise UserError("Record the lead's consent before requesting an AI call.")
        agent = self.env["interntion.ai.agent"].search([("active", "=", True)], limit=1)
        if not agent:
            raise UserError("Configure an active calling agent under Interntion CRM > AI Calling before using this action.")
        try:
            agent.call_lead(self)
        except Exception:
            self.write({"ai_call_status": "failed", "ai_call_agent_id": agent.id})
            raise
        return {"type": "ir.actions.client", "tag": "display_notification", "params": {
            "title": "Call requested", "message": "The external calling agent accepted this lead.",
            "type": "success", "sticky": False,
        }}

    @staticmethod
    def _resume_text(raw):
        if raw.startswith(b"%PDF"):
            try:
                from pypdf import PdfReader
                import io
                return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(raw)).pages)
            except ImportError as error:
                raise UserError("PDF parsing is unavailable. Rebuild the Docker image to install pypdf.") from error
            except Exception as error:
                raise UserError("This PDF could not be read. Upload a text-based PDF instead.") from error
        return raw.decode("utf-8", errors="ignore")

    @staticmethod
    def _section(text, headings):
        pattern = r"(?:%s)\s*:?\s*(.*?)(?=\n\s*[A-Z][A-Za-z &]{2,30}\s*:?[\n]|\Z)" % "|".join(re.escape(item) for item in headings)
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        return " ".join(match.group(1).split()) if match else ""

    def _match_score(self, text):
        keywords = set(re.findall(r"[a-zA-Z][a-zA-Z+#.-]{2,}", (self.x_course_stream or "").lower()))
        if not keywords:
            return 0
        haystack = text.lower()
        return round(100 * sum(keyword in haystack for keyword in keywords) / len(keywords))
