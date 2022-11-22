# Copyright 2022 Christopher Ormaza <mailto://chris.ormaza@.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestSaleRates(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env.ref("base.res_partner_3")
        cls.product = cls.env.ref("product.product_product_5")
        cls.product.invoice_policy = "order"
        cls.product_service = cls.env.ref("product.product_product_1")
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.warehouse.lot_stock_id, 100
        )

    def test_sale_rates_invoiced(self):
        sale_order_form = Form(self.env["sale.order"])
        sale_order_form.partner_id = self.partner
        with sale_order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 10
            line_form.save()
        sale_order_1 = sale_order_form.save()
        sale_order_1.action_confirm()
        self.assertEqual(sale_order_1.invoiced_rate, 0)
        payment = (
            self.env["sale.advance.payment.inv"]
            .with_context(active_ids=sale_order_1.ids, active_model="sale.order")
            .create({"advance_payment_method": "delivered"})
        )
        payment.create_invoices()
        self.assertEqual(sale_order_1.invoiced_rate, 100.0)
        # With lower invoiced rate is modified
        move_form = Form(sale_order_1.invoice_ids[0])
        with move_form.invoice_line_ids.edit(0) as line_form:
            line_form.quantity /= 2.0
        with move_form.invoice_line_ids.edit(1) as line_form:
            line_form.quantity /= 2.0
        move_form.save()
        self.assertEqual(sale_order_1.invoiced_rate, 50.0)
        # With bigger invoiced always get 100.0
        move_form = Form(sale_order_1.invoice_ids[0])
        with move_form.invoice_line_ids.edit(0) as line_form:
            line_form.quantity += 100.0
        with move_form.invoice_line_ids.edit(1) as line_form:
            line_form.quantity += 100.0
        move_form.save()
        self.assertEqual(sale_order_1.invoiced_rate, 100.0)
        # When unlink invoice lines related, recalc invoiced_rate
        sale_order_1.invoice_ids.unlink()
        self.assertEqual(sale_order_1.invoiced_rate, 0.0)
        sale_order_1.force_full_rated = True
        self.assertEqual(sale_order_1.invoiced_rate, 100.0)
        # With Credit Notes
        sale_order_1.force_full_rated = False
        payment = (
            self.env["sale.advance.payment.inv"]
            .with_context(active_ids=sale_order_1.ids, active_model="sale.order")
            .create({"advance_payment_method": "delivered"})
        )
        payment.create_invoices()
        sale_order_1.invoice_ids.action_post()
        self.assertEqual(sale_order_1.invoiced_rate, 100.0)
        move_reversal = (
            self.env["account.move.reversal"]
            .with_context(
                active_model="account.move", active_ids=sale_order_1.invoice_ids.ids
            )
            .create(
                {
                    "journal_id": sale_order_1.invoice_ids.mapped("journal_id").id,
                    "date": fields.Date.today(),
                    "reason": "no reason",
                    "refund_method": "refund",
                }
            )
        )
        reversal = move_reversal.reverse_moves()
        reverse_move = self.env["account.move"].browse(reversal["res_id"])
        self.assertEqual(sum(sale_order_1.order_line.mapped("qty_invoiced")), 0)
        self.assertEqual(sale_order_1.invoiced_rate, 0)
        # Removing lines from credit note
        move_form = Form(reverse_move)
        move_form.invoice_line_ids.remove(0)
        move_form.save()
        self.assertEqual(sum(sale_order_1.order_line.mapped("qty_invoiced")), 10)
        self.assertEqual(sale_order_1.invoiced_rate, 50)
        sale_order_1.write({"force_full_rated": True})
        self.assertEqual(sale_order_1.invoiced_rate, 100)

    def _do_picking(self, picking, date, qty):
        """Do picking with only one move on the given date."""
        picking.action_confirm()
        picking.action_assign()
        picking.move_lines.quantity_done = qty
        res = picking.button_validate()
        if isinstance(res, dict) and res:
            backorder_wiz_id = res["res_id"]
            backorder_wiz = self.env["stock.backorder.confirmation"].browse(
                [backorder_wiz_id]
            )
            backorder_wiz.process()
        return True

    def _make_picking_return(self, picking, quantity):
        return_form = Form(
            self.env["stock.return.picking"].with_context(
                active_id=picking.id,
                active_ids=picking.ids,
            )
        )
        return_form.picking_id = picking
        for i in range(len(return_form.product_return_moves)):
            with return_form.product_return_moves.edit(i) as return_line:
                return_line.quantity = quantity
        return_wizard = return_form.save()
        action = return_wizard.create_returns()
        return_picking = self.env["stock.picking"].browse(action.get("res_id"))
        self._do_picking(return_picking, fields.Datetime.now(), quantity)
        return return_picking

    def test_sale_rates_shipped(self):
        sale_order_form = Form(self.env["sale.order"])
        sale_order_form.partner_id = self.partner
        with sale_order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 10
            line_form.save()
        sale_order_1 = sale_order_form.save()
        sale_order_1.action_confirm()
        self.assertEqual(sale_order_1.shipped_rate, 0)
        out_picking = sale_order_1.picking_ids
        self._do_picking(out_picking, fields.Datetime.now(), 10)
        self.assertEqual(sale_order_1.shipped_rate, 100.0)
        self._make_picking_return(out_picking, 3)
        self.assertEqual(sale_order_1.shipped_rate, 70.0)
        sale_order_1.write({"force_full_rated": True})
        self.assertEqual(sale_order_1.shipped_rate, 100)
