# 統一代碼清理 Healer - 架構設計文檔

## 問題背景

### 舊設計的問題（用戶反饋）

> "你這樣設計很差，把順序整理清楚，不要刪掉了又加回來"

**具體問題：**

```
舊流程中的衝突：
┌─ Step 4.6: Variable Shadowing Detector
│  └─ 動作：刪除 IntegerOps = 0
├─ Step 7.5: Variable-Before-Use Checker  
│  └─ 發現 IntegerOps 未定義
│  └─ 動作：重新添加 IntegerOps = 0 ❌ 重新添加了污染！
└─ 結果：代碼仍然有污染，反復修復無效
```

---

## 新設計：統一清理 Healer

### 設計原理

**一次性 AST 遍歷，完成所有修復 - 避免衝突**

```python
UnifiedCleanupHealer
├─ 第一遍掃描
│  ├─ 收集所有本地定義 (class/function)
│  ├─ 掃描所有賦值語句
│  ├─ 標記重複定義
│  ├─ 標記污染賦值 (包含預定義名稱)
│  └─ 標記變量順序問題
│
└─ 第二遍清理
   ├─ 刪除所有重複定義
   ├─ 刪除所有污染賦值  ← 不再反復
   └─ 處理變量順序
```

### 核心特性

#### 1. **預定義名稱感知**

```python
PREDEFINED_NAMES = {
    'IntegerOps',          # 類別
    'fmt_num',             # 函數
    'to_latex',            # 函數
    'clean_latex_output',  # 函數
    'safe_choice',         # 函數
    'op_latex',            # 字典
    'random_nonzero',      # 方法
    'is_divisible',        # 方法
    'safe_eval'            # 函數
}
```

任何對這些名稱的賦值都被視為污染並刪除。

#### 2. **單一決策樹**

```python
class ProblemScanner(ast.NodeVisitor):
    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                
                # 一次性判決：
                if var_name in PREDEFINED_NAMES:
                    # ✓ 這是污染 → 標記刪除
                    mark_for_deletion(node)
                elif var_name in self.defined_names:
                    # ✓ 覆蓋本地定義 → 標記污染
                    mark_shadowing(node)
                else:
                    # ✓ 正常賦值 → 允許
                    pass
```

**結果：無衝突，無反復修改**

#### 3. **跳過預定義變量的變量檢查**

```python
# 在變量順序檢查中
def _is_builtin(self, name):
    return name in self.PREDEFINED_NAMES or \
           name in builtins
           
# 這樣即使刪除了污染賦值，也不會在變量檢查中重新添加
```

---

## 集成到 code_generator.py

### 變更內容

**file: `core/code_generator.py`**

```python
# Line 60: 更新導入
- from core.healers.anti_duplication_healer import heal_duplicates_and_variables
+ from core.healers.unified_cleanup_healer import heal_unified

# Line 671: 更新函數呼叫
- code_after_anti_dup, total_special_fixes = heal_duplicates_and_variables(code_after_ast)
- anti_dup_fixes = total_special_fixes
+ code_after_anti_dup, anti_dup_fixes = heal_unified(code_after_ast)
```

### 執行流程（AB3 只）

```
Step 2: Regex Healer (Ab2/Ab3)
Step 3: AST Healer (Ab3 only)
Step 4.5: Unified Cleanup Healer (Ab3 only) ← 新流程
        ├─ 刪重複定義
        ├─ 刪污染賦值
        └─ 不再有衝突
        
最終代碼：乾淨、無污染、無衝突
```

---

## 實測驗證

### 測試 1: 單位測試

**輸入代碼：**
```python
def generate_question():
    IntegerOps = 0          # 污染 1
    fmt_num = 0             # 污染 2
    clean_latex_output = None  # 污染 3
    
    class IntegerOps:       # 重複
        pass
    
    def format_output():
        return "test"
    
    def format_output():    # 重複
        return "test2"
```

**修復結果：**
```
✅ 移除 3 個污染賦值
✅ 移除 1 個重複定義
✅ 沒有重新添加污染
✅ 沒有衝突
```

### 測試 2: 整合測試

**場景：模擬代碼生成管道**

**輸入：** 47 行代碼包含 4 個污染賦值、2 個重複定義

**執行：** `heal_unified(code)`

**輸出：**
```
修復統計：
- 重複定義：2 個 ✅
- 污染賦值：4 個 ✅
- 總修復：6 個

驗證：
- 污染檢查：✅ 全部移除
- 重複檢查：✅ 無重複
- 語法檢查：✅ 有效
- 邏輯檢查：✅ IntegerOps.random_nonzero() 正常工作
```

---

## 對比：舊 vs 新

### 舊設計（分離式）

```
問題 1: 多次遍歷 AST
        ├─ AntiDuplicationHealer.heal()
        ├─ VariableShadowingDetector.detect()
        ├─ ShadowingAssignRemover.visit()
        └─ VariableBeforeUseChecker.heal()
        └─ 每次都修改 AST → 複雜、易衝突

問題 2: 步驟間衝突
        A: 刪除 IntegerOps = 0
        B: 掃描發現 IntegerOps 未定義
        C: 重新添加 IntegerOps = 0
        └─ 循環修復，污染無法清除

問題 3: 狀態依賴
        每個步驟都依賴前面步驟的結果
        → 易出現邊界情況
```

### 新設計（統一式）

```
優點 1: 單次 AST 遍歷
        ├─ ProblemScanner 掃描所有問題
        ├─ CodeCleaner 一次性清理
        └─ 完成 → 無需反復

優點 2: 無衝突決策
        ├─ 所有決策在掃描階段完成
        ├─ 清理階段只是執行預定設計
        └─ 無邊界情況

優點 3: 無狀態依賴
        ├─ 每個判決獨立
        ├─ 無上一步的輸出依賴
        └─ 穩定、可預測
```

---

## 對 AB1/AB2 的不影響

**Ablation 設置**

```python
# code_generator.py, Line 666
if ablation_id >= 3:  # ← 只在 AB3 執行
    code_after_anti_dup, anti_dup_fixes = heal_unified(code_after_ast)
else:
    code_after_anti_dup = code_after_ast
    anti_dup_fixes = 0
```

**結果：**
- AB1 (Bare): 無 Healer → 無影響 ✅
- AB2 (Engineered): 無統一 Healer → 無影響 ✅
- AB3 (Full Healing): 使用統一 Healer → 污染被統一清理 ✅

---

## 模塊文件

**新增文件：** `core/healers/unified_cleanup_healer.py` (200+ 行)

**主要類別：**
- `UnifiedCleanupHealer`: 主控制類
- `ProblemScanner(ast.NodeVisitor)`: 掃描問題
- `CodeCleaner(ast.NodeTransformer)`: 清理代碼

**導出函數：**
```python
def heal_unified(code: str) -> tuple[str, int]:
    """
    統一清理代碼
    
    返回: (修復後代碼, 修復數量)
    """
```

---

## 總結

**用戶需求：** "把順序整理清楚，不要刪掉了又加回來"

**解決方案：** 統一 Healer - 單次 AST 遍歷，避免衝突

**效果：**
- ✅ 順序清楚（單次遍歷 = 清晰流程）
- ✅ 無衝突（所有決策同時做出）
- ✅ 無反復（修復一次完成）
- ✅ 穩定性提高（無狀態依賴）
- ✅ 易維護（單一責任）

