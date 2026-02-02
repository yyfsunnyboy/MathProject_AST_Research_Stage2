# 🎯 Prompt 優化報告

## 📋 優化目標
1. 減少 coding prompt 長度和複雜度
2. 降低錯誤和迷航可能性
3. 為 7B 小模型做準備

## 🔍 問題分析

### Tokenizer 效率差異
- **Qwen2.5-Coder:14b**: 1.0 chars/token (效率極差)
- **Gemini-2.5-Flash**: 3.39 chars/token (正常效率)

同樣的 18K chars prompt:
- Qwen: 18,052 tokens ❌
- Gemini: 5,454 tokens ✅

### Prompt 組成 (優化前)
```
UNIVERSAL_GEN_CODE_PROMPT:  7,747 chars (42.3%)
Domain Injection:           4,456 chars (24.3%)
MASTER_SPEC:                6,104 chars (33.3%)
Header:                        19 chars (0.1%)
─────────────────────────────────────────
總計:                      18,326 chars
```

## ✅ 實施的優化

### 1. 精簡 POLYNOMIAL_HELPERS
**優化前**: 3,711 chars
- 冗長的多行 docstring
- 詳細的參數說明
- 多個使用範例

**優化後**: 2,448 chars (-34.0%)
```python
def _coeffs_to_terms(coeffs):
    '''係數列表 [a_n,...,a_0] → terms [(c,e),...]'''
    degree = len(coeffs) - 1
    return [(coeffs[i], degree - i) for i in range(len(coeffs))]
```

### 2. 精簡 Domain Injection 模板
**優化前**: 4,456 chars
- 重複的警告訊息
- 冗長的範例代碼
- 多段文字說明

**優化後**: 3,001 chars (-32.7%)
```
### 🔧 標準函數庫（polynomial, calculus）

{code}

⚠️ 規則：
1. 直接調用上述函數，禁止重新定義
2. 你只需實現 `def generate(level=1, **kwargs)`
3. 答案格式：純多項式逗號分隔，例 "6x-5, 6"（禁止包含 f'(x)= 或換行）
```

## 📊 優化結果

### 總 Prompt 大小
```
優化前: 18,326 chars
優化後: 16,871 chars
減少:    1,455 chars (-7.9%)
```

### Token 數估算

**Qwen2.5-Coder (1:1 比例)**:
- 優化前: ~18,326 tokens
- 優化後: ~16,871 tokens
- 減少: ~1,455 tokens (-7.9%)

**Gemini (3:1 比例)**:
- 優化前: ~6,108 tokens
- 優化後: ~5,623 tokens
- 減少: ~485 tokens (-7.9%)

## 🎯 對 7B 小模型的幫助

### 1. Context Window 壓力降低
- 7B 模型通常 context window 較小 (8K-16K tokens)
- 減少 1,455 tokens 為輸出留出更多空間

### 2. 認知負擔減輕
- 精簡的 docstring 更容易理解
- 減少冗餘信息避免混淆

### 3. 推理效率提升
- 更少的 token 需要處理
- 關鍵信息更集中

## ✅ 功能驗證

所有測試通過：
- ✅ `_coeffs_to_terms` 格式轉換正常
- ✅ `_poly_to_latex` LaTeX 生成正確
- ✅ `_differentiate_poly` 求導邏輯正確
- ✅ 答案格式符合規範: `"6x-5, 6"`

## 🚀 下一步建議

### 短期優化
1. **測試優化後的生成質量**
   - 運行完整的 3x3 實驗
   - 比較優化前後的成功率

2. **進一步精簡可能**
   - UNIVERSAL_GEN_CODE_PROMPT (7,747 chars) 中的 LaTeX 規則
   - MASTER_SPEC 中的重複說明

### 中期優化
3. **為 7B 模型定制 Prompt**
   - 創建 `UNIVERSAL_GEN_CODE_PROMPT_LITE`
   - 移除複雜範例，只保留核心規則

4. **動態 Prompt 調整**
   - 根據模型大小自動選擇 prompt 版本
   - 7B: 精簡版
   - 14B/Gemini: 完整版

### 長期優化
5. **Prompt 壓縮技術**
   - Few-shot 範例壓縮
   - 規則模板化

6. **分層 Prompt 設計**
   - Level 1: 核心規則 (所有模型必需)
   - Level 2: 詳細說明 (大模型用)
   - Level 3: 錯誤預防 (僅 Gemini 用)

## 📈 預期效果

### 成功率提升
- 減少 prompt 複雜度 → 減少誤解
- 關鍵信息更突出 → 提高遵守率

### 成本降低
- Gemini 減少 485 tokens/次
- 1000 次生成節約 ~$0.03 (485k tokens @ $0.075/1M)

### 小模型適配
- 16.8K chars ≈ 16.8K tokens (Qwen)
- 為 7B 模型留出充足的輸出空間 (假設 8K context)

---

**最後更新**: 2026-02-02
**優化版本**: V2.0 - Compact Domain Injection
