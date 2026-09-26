from odoo import api, fields, models

LEVEL_SELECTION = [
    ("btech", "B.Tech / BE"),
    ("mtech", "M.Tech / ME"),
    ("mca", "MCA"),
    ("bca", "BCA"),
    ("mba", "MBA"),
    ("phd", "PhD"),
]

CATEGORY_SELECTION = [
    ("ai", "Artificial Intelligence"),
    ("ml", "Machine Learning"),
    ("data_science", "Data Science"),
    ("web_dev", "Web Development"),
    ("mobile_dev", "Mobile App Development"),
    ("iot", "IoT & Embedded Systems"),
    ("cybersecurity", "Cybersecurity"),
    ("cloud", "Cloud Computing"),
    ("blockchain", "Blockchain"),
]


class InterntionProject(models.Model):
    _name = "interntion.project"
    _description = "Project Assistance Catalogue (AI/ML/Data Science)"
    _order = "name"

    name = fields.Char(required=True)
    category = fields.Selection(CATEGORY_SELECTION, required=True)
    level = fields.Selection(LEVEL_SELECTION, string="Suitable For", required=True)
    description = fields.Text()
    tech_stack = fields.Char(string="Tech Stack", help="e.g. Python, TensorFlow, Flask")
    price = fields.Monetary(string="Price")
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.ref("base.GBP", raise_if_not_found=False)
    )
    market_id = fields.Many2one("interntion.market", string="Default Market")
    market_price_ids = fields.One2many("interntion.market.price", "project_id", string="Market Prices")
    current_market_price = fields.Monetary(string="Current Market Price", compute="_compute_current_market_price", readonly=True)
    current_currency_symbol = fields.Char(compute="_compute_current_market_price", readonly=True)
    has_source_code = fields.Boolean(default=True)
    has_documentation = fields.Boolean(default=True)
    has_expert_support = fields.Boolean(default=True)
    active = fields.Boolean(default=True)

    @api.depends("market_price_ids", "market_price_ids.amount", "market_price_ids.market_id")
    def _compute_current_market_price(self):
        market_obj = self.env["interntion.market"]
        for rec in self:
            market = market_obj.get_default_market()
            price_line = rec.market_price_ids.filtered(lambda p: p.market_id.id == market.id)
            rec.current_market_price = price_line.amount if price_line else (rec.price or 0.0)
            rec.current_currency_symbol = price_line.currency_symbol if price_line else (market.currency_symbol or rec.currency_id.symbol or "£")
