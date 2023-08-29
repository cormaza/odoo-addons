from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestHrContractAvoidOverlap(TransactionCase):
    def setUp(self):
        super().setUp()
        self.employee = self.env["hr.employee"].create(
            {
                "name": "New Employee",
            }
        )
        self.contract = self.env["hr.contract"].create(
            {
                "name": "New Contract",
                "employee_id": self.employee.id,
                "date_start": "2023-01-01",
                "wage": 100.0,
            }
        )

    def test_01_ending_date(self):
        with self.assertRaises(ValidationError):
            self.contract.write({"date_end": "2022-12-31"})

    def test_02_avoid_overlap(self):
        self.contract.write({"date_end": False})
        with self.assertRaises(ValidationError):
            self.env["hr.contract"].create(
                {
                    "name": "New Contract",
                    "employee_id": self.employee.id,
                    "date_start": "2022-01-01",
                    "wage": 100.0,
                }
            )
        with self.assertRaises(ValidationError):
            self.env["hr.contract"].create(
                {
                    "name": "New Contract",
                    "employee_id": self.employee.id,
                    "date_start": "2023-01-02",
                    "wage": 100.0,
                }
            )

    def test_03_avoid_overlap(self):
        self.contract.write({"date_end": "2023-12-31"})
        with self.assertRaises(ValidationError):
            self.env["hr.contract"].create(
                {
                    "name": "New Contract",
                    "employee_id": self.employee.id,
                    "date_start": "2022-01-01",
                    "wage": 100.0,
                }
            )

        with self.assertRaises(ValidationError):
            self.env["hr.contract"].create(
                {
                    "name": "New Contract",
                    "employee_id": self.employee.id,
                    "date_start": "2022-01-01",
                    "date_end": "2023-05-01",
                    "wage": 100.0,
                }
            )

        with self.assertRaises(ValidationError):
            self.env["hr.contract"].create(
                {
                    "name": "New Contract",
                    "employee_id": self.employee.id,
                    "date_start": "2022-01-01",
                    "date_end": "2024-12-31",
                    "wage": 100.0,
                }
            )

        with self.assertRaises(ValidationError):
            self.env["hr.contract"].create(
                {
                    "name": "New Contract",
                    "employee_id": self.employee.id,
                    "date_start": "2023-05-01",
                    "wage": 100.0,
                }
            )

        with self.assertRaises(ValidationError):
            self.env["hr.contract"].create(
                {
                    "name": "New Contract",
                    "employee_id": self.employee.id,
                    "date_start": "2023-05-01",
                    "date_end": "2024-12-31",
                    "wage": 100.0,
                }
            )

        new_contract = self.env["hr.contract"].create(
            {
                "name": "New Contract",
                "employee_id": self.employee.id,
                "date_start": "2024-01-01",
                "wage": 100.0,
            }
        )
        self.assertTrue(new_contract.exists())

        with self.assertRaises(ValidationError):
            self.contract.write({"date_end": False})

        new_contract.unlink()
        self.assertFalse(new_contract.exists())

        new_contract = self.env["hr.contract"].create(
            {
                "name": "New Contract",
                "employee_id": self.employee.id,
                "date_start": "2022-01-01",
                "date_end": "2022-12-31",
                "wage": 100.0,
            }
        )
        self.assertTrue(new_contract.exists())

        with self.assertRaises(ValidationError):
            self.contract.write({"date_start": "2022-05-01"})

        new_contract.unlink()
        self.assertFalse(new_contract.exists())
