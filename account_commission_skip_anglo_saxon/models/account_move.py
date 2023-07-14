from odoo import models


class AccountMove(models.Model):

    _inherit = "account.move"

    def filter_commission_applicable_lines(self):
        lines = super().filter_commission_applicable_lines()
        return lines.filtered(lambda x: not x.is_anglo_saxon_line)
