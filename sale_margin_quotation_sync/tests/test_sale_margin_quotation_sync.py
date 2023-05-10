from odoo.tests import Form, TransactionCase
from odoo.tools import float_round


class TestSaleMarginQuotationSign(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product_ctg = self.env["product.category"].create(
            {
                "name": "test_product_ctg",
                "property_valuation": "real_time",
                "property_cost_method": "fifo",
            }
        )
        self.product1 = self.env["product.product"].create(
            {
                "name": "test_product1",
                "type": "product",
                "categ_id": self.product_ctg.id,
                "standard_price": 50.0,
            }
        )
        self.stock_location_id = self.env.ref("stock.stock_location_stock")
        self.stock_location_supplier_id = self.env.ref("stock.stock_location_suppliers")
        self.stock_picking_type_in = self.env.ref("stock.picking_type_in")
        self.vendor_partner = self.env["res.partner"].create({"name": "vendor"})
        self.customer_partner = self.env["res.partner"].create({"name": "customer"})

    def _create_receipt(self, product, qty, price_unit=10):
        return self.env["stock.picking"].create(
            {
                "name": self.stock_picking_type_in.sequence_id._next(),
                "partner_id": self.vendor_partner.id,
                "picking_type_id": self.stock_picking_type_in.id,
                "location_id": self.stock_location_supplier_id.id,
                "location_dest_id": self.stock_location_id.id,
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": product.name,
                            "product_id": product.id,
                            "product_uom": product.uom_id.id,
                            "product_uom_qty": qty,
                            "price_unit": price_unit,
                            "location_id": self.stock_location_supplier_id.id,
                            "location_dest_id": self.stock_location_id.id,
                            "procure_method": "make_to_stock",
                        },
                    )
                ],
            }
        )

    def _do_picking(self, picking, qty):
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

    def test_01_sale_margin_quotation(self):
        self.assertEqual(50, self.product1.standard_price)
        picking1 = self._create_receipt(self.product1, 10, 10)
        self._do_picking(picking1, 10)
        self.assertEqual(
            100, sum(picking1.mapped("move_lines.stock_valuation_layer_ids.value"))
        )
        picking2 = self._create_receipt(self.product1, 10, 15)
        self._do_picking(picking2, 10)
        self.assertEqual(
            150, sum(picking2.mapped("move_lines.stock_valuation_layer_ids.value"))
        )

        self.product1.standard_price = 50.0

        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.customer_partner
        with sale_form.order_line.new() as so_line:
            so_line.product_id = self.product1
            so_line.product_uom_qty = 15.0
        so = sale_form.save()
        self.assertEqual(10, so.order_line[0].purchase_price)
        so.action_confirm()

        # There are not move_ids yet should get standard price on confirm order
        self.assertEqual(50.0, so.order_line[0].purchase_price)

        self._do_picking(so.picking_ids[0], 15)
        price_unit = float_round(((10 * 10) + (5 * 15)) / 15, precision_digits=2)
        self.assertEqual(price_unit, so.order_line[0].purchase_price)
