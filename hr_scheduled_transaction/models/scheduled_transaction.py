from odoo import _, api, fields, models
from odoo.exceptions import UserError

_FIELDS_TO_CHECK = [
    "employee_id",
    "date",
    "amount",
    "payslip_input_type_id",
]


class HrScheduledTransaction(models.Model):

    _name = "hr.scheduled.transaction"
    _description = "Scheduled Transaction"

    company_id = fields.Many2one(
        "res.company", "Company", required=True, default=lambda self: self.env.company
    )
    employee_id = fields.Many2one(
        "hr.employee", string="Employee", required=True, check_company=True
    )
    date = fields.Date(required=True)
    amount = fields.Float(required=True)
    reference = fields.Char(required=False)
    is_processed = fields.Boolean(
        string="Is Processed?", store=True, compute="_compute_get_status"
    )
    payslip_input_type_id = fields.Many2one(
        "hr.payslip.input.type",
        string="Payslip Input Type",
        store=True,
        required=True,
    )
    payslip_input_ids = fields.Many2many(
        comodel_name="hr.payslip.input",
        string="Payslip inputs",
        required=False,
        ondelete="cascade",
    )

    transaction_type = fields.Selection(
        selection=[
            ("input", "Input"),
            ("output", "Output"),
        ],
        string="Type",
        compute="_compute_type_transaction",
        store=True,
    )

    @api.constrains("amount")
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise UserError(_("Amount must be bigger than zero"))

    @api.depends("amount", "payslip_input_type_id.category_id.code")
    def _compute_type_transaction(self):
        for rec in self:
            rec_type = "input"
            if rec.payslip_input_type_id.category_id.code == "EGRE":
                rec_type = "output"
            rec.transaction_type = rec_type

    @api.depends("payslip_input_ids.payslip_id.state")
    def _compute_get_status(self):
        for rec in self:
            rec.is_processed = (
                rec.payslip_input_ids
                and all(
                    [line.payslip_id.state == "done" for line in rec.payslip_input_ids]
                )
                or False
            )

    @api.model
    def load(self, fields, data):
        res = super(
            HrScheduledTransaction,
            self.with_context(no_recalc_work_entries=True, stop_recurtion=True),
        ).load(fields, data)
        if res and "ids" in res:
            for rec in self.browse(res.get("ids")):
                slip_model = self.env["hr.payslip"].with_context(
                    no_recalc_work_entries=True
                )
                slip_model._recalc_payslip_change(rec.employee_id.id, rec.date)
        return res

    @api.model
    def create(self, vals):
        slip_model = self.env["hr.payslip"].with_context(no_recalc_work_entries=True)
        rec = super(HrScheduledTransaction, self).create(vals)
        recompute = False
        for field in _FIELDS_TO_CHECK:
            if field in vals:
                recompute = True
        if not self.env.context.get("stop_recursion", False) and recompute:
            slip_model._recalc_payslip_change(rec.employee_id.id, rec.date)
        return rec

    def write(self, vals):
        slip_model = self.env["hr.payslip"].with_context(no_recalc_work_entries=True)
        recompute = False
        for field in _FIELDS_TO_CHECK:
            if field in vals:
                recompute = True
        to_recompute_data = []
        if not self.env.context.get("stop_recursion", False) and recompute:
            for rec in self:
                reference_date = vals.get("date", False)
                if reference_date:
                    to_recompute_data.append((rec.employee_id.id, reference_date))
                else:
                    to_recompute_data.append((rec.employee_id.id, rec.date))
        res = super(HrScheduledTransaction, self).write(vals)
        for employee_id, reference_date in to_recompute_data:
            slip_model._recalc_payslip_change(employee_id, reference_date)
        return res

    def unlink(self):
        slip_model = self.env["hr.payslip"].with_context(no_recalc_work_entries=True)
        to_recompute_data = []
        related_inputs = self.env["hr.payslip.input"].browse()
        for rec in self:
            to_recompute_data.append((rec.employee_id.id, rec.date))
            for current_input in rec.payslip_input_ids:
                related_inputs |= current_input
        res = super(HrScheduledTransaction, self).unlink()
        if related_inputs:
            related_inputs.unlink()
        for employee_id, reference_date in to_recompute_data:
            slip_model._recalc_payslip_change(employee_id, reference_date)
        return res
