from odoo import fields, models, api
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
    x_mock_interview_done = fields.Boolean(string="Mock Interview Done")
    x_certificate_issued = fields.Boolean(string="Certificate Issued")

    @api.onchange("x_internship_id")
    def _onchange_x_internship_id(self):
        for rec in self:
            if rec.x_internship_id:
                rec.x_industry_sector = rec.x_internship_id.sector
                rec.x_is_paid_internship = rec.x_internship_id.is_paid
