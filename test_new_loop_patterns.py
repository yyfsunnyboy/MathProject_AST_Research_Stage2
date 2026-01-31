"""
測試新增的無限迴圈模式（5, 6, 7）
"""
from core.code_generator import fix_infinite_loop_patterns

# 測試案例 5: while True 無 break
test_code_5 = """
def generate():
    while True:
        x = random.randint(1, 10)
        if x > 5:
            return x
"""

# 測試案例 6: set 累積型
test_code_6 = """
def generate():
    max_degree = 5
    num_terms = 3
    degrees = set()
    while len(degrees) < num_terms:
        degrees.add(random.randint(0, max_degree))
    return degrees
"""

# 測試案例 7: list 唯一性過濾
test_code_7 = """
def generate():
    max_degree = 5
    num_terms = 3
    exps = []
    while len(exps) < num_terms:
        x = random.randint(0, max_degree)
        if x not in exps:
            exps.append(x)
    return exps
"""

print("="*80)
print("測試案例 5: while True 無 break → for guard")
print("="*80)
fixed_5, fixes_5 = fix_infinite_loop_patterns(test_code_5)
print(f"修復次數: {fixes_5}")
if fixes_5 > 0:
    print("修復後:")
    print(fixed_5)

print("\n" + "="*80)
print("測試案例 6: set 累積型 → 洗牌切片")
print("="*80)
fixed_6, fixes_6 = fix_infinite_loop_patterns(test_code_6)
print(f"修復次數: {fixes_6}")
if fixes_6 > 0:
    print("修復後:")
    print(fixed_6)

print("\n" + "="*80)
print("測試案例 7: list 唯一性過濾 → random.sample")
print("="*80)
fixed_7, fixes_7 = fix_infinite_loop_patterns(test_code_7)
print(f"修復次數: {fixes_7}")
if fixes_7 > 0:
    print("修復後:")
    print(fixed_7)

print("\n" + "="*80)
print(f"🎉 新模式測試完成！總修復: {fixes_5 + fixes_6 + fixes_7}")
print("="*80)
