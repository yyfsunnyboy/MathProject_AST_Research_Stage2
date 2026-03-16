# -*- coding: utf-8 -*-
"""
=============================================================================
tests/radical_auto_test.py
=============================================================================
Autonomous Repair-Loop Test for jh_數學2上_FourOperationsOfRadicals.

Coverage
--------
Suite 1  — DomainFunctionHelper (all 11 patterns × 3 difficulties)
Suite 2  — Scaffold assembly (PREFIX + decisions + SUFFIX syntax + execution)
Suite 3  — Assembler robustness (quoted / unquoted / bare-token / fallback /
           think-blocks / markdown / mis-indented return)
Suite 4  — Radical DNA profiler (_build_radical_profile, _is_radical_isomorphic)
Suite 5  — validate_structure_alignment dispatcher (radical vs integer paths)
Suite 6  — AST healer: 'core' in safe_modules; DomainFunctionHelper fallback
Suite 7  — Regression: Integer / Fraction skills are unaffected

Run
---
    python tests/radical_auto_test.py
    python tests/radical_auto_test.py -v          # verbose
    python tests/radical_auto_test.py --failfast   # stop on first failure

Exit code 0 = all pass, 1 = at least one failure.
=============================================================================
"""

import ast
import importlib.util
import os
import sys
import tempfile
import textwrap
import unittest

# ── Project root on path ─────────────────────────────────────────────────────
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ── Lazy module-level singletons (avoid class-attribute binding issue) ────────
def _get_assemble():
    import core.routes.live_show as ls
    return ls._assemble_radical_orchestrator_code

def _get_radical_utils():
    from core.code_utils.live_show_math_utils import (
        _build_radical_profile,
        _has_square_factor,
        _is_radical_isomorphic,
        _radical_profile_diff,
    )
    return _build_radical_profile, _has_square_factor, _is_radical_isomorphic, _radical_profile_diff

def _get_validate():
    from core.ai_analyzer import validate_structure_alignment
    return validate_structure_alignment

