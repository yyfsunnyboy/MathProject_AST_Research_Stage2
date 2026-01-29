# 🔍 MASTER_SPEC 数据库操作快速索引

**文档版本**: 1.0  
**创建日期**: 2026-01-29  
**适用范围**: MathProject_AST_Research 消融实验

---

## 🎯 一图看懂 MASTER_SPEC 流程

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                   MASTER_SPEC 完整生命周期                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

【Phase 1】Architect (生成规格)
────────────────────────────────────────────────────────
📚 输入: TextbookExample (课本例题)
  ↓
🧠 处理: generate_v15_spec(skill_id, model_tag='standard_14b')
  ├─ 调用 AI Architect
  ├─ 分析问题结构
  └─ 生成 MASTER_SPEC
  ↓
💾 输出: INSERT INTO SkillGenCodePrompt
  │   skill_id: 'gh_ApplicationsOfDerivatives_14b'
  │   prompt_content: '【完整 MASTER_SPEC...】'
  │   prompt_type: 'MASTER_SPEC'
  │   model_tag: 'standard_14b'  ← 统一标准！
  │   id: 42 (新创建的记录 ID)
  └─ 【共 20 个技能，生成 20 条记录】

【Phase 2a】Ab2 Experiment (无 Healer 基线)
────────────────────────────────────────────────────────
📖 读取: SELECT SkillGenCodePrompt
  │   WHERE skill_id='gh_ApplicationsOfDerivatives_14b'
  │   AND prompt_type='MASTER_SPEC'
  │   → 获取 spec_id = 42, spec_content = '...'
  ↓
🔗 组装: UNIVERSAL_GEN_CODE_PROMPT + 
         "### MASTER_SPEC:\n" + spec_content
  ↓
🤖 执行: AI Coder 生成代码 (无修复)
  │   use_regex_healer = False
  │   use_ast_healer = False
  ↓
📝 记录: INSERT INTO experiment_log
  │   ablation_id: 2
  │   spec_prompt_id: 42 ← 指向相同的 MASTER_SPEC
  │   use_master_spec: 1
  │   is_executable: 0 (预期失败)
  │   【共 20 × 5 = 100 条记录】
  └─ ⚠️ 预期成功率: 0-20%

【Phase 2b】Ab3 Experiment (完整 Healer)
────────────────────────────────────────────────────────
📖 读取: SELECT SkillGenCodePrompt
  │   WHERE skill_id='gh_ApplicationsOfDerivatives_14b'
  │   AND prompt_type='MASTER_SPEC'
  │   → 获取 spec_id = 42, spec_content = '...' (相同!)
  ↓
🔗 组装: 相同的 Prompt ✓
  ↓
🤖 执行: AI Coder 生成代码 (+ 修复)
  │   use_regex_healer = True
  │   use_ast_healer = True
  │   修复循环: Regex Clean → AST Parse → 重试
  ↓
📝 记录: INSERT INTO experiment_log
  │   ablation_id: 3
  │   spec_prompt_id: 42 ← 指向相同的 MASTER_SPEC!
  │   use_master_spec: 1
  │   is_executable: 1 (成功)
  │   healing_duration: 2.5 (修复耗时)
  │   【共 20 × 5 = 100 条记录】
  └─ ✅ 预期成功率: 80-100%

【Phase 3】Analytics (数据分析)
────────────────────────────────────────────────────────
📊 对比查询:
   SELECT * FROM experiment_log
   WHERE spec_prompt_id = 42 AND ablation_id IN (2, 3)
   
   结果:
   ┌─────────────┬──────────┬──────────┬────────┐
   │ ablation_id │ trials   │ success  │ rate   │
   ├─────────────┼──────────┼──────────┼────────┤
   │ 2 (Ab2)     │ 100      │ 0        │ 0%     │
   │ 3 (Ab3)     │ 100      │ 100      │ 100%   │
   ├─────────────┼──────────┼──────────┼────────┤
   │ 🎯 Improvement = 100% (Healer 的价值) │
   └─────────────┴──────────┴──────────┴────────┘
