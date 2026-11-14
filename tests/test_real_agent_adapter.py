"""Protocol checks only; these fixtures do not measure model quality."""

import io
import json
import unittest
from unittest.mock import patch

from src.real_agent import ChatController


class ChatControllerTests(unittest.TestCase):
    def test_model_action_receives_question_and_context_without_gold(self):
        captured = []

        def respond(request, timeout):
            payload = json.loads(request.data)
            captured.append(payload)
            action = ({"action": "search", "query": "poverty inequality"}
                      if not json.loads(payload["messages"][1]["content"])["retrieved_context"]
                      else {"action": "answer", "answer": "It fell [c1]", "citations": ["c1"]})
            body = {"choices": [{"message": {"content": json.dumps(action)}}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 8}}
            return io.BytesIO(json.dumps(body).encode("utf-8"))

        controller = ChatController(base_url="https://example.test/v1", model="test-model",
                                    api_key="test-key", timeout_seconds=5)
        with patch("urllib.request.urlopen", side_effect=respond):
            self.assertEqual(controller.decide("Question?", []),
                             {"action": "search", "query": "poverty inequality"})
            self.assertEqual(controller.decide("Question?", [{"context": "[c1] Evidence",
                                                             "queries": ["poverty inequality"]}])["action"],
                             "answer")
        self.assertEqual(len(controller.calls), 2)
        self.assertEqual(captured[0]["model"], "test-model")
        self.assertNotIn("gold", json.dumps(captured))

    def test_malformed_model_action_is_logged_as_error(self):
        body = {"choices": [{"message": {"content": "not JSON"}}]}
        controller = ChatController(base_url="http://localhost:11434/v1", model="test-model",
                                    api_key=None, timeout_seconds=5)
        with patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(body).encode())):
            with self.assertRaises(json.JSONDecodeError):
                controller.decide("Question?", [])
        self.assertEqual(controller.calls[0]["status"], "error")


if __name__ == "__main__":
    unittest.main()
