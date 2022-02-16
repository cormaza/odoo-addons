# Copyright 2022 Christopher Ormaza <mailto://chris.ormaza@.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    shipped_rate = fields.Float(
        compute="_compute_shipped_rate", string="Invoiced (%)", store=True, copy=False
    )
    invoiced_rate = fields.Float(
        compute="_compute_invoiced_rate", string="Delivered (%)", store=True, copy=False
    )
    force_full_rated = fields.Boolean(
        string="Force full invoiced and delivered rated", required=False
    )

    @api.depends(
        "force_full_rated",
        "order_line.qty_delivered",
        "order_line.qty_delivered_method",
        "order_line.qty_delivered_manual",
        "order_line.analytic_line_ids.so_line",
        "order_line.analytic_line_ids.unit_amount",
        "order_line.analytic_line_ids.product_uom_id",
        "order_line.move_ids.state",
        "order_line.move_ids.scrapped",
        "order_line.move_ids.product_uom_qty",
        "order_line.move_ids.product_uom",
    )
    def _compute_shipped_rate(self):
        for record in self:
            if record.force_full_rated:
                shipped_rate = 100.0
            else:
                product_uom_qty = sum(
                    record.order_line.filtered(
                        lambda x: x.product_id.type in ("product", "consu")
                    ).mapped("product_uom_qty")
                )
                qty_delivered = sum(
                    record.order_line.filtered(
                        lambda x: x.product_id.type in ("product", "consu")
                    ).mapped("qty_delivered")
                )
                shipped_rate = (
                    min((qty_delivered / product_uom_qty) * 100, 100.0)
                    if product_uom_qty
                    else 100.0
                )
            record.shipped_rate = shipped_rate

    @api.depends(
        "force_full_rated",
        "order_line.qty_invoiced",
        "order_line.qty_to_invoice",
        "order_line.qty_delivered",
        "order_line.invoice_lines.move_id.state",
        "order_line.invoice_lines.quantity",
    )
    def _compute_invoiced_rate(self):
        for record in self:
            if record.force_full_rated:
                invoiced_rate = 100.0
            else:
                product_uom_qty = sum(record.order_line.mapped("product_uom_qty"))
                qty_to_invoice = sum(record.order_line.mapped("qty_to_invoice"))
                qty_invoiced = sum(record.order_line.mapped("qty_invoiced"))
                if qty_to_invoice > 0:
                    invoiced_rate = (
                        min((qty_invoiced / product_uom_qty) * 100, 100.0)
                        if product_uom_qty
                        else 100.0
                    )
                else:
                    invoiced_rate = 100.0
            record.invoiced_rate = invoiced_rate
