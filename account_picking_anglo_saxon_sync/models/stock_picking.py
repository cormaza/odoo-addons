from odoo import _, fields, models
from odoo.models import MAGIC_COLUMNS
from odoo.tools import float_is_zero


class StockPicking(models.Model):

    _inherit = "stock.picking"


class StockMove(models.Model):

    _inherit = "stock.move"

    def _sync_anglo_saxon_values(self):
        self.ensure_one()
        am_model = self.env["account.move"]
        if (
            self.invoice_line_ids
            and (self._is_out() or self._is_in())
            and self.company_id.anglo_saxon_accounting
        ):
            for line in self.invoice_line_ids.filtered(
                lambda x: x.move_id.is_invoice()
                and not x.move_id.is_purchase_document()
            ):
                anglo_saxon_lines = line.anglo_saxon_line_ids
                current_prices = list(
                    {abs(price) for price in anglo_saxon_lines.mapped("price_unit")}
                )
                layers_value = sum(self.stock_valuation_layer_ids.mapped("value"))
                layers_quantity = sum(self.stock_valuation_layer_ids.mapped("quantity"))
                layers_price = (
                    abs(layers_value / layers_quantity) if layers_quantity != 0 else 0.0
                )
                if len(current_prices) == 1:
                    prices_difference = layers_price - current_prices[0]
                    if not float_is_zero(
                        prices_difference,
                        precision_rounding=self.company_id.currency_id.rounding,
                    ):
                        balance = line.quantity * prices_difference
                        (
                            journal_id,
                            _a,
                            _b,
                            _c,
                        ) = self._get_accounting_data_for_valuation()
                        move_date = self._context.get(
                            "force_period_date", fields.Date.context_today(self)
                        )
                        credit_line = line.anglo_saxon_line_ids.filtered(
                            lambda x: x.credit != 0
                        ).read(load="_classic_write")[0]
                        debit_line = line.anglo_saxon_line_ids.filtered(
                            lambda x: x.debit != 0
                        ).read(load="_classic_write")[0]
                        credit_line.update(
                            {
                                "anglo_saxon_adjusted_line_id": credit_line.get(
                                    "id", False
                                ),
                                "debit": balance < 0 and abs(balance),
                                "credit": balance > 0 and abs(balance),
                                "price_unit": prices_difference * -1,
                            }
                        )
                        debit_line.update(
                            {
                                "anglo_saxon_adjusted_line_id": credit_line.get(
                                    "id", False
                                ),
                                "debit": balance > 0 and abs(balance),
                                "credit": balance < 0 and abs(balance),
                                "price_unit": prices_difference * -1,
                            }
                        )
                        for column in MAGIC_COLUMNS:
                            if column in credit_line:
                                credit_line.pop(column)
                            if column in debit_line:
                                debit_line.pop(column)
                        move_data = {
                            "journal_id": journal_id,
                            "anglo_saxon_adjusted_move_id": line.move_id.id,
                            "date": move_date,
                            "line_ids": [
                                (0, 0, credit_line),
                                (0, 0, debit_line),
                            ],
                            "ref": _("COGS Alignment - %s")
                            % (line.move_id.display_name),
                            "stock_move_id": self.id,
                            "stock_valuation_layer_ids": [
                                (6, None, [self.stock_valuation_layer_ids.ids[0]])
                            ],
                            "move_type": "entry",
                        }
                        new_move = am_model.create(move_data)
                        new_move.action_post()

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done()
        for rec in self:
            rec._sync_anglo_saxon_values()
        return res
