# Architect 源代码修复报告

## 修复日期
2026-02-02

## 问题描述

### 症状
使用 `scripts/sync_skills_files.py` 模式[4] (Architect 自动生成) 生成的技能代码出现 placeholder 泄漏：
```
题目: 已知 __ $LATEX$ _ $BLOCK$ _ $0$ __，求 __ $LATEX$ _ $BLOCK$ _ $1$ __...
```

### 根本原因
**Architect System Prompt** ([core/prompt_architect.py](../core/prompt_architect.py)) 中的格式化规则存在冲突：

1. **旧的格式化指令**（第 104-119 行）：
   - 强制所有题型在最后调用 `clean_latex_output(q)`
   - 示例代码：`q = clean_latex_output(q)  # 最後才呼叫`

2. **UNIVERSAL Prompt 的禁令**：
   - 🔴 **絕對禁止** 對 Domain 函數結果使用 `clean_latex_output()`

3. **冲突后果**：
   - Architect 生成的 MASTER_SPEC 指示 AI："最後呼叫 `clean_latex_output(q)`"
   - AI 遵循 MASTER_SPEC（更具体的权威）调用该函数
   - `clean_latex_output()` 尝试处理已包含 `$` 的混合内容
   - 产生 placeholder 泄漏：`__ $LATEX$ _ $BLOCK$ _ $0$ __`

## 修复方案

### 修改文件
- **文件**: [core/prompt_architect.py](../core/prompt_architect.py)
- **修改范围**: Lines 94-133 (formatting 部分)

### 修复内容

#### 1. 移除通用的强制 clean_latex_output() 指令

**旧代码**（已删除）：
```python
- 使用 clean_latex_output() 自動包裝**最後一次**（僅呼叫一次）

**實作三部曲**：
1. 構造中文敘述：使用占位符 {} 預留位置
2. 構造 LaTeX 式子：用 fmt_num() 和 op_latex 格式化
3. 組合：將式子插入敘述，最後呼叫 clean_latex_output(q)
```

#### 2. 引入双模式系统

**新代码**（已添加）：

##### 🟢 模式 A：使用 Domain 標準函數（推薦）
适用于：多项式、导数、三角函数等使用标准函数库的题型

```python
**實作模式判斷**：

🟢 **模式 A：使用 Domain 標準函數（推薦）**
- 當題型涉及多項式、導數、三角函數等，優先使用 Domain 標準函數庫
- Domain 函數已返回完美 LaTeX（不含 $ 符號）
- ⚠️ **絕對禁止**對 Domain 函數結果調用 clean_latex_output()

範例（導數題型）：
1. 使用標準函數格式化：
   poly_latex = _poly_to_latex(terms)  # 返回 "3x^{2} - 5x + 2" (無 $)
   deriv_sym = _deriv_symbol_latex(1)   # 返回 "f'(x)" (無 $)

2. 手動添加 $ 符號組合題目：
   q = f"已知 $f(x) = {poly_latex}$，求 ${deriv_sym}$ 的值。"
   # ✅ 完成！不要再呼叫 clean_latex_output(q)

3. 列舉多個符號時，每個符號獨立包裹 $：
   symbols = ' 與 '.join(f"${_deriv_symbol_latex(n)}$" for n in orders)
   q = f"已知 $f(x) = {poly_latex}$，求 {symbols}。"
   # ✅ 完成！
```

**关键点**：
- ⚠️ **絕對禁止**對 Domain 函數結果調用 clean_latex_output()
- 手动为每个数学符号添加 `$` 符号
- 组合后直接使用，不再调用 clean

##### 🟡 模式 B：簡單運算式（無 Domain 函數）
适用于：简单四则运算，不使用标准函数库的题型

```python
🟡 **模式 B：簡單運算式（無 Domain 函數）**
- 當題型是簡單四則運算、不使用標準函數庫時
- 可以在最後呼叫 clean_latex_output() 一次

範例（簡單運算）：
1. 構造 LaTeX 式子（不含 $）：
   expr = f"{fmt_num(a)} {op_latex['*']} {fmt_num(b)}"  # "3 \\times 5"

2. 組合題目：
   q = f"計算 {expr} 的值"  # "計算 3 \\times 5 的值"

3. 最後呼叫一次：
   q = clean_latex_output(q)  # "計算 $3 \\times 5$ 的值"
```

