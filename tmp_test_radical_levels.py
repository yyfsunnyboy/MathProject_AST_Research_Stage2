import os
import sys

# Setup environment
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from core.scaffold.domain_libs import RadicalOps
import random
import math
from fractions import Fraction

# Read the python code block from prompt_benchmark.md
prompt_path = os.path.join(os.path.dirname(__file__), "agent_skills", "jh_數學2上_FourOperationsOfRadicals", "prompt_benchmark.md")
with open(prompt_path, "r", encoding="utf-8") as f:
    text = f.read()

code_block = text.split("```python")[1].split("```")[0].strip()

# Execute the code block to load `generate` and `check` functions
namespace = {
    "random": random,
    "math": math,
    "Fraction": Fraction,
    "RadicalOps": RadicalOps
}
exec(code_block, namespace)

generate = namespace["generate"]

print("--- Testing Level 1 (Simplifying) ---")
for i in range(2):
    res = generate(level=1)
    print(f"Q: {res['question_text']}")
    print(f"A: {res['correct_answer']}\n")

print("--- Testing Level 2 (Combining) ---")
for i in range(2):
    res = generate(level=2)
    print(f"Q: {res['question_text']}")
    print(f"A: {res['correct_answer']}\n")

print("--- Testing Level 3 (Four Operations) ---")
for i in range(2):
    res = generate(level=3)
    print(f"Q: {res['question_text']}")
    print(f"A: {res['correct_answer']}\n")
