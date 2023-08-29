from odoo.tests.common import TransactionCase


class TestHrEmployeeSearchByIdentification(TransactionCase):
    def setUp(self):
        super().setUp()
        self.employee = self.env["hr.employee"].create(
            {"name": "Employee Name", "identification_id": "987654321"}
        )

    def test_employee_search_by_identification_number(self):
        names_find = self.env["hr.employee"].name_search("98765")
        for employee_id, name in names_find:
            self.assertEqual(self.employee.id, employee_id)
            self.assertEqual(self.employee.display_name, name)
