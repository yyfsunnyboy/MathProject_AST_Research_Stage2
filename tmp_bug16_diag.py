"""Bug 16 Diagnostic: test which generate() patterns cause l1=4.0"""
import sys; sys.path.insert(0, '.')
from core.prompts.domain_function_library import get_required_domains, get_domain_helpers_code
from scripts.evaluate_mcri import evaluate_live_code

skill = 'jh_數學1上_FourArithmeticOperationsOfNumbers'
domains = get_required_domains(skill)
stubs = get_domain_helpers_code(domains, stub_mode=True)

# Case 1: model uses IntegerOps.safe_eval (preferred)
code1 = stubs + """

def generate(level=1, **kwargs):
    from fractions import Fraction
    a = Fraction(-11, 4)
    ans = IntegerOps.safe_eval(str(a))
    return {"question_text": "test", "correct_answer": str(ans), "mode": 1}

def check(user_ans, correct_ans):
    return {"correct": user_ans == correct_ans}
"""

# Case 2: model uses bare eval (raw model output)
code2 = stubs + """

def generate(level=1, **kwargs):
    from fractions import Fraction
    a = Fraction(-11, 4)
    ans = eval(str(a))
    return {"question_text": "test", "correct_answer": str(ans), "mode": 1}

def check(user_ans, correct_ans):
    return {"correct": user_ans == correct_ans}
"""

# Case 3: healer replaced eval with safe_eval
code3 = stubs + """

def generate(level=1, **kwargs):
    from fractions import Fraction
    a = Fraction(-11, 4)
    ans = safe_eval(str(a))
    return {"question_text": "test", "correct_answer": str(ans), "mode": 1}

def check(user_ans, correct_ans):
    return {"correct": user_ans == correct_ans}
"""

# Case 4: _inject_domain_libs version (full class, eval at depth=1)
from core.code_generator import _inject_domain_libs
base_code = """
def generate(level=1, **kwargs):
    from fractions import Fraction
    a = Fraction(-11, 4)
    ans = eval(str(a))
    return {"question_text": "test", "correct_answer": str(ans), "mode": 1}
"""
code4, _ = _inject_domain_libs(base_code)

exec_result = {'question_text': 'test', 'correct_answer': '-11/4', 'mode': 1}
cases = [
    ('Case1: IntegerOps.safe_eval', code1, {'ast_fixes': 0}),
    ('Case2: bare eval (no heal)', code2, {'ast_fixes': 0}),
    ('Case3: healed safe_eval', code3, {'ast_fixes': 1}),
    ('Case4: _inject_domain_libs', code4, {'ast_fixes': 1}),
]
for label, code, trace in cases:
    m = evaluate_live_code(code=code, exec_result=exec_result, healer_trace=trace, ablation_mode=False)
    print(f"{label}: l1={m['breakdown']['l1_syntax']}, syntax={m['syntax_score']}, total={m['total_score']}")
    # Check for eval nodes
    import ast as _ast
    try:
        tree = _ast.parse(code)
        class Finder(_ast.NodeVisitor):
            def __init__(self): self._in_class=0; self.hits=[]
            def visit_ClassDef(self, n): self._in_class+=1; self.generic_visit(n); self._in_class-=1
            def visit_Name(self, n):
                if n.id in ('eval', 'exec'): self.hits.append((n.id, n.lineno, self._in_class))
        f = Finder(); f.visit(tree)
        for name, line, depth in f.hits:
            print(f"  -> {name}() at L{line}, in_class={depth}")
    except: pass
    print()
