from odoo import api, fields, models

CALL_DIRECTION_SELECTION = [
    ("in", "Inbound"),
    ("out", "Outbound"),
]

CALL_OUTCOME_SELECTION = [
    ("Connected", "Connected"),
    ("No Answer", "No Answer"),
    ("Voicemail", "Voicemail"),
    ("Callback Requested", "Callback Requested"),
    ("Not Interested", "Not Interested"),
    ("Converted", "Converted"),
]

AI_SENTIMENT_SELECTION = [
    ("Positive", "Positive"),
    ("Neutral", "Neutral"),
    ("Negative", "Negative"),
]

CALL_STATUS_SELECTION = [
    ("requested", "Requested"),
    ("in_progress", "In progress"),
    ("completed", "Completed"),
    ("failed", "Failed"),
]


class InterntionCallLog(models.Model):
    _name = "interntion.call.log"
    _description = "Call Log"
    _order = "call_datetime desc"

    lead_id = fields.Many2one("crm.lead", string="Lead", required=True, ondelete="cascade")
    mentor_id = fields.Many2one("interntion.mentor", string="Caller")
    call_direction = fields.Selection(CALL_DIRECTION_SELECTION, string="Direction", required=True, default="out")
    call_datetime = fields.Datetime(string="Call Date", default=fields.Datetime.now)
    duration_minutes = fields.Integer(string="Duration (minutes)", default=0)
    outcome = fields.Selection(CALL_OUTCOME_SELECTION, string="Outcome", default="Connected")
    notes = fields.Text(string="Notes")
    next_action = fields.Char(string="Next Action")
    next_action_date = fields.Date(string="Next Action Date")
    recording_url = fields.Char(string="Recording URL")
    provider_call_id = fields.Char(string="Provider Call ID", copy=False, index=True)
    call_status = fields.Selection(CALL_STATUS_SELECTION, string="Call Status", default="completed")
    language = fields.Char(string="Detected Language")
    intent = fields.Char(string="Detected Intent")
    transcript = fields.Text(string="Transcript")
    ai_confidence = fields.Float(string="AI Confidence (%)")
    consent_captured = fields.Boolean(string="Consent Captured")
    callback_requested = fields.Boolean(string="Callback Requested")
    ai_summary = fields.Text(string="AI Summary", readonly=True)
    ai_sentiment = fields.Selection(AI_SENTIMENT_SELECTION, string="AI Sentiment", readonly=True)
    ai_next_step_suggestion = fields.Text(string="AI Next Step Suggestion", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._generate_ai_insights(record)
        return records

    def write(self, vals):
        result = super().write(vals)
        if "notes" in vals:
            self._generate_ai_insights(self)
        return result

    def _generate_ai_insights(self, call_log=None):
        for record in self:
            call = call_log or record
            notes = call.notes or ""
            summary = notes.strip() or "No call notes captured yet."
            sentiment = "Neutral"
            lower_notes = notes.lower()
            if any(keyword in lower_notes for keyword in ["interested", "happy", "engaged", "positive", "great", "good"]):
                sentiment = "Positive"
            elif any(keyword in lower_notes for keyword in ["not interested", "angry", "frustrated", "concerned", "negative"]):
                sentiment = "Negative"
            next_step = "Follow up with the lead and confirm the next action within 24 hours."
            if notes:
                next_step = "Review the lead notes, confirm the agreed next step, and keep the conversation moving on the agreed date."
            record.ai_summary = summary[:1000]
            record.ai_sentiment = sentiment
            record.ai_next_step_suggestion = next_step

    @api.model
    def process_provider_webhook(self, payload):
        provider_call_id = payload.get("provider_call_id") or payload.get("call_id")
        if not provider_call_id:
            return self.browse()
        record = self.search([("provider_call_id", "=", provider_call_id)], limit=1)
        if not record:
            return self.browse()
        values = {
            "call_status": payload.get("status") or record.call_status,
            "language": payload.get("language") or record.language,
            "intent": payload.get("intent") or record.intent,
            "transcript": payload.get("transcript") or record.transcript,
            "recording_url": payload.get("recording_url") or record.recording_url,
            "duration_minutes": payload.get("duration_minutes", record.duration_minutes),
            "outcome": payload.get("outcome") or record.outcome,
            "ai_confidence": payload.get("ai_confidence", record.ai_confidence),
        }
        if values["transcript"]:
            values["notes"] = values["transcript"]
        record.write(values)
        record._generate_ai_insights(record)
        return record


class InterntionCallLogWizard(models.TransientModel):
    _name = "interntion.call.log.wizard"
    _description = "Log Call Wizard"

    lead_id = fields.Many2one("crm.lead", string="Lead", required=True)
    mentor_id = fields.Many2one("interntion.mentor", string="Caller")
    call_direction = fields.Selection(CALL_DIRECTION_SELECTION, string="Direction", required=True, default="out")
    call_datetime = fields.Datetime(string="Call Date", default=fields.Datetime.now)
    duration_minutes = fields.Integer(string="Duration (minutes)", default=0)
    outcome = fields.Selection(CALL_OUTCOME_SELECTION, string="Outcome", default="Connected")
    notes = fields.Text(string="Notes")
    next_action = fields.Char(string="Next Action")
    next_action_date = fields.Date(string="Next Action Date")
    recording_url = fields.Char(string="Recording URL")

    def action_save(self):
        self.ensure_one()
        self.env["interntion.call.log"].create({
            "lead_id": self.lead_id.id,
            "mentor_id": self.mentor_id.id,
            "call_direction": self.call_direction,
            "call_datetime": self.call_datetime,
            "duration_minutes": self.duration_minutes,
            "outcome": self.outcome,
            "notes": self.notes,
            "next_action": self.next_action,
            "next_action_date": self.next_action_date,
            "recording_url": self.recording_url,
        })
        return {"type": "ir.actions.act_window_close"}