```

---

## 📍 关键代码快速导航

### 🔴 最重要的位置 (必读)

| 功能 | 文件 | 行号 | 关键代码 |
|------|------|------|---------|
| **生成 MASTER_SPEC** | `core/prompt_architect.py` | 370-415 | `generate_v15_spec()` |
| **写入数据库** | `core/prompt_architect.py` | 412-418 | `SkillGenCodePrompt()` + `db.session.add/commit` |
| **读取 MASTER_SPEC** | `core/code_generator.py` | 2076 | `SkillGenCodePrompt.query.filter_by(...)` |
| **三层 Ablation 配置** | `core/code_generator.py` | 2055-2100 | `if ablation_id == 1/2/3` |
| **记录实验日志** | `core/code_generator.py` | 1996-2045 | `INSERT INTO experiment_log` |
| **数据库定义** | `models.py` | 408-460, 695-737 | `class SkillGenCodePrompt`, `ExperimentLog` |

### 🟠 脚本执行入口

| 脚本 | 用途 | 调用 |
|------|------|------|
| `scripts/prompt_factory.py` | 批量生成标准规格 | `generate_v15_spec()` |
| `scripts/sync_skills_files.py` | 科研同步管理 | `run_expert_pipeline()` → Phase 1/2 |
| `scripts/ablation_bare_vs_healer.py` | 对比实验 | `auto_generate_skill_code(ablation_id=2/3)` |
| `scripts/research_runner.py` | 采样执行 | `run_research_samples()` |

### 🟡 初始化脚本

| 脚本 | 操作 | 表 |
|------|------|-----|
| `upgrade_db.py` | 创建表 + 初始化数据 | `ablation_settings`, `execution_samples` |

---

## 🎨 表结构快速参考

### SkillGenCodePrompt (规格表)

```
┌─────────────────────────────────────────────────┐
│ skill_gencode_prompt (存放 MASTER_SPEC)         │
├─────────────────────────────────────────────────┤
│ id: INTEGER PRIMARY KEY [42]                    │
│ skill_id: VARCHAR [gh_ApplicationsOfDerivatives]│
│ prompt_type: VARCHAR ['MASTER_SPEC']            │
│ prompt_content: TEXT [【完整 SPEC 内容...】]   │
│ model_tag: VARCHAR ['standard_14b'] ← 重要!   │
│ created_at: DATETIME [2026-01-29 10:15:30]      │
│ is_active: BOOLEAN [1]                          │
│ architect_model: VARCHAR ['google']             │
└─────────────────────────────────────────────────┘
```

**用途**: 存放 Architect 生成的规格书（MASTER_SPEC）

### AblationSetting (配置表)

```
┌──────────────────────────────────┐
│ ablation_settings                │
├──────────────────────────────────┤
│ id: INTEGER [1, 2, 3]            │
│ name: VARCHAR                    │
│ use_regex: BOOLEAN               │
│ use_ast: BOOLEAN                 │
├──────────────────────────────────┤
│ 1 | Bare | 0 | 0  ← 基线（无修复）│
│ 2 | Regex| 1 | 0  ← Regex 修复    │
│ 3 | Full | 1 | 1  ← 完整修复      │
└──────────────────────────────────┘
```

**用途**: 控制每个 Ablation 的修复开关

### ExperimentLog (日志表)

```
┌──────────────────────────────────────────────┐
│ experiment_log (记录每次代码生成)            │
├──────────────────────────────────────────────┤
│ id: INTEGER PRIMARY KEY (自增)               │
│ skill_id: VARCHAR                            │
│ ablation_id: INTEGER [2 or 3]                │
│ spec_prompt_id: INTEGER [指向 id=42] ← 关键 │
│ use_master_spec: BOOLEAN [1]                 │
│ is_executable: BOOLEAN [0/1]                 │
│ healing_duration: REAL [修复耗时]            │
│ prompt_tokens, completion_tokens: INTEGER    │
│ ... (更多字段)                               │
└──────────────────────────────────────────────┘
```

**用途**: 记录完整实验过程 (Ab2 100条, Ab3 100条)

---

## 💡 核心概念解析

### 1️⃣ 为什么 Ab2 和 Ab3 使用**相同**的 MASTER_SPEC?

```
【科学原理】: 对照实验变量隔离
┌─────────────────────────────────────────┐
│ 变量             │ Ab2  │ Ab3           │
├─────────────────────────────────────────┤
│ MASTER_SPEC ✓   │ 同一份 │ 同一份 ← 控制  │
│ Prompt 工程 ✓   │ 开启  │ 开启 ← 控制    │
│ Regex Healer    │ ✗    │ ✓ ← 测试      │
│ AST Healer      │ ✗    │ ✓ ← 测试      │
└─────────────────────────────────────────┘

