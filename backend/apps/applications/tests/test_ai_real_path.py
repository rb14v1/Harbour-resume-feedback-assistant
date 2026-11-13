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

    @override_settings(OPENAI_API_KEY="sk-test-key")
    def test_real_path_falls_back_when_the_client_cannot_be_constructed(self):
        """Regression: a deploy failed because the client was built outside
        the try block.

        openai <= 1.55.2 raises TypeError from OpenAI(...) itself when httpx
        >= 0.28 is installed. Construction used to sit above the try, so that
        fault escaped this function rather than degrading to the stub, and it
        took a database migration - and the whole deploy - down with it. Any
        failure to construct a client must look the same as a failed call.
        """
        with patch("openai.OpenAI", side_effect=TypeError(
            "Client.__init__() got an unexpected keyword argument 'proxies'"
        )):
            result = ai.generate_resume_feedback("my resume", "the job description")
        self.assertTrue(result["feedback"].startswith(ai.STUB_PREFIX))
        self.assertTrue(result["cover_letter_draft"])

    @override_settings(OPENAI_API_KEY="sk-test-key")
    def test_real_path_falls_back_when_openai_cannot_be_imported(self):
        """The import sits inside _client() for the same reason: an absent or
        broken `openai` install degrades to the stub instead of raising."""
        with patch("apps.common.ai._client", side_effect=ImportError("no openai")):
            result = ai.generate_resume_feedback("my resume", "the job description")
        self.assertTrue(result["feedback"].startswith(ai.STUB_PREFIX))

    @override_settings(OPENAI_API_KEY="sk-test-key", OPENAI_BASE_URL="")
    def test_client_omits_base_url_when_unset(self):
        """Unset means api.openai.com - base_url is left out of the call
        entirely rather than passed as an empty string or None, either of
        which would override the library's own default with nothing."""
        with patch("openai.OpenAI") as mock_openai:
            ai._client()
        _, kwargs = mock_openai.call_args
        self.assertNotIn("base_url", kwargs)
        self.assertEqual(kwargs["api_key"], "sk-test-key")

    @override_settings(
        OPENAI_API_KEY="sk-test-key",
        OPENAI_BASE_URL="https://example.openai.azure.com/openai/v1/",
    )
    def test_client_uses_base_url_when_set(self):
        """Regression: a platform-provisioned Azure OpenAI key was being sent
        to api.openai.com, which rejects it. OPENAI_BASE_URL points the stock
        client at Azure's OpenAI-compatible surface with no other change."""
        with patch("openai.OpenAI") as mock_openai:
            ai._client()
        _, kwargs = mock_openai.call_args
        self.assertEqual(
            kwargs["base_url"], "https://example.openai.azure.com/openai/v1/"
        )

    @override_settings(OPENAI_API_KEY="sk-test-key")
    def test_allow_remote_false_never_calls_out_even_with_a_key(self):
        """Regression: the seed migration made one live model call per demo
        row whenever a key was present in the environment - ten calls on every
        deploy, each able to fail it. allow_remote=False is how a caller that
        must not depend on a network service says so."""
        with patch("apps.common.ai._client") as mock_client:
            result = ai.generate_resume_feedback(
                "my resume", "the job description", allow_remote=False
            )
        mock_client.assert_not_called()
        self.assertTrue(result["feedback"].startswith(ai.STUB_PREFIX))

    def test_seed_migration_passes_allow_remote_false(self):
        """Pins the call site itself, not just the capability: applying
        migrations must never reach a model.

        The migration module cannot be imported by name (it starts with a
        digit), so this reads the call site out of the source. Crude, but it
        fails loudly if someone drops the argument.
        """
        import importlib.util
        from pathlib import Path

        source = (
            Path(__file__).resolve().parents[1]
            / "migrations"
            / "0002_seed_demo_data.py"
        ).read_text(encoding="utf-8")
        self.assertIn("generate_resume_feedback(", source)
        self.assertIn("allow_remote=False", source)
        # And it is importable/valid Python, so the assertion above is not
        # passing against a file that no longer loads.
        spec = importlib.util.spec_from_file_location(
            "seed_demo_data_under_test",
            Path(__file__).resolve().parents[1] / "migrations" / "0002_seed_demo_data.py",
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(hasattr(module, "seed_demo_data"))

