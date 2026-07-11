"""Raw passthrough multi-turn chat history → LLM messages."""
from __future__ import annotations

import os
import unittest
from unittest import mock


class RawPassthroughHistoryTests(unittest.TestCase):
    def test_includes_prior_turns_before_current_user(self):
        from openai_helper import _build_raw_passthrough_llm_messages

        history = [
            {"role": "user", "text": "Kya mera partner commitment ke liye ready hai?"},
            {"role": "assistant", "text": "Haan, mostly ready dikhta hai."},
        ]
        msgs, stats = _build_raw_passthrough_llm_messages(
            system_prompt="SYS",
            user_payload="Par agar woh ignore kare?",
            history=history,
            current_topic="marriage",
            current_question="Par agar woh ignore kare?",
        )
        self.assertEqual(msgs[0], {"role": "system", "content": "SYS"})
        self.assertEqual(msgs[-1], {"role": "user", "content": "Par agar woh ignore kare?"})
        self.assertEqual(len(msgs), 4)  # system + 2 history + current
        self.assertGreaterEqual(stats.get("out", 0), 2)

    def test_dedupes_current_question_on_regenerate(self):
        from openai_helper import _build_raw_passthrough_llm_messages

        q = "Kya mera partner serious hai?"
        history = [
            {"role": "user", "text": q},
        ]
        msgs, _ = _build_raw_passthrough_llm_messages(
            system_prompt="SYS",
            user_payload=q,
            history=history,
            current_topic="marriage",
            current_question=q,
        )
        user_msgs = [m for m in msgs if m["role"] == "user"]
        self.assertEqual(len(user_msgs), 1)
        self.assertEqual(user_msgs[0]["content"], q)

    def test_skips_cosmo_greeting_bubble(self):
        from openai_helper import _build_raw_passthrough_llm_messages

        history = [
            {
                "role": "assistant",
                "text": "Hey, I'm Cosmo ✨ What would you like to know today?",
            },
            {"role": "user", "text": "Career kaisi rahegi?"},
            {"role": "assistant", "text": "Growth phase dikhta hai."},
        ]
        msgs, _ = _build_raw_passthrough_llm_messages(
            system_prompt="SYS",
            user_payload="Aur detail do",
            history=history,
            current_topic="career",
            current_question="Aur detail do",
        )
        contents = [m["content"] for m in msgs if m["role"] == "assistant"]
        self.assertFalse(any("Hey, I'm Cosmo" in c for c in contents))

    @mock.patch.dict(os.environ, {"RAW_PASSTHROUGH_CHAT_HISTORY": "0"})
    def test_killswitch_disables_history(self):
        from openai_helper import _build_raw_passthrough_llm_messages

        history = [
            {"role": "user", "text": "Pehla sawaal"},
            {"role": "assistant", "text": "Pehla jawab"},
        ]
        msgs, stats = _build_raw_passthrough_llm_messages(
            system_prompt="SYS",
            user_payload="Dusra sawaal",
            history=history,
            current_topic="general",
            current_question="Dusra sawaal",
        )
        self.assertEqual(len(msgs), 2)
        self.assertEqual(stats.get("strategy"), "disabled")


if __name__ == "__main__":
    unittest.main()
