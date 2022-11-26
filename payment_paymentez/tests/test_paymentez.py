from odoo.tests import tagged

from .common import PaymentezCommon


@tagged("post_install", "-at_install")
class PaymentezTest(PaymentezCommon):
    def setUp(self):
        super(PaymentezTest, self).setUp()

    def test_success_transaction(self):
        pass

    def test_pending_transaction(self):
        pass

    def test_failure_transaction(self):
        pass

    def test_refund_transaction(self):
        pass
