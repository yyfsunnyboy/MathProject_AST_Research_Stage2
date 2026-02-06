"""
測試無限迴圈 Healer 功能
"""
from core.code_generator import fix_infinite_loop_patterns

# 測試案例 1: 典型的無限迴圈模式
test_code_1 = """
def generate(level=1, **kwargs):
    max_degree = random.randint(3, 5)
    num_terms = random.randint(3, 5)
    terms = []
    
    while len(terms) < num_terms:
        degree = random.randint(0, max_degree)
        if any(d == degree for _, d in terms):
            continue
        coeff = random.choice([1, 2, 3])
        terms.append((coeff, degree))
    
    return terms
"""

# 測試案例 2: num_terms 定義問題
test_code_2 = """
def generate(level=1, **kwargs):
    max_degree = random.randint(3, 5)
    num_terms = random.randint(3, 5)
    degrees = []
    
    while len(degrees) < num_terms:
        d = random.randint(0, max_degree)
        if d not in degrees:
            degrees.append(d)
    
    return degrees
"""

# 測試案例 3: while 條件中有 random.randint (新發現的問題)
test_code_3 = """
def generate(level=1, **kwargs):
    derivative_orders_list = []
    while len(derivative_orders_list) < random.randint(1, 2):
        order = random.randint(1, max_degree)
        if order not in derivative_orders_list:
            derivative_orders_list.append(order)
    return derivative_orders_list
"""

# 測試案例 4: 嵌套 while 迴圈（最新發現！）
test_code_4 = """
def generate(level=1, **kwargs):
    derivative_orders_list = []
    while len(derivative_orders_list) < num_derivatives:
        while len(derivative_orders_list) < num_derivatives:
            order = random.randint(1, min(max_degree, 4))
        if all((order != o for o in derivative_orders_list)):
            derivative_orders_list.append(order)
    return derivative_orders_list
"""

print("="*80)
print("測試案例 1: 典型 while len() < num_terms 模式")
print("="*80)
fixed_code_1, fixes_1 = fix_infinite_loop_patterns(test_code_1)
print(f"\n✅ 修復次數: {fixes_1}")
if fixes_1 > 0:
    print("\n修復後的代碼:")
    print(fixed_code_1)

print("\n" + "="*80)
print("測試案例 2: num_terms 定義 + while 迴圈")
print("="*80)
fixed_code_2, fixes_2 = fix_infinite_loop_patterns(test_code_2)
print(f"\n✅ 修復次數: {fixes_2}")
if fixes_2 > 0:
    print("\n修復後的代碼:")
    print(fixed_code_2)

print("\n" + "="*80)
print("測試案例 3: while 條件中有 random.randint() (動態目標值)")
print("="*80)
fixed_code_3, fixes_3 = fix_infinite_loop_patterns(test_code_3)
print(f"\n✅ 修復次數: {fixes_3}")
if fixes_3 > 0:
    print("\n修復後的代碼:")
    print(fixed_code_3)

print("\n" + "="*80)
print("測試案例 4: 嵌套 while 迴圈（內層無限迴圈）")
print("="*80)
fixed_code_4, fixes_4 = fix_infinite_loop_patterns(test_code_4)
print(f"\n✅ 修復次數: {fixes_4}")
if fixes_4 > 0:
    print("\n修復後的代碼:")
    print(fixed_code_4)

print("\n" + "="*80)
print("🎉 測試完成！")
print(f"總修復次數: {fixes_1 + fixes_2 + fixes_3 + fixes_4}")
print("="*80)
