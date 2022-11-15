from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HrPayslipInputType(models.Model):

    _inherit = "hr.payslip.input.type"

    category_id = fields.Many2one(
        comodel_name="hr.salary.rule.category",
        string="Category Salary Rule",
        required=False,
    )

    account_credit_id = fields.Many2one("account.account", string="Credit Account")
    account_debit_id = fields.Many2one("account.account", string="Debit Account")
    analytic_account_id = fields.Many2one(
        "account.analytic.account", string="Analytic Account"
    )
    not_computed_in_net = fields.Boolean("Not computed in net accountability")
    sequence = fields.Integer(default=5)

    def _hook_new_rule_data(self, new_rule_data):
        """
        Implements on Localizations
        :param new_rule_data:
        :return:
        """
        return new_rule_data

    @api.model
    def create(self, vals):
        rec = super(HrPayslipInputType, self).create(vals)
        rule_model = self.env["hr.salary.rule"]
        struct_model = self.env["hr.payroll.structure"]
        current_structs = rec.struct_ids
        if not current_structs:
            current_structs = struct_model.search(
                [
                    ("country_id", "=", rec.country_id.id),
                ]
            )
        for struct in current_structs:
            new_rule_data = {
                "name": rec.display_name,
                "category_id": rec.category_id.id,
                "code": rec.code,
                "struct_id": struct.id,
                "condition_select": "python",
                "condition_python": "result = inputs.{code} and inputs.{code}.amount or 0".format(  # noqa: disable=B950
                    code=rec.code
                ),
                "amount_select": "code",
                "amount_python_compute": "result = inputs.%(code)s and inputs.%(code)s.amount or 0"  # noqa: disable=B950
                % {"code": rec.code},
                "input_type_id": rec.id,
                "account_credit_id": rec.account_credit_id.id,
                "account_debit_id": rec.account_debit_id.id,
                "analytic_account_id": rec.analytic_account_id.id,
                "not_computed_in_net": rec.not_computed_in_net,
                "sequence": rec.sequence,
            }
            new_rule_data = self._hook_new_rule_data(new_rule_data)
            rule_model.create(new_rule_data)
        return rec

    def write(self, values):
        res = super(HrPayslipInputType, self).write(values)
        for rec in self:
            for rule in self.rule_ids:
                update_rule_data = {
                    "name": rec.display_name,
                    "category_id": rec.category_id.id,
                    "code": rec.code,
                    "condition_python": "result = inputs.{code} and inputs.{code}.amount or 0".format(  # noqa: disable=B950
                        code=rec.code
                    ),
                    "amount_python_compute": "result = inputs.%(code)s and inputs.%(code)s.amount or 0"  # noqa: disable=B950
                    % {"code": rec.code},
                    "account_credit_id": rec.account_credit_id.id,
                    "account_debit_id": rec.account_debit_id.id,
                    "analytic_account_id": rec.analytic_account_id.id,
                    "not_computed_in_net": rec.not_computed_in_net,
                    "sequence": rec.sequence,
                }
                rule.write(update_rule_data)
        return res

    rule_ids = fields.One2many(
        comodel_name="hr.salary.rule",
        inverse_name="input_type_id",
        string="Salary Rules",
        required=False,
    )

    @api.depends("rule_ids")
    def _get_rule_count(self):
        for rec in self:
            rec.rule_count = len(rec.rule_ids)

    rule_count = fields.Integer(
        string="Rules Count", funcion="_get_rule_count", required=False
    )

    def action_show_rules(self):
        self.ensure_one()
        action = self.env.ref("hr_payroll.action_salary_rule_form").read()[0]
        action.update({"domain": [("id", "in", self.rule_ids.ids)]})
        return action

    @api.constrains(
        "code",
    )
    def _check_code_spaces(self):
        for rec in self:
            for c in rec.code:
                if c.isspace():
                    raise UserError(
                        _("Don't include spaces characters in code of %s") % (rec.code)
                    )


class HrSalaryRule(models.Model):

    _inherit = "hr.salary.rule"

    input_type_id = fields.Many2one(
        comodel_name="hr.payslip.input.type",
        string="Input Type",
        ondelete="cascade",
        required=False,
    )


