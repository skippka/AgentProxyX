import unittest

from agentproxyx.cost import estimate_cost, estimate_tokens


class CostTests(unittest.TestCase):
    def test_token_estimate(self):
        self.assertEqual(estimate_tokens("abcd"), 1)
        self.assertEqual(estimate_tokens(""), 0)

    def test_cost_has_cache_savings(self):
        estimate = estimate_cost("a" * 4000, cacheable_chars=2000)
        self.assertGreater(estimate.total_cost, 0)
        self.assertGreater(estimate.cache_savings, 0)


if __name__ == "__main__":
    unittest.main()

