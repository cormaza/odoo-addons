# Copyright 2021 Christopher Ormaza <mailto://chris.ormaza@.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import models


class UtmCampaign(models.Model):

    _name = "utm.campaign"
    _inherit = [
        "utm.campaign",
        "mail.thread",
        "mail.activity.mixin",
    ]
