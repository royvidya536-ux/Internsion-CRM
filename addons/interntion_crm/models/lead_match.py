from odoo import api, fields, models


class InterntionLeadMatch(models.Model):
    _name = "interntion.lead.match"
    _description = "Lead Match"
    _order = "score desc, id desc"

    lead_id = fields.Many2one("crm.lead", string="Lead", required=True, ondelete="cascade")
    internship_id = fields.Many2one("interntion.internship", string="Internship")
    project_id = fields.Many2one("interntion.project", string="Project")
    service_id = fields.Many2one("interntion.service", string="Service")
    score = fields.Float(string="Match Score", default=0.0)
    match_details = fields.Text(string="Match Details")

    @api.model
    def create_matches_for_lead(self, lead_id):
        lead = self.env["crm.lead"].browse(lead_id)
        if not lead:
            return self.browse()
        self.search([("lead_id", "=", lead.id)]).unlink()
        matches = self.browse()
        targets = (
            ("internship_id", self.env["interntion.internship"].search([])),
            ("project_id", self.env["interntion.project"].search([])),
            ("service_id", self.env["interntion.service"].search([])),
        )
        for field_name, records in targets:
            for record in records:
                score = self._score_record(lead, record)
                if score <= 0:
                    continue
                matches |= self.create({
                    "lead_id": lead.id,
                    field_name: record.id,
                    "score": score,
                    "match_details": self._match_detail_text(lead, record),
                })
        return matches

    @api.model
    def _score_record(self, lead, record):
        score = 0.0
        lead_sector = (lead.x_industry_sector or "").lower()
        lead_stream = (lead.x_course_stream or "").lower()
        record_sector = ""
        if record._name == "interntion.internship":
            record_sector = (record.sector or "").lower()
        elif record._name == "interntion.project":
            record_sector = (record.category or "").lower()
        elif record._name == "interntion.service":
            record_sector = (record.code or "").lower()
        if record_sector and record_sector == lead_sector:
            score += 60
        if record._name == "interntion.internship" and lead_stream and (lead_stream in (record.name or "").lower()):
            score += 20
        if record._name == "interntion.project" and lead_stream and (lead_stream in (record.name or "").lower() or lead_stream in (record.tech_stack or "").lower()):
            score += 25
        if record._name == "interntion.service" and lead_stream and (lead_stream in (record.name or "").lower()):
            score += 15
        return round(score, 2)

    @api.model
    def _match_detail_text(self, lead, record):
        summary = []
        if lead.x_industry_sector:
            summary.append(f"Preferred sector: {lead.x_industry_sector}")
        if lead.x_course_stream:
            summary.append(f"Course stream: {lead.x_course_stream}")
        if record._name == "interntion.internship":
            summary.append(f"Role: {record.name}")
        elif record._name == "interntion.project":
            summary.append(f"Project: {record.name}")
        else:
            summary.append(f"Service: {record.name}")
        return " | ".join(summary)
