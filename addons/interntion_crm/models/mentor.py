from odoo import fields, models, api


class InterntionMentor(models.Model):
    _name = "interntion.mentor"
    _description = "Career Mentor / Advisor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    user_id = fields.Many2one("res.users", string="Related User")
    email = fields.Char()
    phone = fields.Char()
    photo = fields.Binary(attachment=True)
    expertise = fields.Char(string="Area of Expertise", help="e.g. Tech, Finance, CV Writing, Mock Interviews")
    bio = fields.Text(string="Biography")
    active = fields.Boolean(default=True)

    application_ids = fields.One2many("crm.lead", "x_mentor_id", string="Mentored Applications")
    application_count = fields.Integer(compute="_compute_application_count")

    @api.depends("application_ids")
    def _compute_application_count(self):
        for rec in self:
            rec.application_count = len(rec.application_ids)

    def action_view_applications(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Mentored Applications",
            "res_model": "crm.lead",
            "view_mode": "list,form,kanban",
            "domain": [("x_mentor_id", "=", self.id)],
        }
