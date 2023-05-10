from odoo import api, models


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    @api.depends(
        "product_id",
        "company_id",
        "currency_id",
        "product_uom",
        "move_ids",
        "move_ids.stock_valuation_layer_ids",
        "move_ids.picking_id.state",
        "order_id.state",
    )
    def _compute_purchase_price(self):
        svl_model = self.env["stock.valuation.layer"].sudo()
        done_lines = self.filtered(lambda x: x.order_id.state not in ("draft", "sent"))
        for line in self - done_lines:
            if line.product_id.categ_id.property_cost_method != "fifo":
                done_lines |= line
                continue
            else:
                candidate_layer = svl_model.search(
                    [
                        ("product_id", "=", line.product_id.id),
                        ("remaining_qty", ">", 0),
                        ("remaining_value", ">", 0),
                        ("company_id", "=", line.order_id.company_id.id),
                    ],
                    limit=1,
                )
                if not candidate_layer:
                    done_lines |= line
                    continue
                else:
                    product_cost = (
                        candidate_layer.remaining_value / candidate_layer.remaining_qty
                    )
                    line.purchase_price = line._convert_price(
                        product_cost, line.product_id.uom_id
                    )
        return super(SaleOrderLine, done_lines)._compute_purchase_price()
