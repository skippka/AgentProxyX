import unittest

from agentproxyx.agents import get_preset, presets


class AgentPresetTests(unittest.TestCase):
    def test_many_agents_are_available(self):
        all_presets = presets()
        for key in ["claude-code", "codex-cli", "gemini-cli", "aider", "cursor", "openhands", "cody"]:
            self.assertIn(key, all_presets)

    def test_env_uses_requested_port(self):
        preset = get_preset("claude-code", 9090)
        self.assertIn("9090", preset.env["ANTHROPIC_BASE_URL"])


if __name__ == "__main__":
    unittest.main()

