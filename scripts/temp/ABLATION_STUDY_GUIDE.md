# Ablation Study 实验指南

## 📋 实验设计确认

### 实验条件 (已验证 ✅)

| Ablation ID | 名称 | Prompt | Healer | 用途 |
|------------|------|--------|--------|------|
| **Ab1** | Bare | BARE_MINIMAL_PROMPT (270 chars)<br>+ MASTER_SPEC | ❌ 无 | 测试最简单配置 |
| **Ab2** | MASTER_SPEC_Only | 纯 MASTER_SPEC<br>(无额外工程化 Prompt) | ❌ 无 | 测试 Prompt 工程化价值 |
| **Ab3** | Full-Healing | 纯 MASTER_SPEC<br>(与 Ab2 相同) | ✅ Regex+AST | 测试 Healer 独立价值 |

### 关键对比点

#### Ab1 vs Ab2
- **Prompt 差异**: Bare (270 chars) vs MASTER_SPEC (1500-2500 chars)
- **Healer 差异**: 都无 Healer
- **预期差异**: 20-40 percentage points
- **验证内容**: MASTER_SPEC 工程化 Prompt 的单独价值

#### Ab2 vs Ab3 ⭐ (核心对比组！)
- **Prompt 差异**: 相同 (都使用纯 MASTER_SPEC)
- **Healer 差异**: 无 vs 完整 (Regex+AST)
- **预期差异**: 30-50 percentage points
- **验证内容**: Healer 自愈机制的独立价值

#### Ab1 vs Ab3
- **Prompt 差异**: Bare vs MASTER_SPEC
- **Healer 差异**: 无 vs 完整
- **预期差异**: 50-70 percentage points
- **验证内容**: 完整系统的整体价值

---

## 🚀 执行步骤

### 1. 验证实验条件

```bash
python scripts/verify_ablation_conditions.py
```

**预期输出**：
- ✅ 所有 Ablation Settings 正确配置
- ✅ 所有测试技能都有 MASTER_SPEC
- ✅ 显示关键对比点

### 2. 执行 Ablation Study

```bash
python scripts/ablation_bare_vs_healer.py
```

**交互式流程**：

#### 步骤 1: 检查 MASTER_SPEC

程序会自动检查所有测试技能的 MASTER_SPEC 状态：

```
🔍 实验准备：检查 MASTER_SPEC (Coding Prompt)
======================================================================
  ✅ 整数的加法运算
     已有 MASTER_SPEC (2516 chars, 3 天前建立)
  ✅ 整数的减法运算
     已有 MASTER_SPEC (1893 chars, 3 天前建立)
  ...
```

#### 步骤 2: 询问是否重新生成

```
💡 是否重新生成所有技能的 MASTER_SPEC (Prompt Architect)?
   注意：重新生成将覆盖现有的 MASTER_SPEC

选项:
  y - 是，重新生成所有 MASTER_SPEC
  n - 否，使用现有的 MASTER_SPEC

请选择 (y/n):
```

**建议**：
- **首次运行**：选择 `y` 确保 MASTER_SPEC 是最新的
- **重复实验**：选择 `n` 使用现有的 MASTER_SPEC（保证可重复性）

#### 步骤 3: 执行实验

程序会为每个技能生成 3 个版本：

```
🧪 技能: 整数的加法运算
   ID: jh_數學1上_IntegerAdditionOperation
======================================================================

📊 测试组 Ab1: Bare Prompt (270 chars, 无 Healer)
----------------------------------------------------------------------
  📝 输出档案: jh_數學1上_IntegerAdditionOperation_14B_Ab1.py
  📝 [Prompt] Ab1 - BARE_MINIMAL_PROMPT (270 chars)
     ⚠️  无工程化指导，无 Healer
  ...
  ✅ 生成成功
     修复次数: 0

📊 测试组 Ab2: Database MASTER_SPEC + Regex Healer
----------------------------------------------------------------------
  📝 输出档案: jh_數學1上_IntegerAdditionOperation_14B_Ab2.py
  📝 [Prompt] Ab2 - Database MASTER_SPEC
     📚 Engineering Prompt: 6833 chars
     📄 MASTER_SPEC: 2516 chars
  ...
  ✅ 生成成功
     修复次数: 3
       - Regex 修复: 3
       - AST 修复: 0

📊 测试组 Ab3: Database MASTER_SPEC + Full Healer (Regex+AST)
----------------------------------------------------------------------
  📝 输出档案: jh_數學1上_IntegerAdditionOperation_14B_Ab3.py
  📝 [Prompt] Ab3 - Database MASTER_SPEC
     📚 Engineering Prompt: 6833 chars
     📄 MASTER_SPEC: 2516 chars
  ...
  ✅ 生成成功
     修复次数: 5
       - Regex 修复: 3
       - AST 修复: 2
```

### 3. 查看结果

#### 生成的文件

在 `skills/` 目录下会生成 12 个文件（4 技能 × 3 ablations）：

```
skills/
├── jh_數學1上_IntegerAdditionOperation_14B_Ab1.py       # Bare
├── jh_數學1上_IntegerAdditionOperation_14B_Ab2.py       # Regex Only
├── jh_數學1上_IntegerAdditionOperation_14B_Ab3.py       # Full-Healing
├── jh_數學1上_IntegerSubtractionOperation_14B_Ab1.py
├── jh_數學1上_IntegerSubtractionOperation_14B_Ab2.py
├── jh_數學1上_IntegerSubtractionOperation_14B_Ab3.py
├── jh_數學1上_IntegerMultiplication_14B_Ab1.py
├── jh_數學1上_IntegerMultiplication_14B_Ab2.py
├── jh_數學1上_IntegerMultiplication_14B_Ab3.py
├── jh_數學1上_IntegerDivision_14B_Ab1.py
├── jh_數學1上_IntegerDivision_14B_Ab2.py
└── jh_數學1上_IntegerDivision_14B_Ab3.py
```

