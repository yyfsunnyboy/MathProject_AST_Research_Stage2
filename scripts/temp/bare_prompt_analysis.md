# 🔴 Bare Prompt 分析报告

## 实验发现：Bare Prompt = Full-Healing Prompt！

### 关键问题
根据代码审查 ([code_generator.py](../core/code_generator.py))，发现：

**所有 ablation_id (1/2/3) 都使用相同的 prompt！**

```python
# Line 1921
def auto_generate_skill_code(skill_id, queue=None, **kwargs):
    ablation_id = kwargs.get('ablation_id', 3)
    
    # 所有实验组都用同一个 prompt！
    prompt = UNIVERSAL_GEN_CODE_PROMPT + f"\n\n### MASTER_SPEC:\n{spec}"
```

---

## UNIVERSAL_GEN_CODE_PROMPT 内容

### 完整 Prompt（所有 ablation_id 共享）

```
【角色】K12 數學演算法工程師。
【任務】實作 `def generate(level=1, **kwargs)`，根據 MASTER_SPEC 產出完整的 Python 代碼。
【限制】僅輸出代碼，無 Markdown/說明。**嚴禁 eval/exec/safe_eval**。

🔴 **最高優先級：MASTER_SPEC 是唯一權威來源**
- 你收到的 MASTER_SPEC 包含完整的題型定義、複雜度要求和實現檢查清單
- **必須逐項實現 MASTER_SPEC 中的所有要求**

【預載工具 (直接使用)】
- random, math, re, ast, operator, Fraction
- fmt_num(n), to_latex(n), clean_latex_output(q)
- check(u, c)
- op_latex = {'+': '+', '-': '-', '*': '\\times', '/': '\\div'}

【生成管線標準】
1. 變數生成（嚴格遵守 MASTER_SPEC）
2. 運算（Python 直接計算，嚴禁 eval）
3. 運算順序與括號
4. 題幹格式化（LaTeX + 中文處理）
5. 答案格式化
6. 回傳標準格式

... (省略詳細規則，共 194 行)
```

### Prompt 特點

✅ **已包含的高級指導**：
- 完整的 LaTeX 格式化規則
- fmt_num(), op_latex, clean_latex_output() 使用說明
- 中文與數學式分離規則
- 運算順序與括號匹配規則
- 防呆檢查清單

❌ **不是 Bare Prompt**：
- 包含大量工程化指導（194 行）
- 明確告知可用工具函數
- 詳細的格式化要求
- 錯誤範例與正確範例

---

## Healer 執行時機

**所有 Healer 都在 AI 生成後執行**（與 ablation_id 無關）：

```python
# Line 1956-2300：Healer Pipeline
# Step A: 移除 Markdown
clean_code, n = COMPILED_PATTERNS['markdown_blocks'].subn('', raw_output)

# Step B: Garbage Cleaner
clean_code = clean_code.replace('\xa0', ' ')

# Step C: Import Cleaner
clean_code, import_removed = clean_redundant_imports(clean_code)

# Step D: 包裹函式
if "def generate" not in clean_code:
    clean_code = "def generate(level=1, **kwargs):\n" + ...

# Step E: 主動邏輯修復（refine_ai_code）
clean_code, healer_fixes = refine_ai_code(clean_code)

# Step E.5: 禁止函數移除器
# Step E.6: 混合數字串修復
# Step E.7: LaTeX 格式修復
# Step E.8: 變數名稱對齊
# Step E.9: Return 語句清洗
# Step F.5: eval→safe_eval 轉換

# Step G: AST Healer
tree = ast.parse(clean_code)
healer = ASTHealer()
tree = healer.visit(tree)
ast_fixes = healer.fixes
```

---

## ablation_settings 表的真相

### 數據庫結構

```sql
CREATE TABLE ablation_settings (
    id INTEGER PRIMARY KEY,
    name TEXT,
    use_regex BOOLEAN,
    use_ast BOOLEAN,
    description TEXT
);

-- 數據
(1, 'Bare', 0, 0, '對照組：無任何修復機制')
(2, 'Regex_Only', 1, 0, '實驗組 A：僅開啟正規表達式修復')
(3, 'Full_Healing', 1, 1, '實驗組 B：開啟 Regex + AST 完整自癒機制')
```

### 問題：代碼從未讀取此表！

```bash
# 搜索結果
$ grep -r "ablation_settings" core/code_generator.py
# 0 matches

$ grep -r "use_regex" core/code_generator.py
# 0 matches

$ grep -r "use_ast" core/code_generator.py
# 0 matches
```

**結論**：`ablation_settings` 表**從未被使用**！

---

## 實驗設計缺陷

### 原始假設

| Ablation ID | 名稱 | Prompt | Healer |
|------------|------|--------|--------|
| 1 | Bare | 簡單指令 | 無 |
| 2 | Regex_Only | 工程化 | Regex |
| 3 | Full_Healing | 工程化 | Regex+AST |

### 實際情況

