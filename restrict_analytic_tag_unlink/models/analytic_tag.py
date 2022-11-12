from odoo import _, api, models
from odoo.exceptions import UserError


class AccountAnalyticTag(models.Model):

    _inherit = "account.analytic.tag"

    @api.ondelete(at_uninstall=False)
    def restrict_used_tag_unlink(self):
        for tag in self:
            field_obj = self.env["ir.model.fields"]
            fields_data = field_obj.search(
                [
                    ("relation", "=", "account.analytic.tag"),
                    ("store", "=", True),
                    ("model_id.transient", "=", False),
                ]
            )
            for field in fields_data:
                model_ref = field.model_id.model
                model = self.env[model_ref]
                if not model._auto:
                    # This model is probably a sql type report
                    continue
                records_count = model.sudo().search_count(
                    [(field.name, "in", [tag.id])]
                )
                if records_count > 0:
                    raise UserError(
                        _(
                            "The analytic tag %(tag_name)s is being "
                            "used in the model %(model_name)s, "
                            "you should inactivate record instead delete it"
                        )
                        % {"tag_name": tag.name, "model_name": field.model_id.name}
                    )
