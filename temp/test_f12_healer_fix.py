"""
測試 F.12 Healer 修復後的安全性
驗證：移除 clean_latex_output 時不會破壞語法
"""
import re

# 模擬 F.12 Healer 的修復邏輯（修復後的版本）
def test_f12_fix(code):
    """模擬新的 F.12 修復邏輯"""
    fixes = 0
    
    # 模式 3: return {..., 'question_text': clean_latex_output(q), ...}
    code, n3 = re.subn(
        r"(['\"]question_text['\"])\s*:\s*clean_latex_output\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\)",
        r"\1: \2",  # 不加註解，避免破壞字典語法
        code
    )
    fixes += n3
    
    return code, fixes

# 測試案例 1: return 字典中的 clean_latex_output
test_code_1 = """
def generate():
    q = "問題"
    ans = "答案"
    return {'question_text': clean_latex_output(q), 'correct_answer': ans, 'mode': 1}
"""

# 測試案例 2: 多行 return 字典
test_code_2 = """
def generate():
    return {
        'question_text': clean_latex_output(q_str),
        'correct_answer': correct_answer,
        'answer': correct_answer,
        'mode': 1
    }
"""

# 測試案例 3: 複雜的 return (實際失敗案例)
test_code_3 = """
def generate():
    return {'question_text': clean_latex_output(q), 'correct_answer': correct_answer, 'answer': correct_answer, 'mode': 1}
"""

print("="*80)
print("測試 F.12 Healer 修復的安全性")
print("="*80)

# 測試 1
print("\n【測試 1】單行 return 字典")
fixed_1, n1 = test_f12_fix(test_code_1)
print(f"修復次數: {n1}")
print("修復後代碼:")
print(fixed_1)

# 驗證語法
try:
    compile(fixed_1, '<test1>', 'exec')
    print("✅ 語法正確！")
except SyntaxError as e:
    print(f"❌ 語法錯誤: {e}")

# 測試 2
print("\n" + "="*80)
print("【測試 2】多行 return 字典")
fixed_2, n2 = test_f12_fix(test_code_2)
print(f"修復次數: {n2}")
print("修復後代碼:")
print(fixed_2)

try:
    compile(fixed_2, '<test2>', 'exec')
    print("✅ 語法正確！")
except SyntaxError as e:
    print(f"❌ 語法錯誤: {e}")

# 測試 3
print("\n" + "="*80)
print("【測試 3】實際失敗案例（之前會破壞語法）")
fixed_3, n3 = test_f12_fix(test_code_3)
print(f"修復次數: {n3}")
print("修復後代碼:")
print(fixed_3)

try:
    compile(fixed_3, '<test3>', 'exec')
    print("✅ 語法正確！")
except SyntaxError as e:
    print(f"❌ 語法錯誤: {e}")

print("\n" + "="*80)
print(f"🎉 測試完成！共修復 {n1 + n2 + n3} 處")
print("="*80)
