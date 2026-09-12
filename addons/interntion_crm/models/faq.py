from odoo import fields, models

CATEGORY_SELECTION = [
    ("general", "General"),
    ("eligibility", "Eligibility"),
    ("process", "Application Process"),
    ("payment", "Fees & Payment"),
    ("international", "International Students"),
]


class InterntionFaq(models.Model):
    _name = "interntion.faq"
    _description = "Frequently Asked Question"
    _order = "sequence, id"

    question = fields.Char(required=True)
    answer = fields.Html(required=True)
    category = fields.Selection(CATEGORY_SELECTION, default="general")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
