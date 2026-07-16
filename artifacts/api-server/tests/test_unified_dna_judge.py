from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_unified import run_domain_llm_with_dna_judge


class _FakeCompletions:
    def __init__(self, outputs: list[str]):
        self.outputs = list(outputs)
        self.messages: list[list[dict[str, str]]] = []

    def create(self, **kwargs):
        self.messages.append(kwargs["messages"])
        text = self.outputs.pop(0)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=text))]
        )


class UnifiedDnaJudgeTests(unittest.TestCase):
    def test_failed_dna_is_rewritten_and_rejudged(self):
        completions = _FakeCompletions([
            "Generic answer.",
            json.dumps({
                "passed": False,
                "issues": ["wrong question focus"],
                "fix_hint": "answer the career question",
            }),
            "Career answer with Saturn in the 10th house as chart proof.",
            json.dumps({"passed": True, "issues": []}),
        ])
        client = SimpleNamespace(chat=SimpleNamespace(completions=completions))

        text, audit = run_domain_llm_with_dna_judge(
            client,
            model="test-model",
            messages=[{"role": "user", "content": "career?"}],
            max_tokens=200,
            question="Meri career kaisi rahegi?",
            meta={
                "answer_mode": "llm_chart",
                "question_dna_item": {
                    "user_wants": "Career outlook",
                    "intent": "career_outlook",
                },
            },
            domain="career",
        )

        self.assertIn("Saturn", text)
        self.assertEqual(audit["attempts"], 2)
        self.assertTrue(audit["dna_retry"])
        self.assertTrue(audit["passed"])
        self.assertTrue(audit["dna_judge_retry"]["passed"])

    def test_knowledge_answer_does_not_require_chart_proof(self):
        completions = _FakeCompletions([
            "Mahadasha is a broad planetary period.",
            json.dumps({"passed": True, "issues": []}),
        ])
        client = SimpleNamespace(chat=SimpleNamespace(completions=completions))

        _, audit = run_domain_llm_with_dna_judge(
            client,
            model="test-model",
            messages=[{"role": "user", "content": "Mahadasha kya hai?"}],
            max_tokens=200,
            question="Mahadasha kya hoti hai?",
            meta={"answer_mode": "llm_knowledge"},
            domain="general",
        )

        judge_prompt = completions.messages[1][0]["content"]
        self.assertIn("chart proof is NOT required", judge_prompt)
        self.assertTrue(audit["passed"])


if __name__ == "__main__":
    unittest.main()
