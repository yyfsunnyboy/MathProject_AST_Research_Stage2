"""
Diagnose: what code does Flask actually pass to evaluate_live_code for Ab3?
"""
import sys, requests
sys.path.insert(0, '.')
from scripts.evaluate_mcri import evaluate_live_code

BASE = "http://127.0.0.1:5000"
SKILL_ID = "jh_數學1上_FourArithmeticOperationsOfNumbers"
OCR = "-2¾ + 1²⁄₇"

print("Calling /api/generate_live ...")
resp = requests.post(f"{BASE}/api/generate_live", json={
    "prompt": OCR,
    "skill_id": SKILL_ID,
    "ablation_mode": False,
    "model_id": "gemini-2.0-flash",
}, timeout=90)
data = resp.json()

# 1. MCRI from route
ab3_mcri = data.get("mcri", {})
ab2_mcri = (data.get("ab2_result") or {}).get("mcri", {})
print(f"\nRoute-reported: Ab2 total={ab2_mcri.get('total_score')}  Ab3 total=  {ab3_mcri.get('total_score')}")
print(f"Ab2 l1={ab2_mcri.get('breakdown',{}).get('l1_syntax')}  Ab3 l1={ab3_mcri.get('breakdown',{}).get('l1_syntax')}")

# 2. Manually evaluate the final_code that was returned
final_code = data.get("final_code", "")
print(f"\nfinal_code length: {len(final_code)}, has 'class ': {'class ' in final_code}, has 'eval': {'eval(' in final_code}")

# check eval location
import ast as _ast
try:
    tree = _ast.parse(final_code)
    class Finder(_ast.NodeVisitor):
        def __init__(self):
            self._in_class = 0
            self.hits = []
        def visit_ClassDef(self, node):
            self._in_class += 1
            self.generic_visit(node)
            self._in_class -= 1
        def visit_Call(self, node):
            if isinstance(node.func, _ast.Name) and node.func.id in ('eval','exec'):
                self.hits.append((node.func.id, node.lineno, self._in_class))
            self.generic_visit(node)
    f = Finder()
    f.visit(tree)
    if f.hits:
        for name, line, depth in f.hits:
            print(f"  {name}() at L{line} in_class_depth={depth}")
    else:
        print("  No eval/exec found in final_code")
except Exception as e:
    print(f"  Parse error: {e}")

# 3. Manually score the final_code
if final_code:
    ab3_result = data.get("results", [{}])
    first_result = ab3_result[0] if ab3_result else {}
    m = evaluate_live_code(
        code=final_code,
        exec_result=first_result,
        healer_trace={"regex_fixes": 0, "ast_fixes": data.get("fixes", 0)},
        ablation_mode=False,
    )
    bd = m["breakdown"]
    print(f"\nManual re-score of final_code:")
    print(f"  l1_syntax={bd['l1_syntax']}  syntax_score={m['syntax_score']}  total={m['total_score']}")

print("\n--- raw_code vs final_code different? ---")
raw_code = data.get("raw_code", "")
print(f"raw_code length={len(raw_code)}, final_code length={len(final_code)}")
print(f"Same code: {raw_code == final_code}")
if raw_code != final_code:
    print("raw_code has 'class ':", 'class ' in raw_code)
    print("raw_code has 'eval(':", 'eval(' in raw_code)
