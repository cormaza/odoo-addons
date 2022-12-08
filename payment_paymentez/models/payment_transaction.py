import json
import logging
import pprint

import requests

from odoo import _, api, models, release
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    @api.model
    def _get_tx_from_feedback_data(self, provider, data):
        tx = super()._get_tx_from_feedback_data(provider, data)
        if provider != "paymentez":
            return tx
        reference = data.get("reference")
        tx = self.search(
            [("reference", "=", reference), ("provider", "=", "paymentez")]
        )
        if not tx:
            raise ValidationError(
                _("Paymentez: No transaction found matching reference %s.", reference)
            )
        return tx

    def _process_feedback_data(self, data):
        res = super()._process_feedback_data(data)
        if self.provider != "paymentez":
            return res
        status = data.get("response", {}).get("transaction", {}).get("status", False)
        message = data.get("response", {}).get("transaction", {}).get("message", "")
        if status == "success":
            _logger.info(pprint.pformat(data.get("response")))
            acquirer_reference = (
                data.get("response", {}).get("transaction", {}).get("id", False)
            )
            self.acquirer_reference = acquirer_reference
            self._set_done(state_message=message)
        elif status == "pending":
            # TODO: create method that retrieve data if transaction if done
            _logger.warning(pprint.pformat(data.get("response")))
            message = "%s: %s" % (_("Transaction is pending"), message)
            acquirer_reference = (
                data.get("response", {}).get("transaction", {}).get("id", False)
            )
            self.acquirer_reference = acquirer_reference
            self._set_pending(state_message=message)
        elif status == "failure":
            _logger.warning(pprint.pformat(data.get("response")))
            message = "%s: %s" % (
                _("Transaction was rejected, please review your card details"),
                message,
            )
            self._set_error(state_message=message)

    def paymentez_get_transaction_status(self):
        acquirer_token = self.acquirer_id._generate_paymentez_token()
        url = "{url}/v2/transaction/{ref}".format(
            url=self.acquirer_id._get_paymentez_api_url(), ref=self.acquirer_reference
        )
        headers = {
            "Auth-Token": acquirer_token,
            "User-Agent": "Odoo/{}".format(release.version),
            "content-type": "application/json",
        }
        response = requests.request("GET", url, headers=headers)
        return json.loads(response.text)

    def _send_refund_request(
        self, amount_to_refund=None, create_refund_transaction=True
    ):
        if self.provider != "paymentez":
            return super()._send_refund_request(
                amount_to_refund=amount_to_refund,
                create_refund_transaction=create_refund_transaction,
            )
        current_status = self.paymentez_get_transaction_status()
        if current_status.get("error"):
            raise UserError(
                _(
                    "Can't refund transaction %(reference)s: type: %(type)s help:%(help)s"
                )
                % {
                    "reference": self.display_name,
                    "type": current_status.get("error").get("type"),
                    "help": current_status.get("error").get("help"),
                }
            )
        if current_status["transaction"]["status_detail"] != 7:
            vals = {
                "transaction": {"id": self.acquirer_reference},
                "order": {
                    "amount": self.amount,
                },
            }
            acquirer_token = self.acquirer_id._generate_paymentez_token()
            url = "{url}/v2/transaction/refund/".format(
                url=self.acquirer_id._get_paymentez_api_url()
            )
            payload = json.dumps(vals)
            headers = {
                "Auth-Token": acquirer_token,
                "User-Agent": "Odoo/{}".format(release.version),
                "content-type": "application/json",
            }
            response = requests.request("POST", url, data=payload, headers=headers)
            _logger.info(
                _("Response Paymentez refund %s"), pprint.pformat(response.text)
            )
            if response.status_code != 200:
                raise UserError(response.text)
            res = json.loads(response.text)
            if res.get("status") == "success":
                refund_tx = super()._send_refund_request(
                    amount_to_refund=amount_to_refund, create_refund_transaction=True
                )
                refund_tx.write(
                    {
                        "acquirer_reference": res.get("transaction", {}).get(
                            "id", False
                        ),
                    }
                )
            elif res.get("status") == "failure":
                raise UserError(
                    _("Can't refund transaction %(reference)s: detail: %(detail)s")
                    % {"reference": self.display_name, "detail": res.get("detail")}
                )
