from odoo import api, fields, models
from odoo.exceptions import ValidationError


class InterntionMarket(models.Model):
    _name = "interntion.market"
    _description = "Interntion Market"
    _order = "name"

    code = fields.Selection([
        ("UK", "UK"),
        ("US", "US"),
        ("IN", "IN"),
    ], required=True, index=True)
    name = fields.Char(required=True)
    currency_symbol = fields.Char(string="Currency Symbol", default="£")
    is_active = fields.Boolean(default=True, string="Active")
    price_ids = fields.One2many("interntion.market.price", "market_id", string="Market Prices")

    _code_unique = models.Constraint(
        "UNIQUE(code)",
        "Market codes must be unique.",
    )

    @api.model
    def get_default_market(self):
        active_code = self.env.context.get("interntion_active_market") or self.env["ir.config_parameter"].sudo().get_param("interntion_active_market")
        if not active_code:
            country_code = (self.env.user.company_id.country_id.code or "").upper()
            mapping = {"GB": "UK", "UK": "UK", "US": "US", "IN": "IN", "IND": "IN"}
            active_code = mapping.get(country_code, "UK")
        market = self.search([("code", "=", active_code), ("is_active", "=", True)], limit=1)
        if not market:
            market = self.search([("code", "=", "UK"), ("is_active", "=", True)], limit=1)
        if market:
            return market
        return self.create({"code": "UK", "name": "United Kingdom", "currency_symbol": "£", "is_active": True})

    @api.model
    def set_active_market(self, code):
        market_code = (code or "").upper()
        if market_code not in ["UK", "US", "IN"]:
            market_code = "UK"
        self.env["ir.config_parameter"].sudo().set_param("interntion_active_market", market_code)
        return {"type": "ir.actions.client", "tag": "reload"}


class InterntionMarketPrice(models.Model):
    _name = "interntion.market.price"
    _description = "Market Price"
    _order = "market_id, id"

    market_id = fields.Many2one("interntion.market", required=True, string="Market")
    internship_id = fields.Many2one("interntion.internship", index=True, ondelete="cascade")
    service_id = fields.Many2one("interntion.service", index=True, ondelete="cascade")
    project_id = fields.Many2one("interntion.project", index=True, ondelete="cascade")
    product_reference = fields.Char(string="Product Reference", compute="_compute_product_reference", store=True)
    amount = fields.Float(string="Amount", required=True, default=0.0)
    currency_symbol = fields.Char(string="Currency Symbol", default="£")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.ref("base.GBP", raise_if_not_found=False))

    @api.depends("internship_id", "service_id", "project_id")
    def _compute_product_reference(self):
        for rec in self:
            if rec.internship_id:
                rec.product_reference = rec.internship_id.name
            elif rec.service_id:
                rec.product_reference = rec.service_id.name
            elif rec.project_id:
                rec.product_reference = rec.project_id.name
            else:
                rec.product_reference = ""

    @api.constrains("internship_id", "service_id", "project_id")
    def _check_reference(self):
        for rec in self:
            total = sum((bool(rec.internship_id), bool(rec.service_id), bool(rec.project_id)))
            if total != 1:
                raise ValidationError("Select exactly one catalog record for this market price.")
