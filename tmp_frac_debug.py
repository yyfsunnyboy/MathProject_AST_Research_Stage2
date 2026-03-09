# -*- coding: utf-8 -*-
import sys, os
os.environ['PYTHONUTF8'] = '1'
sys.path.insert(0, r'D:\Python\MathProject_AST_Research')
from fractions import Fraction
from core.engine.scaler import AdaptiveScaler

scaler = AdaptiveScaler(model_role='generator')
result = scaler.generate_custom_problems(
    skill_name='jh_數學1上_FourArithmeticOperationsOfNumbers',
    input_text='計算 (-2又1/6) + 1又2/9 - (-1又1/3) 的值。',
    count=1, model_id='qwen3-vl-8b', ablation_mode=False,
)
code = result.get('debug_meta', {}).get('final_code', '')
print(f'CODE LENGTH: {len(code)}')

# Show filter lines
for i, line in enumerate(code.split('\n')):
    if 'denominator' in line and ('>' in line or '<' in line):
        print(f'FILTER L{i+1}: {line.strip()}')

# Patch code: add verbose error in except so we see what fails
patched = code
# Replace the bare 'except Exception:\n            continue' inside generate loop
patched = patched.replace(
    '        except Exception:\n            continue',
    '        except Exception as _ex:\n            import traceback; print(f"  EXCEPT: {_ex}  |  {traceback.format_exc(limit=2)[:300]}")\n            continue'
)
# Also patch the D6 filters to print before continue
patched = patched.replace(
    'if isinstance(ans_init, Fraction) and ans_init.denominator > 120:',
    'if isinstance(ans_init, Fraction) and ans_init.denominator > 120: print(f"  D6a-reject: den={ans_init.denominator}");'
).replace(
    'if isinstance(ans_init, Fraction) and abs(ans_init.numerator) > 120 or ans_init.denominator > 36:',
    'if isinstance(ans_init, Fraction) and abs(ans_init.numerator) > 120 or ans_init.denominator > 36: print(f"  D6b-reject: num={ans_init.numerator} den={ans_init.denominator}");'
)

ns = {}
exec(compile(patched, '<gen>', 'exec'), ns)
out = ns['generate'](level=1)
q = out.get('question_text', '?')
a = out.get('correct_answer', '?')
print(f'Result: q={q[:100]}  ans={a}')
