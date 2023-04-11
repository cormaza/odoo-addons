from odoo import api, fields, models
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval


class SaleProductFilter(models.Model):
    _name = "sale.product.filter"

    name = fields.Char(string="Description", required=True)
    filter_domain = fields.Char(string="Filter Domain", required=True)
    user_ids = fields.Many2many(comodel_name="res.users", string="Users")

    @api.model
    def get_user_domains(self):
        current_user = self.env.user
        user_domains = self.search([("user_ids", "=", current_user.id)]).mapped(
            "filter_domain"
        )
        if not user_domains:
            return []
        return expression.OR([safe_eval(domain) for domain in user_domains])
