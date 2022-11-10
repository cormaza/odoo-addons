from odoo import api, fields, models
from odoo.fields import Command


class CalendarEvent(models.Model):

    _inherit = "calendar.event"

    optional_create_attendees = fields.Boolean(
        string="Create attendees?",
        default=True,
    )

    def _attendees_values(self, partner_commands):
        if not self.env.context.get("notify"):
            return []
        if (
            "notify" in self.env.context
            and self.env.context.get("notify")
            and self.env.context.get("partners_to_recreate_attendee", [])
        ):
            res = []
            if self.env.context.get("partners_to_recreate_attendee", []):
                res += [
                    [0, 0, dict(partner_id=partner_id)]
                    for partner_id in self.env.context.get(
                        "partners_to_recreate_attendee", []
                    )
                ]
            return res
        return super()._attendees_values(partner_commands)

    @api.model_create_multi
    def create(self, values):
        recs = self.browse()
        for val in values:
            notify = False
            if val.get("optional_create_attendees", False):
                notify = True
            recs |= super(CalendarEvent, self.with_context(notify=notify)).create(
                values
            )
        return recs

    def write(self, values):
        for rec in self:
            partner_model = self.env["res.partner"]
            notify = rec.optional_create_attendees
            partners_to_recreate_attendee = []
            if "optional_create_attendees" in values:
                notify = values.get("optional_create_attendees")
                if values.get("optional_create_attendees"):
                    partner_ids = rec.partner_ids.ids + values.get("partner_ids", [])
                    not_attendee_partners = partner_ids and partner_model.browse(
                        partner_ids
                    ).filtered(
                        lambda x: x.id not in rec.attendee_ids.mapped("partner_id").ids
                    )
                    values["partner_ids"] = values.get("partner_ids", [])
                    if not_attendee_partners:
                        for partner in not_attendee_partners:
                            partners_to_recreate_attendee.append(partner.id)
                            values["partner_ids"] += [Command.link(partner.id)]
            super(
                CalendarEvent,
                rec.with_context(
                    notify=notify,
                    partners_to_recreate_attendee=partners_to_recreate_attendee,
                ),
            ).write(values)
        return True
