from odoo import fields
from odoo.tests import Form, TransactionCase


class TestAccountPickingAngloSaxonSync(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product_uom = self.env.ref("uom.product_uom_unit")
        self.company = self.env.ref("base.main_company")
        self.company.write({"anglo_saxon_accounting": True})
        self.stock_picking_type_out = self.env.ref("stock.picking_type_out")
        self.stock_picking_type_in = self.env.ref("stock.picking_type_in")
        self.stock_location_id = self.env.ref("stock.stock_location_stock")
        self.stock_location_customer_id = self.env.ref("stock.stock_location_customers")
        self.stock_location_supplier_id = self.env.ref("stock.stock_location_suppliers")
        self.supplier = self.env["res.partner"].create({"name": "Test supplier"})
        self.customer = self.env["res.partner"].create({"name": "Test customer"})

        self.fifo_product = self.env.ref(
            "account_picking_anglo_saxon_sync.fifo_product_demo"
        )
        self.avg_product = self.env.ref(
            "account_picking_anglo_saxon_sync.avg_product_demo"
        )

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

    def _make_sale_order(self, products, quantity, price_unit=False):
        so = Form(self.env["sale.order"])
        so.partner_id = self.customer
        for product in products:
            with so.order_line.new() as sale_line:
                sale_line.product_id = product
                sale_line.product_uom_qty = quantity
                sale_line.price_unit = price_unit or product.list_price
        so = so.save()
        so.action_confirm()
        return so

    def _make_purchase_order(self, product, quantity, price_unit, supplier=False):
        purchase_form = Form(self.env["purchase.order"])
        purchase_form.partner_id = supplier or self.supplier
        with purchase_form.order_line.new() as purchase_line:
            purchase_line.product_id = product
            purchase_line.product_qty = quantity
            purchase_line.price_unit = price_unit
        purchase = purchase_form.save()
        purchase.button_confirm()
        return purchase

    def test_01_invoice_before_picking(self):
        self.assertEqual(self.fifo_product.standard_price, 10.0)
        po1 = self._make_purchase_order(self.fifo_product, 10.0, 15.0)
        self._do_picking(po1.picking_ids, fields.Datetime.now(), 10.0)
        self.assertEqual(self.fifo_product.standard_price, 15.0)

        self.assertEqual(self.avg_product.standard_price, 10.0)
        po2 = self._make_purchase_order(self.avg_product, 10.0, 15.0)
        self._do_picking(po2.picking_ids, fields.Datetime.now(), 10.0)
        self.assertEqual(self.avg_product.standard_price, 15.0)

        so1 = self._make_sale_order(self.fifo_product + self.avg_product, 1.0)
        self._do_picking(so1.picking_ids, fields.Datetime.now(), 1.0)

        fifo_layers = so1.picking_ids.move_lines.filtered(
            lambda x: x.product_id == self.fifo_product
        ).stock_valuation_layer_ids
        self.assertEqual(sum(fifo_layers.mapped("value")), -15.0)
        avg_layers = so1.picking_ids.move_lines.filtered(
            lambda x: x.product_id == self.avg_product
        ).stock_valuation_layer_ids
        self.assertEqual(sum(avg_layers.mapped("value")), -15.0)

        moves = so1._create_invoices()
        moves.action_post()

        fifo_invoice_lines = so1.order_line.filtered(
            lambda x: x.product_id == self.fifo_product
        ).invoice_lines
        fifo_invoice_lines._compute_anglo_saxon_line()
        anglo_saxon_lines_fifo_product = fifo_invoice_lines.anglo_saxon_line_ids
        fifo_product_price = (
            anglo_saxon_lines_fifo_product
            and abs(list(set(anglo_saxon_lines_fifo_product.mapped("price_unit")))[0])
            or 0.0
        )
        self.assertEqual(fifo_product_price, 15.0)

        avg_invoice_lines = so1.order_line.filtered(
            lambda x: x.product_id == self.avg_product
        ).invoice_lines
        avg_invoice_lines._compute_anglo_saxon_line()
        anglo_saxon_lines_avg_product = avg_invoice_lines.anglo_saxon_line_ids
        avg_product_price = (
            anglo_saxon_lines_avg_product
            and abs(list(set(anglo_saxon_lines_avg_product.mapped("price_unit")))[0])
            or 0.0
        )
        self.assertEqual(avg_product_price, 15.0)

        so2 = self._make_sale_order(self.fifo_product + self.avg_product, 1.0)

        moves = so2._create_invoices()
        moves.action_post()

        fifo_invoice_lines = so2.order_line.filtered(
            lambda x: x.product_id == self.fifo_product
        ).invoice_lines
        fifo_invoice_lines._compute_anglo_saxon_line()
        anglo_saxon_lines_fifo_product = fifo_invoice_lines.anglo_saxon_line_ids
        fifo_product_price = (
            anglo_saxon_lines_fifo_product
            and abs(list(set(anglo_saxon_lines_fifo_product.mapped("price_unit")))[0])
            or 0.0
        )
        self.assertEqual(fifo_product_price, 15.0)

        avg_invoice_lines = so2.order_line.filtered(
            lambda x: x.product_id == self.avg_product
        ).invoice_lines
        avg_invoice_lines._compute_anglo_saxon_line()
        anglo_saxon_lines_avg_product = avg_invoice_lines.anglo_saxon_line_ids
        avg_product_price = (
            anglo_saxon_lines_avg_product
            and abs(list(set(anglo_saxon_lines_avg_product.mapped("price_unit")))[0])
            or 0.0
        )
        self.assertEqual(avg_product_price, 15.0)

        po1 = self._make_purchase_order(self.fifo_product, 10.0, 20.0)
        self._do_picking(po1.picking_ids, fields.Datetime.now(), 10.0)
        self.assertEqual(self.fifo_product.standard_price, 15.0)

        po2 = self._make_purchase_order(self.avg_product, 10.0, 20.0)
        self._do_picking(po2.picking_ids, fields.Datetime.now(), 10.0)
        # 9 * 15 = 135, 10 * 20 = 200, 335 / 19 = 17.67
        self.assertEqual(self.avg_product.standard_price, 17.63)

        self._do_picking(so2.picking_ids, fields.Datetime.now(), 1.0)

        fifo_invoice_lines = so2.order_line.filtered(
            lambda x: x.product_id == self.fifo_product
        ).invoice_lines
        fifo_invoice_lines._compute_anglo_saxon_line()
        anglo_saxon_lines_fifo_product = fifo_invoice_lines.anglo_saxon_line_ids
        fifo_product_price = (
            anglo_saxon_lines_fifo_product
            and abs(list(set(anglo_saxon_lines_fifo_product.mapped("price_unit")))[0])
            or 0.0
        )
        self.assertEqual(fifo_product_price, 15.0)

        avg_invoice_lines = so2.order_line.filtered(
            lambda x: x.product_id == self.avg_product
        ).invoice_lines
        avg_invoice_lines._compute_anglo_saxon_line()
        anglo_saxon_lines_avg_product = avg_invoice_lines.anglo_saxon_line_ids
        avg_product_price = (
            anglo_saxon_lines_avg_product
            and abs(list(set(anglo_saxon_lines_avg_product.mapped("price_unit")))[0])
            or 0.0
        )
        self.assertEqual(avg_product_price, 15)
        adjusted_fifo_lines = self.env["account.move.line"].search(
            [
                (
                    "anglo_saxon_adjusted_line_id",
                    "in",
                    fifo_invoice_lines.anglo_saxon_line_ids.ids,
                )
            ]
        )
        adjusted_avg_lines = self.env["account.move.line"].search(
            [
                (
                    "anglo_saxon_adjusted_line_id",
                    "in",
                    avg_invoice_lines.anglo_saxon_line_ids.ids,
                )
            ]
        )
        self.assertFalse(bool(adjusted_fifo_lines))
        self.assertTrue(bool(adjusted_avg_lines))
        avg_product_price += (
            adjusted_avg_lines
            and abs(list(set(adjusted_avg_lines.mapped("price_unit")))[0])
            or 0.0
        )
        avg_debit = sum(
            (avg_invoice_lines.anglo_saxon_line_ids + adjusted_avg_lines).mapped(
                "debit"
            )
        )
        avg_credit = sum(
            (avg_invoice_lines.anglo_saxon_line_ids + adjusted_avg_lines).mapped(
                "credit"
            )
        )
        self.assertEqual(avg_product_price, 17.63)
        self.assertEqual(avg_debit, 17.63)
        self.assertEqual(avg_credit, 17.63)
