pattern_id = "p1"  # ← 強制攔截器會刪除此行，但為測試目的保留

# 由於目標題型為：\sqrt{5} \times \sqrt{11}，屬於「根式 × 根式」結構
# 且 SKILL.md 規定：路徑 B 必須使用 sp.sqrt() 與 sp.Rational()，並嚴禁 abs()
# 同時，題型結構為「最簡根式 × 最簡根式」，無分數、無整數係數、無括號

# 生成邏輯：隨機選擇兩個質數（2,3,5,7,11,13,17,19）作為根號內數字
# 保持運算符為 \times，無任何其他符號或結構變動

import random
import sympy as sp

def generate(level=1, **kwargs):
    r1 = random.choice([2, 3, 5, 7, 11, 13, 17, 19])
    r2 = random.choice([2, 3, 5, 7, 11, 13, 17, 19])
    # 確保 r1 != r2 以避免重複（非必要，但提升題目多樣性）
    while r1 == r2:
        r2 = random.choice([2, 3, 5, 7, 11, 13, 17, 19])

    question_text = f"\\sqrt{{{r1}}} \\times \\sqrt{{{r2}}}"
    expr = sp.sqrt(r1) * sp.sqrt(r2)
    ans_latex = sp.latex(sp.simplify(expr))

    return {
        'question_text': question_text,
        'correct_answer': ans_latex,
        'solution_steps': ["根號內數字相乘，並化簡為最簡根式。"],
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {'correct': str(user_answer).strip() == str(correct_answer).strip(), 'result': '正確'}