| Ablation ID | 名稱 | Prompt | Healer |
|------------|------|--------|--------|
| 1 | Bare | **UNIVERSAL (194行)** | **Full Pipeline** |
| 2 | Regex_Only | **UNIVERSAL (194行)** | **Full Pipeline** |
| 3 | Full_Healing | **UNIVERSAL (194行)** | **Full Pipeline** |

**所有組別完全相同！**

---

## 為什麼簡單技能 100% 成功？

### 答案：Prompt 已經是 Full-Healing 級別

```python
【預載工具 (直接使用)】
- fmt_num(n), to_latex(n), clean_latex_output(q)
- op_latex = {'+': '+', '-': '-', '*': '\\times', '/': '\\div'}
```

AI 被明確告知：
1. 使用 `op_latex` 字典
2. 呼叫 `clean_latex_output(q)`
3. 遵守 LaTeX 格式規則

**所以**：
- Bare (ablation_id=1) 的 AI 也能正確使用這些工具
- Healer 幾乎無事可做（0 fixes）
- 成功率 100%，但不是因為 AI 強，而是 Prompt 已經是工程化的了

---

## 科學性問題

### 實驗設計的致命缺陷

1. **無真正的 Bare 對照組**
   - 所有組別都用工程化 Prompt
   - 無法證明 Prompt 工程化的價值
   
2. **Healer 形同虛設**
   - Prompt 已教會 AI 如何正確生成
   - Healer 只是"保險絲"而非"核心價值"
   
3. **ablation_settings 表無效**
   - 設計了開關但從未使用
   - 實驗標籤 (Bare/Regex/Full) 不符實際

---

## 如何證明 Healer 價值？

### 方案 A：修復實驗設計

創建真正的 Bare Prompt：

```python
BARE_PROMPT = """
你是 Python 程式設計師。請根據 MASTER_SPEC 生成數學題目。

要求：
- 實作 def generate(level=1, **kwargs) 函數
- 回傳字典：{'question_text': 題目, 'answer': 答案, 'mode': 1}
- 題目使用 LaTeX 格式（用 $ $ 包裹）

請直接輸出代碼。

### MASTER_SPEC:
{spec}
"""
```

**預期結果**：
- Bare: 成功率 20-40%（缺少工具指導）
- Full-Healing: 成功率 80-100%（Healer 修復 AI 錯誤）

### 方案 B：測試複雜技能

保持現有 Prompt，但測試：
- 分數四則運算
- 一元一次方程式
- 因式分解

**預期結果**：
- 簡單技能：Healer 0-1 fixes
- 複雜技能：Healer 5-10 fixes
- **證明 Healer 對複雜任務的價值**

---

## 建議的修正行動

### 1. 立即行動：創建真正的 Bare Prompt

```python
# 新增到 code_generator.py
BARE_MINIMAL_PROMPT = """
根據以下 MASTER_SPEC 生成 Python 函數：

{spec}

實作要求：
- 函數名：generate(level=1, **kwargs)
- 回傳格式：{'question_text': q, 'answer': a, 'mode': 1}

直接輸出 Python 代碼。
"""

def auto_generate_skill_code(skill_id, queue=None, **kwargs):
    ablation_id = kwargs.get('ablation_id', 3)
    
    # 根據 ablation_id 選擇 prompt
    if ablation_id == 1:
        base_prompt = BARE_MINIMAL_PROMPT
    else:
        base_prompt = UNIVERSAL_GEN_CODE_PROMPT
    
    prompt = base_prompt.format(spec=spec)
```

### 2. 實作 Healer 開關

```python
from models import AblationSetting

def auto_generate_skill_code(skill_id, queue=None, **kwargs):
    ablation_id = kwargs.get('ablation_id', 3)
    
    # 讀取 ablation 設定
    config = AblationSetting.query.get(ablation_id)
    use_regex = config.use_regex if config else True
    use_ast = config.use_ast if config else True
    
    # 條件執行 Healer
    if use_regex:
        clean_code, healer_fixes = refine_ai_code(clean_code)
    
    if use_ast:
        tree = ast.parse(clean_code)
        healer = ASTHealer()
        tree = healer.visit(tree)
```

### 3. 重新執行實驗

```bash
python scripts/ablation_bare_vs_healer.py --use-true-bare
```

**預期對比**：
- True Bare: 30-50% 成功率
- Full-Healing: 90-100% 成功率
- **差距顯著，證明 Healer 價值**

---

## 總結

### 當前狀態
- ❌ Bare Prompt 不是真正的 Bare
- ❌ Healer 價值無法證明
- ❌ 實驗設計有嚴重缺陷

### 修正後狀態
- ✅ 真正的 Bare vs Engineered 對比
- ✅ Healer 開關實際生效
- ✅ 科學性與說服力提升

### 對研究的影響
**好消息**：問題可修復，且修復後更有說服力！
- 簡單技能：證明 Prompt 工程化的價值
- 複雜技能：證明 Healer 的價值
- 組合：證明 Architect-Coder-Healer 全流程的必要性
