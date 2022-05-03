from odoo import api, fields, models


class CalendarEvent(models.Model):

    _inherit = "calendar.event"

    @api.model
    def _default_partners(self):
        user_model = self.env["res.users"]
        partners = super(CalendarEvent, self)._default_partners()
        active_id = self._context.get("default_res_id")
        if (
            self._context.get("default_res_model") == "crm.lead"
            and active_id
            and self.env.context.get("default_user_id")
        ):
            user = user_model.browse(self.env.context.get("default_user_id"))
            if self.env.user.partner_id != user.partner_id:
                partners -= self.env.user.partner_id
                partners |= user.partner_id
        return partners

    partner_ids = fields.Many2many(default=_default_partners)
