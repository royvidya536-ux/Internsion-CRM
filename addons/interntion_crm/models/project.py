from odoo import fields, models

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
    has_source_code = fields.Boolean(default=True)
    has_documentation = fields.Boolean(default=True)
    has_expert_support = fields.Boolean(default=True)
    active = fields.Boolean(default=True)
