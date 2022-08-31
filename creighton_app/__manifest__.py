{
    "name": "Creighton App",
    "version": "13.0.1.0.0",
    "summary": "Creighton App",
    "category": "Customizations",
    "author": "Christopher Ormaza",
    "website": "https://corac.solutions",
    "license": "AGPL-3",
    "depends": ["base", "contacts", "mail"],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "views/assets.xml",
        "views/root_menu.xml",
        "views/daily_register_view.xml",
    ],
    "qweb": [
        "static/src/xml/widget_creighton.xml",
    ],
    "demo": [""],
    "installable": True,
    "auto_install": False,
    "external_dependencies": {
        "python": [],
    },
}
