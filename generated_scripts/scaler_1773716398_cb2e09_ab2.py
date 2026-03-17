pattern_id = "RadicalOps.Division.Simplified"
difficulty = "Medium"
target_expression = r"\sqrt{98} \div \sqrt{14}"

# 保持同構：根式除法，根號內數字可整除
r2 = 2
multiplier = 7
r1 = r2 * multiplier

question_text = f"計算 $\\sqrt{{{r1}}} \\div \\sqrt{{{r2}}}$ 的值。"
expr = sp.sqrt(r1) / sp.sqrt(r2)
correct_answer = sp.latex(sp.simplify(expr))

# 路徑 A 僅需 3 行變數宣告，符合 DomainFunctionHelper API 規範
pattern_id = "RadicalOps.Division.Simplified"
difficulty = "Medium"
target_expression = r"\sqrt{98} \div \sqrt{14}"