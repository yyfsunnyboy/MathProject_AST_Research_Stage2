# -*- coding: utf-8 -*-
"""
=============================================================================
Module: core/domain_functions.py
Description:
    DomainFunctionHelper — High-level orchestration interface for the
    "Edge AI Orchestrator" architecture.

    This module is the ONLY surface the Qwen3-generated code is allowed to
    import from. It wraps the RadicalSolver engine and provides:

      1. get_golden_pattern_for_liveshow() — OCR-semantic → pattern_id mapping
      2. get_safe_vars_for_pattern()       — controlled random variable generation
      3. solve_problem_pattern()           — delegates to RadicalSolver
      4. format_question_LaTeX()           — question-text LaTeX formatting

    Design constraints:
      - All variable generation is seeded through integer-only arithmetic.
      - No floating-point values are ever inserted into variable dicts.
      - The generated code (from Qwen3) only calls these high-level methods;
        it never touches RadicalSolver directly.

Version: 1.0.0
Skill scope: jh_數學2上_FourOperationsOfRadicals
=============================================================================
"""

import math
import random
from fractions import Fraction
from typing import Dict, List, Optional, Tuple

from core.math_solvers.radical_solver import (
    RadicalSolver,
    _simplify_rad,
    _format_term_unsimplified,
    _format_expression,
    _merge_terms,
    StepList,
    TermsDict,
)

# ---------------------------------------------------------------------------
# Constant sets (match SKILL.md definitions)
# ---------------------------------------------------------------------------
PRIME_SET = [2, 3, 5, 7, 11]
SIMPLIFIABLE_SET = [8, 12, 18, 20, 24, 27, 32, 45, 48, 50, 72, 75]
NON_ZERO_COEFF = [-5, -4, -3, -2, -1, 1, 2, 3, 4, 5]
SMALL_DENOM = [2, 3, 4, 5, 6]

# OCR keyword → pattern_id mapping table (for get_golden_pattern_for_liveshow)
_OCR_KEYWORD_PATTERN_MAP = {
    # Conjugate rationalization keywords
    "共軛": "p5a_conjugate_int",
    "有理化分母": "p5a_conjugate_int",
    r"\frac{1}{\sqrt": "p5a_conjugate_int",
    r"\frac{\sqrt": "p5b_conjugate_rad",
    # Division keywords
    r"\div\sqrt": "p3a_div_expr",
    r"/\sqrt": "p3b_div_simple",
    # Multiplication with bracket
    r"\times(": "p2b_mult_distrib",
    r")(\sqrt": "p2c_mult_binomial",
    # Direct multiplication
    r"\times\sqrt": "p2a_mult_direct",
    r"\sqrt{}\times": "p2a_mult_direct",
    # Addition / subtraction (fallback after all others checked)
    "+": "p1_add_sub",
    "-": "p1_add_sub",
    # Single radical
    r"\sqrt{": "p0_simplify",
}


