from odoo import fields, models

SERVICE_CODE_SELECTION = [
    ("internship_opportunities", "Internship Opportunities"),
    ("project_assistance", "Project Assistance"),
    ("work_experience_support", "Work Experience Support"),
    ("cv_job_preparation", "CV & Job Preparation"),
]


class InterntionService(models.Model):
    _name = "interntion.service"
    _description = "Interntion Core Service"
    _order = "sequence, id"

    name = fields.Char(required=True)
    code = fields.Selection(SERVICE_CODE_SELECTION, required=True)
    description = fields.Text()
    icon = fields.Char(string="Icon (Font Awesome class)", default="fa-briefcase")
    sequence = fields.Integer(default=10)
    is_new = fields.Boolean(string="New Badge")
    url = fields.Char(string="Reference URL")
    active = fields.Boolean(default=True)
