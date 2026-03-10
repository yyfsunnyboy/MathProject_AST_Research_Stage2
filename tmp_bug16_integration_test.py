"""
Integration test: simulate the Bug 16 fix in live_show_pipeline.py.
Verifies that the eval→safe_eval regex pass applied BEFORE evaluate_live_code
causes live Ab3 MCRI to always get l1=7.5 even when raw model output has eval().
"""
import sys, re
sys.path.insert(0, '.')
from core.prompts.domain_function_library import get_required_domains, get_domain_helpers_code
from scripts.evaluate_mcri import evaluate_live_code

skill = 'jh_數學1上_FourArithmeticOperationsOfNumbers'
domains = get_required_domains(skill)
api_stubs = get_domain_helpers_code(domains, stub_mode=True)

# Simulate raw model output with bare eval() (pre-healer)
raw_model_code = """
def generate(level=1, **kwargs):
    from fractions import Fraction
    a = Fraction(-11, 4)
    ans = eval(str(a))  # Model used bare eval() -- healer failed to fix it
    return {"question_text": "test", "correct_answer": str(ans), "mode": 1}

def check(user_ans, correct_ans):
    return {"correct": user_ans == correct_ans}
"""

# Simulate what run_ab3_full_healer does:
# 1. Run healer (assume it crashed or missed eval) → healed_exec_code = raw_model_code
# 2. Apply optimize + patch
healed_exec_code = raw_model_code  # worst case: healer didn't fix it

# 3. [Bug 16 Fix] Apply the regex eval→safe_eval pass
healed_exec_code_BEFORE_FIX = healed_exec_code  # no fix
healed_exec_code_AFTER_FIX = re.sub(r'\beval\s*\(', 'safe_eval(', healed_exec_code)

exec_result = {'question_text': 'test', 'correct_answer': '-11/4', 'mode': 1}
healer_trace = {'regex_fixes': 1, 'ast_fixes': 2}  # some fixes were made (other issues)

# Before fix: api_stubs + healed_exec_code with bare eval
eval_code_before = api_stubs + "\n\n" + healed_exec_code_BEFORE_FIX
m_before = evaluate_live_code(code=eval_code_before, exec_result=exec_result, healer_trace=healer_trace, ablation_mode=False)

# After fix: api_stubs + healed_exec_code with safe_eval
eval_code_after = api_stubs + "\n\n" + healed_exec_code_AFTER_FIX
m_after = evaluate_live_code(code=eval_code_after, exec_result=exec_result, healer_trace=healer_trace, ablation_mode=False)

print("=== Bug 16 Fix: eval→safe_eval regex pass in pipeline ===")
print(f"BEFORE fix: l1={m_before['breakdown']['l1_syntax']}, syntax={m_before['syntax_score']}, total={m_before['total_score']}")
print(f"AFTER  fix: l1={m_after['breakdown']['l1_syntax']}, syntax={m_after['syntax_score']}, total={m_after['total_score']}")
print()

# Ab2 comparison (raw code, no class, no healer)
ab2_code = raw_model_code  # same base code for Ab2 (no healer)
# Ab2 stubs + raw_code (for text path: just raw_code without stubs)
m_ab2 = evaluate_live_code(code=ab2_code, exec_result=exec_result, healer_trace={}, ablation_mode=False)
print(f"Ab2 MCRI: l1={m_ab2['breakdown']['l1_syntax']}, syntax={m_ab2['syntax_score']}, total={m_ab2['total_score']}")
print(f"Ab3 MCRI: l1={m_after['breakdown']['l1_syntax']}, syntax={m_after['syntax_score']}, total={m_after['total_score']}")
print(f"Ab3 - Ab2 = {round(m_after['total_score'] - m_ab2['total_score'], 2):+}")
print()

if m_after['total_score'] >= m_ab2['total_score']:
    print("PASS: Ab3 >= Ab2 invariant maintained after Bug 16 fix.")
else:
    print(f"FAIL: Ab3 ({m_after['total_score']}) < Ab2 ({m_ab2['total_score']})")
