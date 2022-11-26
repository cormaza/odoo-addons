import hashlib
import logging
import time
from base64 import b64encode

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PaymentAcquirer(models.Model):
    _inherit = "payment.acquirer"

    provider = fields.Selection(
        selection_add=[("paymentez", "Paymentez")],
        ondelete={"paymentez": "set default"},
    )
    paymentez_app_code = fields.Char(
        required_if_provider="paymentez",
        groups="base.group_user",
    )
    paymentez_app_key = fields.Char(
        required_if_provider="paymentez",
        groups="base.group_user",
    )
    paymentez_server_code = fields.Char(
        required_if_provider="paymentez",
        groups="base.group_user",
    )
    paymentez_server_key = fields.Char(
        required_if_provider="paymentez",
        groups="base.group_user",
    )
    paymentez_installments_type_id = fields.Many2one(
        comodel_name="paymentez.installments.type",
        string="Installments type",
        required=False,
    )

    def _get_default_payment_method_id(self):
        self.ensure_one()
        if self.provider != "paymentez":
            return super()._get_default_payment_method_id()
        return self.env.ref("payment_paymentez.payment_method_paymentez").id

    @api.model
    def _get_paymentez_api_url(self):
        """Paymentez URLs"""
        if self.state in ("test", "disabled"):
            return "https://ccapi-stg.paymentez.com"
        else:
            return "https://ccapi.paymentez.com"

    @api.model
    def _generate_paymentez_token(self):
        server_application_code = self.paymentez_server_code
        server_app_key = self.paymentez_server_key
        unix_timestamp = str(int(time.time()))
        uniq_token_string = server_app_key + unix_timestamp
        m = hashlib.sha256()
        m.update(bytes(uniq_token_string, "utf-8"))
        uniq_token_hash = m.hexdigest()
        auth_token = b64encode(
            "{};{};{}".format(
                server_application_code, unix_timestamp, uniq_token_hash
            ).encode("ascii")
        )
        return auth_token.decode("ascii")
