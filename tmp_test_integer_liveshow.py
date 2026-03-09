# -*- coding: utf-8 -*-
"""端對端測試：整數四則運算 (含中括號與絕對值) Live Show 路徑 v2"""
import sys, re, ast as _ast, traceback as _tb
sys.stdout.reconfigure(encoding='utf-8')

sk = 'jh_數學1上_FourArithmeticOperationsOfIntegers'

# ── 1. prompt_liveshow.md 載入 ──────────────────────────────────
from core.engine.scaler import AdaptiveScaler
s = AdaptiveScaler()
skill_path = s._get_skill_path(sk)
ls = s._load_skill_prompt(skill_path, 'LIVESHOW')
print(f"[CHECK 1] prompt_liveshow.md: {'OK' if ls else 'MISSING'} ({len(ls.splitlines()) if ls else 0} lines)")
if ls:
    print(f"          line1 = {ls.splitlines()[0]!r}")

# ── 2. registry ─────────────────────────────────────────────────
from core.skill_policies import normalize_skill_id, get_skill_policy
norm   = normalize_skill_id(sk)
policy = get_skill_policy(norm)
print(f"[CHECK 2] normalize_skill_id  : {norm}")
print(f"          family={policy['family']}  fraction_patch={policy['apply_fraction_eval_patch']}")

# ── 3. domain lib injection（含 required_imports）────────────────
from core.code_generator import _inject_domain_libs
dummy = (
    "def generate(level=1, **kwargs):\n"
    "    a = IntegerOps.random_nonzero(-9, 9)\n"
    "    b = random.randint(1, 9)\n"
    "    return {'question_text': f'${a} + {b}$', 'answer': '', 'correct_answer': str(a+b), 'mode': 1}\n"
)
final, inj = _inject_domain_libs(dummy, skill_id=sk)
has_random_import = bool(re.search(r'^import random', final, re.MULTILINE))
has_class        = "class IntegerOps" in final
print(f"[CHECK 3] _inject_domain_libs: injected={inj}, 'import random'={has_random_import}, class IntegerOps={has_class}")

# ── 4. 執行 dummy 鷹架 5 次 ──────────────────────────────────────
print()
print("[CHECK 4] 執行注入後程式碼 (dummy) 5 次:")
try:
    _ast.parse(final)
    g = {}
    exec(final, g)
    gen = g['generate']
    ok = 0
    for i in range(5):
        try:
            res = gen(level=1)
            print(f"  run{i+1}: Q={res.get('question_text','')!r}  A={res.get('correct_answer','')!r}")
            ok += 1
        except Exception as e:
            print(f"  run{i+1}: ERROR {e}")
    print(f"  => {ok}/5 OK")
except Exception:
    _tb.print_exc()

# ── 5. 執行 SKILL.md 中的真實 LIVESHOW scaffold ─────────────────
print()
print("[CHECK 5] 執行 SKILL.md LIVESHOW scaffold (---dash---骨架) 10 次:")

skill_md = open(f'agent_skills/{sk}/SKILL.md', encoding='utf-8').read()
liveshow_m = re.search(r'\[\[MODE:LIVESHOW\]\](.*?)\[\[END_MODE:LIVESHOW\]\]', skill_md, re.DOTALL)
if liveshow_m:
    liveshow_section = liveshow_m.group(1)
    # 找 ---dash--- 分隔的骨架（import 或 def 開頭到下一條 ---dash---）
    dash_m = re.search(r'-{10,}\n((?:import|from |def ).*?)\n-{10,}', liveshow_section, re.DOTALL)
    scaffold_raw = dash_m.group(1).strip() if dash_m else ""

    if scaffold_raw:
        injected_scaffold, _ = _inject_domain_libs(scaffold_raw, skill_id=sk)
        try:
            _ast.parse(injected_scaffold)
            g2 = {}
            exec(injected_scaffold, g2)
            gen2 = g2.get('generate')
            if gen2:
                ok2, err2 = 0, 0
                for i in range(10):
                    try:
                        res = gen2(level=(i % 3) + 1)
                        qt = res.get('question_text', '')
                        ans = res.get('correct_answer', '')
                        print(f"  run{i+1:02} (L={(i%3)+1}): Q={qt!r}  A={ans!r}")
                        ok2 += 1
                    except Exception as e:
                        print(f"  run{i+1:02}: ERROR {e}")
                        err2 += 1
                print(f"  => {ok2}/10 OK, {err2}/10 ERR")
            else:
                print("  generate() not found in scaffold")
        except SyntaxError as e:
            print(f"  SyntaxError in scaffold: {e}")
            for i, l in enumerate(injected_scaffold.splitlines()[:15], 1):
                print(f"  {i:3}: {l!r}")
    else:
        print("  No dash-delimited scaffold found")
else:
    print("  [[MODE:LIVESHOW]] section not found")

