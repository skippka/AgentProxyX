import json
import unittest

from agentproxyx.cache import cache_policy_for, maybe_optimize_anthropic_payload, optimize_payload
from agentproxyx.config import DEFAULT_CONFIG


class CachePolicyTests(unittest.TestCase):
    def test_anthropic_policy_adds_ephemeral_system_cache_control(self):
        body = json.dumps({"system": "a" * 4000, "messages": []}).encode("utf-8")
        result = optimize_payload(body, DEFAULT_CONFIG)
        payload = json.loads(result.body.decode("utf-8"))

        self.assertTrue(result.changed)
        self.assertEqual(result.provider, "anthropic")
        self.assertEqual(result.cacheable_chars, 4000)
        self.assertEqual(payload["system"][0]["cache_control"]["type"], "ephemeral")

    def test_openai_policy_is_noop(self):
        config = {**DEFAULT_CONFIG, "costs": {**DEFAULT_CONFIG["costs"], "provider": "openai"}}
        body = json.dumps({"system": "a" * 4000, "messages": []}).encode("utf-8")
        result = optimize_payload(body, config)

        self.assertFalse(result.changed)
        self.assertEqual(result.body, body)
        self.assertEqual(result.cacheable_chars, 0)
        self.assertEqual(cache_policy_for(config).provider, "openai")

    def test_openrouter_policy_is_noop(self):
        config = {**DEFAULT_CONFIG, "costs": {**DEFAULT_CONFIG["costs"], "provider": "openrouter"}}
        body = json.dumps({"tools": [{"name": "x", "description": "a" * 5000}]}).encode("utf-8")
        result = optimize_payload(body, config)

        self.assertFalse(result.changed)
        self.assertEqual(result.body, body)
        self.assertEqual(result.cacheable_chars, 0)

    def test_non_json_passthrough(self):
        body = b"not json"
        result = optimize_payload(body, DEFAULT_CONFIG)

        self.assertFalse(result.changed)
        self.assertEqual(result.body, body)

    def test_legacy_anthropic_helper_still_returns_tuple(self):
        body = json.dumps({"system": "a" * 4000}).encode("utf-8")
        optimized, changed, cacheable_chars = maybe_optimize_anthropic_payload(body, DEFAULT_CONFIG)

        self.assertTrue(changed)
        self.assertGreater(len(optimized), len(body))
        self.assertEqual(cacheable_chars, 4000)


if __name__ == "__main__":
    unittest.main()