结论: 成功率差异 = 仅由 Healer 贡献
```

### 2️⃣ model_tag='standard_14b' 的含义

```
【统一科学标准】
- 所有 Ablation (1/2/3) 都使用标签 'standard_14b'
- 所有模型大小 (7B/14B/Cloud) 都面对相同难度规格
- 防止「规格难度差异」混淆「模型能力差异」
- 确保实验结果具备可比性

【实例】
Ab2 (14B model):
  prompt = UNIVERSAL + SkillGenCodePrompt(id=42, model_tag='standard_14b')
  
Ab2 (7B model):  
  prompt = UNIVERSAL + SkillGenCodePrompt(id=42, model_tag='standard_14b') ← 相同!
  
Ab3 (14B model):
  prompt = UNIVERSAL + SkillGenCodePrompt(id=42, model_tag='standard_14b') ← 相同!
```

### 3️⃣ spec_prompt_id 的作用

```
【追踪和关联】
experiment_log.spec_prompt_id = 42
  ↓
引用 SkillGenCodePrompt[id=42]
  ↓
追踪此实验使用的具体 MASTER_SPEC 版本
  ↓
支持版本控制和回溯分析

【查询示例】
-- 找出使用 spec_id=42 的所有实验
SELECT * FROM experiment_log WHERE spec_prompt_id = 42;

-- 统计该 MASTER_SPEC 的成功率
SELECT ablation_id, COUNT(*), SUM(is_executable)
FROM experiment_log 
WHERE spec_prompt_id = 42 
GROUP BY ablation_id;
```

---

## 🚀 快速上手指南

### ✅ 【最小化执行流程】

```bash
# Step 1: 生成 MASTER_SPEC (Architect Phase)
python scripts/prompt_factory.py
# 输出: SkillGenCodePrompt 表新增 20 条记录

# Step 2: 执行 Ab2 vs Ab3 实验
python scripts/ablation_bare_vs_healer.py
# 输入: 选择是否重新生成 MASTER_SPEC
# 输出: experiment_log 新增 200 条记录 (100×Ab2 + 100×Ab3)

# Step 3: 查看结果
python -c "
from app import create_app
app = create_app()
with app.app_context():
    from models import db, ExperimentLog
    result = db.session.query(ExperimentLog.ablation_id, 
                              db.func.count('*'),
                              db.func.sum(ExperimentLog.is_executable))
    for ablation_id, count, success in result.group_by(ExperimentLog.ablation_id):
        print(f'Ab{ablation_id}: {success}/{count} = {100*success/count:.1f}%')
"
```

### ✅ 【验证 MASTER_SPEC 是否生成】

```python
from app import create_app
from models import SkillGenCodePrompt

app = create_app()
with app.app_context():
    spec = SkillGenCodePrompt.query.filter_by(
        prompt_type='MASTER_SPEC',
        model_tag='standard_14b'
    ).first()
    
    if spec:
        print(f"✅ 找到 MASTER_SPEC (id={spec.id})")
        print(f"   skill_id: {spec.skill_id}")
        print(f"   长度: {len(spec.prompt_content)} 字符")
        print(f"   创建时间: {spec.created_at}")
    else:
        print("❌ 未找到 MASTER_SPEC，需要先运行 prompt_factory.py")
```

### ✅ 【对比 Ab2 vs Ab3 结果】

```python
from app import create_app
from models import ExperimentLog
from sqlalchemy import func

app = create_app()
with app.app_context():
    query = ExperimentLog.query.filter(
        ExperimentLog.ablation_id.in_([2, 3])
    ).group_by(
        ExperimentLog.ablation_id
    ).with_entities(
        ExperimentLog.ablation_id,
        func.count('*').label('total'),
        func.sum(ExperimentLog.is_executable).label('success')
    )
    
    for ablation_id, total, success in query:
        rate = 100 * success / total if total > 0 else 0
        print(f"Ab{ablation_id}: {success}/{total} = {rate:.1f}%")
```

---

## 🔧 常见问题排查

### ❓ Q: Ab2 和 Ab3 使用的是不同的 MASTER_SPEC 吗?

```
❌ 错误! 它们使用相同的 MASTER_SPEC。
✅ 正确: 查询时都调用相同的数据库记录:
   SkillGenCodePrompt.query.filter_by(
       skill_id=X, 
       prompt_type='MASTER_SPEC'
   ).order_by(...).first()
