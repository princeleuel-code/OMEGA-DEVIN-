import unittest


from chimera.intelligence.online_hmm import OnlineGaussianHMM


class TestOnlineHMM(unittest.TestCase):
    def test_filters_switch_on_large_observations(self) -> None:
        # Two states: low-variance vs high-variance, same mean.
        hmm = OnlineGaussianHMM(
            transition=[[0.98, 0.02], [0.02, 0.98]],
            means=[0.0, 0.0],
            variances=[1.0, 25.0],
            learning_rate=0.0,  # keep parameters fixed for deterministic test
        )

        # Small observations should favor low-variance state (index 0).
        for _ in range(30):
            probs = hmm.update(0.1)
        self.assertGreater(probs[0], 0.7)

        # Large observations should favor high-variance state (index 1).
        for _ in range(30):
            probs = hmm.update(5.0)
        self.assertGreater(probs[1], 0.7)


if __name__ == "__main__":
    unittest.main()