# ── 6. 手寫中括號+絕對值題目 generate() ──────────────────────────
print()
print("[CHECK 6] 手寫中括號+絕對值題目 generate() 執行 5 次 (3 levels):")
abs_bracket_code = r"""
import random

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num
    for _ in range(30):
        a = IntegerOps.random_nonzero(-9, 9)
        b = IntegerOps.random_nonzero(-9, 9)
        c = IntegerOps.random_nonzero(2, 5)
        if level == 1:
            # (-a) + b - (-c)
            ans = a + b + c
            q = r'$(' + fmt(a) + r') + (' + fmt(b) + r') - (' + fmt(-c) + r')$'
            return {'question_text': '計算 ' + q + ' 的值。', 'answer': '', 'correct_answer': str(ans), 'mode': 1}
        elif level == 2:
            # |a + b| × c
            raw = abs(a + b)
            ans = raw * c
            q = r'$|' + fmt(a) + r' + (' + fmt(b) + r')| \times ' + fmt(c) + r'$'
            return {'question_text': '計算 ' + q + ' 的值。', 'answer': '', 'correct_answer': str(ans), 'mode': 1}
        else:
            # [(-a) + b] ÷ c  (確保整除)
            base = (-a) + b
            if base == 0:
                continue
            c_vals = [v for v in range(-9, 10) if v != 0 and base % v == 0]
            if not c_vals:
                continue
            c2 = random.choice(c_vals)
            ans = base // c2
            q = r'$[(' + fmt(-a) + r') + ' + fmt(b) + r'] \div (' + fmt(c2) + r')$'
            return {'question_text': '計算 ' + q + ' 的值。', 'answer': '', 'correct_answer': str(ans), 'mode': 1}
    return {'question_text': 'Error', 'answer': '', 'correct_answer': '0', 'mode': 1}
"""
injected_abs, _ = _inject_domain_libs(abs_bracket_code, skill_id=sk)
try:
    _ast.parse(injected_abs)
    g3 = {}
    exec(injected_abs, g3)
    gen3 = g3['generate']
    ok3 = 0
    for i in range(5):
        lv = (i % 3) + 1
        try:
            res = gen3(level=lv)
            print(f"  run{i+1} (L={lv}): {res.get('question_text','')}  ans={res.get('correct_answer','')}")
            ok3 += 1
        except Exception as e:
            print(f"  run{i+1}: ERROR {e}")
    print(f"  => {ok3}/5 OK")
except SyntaxError as e:
    print(f"  SyntaxError: {e}")

print()
print("=== All checks done ===")

ls = s._load_skill_prompt(skill_path, 'LIVESHOW')
status = "OK" if ls else "MISSING"
lines  = len(ls.splitlines()) if ls else 0
line1  = ls.splitlines()[0] if ls else ""
print(f"[CHECK 1] prompt_liveshow.md: {status} ({lines} lines)")
print(f"          line1 = {line1!r}")

# ── 2. registry ─────────────────────────────────────────────────
from core.skill_policies import normalize_skill_id, get_skill_policy
norm   = normalize_skill_id(sk)
policy = get_skill_policy(norm)
print(f"[CHECK 2] normalize_skill_id  : {norm}")
print(f"          family={policy['family']}  fraction_patch={policy['apply_fraction_eval_patch']}")

# ── 3. domain lib injection ──────────────────────────────────────
from core.code_generator import _inject_domain_libs
dummy = (
    "def generate(level=1):\n"
    "    a = IntegerOps.random_nonzero(-9, 9)\n"
    "    return {'question_text': str(a), 'correct_answer': str(a)}\n"
)
final, inj = _inject_domain_libs(dummy, skill_id=sk)
has_class  = "class IntegerOps" in final
print(f"[CHECK 3] _inject_domain_libs: injected={inj}, class IntegerOps in code={has_class}")

# ── 4. 執行 5 次 generate() 從 SKILL.md 鷹架 ────────────────────
print()
print("[CHECK 4] 執行注入後程式碼 5 次 (dummy 鷹架):")
import ast as _ast, traceback as _tb
try:
    _ast.parse(final)
    g = {}
    exec(final, g)
    generate = g['generate']
    ok = 0
    for i in range(5):
        try:
            res = generate(level=1)
            print(f"  run{i+1}: Q={res.get('question_text','')!r}  A={res.get('correct_answer','')!r}")
            ok += 1
        except Exception as e:
            print(f"  run{i+1}: ERROR {e}")
    print(f"  => {ok}/5 OK")
except Exception:
    _tb.print_exc()

# ── 5. 用真實 SKILL.md LIVESHOW scaffold code ───────────────────
print()
print("[CHECK 5] 用 prompt_liveshow.md 中的範例程式碼直接執行 5 次:")
import re
if ls:
    # 找 LIVESHOW 段落中的第一個 python code fence
    m = re.search(r'```python\s*(def generate.*?)```', ls, re.DOTALL)
    if not m:
        m = re.search(r'```\s*(def generate.*?)```', ls, re.DOTALL)
    if m:
        scaffold = m.group(1).strip()
        injected_scaffold, _ = _inject_domain_libs(scaffold, skill_id=sk)
        try:
            _ast.parse(injected_scaffold)
            g2 = {}
            exec(injected_scaffold, g2)
            generate2 = g2.get('generate')
            if generate2:
                ok2 = 0
                for i in range(5):
                    try:
                        res = generate2(level=1)
                        print(f"  run{i+1}: Q={res.get('question_text','')!r}  A={res.get('correct_answer','')!r}")
                        ok2 += 1
                    except Exception as e:
                        print(f"  run{i+1}: ERROR {e}")
                print(f"  => {ok2}/5 OK")
            else:
                print("  generate() not found in scaffold")
        except SyntaxError as e:
            print(f"  SyntaxError: {e}")
    else:
        print("  No python code fence found in LIVESHOW section")
else:
    print("  prompt_liveshow.md missing, skipped")

# ── 6. 中括號 + 絕對值 題目 形態測試 ────────────────────────────
print()
test_inputs = [
    r'(-3) + 5 - (-2)',
    r'|(-4) + 2| \times 3',
    r'[(-6) \div 2 + 1] \times (-4)',
    r'|3 - 8| + (-1) \times 4',
]
print("[CHECK 6] 題目形態符合度 (中括號 / 絕對值 關鍵字偵測):")
for t in test_inputs:
    has_abs = '|' in t or r'\left|' in t
    has_bracket = '[' in t or r'\left[' in t
    print(f"  input: {t!r}")
    print(f"         abs={'YES' if has_abs else 'no'}  bracket={'YES' if has_bracket else 'no'}")

print()
print("=== All checks done ===")