#### 总结报告

程序最后会输出详细的总结报告：

```
📊 总结报告
======================================================================

成功率对比 (共 4 个技能):
  Ab1 (Bare):       2/4 (50%)
  Ab2 (Regex Only): 3/4 (75%)
  Ab3 (Full):       4/4 (100%)

Healer 修复统计:
  Ab2 总修复次数:   12 (平均 3.0/技能)
  Ab3 总修复次数:   18 (平均 4.5/技能)

📁 生成的档案清单:
  整数的加法运算:
    ✅ jh_數學1上_IntegerAdditionOperation_14B_Ab1.py
    ✅ jh_數學1上_IntegerAdditionOperation_14B_Ab2.py
    ✅ jh_數學1上_IntegerAdditionOperation_14B_Ab3.py
  ...

💡 核心结论:
  ✅ Healer 显著提升成功率:
     Bare → Regex Only: +1 个技能 (+25%)
     Bare → Full:       +2 个技能 (+50%)
     修复总数 (Ab3):    18 次
     ✨ 实验设计有效！Healer 的价值得到证明！
```

---

## 📊 结果分析模式

### 模式 1: 全部成功，有修复
```
Ab1: ✅ 成功 - 修复 0 次
Ab2: ✅ 成功 - 修复 3 次
Ab3: ✅ 成功 - 修复 5 次

📊 模式: 全部成功，Healer 修复了 5 个错误
    说明: Bare Prompt 可能有隐藏错误，Healer 成功修复
```

**解读**：技能较简单，但 Healer 仍在改善代码质量

### 模式 2: 仅 Full-Healing 成功
```
Ab1: ❌ 失败
Ab2: ❌ 失败
Ab3: ✅ 成功 - 修复 8 次

✅ 模式: 仅 Full-Healing 成功
    说明: Healer 关键且有效！
```

**解读**：这是最理想的结果，证明 Healer 的核心价值！

### 模式 3: 全部成功且无需修复
```
Ab1: ✅ 成功 - 修复 0 次
Ab2: ✅ 成功 - 修复 0 次
Ab3: ✅ 成功 - 修复 0 次

⚠️  模式: 全部成功且无需修复
    说明: 此技能过于简单，不需要 Healer
```

**解读**：需要测试更复杂的技能

---

## 🎯 后续行动

### 如果结果显示强 Healer 价值 (Ab1 vs Ab3 差异 ≥50%)
1. ✅ 实验设计有效
2. 准备竞赛简报
3. 强调 Healer 的核心贡献

### 如果结果显示弱 Healer 价值 (Ab1 vs Ab3 差异 <30%)
1. 分析：可能是简单技能，Bare Prompt 也够用
2. 测试复杂技能：
   - `jh_數學1上_FourArithmeticOperationsOfNumbers` (分数四则运算)
   - `jh_數學2上_LinearEquationsInOneVariable` (一元一次方程式)
3. 重新定义 Healer 价值范围："对复杂任务的支持"

### 如果 Ab2 和 Ab3 差异显著 (≥15%)
- 突出 AST Healer 的结构修复能力
- 分析具体修复案例

---

## ⚠️ 注意事项

1. **MASTER_SPEC 一致性**：所有 3 个 ablation 使用相同的 MASTER_SPEC，确保题目要求一致
2. **重复实验**：选择 `n` (不重新生成 MASTER_SPEC) 可以确保实验可重复
3. **API 配置**：确保 `.env` 中有正确的 `GEMINI_API_KEY`
4. **编码问题**：Windows 终端可能需要 UTF-8 编码（程序已自动处理）

---

## 📝 实验日志

实验数据会自动记录到数据库：
- 表：`skill_gen_code_log`
- 字段：`ablation_id`, `total_fixes`, `regex_fixes`, `ast_fixes`, `is_success`

可以用 SQL 查询分析：

```sql
SELECT 
    ablation_id,
    COUNT(*) as total_runs,
    SUM(CASE WHEN is_success = 1 THEN 1 ELSE 0 END) as success_count,
    AVG(total_fixes) as avg_fixes,
    AVG(regex_fixes) as avg_regex_fixes,
    AVG(ast_fixes) as avg_ast_fixes
FROM skill_gen_code_log
WHERE created_at >= date('now', '-1 day')
GROUP BY ablation_id;
```

---

## ✅ 实验检查清单

执行前确认：
- [ ] 已运行 `verify_ablation_conditions.py` 验证配置
- [ ] 所有测试技能都有 MASTER_SPEC
- [ ] `.env` 文件包含 `GEMINI_API_KEY`
- [ ] `instance/kumon_math.db` 数据库存在
- [ ] `skills/` 目录存在且可写

执行后确认：
- [ ] 生成了 12 个文件 (4 技能 × 3 ablations)
- [ ] 总结报告显示成功率差异
- [ ] 核心对比组 (Ab1 vs Ab3) 有明显差异
- [ ] 所有 Ab3 文件都能成功执行

---

**祝实验顺利！🎉**
