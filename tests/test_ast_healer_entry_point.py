# -*- coding: utf-8 -*-
"""ASTHealer entry-point enforcement configurability."""

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.healers.ast_healer import ASTHealer  # noqa: E402


class ASTHealerEntryPointTests(unittest.TestCase):
    def test_default_injects_generate_for_math_flow(self):
        code = "x = 1\n"
        healer = ASTHealer()
        healed, fixes = healer.heal(code)
        self.assertGreater(fixes, 0)
        self.assertIn("def generate(", healed)

    def test_require_entry_point_false_skips_injection(self):
        code = "def is_prime(n):\n    return n > 1\n"
        healer = ASTHealer(require_entry_point=False)
        healed, fixes = healer.heal(code)
        self.assertNotIn("def generate(", healed)
        self.assertNotIn("Fallback due to missing", healed)

    def test_custom_entry_point_name(self):
        code = "x = 1\n"
        healer = ASTHealer(entry_point="solve")
        healed, fixes = healer.heal(code)
        self.assertGreater(fixes, 0)
        self.assertIn("def solve(", healed)
        self.assertNotIn("def generate(", healed)


if __name__ == "__main__":
    unittest.main()
