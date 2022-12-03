import logging

from odoo import _, http
from odoo.exceptions import UserError
from odoo.http import request

_logger = logging.getLogger(__name__)


class PaymentezController(http.Controller):
    @http.route("/payment/paymentez/get_acquirer_info", type="json", auth="public")
    def paymentez_get_acquirer_info(self, acquirer_id, invoice_id=False):
        order_data = {
            "user_id": "",
            "user_email": "",
            "user_phone": "",
            "order_description": "",
            "order_amount": 0.0,
            "order_vat": 0.0,
            "order_reference": "",
            "order_taxable_amount": 0.0,
            "order_tax_percentage": 0.0,
        }
        if request.session.get("sale_order_id", False):
            order = (
                request.env["sale.order"]
                .browse(request.session.get("sale_order_id", False))
                .sudo()
            )
            taxes_data = order._get_taxes_data_paymentez()
            tax_rates = list(
                {tax.amount for tax in taxes_data.keys() if tax.amount != 0}
            )
            # CHECKME: When you send data paymentez
            # only accept one rate of iva, and compare
            # all value with taxes value
            if len(tax_rates) > 1:
                raise UserError(
                    _(
                        "Your have more than one VAT tax assigned on your order, "
                        "please ask for support for page administrator"
                    )
                )
            base_amount = sum(
                taxes_data[tax].get("base")
                for tax in taxes_data.keys()
                if tax.amount > 0
            )
            order_data.update(
                {
                    "user_id": str(order.partner_id.vat or order.partner_id.id),
                    "user_email": order.partner_id.email or "",
                    "user_phone": order.partner_id.mobile
                    or order.partner_id.phone
                    or "",
                    "order_description": order.display_name or "",
                    "order_amount": order.amount_total,
                    "order_vat": order.amount_tax,
                    "order_reference": order.name,
                    "order_taxable_amount": base_amount,
                    "order_tax_percentage": tax_rates and tax_rates[0] or 0,
                }
            )
        elif invoice_id:
            invoice = request.env["account.move"].browse(invoice_id).sudo()
            taxes_data = invoice._get_taxes_data_paymentez()
            tax_rates = list(
                {tax.amount for tax in taxes_data.keys() if tax.amount != 0}
            )
            # CHECKME: When you send data paymentez only
            # accept one rate of iva, and compare
            # all value with taxes value
            if len(tax_rates) > 1:
                raise UserError(
                    _(
                        "Your have more than one VAT tax assigned on your order, "
                        "please ask for support for page administrator"
                    )
                )
            base_amount = sum(
                taxes_data[tax].get("base")
                for tax in taxes_data.keys()
                if tax.amount > 0
            )
            order_data.update(
                {
                    "user_id": str(invoice.partner_id.vat or invoice.partner_id.id),
                    "user_email": invoice.partner_id.email or "",
                    "user_phone": invoice.partner_id.mobile
                    or invoice.partner_id.phone
                    or "",
                    "order_description": invoice.display_name or "",
                    "order_amount": invoice.amount_total,
                    "order_vat": invoice.amount_tax,
                    "order_reference": invoice.name,
                    "order_taxable_amount": base_amount,
                    "order_tax_percentage": tax_rates and tax_rates[0] or 0,
                }
            )
        acquirer_sudo = (
            request.env["payment.acquirer"].sudo().browse(acquirer_id).exists()
        )
        installment_type = acquirer_sudo.paymentez_installments_type_id.installment_type
        return {
            "state": acquirer_sudo.state,
            "client_app_code": acquirer_sudo.paymentez_app_code,
            "client_app_key": acquirer_sudo.paymentez_app_key,
            "env_mode": acquirer_sudo.state == "test" and "sgt" or "prod",
            "order_installments_type": installment_type and int(installment_type) or 0,
            "order_data": order_data,
        }

    @http.route("/payment/paymentez/payment", type="json", auth="public")
    def paymentez_payment(self, response_data):
        reference = response_data.get("transaction", {}).get("dev_reference", "")
        feedback_data = {"reference": reference, "response": response_data}
        request.env["payment.transaction"].sudo()._handle_feedback_data(
            "paymentez", feedback_data
        )
