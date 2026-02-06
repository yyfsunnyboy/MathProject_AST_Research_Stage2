# Ab2/Ab3 簡化版 Prompt 實作完成 ✅

## 📦 實作摘要

已根據 `ab2_simplified_prompt_v1.txt` 的簡化版本，實装 Ab2 和 Ab3 的鷹架版工程化 Prompt。

---

## 📊 Prompt 對比表

| 指標 | Ab1 (對照組) | Ab2 舊版 | Ab2 新版 (簡化) | Ab3 新版 (簡化) |
|------|--------------|---------|----------------|----------------|
| 基礎 Prompt | BARE_PROMPT_TEMPLATE | UNIVERSAL_GEN_CODE_PROMPT | SIMPLIFIED_GEN_CODE_PROMPT | SIMPLIFIED_GEN_CODE_PROMPT |
| 字符數 | ~900 | ~9000+ | ~2000 | ~2000 |
| 規則數 | 5 條 | 20+ 條 | 5 條 | 5 條 |
| Domain 函數 | ❌ 不使用 | ✅ 注入 | ✅ 注入 | ✅ 注入 |
| MASTER_SPEC | ❌ 不使用 | ✅ 注入 | ✅ 注入 | ✅ 注入 |
| 代碼修復 (Healer) | ❌ 無 | ❌ 無 | ❌ 無 | ✅ 啟用 |
| 預期成功率 | 100% | 0% (失敗) | ? (待測) | ? (待測) |

---

## 🔄 改動清單

### ✅ 1. 新增 SIMPLIFIED_GEN_CODE_PROMPT 常量
**文件**: `core/prompts/prompt_builder.py`  
**位置**: Line ~150-245 (新增區段)  
**內容**: 完整的簡化版工程化 Prompt (~2000 字符)

**結構**:
```
【角色】K12 數學演算法工程師
【任務】實作 def generate()...
【預載工具】(function list)
【核心規則】(5 rules only)
  1. 安全迴圈
  2. LaTeX 格式
  3. 答案格式
  4. Domain 函數
  5. 只輸出代碼
【成功的代碼模式】(working example)
```

### ✅ 2. 更新 PromptBuilder.build() 方法

**改動前** (Line 715-730):
```python
elif ablation_id == 2:
    prompt = UNIVERSAL_GEN_CODE_PROMPT + domain_injection + ...
else:
    prompt = UNIVERSAL_GEN_CODE_PROMPT + domain_injection + ...
```

**改動後**:
```python
elif ablation_id == 2:
    prompt = SIMPLIFIED_GEN_CODE_PROMPT + domain_injection + ...
    logger.info(f"Prompt Ab2 - SIMPLIFIED_GEN_CODE_PROMPT ... (鷹架版)")
else:
    prompt = SIMPLIFIED_GEN_CODE_PROMPT + domain_injection + ...
    logger.info(f"Prompt Ab{ablation_id} - SIMPLIFIED_GEN_CODE_PROMPT ... (鷹架版)")
```

### ✅ 3. 更新 PromptBuilder 的 docstring
```python
# 舊
Ab2: UNIVERSAL_GEN_CODE_PROMPT + MASTER_SPEC
Ab3: UNIVERSAL_GEN_CODE_PROMPT + MASTER_SPEC (默認)

# 新
Ab2: SIMPLIFIED_GEN_CODE_PROMPT + MASTER_SPEC (工程化鷹架版，~2000 字符)
Ab3: SIMPLIFIED_GEN_CODE_PROMPT + MASTER_SPEC + Healer (鷹架版 + AST 修復)
```

### ✅ 4. 更新 __all__ 導出列表
```python
# 新增
'BARE_PROMPT_TEMPLATE',
'SIMPLIFIED_GEN_CODE_PROMPT',
```

---

## 🎓 教學脚手架設計理念

新 Prompt 遵循以下原則（而不是规則堆砌）：

### 原則 1️⃣ : 明確的任務
- ✅ 一句話清楚說什麼：實作 `def generate(level=1, **kwargs)`
- ❌ 不是多段複雜說明

### 原則 2️⃣ : 預先提供工具
- ✅ 列出所有可用函數，讓模型知道「不用自己定義這些」
- ❌ 不是讓模型猜測工具在哪裡

### 原則 3️⃣ : 簡潔而不妥協的規則
- ✅ 5 條鐵律 vs 20+ 條雜亂建議
- ✅ 每條都是「必須遵守」而不是「建議參考」

