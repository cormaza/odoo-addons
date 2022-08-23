from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_is_zero


class StockInventoryLine(models.Model):

    _inherit = "stock.inventory.line"

    currency_id = fields.Many2one(related="inventory_id.company_id.currency_id")
    custom_cost = fields.Monetary(
        string="Custom cost",
    )

    @api.constrains(
        "custom_cost",
    )
    def _check_custom_cost_negative(self):
        for rec in self:
            if (
                float_compare(
                    rec.custom_cost, 0, precision_rounding=self.currency_id.rounding
                )
                == -1
            ):
                raise ValidationError(
                    _("Custom cost can't be lower than zero on line %s")
                    % (rec.display_name)
                )

    def _get_move_values(self, qty, location_id, location_dest_id, out):
        self.ensure_one()
        res = super(StockInventoryLine, self)._get_move_values(
            qty, location_id, location_dest_id, out
        )
        if self.env.user.has_group(
            "stock_inventory_custom_cost.group_custom_cost_inventory"
        ) and not float_is_zero(
            self.custom_cost, precision_rounding=self.currency_id.rounding
        ):
            res.update(
                {
                    "price_unit": self.custom_cost,
                }
            )
        return res
