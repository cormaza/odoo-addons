from odoo import models


class AccountMove(models.Model):

    _inherit = "account.move"

    def _get_taxes_data_paymentez(self):
        self.ensure_one()
        tax_lines_data = self._prepare_tax_lines_data_for_totals_from_invoice()
        res = {}
        for line in tax_lines_data:
            res.setdefault(
                line.get("tax", False),
                {
                    "base": 0.0,
                    "tax": 0.0,
                },
            )
            res[line.get("tax", False)]["base"] += line.get("base_amount", 0.0)
            res[line.get("tax", False)]["tax"] += line.get("tax_amount", 0.0)
        return res
