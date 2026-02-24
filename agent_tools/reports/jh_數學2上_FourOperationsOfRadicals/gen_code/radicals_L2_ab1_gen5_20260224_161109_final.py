# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 5.52s | Tokens: In=637, Out=401
# Created At: 2026-02-24 16:11:09
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    def simplify_radical(expr):
        terms = expr.split('+')
        simplified_terms = []
        for term in terms:
            term = term.strip()
            if term.startswith('-'):
                term = term[1:]
            if 'sqrt' in term:
                parts = term.split('sqrt')
                if len(parts) == 2:
                    num = int(parts[1])
                    if num == 2:
                        simplified_terms.append('sqrt{2}')
                    else:
                        simplified_terms.append(f'sqrt{{{num}}}')
                else:
                    simplified_terms.append(term)
            else:
                simplified_terms.append(term)
        return '+'.join(simplified_terms)

    def generate_term():
        op = random.choice(['+', '-'])
        num = random.randint(1, 10)
        radical = random.choice(['sqrt(2)', 'sqrt(3)', 'sqrt(5)', 'sqrt(6)', 'sqrt(8)', 'sqrt(10)'])
        return f"{op}{num}{radical}"

    def generate_expression():
        term1 = generate_term()
        term2 = generate_term()
        term3 = generate_term()
        term4 = generate_term()
        term5 = generate_term()
        term6 = generate_term()
        return f"({term1}+{term2}+{term3})+({term4}+{term5})({term6})"

    expr = generate_expression()
    simplified_expr = simplify_radical(expr)
    return {
        'question_text': f'\\({simplified_expr}\\)',
        'answer': '',
        'correct_answer': simplified_expr,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': 'Correct' if correct else 'Wrong'}