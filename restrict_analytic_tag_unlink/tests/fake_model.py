from odoo import fields, models


class FakeRestrictionTestModel(models.Model):

    _name = "fake.restriction.test.model"

    name = fields.Char()
    analytic_tag_ids = fields.Many2many(
        comodel_name="account.analytic.tag", string="Analytic tags"
    )
