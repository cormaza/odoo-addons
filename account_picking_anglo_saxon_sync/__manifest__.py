{
    "name": "Invoice Picking Anglo Saxon Sync",
    "version": "15.0.1.0.0",
    "summary": "Invoice Picking Anglo Saxon Sync",
    "category": "Accounting",
    "author": "Christopher Ormaza",
    "website": "https://github.com/cormaza/odoo-addons",
    "license": "AGPL-3",
    "depends": [
        "stock_picking_invoice_link",
        "account",
        "sale",
        "sale_stock",
        "purchase",
    ],
    "data": [
        "views/account_move_view.xml",
        "views/stock_picking_view.xml",
    ],
    "demo": [
        "demo/data.xml",
    ],
    "installable": True,
    "auto_install": False,
    "external_dependencies": {
        "python": [],
    },
}
