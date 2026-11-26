# Copyright 2026 Christopher Ormaza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from lxml import html

from odoo import Command
from odoo.tests import tagged
from odoo.tools.safe_eval import safe_eval

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

PNG_1X1_B64 = (
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    b"+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


@tagged("post_install", "-at_install")
class TestStockPackageLabelPrint(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report = cls.env.ref("stock_package_label_print.report_package_label")
        cls.paperformat = cls.env.ref("stock_package_label_print.label_10_x_10")
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.picking_type_out = cls.warehouse.out_type_id
        cls.location_src = cls.warehouse.lot_stock_id
        cls.location_dest = cls.env.ref("stock.stock_location_customers")
        cls.product = cls.env["product.product"].create(
            {
                "name": "SPLP Test Product",
                "type": "consu",
                "is_storable": True,
                "list_price": 10.0,
            }
        )
        cls.country = cls.env.ref("base.ec")
        cls.state = cls.env["res.country.state"].create(
            {
                "name": "Pichincha Test",
                "code": "P-SPLP",
                "country_id": cls.country.id,
            }
        )
        cls.city_rec = cls.env["res.city"].create(
            {
                "name": "Quito Test",
                "country_id": cls.country.id,
                "state_id": cls.state.id,
            }
        )

    def _create_picking(self, partner=False, origin=False, invoice_ids=None, qty=1.0):
        vals = {
            "picking_type_id": self.picking_type_out.id,
            "location_id": self.location_src.id,
            "location_dest_id": self.location_dest.id,
            "company_id": self.env.company.id,
            "partner_id": partner.id if partner else False,
            "origin": origin,
            "move_ids": [
                Command.create(
                    {
                        "product_id": self.product.id,
                        "product_uom_qty": qty,
                        "product_uom": self.product.uom_id.id,
                        "location_id": self.location_src.id,
                        "location_dest_id": self.location_dest.id,
                    }
                )
            ],
        }
        if invoice_ids:
            vals["invoice_ids"] = [Command.set(invoice_ids.ids)]
        return self.env["stock.picking"].create(vals)

    def _create_out_invoice(self, partner):
        return self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "journal_id": self.company_data["default_journal_sale"].id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "quantity": 1.0,
                            "price_unit": 10.0,
                        }
                    )
                ],
            }
        )

    def _render_html(self, pickings):
        rendered_bytes, report_type = self.report._render_qweb_html(
            self.report.id, pickings.ids
        )
        self.assertEqual(report_type, "html")
        raw_html = rendered_bytes.decode("utf-8")
        doc = html.fromstring(raw_html)
        containers = doc.xpath(
            "//div[contains(concat(' ', normalize-space(@class), ' '), ' container ')]"
        )
        text = " ".join(doc.xpath("//body//text()"))
        return raw_html, doc, containers, text

    def test_01_full_label_all_sections_city_id_and_multiple_invoices(self):
        self.env.company.logo = PNG_1X1_B64
        parent_partner = self.env["res.partner"].create(
            {
                "name": "Cliente Comercial Matrix",
                "is_company": True,
            }
        )
        delivery_partner = self.env["res.partner"].create(
            {
                "name": "Sucursal Entrega Norte",
                "type": "delivery",
                "parent_id": parent_partner.id,
                "street": "Av. Amazonas N35-100",
                "street2": "Edificio Matriz Piso 4",
                "vat": "1790011223001",
                "phone": "+593 99 123 4567",
                "country_id": self.country.id,
                "state_id": self.state.id,
                "city_id": self.city_rec.id,
                "city": "Fallback City Text",
            }
        )
        inv_1 = self._create_out_invoice(parent_partner)
        inv_2 = self._create_out_invoice(parent_partner)
        picking = self._create_picking(
            partner=delivery_partner,
            origin="SO-2026-0001",
            invoice_ids=inv_1 | inv_2,
        )

        raw_html, doc, containers, text = self._render_html(picking)

        self.assertEqual(len(containers), 1)
        logo_imgs = doc.xpath("//img[contains(@class, 'company-logo')]")
        self.assertEqual(len(logo_imgs), 1)
        self.assertIn("data:image/png;base64,", logo_imgs[0].get("src", ""))

        self.assertIn("ORDEN DE PEDIDO:", text)
        self.assertIn("SO-2026-0001", text)
        self.assertIn(f"{inv_1.display_name} / {inv_2.display_name}", raw_html)
        self.assertIn("NOTA DE ENVIO:", text)
        self.assertIn(picking.name, text)
        self.assertIn("CLIENTE:", text)
        self.assertIn("Cliente Comercial Matrix", text)
        self.assertNotIn("Sucursal Entrega Norte", text)
        self.assertIn("Dirección de Envío:", text)
        self.assertIn("Av. Amazonas N35-100 Edificio Matriz Piso 4", raw_html)
        self.assertIn("RUC/CI:", text)
        self.assertIn("1790011223001", text)
        self.assertIn("TELEFONO(S):", text)
        self.assertIn("+593 99 123 4567", text)
        self.assertIn("PROVINCIA:", text)
        self.assertIn("Pichincha Test", text)
        self.assertIn("CIUDAD:", text)
        self.assertIn("Quito Test", text)
        self.assertNotIn("Fallback City Text", raw_html)
        self.assertNotIn("PAQUETES:", text)

    def test_02_minimal_label_no_partner_no_logo_no_optional_fields(self):
        self.env.company.logo = False
        picking = self._create_picking(partner=False, origin=False)

        _raw_html, doc, containers, text = self._render_html(picking)

        self.assertEqual(len(containers), 1)
        self.assertFalse(doc.xpath("//img[contains(@class, 'company-logo')]"))
        self.assertIn("NOTA DE ENVIO:", text)
        self.assertIn(picking.name, text)
        for absent in (
            "ORDEN DE PEDIDO:",
            "CLIENTE:",
            "Dirección de Envío:",
            "RUC/CI:",
            "TELEFONO(S):",
            "PROVINCIA:",
            "CIUDAD:",
            "PAQUETES:",
        ):
            self.assertNotIn(absent, text)

    def test_03_partner_phone_and_address_edge_cases(self):
        # Subcase A: partner without phone (Odoo 19 removed mobile),
        # street without street2, city text fallback without city_id.
        partner_no_phone = self.env["res.partner"].create(
            {
                "name": "Partner Sin Telefono",
                "street": "Calle Unica 123",
                "street2": False,
                "phone": False,
                "vat": False,
                "state_id": False,
                "city_id": False,
                "city": "Guayaquil Fallback",
            }
        )
        picking_a = self._create_picking(partner=partner_no_phone)
        raw_a, _doc_a, containers_a, text_a = self._render_html(picking_a)
        self.assertEqual(len(containers_a), 1)
        self.assertIn("CLIENTE:", text_a)
        self.assertIn("Partner Sin Telefono", text_a)
        self.assertIn("Dirección de Envío:", text_a)
        self.assertIn("Calle Unica 123", raw_a)
        self.assertIn("CIUDAD:", text_a)
        self.assertIn("Guayaquil Fallback", text_a)
        for absent in ("TELEFONO(S):", "RUC/CI:", "PROVINCIA:"):
            self.assertNotIn(absent, text_a)

        # Subcase B: partner with phone set, street=False (even if street2 set),
        # and no city/city_id.
        partner_with_phone = self.env["res.partner"].create(
            {
                "name": "Partner Con Telefono",
                "phone": "02-222-3333",
                "street": False,
                "street2": "Piso 3 Ignorado",
                "city_id": False,
                "city": False,
            }
        )
        picking_b = self._create_picking(partner=partner_with_phone)
        raw_b, _doc_b, containers_b, text_b = self._render_html(picking_b)
        self.assertEqual(len(containers_b), 1)
        self.assertIn("TELEFONO(S):", text_b)
        self.assertIn("02-222-3333", text_b)
        self.assertNotIn("Dirección de Envío:", text_b)
        self.assertNotIn("Piso 3 Ignorado", raw_b)
        self.assertNotIn("CIUDAD:", text_b)

        # Subcase C: delivery partner with name=False must not crash concatenation.
        partner_unnamed = self.env["res.partner"].create(
            {"type": "delivery", "name": False}
        )
        picking_c = self._create_picking(partner=partner_unnamed)
        _raw_c, _doc_c, containers_c, text_c = self._render_html(picking_c)
        self.assertEqual(len(containers_c), 1)
        self.assertNotIn("CLIENTE:", text_c)

    def test_04_single_invoice_and_multi_picking_batch(self):
        partner = self.env["res.partner"].create({"name": "Partner Batch"})
        inv = self._create_out_invoice(partner)
        picking_1 = self._create_picking(
            partner=partner, origin="SO-BATCH-1", invoice_ids=inv
        )
        picking_2 = self._create_picking(partner=partner, origin="SO-BATCH-2")

        raw_html, _doc, containers, text = self._render_html(picking_1 | picking_2)

        self.assertEqual(len(containers), 2)
        self.assertIn(picking_1.name, text)
        self.assertIn(picking_2.name, text)
        self.assertIn(inv.display_name, raw_html)
        self.assertNotIn(f"{inv.display_name} /", raw_html)

    def test_05_packages_assigned_single_and_done_pickings(self):
        partner = self.env["res.partner"].create({"name": "Partner Paquetes"})
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.location_src, 20.0
        )

        # Subcase A: assigned picking with 2 distinct packages
        pack_1 = self.env["stock.package"].create({"name": "PACK-A1"})
        pack_2 = self.env["stock.package"].create({"name": "PACK-A2"})
        picking_multi = self._create_picking(partner=partner, qty=4.0)
        picking_multi.action_confirm()
        picking_multi.action_assign()
        picking_multi.move_line_ids.unlink()
        self.env["stock.move.line"].create(
            [
                {
                    "picking_id": picking_multi.id,
                    "move_id": picking_multi.move_ids[0].id,
                    "product_id": self.product.id,
                    "product_uom_id": self.product.uom_id.id,
                    "location_id": self.location_src.id,
                    "location_dest_id": self.location_dest.id,
                    "quantity": 2.0,
                    "result_package_id": pack_1.id,
                },
                {
                    "picking_id": picking_multi.id,
                    "move_id": picking_multi.move_ids[0].id,
                    "product_id": self.product.id,
                    "product_uom_id": self.product.uom_id.id,
                    "location_id": self.location_src.id,
                    "location_dest_id": self.location_dest.id,
                    "quantity": 2.0,
                    "result_package_id": pack_2.id,
                },
            ]
        )
        self.assertEqual(picking_multi.packages_count, 2)
        _raw_a, _doc_a, containers_a, text_a = self._render_html(picking_multi)
        self.assertEqual(len(containers_a), 2)
        self.assertIn("PAQUETES: 1 de 2", text_a)
        self.assertIn("PAQUETES: 2 de 2", text_a)

        # Subcase B: assigned picking with 2 lines pointing to the same package
        pack_single = self.env["stock.package"].create({"name": "PACK-SINGLE"})
        picking_single = self._create_picking(partner=partner, qty=4.0)
        picking_single.action_confirm()
        picking_single.action_assign()
        picking_single.move_line_ids.unlink()
        self.env["stock.move.line"].create(
            [
                {
                    "picking_id": picking_single.id,
                    "move_id": picking_single.move_ids[0].id,
                    "product_id": self.product.id,
                    "product_uom_id": self.product.uom_id.id,
                    "location_id": self.location_src.id,
                    "location_dest_id": self.location_dest.id,
                    "quantity": 2.0,
                    "result_package_id": pack_single.id,
                },
                {
                    "picking_id": picking_single.id,
                    "move_id": picking_single.move_ids[0].id,
                    "product_id": self.product.id,
                    "product_uom_id": self.product.uom_id.id,
                    "location_id": self.location_src.id,
                    "location_dest_id": self.location_dest.id,
                    "quantity": 2.0,
                    "result_package_id": pack_single.id,
                },
            ]
        )
        self.assertEqual(picking_single.packages_count, 1)
        _raw_b, _doc_b, containers_b, text_b = self._render_html(picking_single)
        self.assertEqual(len(containers_b), 1)
        self.assertIn("PAQUETES: 1 de 1", text_b)
        self.assertNotIn("de 2", text_b)

        # Subcase C: validated (done) picking with 2 distinct packages
        pack_done_1 = self.env["stock.package"].create({"name": "PACK-DONE-1"})
        pack_done_2 = self.env["stock.package"].create({"name": "PACK-DONE-2"})
        picking_done = self._create_picking(partner=partner, qty=4.0)
        picking_done.action_confirm()
        picking_done.action_assign()
        picking_done.move_line_ids.unlink()
        self.env["stock.move.line"].create(
            [
                {
                    "picking_id": picking_done.id,
                    "move_id": picking_done.move_ids[0].id,
                    "product_id": self.product.id,
                    "product_uom_id": self.product.uom_id.id,
                    "location_id": self.location_src.id,
                    "location_dest_id": self.location_dest.id,
                    "quantity": 2.0,
                    "picked": True,
                    "result_package_id": pack_done_1.id,
                },
                {
                    "picking_id": picking_done.id,
                    "move_id": picking_done.move_ids[0].id,
                    "product_id": self.product.id,
                    "product_uom_id": self.product.uom_id.id,
                    "location_id": self.location_src.id,
                    "location_dest_id": self.location_dest.id,
                    "quantity": 2.0,
                    "picked": True,
                    "result_package_id": pack_done_2.id,
                },
            ]
        )
        picking_done.button_validate()
        self.assertEqual(picking_done.state, "done")
        self.assertEqual(picking_done.packages_count, 2)
        _raw_c, _doc_c, containers_c, text_c = self._render_html(picking_done)
        self.assertEqual(len(containers_c), 2)
        self.assertIn("PAQUETES: 1 de 2", text_c)
        self.assertIn("PAQUETES: 2 de 2", text_c)

    def test_06_report_values_print_name_and_pdf_render(self):
        partner = self.env["res.partner"].create({"name": "Partner PDF"})
        picking = self._create_picking(partner=partner, origin="SO-PDF-1")

        self.assertEqual(
            self.report._get_report_from_name("stock_package_label_print.report_splp"),
            self.report,
        )
        self.assertEqual(self.report.paperformat_id, self.paperformat)

        report_model = self.env["report.stock_package_label_print.report_splp"]
        values_no_data = report_model._get_report_values(picking.ids)
        self.assertEqual(values_no_data["docs"], picking)
        self.assertEqual(values_no_data["report_type"], "")
        self.assertIsNone(values_no_data["data"])

        values_with_data = report_model._get_report_values(
            picking.ids, data={"report_type": "pdf"}
        )
        self.assertEqual(values_with_data["docs"], picking)
        self.assertEqual(values_with_data["report_type"], "pdf")
        self.assertEqual(values_with_data["data"], {"report_type": "pdf"})

        self.assertEqual(
            safe_eval(self.report.print_report_name, {"object": picking}),
            f"Package label for Picking - {picking.name}",
        )

        html_content, fallback_type = self.report._render_qweb_pdf(
            self.report.id, picking.ids
        )
        self.assertEqual(fallback_type, "html")
        self.assertIn(picking.name.encode(), html_content)

        with patch.object(
            type(self.report),
            "_run_wkhtmltopdf",
            return_value=b"%PDF-1.4\n",
        ) as mock_wkhtmltopdf:
            pdf_content, report_type = self.report.with_context(
                force_report_rendering=True
            )._render_qweb_pdf(self.report.id, picking.ids)
        self.assertEqual(report_type, "pdf")
        self.assertTrue(pdf_content.startswith(b"%PDF"))
        mock_wkhtmltopdf.assert_called_once()
        bodies = mock_wkhtmltopdf.call_args.args[0]
        self.assertEqual(len(bodies), 1)
        self.assertIn(picking.name, bodies[0])
