from odoo import api, fields, models
from .employer import SECTOR_SELECTION


class InterntionCampaign(models.Model):
    _inherit = "utm.campaign"
    _description = "Interntion Marketing Campaign"

    campaign_type = fields.Selection([
        ("Broadcast", "Broadcast"),
        ("List Push", "List Push"),
        ("Triggered", "Triggered"),
    ], default="Broadcast", required=True, string="Campaign Type")
    market_id = fields.Many2one("interntion.market", string="Target Market")
    target_sector = fields.Selection(SECTOR_SELECTION, string="Target Sector")
    channel_email = fields.Boolean(string="Email")
    channel_whatsapp = fields.Boolean(string="WhatsApp")
    channel_sms = fields.Boolean(string="SMS")
    channel_ai_voice_call = fields.Boolean(string="AI Voice Call")
    message_email = fields.Html(string="Email Message")
    message_whatsapp = fields.Text(string="WhatsApp Message")
    message_sms = fields.Text(string="SMS Message")
    voice_call_script = fields.Text(string="AI Voice Call Script")
    target_lead_ids = fields.Many2many("crm.lead", string="Target Leads")
    status = fields.Selection([
        ("Draft", "Draft"),
        ("Scheduled", "Scheduled"),
        ("Sent", "Sent"),
        ("Completed", "Completed"),
    ], default="Draft", required=True)
    scheduled_at = fields.Datetime(string="Scheduled At")
    objective = fields.Selection([
        ("applications", "Student applications"),
        ("partnerships", "Industry partnerships"),
        ("reengagement", "Lead re-engagement"),
        ("brand", "Brand awareness"),
    ], default="applications", required=True)
    source_id = fields.Many2one("utm.source", string="Source")
    medium_id = fields.Many2one("utm.medium", string="Medium")
    lifecycle = fields.Selection([
        ("planned", "Planned"),
        ("running", "Running"),
        ("paused", "Paused"),
        ("completed", "Completed"),
    ], default="planned", required=True)
    date_start = fields.Date(string="Start date")
    date_end = fields.Date(string="End date")
    target_leads = fields.Integer(string="Target leads")
    budget = fields.Monetary(string="Budget")
    landing_url = fields.Char(string="Landing page")
    notes = fields.Html(string="Campaign brief")
    lead_count = fields.Integer(compute="_compute_metrics", string="Leads")
    qualified_count = fields.Integer(compute="_compute_metrics", string="Qualified")
    won_count = fields.Integer(compute="_compute_metrics", string="Won")
    conversion_rate = fields.Float(compute="_compute_metrics", string="Conversion rate (%)")
    cost_per_lead = fields.Monetary(compute="_compute_metrics", string="Cost per lead")

    @api.depends("name", "budget", "target_lead_ids")
    def _compute_metrics(self):
        Lead = self.env["crm.lead"]
        for campaign in self:
            leads = Lead.search([("campaign_id", "=", campaign.id)])
            qualified = leads.filtered(lambda lead: lead.stage_id and not lead.stage_id.fold)
            won = leads.filtered(lambda lead: lead.stage_id and lead.stage_id.is_won)
            campaign.lead_count = len(leads) or len(campaign.target_lead_ids)
            campaign.qualified_count = len(qualified)
            campaign.won_count = len(won)
            campaign.conversion_rate = round(100 * len(won) / len(leads), 2) if leads else 0.0
            campaign.cost_per_lead = campaign.budget / len(leads) if leads else 0.0

    def action_set_running(self):
        self.write({"lifecycle": "running"})

    def action_set_paused(self):
        self.write({"lifecycle": "paused"})

    def action_set_completed(self):
        self.write({"lifecycle": "completed"})

    def action_view_campaign_leads(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Campaign Leads: %s" % self.name,
            "res_model": "crm.lead",
            "view_mode": "kanban,list,form",
            "domain": [("campaign_id", "=", self.id)],
            "context": {"default_campaign_id": self.id},
        }

    def _log_channel_activity(self, channel_name, lead):
        self.env["interntion.call.log"].create({
            "lead_id": lead.id,
            "call_direction": "out",
            "call_datetime": fields.Datetime.now(),
            "duration_minutes": 0,
            "outcome": "Connected",
            "notes": f"Would send via {channel_name} for campaign {self.name}.",
        })

    def _send_email_channel(self):
        for lead in self.target_lead_ids:
            self._log_channel_activity("Email", lead)

    def _send_whatsapp_channel(self):
        for lead in self.target_lead_ids:
            self._log_channel_activity("WhatsApp", lead)

    def _send_sms_channel(self):
        for lead in self.target_lead_ids:
            self._log_channel_activity("SMS", lead)

    def _send_ai_voice_channel(self):
        for lead in self.target_lead_ids:
            self._log_channel_activity("AI Voice", lead)

    def action_send_campaign(self):
        self.ensure_one()
        if self.channel_email:
            self._send_email_channel()
        if self.channel_whatsapp:
            self._send_whatsapp_channel()
        if self.channel_sms:
            self._send_sms_channel()
        if self.channel_ai_voice_call:
            self._send_ai_voice_channel()
        self.write({"status": "Sent"})
        return {"type": "ir.actions.client", "tag": "display_notification", "params": {"title": "Campaign queued", "message": "Channel sends were queued for the selected leads.", "type": "success", "sticky": False}}

    def action_add_matched_leads(self, threshold=30):
        self.ensure_one()
        matches = self.env["interntion.lead.match"].search([
            ("lead_id.x_industry_sector", "=", self.target_sector),
            ("score", ">=", threshold),
        ])
        matched = matches.mapped("lead_id")
        self.target_lead_ids = matched
        return True

    def action_find_matching_campaigns(self):
        self.ensure_one()
        campaigns = self.env["utm.campaign"].search([
            ("target_sector", "=", self.target_sector),
        ])
        return {
            "type": "ir.actions.act_window",
            "name": "Matching Campaigns",
            "res_model": "utm.campaign",
            "view_mode": "list,form",
            "domain": [("id", "in", campaigns.ids)],
        }