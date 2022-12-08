from odoo import fields, models


class PaymentezInstallmentsType(models.Model):

    _name = "paymentez.installments.type"
    _description = "The installments type are only available for Ecuador."

    installment_type = fields.Char(required=True)

    installment_state = fields.Boolean(required=False)

    installment_description = fields.Text(required=False)

    def name_get(self):
        result = []
        for installment_type in self:
            result.append(
                (
                    installment_type.id,
                    "{} * {}".format(
                        installment_type.installment_type,
                        installment_type.installment_description,
                    ),
                )
            )
        return result