### 原則 4️⃣ : 成功的代碼範例
- ✅ 給完整的、可直接執行的例子
- ❌ 不是讀文字說明然後自己推理

### 原則 5️⃣ : 最小化決策點
- ✅ LaTeX 只有一種方式：f"計算 ${expr}$ 的值"
- ❌ 不是「選擇你喜歡的 3 種方式之一」

---

## 🧪 5 條核心規則詳解

### Rule 1: 安全的迴圈設計
```python
✅ 使用 shuffle + slice
available = list(range(n))
random.shuffle(available)
selected = available[:k]  # O(1) 保證成功

❌ 禁止 while True + if not in set
while True:
    x = random.randint(0, n)
    if x not in selected:  # ⚠️ 無限迴圈風險
        break
```

### Rule 2: LaTeX 格式
```
✅ 所有數學式被 $ 包裹且中文分離
f"計算 ${expr}$ 的值"

❌ 中文與 $ 直接相連
f"求${expr}$的因式分解"
```

### Rule 3: 答案格式
```
✅ 純結果，逗號分隔
"6x^2-10x, 12x-10"

❌ 包含符號或換行
"f'(x) = 6x^2-10x\nf''(x) = 12x-10"
```

### Rule 4: Domain 函數使用
```python
✅ 轉換格式 → 調用 → 直接用
terms = _coeffs_to_terms(coeffs)
latex = _poly_to_latex(terms)

❌ 對結果再次呼叫 clean_latex_output()
clean_latex_output(latex)  # 多此一舉
```

### Rule 5: 只輸出代碼
```
✅ 代碼結束就結束
[code ends here]

❌ 代碼後跟說明
[code]
This code implements...
```

---

## 📈 預期效果與測試

### Phase 1 ✅ (已完成)
- [x] 創建簡化版本 Prompt
- [x] 實装到 prompt_builder.py
- [x] 驗證語法無誤

### Phase 2 ⏳ (待測)
- [ ] Ab2 代碼生成測試 (使用新簡化 Prompt)
- [ ] Ab3 代碼生成測試 (新簡化 Prompt + Healer)
- [ ] 比較生成代碼質量

### Phase 3 ⏳ (待測)
- [ ] 積分驗證：Ab2 通過率
- [ ] 積分驗證：Ab3 通過率
- [ ] 與 Ab1 對比

### Phase 4 ⏳ (可選)
- [ ] 用難題 (聯立方程式) 驗證架構價值
- [ ] Ab1 應該失敗，Ab3 應該成功

---

## 🔄 回滾方案

如果簡化版本效果不理想，可以：

### 方案 A: 回到舊版本
```python
# 在 PromptBuilder.build() 中改為
prompt = UNIVERSAL_GEN_CODE_PROMPT + domain_injection + ...
```

### 方案 B: 微調簡化版本
修改 `SIMPLIFIED_GEN_CODE_PROMPT` 中的任何部分，重新測試

### 方案 C: 混合版本
保留簡化版本的結構，添加特定場景的補充說明

---

## 📁 相關文件

| 文件 | 說明 |
|-----|------|
| `ab2_simplified_prompt_v1.txt` | 簡化版本的參考源檔（調教版） |
| `core/prompts/prompt_builder.py` | 正式實装的位置 |
| `SCAFFOLD_PROMPT_IMPLEMENTATION_LOG.md` | 詳細實装日誌 |
| `SIMPLIFIED_AB2_AB3_PROMPT_CHANGES.md` | 當前文件（快速參考） |

---

## ✨ 核心優勢

### 1️⃣ 認知負荷降低
- 9000+ → 2000 字符 (約 78% 減少)
- 20+ 規則 → 5 條鐵律
- 模型可專注核心任務

### 2️⃣ 清楚的成功標準
- 提供完整的、可直接執行的代碼範例
- 不是讀規則然後自己推理

### 3️⃣ 教學脚手架設計
- 遵循已驗證的教學原則
- 不是規則堆砌，而是有邏輯的脚手架

### 4️⃣ 對齐 Ab1 的簡潔性
- Ab1 成功的原因：簡潔而清楚
- 新 Ab2/Ab3：保持簡潔，加上必要的工程化指導

---

## 📝 下一步

1. **運行測試**: 執行 Ab2 和 Ab3 題目生成
2. **比較結果**: 與舊版本對比質量
3. **分析日誌**: 查看 logger 輸出確認使用的是新 Prompt
4. **迭代調教**: 若需要，修改 5 條規則或範例代碼
5. **難題驗證**: 用聯立方程式驗證架構價值

