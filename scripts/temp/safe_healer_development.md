# 🛡️ 安全的 Healer 開發流程

## 問題回顧
**症狀**: A 技能成功 → 修改 code_generator 修復 B → A 又失敗了！  
**根因**: Healer 的 Regex 修復過度匹配或破壞代碼結構

---

## ✅ 新的開發流程（黃金法則）

### 1️⃣ 每次修改前：建立基準測試
```powershell
# 把已成功的技能加入測試清單
# 編輯 scripts/regression_test.py 的 GOLDEN_SKILLS
GOLDEN_SKILLS = [
    'jh_數學1上_FourArithmeticOperationsOfIntegers',  # ✅ 已成功
    # 'jh_數學1上_IntegerAddition',  # 新成功的加這裡
]
```

### 2️⃣ 修改 Healer 代碼
```python
# 在 core/code_generator.py 中新增或修改 Healer
# ⚠️ 必須遵守以下規則：
# 1. 使用 AST 而非字串操作（優先）
# 2. Regex 必須非常精確（至少 5 行上下文）
# 3. 加入 if-guard 防止誤傷
# 4. 記錄修復前後的代碼 diff
```

### 3️⃣ 立即執行回歸測試
```powershell
python scripts/regression_test.py
```

**必須 100% 通過才能繼續！**

### 4️⃣ 測試新技能
```powershell
python scripts/sync_skills_files.py
# 選擇要修復的新技能（如分數四則運算）
```

### 5️⃣ 新技能成功後，加入 GOLDEN_SKILLS
```python
# 編輯 scripts/regression_test.py
GOLDEN_SKILLS = [
    'jh_數學1上_FourArithmeticOperationsOfIntegers',
    'jh_數學1上_FourArithmeticOperationsOfNumbers',  # ✅ 新加入
]
```

### 6️⃣ 再次執行回歸測試確認
```powershell
python scripts/regression_test.py
```

---

## 🚫 禁止的危險操作

### ❌ 禁止：字串插入修改代碼
```python
# 這會破壞後續所有 Regex 匹配位置！
refined_code = refined_code[:pos] + new_code + refined_code[pos:]
```

### ✅ 推薦：使用 re.sub 全局替換
```python
# 這樣不會破壞位置
refined_code = re.sub(pattern, replacement, refined_code)
```

### ✅ 最佳：使用 AST 修改
```python
import ast
tree = ast.parse(refined_code)
# ... 使用 AST NodeTransformer 修改
refined_code = ast.unparse(tree)
```

---

## 🔬 Healer 設計準則

### 準則 1: 精確匹配（至少 5 行上下文）
```python
# ❌ 危險：太寬鬆
pattern = r'value\s*=\s*'

# ✅ 安全：包含充足上下文
pattern = r'''
    for\s+_\s+in\s+range\(num_operands\):\s*\n
    \s+value\s*=\s*[^\n]+\n
    \s+# 這裡應該有 operand_values\.append\(value\)
    (?!\s+operand_values\.append)  # 確保確實沒有 append
'''
```

### 準則 2: 防禦性檢查
```python
# 修復前先確認真的需要修復
if pattern matches AND not already_fixed AND is_safe_to_fix:
    apply_fix()
```

### 準則 3: 小步迭代
- 一次只修一種錯誤
- 每次修改立即測試
- 不要批量添加多個 Healer

---

## 📊 當前狀態檢查清單

- [x] 禁用危險的 Healer 1.7 & 1.8
- [x] 建立回歸測試框架
- [ ] 重新測試整數四則運算（確認沒被破壞）
- [ ] 用新流程修復分數四則運算
- [ ] 逐個添加成功技能到 GOLDEN_SKILLS

---

## 🎯 下一步行動

### 今天（2026-01-28）
1. 執行回歸測試：`python scripts/regression_test.py`
2. 確認整數四則運算仍然正常
3. 手動修復分數四則運算的 MASTER_SPEC（如果需要）

### 明天（2026-01-29）
1. 設計安全的 Healer 1.7 v2（使用 AST）
2. 小步測試 + 回歸測試
3. 記錄成功模式

### 本週末（2026-02-01）
1. 至少完成 5 個技能的穩定生成
2. 確認流水線可以穩定運行
3. 準備小規模實驗（3 技能 × 3 次）

---

## 💡 長期建議

### 策略調整：放棄「完美 Healer」
**舊目標**: 一個萬能的 Healer 修復所有技能  
**新目標**: 針對每個錯誤模式，設計專用 Healer，嚴格測試

**理由**:
- 數學題生成的代碼模式有限（約 10-15 種）
- 每種模式都可以設計專用、精確的 Healer
- 專用 Healer 不會互相干擾

### 技術債務管理
1. 每週五執行全量回歸測試
2. 記錄每個 Healer 的「適用範圍」
3. 建立 Healer 的單元測試

---

**🏆 記住目標**: 不是追求完美代碼，而是**穩定可靠地生成 20 個技能**，拿下金牌！
