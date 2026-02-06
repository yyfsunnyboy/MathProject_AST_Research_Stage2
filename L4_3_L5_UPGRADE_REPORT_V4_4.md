# MCRI V4.4 升級報告

## 概述

成功將 MCRI 評估系統從 **V4.2.2** 升級至 **V4.4**，新增並改進了質量控制和複雜度分析功能。

---

## 改動摘要

### 1. L4.3 質量控制規則修訂 (v2)

**版本**: V4.2.2 → V4.4  
**關鍵變化**: 修改扣分邏輯，更精細地區分違規等級

#### 舊規則 (V4.2.2)
- 零係數項: 扣100分 (直接0分)
- 符號未簡化: 每個扣5分
- 冗餘係數: 每個扣2分

#### 新規則 (V4.4)
- **零係數項** (0x 或 0x^n): **扣10分** - 嚴重違規
- **符號未簡化** (+ - 或 - -): **扣3分** - 中度違規
- **冗餘係數** (1x 或 -1x): **扣2分** - 輕微違規
- **次方未隱藏** (^1): **扣2分** - 輕微違規 [新增]

**滿分**: 10分 (從原本的20分分散結構改為10分)  
**計算方式**: 初始10分，往下扣，最低0分

#### 測試結果
✅ 6/6 測試通過
- 正常表達式: 10分
- 零係數項: 0分
- 符號未簡化: 4分 (扣6分)
- 次方未隱藏: 8分 (扣2分)
- 冗餘係數: 6分 (扣4分)
- 混合違規: 0分

---

### 2. L5 複雜度分析 (新增維度)

**概念**: 記錄但不影響總分 (100分)

#### L5A: 數學複雜度分析
**方法**: 使用 SymPy 解析數學表達式

**指標**:
- `complexity_math_ops`: 運算子數量
- `complexity_ast_atoms`: 原子數量 (變數/常數)

**計算邏輯**:
```python
ops_count = len(sympy.preorder_traversal(expr)) - 1
atom_count = len(expr.free_symbols)
```

**失敗處理**: 若 SymPy 解析失敗，返回 (0, 0)

#### L5B: 代碼複雜度分析
**方法**: 使用 AST 解析 Python 代碼

**指標**:
- `complexity_ast_nodes`: AST 節點數量
- `complexity_loop_depth`: 最大循環深度

**計算邏輯**:
```python
ast_node_count = len(list(ast.walk(tree)))
max_loop_depth = 計算嵌套 for/while 迴圈的最大深度
```

**測試結果**:
✅ 4/4 測試通過
- 無循環代碼: loop_depth=0
- 單層循環: loop_depth=1
- 雙層循環: loop_depth=2

---

## 代碼變更詳情

### 文件: `evaluate_mcri.py`

#### 1. 導入部分 (L1-30)
```python
# 新增可選 SymPy 導入
try:
    import sympy
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False
```

#### 2. L4.3 方法修改 (L814-900)
方法名: `evaluate_math_artifacts()`
- 舊規則邏輯已替換
- 新增 `^1` 次方未隱藏檢測
- 調整所有扣分值

#### 3. L5A 新增方法 (L901-950)
```python
def analyze_math_complexity(question_text: str) -> Tuple[int, int]:
    """
    L5A 數學複雜度分析
    Returns: (ops_count, atom_count)
    """
```

#### 4. L5B 新增方法 (L951-1000)
```python
def analyze_code_structure(code_content: str) -> Tuple[int, int]:
    """
    L5B 代碼複雜度分析
    Returns: (ast_node_count, max_loop_depth)
    """
```

#### 5. Item Dictionary 擴展 (L1010-1040)
```python
item = {
    # ... 既有欄位 ...
    'score_l4_3_artifacts': 0,       # L4.3 質量控制分數
    'complexity_math_ops': 0,        # [V4.4 NEW] L5A 指標
    'complexity_ast_nodes': 0,       # [V4.4 NEW] L5B 指標
    'complexity_loop_depth': 0,      # [V4.4 NEW] L5B 指標
}
```

#### 6. 評估流程更新 (L1075-1090)
```python
# L4.3 質量控制
score_l4_3, _ = self.evaluate_math_artifacts(result)
item['score_l4_3_artifacts'] = int(score_l4_3)

# L5A 數學複雜度
math_ops, math_atoms = self.analyze_math_complexity(...)
item['complexity_math_ops'] = math_ops

# L5B 代碼複雜度
ast_nodes, loop_depth = self.analyze_code_structure(...)
item['complexity_ast_nodes'] = ast_nodes
item['complexity_loop_depth'] = loop_depth
```

#### 7. 資料庫 Schema 更新

