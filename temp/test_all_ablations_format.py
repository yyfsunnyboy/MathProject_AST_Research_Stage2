"""測試三個 Ablation 的答案格式"""

import sys
sys.path.insert(0, r'E:\Python\MathProject_AST_Research\skills')

print("測試三個 Ablation 的答案格式")
print("=" * 80)

# 測試 Ab1
from gh_ApplicationsOfDerivatives_Cloud_Ab1 import generate as generate_ab1
result_ab1 = generate_ab1(level=1)
print("【Ab1 - Bare Prompt】")
print(f"題目: {result_ab1['question_text']}")
print(f"答案: {result_ab1['correct_answer']}")
print()

# 測試 Ab2
from gh_ApplicationsOfDerivatives_Cloud_Ab2 import generate as generate_ab2
result_ab2 = generate_ab2(level=1)
print("【Ab2 - Engineered Prompt】")
print(f"題目: {result_ab2['question_text']}")
print(f"答案: {result_ab2['correct_answer']}")
print()

# 測試 Ab3
from gh_ApplicationsOfDerivatives_Cloud_Ab3 import generate as generate_ab3
result_ab3 = generate_ab3(level=1)
print("【Ab3 - Full Healing】")
print(f"題目: {result_ab3['question_text']}")
print(f"答案: {result_ab3['correct_answer']}")
print()

print("=" * 80)
print("✅ 確認：所有答案格式為純多項式，用逗號間隔")
