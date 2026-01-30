# ⚠️⚠️⚠️ 暫時檔案 可刪除! ⚠️⚠️⚠️
# Code Generator 重構計畫 - V2.0
# 創建日期: 2026-01-30
# 目標: 將 3008 行的 code_generator.py 拆分成模組化架構

## 一、重構架構總覽

```
core/
├── code_generator.py          # 主控器（保留舊介面）
├── utils/                     # ✅ 已完成
│   ├── __init__.py
│   ├── math_utils.py          # 18 個數學工具函數
│   ├── latex_utils.py         # LaTeX 清洗器
│   └── file_utils.py          # 檔案系統工具
├── healers/                   # ✅ 已完成
│   ├── __init__.py
│   ├── regex_healer.py        # F.1-F.12 修復規則
│   └── ast_healer.py          # AST 層級修復
├── validators/                # ✅ 已完成
│   ├── __init__.py
│   ├── syntax_validator.py    # Python 語法驗證
│   └── dynamic_sampler.py     # 動態採樣驗證
└── prompts/                   # ✅ 已完成
    ├── __init__.py
    └── prompt_builder.py      # Prompt 構建器
```

## 二、向後相容性保證

### 呼叫端約束（絕對不可改）

**1. scripts/sync_skills_files.py (line 233)**
```python
is_ok, msg, metrics = auto_generate_skill_code(
    skill_id, queue=None, 
    ablation_id=ablation_id, 
    model_size_class=model_size_class,
    prompt_level=prompt_level
)
```

**2. core/routes/admin.py (line 519)**
```python
result = auto_generate_skill_code(skill_id, queue=None)
```

**3. core/textbook_processor.py (line 197)**
```python
success, msg, _ = auto_generate_skill_code(skill_id, queue)
```

### 函數簽名（必須保持）
```python
def auto_generate_skill_code(skill_id, queue=None, **kwargs):
    """
    Args:
        skill_id: str - 技能 ID
        queue: Queue - 可選的進度回報佇列
        **kwargs: 其他參數（ablation_id, model_size_class, prompt_level）
    
    Returns:
        tuple: (bool, str, dict)
            - is_ok: 是否成功
            - message: 錯誤訊息或成功訊息
            - metrics: 生成指標（max_heals, heal_count 等）
    """
    pass
```

## 三、已完成模組詳解

### 3.1 core/utils/ - 工具函數集合

#### math_utils.py (18 個函數)
**基礎工具**:
- `safe_choice(lst)` - 安全隨機選擇
- `to_latex(num)` - 轉換為 LaTeX 格式
- `fmt_num(num, force_decimal=False)` - 格式化數字
- `safe_eval(expr)` - 安全執行數學運算式

**數論工具**:
- `is_prime(n)` - 判斷質數
- `gcd(a, b)` - 最大公因數
- `lcm(a, b)` - 最小公倍數
- `get_factors(n)` - 獲取因數列表

**跨領域工具**:
- `clamp_fraction(a, b, max_val=10)` - 限制分數範圍
- `safe_pow(base, exp, max_exp=10)` - 安全指數運算
- `factorial_bounded(n, max_n=20)` - 有界階乘
- `nCr(n, r)` - 組合數
- `nPr(n, r)` - 排列數

**進階工具**:
- `rational_gauss_solve(A, b)` - 有理數高斯消去法
- `normalize_angle(deg)` - 角度正規化
- `fmt_set(s)` - 集合格式化
- `fmt_interval(a, b, left_open=False, right_open=False)` - 區間格式化
- `fmt_vec(v)` - 向量格式化

**驗證函數**:
- `check()` - 驗證函數（用於測試）

#### latex_utils.py (1 個函數)
- `clean_latex_output(text)` - 清洗 LaTeX 輸出（移除多餘空格、標準化分隔符）

#### file_utils.py (3 個函數)
- `get_base_root()` - 取得專案根目錄
- `path_in_root(*parts)` - 構建相對路徑
- `ensure_dir(path)` - 確保目錄存在

---

### 3.2 core/healers/ - 修復引擎

#### regex_healer.py
**類別**: `RegexHealer`

