from odoo.tests import tagged

from odoo.addons.account_commission.tests.test_account_commission import (
    TestAccountCommission,
)


@tagged("-at_install", "post_install")
class TestAccountCommisionSkipAngloSaxon(TestAccountCommission):
    def setUp(self):
        super().setUp()
        self.company.anglo_saxon_accounting = True
        self.stock_account_product_categ = self.env["product.category"].create(
            {
                "name": "Test category",
                "property_valuation": "real_time",
                "property_cost_method": "fifo",
            }
        )
        self.product.write(
            {
                "categ_id": self.stock_account_product_categ.id,
                "type": "product",
                "standard_price": 10.0,
            }
        )

    def test_skip_anglo_saxon_commission_lines(self):
        new_invoice = self._process_invoice_and_settle(
            self.agent_quaterly,
            self.env.ref("commission.demo_commission"),
            1,
        )

        self.assertTrue(
            bool(new_invoice.line_ids.filtered(lambda x: x.is_anglo_saxon_line))
        )

        commission_lines_created = self.env["account.invoice.line.agent"].search(
            [("invoice_id", "=", new_invoice.id)]
        )
        self.assertEqual(len(commission_lines_created), 1)
