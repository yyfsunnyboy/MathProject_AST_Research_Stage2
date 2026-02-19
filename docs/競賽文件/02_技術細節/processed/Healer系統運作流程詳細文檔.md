# Healer 系統運作流程詳細文檔

**版本**: V2.8  
**更新日期**: 2026-02-14  
**維護團隊**: Math AI Project Team

---

## 📋 目錄

1. [系統概述](#系統概述)
2. [架構與模式](#架構與模式)
3. [四層 Healer 體系](#四層-healer-體系)
4. [完整運作流程](#完整運作流程)
5. [各 Healer 詳細說明](#各-healer-詳細說明)
6. [修復策略與場景](#修復策略與場景)
7. [集成與調用方式](#集成與調用方式)

---

## 系統概述

### 核心理念

**Healer 系統** 是 Math AI 自動代碼生成和修復的的關鍵引擎。它將 AI 生成的不完美代碼進行多層級、漸進式修復，確保生成的計算代碼可以正確執行。

```
AI 生成代碼 (Dirty Code)
     ↓
[RegexHealer] 文字級修復
     ↓
[ASTHealer] 語法樹級修復  
     ↓
[AntiDuplicationHealer] 去重與變量順序修復
     ↓
[UnifiedCleanupHealer] 統一清理與整合
     ↓
可執行代碼 (Clean Code)
```

### 處理層級

| 層級 | 工具 | 位置 | 作用範圍 |
|------|------|------|---------|
| **文字層** | RegexHealer | `core/healers/regex_healer.py` | 字符串級別的修復、依賴注入、符號修復 |
| **語法樹層** | ASTHealer | `core/healers/ast_healer.py` | 邏輯錯誤、危險函數替換、無窮迴圈修復 |
| **去重層** | AntiDuplicationHealer | `core/healers/anti_duplication_healer.py` | 重複定義、變量遮蔽、執行順序 |
| **統一清理層** | UnifiedCleanupHealer | `core/healers/unified_cleanup_healer.py` | 一次性掃描解決所有污染問題 |

---

## 架構與模式

### 設計模式

1. **逐層修復策略** (Layered Healing)
   - 每層處理特定類型的問題
   - 後層修復不影響前層結果
   - 層級遞進，逐漸增加修復精度

2. **修復原則**
   - **保守策略**: 不確定時不修改，避免破壞正確代碼
   - **防守優先**: 預防問題比修復更重要
   - **可追蹤性**: 記錄每次修復的詳細信息

3. **容錯機制**
   - AST 解析失敗時進行語法修復重試
   - 修復失敗時返回原始代碼（避免惡化）
   - 統計修復次數便於調試

### 導出接口

所有 Healer 通過 `core/healers/__init__.py` 統一導出：

```python
from core.healers import (
    ASTHealer,                          # AST 修復引擎
    RegexHealer,                        # Regex 修復引擎
    fix_code_syntax,                    # 便利函數
    clean_redundant_imports,            # 便利函數
    remove_forbidden_functions_unified  # 便利函數
)
```

---

## 四層 Healer 體系

### 1️⃣ RegexHealer (文字層級修復) - V2.8

**文件**: `core/healers/regex_healer.py`  
**責任**: 修復文本級別的問題、自動注入依賴、清理格式

#### 核心修復步驟

```
Step 0    → 移除末尾非 Python 殘留物 (}, ``, 等)
Step -1   → 移除夾雜的中文廢話 (Thinking Leakage)
Step 0.5  → 修復括號不匹配 (缺少 }, ], ))
Step 0.8  → 移除無效依賴引用
Step 1.8  → 自動補全類前綴 (IntegerOps.xxx → xxx 的反向修復)
Step 1    → 移除 Markdown 代碼塊標記 (```python)
Step 2    → 智慧依賴注入 (自動補 import)
Step 2.1  → 遺漏的標準庫注入 (collections, fractions 等)
Step 2.5  → 移除重複的類定義
Step 2.8  → 修復錯誤的類方法調用
Step 3    → 語法符號修復 (中文括號等)
Step 4    → 移除 input() 呼叫 (避免程序卡死)
```

#### 主要方法

| 方法名 | 功能 | 輸入/輸出 |
|--------|------|---------|
| `heal()` | 主要修復入口 | `(code_str) → (fixed_code, stats_dict)` |
| `remove_trailing_artifacts()` | 移除末尾垃圾符號 | `(code) → cleaned_code` |
| `fix_mismatched_braces()` | 修復括號不匹配 | `(code) → fixed_code` |
| `remove_markdown_fences()` | 移除 Markdown 標記 | `(code) → code_without_markdown` |
| `inject_domain_imports()` | 注入領域特定的 import | `(code) → (code_with_imports, count)` |
| `inject_standard_libraries()` | 注入標準庫 import | `(code) → (code, count)` |
| `remove_duplicate_class_definitions()` | 去除重複類 | `(code) → (code, count)` |
| `fix_incorrect_class_method_calls()` | 修復方法調用 | `(code) → (code, count)` |
| `remove_input_calls()` | 移除 input() | `(code) → (code_without_input, found)` |

#### 修復示例

**問題 1: 末尾垃圾符號**
```python
# ❌ 輸入
def calculate():
    return x + y
}

# ✅ 輸出
def calculate():
    return x + y
```

**問題 2: 括號不匹配**
```python
# ❌ 輸入
return {
    'result': value
    # 缺少 }

# ✅ 輸出
return {
    'result': value
}
```

**問題 3: 重複類定義**
```python
# ❌ 輸入
class IntegerOps:
    pass

class IntegerOps:  # 重複！
    pass

# ✅ 輸出
class IntegerOps:
    pass
```

---

### 2️⃣ ASTHealer (語法樹層級修復) - V2.1

**文件**: `core/healers/ast_healer.py`  
**責任**: 修復語法樹層級的邏輯錯誤、函數調用問題

#### 核心修復機制

使用 Python `ast.NodeTransformer` 遍歷抽象語法樹 (AST)，識別和修改有問題的節點：

```
源代碼
   ↓
ast.parse() → AST 樹
   ↓
NodeTransformer.visit() → 節點遍歷與修改
   ↓
ast.unparse() → 修復後的代碼
```

#### 修復對象 (visit_* 方法)

| 修復目標 | 方法 | 處理內容 |
|---------|------|---------|
| 二元運算符 | `visit_BinOp()` | 將 XOR (^) 轉為 Pow (**) |
| 函數調用 | `visit_Call()` | 移除幻覺函數、替換危險函數、修復參數 |
| 導入語句 | `visit_Import()` | 清理非法 import |
| 函數定義 | `visit_FunctionDef()` | 修復函數簽名、參數 |
| 賦值語句 | `visit_Assign()` | 檢測變量遮蔽、執行順序 |

#### 修復示例

**問題 1: 幻覺函數**
```python
# ❌ 輸入 (AI 幻覺生成)
result = build_polynomial_text(coeffs)
result = format_polynomial(coeffs)
result = poly_to_latex(coeffs)

# ✅ 輸出 (統一為正確函數)
result = build_polynomial_text(coeffs)
result = build_polynomial_text(coeffs)
result = build_polynomial_text(coeffs)
```

**問題 2: 危險函數替換**
```python
# ❌ 輸入
value = eval(user_input)
exec(code_string)

# ✅ 輸出
value = safe_eval(user_input)
safe_eval(code_string)
```

**問題 3: 二元運算符修復**
```python
# ❌ 輸入 (XOR 當作是次方)
result = 2 ^ 3  # 得到 1，而非 8

# ✅ 輸出
result = 2 ** 3  # 正確的次方運算
```

**問題 4: input() 切除**
```python
# ❌ 輸入 (會卡死)
x = input("Enter number: ")

# ✅ 輸出 (用常數替換)
x = "0"
```

#### 語法修復 (Syntax De-Noising)

當代碼有語法錯誤時，AST Healer 會進行迭代式修復：

```python
# 遍歷多達 5 次，刪除導致 SyntaxError 的行
for attempt in range(5):
    try:
        tree = ast.parse(code_str)
        break  # ✅ 語法有效
    except SyntaxError as e:
        # ❌ 語法錯誤，刪除有問題的行
        lines.pop(e.lineno - 1)
        self.fixes += 1
```

#### 語意修復 (Semantic Healing)

當靜態分析無法解決邏輯錯誤時，使用 AI 進行深層修復：

```python
def semantic_heal(code_str, error_msg, model='qwen2.5-coder:14b'):
    """
    使用 LLM 進行自我修復
    - 提交失敗的代碼和錯誤堆疊
    - LLM 基於上下文修復邏輯錯誤
    - 驗證修復後的代碼
    """
```

---

### 3️⃣ AntiDuplicationHealer (去重層) - V1.0

**文件**: `core/healers/anti_duplication_healer.py`  
**責任**: 消除重複定義、變量遮蔽、執行順序問題

#### 三大核心功能

##### 功能 1: 去除重複定義

檢測並移除重複的類和函數定義，保留第一個完整的版本：

```python
# ❌ 輸入
class IntegerOps:
    def __init__(self):
        self.data = []
    
    def fmt_num(self, x):
        return str(x)

class IntegerOps:  # 重複！
    def __init__(self):
        pass

# ✅ 輸出
class IntegerOps:
    def __init__(self):
        self.data = []
    
    def fmt_num(self, x):
        return str(x)
```

**檢測邏輯**:
```python
1. 遍歷 AST，記錄所有 ClassDef 和 FunctionDef
2. 統計每個名稱出現的次數
3. 保留第一個定義，刪除後續重複
4. 記錄修復信息便於除錯
```

##### 功能 2: 變量遮蔽檢測

防止生成的代碼覆蓋骨架代碼中的預定義名稱：

```python
# 骨架預定義
IntegerOps  # 是類
fmt_num     # 是函數

# ❌ 輸入 (遮蔽)
IntegerOps = 5  # 將類變成數字！危險
fmt_num = "hello"  # 將函數變成字符串！危險

# ✅ 輸出 (刪除污染賦值)
# IntegerOps 和 fmt_num 保持不變
```

**預定義名稱表** (位於骨架代碼):
```python
PREDEFINED_NAMES = {
    'IntegerOps',
    'FractionOps',
    'fmt_num',
    'to_latex',
    'clean_latex_output',
    'safe_choice',
    'op_latex',
    'random_nonzero',
    'is_divisible',
    'safe_eval',
}
```

##### 功能 3: 變量使用順序修復

確保變量在使用前已定義，否則進行重排或注入默認值：

```python
# ❌ 輸入 (使用前未定義)
result = x + y  # x, y 未定義
x = 10
y = 20

# ✅ 選項 A (重排)
x = 10
y = 20
result = x + y

# ✅ 選項 B (注入默認)
if 'x' not in locals():
    x = 0
result = x + y
x = 10
y = 20
```

#### 實現細節

使用兩個專有類:

1. **DuplicateRemover** - NodeTransformer，刪除重複節點
2. **VariableShadowingDetector** - NodeVisitor，檢測變量問題

---

### 4️⃣ UnifiedCleanupHealer (統一清理層) - V1.0

**文件**: `core/healers/unified_cleanup_healer.py`  
**責任**: 一次性掃描解決所有污染問題，避免反復修改

#### 設計優勢

傳統方式：多次掃描代碼，多次刪除與添加
```
Scan 1 → Remove duplicates X
Scan 2 → Check variables
Scan 3 → Check shadowing
... (最多 5-10 次)
```

統一方式：單次 AST 遍歷，所有修復同時進行
```
Single Pass Scan:
  - 檢測重複定義 ✓
  - 檢測變量遮蔽 ✓
  - 檢測執行順序 ✓
  - 移除所有問題 ✓
(一次完成)
```

#### 統計信息

```python
self.total_fixes = 0          # 總修復次數
self.duplicate_count = 0      # 移除的重複定義數
self.shadowing_count = 0      # 修復的遮蔽變量數
self.variable_order_count = 0 # 修復的執行順序數
```

---

## 完整運作流程

### 核心調用鏈

以下是從生成代碼到可執行代碼的完整流程：

```
┌─────────────────────────────────────────────────────┐
│  AI 生成代碼 (可能有語法錯誤、缺少 import、邏輯錯誤)  │
└────────────┬────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────┐
│  [Stage 1] RegexHealer.heal()                       │
│  - 移除末尾垃圾 (}, ```, 等)                        │
│  - 移除中文廢話                                      │
│  - 修復括號不匹配                                    │
│  - 刪除 Markdown 標記                               │
│  - 自動注入 import (domain + stdlib)               │
│  - 去除重複類定義                                   │
│  - 修復類方法調用                                   │
│  - 修復中文符號                                     │
│  - 移除 input() 呼叫                               │
└────────────┬────────────────────────────────────────┘
             │ (修復統計信息)
             ▼
┌─────────────────────────────────────────────────────┐
│  [Stage 2] ASTHealer.heal()                         │
│  如果有語法錯誤:                                    │
│    - 迭代式刪除導致 SyntaxError 的行               │
│  然後:                                              │
│    - visit_BinOp()      修復 ^ → **                │
│    - visit_Call()       修復幻覺函數、input()      │
│    - visit_Import()     清理非法 import            │
│    - visit_Assign()     修復 fmt_num 參數          │
└────────────┬────────────────────────────────────────┘
             │ (修復統計信息)
             ▼
┌─────────────────────────────────────────────────────┐
│  [Stage 3] AntiDuplicationHealer.heal() 或           │
│           UnifiedCleanupHealer.heal()               │
│  - 移除重複類/函數定義                             │
│  - 檢測變量遮蔽                                     │
│  - 修復變量使用順序                                │
│  - 注入變量初值 (必要時)                          │
└────────────┬────────────────────────────────────────┘
             │ (修復統計信息)
             ▼
┌─────────────────────────────────────────────────────┐
│  [Optional] 如果仍有執行錯誤:                      │
│  ASTHealer.semantic_heal()                         │
│  - 使用 LLM 進行深層邏輯修復                      │
│  - 驗證修復後的代碼                                │
└────────────┬────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────┐
│  可執行代碼 (Clean Code) ✓                         │
│  - 語法正確                                        │
│  - 依賴完整                                        │
│  - 邏輯清晰                                        │
│  - 無重複定義                                      │
│  - 無變量衝突                                      │
└─────────────────────────────────────────────────────┘
```

### 實際代碼調用示例

```python
from core.healers import ASTHealer, RegexHealer

# 假設 ai_generated_code 是 AI 生成的代碼
code = ai_generated_code

# 第一階段：Regex 修復
regex_healer = RegexHealer()
code, regex_stats = regex_healer.heal(code)
print(f"✓ Regex 修復 {regex_stats['regex_fix_count']} 個問題")

# 第二階段：AST 修復
ast_healer = ASTHealer(ai_client=None)  # 不使用 AI 語意修復
code, ast_fixes = ast_healer.heal(code)
print(f"✓ AST 修復 {ast_fixes} 個問題")

# 第三階段：去重修復 (可選)
from core.healers.anti_duplication_healer import heal_duplicates_and_variables
code, dedup_fixes = heal_duplicates_and_variables(code)
print(f"✓ 去重修復 {dedup_fixes} 個問題")

# 驗證代碼有效性
try:
    compile(code, '<string>', 'exec')
    print("✅ 代碼編譯成功！")
except SyntaxError as e:
    print(f"❌ 仍有語法錯誤: {e}")
```

---

## 各 Healer 詳細說明

### 3️⃣ AntiDuplicationHealer 詳細實現

#### 類與類方法

```python
class AntiDuplicationHealer:
    def __init__(self):
        self.fixes = 0
        self.duplicate_classes = {}
        self.duplicate_functions = {}
    
    def heal(self, code: str) -> tuple:
        """主要修復入口"""
        # 1. 嘗試解析代碼
        # 2. 第一遍掃描記錄所有定義
        # 3. 識別重複定義
        # 4. 第二遍移除重複節點
        # 5. 轉回代碼字符串
```

#### 輔助類

```python
class DuplicateRemover(ast.NodeTransformer):
    """刪除被標記的重複 AST 節點"""
    
    def visit_ClassDef(self, node):
        if id(node) in self.duplicates_to_remove:
            return None  # 返回 None = 刪除該節點
        return node
    
    def visit_FunctionDef(self, node):
        if id(node) in self.duplicates_to_remove:
            return None  # 刪除
        return node

class VariableShadowingDetector(ast.NodeVisitor):
    """檢測變量遮蔽問題"""
    
    PREDEFINED_NAMES = {
        'IntegerOps', 'fmt_num', 'to_latex', ...
    }
    
    def visit_Assign(self, node):
        # 檢查左邊是否在試圖重新賦值預定義名稱
        if isinstance(node.targets[0], ast.Name):
            target = node.targets[0].id
            if target in self.PREDEFINED_NAMES:
                # 標記為污染賦值，待刪除
                self.shadowing_assigns.append((target, node.lineno))
```

---

### 4️⃣ UnifiedCleanupHealer 詳細實現

#### Key Features

1. **單次 AST 遍歷**
   ```python
   def heal(self, code: str):
       tree = ast.parse(code)
       
       # 在一個遍歷中完成所有掃描
       seen_classes = set(self.PREDEFINED_NAMES)
       seen_functions = set()
       defined_variables = {}
       
       # ... 進行所有檢查 ...
       
       return fixed_code
   ```

2. **統計信息**
   ```python
   {
       'total_fixes': 15,
       'duplicate_count': 3,      # 移除了 3 個重複類
       'shadowing_count': 2,      # 修復了 2 個遮蔽
       'variable_order_count': 10 # 修復了 10 個順序問題
   }
   ```

3. **與 RegexHealer 的協作**
   ```
   RegexHealer (移除重複類定義) 
       ↓
   UnifiedCleanupHealer (檢測遮蔽和順序)
       ↓
   完全清潔的代碼
   ```

---

## 修復策略與場景

### 場景 1: "幻覺函數" 問題

**問題描述**: AI 模型生成不存在的函數調用

```python
# ❌ 錯誤代碼
result = build_polynomial_text(coeffs)  # ✓ 存在
result = format_polynomial(coeffs)      # ✗ 這個函數不存在！
result = latex_polynomial(coeffs)       # ✗ 這個也不存在！
```

**修復過程**:

| 步驟 | Healer | 動作 |
|------|--------|------|
| 1 | RegexHealer | 識別這些函數調用，保持原樣 |
| 2 | ASTHealer | 檢測幻覺函數列表中的函數 |
| | | 將 `format_polynomial()` → `build_polynomial_text()` |
| | | 將 `latex_polynomial()` → `build_polynomial_text()` |
| 3 | 驗證 | 所有多項式格式化都統一使用 `build_polynomial_text()` |

**AST Healer 代碼**:
```python
hallucinated_funcs = [
    'build_polynomial_text', 'format_polynomial', 'poly_to_latex',
    'build_expression', 'latex_polynomial',
    ...
]

if isinstance(node.func, ast.Name) and node.func.id in hallucinated_funcs:
    node.func.id = 'build_polynomial_text'
    self.fixes += 1
```

---

### 場景 2: 括號不匹配

**問題描述**: 返回字典或列表時缺少結尾括號

```python
# ❌ 錯誤代碼
def calculate():
    return {
        'result': x + y,
        'status': 'ok'
        # ← 缺少 }

# ✅ 修復後
def calculate():
    return {
        'result': x + y,
        'status': 'ok'
    }  # ← 補上 }
```

**修復過程**:

| 步驟 | Healer | 動作 |
|------|--------|------|
| 1 | RegexHealer | 檢測末尾不匹配的括號 |
| | | 匹配 `{` 的數量和 `}` 的數量 |
| 2 | RegexHealer | 在合適位置補上缺失的 `}` |
| 3 | 驗證 | AST 可成功解析 |

**RegexHealer 代碼**:
```python
def fix_mismatched_braces(self, code_str: str) -> str:
    """檢測並修復括號不匹配 - 保守策略"""
    
    # 計算括號數量
    open_count = code_str.count('{')
    close_count = code_str.count('}')
    
    if open_count > close_count:
        # 缺少 }
        code_str += '\n' + '}' * (open_count - close_count)
        
    return code_str
```

---

### 場景 3: 重複定義

**問題描述**: 同一類或函數被定義多次

```python
# ❌ 錯誤代碼
class IntegerOps:
    def __init__(self):
        self.value = 0
    
    def fmt_num(self, x):
        return str(x)

# 重複定義！（可能是因為骨架代碼被複制）
class IntegerOps:
    def __init__(self):
        pass

# ✅ 修復後（只保留第一個）
class IntegerOps:
    def __init__(self):
        self.value = 0
    
    def fmt_num(self, x):
        return str(x)
```

**修復過程**:

| 步驟 | Healer | 動作 |
|------|--------|------|
| 1 | RegexHealer (V2.8) | 在文字級別檢測並移除重複類定義 |
| 2 | AST/UnifiedCleanup | 在 AST 級別驗證去重結果 |
| 3 | 驗證 | 確保只有一個完整的類定義 |

---

### 場景 4: 變量遮蔽污染

**問題描述**: 生成的代碼覆蓋骨架里的工具函數

```python
# 骨架代碼 (預定義)
def fmt_num(x):
    """格式化數字的工具函數"""
    return str(x)

# ❌ AI 生成代碼（污染）
fmt_num = lambda x: x * 2  # ← 覆蓋了原函數！

# ✅ 修復後（移除污染）
# fmt_num = lambda x: x * 2  ← 被刪除

# fmt_num() 仍然是原來的工具函數
```

**修復過程**:

| 步驟 | Healer | 動作 |
|------|--------|------|
| 1 | AntiDuplicationHealer/UnifiedCleanup | 掃描預定義名稱列表 |
| 2 | | 檢測是否有賦值語句覆蓋預定義名稱 |
| 3 | | 刪除所有污染賦值 |
| 4 | 驗證 | 預定義函數保持原狀 |

**代碼** (UnifiedCleanupHealer):
```python
PREDEFINED_NAMES = {
    'IntegerOps',
    'fmt_num',
    'to_latex',
    'clean_latex_output',
    'safe_choice',
    'op_latex',
    'random_nonzero',
    'is_divisible',
    'safe_eval',
}

# 掃描所有賦值
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in self.PREDEFINED_NAMES:
                # 污染！標記為刪除
                self.shadowing_assigns.append(node)
```

---

### 場景 5: 執行順序錯誤

**問題描述**: 變量在定義前被使用

```python
# ❌ 錯誤代碼
def calculate():
    result = x + y      # ← x, y 還未定義！
    x = 10
    y = 20
    return result

# ✅ 修復後（重排）
def calculate():
    x = 10
    y = 20
    result = x + y      # ← 現在 x, y 已定義
    return result
```

**修復過程**:

| 步驟 | Healer | 動作 |
|------|--------|------|
| 1 | AntiDuplicationHealer | 掃描所有節點，記錄定義點 |
| 2 | | 檢測每個變量的使用點 |
| 3 | | 如果使用在定義之前，進行重排 |
| 4 | UnifiedCleanupHealer | 一次掃描完成所有重排 |

---

## 集成與調用方式

### 直接調用

```python
from core.healers import ASTHealer, RegexHealer

# 方法 1: 完整流程
code = """
class IntegerOps:
    pass

def fmt_num(x):
    return str(x)

result = 2 ^ 3  # 這是 XOR，不是次方！
"""

# Stage 1: Regex 修復
regex_healer = RegexHealer()
code, regex_stats = regex_healer.heal(code)

# Stage 2: AST 修復
ast_healer = ASTHealer()
code, ast_fixes = ast_healer.heal(code)

# Stage 3: 去重修復
from core.healers.anti_duplication_healer import heal_duplicates_and_variables
code, dedup_fixes = heal_duplicates_and_variables(code)

print(code)  # 修復後的代碼
```

### 在生成管道中集成

```python
from core.healers import ASTHealer, RegexHealer
from core.code_generator import CodeGenerator

class GenerationPipeline:
    def __init__(self, ai_client):
        self.ai_client = ai_client
        self.regex_healer = RegexHealer()
        self.ast_healer = ASTHealer(ai_client=ai_client)
    
    def generate_and_heal(self, prompt):
        # Step 1: 使用 AI 生成代碼
        raw_code = self.ai_client.generate_content(prompt)
        
        # Step 2: 應用 Healers
        code, _ = self.regex_healer.heal(raw_code)
        code, _ = self.ast_healer.heal(code)
        
        # Step 3: 驗證與返回
        try:
            compile(code, '<string>', 'exec')
            return code
        except SyntaxError:
            return None
```

### 透過日誌追蹤修復

每個 Healer 都會記錄詳細的修復信息：

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

regex_healer = RegexHealer()
code, stats = regex_healer.heal(dirty_code)

# 輸出：
# 🔧 [RegexHealer V2.6] 移除末尾非代碼殘留物 (如 '}', 'python')
# 🔧 [RegexHealer V2.6] 修復括號不匹配
# 🔧 [RegexHealer V2.8] 移除 3 個重複的類定義
# 🔧 [RegexHealer V2.8] 修復 2 個錯誤的方法調用
# 🔧 [RegexHealer] 移除 Markdown 代碼塊標記
# ✓ Regex 修復統計: {'regex_fix_count': 7, ...}
```

---

## 常見問題 (FAQ)

### Q1: Regex Healer 和 AST Healer 有什麼區別？

**Regex Healer**:
- 在 AST 解析**之前**工作
- 處理文字層級的問題（末尾垃圾、括號不匹配）
- 注入依賴、清理格式
- 速度快，但精度有限

**AST Healer**:
- 在 AST **解析後**工作
- 處理邏輯層級的問題（幻覺函數、危險函數、無窮迴圈）
- 修改語法樹中的節點
- 速度慢，但精度高

### Q2: 為什麼要分多層？不能一層搞定？

因為不同類型的錯誤需要不同級別的分析：

1. **文字級錯誤** (括號、Markdown) → Regex 搞定
2. **邏輯級錯誤** (幻覺函數、XOR) → AST 搞定
3. **污染級錯誤** (重複定義、遮蔽) → UnifiedCleanup 搞定

分層設計使每層職責單一，易於維護和測試。

### Q3: 修復失敗時會怎樣？

Healers 採用**保守策略**：

```python
try:
    tree = ast.parse(code)
    # 修復...
    return modified_code
except Exception as e:
    logger.error(f"修復失敗: {e}")
    return original_code  # ← 返回原代碼，避免惡化
```

### Q4: 可以禁用某個 Healer 嗎？

可以，直接跳過即可：

```python
code = ai_generated_code

# 只使用 AST Healer
ast_healer = ASTHealer()
code, _ = ast_healer.heal(code)

# 跳過 Regex 和 AntiDuplication
```

### Q5: Semantic Heal 是什麼？

當靜態分析無法解決的邏輯錯誤時，使用 LLM 進行修復：

```python
ast_healer = ASTHealer(ai_client=gemini_client)

try:
    exec(code)
except NameError as e:
    # 變量未定義錯誤，使用 LLM 修復
    code, success = ast_healer.semantic_heal(code, str(e))
```

---

## 性能與優化

### 時間複雜度

| Healer | 複雜度 | 原因 |
|--------|--------|------|
| RegexHealer | O(n) | 字符串掃描 |
| ASTHealer | O(n) | AST 遍歷 |
| AntiDuplicationHealer | O(n) | 兩次 AST 遍歷 |
| UnifiedCleanupHealer | O(n) | 單次 AST 遍歷 |

其中 n = 代碼行數

### 優化建議

1. **批量處理**: 對多個代碼片段，複用 Healer 實例
   ```python
   healer = RegexHealer()  # 只初始化一次
   for code in code_list:
       code, _ = healer.heal(code)
   ```

2. **條件跳過**: 如果代碼已經乾淨，跳過 Healer
   ```python
   if 'eval' not in code and 'exec' not in code:
       # 可能不需要 AST 修復
       pass
   ```

3. **選擇性應用**: 根據生成模型選擇 Healer
   ```python
   if model == 'gpt-4':
       # GPT-4 生成質量高，只用 Regex
       healer = RegexHealer()
   else:
       # 其他模型生成質量低，需要完整流程
       # 使用 RegexHealer + ASTHealer + UnifiedCleanup
   ```

---

## 總結

**Healer 系統**通過多層級、漸進式的修復，確保 AI 生成的代碼可以正確執行。核心流程為：

```
文字層 (RegexHealer)
  ↓
語法樹層 (ASTHealer)
  ↓
去重層 (UnifiedCleanupHealer/AntiDuplicationHealer)
  ↓
可執行代碼
```

每層都有具體的責任，互相協作，最終產出乾淨、可靠的代碼。

---

**文檔完成時間**: 2026-02-14  
**版本**: V2.8  
**下一步計劃**:
- [ ] 增強 Semantic Heal 的錯誤恢復能力
- [ ] 優化 UnifiedCleanupHealer 的單次掃描性能
- [ ] 針對特定數學域添加專用 Healer
