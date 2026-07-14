import unittest

from agentproxyx.config import DEFAULT_CONFIG
from agentproxyx.firewall import AgentFirewall


class FirewallTests(unittest.TestCase):
    def test_blocks_env_read(self):
        decision = AgentFirewall(DEFAULT_CONFIG).check_tool_call({"command": "cat .env", "files": [".env"]})
        self.assertFalse(decision.allowed)

    def test_allows_tests(self):
        decision = AgentFirewall(DEFAULT_CONFIG).check_tool_call({"command": "pytest tests", "files": ["tests/test_firewall.py"]})
        self.assertTrue(decision.allowed)


if __name__ == "__main__":
    unittest.main()

