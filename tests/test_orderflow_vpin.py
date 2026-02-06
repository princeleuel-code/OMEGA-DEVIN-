import unittest


from chimera.orderflow.vpin import Trade, build_volume_buckets, compute_vpin


class TestVPIN(unittest.TestCase):
    def test_vpin_higher_for_imbalanced_flow(self) -> None:
        # 80 buys, 20 sells, all size=1.0
        trades = [Trade(price=100.0, size=1.0, is_buy=True) for _ in range(80)] + [
            Trade(price=100.0, size=1.0, is_buy=False) for _ in range(20)
        ]

        buckets = build_volume_buckets(trades, bucket_volume=10.0)
        self.assertEqual(len(buckets), 10)

        vpin = compute_vpin(trades, bucket_volume=10.0, window_buckets=5)
        self.assertIsNotNone(vpin)
        assert vpin is not None
        self.assertGreater(vpin, 0.2)

    def test_vpin_near_zero_for_balanced_flow(self) -> None:
        trades = []
        for _ in range(50):
            trades.append(Trade(price=100.0, size=1.0, is_buy=True))
            trades.append(Trade(price=100.0, size=1.0, is_buy=False))

        vpin = compute_vpin(trades, bucket_volume=10.0, window_buckets=5)
        self.assertIsNotNone(vpin)
        assert vpin is not None
        self.assertLess(vpin, 0.05)


if __name__ == "__main__":
    unittest.main()

