from odoo.tests.common import TransactionCase


class TestSaleOrderTagSync(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Create a public product category
        cls.public_category = cls.env["product.public.category"].create(
            {
                "name": "Test Public Category",
            }
        )

        # Create a product with the public category
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "public_categ_ids": [(4, cls.public_category.id)],
                "list_price": 100.0,
            }
        )

        # Create a partner with no initial categories
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        # Create a partner category that already exists to test matching
        cls.existing_partner_category = cls.env["res.partner.category"].create(
            {
                "name": "Existing Public Category",
            }
        )

        # Product with a different category that has a matching partner category
        cls.public_category_2 = cls.env["product.public.category"].create(
            {
                "name": "Existing Public Category",
            }
        )
        cls.product_existing = cls.env["product.product"].create(
            {
                "name": "Test Product Existing",
                "public_categ_ids": [(4, cls.public_category_2.id)],
                "list_price": 50.0,
            }
        )

    def test_sale_order_confirm_syncs_tags(self):
        # Create a sale order
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1.0,
                            "price_unit": 100.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_existing.id,
                            "product_uom_qty": 1.0,
                            "price_unit": 50.0,
                        },
                    ),
                ],
            }
        )

        # Ensure partner has no tags initially
        self.assertFalse(self.partner.category_id)

        # Confirm the sale order
        sale_order.action_confirm()

        # Check that the partner now has the expected tags
        tag_names = self.partner.category_id.mapped("name")

        self.assertIn("Test Public Category", tag_names)
        self.assertIn("Existing Public Category", tag_names)

        # Ensure the existing tag was reused, not duplicated
        existing_tags = self.env["res.partner.category"].search(
            [("name", "=", "Existing Public Category")]
        )
        self.assertEqual(len(existing_tags), 1)

        # Verify a message was posted in the chatter
        messages = self.env["mail.message"].search(
            [
                ("model", "=", "sale.order"),
                ("res_id", "=", sale_order.id),
                ("body", "ilike", "Etiquetas de cliente sincronizadas"),
            ]
        )
        self.assertTrue(
            messages, "A chatter message should have been posted on the sale order."
        )
