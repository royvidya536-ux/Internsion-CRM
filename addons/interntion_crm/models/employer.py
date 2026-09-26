from odoo import fields, models, api

# Shared across Employer, Internship and CRM Lead (20+ sectors as advertised
# on interntion.co.uk: "Real paid internships across 20+ sectors").
SECTOR_SELECTION = [
    ("technology", "Technology / Software"),
    ("finance", "Finance & Accounting"),
    ("marketing", "Marketing & Digital"),
    ("healthcare", "Healthcare"),
    ("engineering", "Engineering"),
    ("human_resources", "Human Resources"),
    ("legal", "Legal"),
    ("consulting", "Consulting"),
    ("media", "Media & Communications"),
    ("retail", "Retail & E-commerce"),
    ("hospitality", "Hospitality & Tourism"),
    ("education", "Education"),
    ("non_profit", "Non-Profit / NGO"),
    ("real_estate", "Real Estate"),
    ("manufacturing", "Manufacturing"),
    ("logistics", "Logistics & Supply Chain"),
    ("data_science", "Data Science & Analytics"),
    ("design", "Design & Creative"),
    ("sales", "Sales & Business Development"),
    ("public_sector", "Public Sector / Government"),
    ("sustainability", "Environmental & Sustainability"),
    ("other", "Other"),
]


class InterntionEmployer(models.Model):
    _name = "interntion.employer"
    _description = "Industry Partner (Employer)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    sector = fields.Selection(SECTOR_SELECTION, string="Sector", required=True, tracking=True)
    partner_country = fields.Selection([
        ("uk", "UK"), ("india", "India"), ("uae", "UAE"), ("usa", "USA"), ("other", "Other"),
    ], string="Partner Country", tracking=True)
    account_manager_id = fields.Many2one("res.users", string="Account Manager", tracking=True)
    website = fields.Char()
    logo = fields.Binary(attachment=True)
    contact_name = fields.Char(string="Contact Person")
    contact_email = fields.Char(string="Contact Email")
    contact_phone = fields.Char(string="Contact Phone")
    partner_since = fields.Date(string="Industry Partner Since", default=fields.Date.context_today)
    is_industry_partner = fields.Boolean(default=True, tracking=True)
    active = fields.Boolean(default=True)
    notes = fields.Text()

    internship_ids = fields.One2many("interntion.internship", "employer_id", string="Internships")
    internship_count = fields.Integer(compute="_compute_internship_count")

    application_ids = fields.One2many(
        "crm.lead", "x_employer_id", string="Applications"
    )
    application_count = fields.Integer(compute="_compute_application_count")

    @api.depends("internship_ids")
    def _compute_internship_count(self):
        for rec in self:
            rec.internship_count = len(rec.internship_ids)

    @api.depends("application_ids")
    def _compute_application_count(self):
        for rec in self:
            rec.application_count = len(rec.application_ids)

    def action_view_internships(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Internships",
            "res_model": "interntion.internship",
            "view_mode": "list,form",
            "domain": [("employer_id", "=", self.id)],
        }

    def action_view_applications(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Applications",
            "res_model": "crm.lead",
            "view_mode": "list,form,kanban",
            "domain": [("x_employer_id", "=", self.id)],
        }
