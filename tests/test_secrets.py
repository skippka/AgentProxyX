import unittest

from agentproxyx.secrets import find_secrets, redact_text


class SecretTests(unittest.TestCase):
    def test_openai_key_is_detected_and_redacted(self):
        text = "token sk-abcdefghijklmnopqrstuvwxyz123456"
        redacted, findings = redact_text(text)
        self.assertEqual(len(findings), 1)
        self.assertIn("[REDACTED]:OpenAI API key", redacted)

    def test_plain_text_has_no_findings(self):
        self.assertEqual(find_secrets("hello world"), [])


if __name__ == "__main__":
    unittest.main()

