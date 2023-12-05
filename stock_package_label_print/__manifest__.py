{
    "name": "Stock Package Label Printing",
    "summary": """
        Print label for stock picking with package(s)
        """,
    "author": "Christopher Ormaza",
    "website": "https://github.com/cormaza/odoo-addons",
    "category": "Report",
    "version": "16.0.1.0.0",
    "depends": [
        "base",
        "stock",
        "base_address_extended",
        "product",
        "stock_picking_invoice_link",
    ],
    "data": [
        "report/report_stock_package_label_paperformat.xml",
        "report/report_stock_package_label_print.xml",
    ],
    "demo": [],
    "license": "LGPL-3",
}
