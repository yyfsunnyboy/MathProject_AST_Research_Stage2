# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 48.78s | Tokens: In=759, Out=2048
# Created At: 2026-02-24 15:52:44
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    question_text = ""
    answer = ""
    correct_answer = ""
    mode = 1
    terms = []
    operations = ["+", "-"]
    radicals = ["\\sqrt{2}", "\\sqrt{3}", "\\sqrt{5}", "\\sqrt{7}", "\\sqrt{11}", "\\sqrt{13}"]
    coefficients = [1, 2, 3, 4, 5, -1, -2, -3, -4, -5]
    operations_between_terms = random.choices(operations, k=3)
    operations_between_radicals = random.choices(operations, k=1)
    terms_radicals = []
    terms_radicals.append(random.choice(radicals))
    terms_radicals.append(random.choice(radicals))
    terms_radicals.append(random.choice(radicals))
    coefficients_radicals = [random.choice(coefficients), random.choice(coefficients), random.choice(coefficients)]
    terms_radicals = [f"{coefficients_radicals[i]}{terms_radicals[i]}" for i in range(3)]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[1] + "+" + terms_radicals[2]]
    terms_radicals = [terms_radicals[0] + "+" + terms_radicals[