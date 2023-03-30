from odoo import _, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    website_hide_price = fields.Boolean(string="Hide prices on website")
    website_hide_price_message = fields.Text(
        string="Hidden price message",
        help="When the price is hidden on the website we can give the customer"
        "some tips on how to find it out.",
        translate=True,
    )

    def _search_render_results(self, fetch_fields, mapping, icon, limit):
        """Hide price on the search bar results"""
        results_data = super()._search_render_results(
            fetch_fields, mapping, icon, limit
        )
        for product, data in zip(self, results_data):
            if product.website_hide_price and product.website_published:
                data.update(
                    {
                        "price": "<a href='/contactus?subject=%(contact_name)s&description=%(contact_description)s' target='_blank'><span>%(product_name)s</span></a>"  # noqa: B950
                        % {
                            "contact_name": product.display_name,
                            "contact_description": _(
                                "Can you give more information about this product %(product_name)s"  # noqa: B950
                            )
                            % {"product_name": product.display_name},
                            "product_name": product.website_hide_price_message or "",
                        },
                        "list_price": "",
                    }
                )
        return results_data
