# 鷹架版 Prompt 實作日誌

**日期**: 2026-02-03  
**版本**: V2.4 - SIMPLIFIED_GEN_CODE_PROMPT (Scaffolding-Based Prompt)  
**目標**: 從 9000+ 字符的工程化 Prompt 簡化到 ~2000 字符，應用教學脚手架原則

---

## 📋 實作內容

### 1. 新增 `SIMPLIFIED_GEN_CODE_PROMPT` 常量

**位置**: `core/prompts/prompt_builder.py` (line ~150-245)

**特點**:
- ✅ 精簡化：從 9000+ 字符 → ~2000 字符（約 78% 減少）
- ✅ 核心規則：20+ → 5 條不可違反的規則
- ✅ 脚手架設計：明確的任務 → 提供的工具 → 簡潔的規則 → 成功範例
- ✅ 移除冗餘：刪除重複警告符號（🔴❌💣），只保留必要警告
- ✅ 認知負荷降低：讓 Qwen 專注核心任務，不被約束規則淹沒

**結構**:
```
【角色】K12 數學演算法工程師
【任務】實作 def generate(level=1, **kwargs)，根據 MASTER_SPEC 生成代碼
【預載工具】(list of functions)
【核心規則】(only 5 rules)
  1. 安全的迴圈設計 (shuffle+slice)
  2. LaTeX 格式 (中文與 $ 分離)
  3. 答案格式 (純結果，無符號)
  4. Domain 函數使用 (轉換→調用，不要 clean)
  5. 只輸出代碼 (無說明、無 eval)
【成功的代碼模式】(complete working example)
```

### 2. 更新 PromptBuilder.build() 方法

**改動**:

| Ablation | 舊版 | 新版 |
|----------|------|------|
| Ab1 | BARE_PROMPT_TEMPLATE | ✅ 保持不變 |
| Ab2 | UNIVERSAL_GEN_CODE_PROMPT (9000+ chars) | ⬇️ SIMPLIFIED_GEN_CODE_PROMPT (~2000 chars) |
| Ab3 | UNIVERSAL_GEN_CODE_PROMPT (9000+ chars) | ⬇️ SIMPLIFIED_GEN_CODE_PROMPT (~2000 chars) |

**代碼改動** (lines ~715-730):
```python
# 舊
prompt = UNIVERSAL_GEN_CODE_PROMPT + domain_injection + f"\n\n### MASTER_SPEC:\n{master_spec}"

# 新
prompt = SIMPLIFIED_GEN_CODE_PROMPT + domain_injection + f"\n\n### MASTER_SPEC:\n{master_spec}"
```

### 3. 更新導出列表

**位置**: `__all__` (line ~737)

**新增**:
- `BARE_PROMPT_TEMPLATE` (Ab1 專用)
- `SIMPLIFIED_GEN_CODE_PROMPT` (Ab2/Ab3 新脚手架)

---

## 🎯 教學脚手架設計原則

新 Prompt 遵循以下教學脚手架原則：

### ✅ 1. 明確的任務描述
```
只有一句話清楚說明：實作 def generate(level=1, **kwargs)
（而不是多段複雜說明）
```

### ✅ 2. 預先提供必要工具
```
列出所有可用函數，讓開發者知道「他不需要自己定義這些」
（降低認知負荷：不用擔心工具在哪裡）
```

### ✅ 3. 簡潔而不妥協的規則
```
5 條 vs 20+ 條
每條都是「不得違反的鐵律」，而不是「建議」
```

### ✅ 4. 成功的代碼範例
```
給一個完整的、可直接執行的例子
讓模型看到「成功的樣子」而不是讀文字說明
```

### ✅ 5. 最小化決策點
```
不要讓模型選擇：「LaTeX 有 3 種方式，你選一種吧」
而是：「LaTeX 只有這一種方式，遵守即可」
```

---

## 📊 預期效果

### 目標 1：提高 Ab2 代碼生成成功率
- **舊版**: Ab2 生成失敗，複雜度堆砌導致 Qwen 混淆
- **新版**: 簡化的規則應讓 Qwen 更清楚地遵守要求

### 目標 2：改進答案格式正確性
- **舊版**: 答案格式有時包含多餘的函數符號或換行
- **新版**: 清楚的答案格式規則 + 成功範例，應提高準確率

