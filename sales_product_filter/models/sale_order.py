from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_id = fields.Many2one(context={"filter_products": True})


class ProductProduct(models.Model):

    _inherit = "product.product"

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        if self.env["sale.product.filter"].get_user_domains():
            args = self.env["sale.product.filter"].get_user_domains()
        return super(ProductProduct, self).name_search(name, args, operator, limit)

    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self.env["sale.product.filter"].get_user_domains():
            if not args:
                args = []
            args += self.env["sale.product.filter"].get_user_domains()
        return super(ProductProduct, self).search(args, offset, limit, order, count)


class ProductTemplate(models.Model):

    _inherit = "product.template"

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        if self.env["sale.product.filter"].get_user_domains():
            args = self.env["sale.product.filter"].get_user_domains()
        return super(ProductTemplate, self).name_search(name, args, operator, limit)

    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self.env["sale.product.filter"].get_user_domains():
            if not args:
                args = []
            args += self.env["sale.product.filter"].get_user_domains()
        return super(ProductTemplate, self).search(args, offset, limit, order, count)
