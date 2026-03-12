def generate(level=1, **kwargs):
    question_text = 'import random\nimport math\nfrom fractions import Fraction\n# RadicalOps and FractionOps are injected automatically\n\ndef generate(level=1, **kwargs):\n    # Step 0: 解析題型結構 (必須先寫出這三行註解，確保你確實算過)\n    # 根式項數 (即原題參與加減運算的根式有幾項): 2 項\n    # 乘法分配律區塊: 0 (無)\n    # 特殊結構: 分數係數 / 指數被開方數\n\n    simplifiable = [8, 12, 18, 20, 24, 27, 32, 45, 48, 50, 72, 75]\n    simple = [2, 3, 5, 7, 11]\n\n    for _ in range(50):\n        try:\n            # 1. 根據 Step 0 的項數與區塊宣告對應數量的變數\n            c1 = Fraction(1, 1)\n            r1 = Fraction(random.choice(simplifiable), random.choice(simplifiable))\n            c2 = Fraction(1, 1)\n            r2 = Fraction(random.choice(simplifiable), random.choice(simplifiable))\n\n            # 2. 組合題目字串\n            q_part1 = RadicalOps.format_term_unsimplified(c1, r1, True)\n            q_part2 = RadicalOps.format_term_unsimplified(c2, r2, False)\n            question_text = f"計算 $({q_part1}) \\\\div ({q_part2})$ 的值。"\n\n            # 3. 計算答案（純數值操作）\n            final_terms = {}\n\n            # 狀況 C: 若被開方數 (radicand) 是 Fraction (例如 \\frac{\\sqrt{A}}{\\sqrt{B}}) 相乘除\n            new_c, new_r = RadicalOps.simplify_term(c1 * c2, r1 / r2)\n            final_terms[new_r] = final_terms.get(new_r, 0) + new_c\n\n            correct_answer = RadicalOps.format_expression(final_terms)\n            if correct_answer and correct_answer != \'0\':\n                return {\n                    \'question_text\': question_text,\n                    \'answer\': \'\',\n                    \'correct_answer\': correct_answer,\n                    \'mode\': 1,\n                    \'_o1_healed\': False\n                }\n        except Exception:\n            continue\n\n    return {\'question_text\': \'Error\', \'answer\': \'\', \'correct_answer\': \'0\', \'mode\': 1}\n\ndef check(user_answer, correct_answer):\n    correct = str(user_answer).strip() == str(correct_answer).strip()\n    return {\'correct\': correct, \'result\': \'正確\' if correct else \'錯誤\'}'
    try:
        from core.code_utils.live_show_math_utils import _recompute_correct_answer_from_question
        ans = _recompute_correct_answer_from_question(question_text) or "0"
    except Exception:
        ans = "0"
    if "計算" not in question_text:
        question_text = f"計算 ${question_text}$ 的值。"
    return {
        "question_text": question_text,
        "correct_answer": str(ans),
        "mode": 1
    }

def check(user_answer, correct_answer):
    ok = str(user_answer).strip() == str(correct_answer).strip()
    return {"correct": ok, "result": "正確" if ok else "錯誤"}