class HrPayslipInput(models.Model):

    _inherit = "hr.payslip.input"

    transaction_ids = fields.Many2many(
        "hr.scheduled.transaction",
        string="Scheduled Transactions",
    )

    def write(self, values):
        if "amount" in values and not self.env.context.get("mass_compute", False):
            for line in self:
                if len(line.transaction_ids) > 1 and abs(values.get("amount")) != abs(
                    line.amount
                ):
                    raise UserError(
                        _(
                            "You cannot modify this record because there's "
                            "more than one transaction with this code %s, "
                            "you must modify on scheduled transactions"
                        )
                        % line.input_type_id.code
                    )
                if len(line.transaction_ids) == 1:
                    line.transaction_ids.with_context(stop_recurtion=True).amount = abs(
                        values.get("amount")
                    )
        return super(HrPayslipInput, self).write(values)


class HrPayslip(models.Model):

    _inherit = "hr.payslip"

    def compute_sheet(self):
        payslip_input_model = self.env["hr.payslip.input"]
        input_type_model = self.env["hr.payslip.input.type"]
        for payslip in self:
            if self.env.context.get("mass_compute", False):
                if payslip.input_line_ids:
                    payslip.input_line_ids.unlink()
            date_to = payslip.date_to
            if self.env.context.get("severance_pay", False):
                date_to = payslip.date_from + relativedelta(months=1, day=1, days=-1)
            scheduled_transactions = self.env["hr.scheduled.transaction"].search(
                [
                    ("employee_id", "=", payslip.employee_id.id),
                    ("is_processed", "=", False),
                    ("date", ">=", payslip.date_from),
                    ("date", "<=", date_to),
                ]
            )
            fixed_inputs = payslip.contract_id._get_current_fixed_inputs(
                payslip.date_from, payslip.date_to
            )
            input_types = input_type_model.browse()
            for input_type in scheduled_transactions.mapped("payslip_input_type_id"):
                input_types |= input_type
            for input_type in fixed_inputs.mapped("payslip_input_type_id"):
                input_types |= input_type
            for input_type in input_types:
                current_input = payslip.input_line_ids.filtered(
                    lambda x: x.input_type_id.id == input_type.id
                )
                current_st = scheduled_transactions.filtered(
                    lambda x: x.payslip_input_type_id.id == input_type.id
                )
                amount = sum(
                    st.type == "input" and st.amount or st.amount * -1
                    for st in current_st
                )
                current_fi = fixed_inputs.filtered(
                    lambda x: x.payslip_input_type_id.id == input_type.id
                )
                amount += sum(
                    fi.type_transaction == "input" and fi.amount or fi.amount * -1
                    for fi in current_fi
                )
                if current_input:
                    current_input.with_context(mass_compute=True).write(
                        {
                            "amount": amount,
                        }
                    )
                else:
                    data = {
                        "payslip_id": payslip.id,
                        "input_type_id": input_type.id,
                        "transaction_ids": current_st.ids,
                        "amount": amount,
                    }
                    if isinstance(payslip.id, models.NewId):
                        payslip_input_model.new(data)
                    else:
                        payslip_input_model.create(data)
        return super(HrPayslip, self).compute_sheet()

    l10n_ec_count_transactions = fields.Integer(
        string="Count Scheduled Transactions",
        compute="_compute_count_transactions",
        store=False,
    )

    @api.depends(
        "employee_id",
        "date_from",
        "date_to",
    )
    def _compute_count_transactions(self):
        transaction_model = self.env["hr.scheduled.transaction"]
        for rec in self:
            current_transactions = transaction_model.search(
                [
                    ("employee_id", "=", rec.employee_id.id),
                    ("date", ">=", rec.date_from),
                    ("date", "<=", rec.date_to),
                ]
            )
            rec.l10n_ec_count_transactions = len(current_transactions.ids)

    def action_show_current_transactions(self):
        self.ensure_one()
        action = self.env.ref(
            "hr_scheduled_transaction.action_hr_scheduled_transaction_tree_view"
        ).read()[0]
        action.update(
            {
                "domain": [
                    ("employee_id", "=", self.employee_id.id),
                    ("date", ">=", self.date_from),
                    ("date", "<=", self.date_to),
                ]
            }
        )
        action["context"] = dict(
            self._context,
            default_employee_id=self.employee_id.id,
            default_date=self.date_to,
        )
        return action

    @api.model
    def _recalc_payslip_change(self, employee_id, reference_date):
        slip_model = self.env["hr.payslip"]
        open_slip = slip_model.search(
            [
                ("employee_id", "=", employee_id),
                ("date_from", "<=", reference_date),
                ("date_to", ">=", reference_date),
                ("state", "in", ("draft", "verify")),
            ]
        )
        if open_slip:
            open_slip.with_context(no_recalc_work_entries=True).compute_sheet()
        return True
