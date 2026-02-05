"""測試 MASTER_SPEC 淨化器效果"""
from core.prompts.prompt_builder import PromptBuilder

# 測試用的 MASTER_SPEC（包含會被移除的欄位）
spec = """
domain: algebra.calculus.derivatives

entities:
  - polynomial_terms: list of tuple
    constraints:
      - coefficient: integer, 範圍 -10~10

operators:
  - derivative: 導數運算

constraints:
  - 可計算性: 所有係數必須是整數

templates:
  - name: polynomial_multiple_derivatives
    
    complexity_requirements: |
      - 原始多項式必須包含至少 3 個非零項
      - 原始多項式最高次數必須介於 3 到 5 之間
      
    variables:
      - num_terms: 整數，範圍 3~5
      - max_degree: 整數，範圍 3~5
    
    construction: |
      1. 生成原始多項式項：
          a. 隨機確定 max_degree (3~5)
          b. 生成 num_terms 個唯一指數
          c. 為每個指數生成係數 (-10~10)
      2. 生成請求的導數階數
      3. 計算每個導數
      4. 驗證結果
    
    implementation_checklist: |
      - [ ] 必須有外層 while True: 迴圈
      - [ ] 所有驗證邏輯都在 while True 內
      - [ ] 格式化和 return 都在 while True 外
    
    formatting:
      question_display: |
        使用 _poly_to_latex() 函數將多項式轉換為 LaTeX
      answer_display: |
        使用 _poly_to_text() 函數生成答案

diversity:
  - 變異點 1: 原始多項式的項數 (3~5)
  - 變異點 2: 原始多項式的最高次數 (3~5)
"""

print(f"📊 原始 MASTER_SPEC: {len(spec)} 字元\n")

# 測試淨化
clean_spec = PromptBuilder._clean_master_spec(spec)
print(f"✅ 淨化後 MASTER_SPEC: {len(clean_spec)} 字元")
print(f"📉 減少: {len(spec) - len(clean_spec)} 字元 ({(1 - len(clean_spec)/len(spec))*100:.1f}%)\n")

# 檢查是否移除了關鍵詞
removed_keys = ['construction:', 'implementation_checklist:', 'formatting:', 'variables:']
print("🔍 檢查移除狀態:")
for key in removed_keys:
    in_original = key in spec
    in_cleaned = key in clean_spec
    status = "❌ 已移除" if in_original and not in_cleaned else ("⚠️ 未移除" if in_cleaned else "✅ 原本就沒有")
    print(f"  {key:30s} {status}")

print("\n📝 淨化後的 MASTER_SPEC 完整內容:")
print("=" * 70)
print(clean_spec)


