"""Compare MCRI scores between actual Ab2 and Ab3 generated files."""
import sys
sys.path.insert(0, r"E:\Python\MathProject_AST_Research")

from scripts.evaluate_mcri import evaluate_live_code, analyze_code_robustness

ab2_file = r"E:\Python\MathProject_AST_Research\generated_scripts\scaler_1773063495_fc7f4b_ab2.py"
ab3_file = r"E:\Python\MathProject_AST_Research\generated_scripts\live_show_1773063507_c69e37.py"

with open(ab2_file, encoding="utf-8") as f:
    ab2_code = f.read()
with open(ab3_file, encoding="utf-8") as f:
    ab3_code = f.read()

print(f"Ab2 code length: {len(ab2_code)} chars, has IntegerOps: {'IntegerOps' in ab2_code}, has check(): {'def check' in ab2_code}")
print(f"Ab3 code length: {len(ab3_code)} chars, has IntegerOps: {'IntegerOps' in ab3_code}, has check(): {'def check' in ab3_code}")

# Simulate typical exec_result
exec_result_ab2 = {
    "question_text": "計算 $(\\frac{13}{4}) + (\\frac{5}{3})$ 的值。",
    "answer": "",
    "correct_answer": "59/12",
    "mode": 1,
}
exec_result_ab3 = {
    "question_text": "計算 $(1\\frac{1}{5}) + (1\\frac{1}{6})$ 的值。",
    "answer": "",
    "correct_answer": "41/30",
    "mode": 1,
}

ab2_m = evaluate_live_code(
    code=ab2_code,
    exec_result=exec_result_ab2,
    healer_trace={},
    ablation_mode=False,
)
ab3_m = evaluate_live_code(
    code=ab3_code,
    exec_result=exec_result_ab3,
    healer_trace={"regex_fixes": 3, "ast_fixes": 1},
    ablation_mode=False,
)

def show(label, m):
    bd = m["breakdown"]
    print(f"\n[{label}]")
    print(f"  syntax={m['syntax_score']}  logic={m['logic_score']}  render={m['render_score']}  stability={m['stability_score']}  TOTAL={m['total_score']}")
    print(f"  robust_status={bd['l5_robust_status']}  total_fixes={bd['healer_fixes']}")
    print(f"  has_check={bd['has_check_fn']}  check_body_ok={bd['check_body_ok']}")
    print(f"  l1_syntax={bd['l1_syntax']}  l2_purity={bd['l2_purity']}")
    print(f"  exec_base={bd['logic_exec_base']}  check_bonus={bd['logic_check_bonus']}  ans_bonus={bd['l3_answer_bonus']}  sympy_ok={bd['l3_sympy_ok']}")

show("Ab2", ab2_m)
show("Ab3", ab3_m)

print(f"\nAb3 - Ab2 = {round(ab3_m['total_score'] - ab2_m['total_score'], 2):+.2f}")

status_ab2, ev_ab2 = analyze_code_robustness(ab2_code)
status_ab3, ev_ab3 = analyze_code_robustness(ab3_code)
print(f"\nrobustness: Ab2={status_ab2}({ev_ab2})  Ab3={status_ab3}({ev_ab3})")
