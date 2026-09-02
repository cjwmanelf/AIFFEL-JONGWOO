"""shipping.shipping_fee 테스트. 이 파일은 수정 금지."""
import unittest

from shipping import shipping_fee


class ShippingFeeTest(unittest.TestCase):
    def test_over_threshold_is_free(self):
        self.assertEqual(shipping_fee(60_000, 1.0), 0)

    def test_exactly_at_threshold_is_free(self):
        # 무료배송 기준 '이상' 이므로 정확히 50,000원도 무료여야 한다.
        self.assertEqual(shipping_fee(50_000, 2.0), 0)

    def test_basic_fee(self):
        self.assertEqual(shipping_fee(10_000, 2.0), 4_000)

    def test_zero_weight(self):
        self.assertEqual(shipping_fee(0, 0), 3_000)

    def test_express_rounds_to_nearest_100(self):
        # 3000 + 500*1.3 = 3650, x1.5 = 5475 -> 100원 단위 반올림 = 5500
        self.assertEqual(shipping_fee(10_000, 1.3, express=True), 5_500)


if __name__ == "__main__":
    unittest.main()