**方法**:
- `heal(code_str) -> (str, int)`
  - 執行 F.1-F.12 修復規則
  - 返回修復後的代碼和修復次數
  - **臨時實現**: 調用原 `refine_ai_code()` 保證功能

**TODO**: 將 F.1-F.12 規則拆分成獨立方法
```python
def _fix_import_order(self, code): pass
def _fix_undefined_variables(self, code): pass
def _fix_syntax_errors(self, code): pass
# ... F.4-F.12
```

#### ast_healer.py
**類別**: `ASTHealer`

**方法**:
- `heal(code_str) -> (str, int)`
  - AST 層級修復（變數作用域、未定義變數等）
  - 返回修復後的代碼和修復次數
  - **臨時實現**: 調用原 `fix_code_via_ast()` 保證功能

---

### 3.3 core/validators/ - 驗證引擎

#### syntax_validator.py
**類別**: `SyntaxValidator`

**方法**:
- `validate(code_str) -> (bool, str)`
  - 驗證 Python 語法是否正確
  - 返回 (是否通過, 錯誤訊息)
  - **臨時實現**: 調用原 `validate_python_code()`

#### dynamic_sampler.py
**類別**: `DynamicSampler`

**初始化**:
- `__init__(iterations=3)`

**方法**:
- `validate(code_str, iterations=None) -> (bool, str)`
  - 執行動態採樣驗證（執行代碼並檢查輸出）
  - 檢查 `generate()` 函數存在性
  - 驗證返回值格式（dict, question_text, answer）
  - 執行多次採樣確保穩定性
  - 返回 (是否通過, 錯誤訊息)

---

### 3.4 core/prompts/ - Prompt 構建器

#### prompt_builder.py
**類別**: `PromptBuilder`

**方法**:
- `build(skill_id, **kwargs) -> str`
  - 構建完整 Prompt
  - **臨時實現**: 調用原 `get_dynamic_skeleton(skill_id)`

**TODO**: 實現以下方法
```python
def _build_bare_prompt(self, skill_id): pass
def _build_engineered_prompt(self, skill_id): pass
def _build_full_prompt(self, skill_id): pass
```

---

## 四、重構主控器計畫

### 4.1 code_generator.py 重構策略

**保留部分（向後相容）**:
```python
# 保留原函數簽名
def auto_generate_skill_code(skill_id, queue=None, **kwargs):
    """
    主要入口，保持向後相容
    """
    # 初始化模組
    from core.utils import safe_choice, to_latex
    from core.healers import RegexHealer, ASTHealer
    from core.validators import SyntaxValidator, DynamicSampler
    from core.prompts import PromptBuilder
    
    # 使用新模組重構內部邏輯
    prompt = PromptBuilder.build(skill_id, **kwargs)
    # ... 其他邏輯
    
    return is_ok, message, metrics
```

**移除部分（已搬移到子模組）**:
- ❌ `safe_choice`, `to_latex`, `fmt_num` 等工具函數 → utils/
- ❌ `refine_ai_code`, `fix_code_via_ast` → healers/
- ❌ `validate_python_code` → validators/
- ❌ `get_dynamic_skeleton` → prompts/

**重構後行數估計**:
- 原始: 3008 行
- 重構後: ~800-1000 行（主控邏輯 + 必要的輔助函數）
- 減少: ~2000-2200 行（67-73% 減少）

---

## 五、測試結果

### 測試框架: temp/test_backward_compatibility.py

**測試項目** (6/6 通過):
1. ✅ 基礎導入測試 - 確保 `auto_generate_skill_code` 可導入
2. ✅ 函數簽名測試 - 確保參數列表正確 (`skill_id, queue, kwargs`)
3. ✅ Utils 模組測試 - 確保工具函數可導入
4. ✅ Healers 模組測試 - 確保修復引擎可實例化
5. ✅ Validators 模組測試 - 確保驗證器可實例化
6. ✅ Prompts 模組測試 - 確保 Prompt 構建器可導入

**最新測試輸出**:
```
============================================================
測試結果: 6/6 通過
🎉 所有測試通過！
============================================================
```

---

## 六、進度追蹤

