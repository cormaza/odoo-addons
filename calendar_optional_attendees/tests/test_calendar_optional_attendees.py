from odoo import fields
from odoo.tests.common import Form, TransactionCase


class TestCalendarOptionalAttendees(TransactionCase):
    def setUp(self):
        super().setUp()
        self.CalendarEvent = self.env["calendar.event"]
        self.partner_1 = self.env.ref("base.res_partner_1")
        self.partner_2 = self.env.ref("base.res_partner_2")
        self.partner_3 = self.env.ref("base.res_partner_3")

    def test_01_optional_attendees(self):
        new_event_form = Form(self.CalendarEvent)
        new_event_form.name = "Test Event"
        new_event_form.start_datetime = fields.Datetime.now()
        new_event_form.partner_ids.add(self.partner_1)
        new_event_form.partner_ids.add(self.partner_2)
        new_event_form.partner_ids.add(self.partner_3)
        new_meeting = new_event_form.save()
        self.assertEqual(len(new_meeting.attendee_ids), 3)

        new_event_form = Form(self.CalendarEvent)
        new_event_form.name = "Test Event"
        new_event_form.start_datetime = fields.Datetime.now()
        new_event_form.partner_ids.add(self.partner_1)
        new_event_form.partner_ids.add(self.partner_2)
        new_event_form.partner_ids.add(self.partner_3)
        new_event_form.optional_create_attendees = False
        new_meeting = new_event_form.save()
        self.assertEqual(len(new_meeting.attendee_ids), 0)

        new_event_form = Form(self.CalendarEvent)
        new_event_form.name = "Test Event"
        new_event_form.start_datetime = fields.Datetime.now()
        new_event_form.partner_ids.add(self.partner_1)
        new_event_form.partner_ids.add(self.partner_2)
        new_meeting = new_event_form.save()
        self.assertEqual(len(new_meeting.attendee_ids), 2)
        new_meeting.write({"partner_ids": [(4, self.partner_3.id)]})
        self.assertEqual(len(new_meeting.attendee_ids), 3)

        new_event_form = Form(self.CalendarEvent)
        new_event_form.name = "Test Event"
        new_event_form.start_datetime = fields.Datetime.now()
        new_event_form.partner_ids.add(self.partner_1)
        new_event_form.partner_ids.add(self.partner_2)
        new_event_form.optional_create_attendees = False
        new_meeting = new_event_form.save()
        self.assertEqual(len(new_meeting.attendee_ids), 0)
        new_meeting.write({"partner_ids": [(4, self.partner_3.id)]})
        self.assertEqual(len(new_meeting.attendee_ids), 0)

        new_event_form = Form(self.CalendarEvent)
        new_event_form.name = "Test Event"
        new_event_form.start_datetime = fields.Datetime.now()
        new_event_form.partner_ids.add(self.partner_1)
        new_event_form.partner_ids.add(self.partner_2)
        new_event_form.optional_create_attendees = False
        new_meeting = new_event_form.save()
        self.assertEqual(len(new_meeting.attendee_ids), 0)
        new_meeting.write({"optional_create_attendees": True})
        self.assertEqual(len(new_meeting.attendee_ids), 2)
        new_meeting.write({"partner_ids": [(4, self.partner_3.id)]})
        self.assertEqual(len(new_meeting.attendee_ids), 3)
