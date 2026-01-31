"""測試修改後的 Ab1 check() 函數和 Bare Prompt"""

import sys
sys.path.insert(0, r'E:\Python\MathProject_AST_Research\skills')

print("=" * 80)
print("【測試 Ab1 check() 函數】")
print("=" * 80)

from gh_ApplicationsOfDerivatives_Cloud_Ab1 import generate, check

# 測試生成
result = generate(level=1)
print(f"生成題目: {result['question_text']}")
print(f"正確答案: {result['correct_answer']}")
print()

# 測試 check() 函數的各種情況
test_cases = [
    ("正確答案", result['correct_answer'], result['correct_answer']),
    ("移除空白", result['correct_answer'].replace(" ", ""), result['correct_answer']),
    ("錯誤答案", "x^2 + 1", result['correct_answer']),
    ("未作答", "", result['correct_answer']),
]

print("檢查函數測試：")
for name, student_ans, correct_ans in test_cases:
    result_check = check(student_ans, correct_ans)
    status = "✅" if result_check['correct'] else "❌"
    print(f"{status} {name}: {result_check}")

print()
print("=" * 80)
print("【測試 Bare Prompt 是否包含 check() 要求】")
print("=" * 80)

from core.prompts.prompt_builder import PromptBuilder

prompt = PromptBuilder.build(
    master_spec="",
    ablation_id=1,
    textbook_example="範例：已知 f(x) = 3x^2，求 f'(x)",
    topic="導數"
)

if "def check(student_answer, correct_answer)" in prompt:
    print("✅ Bare Prompt 包含 check() 函數要求")
else:
    print("❌ Bare Prompt 缺少 check() 函數要求")

if "'correct': True/False" in prompt:
    print("✅ Bare Prompt 包含 check() 回傳格式說明")
else:
    print("❌ Bare Prompt 缺少 check() 回傳格式說明")

print()
print("✅ 所有修改完成！")
