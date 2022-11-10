from odoo import api, models


class MailActivity(models.Model):

    _inherit = "mail.activity"

    @api.model
    def default_get(self, fields):
        values = super(MailActivity, self).default_get(fields)
        if self.env.context.get("default_res_model") == "crm.lead":
            lead = self.env["crm.lead"].browse(self.env.context.get("default_res_id"))
            values["user_id"] = lead.user_id.id
        return values

    def action_create_calendar_event(self):
        res = super(MailActivity, self).action_create_calendar_event()
        if res.get("context", {}).get("default_res_model") == "crm.lead":
            res.get("context", {}).update(
                {
                    "default_user_id": self.user_id.id,
                }
            )
        return res

    @api.onchange("activity_type_id", "res_model", "res_id")
    def _onchange_activity_type_id(self):
        lead_model = self.env["crm.lead"]
        if self.res_model == "crm.lead" and self.activity_type_id and self.res_id:
            current_lead = lead_model.browse(self.res_id)
            if self.activity_type_id.summary:
                self.summary = self.activity_type_id.summary
            self.date_deadline = self._calculate_date_deadline(self.activity_type_id)
            self.user_id = self.activity_type_id.default_user_id or current_lead.user_id
            if self.activity_type_id.default_note:
                self.note = self.activity_type_id.default_note
        else:
            return super(MailActivity, self)._onchange_activity_type_id()
