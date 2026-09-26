import re

from odoo import fields, models


class InterntionLeadGeneration(models.TransientModel):
    _name = "interntion.lead.generation"
    _description = "Interntion Lead Generation Studio"

    source = fields.Selection([
        ("website", "Website campaign"),
        ("referral", "Student referral"),
        ("career_fair", "Career fair"),
        ("partner", "Industry outreach"),
    ], required=True, default="website")
    side = fields.Selection([
        ("student", "Student placement"),
        ("partner", "Corporate partnership"),
    ], required=True, default="student")
    names = fields.Text(
        string="Names or companies",
        help="Enter one person or company per line. An optional email can follow after a comma.",
    )
    campaign = fields.Char(string="Campaign", default="Interntion outreach")
    campaign_id = fields.Many2one("utm.campaign", string="Attribution campaign")
    sample_count = fields.Integer(string="Sample leads", default=0)

    def action_generate_leads(self):
        self.ensure_one()
        team_xmlid = (
            "interntion_crm.team_corporate_partnerships"
            if self.side == "partner"
            else "interntion_crm.crm_team_interntion"
        )
        stage_name = "New Enquiry" if self.side == "partner" else "New Application"
        team = self.env.ref(team_xmlid)
        stage = self.env["crm.stage"].search([
            ("name", "=", stage_name), ("team_id", "=", team.id)
        ], limit=1)
        entries = [line.strip() for line in (self.names or "").splitlines() if line.strip()]
        if self.sample_count:
            entries += [
                "Sample Student %02d, sample%02d@interntion.local" % (index, index)
                for index in range(1, self.sample_count + 1)
            ]
        created = self.env["crm.lead"]
        for entry in entries:
            parts = [part.strip() for part in entry.split(",", 1)]
            name = parts[0]
            email = parts[1] if len(parts) == 2 else self._extract_email(name)
            if email and self.env["crm.lead"].search_count([("email_from", "=ilike", email)]):
                continue
            vals = {
                "name": "%s: %s" % ("Partnership enquiry" if self.side == "partner" else "Student application", name),
                "partner_name": name,
                "email_from": email,
                "team_id": team.id,
                "user_id": team.user_id.id or self.env.user.id,
                "stage_id": stage.id or False,
                "type": "opportunity",
                "interntion_side": self.side,
                "x_application_source": self.source if self.side == "student" else False,
                "lead_source_detail": self.campaign,
                "campaign_id": self.campaign_id.id or False,
                "description": "Created by Lead Generation Studio.",
            }
            created |= self.env["crm.lead"].create(vals)
        return {
            "type": "ir.actions.act_window",
            "name": "Generated Leads (%s)" % len(created),
            "res_model": "crm.lead",
            "view_mode": "kanban,list,form",
            "domain": [("id", "in", created.ids)],
            "context": {"default_team_id": team.id, "default_type": "opportunity"},
        }

    @staticmethod
    def _extract_email(value):
        match = re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", value)
        return match.group(0) if match else False