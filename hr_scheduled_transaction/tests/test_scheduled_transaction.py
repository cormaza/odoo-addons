from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class ScheduledTransactionTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.input_type_model = cls.env["hr.payslip.input.type"]
        cls.category_model = cls.env["hr.salary.rule.category"]
        cls.employee_model = cls.env["hr.employee"]
        cls.contract_model = cls.env["hr.contract"]
        cls.payslip_model = cls.env["hr.payslip"]
        cls.scheduled_transaction_model = cls.env["hr.scheduled.transaction"]
        cls.fixed_transaction_model = cls.env["hr.contract.fixed.inputs"]
        cls.category_egre = cls.category_model.search(
            [("code", "=", "EGRE")], limit=1
        ) or cls.category_model.create(
            {
                "name": "EGRE",
                "code": "EGRE",
            }
        )
        cls.input_type_id = cls.input_type_model.create(
            {
                "name": "Extra Input",
                "code": "ExtraInput",
                "category_id": cls.category_model.search([], limit=1).id,
            }
        )
        cls.output_type_id = cls.input_type_model.create(
            {
                "name": "Extra Output",
                "code": "ExtraOutput",
                "category_id": cls.category_egre.id,
            }
        )
        cls.employee_id = cls.employee_model.create(
            {
                "name": "Test Employee",
            }
        )
        cls.contract_id = cls.contract_model.create(
            {
                "name": cls.employee_id.display_name,
                "employee_id": cls.employee_id.id,
                "date_start": "2021-01-01",
                "date_end": "2021-12-31",
                "wage": 600.0,
                "state": "open",
                "kanban_state": "normal",
            }
        )

    def test_scheduled_transaction_creation(self):
        with self.assertRaises(UserError):
            self.scheduled_transaction_model.create(
                {
                    "employee_id": self.employee_id.id,
                    "date": fields.Date.today(),
                    "payslip_input_type_id": self.input_type_id.id,
                    "amount": -100.0,
                }
            )
        new_transaction = self.scheduled_transaction_model.create(
            {
                "employee_id": self.employee_id.id,
                "date": fields.Date.today(),
                "payslip_input_type_id": self.output_type_id.id,
                "amount": 100.0,
            }
        )
        self.assertEqual(new_transaction.transaction_type, "output")
        new_transaction = self.scheduled_transaction_model.create(
            {
                "employee_id": self.employee_id.id,
                "date": fields.Date.today(),
                "payslip_input_type_id": self.input_type_id.id,
                "amount": 100.0,
            }
        )
        self.assertEqual(new_transaction.transaction_type, "input")

    def test_contract(self):
        with self.assertRaises(UserError):
            self.fixed_transaction_model(
                {
                    "contract_id": self.contract_id.id,
                    "day_to_apply": 31,
                    "payslip_input_type_id": self.input_type_id.id,
                    "amount": -100.0,
                }
            )
        with self.assertRaises(UserError):
            self.fixed_transaction_model(
                {
                    "contract_id": self.contract_id.id,
                    "day_to_apply": 40,
                    "payslip_input_type_id": self.input_type_id.id,
                    "amount": 100.0,
                }
            )
        with self.assertRaises(UserError):
            self.fixed_transaction_model(
                {
                    "contract_id": self.contract_id.id,
                    "day_to_apply": 0,
                    "payslip_input_type_id": self.input_type_id.id,
                    "amount": 100.0,
                }
            )
        with self.assertRaises(UserError):
            self.fixed_transaction_model(
                {
                    "contract_id": self.contract_id.id,
                    "start_date": self.contract_id.date_start - relativedelta(days=1),
                    "day_to_apply": 31,
                    "payslip_input_type_id": self.input_type_id.id,
                    "amount": 100.0,
                }
            )
        with self.assertRaises(UserError):
            self.fixed_transaction_model(
                {
                    "contract_id": self.contract_id.id,
                    "start_date": self.contract_id.date_end + relativedelta(days=1),
                    "day_to_apply": 31,
                    "payslip_input_type_id": self.input_type_id.id,
                    "amount": 100.0,
                }
            )
        new_transaction = self.fixed_transaction_model.create(
            {
                "contract_id": self.contract_id.id,
                "day_to_apply": 0,
                "payslip_input_type_id": self.output_type_id.id,
                "amount": 100.0,
            }
        )
        self.assertEqual(new_transaction.transaction_type, "output")
        new_transaction = self.fixed_transaction_model.create(
            {
                "contract_id": self.contract_id.id,
                "day_to_apply": 0,
                "payslip_input_type_id": self.input_type_id.id,
                "amount": 100.0,
            }
        )
        self.assertEqual(new_transaction.transaction_type, "input")

    def test_payslip(self):
        pass