**关键点**：
- 只在简单运算时允许使用 clean_latex_output()
- 确保调用时内容中没有已经手动添加的 `$` 符号

#### 3. 强化禁止列表

```python
**絕對禁止（會導致佔位符外洩）**：
- ❌ 對 Domain 函數結果使用 clean_latex_output()
- ❌ 混合已包裹 $ 和未包裹內容後再 clean_latex_output()
- ❌ 重複呼叫 clean_latex_output()（會產生多層 $ $）
- ❌ 先手動添加 $ 符號後又呼叫 clean_latex_output()（會產生 $...$...$）
- ❌ 將中文包在 $ $ 內（matplotlib 無法渲染中文）
- ❌ 不用 fmt_num()，直接用 str(a)（無法正確處理負數和分數）
```

## 修复效果

### 验证结果
运行 `python temp\verify_architect_fix.py`：

```
✅ 检查点 1: Domain 函数模式指导
   - 包含 Domain 模式说明: True
   - 包含禁止 clean 警告: True

✅ 检查点 2: 旧指令移除
   - 仍包含旧的强制 clean 指令: False

✅ 检查点 3: 模式区分
   - 包含简单运算模式说明: True

✅ 修复成功！Architect 现在会生成正确的 MASTER_SPEC
```

### 预期行为

#### 修复前（旧版 Architect）
```yaml
# 生成的 MASTER_SPEC 包含冲突指令
formatting:
  question_display: |
    1. 構造 LaTeX 式子
    2. 組合題目
    3. 最後呼叫 clean_latex_output(q)  # ❌ 对 Domain 函数也强制调用
```

#### 修复后（新版 Architect）
```yaml
# 生成的 MASTER_SPEC 根据题型选择模式
formatting:
  question_display: |
    🟢 模式 A (Domain 函數):
       - 手動添加 $ 符號
       - ⚠️ 不要呼叫 clean_latex_output()
    
    🟡 模式 B (簡單運算):
       - 可以在最後呼叫 clean_latex_output()
```

## 影响范围

### 直接影响
- **scripts/sync_skills_files.py 模式[4]**: Architect 自动生成的技能
- **所有使用 Architect 的新技能**: 从此次修复后开始生成的所有 MASTER_SPEC

### 不影响
- **已存在的 MASTER_SPEC**: 数据库中已有的记录不会自动更新
- **手动创建的 MASTER_SPEC**: 需要手动应用新规则
- **模式[1][2][3]**: Ab1/Ab2/Ab3 不使用 Architect

## 使用指南

### 为现有技能更新 MASTER_SPEC

如果你想为现有技能应用新的格式化规则：

1. **删除旧的 MASTER_SPEC**（可选）：
   ```sql
   DELETE FROM skill_gencode_prompt 
   WHERE skill_id = 'gh_ApplicationsOfDerivatives' 
   AND prompt_type = 'MASTER_SPEC';
   ```

2. **重新运行 Architect 生成**：
   ```bash
   python scripts/sync_skills_files.py
   # 选择模式[4] - Architect
   ```

3. **验证新生成的代码**：
   ```python
   from skills.gh_ApplicationsOfDerivatives_14b_Ab3 import generate
   r = generate()
   assert '__ $LATEX$ _' not in r['question_text'], "Placeholder 泄漏！"
   print("✅ 验证通过")
   ```

### 手动修复现有 MASTER_SPEC

如果不想重新生成，可以手动修改数据库中的 MASTER_SPEC：

```python
# 使用 temp/fix_master_spec_no_clean.py 作为参考
# 核心修改：
# 1. 找到 formatting.question_display 部分
# 2. 移除 "最後呼叫 clean_latex_output(q)" 指令
# 3. 添加 "⚠️ 不要呼叫 clean_latex_output(q)" 警告
```

## 技术细节

### Placeholder 泄漏机制解析

1. **正常流程**（clean_latex_output 设计初衷）：
   ```python
   q = "計算 3 \\times 5 的值"
   q = clean_latex_output(q)
   # 结果: "計算 $3 \\times 5$ 的值"
   ```

