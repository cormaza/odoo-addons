from odoo_test_helper import FakeModelLoader

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestRestrictAnalyticTagUnlink(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        cls.addClassCleanup(cls.loader.restore_registry)
        from .fake_model import FakeRestrictionTestModel

        cls.loader.update_registry((FakeRestrictionTestModel,))

    def test_unlink_tag(self):
        self.tag = self.env["account.analytic.tag"].create({"name": "Test Tag"})
        self.env["fake.restriction.test.model"].create(
            {"name": "Test", "analytic_tag_ids": [(4, self.tag.id)]}
        )
        with self.assertRaises(UserError):
            self.tag.unlink()
