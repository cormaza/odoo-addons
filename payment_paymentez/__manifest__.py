{
    "name": "Paymentez Payment Acquirer",
    "version": "15.0.1.0.0",
    "category": "Accounting/Payment Acquirers",
    "sequence": 30,
    "summary": "Payment Acquirer: Paymentez Implementation",
    "author": "Christopher Ormaza",
    "website": "https://github.com/cormaza/odoo-addons",
    "depends": ["payment", "website_sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/payment_views.xml",
        "views/payment_paymentez_templates.xml",
        "data/payment_acquirer_data.xml",
    ],
    "application": True,
    "uninstall_hook": "uninstall_hook",
    "assets": {
        "web.assets_frontend": [
            "payment_paymentez/static/src/scss/payment_paymentez.scss",
            "payment_paymentez/static/src/js/payment_form.js",
        ],
    },
    "license": "AGPL-3",
}
