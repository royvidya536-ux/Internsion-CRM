from odoo import fields, models, api


class InterntionDashboard(models.Model):
    """Singleton-style KPI dashboard mirroring the public website's
    'Students Placed / Success Rate / Industry Partners' statistics,
    but computed live from real CRM data."""

    _name = "interntion.dashboard"
    _description = "Interntion CRM Dashboard"

    name = fields.Char(default="Interntion Overview", readonly=True)

    students_placed = fields.Integer(compute="_compute_kpis", string="Students Placed")
    total_applications = fields.Integer(compute="_compute_kpis", string="Total Applications")
    success_rate = fields.Float(compute="_compute_kpis", string="Success Rate (%)")
    industry_partners = fields.Integer(compute="_compute_kpis", string="Industry Partners")
    open_internships = fields.Integer(compute="_compute_kpis", string="Open Internships")
    active_mentors = fields.Integer(compute="_compute_kpis", string="Active Mentors")

    def _compute_kpis(self):
        Lead = self.env["crm.lead"]
        Employer = self.env["interntion.employer"]
        Internship = self.env["interntion.internship"]
        Mentor = self.env["interntion.mentor"]

        total = Lead.search_count([("type", "=", "opportunity")])
        won = Lead.search_count([("type", "=", "opportunity"), ("stage_id.is_won", "=", True)])
        partners = Employer.search_count([("active", "=", True), ("is_industry_partner", "=", True)])
        internships = Internship.search_count([("active", "=", True)])
        mentors = Mentor.search_count([("active", "=", True)])

        for rec in self:
            rec.students_placed = won
            rec.total_applications = total
            rec.success_rate = round((won / total) * 100, 1) if total else 0.0
            rec.industry_partners = partners
            rec.open_internships = internships
            rec.active_mentors = mentors

    def action_view_placed(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Placed Students",
            "res_model": "crm.lead",
            "view_mode": "list,form,kanban",
            "domain": [("type", "=", "opportunity"), ("stage_id.is_won", "=", True)],
        }

    def action_view_partners(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Industry Partners",
            "res_model": "interntion.employer",
            "view_mode": "list,form,kanban",
        }

    def action_view_internships(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Open Internships",
            "res_model": "interntion.internship",
            "view_mode": "list,form,kanban",
            "domain": [("active", "=", True)],
        }

    @api.model
    def get_or_create_singleton(self):
        rec = self.search([], limit=1)
        if not rec:
            rec = self.create({"name": "Interntion Overview"})
        return rec
