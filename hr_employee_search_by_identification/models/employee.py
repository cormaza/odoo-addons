from odoo import api, models
from odoo.osv import expression


class HrEmployee(models.Model):

    _inherit = "hr.employee"

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        if name:
            domain = [
                "|",
                ("identification_id", "=ilike", "%" + name + "%"),
                ("name", operator, name),
            ]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ["&", "!"] + domain[1:]
        assets = self.search(domain + args, limit=limit)
        return assets.name_get()