### 已完成（08:00-12:00，4 小時）
- ✅ 建立目錄結構
- ✅ 建立 Git 分支：`refactor/modular-code-generator`
- ✅ 創建測試框架
- ✅ 完成 utils/ 模組（3 個檔案，24 個函數）
- ✅ 完成 healers/ 模組（2 個檔案）
- ✅ 完成 validators/ 模組（2 個檔案）
- ✅ 完成 prompts/ 模組（1 個檔案）
- ✅ 測試通過：6/6 ✅

### 進度統計
```
完成模組: 4/4 (utils, healers, validators, prompts)
完成檔案: 12/12
預估進度: 60%
耗時: 4 小時 / 10 小時
```

### 待完成（13:00-18:00，5 小時）
- [ ] 重寫 code_generator.py 主控器
- [ ] 完整回歸測試
- [ ] 實際 skill 生成測試（執行 `auto_generate_skill_code('M2300')` 等）
- [ ] Git 提交
- [ ] 更新文檔

---

## 七、關鍵注意事項

### 1. 向後相容性（最高優先）
- ✅ **絕對不可改變**：`auto_generate_skill_code(skill_id, queue=None, **kwargs)` 簽名
- ✅ **絕對不可改變**：返回值格式 `(bool, str, dict)`
- ✅ **測試驗證**：6/6 測試通過

### 2. 臨時實現策略
- ✅ **Healers**: 臨時調用原 `refine_ai_code()` 和 `fix_code_via_ast()`
- ✅ **Validators**: 臨時調用原 `validate_python_code()`
- ✅ **Prompts**: 臨時調用原 `get_dynamic_skeleton()`
- **優點**: 保證功能不破壞，後續可逐步重構細節

### 3. 架構規範遵循
- ✅ UTF-8 標頭
- ✅ 多行 docstring（模組名稱、功能說明、版本、日期、維護團隊）
- ✅ 類別：PascalCase
- ✅ 函數：snake_case
- ✅ 使用 logger 而非 print

### 4. 暫時檔案管理
- ✅ 所有測試檔案放 temp/
- ✅ 標註：`# ⚠️⚠️⚠️ 暫時檔案 可刪除! ⚠️⚠️⚠️`

---

## 八、下一步執行計畫

### 13:00-14:30（1.5 小時）- 重寫主控器
1. 備份原 code_generator.py
2. 重構主控器：
   - 保留 `auto_generate_skill_code()` 函數
   - 使用新模組重構內部邏輯
   - 移除已搬移到子模組的代碼
3. 確保所有 import 正確

### 14:30-16:00（1.5 小時）- 完整測試
1. 執行向後相容性測試
2. 實際 skill 生成測試：
   ```python
   auto_generate_skill_code('M2300', queue=None)
   auto_generate_skill_code('M2301', queue=None, ablation_id='Ab1')
   ```
3. 回歸測試（確保所有舊功能正常）

### 16:00-17:30（1.5 小時）- 驗證與修復
1. 執行完整的測試套件
2. 修復發現的問題
3. 性能測試（確保重構未降低性能）

### 17:30-18:00（0.5 小時）- 提交與文檔
1. Git commit
2. 更新專案速查.md
3. 創建重構報告

---

## 九、風險與應對

### 風險 1: 主控器重構破壞功能
- **應對**: 分步測試，每次改動立即驗證
- **備份**: 保留原 code_generator.py 備份

### 風險 2: 性能降低
- **應對**: 使用臨時調用原函數，確保性能不降低
- **後續**: 逐步優化子模組內部實現

### 風險 3: 時間不足
- **應對**: 優先保證功能正確，細節優化可後續進行
- **策略**: 先完成主控器重構，測試通過後再考慮優化

---

## 十、成功標準

### 必須達成
1. ✅ 所有測試通過（向後相容性）
2. ⏳ 實際 skill 生成測試通過
3. ⏳ 代碼行數減少 60% 以上
4. ⏳ 架構清晰，模組職責明確

### 期望達成
1. ⏳ 性能無降低
2. ⏳ 代碼可讀性提升
3. ⏳ 方便後續維護與擴展

---

**建立日期**: 2026-01-30  
**預計完成**: 2026-01-30 18:00  
**當前進度**: 60% ✅  
**狀態**: 🟢 按計畫進行
