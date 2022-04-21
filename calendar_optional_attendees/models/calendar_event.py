from odoo import fields, models


class CalendarEvent(models.Model):

    _inherit = "calendar.event"

    optional_create_attendees = fields.Boolean(
        string="Create attendees?",
        default=True,
    )

    def create_attendees(self):
        return super(
            CalendarEvent, self.filtered(lambda x: x.optional_create_attendees)
        ).create_attendees()

    def write(self, values):
        res = super(CalendarEvent, self).write(values)
        if "optional_create_attendees" in values and values.get(
            "optional_create_attendees"
        ):
            for meeting in self:
                meeting.with_context(dont_notify=True).create_attendees()
        return res
