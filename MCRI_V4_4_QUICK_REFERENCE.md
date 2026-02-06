# MCRI V4.4 快速參考

## 什麼改變了？

### 1. L4.3 質量控制 (重新設計)

**新規則**:
```
初始 10 分 → 往下扣 → 最低 0 分

違規項目           扣分    等級
─────────────────────────────────
0x 或 0x^n         -10    嚴重 ⛔
+ - 或 - -        -3     中度 ⚠️
1x 或 -1x          -2     輕微 ⚡
^1 (1次方)         -2     輕微 ⚡
```

**例子**:
- 正常: "f(x) = 3x + 2" → 10分
- 零係數: "0x + 5" → 0分 (扣10)
- 混合: "0x + - 1^1" → -17分 → 0分 (最低0)

---

### 2. L5 複雜度分析 (新增)

**不影響總分，只記錄**

| 指標 | 說明 | 來源 |
|------|------|------|
| complexity_math_ops | 運算子數量 | SymPy |
| complexity_ast_nodes | 代碼節點數 | AST |
| complexity_loop_depth | 迴圈深度 | AST |

**例子**:
```python
# 數學表達式: 2x + 3
math_ops = 1 (加法運算)
atoms = 2 (x和3)

# 代碼: for i in range(10): x = i
ast_nodes = 13
loop_depth = 1
```

---

## 分數構成

```
總分 100 分 (不變)
├─ L1: 工程基石 (20分) ✓
├─ L2: 資料衛生 (20分) ✓
├─ L3: 評測公平 (30分) ✓
└─ L4: 教學有效 (30分) ✓
    ├─ L4.1: 數值友善 (10分)
    ├─ L4.2: 視覺可讀 (10分)
    └─ L4.3: 質量控制 (10分) ⭐ [修改]

L5: 複雜度分析 (不計分) 📊 [新增]
```

---

## 資料庫欄位

### 新增欄位

**evaluation_items 表**:
```sql
complexity_math_ops INTEGER           -- 數學運算子
complexity_ast_nodes INTEGER          -- 代碼節點數
complexity_loop_depth INTEGER         -- 迴圈深度
```

**experiment_runs 表**:
```sql
avg_l4_3_artifacts FLOAT              -- L4.3 平均
avg_complexity_math_ops FLOAT         -- 複雜度平均
avg_complexity_ast_nodes FLOAT        -- 節點數平均
avg_complexity_loop_depth FLOAT       -- 迴圈深度平均
```

---

## CSV 輸出欄位

### evaluation_items.csv
```
... [既有 20 欄] ...
score_l4_3_artifacts          ⭐ [修改]
complexity_math_ops           📊 [新增]
complexity_ast_nodes          📊 [新增]
complexity_loop_depth         📊 [新增]
```

### experiment_runs.csv
```
... [既有 36 欄] ...
avg_l4_3_artifacts            ⭐ [新增]
avg_complexity_math_ops       📊 [新增]
avg_complexity_ast_nodes      📊 [新增]
avg_complexity_loop_depth     📊 [新增]
```

---

## 升級清單

### 需要做什麼？

1. **備份資料庫**
   ```bash
   cp instance/kumon_math.db instance/kumon_math.db.bak
   ```

2. **運行新版本**
   ```bash
   python scripts/evaluate_mcri.py
   ```

3. **驗證**
   ```bash
   python test_l4_3_l5_v2.py
   ```

### 檔案變更

✅ `scripts/evaluate_mcri.py` (V4.4)
- 導入 SymPy
- 重寫 L4.3 方法
- 新增 L5A/L5B 方法
- 擴展 database schema
- 更新 CSV fieldnames

---

## 使用範例

```python
from scripts.evaluate_mcri import MCRI_Evaluator

# 建立評估器
evaluator = MCRI_Evaluator(
    skill_path='skills/gh_Application.py',
    ablation_id=1
)

# 執行 20 次重複測試
run_record, items = evaluator.run_full_evaluation(
    sample_index=0,
    repetitions=20
)

# 查詢複雜度指標
for item in items:
    l4_3_score = item['score_l4_3_artifacts']  # 0-10
    math_ops = item['complexity_math_ops']      # 0+
    loop_depth = item['complexity_loop_depth']  # 0+
    
    print(f"L4.3: {l4_3_score}/10, "
          f"Math: {math_ops}, "
          f"Depth: {loop_depth}")
```

---

## 測試狀態

✅ **全部通過**
- L4.3: 6/6 測試
- L5B: 4/4 測試
- 整體: 3/3 套件通過

---

## 常見問題

**Q: 我的資料會怎樣?**  
A: 舊資料保留，新欄位自動初始化為 0

**Q: L5 影響總分嗎?**  
A: 不，L5 只記錄複雜度，不計分

**Q: 需要安裝 SymPy 嗎?**  
A: 可選。沒有的話，math_ops 返回 0

**Q: 向後相容嗎?**  
A: 是。L1-L2-L3 完全不變

**Q: 如何回到 V4.2.2?**  
A: 還原資料庫備份: `cp instance/kumon_math.db.bak instance/kumon_math.db`

---

## 關鍵指標對比

| 指標 | V4.2.2 | V4.4 | 變化 |
|------|--------|------|------|
| L4.3 滿分 | 10 | 10 | 無 |
| 零係數項扣分 | 100 → 0 | 10 → 0 | ⬇️ 少扣90 |
| 符號未簡化 | 5/個 | 3/個 | ⬇️ 少扣2 |
| 次方未隱藏 | 無 | 2/個 | ✨ 新增 |
| L5 複雜度 | 無 | 記錄 | ✨ 新增 |

---

## 技術細節

### L4.3 檢測流程
```
輸入: 題目 + 答案
     ↓
檢測零係數項
     ↓ (有) → 返回 0分
     ↓ (無)
檢測符號未簡化
     ↓ 扣分
檢測冗餘係數
     ↓ 扣分
檢測次方未隱藏
     ↓ 扣分
     ↓
輸出: 最終分數 (0-10)
```

### L5A 複雜度計算
```
輸入: 數學表達式
     ↓
使用 SymPy 解析
     ↓
計算 ops_count (運算子)
計算 atom_count (變數)
     ↓
輸出: (ops_count, atom_count)
```

### L5B 複雜度計算
```
輸入: Python 代碼
     ↓
使用 AST 解析
     ↓
計算 node_count (所有節點)
計算 max_loop_depth (嵌套深度)
     ↓
輸出: (node_count, max_depth)
```

---

## 文件清單

📄 [詳細升級報告](L4_3_L5_UPGRADE_REPORT_V4_4.md)  
📄 [部署摘要](MCRI_V4_4_DEPLOYMENT_SUMMARY.md)  
🧪 [測試檔案](test_l4_3_l5_v2.py)  
📊 [主評估器](scripts/evaluate_mcri.py)

---

**版本**: V4.4  
**狀態**: ✅ 生產就緒  
**最後更新**: 2025-02-04