```

### ❓ Q: experiment_log 中的 spec_prompt_id 有什么用?

```
用途: 追踪此实验使用的 MASTER_SPEC 版本
┌─────────────────────────────────────┐
│ experiment_log.spec_prompt_id = 42   │
│             ↓                         │
│ SkillGenCodePrompt[id=42]            │
│ (prompt_type='MASTER_SPEC')          │
│ (prompt_content='【SPEC 内容】')     │
└─────────────────────────────────────┘
```

### ❓ Q: 为什么要强制 model_tag='standard_14b'?

```
【科学控制】
- 隔离变量: 让 Ab2/Ab3 的差异仅来自 Healer
- 统一难度: 不同模型大小面对相同规格
- 可比性: 确保实验数据具备统计意义
```

### ❓ Q: 如果要重新生成 MASTER_SPEC 怎么办?

```
推荐做法:
1. 删除旧的 (或标记 is_active=0)
2. 生成新的 (generate_v15_spec 自动覆盖)
3. 新记录会通过 ORDER BY DESC 自动被选中

不推荐直接 UPDATE，因为会改变历史记录。
```

---

## 📈 关键指标说明

| 指标 | 含义 | Ab2 预期 | Ab3 预期 |
|------|------|---------|---------|
| `success_rate` | 代码可执行比例 | 0-20% | 80-100% |
| `healing_duration` | 修复耗时(秒) | 0 | 2-5 |
| `prompt_tokens` | 输入 token | 1200 | 1200 (相同) |
| `total_tokens` | 总 token | 2000 | 2200 |
| `is_executable` | 最终成功 | 0 | 1 |

---

## 🎓 学习路径

### 初级 (理解流程)
1. 阅读本文档的「一图看懂」
2. 查看 `ablation_bare_vs_healer.py` 的完整输出
3. 在 DB 中手动查询看结果

### 中级 (深入代码)
1. 阅读 `MASTER_SPEC_DATABASE_UPDATE_REPORT.md`
2. 跟踪 `generate_v15_spec()` 的执行
3. 理解 Ab2 vs Ab3 的 Prompt 区别

### 高级 (修改和扩展)
1. 阅读 `MASTER_SPEC_SQL_EXAMPLES.md`
2. 修改 Prompt 或修复逻辑
3. 添加新的 Ablation 配置

---

## 📞 快速参考卡

### 最常用的查询

```sql
-- 查看所有 MASTER_SPEC
SELECT id, skill_id, LENGTH(prompt_content) as len, created_at 
FROM skill_gencode_prompt 
WHERE prompt_type='MASTER_SPEC' 
ORDER BY created_at DESC;

-- 对比 Ab2 vs Ab3 成功率
SELECT ablation_id, COUNT(*), SUM(is_executable), 
       ROUND(SUM(is_executable)*100.0/COUNT(*), 1) as rate
FROM experiment_log 
WHERE ablation_id IN (2,3)
GROUP BY ablation_id;

-- 查看某个 MASTER_SPEC 的使用情况
SELECT spec_prompt_id, ablation_id, COUNT(*), SUM(is_executable)
FROM experiment_log 
WHERE spec_prompt_id IS NOT NULL
GROUP BY spec_prompt_id, ablation_id;
```

### 最常用的 Python 操作

```python
# 获取最新 MASTER_SPEC
spec = SkillGenCodePrompt.query.filter_by(
    skill_id='X', prompt_type='MASTER_SPEC'
).order_by(SkillGenCodePrompt.created_at.desc()).first()

# 统计实验结果
from sqlalchemy import func
result = ExperimentLog.query.filter_by(
    spec_prompt_id=spec.id
).group_by(ExperimentLog.ablation_id).with_entities(
    ExperimentLog.ablation_id,
    func.count('*'),
    func.sum(ExperimentLog.is_executable)
).all()
```

---

## ✨ 总结

✅ **MASTER_SPEC 是科研实验的基石**
- Architect 负责设计 (生成 MASTER_SPEC)
- Coder 负责实现 (读取 MASTER_SPEC)
- Healer 负责修复 (条件启用)

✅ **Ab2 vs Ab3 的对照是科学的**
- 使用相同的 MASTER_SPEC (控制规格难度)
- 使用相同的 Prompt 工程 (控制提示策略)
- 仅区分 Healer 开关 (隔离测试变量)

✅ **数据库记录完整和可追踪**
- `spec_prompt_id` 指向具体的 MASTER_SPEC 版本
- `ablation_id` 记录实验组别
- `experiment_log` 记录详细过程