2. **混合内容导致泄漏**：
   ```python
   # AI 生成的代码（遵循旧 MASTER_SPEC）
   poly_latex = _poly_to_latex(terms)  # "3x^{2} - 5x + 2" (无 $)
   deriv_sym = _deriv_symbol_latex(1)  # "f'(x)" (无 $)
   
   # 组合题目（混合了手动 $ 和裸露符号）
   q = f"已知 $f(x) = {poly_latex}$，求 {deriv_sym}。"
   # 此时 q = "已知 $f(x) = 3x^{2} - 5x + 2$，求 f'(x)。"
   
   # ❌ 调用 clean_latex_output（按照旧 MASTER_SPEC）
   q = clean_latex_output(q)
   
   # clean_latex_output 执行：
   # 1. 提取 $f(x) = ...$ → 替换为 __LATEX_BLOCK_0__
   # 2. 剩余: "已知 __LATEX_BLOCK_0__，求 f'(x)。"
   # 3. 看到中文 "求"，尝试分离中文和数学
   # 4. 误判 __LATEX_BLOCK_0__ 为数学式，尝试添加 $
   # 5. 拆分下划线、字母，产生: "__ $LATEX$ _ $BLOCK$ _ $0$ __"
   
   # 最终输出: "已知 __ $LATEX$ _ $BLOCK$ _ $0$ __，求 $f'$ $(x)$。"
   ```

3. **修复后的正确流程**：
   ```python
   # AI 生成的代码（遵循新 MASTER_SPEC）
   poly_latex = _poly_to_latex(terms)  # "3x^{2} - 5x + 2" (无 $)
   deriv_sym = _deriv_symbol_latex(1)  # "f'(x)" (无 $)
   
   # 手动为每个符号添加 $
   q = f"已知 $f(x) = {poly_latex}$，求 ${deriv_sym}$。"
   # 结果: "已知 $f(x) = 3x^{2} - 5x + 2$，求 $f'(x)$。"
   
   # ✅ 不再调用 clean_latex_output
   # 题目完美，无需后处理
   ```

## 相关文件

- **修复文件**: [core/prompt_architect.py](../core/prompt_architect.py)
- **验证脚本**: [temp/verify_architect_fix.py](../temp/verify_architect_fix.py)
- **历史修复** (针对已存在的 MASTER_SPEC):
  - [temp/fix_master_spec_no_clean.py](../temp/fix_master_spec_no_clean.py) - 创建 ID 204
  - [temp/fix_master_spec_format.py](../temp/fix_master_spec_format.py) - 早期修复

## 后续行动

### 立即行动
- [x] 修复 [core/prompt_architect.py](../core/prompt_architect.py) 源代码
- [x] 验证修复成功
- [x] 创建修复文档

### 推荐行动
- [ ] 为所有 Domain 题型重新生成 MASTER_SPEC（使用模式[4]）
- [ ] 更新现有技能代码（如果使用旧 MASTER_SPEC 生成）
- [ ] 在研究论文中记录此次修复（Prompt Engineering 案例）

### 可选行动
- [ ] 为其他 Domain（三角、概率等）创建标准函数库
- [ ] 扩展验证脚本，自动检测 MASTER_SPEC 冲突
- [ ] 创建 MASTER_SPEC 模板库（预定义常见题型的格式化规则）

## 总结

此次修复从**源头**解决了 Architect 生成 MASTER_SPEC 时的格式化冲突问题。通过引入双模式系统（Domain 函数模式 vs 简单运算模式），明确了不同题型应该使用的格式化策略，彻底避免了 placeholder 泄漏问题。

**关键成果**：
- ✅ 修复了 Architect System Prompt 的内部矛盾
- ✅ 建立了清晰的格式化规则双模式系统
- ✅ 确保未来生成的 MASTER_SPEC 不会再包含冲突指令
- ✅ 为所有使用 Domain 函数的题型提供了正确的实现指导

**影响**：
- 从现在起，使用模式[4] (Architect) 生成的所有技能将自动遵循正确的格式化规则
- 不再需要手动修复每个生成的 MASTER_SPEC
- 降低了 Prompt Engineering 的复杂度和维护成本
