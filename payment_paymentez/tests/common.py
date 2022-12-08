from odoo.addons.payment.tests.common import PaymentCommon


class PaymentezCommon(PaymentCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.paymentez = cls._prepare_acquirer(
            "paymentez",
            update_values={
                "paymentez_app_code": "dummy",
                "paymentez_app_key": "dummy",
                "paymentez_server_code": "dummy",
                "paymentez_server_key": "dummy",
            },
        )

        cls.acquirer = cls.paymentez
