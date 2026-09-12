from odoo import fields, models


class InterntionTestimonial(models.Model):
    _name = "interntion.testimonial"
    _description = "Student Success Story / Testimonial"
    _order = "sequence, id"

    student_name = fields.Char(required=True)
    course = fields.Char(string="Course / Stream", help="e.g. B.Tech CSE, MBA Marketing")
    role = fields.Char(string="Placed As", help="e.g. Software Intern, Brand Intern")
    quote = fields.Text(required=True)
    photo = fields.Binary(attachment=True)
    photo_url = fields.Char(string="Photo URL")
    rating = fields.Selection(
        [("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5")], default="5"
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
