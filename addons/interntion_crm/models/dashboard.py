from datetime import datetime, timedelta

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
    new_applications = fields.Integer(compute="_compute_kpis", string="New Applications")
    cv_screening = fields.Integer(compute="_compute_kpis", string="CV Screening")
    interviews = fields.Integer(compute="_compute_kpis", string="Interviews")
    offers_open = fields.Integer(compute="_compute_kpis", string="Offers Open")
    placed_applications = fields.Integer(compute="_compute_kpis", string="Placed Applications")
    active_partners = fields.Integer(compute="_compute_kpis", string="Active Partners")
    industries_covered = fields.Integer(compute="_compute_kpis", string="Industries Covered")
    countries_active = fields.Integer(compute="_compute_kpis", string="Countries Active")
    partnership_sla_rate = fields.Float(compute="_compute_kpis", string="Partner SLA %")
    student_match_sla_rate = fields.Float(compute="_compute_kpis", string="Student Match SLA %")
    at_risk_count = fields.Integer(compute="_compute_kpis", string="At Risk")
    open_support_tickets = fields.Integer(compute="_compute_kpis", string="Open Support Tickets")
    urgent_support_tickets = fields.Integer(compute="_compute_kpis", string="Urgent Support Tickets")
    calls_made_this_week = fields.Integer(compute="_compute_kpis", string="Calls Made This Week")
    connect_rate = fields.Float(compute="_compute_kpis", string="Connect Rate %")
    avg_time_to_first_call = fields.Float(compute="_compute_kpis", string="Avg. Time to First Call")
    addon_revenue_month = fields.Monetary(compute="_compute_kpis", string="Add-on Revenue")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.ref("base.GBP", raise_if_not_found=False))

    def _compute_kpis(self):
        Lead = self.env["crm.lead"]
        Employer = self.env["interntion.employer"]
        Internship = self.env["interntion.internship"]
        Mentor = self.env["interntion.mentor"]
        SupportTicket = self.env["interntion.support.ticket"]

        def stage_count(stage_names):
            base_domain = [("type", "=", "opportunity"), ("interntion_side", "=", "student")]
            if len(stage_names) == 1:
                return Lead.search_count(base_domain + [("stage_id.name", "=", stage_names[0])])

            domain = base_domain.copy()
            first_clause = [("stage_id.name", "=", stage_names[0])]
            for stage_name in stage_names[1:]:
                first_clause = ["|"] + first_clause + [("stage_id.name", "=", stage_name)]
            return Lead.search_count(domain + first_clause)

        total = Lead.search_count([("type", "=", "opportunity"), ("interntion_side", "=", "student")])
        won = Lead.search_count([("type", "=", "opportunity"), ("interntion_side", "=", "student"), ("stage_id.name", "=", "Placement Completed")])
        partners = Employer.search_count([("active", "=", True), ("is_industry_partner", "=", True)])
        internships = Internship.search_count([("active", "=", True)])
        mentors = Mentor.search_count([("active", "=", True)])

        stage_counts = {
            "new": stage_count(("New Application", "New")),
            "screening": stage_count(("CV/Profile Review", "CV Screening", "Qualified")),
            "interview": Lead.search_count([
                ("type", "=", "opportunity"),
                ("interntion_side", "=", "student"),
                ("stage_id.name", "=", "Interview Scheduled"),
            ]),
            "offers": stage_count(("Offer Extended", "Proposition")),
            "placed": stage_count(("Placement Active", "Placed", "Won")),
        }

        for rec in self:
            rec.students_placed = won
            rec.total_applications = total
            rec.success_rate = round((won / total) * 100, 2) if total else 0.0
            rec.industry_partners = partners
            rec.open_internships = internships
            rec.active_mentors = mentors
            rec.new_applications = stage_counts["new"]
            rec.cv_screening = stage_counts["screening"]
            rec.interviews = stage_counts["interview"]
            rec.offers_open = stage_counts["offers"]
            rec.placed_applications = stage_counts["placed"]
            rec.active_partners = Lead.search_count([("type", "=", "opportunity"), ("interntion_side", "=", "partner"), ("stage_id.name", "=", "Active Partner")])
            rec.industries_covered = len(self.env["interntion.industry"].search([("active", "=", True)]))
            rec.countries_active = len(set(self.env["interntion.employer"].search([("active", "=", True)]).mapped("partner_country"))) if "partner_country" in self.env["interntion.employer"]._fields else 0
            partner_leads = Lead.search([("type", "=", "opportunity"), ("interntion_side", "=", "partner"), ("create_date", ">=", fields.Datetime.now() - timedelta(days=30))])
            student_leads = Lead.search([("type", "=", "opportunity"), ("interntion_side", "=", "student"), ("create_date", ">=", fields.Datetime.now() - timedelta(days=30))])
            rec.partnership_sla_rate = self._sla_rate(partner_leads)
            rec.student_match_sla_rate = self._sla_rate(student_leads)
            rec.at_risk_count = Lead.search_count([("type", "=", "opportunity"), ("sla_status", "in", ["at_risk", "breached"])])
            rec.open_support_tickets = SupportTicket.search_count([("state", "in", ["new", "in_progress"])])
            rec.urgent_support_tickets = SupportTicket.search_count([("state", "in", ["new", "in_progress"]), ("priority", "=", "3")])
            call_logs = self.env["interntion.call.log"].search([
                ("call_datetime", ">=", fields.Datetime.to_string(fields.Datetime.now() - timedelta(days=7))),
            ])
            rec.calls_made_this_week = len(call_logs)
            connected_calls = call_logs.filtered(lambda log: log.outcome == "Connected")
            rec.connect_rate = round((len(connected_calls) / len(call_logs) * 100), 2) if call_logs else 0.0
            first_call_dates = []
            for lead in Lead.search([("type", "=", "opportunity")]):
                lead_calls = lead.call_log_ids.sorted("call_datetime")
                if lead_calls:
                    if lead.create_date and lead_calls[0].call_datetime >= lead.create_date:
                        first_call_dates.append((lead_calls[0].call_datetime - lead.create_date).total_seconds() / 3600)
            rec.avg_time_to_first_call = round(sum(first_call_dates) / len(first_call_dates), 2) if first_call_dates else 0.0
            rec.addon_revenue_month = 0.0

    @staticmethod
    def _sla_rate(leads):
        if not leads:
            return 0.0
        return round(100 * len(leads.filtered(lambda lead: lead.sla_status == "on_track")) / len(leads), 2)

    def _student_stage_domain(self, *stage_names):
        domain = [("type", "=", "opportunity"), ("interntion_side", "=", "student")]
        if not stage_names:
            return domain
        clause = [("stage_id.name", "=", stage_names[0])]
        for stage_name in stage_names[1:]:
            clause = ["|"] + clause + [("stage_id.name", "=", stage_name)]
        return domain + clause

    def action_view_total_applications(self):
        return {
            "type": "ir.actions.act_window",
            "name": "All Student Applications",
            "res_model": "crm.lead",
            "view_mode": "kanban,list,form",
            "domain": [("type", "=", "opportunity"), ("interntion_side", "=", "student")],
            "context": {"default_type": "opportunity", "default_interntion_side": "student"},
        }

    def action_view_placed(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Placed Students",
            "res_model": "crm.lead",
            "view_mode": "list,form,kanban",
            "domain": [("type", "=", "opportunity"), ("stage_id.is_won", "=", True), ("interntion_side", "=", "student")],
        }

    def action_view_partners(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Industry Partners",
            "res_model": "interntion.employer",
            "view_mode": "list,form,kanban",
            "domain": [("active", "=", True)],
        }

    def action_view_internships(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Open Internships",
            "res_model": "interntion.internship",
            "view_mode": "list,form,kanban",
            "domain": [("active", "=", True)],
        }

    def action_view_new_applications(self):
        return {
            "type": "ir.actions.act_window",
            "name": "New Applications",
            "res_model": "crm.lead",
            "view_mode": "kanban,list,form",
            "domain": self._student_stage_domain("New Application", "New"),
            "context": {"default_type": "opportunity", "default_interntion_side": "student"},
        }

    def action_view_cv_screening(self):
        return {
            "type": "ir.actions.act_window",
            "name": "CV Screening",
            "res_model": "crm.lead",
            "view_mode": "kanban,list,form",
            "domain": self._student_stage_domain("CV/Profile Review", "CV Screening", "Qualified"),
            "context": {"default_type": "opportunity", "default_interntion_side": "student"},
        }

    def action_view_interviews(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Interview Stage",
            "res_model": "crm.lead",
            "view_mode": "kanban,list,form",
            "domain": self._student_stage_domain("Interview Scheduled"),
            "context": {"default_type": "opportunity", "default_interntion_side": "student"},
        }

    def action_view_offers(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Offers Open",
            "res_model": "crm.lead",
            "view_mode": "kanban,list,form",
            "domain": self._student_stage_domain("Offer Extended", "Proposition"),
            "context": {"default_type": "opportunity", "default_interntion_side": "student"},
        }

    def action_view_placement_pipeline(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Placement Pipeline",
            "res_model": "crm.lead",
            "view_mode": "kanban,list,form",
            "domain": self._student_stage_domain("New Application", "CV/Profile Review", "CV Screening", "Interview Scheduled", "Offer Extended", "Placement Active", "Placement Completed", "Placed", "Won"),
            "context": {"default_type": "opportunity", "default_interntion_side": "student"},
        }

    def action_view_open_internships(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Open Internship Roles",
            "res_model": "interntion.internship",
            "view_mode": "kanban,list,form",
            "domain": [("active", "=", True)],
        }

    def action_view_active_mentors(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Active Mentors",
            "res_model": "interntion.mentor",
            "view_mode": "kanban,list,form",
            "domain": [("active", "=", True)],
        }

    def action_view_support_queue(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Open Support Requests",
            "res_model": "interntion.support.ticket",
            "view_mode": "list,form",
            "domain": [("state", "in", ["new", "in_progress"])],
            "context": {"default_assigned_user_id": self.env.user.id},
        }

    def action_create_support_request(self):
        return {
            "type": "ir.actions.act_window",
            "name": "New Support Request",
            "res_model": "interntion.support.ticket",
            "view_mode": "form",
            "target": "current",
            "context": {"default_assigned_user_id": self.env.user.id},
        }

    def action_view_student_pipeline(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Student Placement Pipeline",
            "res_model": "crm.lead",
            "view_mode": "kanban,list,form",
            "domain": [("type", "=", "opportunity"), ("interntion_side", "=", "student")],
            "context": {"default_type": "opportunity", "default_interntion_side": "student"},
        }

    def action_view_partner_pipeline(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Corporate Partner Pipeline",
            "res_model": "crm.lead",
            "view_mode": "kanban,list,form",
            "domain": [("type", "=", "opportunity"), ("interntion_side", "=", "partner")],
            "context": {"default_type": "opportunity", "default_interntion_side": "partner"},
        }

    @api.model
    def get_or_create_singleton(self):
        rec = self.search([], limit=1)
        if not rec:
            rec = self.create({"name": "Interntion Overview"})
        return rec