### 目標 3：降低認知負荷
- **舊版**: 模型需理解 9000+ 字符，包含多個層級的警告
- **新版**: 模型只需理解 2000 字符的核心規則 + 一個完整範例

---

## 🔧 技術細節

### SIMPLIFIED_GEN_CODE_PROMPT 的 5 條核心規則

#### Rule 1: 安全的迴圈設計
```python
✅ 使用 shuffle + slice
❌ 禁止 while True + if not in set 的無限迴圈模式
```

#### Rule 2: LaTeX 格式
```
✅ 所有數學式被 $ 包裹：f"計算 ${expr}$ 的值"
❌ 中文與 $ 不能直接相連：f"求${expr}$的"
```

#### Rule 3: 答案格式
```
✅ 純結果："6x^2-10x, 12x-10"
❌ 包含符號："f'(x) = 6x^2-10x\nf''(x) = 12x-10"
```

#### Rule 4: Domain 函數使用
```
✅ 轉換格式 → 調用函數 → 直接用
❌ 不要對 Domain 函數結果呼叫 clean_latex_output()
```

#### Rule 5: 只輸出代碼
```
✅ 代碼結束後不加任何說明
❌ 不要加 "This code..." 或其他說明文字
```

---

## 📝 測試計劃

### Phase 1: 快速驗證 (當前)
- [x] 添加 SIMPLIFIED_GEN_CODE_PROMPT 常量到 prompt_builder.py
- [x] 更新 PromptBuilder.build() 方法
- [x] 更新導出列表和文檔字符串
- [ ] 驗證 prompt_builder.py 無語法錯誤

### Phase 2: 代碼生成測試
- [ ] 測試 Ab2 使用新簡化 Prompt
- [ ] 測試 Ab3 使用新簡化 Prompt + Healer
- [ ] 比較生成代碼的質量

### Phase 3: 積分驗證
- [ ] 運行 Ab2 題目生成，檢查通過率
- [ ] 運行 Ab3 題目生成，檢查通過率
- [ ] 比較 Ab1 vs Ab2 vs Ab3 的性能

### Phase 4: 難題驗證 (聯立方程式)
- [ ] 用新 Prompt 生成聯立方程式題目
- [ ] 驗證 Ab1 是否無法生成（預期）
- [ ] 驗證 Ab3 是否能正確生成（預期）

---

## 📌 重要提醒

### 關鍵改變點
1. **Ab2 現在用簡化版本而不是複雜版本**
   - 如果 Ab2 還是失敗，問題不在 Prompt 長度，而在 Prompt 內容邏輯
   - 需要進一步調教 5 條規則的具體措辭

2. **Ab1 保持不變**
   - 完全獨立的自然語言 Prompt
   - 不使用 Domain 函數，不使用 MASTER_SPEC
   - 用作對照組的基準線

3. **Domain 函數庫仍然被注入**
   - SIMPLIFIED_GEN_CODE_PROMPT 本身不包含具體函數實現
   - Domain 函數代碼在 `domain_injection` 階段單獨注入
   - 最終 Prompt = Simplified Prompt + Domain Code + MASTER_SPEC

---

## 🗂️ 文件參考

- **新 Prompt 源檔**: `ab2_simplified_prompt_v1.txt` (參考版本)
- **正式實装**: `core/prompts/prompt_builder.py` line ~150-245
- **原舊 Prompt**: `UNIVERSAL_GEN_CODE_PROMPT` (仍保留以備回滾)
- **這個日誌**: `SCAFFOLD_PROMPT_IMPLEMENTATION_LOG.md` (當前文件)

---

## 🚀 下一步

用戶若要調教新 Prompt：
1. 修改 `SIMPLIFIED_GEN_CODE_PROMPT` 中的 5 條規則
2. 或調整「成功的代碼模式」的例子
3. 重新運行 Ab2/Ab3 測試
4. 比較生成代碼質量和通過率

如需回滾到舊版本：
1. 將 `PromptBuilder.build()` 中的 `SIMPLIFIED_GEN_CODE_PROMPT` 改回 `UNIVERSAL_GEN_CODE_PROMPT`
2. 或直接使用 BARE_PROMPT_TEMPLATE (Ab1 模式)

