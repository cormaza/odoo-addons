from odoo import _, api, models
from odoo.exceptions import ValidationError


class HrContract(models.Model):

    _inherit = "hr.contract"

    @api.constrains("date_start", "date_end", "employee_id")
    def _check_dates(self):
        for contract in self:
            date_from = contract.date_start
            date_to = contract.date_end
            if date_to and date_to < date_from:
                raise ValidationError(
                    _("The ending date must not be prior to the starting date.")
                )
            domain = [
                ("id", "!=", contract.id),
                ("employee_id", "=", contract.employee_id.id),
            ]
            other_contracts = self.search(domain)
            open_contracts = other_contracts.filtered(lambda x: not x.date_end)
            overlapping = False
            if open_contracts and not contract.date_end:
                overlapping = True
            closed_contracts = other_contracts.filtered(lambda x: x.date_end)
            if not overlapping:
                for closed_contract in closed_contracts:
                    if (
                        not contract.date_end
                        and contract.date_start < closed_contract.date_start
                    ):
                        overlapping = True
                        break
                    if (
                        closed_contract.date_end
                        >= contract.date_start
                        >= closed_contract.date_start
                    ):
                        overlapping = True
                        break
                    if contract.date_end:
                        if (
                            closed_contract.date_end
                            >= contract.date_end
                            >= closed_contract.date_start
                        ):
                            overlapping = True
                            break
                        if (
                            contract.date_start <= closed_contract.date_start
                            and contract.date_end >= closed_contract.date_end
                        ):
                            overlapping = True
                            break
            if overlapping:
                raise ValidationError(
                    _(
                        "You can not have an overlap between two contract for employee %s, "
                        "please correct the start and/or end dates of your contracts."
                    )
                    % (contract.employee_id.display_name)
                )
