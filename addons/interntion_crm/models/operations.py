from datetime import timedelta

from odoo import api, fields, models

from .employer import SECTOR_SELECTION


class InterntionIndustry(models.Model):
    _name = "interntion.industry"
    _description = "Interntion Industry"
    _order = "sequence, name"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _code_unique = models.Constraint("UNIQUE(code)", "Industry codes must be unique.")


class InterntionAddonService(models.Model):
    _name = "interntion.addon.service"
    _description = "Interntion Paid Add-on Service"
    _order = "sequence, name"

    name = fields.Char(required=True)
    product_id = fields.Many2one("product.product", required=True, ondelete="restrict")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)


class InterntionSupportTicket(models.Model):
    _name = "interntion.support.ticket"
    _description = "Placement Support Ticket"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "priority desc, create_date desc"

    name = fields.Char(required=True, tracking=True)
    lead_id = fields.Many2one("crm.lead", required=True, ondelete="cascade", tracking=True)
    reporter_type = fields.Selection([
        ("student", "Student"), ("partner", "Partner"), ("mentor", "Mentor"),
    ], required=True, default="student", tracking=True)
    description = fields.Html(required=True)
    priority = fields.Selection([
        ("0", "Low"), ("1", "Normal"), ("2", "High"), ("3", "Urgent"),
    ], default="1", tracking=True)
    state = fields.Selection([
        ("new", "New"), ("in_progress", "In progress"),
        ("resolved", "Resolved"), ("closed", "Closed"),
    ], default="new", tracking=True)
    assigned_user_id = fields.Many2one("res.users", tracking=True)


