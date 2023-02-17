from odoo import api, fields, models


class AccountMove(models.Model):

    _inherit = "account.move"

    anglo_saxon_adjusted_move_id = fields.Many2one(
        comodel_name="account.move", string="Anglo saxon adjusted entry", required=False
    )


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    anglo_saxon_adjusted_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Anglo saxon adjusted journal item",
        required=False,
    )
    anglo_saxon_adjusted_line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="anglo_saxon_adjusted_line_id",
        string="Anglo saxon adjusted lines",
        required=False,
    )

    anglo_saxon_line_ids = fields.Many2many(
        comodel_name="account.move.line", compute="_compute_anglo_saxon_line"
    )

    @api.depends()
    def _compute_anglo_saxon_line(self):
        for rec in self:
            anglo_saxon_line_ids = rec.move_id.line_ids.filtered(
                lambda x: x.is_anglo_saxon_line
                and x.product_id == rec.product_id
                and x.product_uom_id == rec.product_uom_id
                and x.quantity == rec.quantity
            )
            rec.anglo_saxon_line_ids = anglo_saxon_line_ids.ids
