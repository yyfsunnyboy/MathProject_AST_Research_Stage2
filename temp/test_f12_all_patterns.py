"""
全面測試 F.12 Healer 的所有 3 種模式
"""
import re

def test_all_f12_patterns(code):
    """測試所有 3 種 F.12 修復模式（最新版本）"""
    
    # 模式 1: question_text = clean_latex_output(q_str)
    code, n1 = re.subn(
        r"question_text\s*=\s*clean_latex_output\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\)",
        r"question_text = \1  # [Auto-Fix F.12] Domain 函數已格式化 LaTeX，移除 clean_latex_output",
        code
    )
    
    # 模式 2: q = clean_latex_output(q) - 已禁用（太危險）
    n2 = 0
    
    # 模式 3: return {..., 'question_text': clean_latex_output(q), ...}
    code, n3 = re.subn(
        r"(['\"]question_text['\"])\s*:\s*clean_latex_output\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\)",
        r"\1: \2",  # 不加註解
        code
    )
    
    return code, (n1, n2, n3)

# 測試案例 1: 模式 1 - 獨立賦值語句
test1 = """
def generate():
    q_str = "問題"
    question_text = clean_latex_output(q_str)
    return {'question_text': question_text}
"""

# 測試案例 2: 模式 2 - 自我覆蓋
test2 = """
def generate():
    q = "原始問題"
    q = clean_latex_output(q)
    return q
"""

# 測試案例 3: 組合測試（可能被模式 2 誤刪）
test3 = """
def generate():
    q = build_question()
    a = clean_latex_output(a)
    return {'question_text': q, 'answer': a}
"""

# 測試案例 4: return 字典內的模式 3
test4 = """
def generate():
    return {'question_text': clean_latex_output(q), 'answer': ans}
"""

print("="*80)
print("F.12 Healer 全模式安全性測試")
print("="*80)

for i, test_code in enumerate([test1, test2, test3, test4], 1):
    print(f"\n【測試 {i}】")
    print("原始代碼:", test_code.strip()[:80] + "...")
    
    fixed, (n1, n2, n3) = test_all_f12_patterns(test_code)
    print(f"修復: 模式1={n1}, 模式2={n2}, 模式3={n3}")
    
    # 語法檢查
    try:
        compile(fixed, f'<test{i}>', 'exec')
        print("✅ 語法正確")
        if n1 + n2 + n3 > 0:
            print("修復後代碼:")
            print(fixed)
    except SyntaxError as e:
        print(f"❌ 語法錯誤: {e}")
        print("修復後代碼:")
        print(fixed)

print("\n" + "="*80)
print("🎯 測試完成！")
print("="*80)