class InterntionLead(models.Model):
    _inherit = "crm.lead"

    interntion_side = fields.Selection([
        ("student", "Student placement"), ("partner", "Corporate partnership"),
    ], default="student", index=True, tracking=True)
    university_institution = fields.Char(string="University / institution")
    country = fields.Many2one("res.country", string="Student country")
    target_industry_ids = fields.Many2many("interntion.industry", string="Target industries")
    placement_mode = fields.Selection([
        ("onsite", "On-site"), ("remote", "Remote"), ("hybrid", "Hybrid"),
    ], string="Placement mode")
    addon_service_ids = fields.Many2many("interntion.addon.service", string="Add-on services")
    mentor_assigned_user_id = fields.Many2one("res.users", string="Mentor", tracking=True)
    certificate_issued = fields.Boolean(string="Certificate issued", tracking=True)
    certificate_issued_date = fields.Date(string="Certificate issue date", tracking=True)
    latest_cv_attachment_id = fields.Many2one("ir.attachment", string="Latest CV", copy=False)
    company_industry_sector = fields.Selection(SECTOR_SELECTION, string="Company industry sector")
    partnership_interest_type = fields.Selection([
        ("one_off", "One-off placement"), ("ongoing", "Ongoing graduate pipeline"),
        ("project", "Project collaboration"), ("cobranding", "Co-branding / sponsorship"),
        ("other", "Other"),
    ], string="Partnership interest")
    partner_country = fields.Selection([
        ("uk", "UK"), ("india", "India"), ("uae", "UAE"),
        ("usa", "USA"), ("other", "Other"),
    ], string="Partner country")
    active_cohort_count = fields.Integer(string="Active cohort count")
    account_manager_id = fields.Many2one("res.users", string="Account manager", tracking=True)
    lead_source_detail = fields.Char(string="Source detail")
    sla_deadline = fields.Datetime(compute="_compute_sla_deadline", store=True, index=True)
    sla_status = fields.Selection([
        ("on_track", "On Track"), ("at_risk", "At Risk"), ("breached", "Breached"),
    ], compute="_compute_sla_status", search="_search_sla_status", string="SLA status")
    sla_completed_at = fields.Datetime(string="SLA completed at", copy=False)
    matched_at = fields.Datetime(string="Matched at", copy=False)
    onboarding_completed = fields.Boolean(string="Onboarding completed")
    expected_internship_end = fields.Date(string="Expected internship end")
    partner_company_id = fields.Many2one("interntion.employer", string="Target partner company")
    support_ticket_ids = fields.One2many("interntion.support.ticket", "lead_id")
    support_ticket_count = fields.Integer(compute="_compute_support_ticket_count")

    @api.depends("create_date", "interntion_side")
    def _compute_sla_deadline(self):
        for lead in self:
            if not lead.create_date:
                lead.sla_deadline = False
                continue
            hours = 24 if lead.interntion_side == "partner" else 24 * 7
            lead.sla_deadline = lead.create_date + timedelta(hours=hours)

    @api.depends("create_date", "interntion_side", "sla_completed_at", "sla_deadline")
    def _compute_sla_status(self):
        now = fields.Datetime.now()
        for lead in self:
            if not lead.create_date or not lead.sla_deadline:
                lead.sla_status = "on_track"
                continue
            if lead.sla_completed_at:
                lead.sla_status = "on_track" if lead.sla_completed_at <= lead.sla_deadline else "breached"
            elif now > lead.sla_deadline:
                lead.sla_status = "breached"
            elif now > lead.create_date + timedelta(hours=20 if lead.interntion_side == "partner" else 24 * 5):
                lead.sla_status = "at_risk"
            else:
                lead.sla_status = "on_track"

    def _search_sla_status(self, operator, value):
        ids = self.search([]).filtered(lambda lead: lead.sla_status == value).ids
        return [("id", operator, ids)]

    @api.depends("support_ticket_ids")
    def _compute_support_ticket_count(self):
        for lead in self:
            lead.support_ticket_count = len(lead.support_ticket_ids)

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        for lead in leads:
            lead._schedule_initial_sla_activity()
        return leads

    def write(self, vals):
        result = super().write(vals)
        if "stage_id" in vals:
            for lead in self:
                if lead.stage_id.name == "Matched to Partner" and not lead.matched_at:
                    lead.matched_at = fields.Datetime.now()
                    lead.sla_completed_at = lead.matched_at
                if lead.stage_id.name == "Placement Completed":
                    lead.certificate_issued = False
                    lead.activity_schedule(
                        "mail.mail_activity_data_todo",
                        summary="Issue completion certificate",
                        note="Generate and send the completion certificate.",
                        user_id=lead.user_id.id or self.env.user.id,
                    )
        return result

    def _schedule_initial_sla_activity(self):
        self.ensure_one()
        summary = "Respond within 24h" if self.interntion_side == "partner" else "Match within 7 days"
        user = self.account_manager_id or self.user_id or self.env.user
        self.activity_schedule("mail.mail_activity_data_todo", summary=summary, user_id=user.id)

    @api.model
    def cron_monitor_slas(self):
        leads = self.search([
            ("type", "=", "opportunity"),
            ("stage_id.is_won", "=", False),
        ])
        for lead in leads:
            if lead.sla_status not in ("at_risk", "breached"):
                continue
            summary = "SLA %s: %s" % (lead.sla_status.replace("_", " ").title(), lead.name)
            existing = self.env["mail.activity"].search([
                ("res_model", "=", "crm.lead"), ("res_id", "=", lead.id),
                ("summary", "=", summary), ("active", "=", True),
            ], limit=1)
            if not existing:
                lead.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary=summary,
                    note="Review and escalate this Interntion SLA exception.",
                    user_id=lead.user_id.id or self.env.user.id,
                )

    def action_create_addon_quotation(self):
        self.ensure_one()
        partner = self.partner_id
        if not partner:
            partner = self.env["res.partner"].create({"name": self.partner_name or self.name, "email": self.email_from})
        order = self.env["sale.order"].create({"partner_id": partner.id, "opportunity_id": self.id})
        for service in self.addon_service_ids:
            self.env["sale.order.line"].create({"order_id": order.id, "product_id": service.product_id.id, "product_uom_qty": 1})
        return {"type": "ir.actions.act_window", "res_model": "sale.order", "res_id": order.id, "view_mode": "form"}

    def action_view_support_tickets(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window", "name": "Placement Support",
            "res_model": "interntion.support.ticket", "view_mode": "list,form",
            "domain": [("lead_id", "=", self.id)], "context": {"default_lead_id": self.id},
        }
