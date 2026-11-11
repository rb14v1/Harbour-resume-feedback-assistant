from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from apps.common import ai


def _mock_openai_response(content):
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


class AIRealPathTests(TestCase):
    """Exercises the real-mode (OPENAI_API_KEY set) branch with a mocked
    OpenAI client - no real network calls are made. Confirms the module
    correctly switches paths and defensively parses the model's response."""

    def test_is_stub_mode_true_without_key(self):
        with override_settings(OPENAI_API_KEY=""):
            self.assertTrue(ai.is_stub_mode())

    def test_is_stub_mode_false_with_key(self):
        with override_settings(OPENAI_API_KEY="sk-test-key"):
            self.assertFalse(ai.is_stub_mode())

    @override_settings(OPENAI_API_KEY="sk-test-key", OPENAI_CHAT_MODEL="gpt-5.4-mini")
    def test_real_path_parses_valid_json_response(self):
        content = (
            '{"feedback": "Great match overall.", '
            '"cover_letter_draft": "Dear Hiring Manager, ..."}'
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(content)
        with patch("openai.OpenAI", return_value=mock_client):
            result = ai.generate_resume_feedback("my resume", "the job description")
        self.assertEqual(result["feedback"], "Great match overall.")
        self.assertEqual(result["cover_letter_draft"], "Dear Hiring Manager, ...")
        mock_client.chat.completions.create.assert_called_once()
        _, kwargs = mock_client.chat.completions.create.call_args
        self.assertEqual(kwargs["model"], "gpt-5.4-mini")

    @override_settings(OPENAI_API_KEY="sk-test-key")
    def test_real_path_falls_back_on_malformed_json(self):
        content = "This is not JSON at all, sorry."
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(content)
        with patch("openai.OpenAI", return_value=mock_client):
            result = ai.generate_resume_feedback("my resume", "the job description")
        # Never crashes - falls back gracefully with non-empty strings.
        self.assertTrue(result["feedback"])
        self.assertTrue(result["cover_letter_draft"])

    @override_settings(OPENAI_API_KEY="sk-test-key")
    def test_real_path_falls_back_on_client_exception(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("network error")
        with patch("openai.OpenAI", return_value=mock_client):
            result = ai.generate_resume_feedback("my resume", "the job description")
        self.assertTrue(result["feedback"])
        self.assertTrue(result["cover_letter_draft"])

    @override_settings(OPENAI_API_KEY="sk-test-key")
    def test_real_path_parses_json_wrapped_in_code_fence(self):
        content = (
            "```json\n"
            '{"feedback": "Solid.", "cover_letter_draft": "Dear Team, ..."}'
            "\n```"
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(content)
        with patch("openai.OpenAI", return_value=mock_client):
            result = ai.generate_resume_feedback("my resume", "the job description")
        self.assertEqual(result["feedback"], "Solid.")
        self.assertEqual(result["cover_letter_draft"], "Dear Team, ...")

    def test_default_chat_model_setting(self):
        from django.conf import settings

        # Default is gpt-5.4-mini when OPENAI_CHAT_MODEL is unset in the
        # environment - deliberately different from the gpt-5.6-sol default
        # used by some sibling apps.
        self.assertEqual(settings.OPENAI_CHAT_MODEL, "gpt-5.4-mini")