class DomainFunctionHelper:
    """
    High-level helper interface for the Edge AI Orchestrator.

    The Qwen3 model instantiates this class and calls its methods.
    All mathematical computation is handled internally by RadicalSolver;
    the model only provides pattern_id, difficulty, and optional OCR hints.

    Usage in Qwen3-generated code:
        from core.domain_functions import DomainFunctionHelper
        df = DomainFunctionHelper()

        pattern_id = "p1_add_sub"
        difficulty  = "mid"

        vars        = df.get_safe_vars_for_pattern(pattern_id, difficulty)
        ans, sol    = df.solve_problem_pattern(pattern_id, vars, difficulty)
        question    = df.format_question_LaTeX(pattern_id, vars)
    """

    def __init__(self):
        self._solver = RadicalSolver()

    # -----------------------------------------------------------------------
    # 1. OCR semantic → pattern_id (mocked)
    # -----------------------------------------------------------------------

    def get_golden_pattern_for_liveshow(
        self,
        skill_name: str,
        difficulty: str,
        uploaded_ocr_semantics: str,
    ) -> str:
        """
        [MOCKED] Given a skill name, difficulty level, and OCR-extracted text
        from the uploaded textbook image, return the most suitable pattern_id.

        In production this would call a lightweight classifier; currently uses
        a deterministic keyword-priority heuristic so the pipeline never fails.

        Args:
            skill_name: e.g. "jh_數學2上_FourOperationsOfRadicals"
            difficulty: "easy" | "mid" | "hard"
            uploaded_ocr_semantics: raw OCR text or structured LaTeX snippet

        Returns:
            A pattern_id string from SKILL.md Pattern Catalogue.
        """
        ocr = str(uploaded_ocr_semantics)

        # Priority-ordered keyword scan
        priority = [
            ("p5b_conjugate_rad", [r"\frac{\sqrt", r"√p/(", "共軛根式"]),
            ("p5a_conjugate_int", [r"\frac{1}{\sqrt", r"1/(", "共軛", "有理化分母"]),
            ("p2c_mult_binomial", [r")(\sqrt", r")×(", "雙括號"]),
            ("p2b_mult_distrib",  [r"\times(", r"×(", "分配律"]),
            ("p2a_mult_direct",   [r"\times\sqrt", r"×\sqrt", "直接相乘"]),
            ("p4_frac_mult",      [r"\frac{", r"分數×", "純分數"]),
            ("p3a_div_expr",      [r"\div\sqrt", r"÷\sqrt", "除以根式"]),
            ("p3b_div_simple",    [r"/\sqrt", r"有理化", "rationalize"]),
            ("p6_combo",          ["複合", "多步驟", "combined"]),
            ("p1_add_sub",        ["+", "-", "加減", "合併"]),
            ("p0_simplify",       [r"\sqrt{", "化簡", "simplify"]),
        ]

        for pid, keywords in priority:
            if any(kw in ocr for kw in keywords):
                return pid

        # Default by difficulty
        defaults = {"easy": "p0_simplify", "mid": "p1_add_sub", "hard": "p6_combo"}
        return defaults.get(difficulty, "p1_add_sub")

    # -----------------------------------------------------------------------
    # 2. Safe variable generation
    # -----------------------------------------------------------------------

    def get_safe_vars_for_pattern(
        self,
        pattern_id: str,
        difficulty: str,
        max_retries: int = 200,
        target_profile: Optional[dict] = None,
        term_count: int = None,
    ) -> dict:
        """
        Generate a dictionary of safe, controlled random variables for the
        given pattern and difficulty.

        All values are pure integers (no floats). The method retries up to
        max_retries times until all mathematical constraints are satisfied.

        Args:
            pattern_id:     one of the IDs from SKILL.md Pattern Catalogue
            difficulty:     "easy" | "mid" | "hard"
            max_retries:    max generation attempts before raising RuntimeError
            target_profile: optional Radical DNA dict from _build_radical_profile.
                            When provided, the generator tries to produce vars whose
                            simplifiable_count matches target_profile["simplifiable_count"].
                            If the constraint cannot be satisfied within max_retries the
                            best-effort vars (mathematically correct) are returned.

        Returns:
            A dict of variables consumed by solve_problem_pattern and
            format_question_LaTeX for the given pattern_id.

        Raises:
            RuntimeError if valid vars cannot be generated within max_retries
            AND no best-effort result is available.
        """
        pid = pattern_id.lower().strip()
        generator_map = {
            "p0_simplify":         self._vars_p0,
            "p1_add_sub":          self._vars_p1,
            "p2a_mult_direct":     self._vars_p2a,
            "p2b_mult_distrib":    self._vars_p2b,
            "p2c_mult_binomial":   self._vars_p2c,
            "p3a_div_expr":        self._vars_p3a,
            "p3b_div_simple":      self._vars_p3b,
            "p4_frac_mult":        self._vars_p4,
            "p5a_conjugate_int":   self._vars_p5a,
            "p5b_conjugate_rad":   self._vars_p5b,
            "p6_combo":            self._vars_p6,
        }
        if pid not in generator_map:
            raise ValueError(
                f"Unknown pattern_id '{pattern_id}'. "
                f"Valid IDs: {list(generator_map.keys())}"
            )

        target_sc = (
            target_profile.get("simplifiable_count")
            if isinstance(target_profile, dict)
            else None
        )

        best_effort_vars: Optional[dict] = None

        for attempt in range(max_retries):
            try:
                if pid == "p1_add_sub":
                    v = self._vars_p1(difficulty, term_count=term_count)
                else:
                    v = generator_map[pid](difficulty)
                best_effort_vars = v  # always keep latest mathematically-valid vars

                if target_sc is not None:
                    actual_sc = self.count_simplifiable_in_vars(pid, v)
                    # -1 means the pattern's radicand layout is not yet catalogued;
                    # skip the profile check rather than spinning endlessly.
                    if actual_sc != -1 and actual_sc != target_sc:
                        raise _RetrySignal()

                return v
            except _RetrySignal:
                continue
            except Exception as exc:
                if attempt >= max_retries - 1:
                    break
                continue

        # Profile constraint could not be met — return best-effort (math is correct).
        if best_effort_vars is not None:
            return best_effort_vars

        raise RuntimeError(
            f"get_safe_vars_for_pattern: could not generate valid vars for "
            f"'{pattern_id}' (difficulty='{difficulty}') within {max_retries} tries."
        )

    # -----------------------------------------------------------------------
    # 3. Solve (delegates to RadicalSolver)
    # -----------------------------------------------------------------------

    def solve_problem_pattern(
        self,
        pattern_id: str,
        variables: dict,
        difficulty: str = "mid",
    ) -> Tuple[str, StepList]:
        """
        Compute the answer and solution steps for a given pattern + variables.

        Delegates entirely to RadicalSolver.solve_problem_pattern.

        Returns:
            (latex_answer: str, solution_steps: List[str])
        """
        return self._solver.solve_problem_pattern(pattern_id, variables, difficulty)

    # -----------------------------------------------------------------------
    # 4. Question LaTeX formatting
    # -----------------------------------------------------------------------

    def format_question_LaTeX(self, pattern_id: str, variables: dict) -> str:
        """
        Format the question text as a LaTeX-wrapped string for MathJax rendering.

        The generated code calls this INSTEAD of building LaTeX manually.
        Returns a string like: "化簡 $2\\sqrt{12} - \\sqrt{27}$。"

        Args:
            pattern_id: the pattern identifier
            variables:  the same dict returned by get_safe_vars_for_pattern

        Returns:
            A complete question_text string with $...$ LaTeX wrapping.
        """
        pid = pattern_id.lower().strip()
        formatter_map = {
            "p0_simplify":         self._fmt_p0,
            "p1_add_sub":          self._fmt_p1,
            "p2a_mult_direct":     self._fmt_p2a,
            "p2b_mult_distrib":    self._fmt_p2b,
            "p2c_mult_binomial":   self._fmt_p2c,
            "p3a_div_expr":        self._fmt_p3a,
            "p3b_div_simple":      self._fmt_p3b,
            "p4_frac_mult":        self._fmt_p4,
            "p5a_conjugate_int":   self._fmt_p5a,
            "p5b_conjugate_rad":   self._fmt_p5b,
            "p6_combo":            self._fmt_p6,
        }
        if pid not in formatter_map:
            raise ValueError(f"Unknown pattern_id '{pattern_id}'.")
        return formatter_map[pid](variables)

    # -----------------------------------------------------------------------
    # 5. Radical DNA helpers
    # -----------------------------------------------------------------------

    def count_simplifiable_in_vars(self, pattern_id: str, variables: dict) -> int:
        """Return the number of simplifiable radicands that will appear in the
        question text for *pattern_id* given *variables*.

        A radicand N is *simplifiable* when √N can be reduced (e.g. √12 → 2√3).
        This count forms the ``simplifiable_count`` field of the Radical DNA
        profile and is used to validate that the generated question matches the
        structural complexity of the OCR input.

        Returns -1 for patterns whose radicand layout is not yet catalogued so
        callers can skip the check instead of looping endlessly.
        """
        from core.code_utils.live_show_math_utils import _has_square_factor

        pid = pattern_id.lower().strip()

        def _sc(radicands: list) -> int:
            return sum(
                1 for r in radicands
                if isinstance(r, int) and _has_square_factor(r)
            )

        if pid == "p0_simplify":
            return _sc([variables.get("r", 1)])

        if pid == "p1_add_sub":
            return _sc([t[1] for t in variables.get("terms", [])])

        if pid == "p2a_mult_direct":
            return _sc([variables.get("r1", 1), variables.get("r2", 1)])

        if pid == "p2b_mult_distrib":
            # question: c1√r1 × (c2√r2 ± c3√r3) — r2 comes from SIMPLIFIABLE_SET
            return _sc([variables.get("r1", 1),
                        variables.get("r2", 1),
                        variables.get("r3", 1)])

        if pid == "p2c_mult_binomial":
            # question: (c1√r1 ± c2√r2)(c3√r3 ± c4) — all r from PRIME_SET
            return _sc([variables.get("r1", 1),
                        variables.get("r2", 1),
                        variables.get("r3", 1)])

        if pid == "p3a_div_expr":
            # question: (c1√r1 ± c2√r2) ÷ √denom_r
            return _sc([variables.get("r1", 1),
                        variables.get("r2", 1),
                        variables.get("denom_r", 1)])

        if pid == "p3b_div_simple":
            # question: a/√b — b from PRIME_SET → always 0
            return _sc([variables.get("b", 1)])

        if pid == "p4_frac_mult":
            return _sc([variables.get("r", 1)])

        if pid in ("p5a_conjugate_int", "p5b_conjugate_rad"):
            # both use PRIME_SET radicands → always 0
            return 0

        if pid == "p6_combo":
            sp1 = variables.get("sub_pattern1", "")
            sp2 = variables.get("sub_pattern2", "")
            c1 = self.count_simplifiable_in_vars(sp1, variables.get("vars1", {})) if sp1 else 0
            c2 = self.count_simplifiable_in_vars(sp2, variables.get("vars2", {})) if sp2 else 0
            return (c1 if c1 != -1 else 0) + (c2 if c2 != -1 else 0)

        return -1  # unknown — caller should skip the profile check

    def get_radical_profile(self, question_text: str) -> dict:
        """Return the Radical DNA profile of a *question_text* string.

        Delegates to ``_build_radical_profile`` in live_show_math_utils.
        Use this to inspect what the DomainFunctionHelper actually generated
        and compare it against the OCR target profile.

        Returns:
            dict with keys: rad_count, simplifiable_count,
                            rationalize_count, radicands
        """
        from core.code_utils.live_show_math_utils import _build_radical_profile
        return _build_radical_profile(question_text)

    # =======================================================================
    # Variable generators (private)
    # =======================================================================

    def _vars_p0(self, difficulty: str) -> dict:
        r = random.choice(SIMPLIFIABLE_SET)
        _, simplified_r = _simplify_rad(1, r)
        if simplified_r == r:
            raise _RetrySignal()
        return {"r": r}

    def _vars_p1(self, difficulty: str, term_count: int = None) -> dict:
        if term_count is not None and term_count >= 2:
            n_terms = term_count
        else:
            n_terms = {"easy": 2, "mid": 3, "hard": 4}.get(difficulty, 2)
        terms = []
        for i in range(n_terms):
            c = random.choice(NON_ZERO_COEFF)
            r = random.choice(SIMPLIFIABLE_SET)
            op = "+" if i == 0 else random.choice(["+", "-"])
            terms.append((c, r, op))

        # Validate: at least two terms should simplify to same radicand
        simplified_radicands = [_simplify_rad(1, t[1])[1] for t in terms]
        if len(set(simplified_radicands)) == len(simplified_radicands):
            raise _RetrySignal()  # all distinct — no combination possible

        return {"terms": terms}

    def _vars_p2a(self, difficulty: str) -> dict:
        pool = SIMPLIFIABLE_SET if difficulty != "easy" else SIMPLIFIABLE_SET[:6]
        c1 = random.choice(NON_ZERO_COEFF)
        c2 = random.choice(NON_ZERO_COEFF)
        r1 = random.choice(pool)
        r2 = random.choice(pool)
        return {"c1": c1, "r1": r1, "c2": c2, "r2": r2}

    def _vars_p2b(self, difficulty: str) -> dict:
        c1 = random.choice([c for c in NON_ZERO_COEFF if abs(c) <= 3])
        r1 = random.choice(PRIME_SET)
        c2 = random.choice([c for c in NON_ZERO_COEFF if abs(c) <= 3])
        r2 = random.choice(SIMPLIFIABLE_SET)
        c3 = random.choice([c for c in NON_ZERO_COEFF if abs(c) <= 3])
        r3 = random.choice(PRIME_SET)
        op = random.choice(["+", "-"])
        return {"c1": c1, "r1": r1, "c2": c2, "r2": r2, "c3": c3, "r3": r3, "op": op}

    def _vars_p2c(self, difficulty: str) -> dict:
        c1 = random.choice([c for c in NON_ZERO_COEFF if abs(c) <= 3])
        r1 = random.choice(PRIME_SET)
        c2 = random.choice([c for c in NON_ZERO_COEFF if abs(c) <= 3])
        r2 = random.choice(PRIME_SET)
        c3 = random.choice([c for c in NON_ZERO_COEFF if abs(c) <= 3])
        r3 = random.choice(PRIME_SET)
        c4 = random.choice([c for c in NON_ZERO_COEFF if abs(c) <= 4])
        return {"c1": c1, "r1": r1, "c2": c2, "r2": r2,
                "c3": c3, "r3": r3, "c4": c4, "r4": 1}

    def _vars_p3a(self, difficulty: str) -> dict:
        for _ in range(50):
            c1 = random.choice([c for c in NON_ZERO_COEFF if abs(c) <= 4])
            r1 = random.choice(SIMPLIFIABLE_SET)
            c2 = random.choice([c for c in NON_ZERO_COEFF if abs(c) <= 3])
            r2 = random.choice(PRIME_SET)
            d = random.choice(PRIME_SET)
            op = random.choice(["+", "-"])
            c2_signed = c2 if op == "+" else -c2

            # Verify both terms rationalize cleanly
            valid = True
            for coeff, radicand in [(c1, r1), (c2_signed, r2)]:
                if radicand % d == 0:
                    continue
                nc_raw, _ = _simplify_rad(coeff, radicand * d)
                if nc_raw % d != 0:
                    valid = False
                    break
            if valid:
                return {"c1": c1, "r1": r1, "c2": c2, "r2": r2, "denom_r": d, "op": op}
        raise _RetrySignal()

    def _vars_p3b(self, difficulty: str) -> dict:
        a = random.choice([c for c in range(1, 6)])
        b = random.choice(PRIME_SET)
        return {"a": a, "b": b}

    def _vars_p4(self, difficulty: str) -> dict:
        a = random.randint(1, 5)
        b = random.choice(SMALL_DENOM)
        r = random.choice(SIMPLIFIABLE_SET)
        c = random.choice(SMALL_DENOM)
        return {"a": a, "b": b, "r": r, "c": c}

    def _vars_p5a(self, difficulty: str) -> dict:
        for _ in range(50):
            b = random.choice([1, 2, 3])
            q = random.choice(PRIME_SET)
            c = random.randint(1, 4)
            sign = random.choice([1, -1])
            denom = b * b * q - c * c
            if denom != 0:
                return {"b": b, "q": q, "c": c, "sign": sign}
        raise _RetrySignal()

    def _vars_p5b(self, difficulty: str) -> dict:
        for _ in range(50):
            p = random.choice(PRIME_SET)
            b = random.choice([1, 2, 3])
            q = random.choice(PRIME_SET)
            c = random.randint(1, 5)
            sign = random.choice([1, -1])
            denom = b * b * q - c * c
            if denom != 0 and p != q:
                return {"p": p, "b": b, "q": q, "c": c, "sign": sign}
        raise _RetrySignal()

    def _vars_p6(self, difficulty: str) -> dict:
        """Compose two sub-patterns for the multi-step combination."""
        combos = [
            ("p2b_mult_distrib", "p1_add_sub"),
            ("p3b_div_simple",   "p1_add_sub"),
            ("p5a_conjugate_int", "p1_add_sub"),
        ]
        sp1, sp2 = random.choice(combos)
        combo_op = random.choice(["+", "-"])
        return {
            "sub_pattern1": sp1,
            "vars1":        self.get_safe_vars_for_pattern(sp1, difficulty),
            "sub_pattern2": sp2,
            "vars2":        self.get_safe_vars_for_pattern(sp2, difficulty),
            "combo_op":     combo_op,
        }

    # =======================================================================
    # Question formatters (private)
    # =======================================================================

    def _fmt_p0(self, v: dict) -> str:
        r = v["r"]
        return rf"化簡 $\sqrt{{{r}}}$。"

    def _fmt_p1(self, v: dict) -> str:
        terms = v["terms"]
        parts = []
        for i, (coeff, radicand, op) in enumerate(terms):
            is_first = (i == 0)
            if is_first:
                parts.append(_format_term_unsimplified(coeff, radicand, True))
            else:
                # Use the op sign rather than the coeff's own sign
                parts.append(_format_term_unsimplified(
                    coeff if op == "+" else -coeff, radicand, False
                ))
        expr = "".join(parts)
        return rf"化簡 ${expr}$。"

    def _fmt_p2a(self, v: dict) -> str:
        q1 = _format_term_unsimplified(v["c1"], v["r1"], True)
        q2 = _format_term_unsimplified(v["c2"], v["r2"], True)
        return rf"化簡 ${q1} \times {q2}$。"

    def _fmt_p2b(self, v: dict) -> str:
        c1, r1 = v["c1"], v["r1"]
        c2, r2 = v["c2"], v["r2"]
        c3, r3 = v["c3"], v["r3"]
        op = v.get("op", "+")
        c3_display = c3 if op == "+" else -c3
        q1 = _format_term_unsimplified(c1, r1, True)
        q2 = _format_term_unsimplified(c2, r2, True)
        q3 = _format_term_unsimplified(c3_display, r3, False)
        return rf"化簡 ${q1} \times ({q2}{q3})$。"

    def _fmt_p2c(self, v: dict) -> str:
        c1, r1 = v["c1"], v["r1"]
        c2, r2 = v.get("c2", 0), v.get("r2", 1)
        c3, r3 = v["c3"], v["r3"]
        c4 = v.get("c4", 0)
        t1 = _format_term_unsimplified(c1, r1, True)
        t2 = (f" + {c2}\\sqrt{{{r2}}}" if c2 > 0 else f" - {abs(c2)}\\sqrt{{{r2}}}") if c2 else ""
        t3 = _format_term_unsimplified(c3, r3, True)
        t4 = (f" + {c4}" if c4 > 0 else f" - {abs(c4)}") if c4 else ""
        return rf"化簡 $({t1}{t2})({t3}{t4})$。"

    def _fmt_p3a(self, v: dict) -> str:
        c1, r1 = v["c1"], v["r1"]
        c2, r2 = v.get("c2", 0), v.get("r2", 1)
        op = v.get("op", "+")
        d = v["denom_r"]
        c2_display = c2 if op == "+" else -c2
        q1 = _format_term_unsimplified(c1, r1, True)
        q2 = _format_term_unsimplified(c2_display, r2, False) if c2 else ""
        return rf"化簡 $({q1}{q2}) \div \sqrt{{{d}}}$。"

    def _fmt_p3b(self, v: dict) -> str:
        a, b = v["a"], v["b"]
        return rf"化簡 $\dfrac{{{a}}}{{\sqrt{{{b}}}}}$。"

    def _fmt_p4(self, v: dict) -> str:
        a, b, r, c = v["a"], v["b"], v["r"], v["c"]
        return rf"計算 $\dfrac{{{a}}}{{{b}}} \times \dfrac{{\sqrt{{{r}}}}}{{{c}}}$ 的值。"

    def _fmt_p5a(self, v: dict) -> str:
        b, q, c, sign = v["b"], v["q"], v["c"], v["sign"]
        b_str = "" if b == 1 else str(b)
        sign_str = "+" if sign == 1 else "-"
        return rf"化簡 $\dfrac{{1}}{{{b_str}\sqrt{{{q}}}{sign_str}{c}}}$。"

    def _fmt_p5b(self, v: dict) -> str:
        p, b, q, c, sign = v["p"], v["b"], v["q"], v["c"], v["sign"]
        b_str = "" if b == 1 else str(b)
        sign_str = "+" if sign == 1 else "-"
        return rf"化簡 $\dfrac{{\sqrt{{{p}}}}}{{{b_str}\sqrt{{{q}}}{sign_str}{c}}}$。"

    def _fmt_p6(self, v: dict) -> str:
        sp1 = v.get("sub_pattern1", "?")
        sp2 = v.get("sub_pattern2", "?")
        return rf"計算下列複合根式運算（子題型：{sp1} 與 {sp2}）。"

    # =======================================================================
    # Internal utilities
    # =======================================================================

    def _combine_latex_answers(
        self, ans1: str, ans2: str, op: str
    ) -> TermsDict:
        """
        Attempt to symbolically combine two LaTeX answer strings.

        This is a best-effort parser for simple forms like:
            "3\\sqrt{2}", "-\\sqrt{5}", "4", "\\frac{2\\sqrt{3}}{5}"

        Returns a TermsDict if successful, else raises ValueError so the
        caller can fall back to string concatenation.
        """
        def _parse_simple(s: str) -> TermsDict:
            s = s.strip()
            # Integer-only answer
            if s.lstrip("-").isdigit():
                return {1: int(s)}
            # k√r form
            import re
            m = re.fullmatch(
                r"(-?)(\d*)\s*\\sqrt\{(\d+)\}", s
            )
            if m:
                neg, k_str, r_str = m.groups()
                k = int(k_str) if k_str else 1
                r = int(r_str)
                return {r: -k if neg else k}
            raise ValueError(f"Cannot parse answer '{s}' for symbolic combination.")

        t1 = _parse_simple(ans1)
        t2 = _parse_simple(ans2)
        if op == "-":
            t2 = {r: -c for r, c in t2.items()}
        merged = {}
        for d, c in {**t1, **t2}.items():
            merged[d] = merged.get(d, 0) + c
        return _merge_terms(merged)


# ---------------------------------------------------------------------------
# Internal sentinel for clean retry signalling
# ---------------------------------------------------------------------------

class _RetrySignal(Exception):
    """Raised inside variable generators to trigger a retry loop cleanly."""
    pass
