import sys
import os
import traceback
from fractions import Fraction

sys.path.append(os.getcwd())

from core.routes.live_show import (
    _build_structural_profile,
    _is_expression_isomorphic,
    _build_isomorphic_fallback_code,
    _extract_math_expr_from_question
)

class MockIntegerOps:
    @staticmethod
    def random_nonzero(a, b):
        import random
        return random.randint(a, b)
    
    @staticmethod
    def fmt_num(n):
        if n < 0:
            return f"({n})"
        return str(n)
    
def mock_safe_eval(expr):
    from fractions import Fraction
    class MyFrac:
        def __init__(self, n): self.n = n
        def __call__(self, d): return Fraction(self.n, d)

    s = str(expr)
    s = s.replace('×', '*').replace('÷', '/').replace('＋', '+').replace('－', '-')
    s = s.replace('\\times', '*').replace('\\div', '/').replace('\\cdot', '*')
    s = s.replace('\\left', '').replace('\\right', '')
    s = s.replace('\\{', '(').replace('\\}', ')').replace('{', '(').replace('}', ')')
    s = s.replace('\\frac', 'MyFrac')
    return eval(s, {"__builtins__": {}}, {"Fraction": Fraction, "abs": abs, "MyFrac": MyFrac})

def test_fallback(ocr_text):
    print(f"\n--- Testing OCR: {ocr_text} ---")
    try:
        expected_fp = _build_structural_profile(ocr_text)
        
        fallback_code = _build_isomorphic_fallback_code(ocr_text)
        
        exec_globals = {
            "IntegerOps": MockIntegerOps, 
            "Fraction": Fraction,
            "safe_eval": mock_safe_eval
            }
        
        try:
            exec(fallback_code, exec_globals)
        except SyntaxError as e:
            with open("debug_out.txt", "w", encoding="utf-8") as f:
                f.write("Syntax Error in Generated Code!\n")
                f.write(fallback_code)
            raise e
            
        with open("debug_out.txt", "w", encoding="utf-8") as f:
            f.write("Generated Code:\n")
            f.write(fallback_code)
        
        generate_fn = exec_globals['generate']
        
        import time
        s = time.time()
        result = generate_fn()
        print(f"Time: {time.time()-s:.4f}s")
        question_text = result['question_text']
        correct_answer = result['correct_answer']
        print("Generated Question:", question_text)
        print("Provided Answer:", correct_answer)
        
        generated_expr = _extract_math_expr_from_question(question_text)
        is_iso = _is_expression_isomorphic(expected_fp, generated_expr)
        print("Is Isomorphic:", is_iso)
        
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    test_cases = [
        # complex division
        r"[(-60)\div[(-7)\times2-1]]"
    ]
    
    for tc in test_cases:
        test_fallback(tc)
