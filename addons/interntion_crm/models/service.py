from odoo import api, fields, models

SERVICE_CODE_SELECTION = [
    ("internship_opportunities", "Internship Opportunities"),
    ("project_assistance", "Project Assistance"),
    ("work_experience_support", "Work Experience Support"),
    ("cv_job_preparation", "CV & Job Preparation"),
]


class InterntionService(models.Model):
    _name = "interntion.service"
    _description = "Interntion Core Service"
    _order = "sequence, id"

    name = fields.Char(required=True)
    code = fields.Selection(SERVICE_CODE_SELECTION, required=True)
    description = fields.Text()
    icon = fields.Char(string="Icon (Font Awesome class)", default="fa-briefcase")
    sequence = fields.Integer(default=10)
    is_new = fields.Boolean(string="New Badge")
    url = fields.Char(string="Reference URL")
    active = fields.Boolean(default=True)
    price = fields.Monetary(string="Base Price")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.ref("base.GBP", raise_if_not_found=False))
    market_id = fields.Many2one("interntion.market", string="Default Market")
    market_price_ids = fields.One2many("interntion.market.price", "service_id", string="Market Prices")
    current_market_price = fields.Monetary(string="Current Market Price", compute="_compute_current_market_price", readonly=True)
    current_currency_symbol = fields.Char(compute="_compute_current_market_price", readonly=True)

    @api.depends("market_price_ids", "market_price_ids.amount", "market_price_ids.market_id")
    def _compute_current_market_price(self):
        market_obj = self.env["interntion.market"]
        for rec in self:
            market = market_obj.get_default_market()
            price_line = rec.market_price_ids.filtered(lambda p: p.market_id.id == market.id)
            rec.current_market_price = price_line.amount if price_line else (rec.price or 0.0)
            rec.current_currency_symbol = price_line.currency_symbol if price_line else (market.currency_symbol or rec.currency_id.symbol or "£")