# ── Constants ─────────────────────────────────────────────────────────────────
_RADICAL_SKILL_ID = "jh_數學2上_FourOperationsOfRadicals"
_ALL_PATTERNS = [
    "p0_simplify",
    "p1_add_sub",
    "p2a_mult_direct",
    "p2b_mult_distrib",
    "p2f_int_mult_rad",
    "p2g_rad_mult_frac",
    "p2h_frac_mult_rad",
    "p2c_mult_binomial",
    "p3a_div_expr",
    "p3b_div_simple",
    "p4_frac_mult",
    "p5a_conjugate_int",
    "p5b_conjugate_rad",
    "p6_combo",
]
_ALL_DIFFS = ["easy", "mid", "hard"]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _exec_module(code: str):
    """Write *code* to a temp file, load it as a module, and return it."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(code)
        path = f.name
    try:
        spec = importlib.util.spec_from_file_location("_rad_test_mod", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def _load_scaffold_constants():
    from core.prompt_architect import (
        RADICAL_V4_SCAFFOLD_PREFIX as PRE,
        RADICAL_V4_SCAFFOLD_SUFFIX as SUF,
    )
    return PRE, SUF


def _build_code(pid: str, diff: str) -> str:
    PRE, SUF = _load_scaffold_constants()
    decisions = (
        f'    pattern_id = "{pid}"\n'
        f'    difficulty  = "{diff}"\n'
        '    term_count = 2\n'  # Required by scaffold; p2f etc. ignore it
    )
    return PRE + decisions + SUF


def _validate_result(result: dict, label: str):
    assert isinstance(result, dict), f"{label}: generate() must return dict, got {type(result)}"
    assert "question_text" in result, f"{label}: missing 'question_text'"
    assert "correct_answer" in result, f"{label}: missing 'correct_answer'"
    assert result["question_text"], f"{label}: empty question_text"


# ─────────────────────────────────────────────────────────────────────────────
# Suite 1 — DomainFunctionHelper direct API
# ─────────────────────────────────────────────────────────────────────────────

class Suite1_DomainFunctionHelper(unittest.TestCase):
    """Every pattern must generate vars, solve, and format a question string."""

    @classmethod
    def setUpClass(cls):
        from core.domain_functions import DomainFunctionHelper
        cls.df = DomainFunctionHelper()

    def _run_pattern(self, pid: str, diff: str):
        df = self.df
        label = f"{pid}/{diff}"
        v = df.get_safe_vars_for_pattern(pid, diff)
        self.assertIsInstance(v, dict, f"{label}: vars must be dict")
        ans, sol = df.solve_problem_pattern(pid, v, diff)
        self.assertTrue(ans, f"{label}: answer must be non-empty")
        self.assertIsInstance(sol, list, f"{label}: solution must be list")
        qt = df.format_question_LaTeX(pid, v)
        self.assertTrue(qt, f"{label}: question_text must be non-empty")
        # p6_combo returns a descriptive sentence; all others carry LaTeX $…$
        if pid != "p6_combo":
            self.assertIn("$", qt, f"{label}: question_text must contain LaTeX $…$")
        return qt, ans

    def test_p0_simplify(self):
        self._run_pattern("p0_simplify", "easy")

    def test_p1_add_sub_easy(self):
        self._run_pattern("p1_add_sub", "easy")

    def test_p1_add_sub_mid(self):
        self._run_pattern("p1_add_sub", "mid")

    def test_p1_add_sub_hard(self):
        self._run_pattern("p1_add_sub", "hard")

    def test_p2a_mult_direct(self):
        self._run_pattern("p2a_mult_direct", "easy")

    def test_p2b_mult_distrib(self):
        self._run_pattern("p2b_mult_distrib", "mid")

    def test_p2f_int_mult_rad(self):
        self._run_pattern("p2f_int_mult_rad", "easy")

    def test_p2g_rad_mult_frac(self):
        self._run_pattern("p2g_rad_mult_frac", "easy")

    def test_p2h_frac_mult_rad(self):
        self._run_pattern("p2h_frac_mult_rad", "easy")

    def test_p2c_mult_binomial(self):
        self._run_pattern("p2c_mult_binomial", "hard")

    def test_p3a_div_expr(self):
        self._run_pattern("p3a_div_expr", "mid")

    def test_p3b_div_simple(self):
        self._run_pattern("p3b_div_simple", "easy")

    def test_p4_frac_mult(self):
        self._run_pattern("p4_frac_mult", "mid")

    def test_p5a_conjugate_int(self):
        self._run_pattern("p5a_conjugate_int", "mid")

    def test_p5b_conjugate_rad(self):
        self._run_pattern("p5b_conjugate_rad", "hard")

    def test_p6_combo(self):
        self._run_pattern("p6_combo", "hard")

    def test_count_simplifiable_in_vars(self):
        df = self.df
        # p0_simplify always uses SIMPLIFIABLE_SET
        v0 = df.get_safe_vars_for_pattern("p0_simplify", "easy")
        self.assertEqual(df.count_simplifiable_in_vars("p0_simplify", v0), 1)
        # p3b_div_simple always uses PRIME_SET → 0
        v3b = df.get_safe_vars_for_pattern("p3b_div_simple", "easy")
        self.assertEqual(df.count_simplifiable_in_vars("p3b_div_simple", v3b), 0)

    def test_get_radical_profile(self):
        df = self.df
        prof = df.get_radical_profile(r"化簡 $2\sqrt{12} - \sqrt{27}$。")
        self.assertEqual(prof["rad_count"], 2)
        self.assertEqual(prof["simplifiable_count"], 2)


# ─────────────────────────────────────────────────────────────────────────────
# Suite 2 — Full scaffold: syntax + runtime execution
# ─────────────────────────────────────────────────────────────────────────────

class Suite2_ScaffoldExecution(unittest.TestCase):
    """Each assembled scaffold must compile and generate a valid result dict."""

    def _test_pattern_diff(self, pid: str, diff: str):
        label = f"{pid}/{diff}"
        code = _build_code(pid, diff)

        # 2-a. Syntax check
        try:
            ast.parse(code)
        except SyntaxError as e:
            self.fail(f"{label}: SyntaxError in assembled code: {e}\n\n{code}")

        # 2-b. Runtime execution via module loading (same as scaler)
        try:
            mod = _exec_module(code)
        except Exception as e:
            self.fail(f"{label}: Module load error: {e}")

        gen = getattr(mod, "generate", None)
        self.assertIsNotNone(gen, f"{label}: generate() not found in module")

        try:
            result = gen(level=1)
        except Exception as e:
            self.fail(f"{label}: generate() raised: {e}")

        _validate_result(result, label)

        # 2-c. check() function present and functional
        chk = getattr(mod, "check", None)
        self.assertIsNotNone(chk, f"{label}: check() not found in module")
        resp = chk(result["correct_answer"], result["correct_answer"])
        self.assertTrue(resp["correct"], f"{label}: check() should return True for identical answers")


def _make_test(pid, diff):
    def _test(self):
        self._test_pattern_diff(pid, diff)
    _test.__name__ = f"test_{pid}_{diff}"
    return _test


# Dynamically generate one test method per (pattern, difficulty) pair
for _pid in _ALL_PATTERNS:
    for _diff in _ALL_DIFFS:
        _name = f"test_{_pid}_{_diff}"
        setattr(Suite2_ScaffoldExecution, _name, _make_test(_pid, _diff))


# ─────────────────────────────────────────────────────────────────────────────
# Suite 3 — Assembler robustness
# ─────────────────────────────────────────────────────────────────────────────

class Suite3_AssemblerRobustness(unittest.TestCase):
    """_assemble_radical_orchestrator_code must survive all model output variants."""

    def _assembled_exec(self, raw: str) -> dict:
        assemble = _get_assemble()
        code = assemble(raw)
        # Syntax check
        try:
            ast.parse(code)
        except SyntaxError as e:
            self.fail(f"SyntaxError after assembly: {e}\n\nAssembled:\n{code}")
        mod = _exec_module(code)
        return mod.generate(level=1)

    def test_quoted_assignment(self):
        result = self._assembled_exec('pattern_id = "p3b_div_simple"\ndifficulty = "easy"')
        _validate_result(result, "quoted")
        self.assertIn(r"\dfrac", result["question_text"])  # p3b always has \dfrac

    def test_single_quoted_assignment(self):
        result = self._assembled_exec("pattern_id = 'p0_simplify'\ndifficulty = 'easy'")
        _validate_result(result, "single-quoted")

    def test_unquoted_assignment(self):
        result = self._assembled_exec("pattern_id = p2a_mult_direct\ndifficulty = easy")
        _validate_result(result, "unquoted")

    def test_bare_token_in_prose(self):
        result = self._assembled_exec(
            "I think the appropriate pattern is p5a_conjugate_int at mid difficulty."
        )
        _validate_result(result, "bare-token")

    def test_markdown_fenced_output(self):
        raw = "```python\npattern_id = \"p1_add_sub\"\ndifficulty = \"mid\"\n```"
        result = self._assembled_exec(raw)
        _validate_result(result, "markdown-fenced")

    def test_think_block_stripped(self):
        raw = "<think>internal\nreasoning</think>\npattern_id = \"p0_simplify\"\ndifficulty = \"easy\""
        result = self._assembled_exec(raw)
        _validate_result(result, "think-stripped")

    def test_return_outside_function_in_raw(self):
        """Model accidentally outputs return {...} at module level — must not crash."""
        raw = (
            'pattern_id = "p1_add_sub"\n'
            'difficulty = "mid"\n'
            "return {\n"
            "    'question_text': 'bad',\n"
            "    'correct_answer': '0'\n"
            "}\n"
        )
        assemble = _get_assemble()
        code = assemble(raw)
        try:
            ast.parse(code)
        except SyntaxError as e:
            self.fail(f"SyntaxError: model's bare return leaked into scaffold: {e}")
        result = _exec_module(code).generate(level=1)
        _validate_result(result, "return-outside-fn")

    def test_hard_fallback_on_garbage(self):
        result = self._assembled_exec("totally unrelated text with no pattern or difficulty")
        _validate_result(result, "hard-fallback")
        # fallback must use p1_add_sub which always generates add/sub expression
        self.assertIn(r"\sqrt", result["question_text"])

    def test_indentation_of_decisions(self):
        """Decisions must sit inside def generate() — 4-space indent."""
        assemble = _get_assemble()
        code = assemble('pattern_id = "p4_frac_mult"\ndifficulty = "mid"')
        # Both assignment lines must be inside def generate, not at module level
        tree = ast.parse(code)
        gen_node = next(
            (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "generate"),
            None,
        )
        self.assertIsNotNone(gen_node, "def generate not found in assembled code")
        # The assignments must be direct children of the function body
        assign_targets = [
            n.targets[0].id
            for n in ast.walk(gen_node)
            if isinstance(n, ast.Assign)
            and isinstance(n.targets[0], ast.Name)
            and n.targets[0].id in ("pattern_id", "difficulty")
        ]
        self.assertIn("pattern_id", assign_targets, "pattern_id not inside def generate")
        self.assertIn("difficulty", assign_targets, "difficulty not inside def generate")

    def test_no_return_at_module_level(self):
        """Module body must never contain a bare Return node."""
        assemble = _get_assemble()
        code = assemble('pattern_id = "p2b_mult_distrib"\ndifficulty = "hard"')
        tree = ast.parse(code)
        module_returns = [
            n for n in tree.body if isinstance(n, ast.Return)
        ]
        self.assertEqual(module_returns, [], "bare Return at module level detected")


# ─────────────────────────────────────────────────────────────────────────────
# Suite 4 — Radical DNA profiler
# ─────────────────────────────────────────────────────────────────────────────

class Suite4_RadicalDNAProfiler(unittest.TestCase):

    def test_has_square_factor(self):
        _, _has_sq, _, _ = _get_radical_utils()
        for n in (4, 8, 9, 12, 18, 20, 24, 25, 27, 45, 50, 72, 75):
            self.assertTrue(_has_sq(n), f"{n} should be simplifiable")
        for n in (1, 2, 3, 5, 6, 7, 10, 11, 13):
            self.assertFalse(_has_sq(n), f"{n} should be in simplest form")

    def test_distinguishes_simplifiable(self):
        # THE key scenario: both expressions have 2 radicals, only one is simplifiable
        _build_rp, _, _, _ = _get_radical_utils()
        p_simple  = _build_rp(r"2\sqrt{3} + \sqrt{5}")
        p_complex = _build_rp(r"2\sqrt{3} + \sqrt{12}")
        self.assertEqual(p_simple["rad_count"], 2)
        self.assertEqual(p_complex["rad_count"], 2)
        self.assertEqual(p_simple["simplifiable_count"], 0,
                         "√3 and √5 are both prime — simplifiable_count must be 0")
        self.assertEqual(p_complex["simplifiable_count"], 1,
                         "√12 has factor 4 — simplifiable_count must be 1")

    def test_rationalize_count(self):
        _build_rp, _, _, _ = _get_radical_utils()
        p = _build_rp(r"\dfrac{5}{\sqrt{3}}")
        self.assertEqual(p["rad_count"], 1)
        self.assertEqual(p["simplifiable_count"], 0)
        self.assertEqual(p["rationalize_count"], 1)

    def test_empty_expression(self):
        _build_rp, _, _, _ = _get_radical_utils()
        p = _build_rp("")
        self.assertEqual(p["rad_count"], 0)

    def test_iso_strict_check(self):
        _, _, _iso, _ = _get_radical_utils()
        target = {"rad_count": 2, "simplifiable_count": 1}
        self.assertTrue(_iso(target, r"2\sqrt{3} + \sqrt{12}"))
        self.assertFalse(_iso(target, r"\sqrt{3} + \sqrt{5}"))

    def test_empty_fp_always_iso(self):
        from core.code_utils.live_show_math_utils import _is_expression_isomorphic
        # empty expected_fp = bypass mode
        self.assertTrue(_is_expression_isomorphic({}, r"2\sqrt{12} - \sqrt{27}"))
        self.assertFalse(_is_expression_isomorphic({}, ""))

    def test_diff_fn_reports_mismatch(self):
        _, _, _, _diff_fn = _get_radical_utils()
        target = {"rad_count": 3, "simplifiable_count": 2}
        diffs = _diff_fn(target, r"\sqrt{3} + \sqrt{5}")
        self.assertTrue(any("rad_count" in d for d in diffs))


# ─────────────────────────────────────────────────────────────────────────────
# Suite 5 — validate_structure_alignment dispatcher
# ─────────────────────────────────────────────────────────────────────────────

class Suite5_ValidateStructureAlignment(unittest.TestCase):

    def test_radical_path_selected(self):
        validate = _get_validate()
        r = validate(
            _RADICAL_SKILL_ID,
            r"2\sqrt{3} + \sqrt{12}",
            r"3\sqrt{5} + \sqrt{20}",  # rad=2, simpl=1 — same profile
        )
        self.assertEqual(r["profile_type"], "radical")
        self.assertTrue(r["aligned"], f"Expected aligned=True: {r}")

    def test_radical_mismatch_detected(self):
        validate = _get_validate()
        r = validate(
            _RADICAL_SKILL_ID,
            r"2\sqrt{3} + \sqrt{12}",   # simpl=1
            r"\sqrt{3} + \sqrt{5}",     # simpl=0
        )
        self.assertEqual(r["profile_type"], "radical")
        self.assertFalse(r["aligned"], f"Profiles differ, expected aligned=False: {r}")
        self.assertTrue(len(r["diffs"]) > 0)

    def test_integer_path_selected(self):
        validate = _get_validate()
        r = validate("jh_數學1上_IntegerArithmetic", "3 + 5", "3 + 5")
        self.assertEqual(r["profile_type"], "integer")

    def test_aliases_trigger_radical_path(self):
        validate = _get_validate()
        r = validate("SomeSkill_Radicals_Extra", r"\sqrt{2}", r"\sqrt{2}")
        self.assertEqual(r["profile_type"], "radical")

    def test_never_raises(self):
        validate = _get_validate()
        # Garbage input — must return a valid dict, never raise
        r = validate(None, None, None)
        self.assertIn("aligned", r)


# ─────────────────────────────────────────────────────────────────────────────
# Suite 6 — AST Healer safeguards
# ─────────────────────────────────────────────────────────────────────────────

class Suite6_ASTHealer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from core.healers.ast_healer import ASTHealer
        cls.ASTHealer = ASTHealer

    def test_core_import_preserved(self):
        """visit_ImportFrom must NOT strip from core.domain_functions import …"""
        code = textwrap.dedent("""\
            from core.domain_functions import DomainFunctionHelper
            df = DomainFunctionHelper()

            def generate(level=1, **kwargs):
                pattern_id = "p1_add_sub"
                difficulty  = "mid"
                v = df.get_safe_vars_for_pattern(pattern_id, difficulty)
                a, s = df.solve_problem_pattern(pattern_id, v, difficulty)
                q = df.format_question_LaTeX(pattern_id, v)
                return {'question_text': q, 'answer': '', 'correct_answer': a,
                        'solution_steps': s, 'mode': 1, '_o1_healed': False}

            def check(u, c):
                return {'correct': str(u).strip() == str(c).strip(), 'result': 'ok'}
        """)
        healer = self.ASTHealer()
        healed, _ = healer.heal(code)
        self.assertIn("DomainFunctionHelper", healed,
                      "visit_ImportFrom stripped core.domain_functions — must not!")

    def test_fallback_generate_uses_domain_function_helper(self):
        """When generate() is missing, injected fallback must reference DomainFunctionHelper."""
        code = textwrap.dedent("""\
            x = 1

            def check(u, c):
                return {'correct': True, 'result': 'ok'}
        """)
        healer = self.ASTHealer()
        healed, fixes = healer.heal(code)
        self.assertGreater(fixes, 0, "Expected healer to inject missing generate()")
        self.assertIn("generate", healed)
        self.assertIn("DomainFunctionHelper", healed,
                      "Injected generate() must include DomainFunctionHelper try-block")

    def test_format_polynomial_not_removed(self):
        """Polynomial helpers must remain in the forbidden list (no regression)."""
        code = textwrap.dedent("""\
            def format_polynomial(terms):
                return '+'.join(str(t) for t in terms)

            def generate(level=1, **kwargs):
                return {'question_text': 'test', 'correct_answer': '1'}

            def check(u, c):
                return {'correct': True, 'result': 'ok'}
        """)
        healer = self.ASTHealer()
        healed, _ = healer.heal(code)
        # format_polynomial is in forbidden_helper_funcs → should be removed
        self.assertNotIn("def format_polynomial", healed)

    def test_healed_code_syntax_valid(self):
        """Healer output for radical scaffold must always be valid Python."""
        PRE, SUF = _load_scaffold_constants()
        code = PRE + '    pattern_id = "p1_add_sub"\n    difficulty = "mid"\n' + SUF
        healer = self.ASTHealer()
        healed, _ = healer.heal(code)
        try:
            ast.parse(healed)
        except SyntaxError as e:
            self.fail(f"Healer produced invalid Python: {e}\n\n{healed}")


# ─────────────────────────────────────────────────────────────────────────────
# Suite 7 — Regression: Integer / Fraction skills unaffected
# ─────────────────────────────────────────────────────────────────────────────

class Suite7_Regression(unittest.TestCase):

    def test_is_expression_isomorphic_non_radical(self):
        """Non-empty expected_fp still enforces structural matching for integers."""
        from core.code_utils.live_show_math_utils import (
            _build_structural_profile, _is_expression_isomorphic,
        )
        fp = _build_structural_profile("3 + 5")
        self.assertTrue(_is_expression_isomorphic(fp, "3 + 5"))
        self.assertFalse(_is_expression_isomorphic(fp, "3 * 5"),
                         "operator_sequence mismatch must return False for integers")

    def test_validate_structure_alignment_integer_path(self):
        from core.ai_analyzer import validate_structure_alignment
        r = validate_structure_alignment(
            "jh_數學1上_FourArithmeticOperationsOfIntegers", "3 + 5", "3 + 5"
        )
        self.assertEqual(r["profile_type"], "integer")
        self.assertTrue(r["aligned"])

    def test_scaffold_constants_clean_of_integer_constraints(self):
        """V4 spec constants must contain no isomorphic / bracket keywords."""
        import core.prompt_architect as pa
        v4_src = " ".join([
            getattr(pa, f"_V4_{name}", "")
            for name in ("HEADER", "ARCH_NOTE", "DIFFICULTY_GUIDE",
                         "PROHIBITIONS", "PATTERN_TABLE", "API_SIGNATURES")
        ])
        forbidden = [
            "isomorphic", "bracket_count", "abs_count",
            "operator_sequence", "number_count",
        ]
        for kw in forbidden:
            self.assertNotIn(
                kw, v4_src,
                f"Integer constraint keyword {kw!r} found in V4 radical spec constants",
            )

    def test_assembler_does_not_affect_integer_skill_code(self):
        """_assemble_radical_orchestrator_code is ONLY called for the radical skill.
        Integer skill code should never pass through it — verify it's gated."""
        from core.routes import live_show as ls
        src = open(ls.__file__, encoding="utf-8").read()
        # The assembler call must be gated on _RADICAL_SKILL_ID
        import re
        gate = re.search(
            r'if\s+skill_id\s*==\s*_RADICAL_SKILL_ID[^\n]*\n[^\n]*_assemble_radical_orchestrator_code',
            src,
        )
        self.assertIsNotNone(
            gate,
            "_assemble_radical_orchestrator_code call must be gated on skill_id == _RADICAL_SKILL_ID",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("Radical Skill Autonomous Test Suite")
    print("=" * 70)
    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = None   # preserve declaration order
    suite = unittest.TestSuite()
    for cls in [
        Suite1_DomainFunctionHelper,
        Suite2_ScaffoldExecution,
        Suite3_AssemblerRobustness,
        Suite4_RadicalDNAProfiler,
        Suite5_ValidateStructureAlignment,
        Suite6_ASTHealer,
        Suite7_Regression,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2, failfast="--failfast" in sys.argv)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
