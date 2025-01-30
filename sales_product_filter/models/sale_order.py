from odoo import api, fields, models
from odoo.osv.expression import AND


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


def add_product_variant_to_domain(args):
    new_args = []
    for arg in args:
        if isinstance(arg, (list, tuple)):
            new_args.append((f"product_variant_ids.{arg[0]}", arg[1], arg[2]))
        else:
            new_args.append(arg)
    return new_args


class ProductTemplate(models.Model):

    _inherit = "product.template"

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        if self.env["sale.product.filter"].get_user_domains():
            args = self.env["sale.product.filter"].get_user_domains()
            args = add_product_variant_to_domain(args)
        return super(ProductTemplate, self).name_search(name, args, operator, limit)

    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self.env["sale.product.filter"].get_user_domains():
            if not args:
                args = []
            domain = self.env["sale.product.filter"].get_user_domains()
            domain = add_product_variant_to_domain(domain)
            if domain:
                args = AND([args, domain])
        return super(ProductTemplate, self).search(args, offset, limit, order, count)
