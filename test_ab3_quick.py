import sys
sys.path.insert(0, 'e:\\Python\\MathProject_AST_Research')

try:
    from skills.gh_ApplicationsOfDerivatives_14b_Ab3 import generate
    print("Calling generate()...")
    result = generate(level=1)
    print("SUCCESS:")
    print(f"  Q: {result['question_text']}")
    print(f"  A: {result['correct_answer']}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
