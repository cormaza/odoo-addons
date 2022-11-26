import logging

from odoo import http
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
            order_data.update(
                {
                    "user_id": str(order.partner_id.vat or order.partner_id.id),
                    "user_email": order.partner_id.email or "",
                    "user_phone": order.partner_id.mobile
                    or order.partner_id.phone
                    or "",
                    "order_description": order.display_name
                    or "",  # TODO: get more detailed description from lines
                    "order_amount": order.amount_total * 1.12,
                    # "order_vat": order.amount_tax,
                    "order_vat": order.amount_total * 0.12,
                    "order_reference": order.name,
                    # TODO: get installments allowed from acquirer
                    # "order_installments_type": "",
                    # TODO: get taxable amount from order
                    "order_taxable_amount": order.amount_total,
                    # TODO: get tax percentage from tax applied on lines
                    "order_tax_percentage": 12.0,
                }
            )
        elif invoice_id:
            invoice = request.env["account.move"].browse(invoice_id).sudo()
            order_data.update(
                {
                    "user_id": str(invoice.partner_id.vat or invoice.partner_id.id),
                    "user_email": invoice.partner_id.email or "",
                    "user_phone": invoice.partner_id.mobile
                    or invoice.partner_id.phone
                    or "",
                    # TODO: get more detailed description from lines
                    "order_description": invoice.display_name or "",
                    "order_amount": invoice.amount_total * 1.12,
                    "order_vat": invoice.amount_total * 0.12,
                    "order_reference": invoice.name,
                    # TODO: get taxable amount from order
                    "order_taxable_amount": invoice.amount_total,
                    # TODO: get tax percentage from tax applied on lines
                    "order_tax_percentage": 12.0,
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