**experiment_runs 表** (新增 4 欄):
```sql
avg_l4_3_artifacts FLOAT              -- L4.3 平均分
avg_complexity_math_ops FLOAT         -- L5A 平均運算子數
avg_complexity_ast_nodes FLOAT        -- L5B 平均節點數
avg_complexity_loop_depth FLOAT       -- L5B 平均循環深度
```

**evaluation_items 表** (新增 3 欄):
```sql
complexity_math_ops INTEGER           -- L5A 運算子數
complexity_ast_nodes INTEGER          -- L5B 節點數
complexity_loop_depth INTEGER         -- L5B 循環深度
```

#### 8. CSV 導出更新

**experiment_runs.csv** (新增 4 欄):
```
avg_l4_3_artifacts,
avg_complexity_math_ops,
avg_complexity_ast_nodes,
avg_complexity_loop_depth
```

**evaluation_items.csv** (新增 3 欄):
```
complexity_math_ops,
complexity_ast_nodes,
complexity_loop_depth
```

---

## 分數分配

### 總分: 100 分

| 維度 | 滿分 | 子項 | 說明 |
|------|------|------|------|
| L1 工程基石 | 20 | L1.1/L1.2 | 語法安全 + 執行穩定 |
| L2 資料衛生 | 20 | L2.1/L2.2 | 介面契約 + 格式純淨 |
| L3 評測公平 | 30 | L3.1/L3.2 | 內部一致 + 外部強健 |
| L4 教學有效 | 30 | L4.1/L4.2/L4.3 | 數值友善(10) + 視覺可讀(10) + 質量控制(10) |
| **L5 複雜度分析** | **0** (記錄) | L5A/L5B | **不計入總分** |

---

## 運行範例

### 單項評估
```python
evaluator = MCRI_Evaluator(
    skill_path='skills/gh_Application.py',
    ablation_id=1,
    model_name='gemini-pro'
)

run_record, item_records = evaluator.run_full_evaluation(sample_index=0, repetitions=20)
```

### 輸出內容
```python
# 每個 evaluation_item 包含:
{
    'item_id': 'xxx',
    'status': 'PASS',
    'score_l4_3_artifacts': 10,     # L4.3 分數
    'complexity_math_ops': 5,       # L5A 指標
    'complexity_ast_nodes': 23,     # L5B 指標
    'complexity_loop_depth': 2,     # L5B 指標
    # ... 其他評分 ...
}

# 每個 experiment_run 包含:
{
    'run_id': 'xxx',
    'avg_l4_3_artifacts': 8.5,      # L4.3 平均
    'avg_complexity_math_ops': 4.2, # L5A 平均
    'avg_complexity_ast_nodes': 21.7,
    'avg_complexity_loop_depth': 1.8,
    # ... 其他統計 ...
}
```

---

## 測試驗證

### 測試檔案: `test_l4_3_l5_v2.py`

運行:
```bash
python test_l4_3_l5_v2.py
```

結果:
```
============================================================
Summary
============================================================
[OK] L4.3 Quality Control
[OK] L5A Math Complexity
[OK] L5B Code Complexity

Total: 3/3 tests passed
```

---

## 向後兼容性

✅ **完全兼容** 既有的 L1-L4 評分邏輯
✅ **無破壞性更改** - 只修改 L4.3 規則，不影響其他維度
⚠️ **資料庫重建**: 需運行 `create_database()` 重新初始化表結構

---

## 部署檢查清單

- [x] 導入部分修改 (SymPy 可選)
- [x] L4.3 規則更新 (V4.2.2 → V4.4)
- [x] L5A 方法實現
- [x] L5B 方法實現
- [x] Item dict 擴展
- [x] 資料庫 schema 更新
- [x] CSV fieldnames 更新
- [x] run_record 計算邏輯更新
- [x] 單元測試通過 (6/6 + 4/4)
- [x] 版本號更新 (V4.2.2 → V4.4)

---

## 已知限制

1. **SymPy 可選**: 若未安裝 SymPy，`analyze_math_complexity()` 返回 (0, 0)
2. **L5 不計分**: 複雜度指標僅供參考，不影響最終 MCRI 總分
3. **代碼結構**: L5B 只解析 Python AST，不支援其他語言

---

## 下一步

### 可選增強
1. **L5C 視覺複雜度**: 分析 LaTeX 表達式的視覺複雜度
2. **L4.4 風格檢測**: 偵測不規範的數學表達方式
3. **統計分析**: 計算 L5 指標與最終成績的相關性

### 性能優化
1. 緩存 SymPy 解析結果
2. 並行評估多個 repetitions
3. 增量更新資料庫而非重建

---

**升級完成日期**: 2025-02-04  
**升級版本**: V4.4  
**測試狀態**: ✅ 全部通過

