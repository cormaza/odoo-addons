from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HrContractFixedInputs(models.Model):

    _name = "hr.contract.fixed.inputs"

    contract_id = fields.Many2one(
        comodel_name="hr.contract", string="Contract", required=False
    )
    payslip_input_type_id = fields.Many2one(
        "hr.payslip.input.type",
        string="Payslip Input Type",
        required=True,
    )
    start_date = fields.Date(required=False)
    end_date = fields.Date(required=False)
    day_to_apply = fields.Integer(default=31, required=False)
    amount = fields.Float(
        required=True,
    )
    type_transaction = fields.Selection(
        selection=[
            ("input", "Input"),
            ("output", "Output"),
        ],
        string="Type",
        compute="_compute_type_transaction",
        store=True,
    )

    @api.depends("amount", "payslip_input_type_id.category_id.code")
    def _compute_type_transaction(self):
        for rec in self:
            rec_type = "input"
            if rec.payslip_input_type_id.category_id.code == "EGRE":
                rec_type = "output"
            rec.type_transaction = rec_type

    @api.constrains("day_to_apply")
    def _check_day_to_apply(self):
        for rec in self:
            if 0 > rec.day_to_apply > 31:
                raise UserError(
                    _("Day to apply of fixed input %s must be between 1 or 31")
                    % (rec.payslip_input_type_id.display_name)
                )

    @api.constrains("amount")
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise UserError(
                    _("Amount of fixed input %(input_name)s must be bigger than zero")
                    % {"input_name": rec.payslip_input_type_id.display_name}
                )

    @api.constrains(
        "contract_id",
        "start_date",
        "end_date",
    )
    def _check_dates(self):
        for rec in self:
            if rec.start_date:
                if rec.start_date < rec.contract_id.date_start:
                    raise UserError(
                        _(
                            "Start Date of Fixed Input "
                            "%(input_name)s %(input_date_start)s "
                            "must be after contract "
                            "date start %(date_start)s"
                        )
                        % {
                            "input_name": rec.payslip_input_type_id.display_name,
                            "input_date_start": rec.start_date,
                            "date_start": rec.contract_id.date_start,
                        }
                    )
            if rec.end_date and rec.contract_id.date_end:
                if rec.end_date > rec.contract_id.date_end:
                    raise UserError(
                        _(
                            "End Date of Fixed Input "
                            "%(input_name)s %(input_end_date)s "
                            "must be before contract "
                            "date end %(contract_date_end)s"
                        )
                        % {
                            "input_name": rec.payslip_input_type_id.display_name,
                            "input_end_date": rec.end_date,
                            "contract_date_end": rec.contract_id.date_end,
                        }
                    )


class HrContract(models.Model):

    _inherit = "hr.contract"

    fixed_inputs_ids = fields.One2many(
        comodel_name="hr.contract.fixed.inputs",
        inverse_name="contract_id",
        string="Fixed inputs",
        required=False,
    )

    def _get_current_fixed_inputs(self, start_date, end_date):
        self.ensure_one()
        fixed_inputs = self.fixed_inputs_ids.filtered(
            lambda x: not x.start_date and not x.end_date
        )
        domain = [
            ("contract_id", "=", self.id),
            "|",
            "|",
            "&",
            ("start_date", "<=", start_date),
            ("end_date", ">=", start_date),
            "&",
            ("start_date", "<=", end_date),
            ("end_date", ">=", end_date),
            "&",
            ("start_date", "<=", start_date),
            ("end_date", ">=", end_date),
        ]
        recs_founded = self.env["hr.contract.fixed.inputs"].search(domain)
        end_month = (
            end_date + relativedelta(months=+1, day=1, days=-1)
        ).day == end_date.day
        end_date_day = end_month and 31 or end_date.day
        recs_founded = recs_founded.filtered(
            lambda x: x.start_date.day <= x.day_to_apply <= end_date_day
        )
        for rec in recs_founded:
            fixed_inputs |= rec
        return fixed_inputs
