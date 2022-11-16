from odoo.tests.common import TransactionCase


class ScheduledTransactionTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        input_type_model = cls.env["hr.payslip.input.type"]
        category_model = cls.env["hr.salary.rule.category"]
        employee_model = cls.env["hr.employee"]
        contract_model = cls.env["hr.contract"]
        cls.input_type_id = input_type_model.create(
            {
                "name": "Extra Input",
                "code": "ExtraInput",
                "category_id": category_model.search([], limit=1).id,
            }
        )
        cls.output_type_id = input_type_model.create(
            {
                "name": "Extra Output",
                "code": "ExtraOutput",
                "category_id": category_model.search([], limit=1).id,
            }
        )
        cls.employee_id = employee_model.create(
            {
                "name": "Test Employee",
            }
        )
        cls.contract_id = contract_model.create(
            {
                "employee_id": cls.employee_id.id,
                "date_start": "2021-01-01",
                "date_end": "2021-31-12",
                "wage": 600.0,
                "state": "open",
            }
        )

    def test_fixed_inputs(self):
        pass
