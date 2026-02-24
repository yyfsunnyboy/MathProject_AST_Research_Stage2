# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 182.74s | Tokens: In=631, Out=11706
# Created At: 2026-02-20 04:50:41
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
from collections import defaultdict

def generate(level=1, **kwargs):
    m_list = [2,3,5,6,7,10]
    k1 = random.randint(2,5)
    m1 = random.choice(m_list)
    a = k1**2 * m1
    k2 = random.randint(2,5)
    m2 = random.choice(m_list)
    b = k2**2 * m2
    k3 = random.randint(2,5)
    m3 = random.choice(m_list)
    c = k3**2 * m3
    m4 = random.choice(m_list)
    k4 = random.randint(2,5)
    d = k4**2 * m4
    m5 = random.choice(m_list)
    k5 = random.randint(2,5)
    e = k5**2 * m5
    m6 = random.choice(m_list)
    k6 = random.randint(2,5)
    f = k6**2 * m6
    term1 = {'coefficient': k1, 'radicand': m1}
    term2 = {'coefficient': k2, 'radicand': m2}
    term3 = {'coefficient': -2*k3, 'radicand': m3}
    radicand4 = m4 * m6
    term4 = {'coefficient': k4 * k6, 'radicand': radicand4}
    term5 = {'coefficient': -k4, 'radicand': m4}
    radicand6 = m5 * m6
    term6 = {'coefficient': k5 * k6, 'radicand': radicand6}
    term7 = {'coefficient': -k5, 'radicand': m5}
    all_terms = [term1, term2, term3, term4, term5, term6, term7]
    grouped = defaultdict(float)
    for term in all_terms:
        radicand = term['radicand']
        grouped[radicand] += term['coefficient']
    terms = []
    for radicand, coeff in grouped.items():
        if coeff != 0:
            if radicand == 1:
                terms.append(str(coeff))
            else:
                if coeff > 0:
                    terms.append(f"{coeff}\\sqrt{{{radicand}}}")
                else:
                    terms.append(f"-{abs(coeff)}\\sqrt{{{radicand}}}")
    correct_answer = ' + '.join(terms)
    correct_answer = correct_answer.replace(' + -', ' - ')
    first_part = f"\\sqrt{{{a}}} + \\sqrt{{{b}}} - 2\\sqrt{{{c}}}"
    second_part = f"(\\sqrt{{{d}}} + \\sqrt{{{e}}})(\\sqrt{{{f}}} - 1)"
    question_text = f"({first_part}) + ({second_part})"
    return {
        'question_text': f"${question_text}$",
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}