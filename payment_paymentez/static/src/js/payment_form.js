odoo.define("payment_paymentez.payment_form", (require) => {
    "use strict";

    const core = require("web.core");

    const checkoutForm = require("payment.checkout_form");
    const manageForm = require("payment.manage_form");

    const _t = core._t;

    const paymentezMixin = {
        jsLibs: ["https://cdn.paymentez.com/ccapi/sdk/payment_checkout_stable.min.js"],

        _prepatePaymentezModal: function (
            provider,
            acquirerId,
            client_app_code,
            client_app_key,
            env_mode
        ) {
            var self = this;
            // eslint-disable-next-line no-undef
            return new PaymentCheckout.modal({
                client_app_code: client_app_code,
                client_app_key: client_app_key,
                // TODO: get language from website?
                locale: "es",
                env_mode: env_mode,
                onClose: function () {
                    $("body").unblock();
                    self._enableButton();
                },
                onResponse: function (response) {
                    return self._processDirectPayment(provider, acquirerId, response);
                },
            });
        },

        _processPayment: function (provider, paymentOptionId, flow) {
            console.log(flow);
            var self = this;
            return this._rpc({
                route: "/payment/paymentez/get_acquirer_info",
                params: {
                    acquirer_id: paymentOptionId,
                    invoice_id: self.txContext.invoiceId,
                },
            })
                .then((acquirerInfo) => {
                    this.paymentezInfo = acquirerInfo;
                })
                .then(() => {
                    var paymentCheckout = this._prepatePaymentezModal(
                        provider,
                        paymentOptionId,
                        this.paymentezInfo.client_app_code,
                        this.paymentezInfo.client_app_key,
                        this.paymentezInfo.env_mode
                    );
                    var order_data = this.paymentezInfo.order_data;
                    var order_installments_type =
                        this.paymentezInfo.order_installments_type;
                    paymentCheckout.open({
                        user_id: order_data.user_id,
                        user_email: order_data.user_email,
                        user_phone: order_data.user_phone,
                        order_description: order_data.order_description,
                        order_amount: order_data.order_amount,
                        order_vat: order_data.order_vat,
                        order_reference: order_data.order_reference,
                        order_installments_type: order_installments_type,
                        order_taxable_amount: order_data.order_taxable_amount,
                        order_tax_percentage: order_data.order_tax_percentage,
                    });
                })
                .guardedCatch((error) => {
                    error.event.preventDefault();
                    this._displayError(
                        _t("Server Error"),
                        _t("An error occurred when displayed this payment form."),
                        error.message.data.message
                    );
                });
        },
        _processDirectPayment: function (provider, acquirerId, processingValues) {
            if (provider !== "paymentez") {
                return this._super(...arguments);
            }
            return this._rpc({
                route: this.txContext.transactionRoute,
                params: this._prepareTransactionRouteParams(
                    "paymentez",
                    acquirerId,
                    "direct"
                ),
            })
                .then(() =>
                    this._rpc({
                        route: "/payment/paymentez/payment",
                        params: {
                            response_data: processingValues,
                        },
                    })
                )
                .then(() => {
                    window.location = "/payment/status";
                });
        },
    };

    checkoutForm.include(paymentezMixin);
    manageForm.include(paymentezMixin);
});
