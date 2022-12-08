from odoo import models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    def _get_taxes_data_paymentez(self):
        self.ensure_one()

        def compute_taxes(order_line):
            price = order_line.price_unit * (1 - (order_line.discount or 0.0) / 100.0)
            order = order_line.order_id
            return order_line.tax_id._origin.compute_all(
                price,
                order.currency_id,
                order_line.product_uom_qty,
                product=order_line.product_id,
                partner=order.partner_shipping_id,
            )

        account_move = self.env["account.move"].sudo()
        order = self
        tax_lines_data = account_move._prepare_tax_lines_data_for_totals_from_object(
            order.order_line, compute_taxes
        )
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
