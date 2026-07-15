import tempfile
import unittest
from pathlib import Path

from agentproxyx.config import DEFAULT_CONFIG
from agentproxyx.firewall import AgentFirewall
from agentproxyx.mcp import inspect_mcp_message, normalize_mcp_tool_call, wrap_mcp_server
from agentproxyx.replay import ReplayStore


class MCPWrapperTests(unittest.TestCase):
    def _store(self) -> ReplayStore:
        path = Path(tempfile.mkdtemp()) / "replay.sqlite"
        return ReplayStore(path)

    def test_normalizes_bash_tool_command(self):
        message = {"method": "tools/call", "params": {"name": "bash", "arguments": {"command": "cat .env"}}}
        self.assertEqual(normalize_mcp_tool_call(message)["command"], "cat .env")

    def test_blocks_file_tool_payloads(self):
        message = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "read_file", "arguments": {"path": ".env"}}}
        inspection = inspect_mcp_message(message, AgentFirewall(DEFAULT_CONFIG), self._store())
        self.assertFalse(inspection.should_forward)
        self.assertEqual(inspection.response["id"], 1)
        self.assertIn("File access denied", inspection.response["error"]["data"]["reason"])

    def test_blocks_network_tool_metadata_urls(self):
        message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "fetch", "arguments": {"url": "http://169.254.169.254/latest/meta-data"}},
        }
        inspection = inspect_mcp_message(message, AgentFirewall(DEFAULT_CONFIG), self._store())
        self.assertFalse(inspection.should_forward)
        self.assertIn("URL access denied", inspection.response["error"]["data"]["reason"])

    def test_logs_allowed_tool_calls(self):
        store = self._store()
        message = {"method": "tools/call", "params": {"name": "bash", "arguments": {"command": "python -m unittest discover -s tests"}}}
        inspection = inspect_mcp_message(message, AgentFirewall(DEFAULT_CONFIG), store)
        self.assertTrue(inspection.should_forward)
        self.assertEqual(store.recent()[0]["kind"], "tool_allowed")

    def test_wrap_requires_command_after_separator(self):
        with self.assertRaises(ValueError):
            wrap_mcp_server(["--"], AgentFirewall(DEFAULT_CONFIG), self._store())


if __name__ == "__main__":
    unittest.main()
