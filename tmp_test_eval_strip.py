import re

cases = [
    'result = safe_eval(expr, {"__builtins__": {"abs": abs}})',
    'x = safe_eval(some_expr, globals_dict)',
    'y = safe_eval(expr)',
    'z = safe_eval(abs(-42) / (-8 * 1 - 6), {"abs": abs})',
    'w = safe_eval("12+3", my_env)',
]

pattern = r'\bsafe_eval\s*\(\s*([^,)]+?)\s*,\s*(?:\{[^}]*\}|[A-Za-z_]\w*)\s*\)'

for c in cases:
    result = re.sub(pattern, r'safe_eval(\1)', c)
    changed = "✅ STRIPPED" if result != c else "  unchanged"
    print(f"{changed}")
    print(f"  IN:  {c}")
    print(f"  OUT: {result}")
    print()
