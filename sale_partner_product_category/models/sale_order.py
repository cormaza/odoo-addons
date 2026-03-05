from odoo import _, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _sync_partner_category(self):
        category_type = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sale_partner_product_category.category_type", default="leaf")
        )
        for order in self:
            if not order.partner_id:
                continue

            # Collect unique public category names from products in this order line
            public_categs = order.order_line.mapped("product_id.public_categ_ids")
            if not public_categs:
                continue

            category_names = set()
            for categ in public_categs:
                if category_type == "root":
                    root_categ = categ
                    while root_categ.parent_id:
                        root_categ = root_categ.parent_id
                    category_names.add(root_categ.name)
                else:
                    category_names.add(categ.name)

            partner_categories_to_add = self.env["res.partner.category"]

            for name in category_names:
                # Search by exact name
                partner_category = self.env["res.partner.category"].search(
                    [("name", "=", name)], limit=1
                )

                if not partner_category:
                    # Create if it doesn't exist
                    partner_category = self.env["res.partner.category"].create(
                        {"name": name}
                    )

                partner_categories_to_add |= partner_category

            if partner_categories_to_add:
                # Add categories without replacing existing ones using command 4
                commands = [(4, cat.id) for cat in partner_categories_to_add]
                order.partner_id.sudo().write({"category_id": commands})

                # Deja un mensaje en el chatter del pedido
                tag_names = ", ".join(partner_categories_to_add.mapped("name"))
                order.message_post(
                    body=_(
                        "Etiquetas de cliente sincronizadas "
                        f"desde los productos de este pedido: <b>{tag_names}</b>"
                    )
                )

    def action_confirm(self):
        res = super().action_confirm()
        self._sync_partner_category()
        return res

    def action_quotation_send(self):
        res = super().action_quotation_send()
        self._sync_partner_category()
        return res
