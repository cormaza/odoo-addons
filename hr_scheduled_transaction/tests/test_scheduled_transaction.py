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
        cls.struct_model = cls.env["hr.payroll.structure"]
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
        cls.current_country = cls.env.ref("base.ec")
        cls.structure_type = cls.env["hr.payroll.structure.type"].create(
            {
                "name": "Test - Developer",
            }
        )
        cls.struct_1 = cls.struct_model.create(
            {
                "name": "Struct 1",
                "type_id": cls.structure_type.id,
                "country_id": cls.current_country.id,
            }
        )
        cls.struct_2 = cls.struct_model.create(
            {
                "name": "Struct 2",
                "type_id": cls.structure_type.id,
                "country_id": cls.current_country.id,
            }
        )
        cls.struct_3 = cls.struct_model.create(
            {
                "name": "Struct 3",
                "type_id": cls.structure_type.id,
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
            self.fixed_transaction_model.create(
                {
                    "contract_id": self.contract_id.id,
                    "day_to_apply": 31,
                    "payslip_input_type_id": self.input_type_id.id,
                    "amount": -100.0,
                }
            )
        with self.assertRaises(UserError):
            self.fixed_transaction_model.create(
                {
                    "contract_id": self.contract_id.id,
                    "day_to_apply": 40,
                    "payslip_input_type_id": self.input_type_id.id,
                    "amount": 100.0,
                }
            )
        with self.assertRaises(UserError):
            self.fixed_transaction_model.create(
                {
                    "contract_id": self.contract_id.id,
                    "day_to_apply": 0,
                    "payslip_input_type_id": self.input_type_id.id,
                    "amount": 100.0,
                }
            )
        with self.assertRaises(UserError):
            self.fixed_transaction_model.create(
                {
                    "contract_id": self.contract_id.id,
                    "start_date": self.contract_id.date_start - relativedelta(days=1),
                    "day_to_apply": 31,
                    "payslip_input_type_id": self.input_type_id.id,
                    "amount": 100.0,
                }
            )
        with self.assertRaises(UserError):
            self.fixed_transaction_model.create(
                {
                    "contract_id": self.contract_id.id,
                    "start_date": self.contract_id.date_start,
                    "end_date": self.contract_id.date_end + relativedelta(days=1),
                    "day_to_apply": 31,
                    "payslip_input_type_id": self.input_type_id.id,
                    "amount": 100.0,
                }
            )
        new_transaction = self.fixed_transaction_model.create(
            {
                "contract_id": self.contract_id.id,
                "day_to_apply": 31,
                "payslip_input_type_id": self.output_type_id.id,
                "amount": 100.0,
            }
        )
        self.assertEqual(new_transaction.transaction_type, "output")
        new_transaction = self.fixed_transaction_model.create(
            {
                "contract_id": self.contract_id.id,
                "day_to_apply": 31,
                "payslip_input_type_id": self.input_type_id.id,
                "amount": 100.0,
            }
        )
        self.assertEqual(new_transaction.transaction_type, "input")

    def test_input_type(self):
        new_input = self.input_type_model.create(
            {
                "name": "Extra Input",
                "code": "TESTCODE",
                "category_id": self.category_model.search([], limit=1).id,
                "country_id": self.current_country.id,
            }
        )
        self.assertEqual(set(new_input.rule_ids.mapped("code")), {"TESTCODE"})
        self.assertEqual(len(new_input.rule_ids), 2)
        self.assertEqual(new_input.rule_count, 2)
        new_input.write({"code": "TESTCODE1"})
        self.assertEqual(set(new_input.rule_ids.mapped("code")), {"TESTCODE1"})
        self.assertEqual(len(new_input.rule_ids), 2)
        self.assertEqual(new_input.rule_count, 2)
        action = new_input.action_show_rules()
        self.assertEqual(
            [("id", "in", new_input.rule_ids.ids)], action.get("domain", [])
        )
        with self.assertRaises(UserError):
            new_input.write({"code": "TESTCODE WITH SPACE"})

    def test_payslip(self):
        payslip_run = self.env["hr.payslip.run"].create(
            {
                "date_start": "2021-12-01",
                "date_end": "2021-12-31",
                "name": "Test Payslip Run",
            }
        )
        # I create record for generating the payslip for this Payslip run.
        payslip_employee = self.env["hr.payslip.employees"].create(
            {
                "employee_ids": [(4, self.employee_id.id)],
                "structure_id": self.struct_1.id,
            }
        )
        payslip_employee.with_context(active_id=payslip_run.id).compute_sheet()
        current_payslip = payslip_run.slip_ids[0]
        self.fixed_transaction_model.create(
            {
                "contract_id": self.contract_id.id,
                "day_to_apply": 31,
                "payslip_input_type_id": self.input_type_id.id,
                "amount": 100.0,
            }
        )
        new_input = self.scheduled_transaction_model.create(
            {
                "employee_id": self.employee_id.id,
                "date": "2021-12-01",
                "payslip_input_type_id": self.input_type_id.id,
                "amount": 100.0,
            }
        )
        new_output = self.scheduled_transaction_model.create(
            {
                "employee_id": self.employee_id.id,
                "date": "2021-12-01",
                "payslip_input_type_id": self.output_type_id.id,
                "amount": 100.0,
            }
        )
        inputs = current_payslip.input_line_ids.filtered(
            lambda x: x.input_type_id.id == self.input_type_id.id
        )
        self.assertEqual(len(inputs), 1)
        self.assertEqual(sum(inputs.mapped("amount")), 200)
        outputs = current_payslip.input_line_ids.filtered(
            lambda x: x.input_type_id.id == self.output_type_id.id
        )
        self.assertEqual(sum(outputs.mapped("amount")), -100)
        self.assertEqual(len(outputs), 1)
        new_output.write(
            {
                "amount": 50,
            }
        )
        outputs = current_payslip.input_line_ids.filtered(
            lambda x: x.input_type_id.id == self.output_type_id.id
        )
        self.assertEqual(sum(outputs.mapped("amount")), -50)
        new_input.write(
            {
                "date": "2021-11-30",
            }
        )
        inputs = current_payslip.input_line_ids.filtered(
            lambda x: x.input_type_id.id == self.input_type_id.id
        )
        self.assertEqual(len(inputs), 1)
        self.assertEqual(sum(inputs.mapped("amount")), 100)
        new_input.write(
            {
                "date": "2021-12-01",
            }
        )
        inputs = current_payslip.input_line_ids.filtered(
            lambda x: x.input_type_id.id == self.input_type_id.id
        )
        self.assertEqual(len(inputs), 1)
        self.assertEqual(sum(inputs.mapped("amount")), 200)
        new_input.unlink()
        inputs = current_payslip.input_line_ids.filtered(
            lambda x: x.input_type_id.id == self.input_type_id.id
        )
        self.assertEqual(len(inputs), 1)
        self.assertEqual(sum(inputs.mapped("amount")), 100)
        current_payslip.compute_sheet()
        current_payslip.action_payslip_done()
        self.assertTrue(new_output.is_processed)
