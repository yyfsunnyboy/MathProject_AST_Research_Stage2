import sys
sys.path.insert(0, 'e:\\Python\\MathProject_AST_Research')

print("=" * 60)
print("Testing Ab1 (Bare)...")
print("=" * 60)
from skills.gh_ApplicationsOfDerivatives_14b_Ab1 import generate as gen_ab1
for i in range(3):
    result = gen_ab1(level=1)
    print(f"Ab1 Run {i+1}:")
    print(f"  Q: {result['question_text']}")
    print(f"  A: {result['correct_answer']}\n")

print("=" * 60)
print("Testing Ab2 (Engineered)...")
print("=" * 60)
from skills.gh_ApplicationsOfDerivatives_14b_Ab2 import generate as gen_ab2
for i in range(3):
    result = gen_ab2(level=1)
    print(f"Ab2 Run {i+1}:")
    print(f"  Q: {result['question_text']}")
    print(f"  A: {result['correct_answer']}\n")

print("=" * 60)
print("Testing Ab3 (Full Healing)...")
print("=" * 60)
from skills.gh_ApplicationsOfDerivatives_14b_Ab3 import generate as gen_ab3
for i in range(3):
    result = gen_ab3(level=1)
    print(f"Ab3 Run {i+1}:")
    print(f"  Q: {result['question_text']}")
    print(f"  A: {result['correct_answer']}\n")

print("✅ All ablations working!")
