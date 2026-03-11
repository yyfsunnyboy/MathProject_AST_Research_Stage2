"""Unit tests for Bug 26 MIXED_GUARD regex and decision logic."""
import re

_HAS_MIXED_RE = re.compile(r'(?<![\\{/])\d+\s*\\frac\s*\{')

def has_mixed(qt):
    return bool(_HAS_MIXED_RE.search(qt))

# (question_text_as_python_string,  expect_has_mixed, description)
tests = [
    (r"計算 $\frac{2}{3}-(-\frac{3}{4})$ 的值。",        False, "pure fractions only"),
    (r"計算 $2\frac{1}{3}-(-\frac{3}{4})$ 的值。",        True,  "mixed number 2\\frac"),
    (r"計算 $-3\frac{2}{5}+\frac{1}{2}$ 的值。",          True,  "negative mixed -3\\frac"),
    (r"計算 $\frac{7}{3} \div \frac{2}{5}$ 的值。",       False, "improper pure \\frac"),
    (r"計算 $8\frac{7}{10}-(12\frac{3}{5})$ 的值。",      True,  "two mixed numbers"),
    (r"計算 $\frac{-13}{6}+\frac{3}{4}$ 的值。",          False, "negative numerator pure frac"),
    # guard edge case: \frac should NOT match as mixed
    (r"\frac{2}{3} test",                                  False, "bare \\frac, no digit before"),
]

print("=" * 60)
print("Bug 26 MIXED_GUARD — regex unit tests")
print("=" * 60)
all_ok = True
for qt, expected, desc in tests:
    got = has_mixed(qt)
    status = "PASS" if got == expected else "FAIL"
    if got != expected:
        all_ok = False
    print(f"  [{status}] has_mixed={got!s:<5}  expected={expected!s:<5}  {desc}")

print()
print("=" * 60)
print("Decision matrix (mode x has_mixed -> trigger?)")
print("=" * 60)
cases = [
    ("fraction", False, "pure in, pure out  -> NO trigger"),
    ("fraction", True,  "pure in, mixed out -> BUG26 trigger"),
    ("mixed",    True,  "mixed in, mixed out -> NO trigger"),
    ("mixed",    False, "mixed in, pure out -> BUG26 trigger"),
    ("none",     True,  "non-frac skill     -> handled by Bug25"),
]
for mode, hm, note in cases:
    trigger = mode in ("fraction", "mixed") and (
        (mode == "fraction" and hm) or (mode == "mixed" and not hm)
    )
    t_str = "TRIGGER  ✓" if trigger else "no-trigger"
    print(f"  mode={mode!r:10s} has_mixed={str(hm):5s} -> {t_str}  ({note})")

print()
if all_ok:
    print("All regex tests PASSED ✅")
else:
    print("SOME TESTS FAILED ❌")
    raise SystemExit(1)
