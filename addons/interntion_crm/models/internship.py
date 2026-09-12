from odoo import fields, models, api
from .employer import SECTOR_SELECTION


class InterntionInternship(models.Model):
    _name = "interntion.internship"
    _description = "Internship Opportunity"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "is_new desc, name"

    name = fields.Char(string="Role Title", required=True, tracking=True)
    employer_id = fields.Many2one("interntion.employer", string="Industry Partner", tracking=True)
    sector = fields.Selection(SECTOR_SELECTION, string="Sector", required=True, tracking=True)
    description = fields.Html(string="Description")
    duration = fields.Char(string="Duration", help="e.g. 3 months, 6 months")
    location = fields.Char(default="United Kingdom (Remote/On-site)")

    is_paid = fields.Boolean(string="Paid Internship", default=True, tracking=True)
    stipend_amount = fields.Monetary(string="Monthly Stipend")
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.ref("base.GBP", raise_if_not_found=False)
    )

    is_new = fields.Boolean(string="New", default=True)
    active = fields.Boolean(default=True)
    open_positions = fields.Integer(string="Open Positions", default=1)

    application_ids = fields.One2many("crm.lead", "x_internship_id", string="Applications")
    application_count = fields.Integer(compute="_compute_application_count")
    placed_count = fields.Integer(compute="_compute_application_count", string="Placed")

    @api.depends("application_ids", "application_ids.stage_id")
    def _compute_application_count(self):
        for rec in self:
            rec.application_count = len(rec.application_ids)
            rec.placed_count = len(rec.application_ids.filtered(lambda a: a.stage_id.is_won))

    def action_view_applications(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Applications",
            "res_model": "crm.lead",
            "view_mode": "list,form,kanban",
            "domain": [("x_internship_id", "=", self.id)],
        }
