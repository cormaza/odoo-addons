from odoo import api, models


class ReportStockPackageLabelPrint(models.AbstractModel):

    _name = "report.stock_package_label_print.report_splp"
    _description = "Report Package Label Print"

    @api.model
    def _get_report_values(self, docids, data=None):
        records = self.env["stock.picking"].browse(docids)
        return {
            "docs": records,
            "report_type": data.get("report_type") if data else "",
            "data": data,
        }
