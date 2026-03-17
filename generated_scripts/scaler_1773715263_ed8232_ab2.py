pattern_id = "radical_division_same_root"
c1 = 7
r1 = 14
c2 = 1
r2 = 14

question_text = f"計算 $\\sqrt{{{c1 \\times r1}}} \\div \\sqrt{{{c2 \\times r2}}}$ 的值。"
expr = sp.sqrt(c1 * r1) / sp.sqrt(c2 * r2)
ans_latex = sp.latex(sp.simplify(expr))

return {
    'question_text': question_text,
    'correct_answer': ans_latex,
    'solution_steps': ["利用根式除法性質：$\\sqrt{a} \\div \\sqrt{b} = \\sqrt{a/b}$，並化簡結果。"],
    'mode': 1
}