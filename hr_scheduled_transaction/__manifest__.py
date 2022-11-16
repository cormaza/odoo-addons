{
    "name": "Payroll Inputs Scheduled",
    "summary": """Add Structure to add possibility to schedule inputs on payroll""",
    "author": "Christopher Ormaza",
    "website": "https://github.com/cormaza/odoo-addons",
    "category": "Human Resources",
    "version": "15.0.1.0.0",
    "depends": [
        "base",
        "hr",
        "hr_payroll",
        "hr_payroll_account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/scheduled_transaction_view.xml",
        "views/payslip_view.xml",
        "views/contract_view.xml",
    ],
    "demo": [],
    "license": "AGPL-3",
}
