# MASTER_SPEC 数据库更新逻辑完整报告

**创建日期**: 2026-01-29  
**项目**: MathProject_AST_Research (旺宏科学奖)  
**焦点**: MASTER_SPEC 生成、存储和使用的完整流程

---

## 🎯 总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     MASTER_SPEC 生命周期                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Phase 1: Architect (分析 & 设计)                               │
│  ├─ 输入: TextbookExample (课本例题)                            │
│  ├─ 处理: AI Architect 分析题型结构                             │
│  └─ 输出: MASTER_SPEC → SkillGenCodePrompt 表                  │
│          (prompt_type='MASTER_SPEC', model_tag='standard_14b')  │
│                                                                   │
│  Phase 2: Storage (持久化)                                      │
│  ├─ 表: skill_gencode_prompt                                    │
│  ├─ 关键字段: id, skill_id, prompt_content, prompt_type        │
│  └─ 标记: model_tag='standard_14b' (统一标准)                  │
│                                                                   │
│  Phase 3: Coder (使用 & 修复)                                   │
│  ├─ 读取: SkillGenCodePrompt.query.filter_by(                  │
│  │         skill_id, prompt_type='MASTER_SPEC')                │
│  ├─ 组装: BARE_MINIMAL_PROMPT + "### MASTER_SPEC:\n" + content │
│  ├─ 执行: AI Coder 根据 Prompt 生成代码                        │
│  └─ 修复: Regex Healer + AST Healer (根据 ablation_id)        │
│                                                                   │
│  Phase 4: Logging (实验记录)                                    │
│  ├─ 表: experiment_log                                          │
│  ├─ 记录: ablation_id, spec_prompt_id, use_master_spec等      │
│  └─ 用途: 追踪 MASTER_SPEC 的使用情况                         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📍 关键代码位置汇总

### 1. **SkillGenCodePrompt 表定义** 
📄 [models.py](models.py#L408-L460)

```python
class SkillGenCodePrompt(db.Model):
    __tablename__ = 'skill_gencode_prompt'
    
    # 关键字段
    id = db.Column(db.Integer, primary_key=True)
    skill_id = db.Column(db.String(50), nullable=False)
    prompt_type = db.Column(db.String(50), default='standard')  # 'MASTER_SPEC'
    prompt_content = db.Column(db.Text)  # 【MASTER_SPEC 内容存放处】
    model_tag = db.Column(db.String(50), default='default')    # 'standard_14b'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
```

**关键字段说明**:
- `prompt_content`: 完整的 MASTER_SPEC 文本（最重要！）
- `prompt_type`: 值为 `"MASTER_SPEC"` 用于标识
- `model_tag`: 值为 `"standard_14b"` 表示统一标准规格
- `created_at`: 生成时间戳，用于版本控制

---

### 2. **MASTER_SPEC 生成与写入**
📄 [core/prompt_architect.py](core/prompt_architect.py#L370-L415)

**函数**: `generate_v15_spec(skill_id, model_tag="local_14b", architect_model=None)`

#### 生成流程:
```python
def generate_v15_spec(skill_id, model_tag="local_14b", architect_model=None):
    """
    生成 MASTER_SPEC 并存入数据库
    """
    # Step 1: 读取例题
    skill = SkillInfo.query.filter_by(skill_id=skill_id).first()
    example = TextbookExample.query.filter_by(skill_id=skill_id).limit(1).first()
    
    # Step 2: 构建 Prompt
    user_prompt = f"""
    当前技能 ID: {skill_id}
    技能名称: {skill.skill_ch_name}
    
    参考例题：
    {example.problem_text}
    {example.detailed_solution}
    
    任务：请撰写一份 MASTER_SPEC...
    """
    
    # Step 3: 调用 AI Architect
    full_prompt = ARCHITECT_SYSTEM_PROMPT + user_prompt
    client = get_ai_client(role='architect')
    response = client.generate_content(full_prompt)
    spec_content = response.text
    
    # 【核心操作】Step 4: 【INSERT INTO SkillGenCodePrompt】
    new_prompt_entry = SkillGenCodePrompt(
        skill_id=skill_id,
        prompt_content=spec_content,      # ← MASTER_SPEC 内容
        prompt_type="MASTER_SPEC",        # ← 标记为 MASTER_SPEC
        system_prompt=ARCHITECT_SYSTEM_PROMPT,
        user_prompt_template=user_prompt,
        model_tag=model_tag,              # ← 通常为 'standard_14b'
        created_at=datetime.now()
    )
    
    # 【数据库写入】
    db.session.add(new_prompt_entry)      # ← INSERT
    db.session.commit()                    # ← COMMIT
    
    return {'success': True, 'spec': spec_content, 'prompt_id': new_prompt_entry.id}
```

**执行入口**:
- [scripts/prompt_factory.py](scripts/prompt_factory.py#L44-L89) - 标准化规格生成工厂
- [scripts/sync_skills_files.py](scripts/sync_skills_files.py#L176-L202) - 科研同步管理
- [scripts/ablation_bare_vs_healer.py](scripts/ablation_bare_vs_healer.py#L115-L150) - 消融实验

---

### 3. **MASTER_SPEC 读取与使用**
📄 [core/code_generator.py](core/code_generator.py#L2076)

**读取位置**:
```python
def auto_generate_skill_code(skill_id, queue=None, **kwargs):
    # 【读取 MASTER_SPEC】
    active_prompt = SkillGenCodePrompt.query.filter_by(
        skill_id=skill_id, 
        prompt_type="MASTER_SPEC"
    ).order_by(SkillGenCodePrompt.created_at.desc()).first()  # ← 读取最新的
    
    db_master_spec = active_prompt.prompt_content if active_prompt else "生成一题简单的整数四则运算。"
```

**三层 Ablation 实验设置** (lines 2055-2095):

#### Ab1 (Bare 对照组):
```python
if ablation_id == 1:
    # Ab1 (Bare): 最简 Prompt + MASTER_SPEC，无 Healer
    prompt = BARE_MINIMAL_PROMPT + f"\n\n### MASTER_SPEC:\n{db_master_spec}"
    # 【无任何修复】
    use_regex_healer = False
    use_ast_healer = False
```

#### Ab2 (MASTER_SPEC Only):
```python
elif ablation_id == 2:
    # Ab2: 完整工程化 Prompt + MASTER_SPEC，无 Healer
    prompt = UNIVERSAL_GEN_CODE_PROMPT + f"\n\n### MASTER_SPEC:\n{db_master_spec}"
    # 【无自癒修复，测试 Prompt 工程的贡献】
    use_regex_healer = False
    use_ast_healer = False
```

#### Ab3 (完整版):
```python
else:  # ablation_id == 3 (默认)
    # Ab3: 完整工程化 Prompt + MASTER_SPEC + 完整 Healer
    prompt = UNIVERSAL_GEN_CODE_PROMPT + f"\n\n### MASTER_SPEC:\n{db_master_spec}"
    # 【开启完整 Healer】
    use_regex_healer = True
    use_ast_healer = True
```

---

### 4. **Ablation Settings 配置**
📄 [models.py](models.py#L506-L512)

```python
class AblationSetting(db.Model):
    """消融实验配置表"""
    __tablename__ = 'ablation_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)      # 'Bare', 'Regex_Only', 'Full_Healing'
    use_regex = db.Column(db.Boolean, default=False)     # Regex Healer 开关
    use_ast = db.Column(db.Boolean, default=False)       # AST Healer 开关
    description = db.Column(db.Text)
```

**初始数据** (upgrade_db.py 第 63-69 行):
```python
ablation_data = [
    (1, 'Bare', 0, 0, '对照组：无任何修复机制 (Baseline)'),
    (2, 'Regex_Only', 1, 0, '实验组 A：仅开启正规表达式修复'),
    (3, 'Full_Healing', 1, 1, '实验组 B：开启 Regex + AST 完整自癒机制')
]
cursor.executemany("REPLACE INTO ablation_settings VALUES (?, ?, ?, ?, ?)", ablation_data)
```

---

### 5. **实验日志记录**
📄 [core/code_generator.py](core/code_generator.py#L1996-2045)

**表**: `experiment_log`  
📄 [models.py](models.py#L695-L737)

**关键字段** (涉及 MASTER_SPEC 的):
```python
class ExperimentLog(db.Model):
    __tablename__ = 'experiment_log'
    
    # MASTER_SPEC 相关字段
    ablation_id = db.Column(db.Integer)                  # 实验组 ID
    spec_prompt_id = db.Column(db.Integer)               # 【关键】指向 SkillGenCodePrompt.id
    use_master_spec = db.Column(db.Boolean, default=0)   # 【关键】是否使用了 MASTER_SPEC
    
    # 修复计数
    prompt_tokens = db.Column(db.Integer, default=0)     # 输入 tokens
    completion_tokens = db.Column(db.Integer, default=0) # 输出 tokens
    total_tokens = db.Column(db.Integer, default=0)
```

**写入逻辑** (code_generator.py 1996-2045):
```python
# 【INSERT INTO experiment_log】
query = """
INSERT INTO experiment_log (
    skill_id, start_time, duration_seconds, prompt_len, code_len,
    is_success, error_msg, repaired, model_name,
    model_size_class, prompt_level, raw_response, final_code,
    score_syntax, score_math, score_visual, healing_duration,
    is_executable, ablation_id, missing_imports_fixed, resource_cleanup_flag,
    prompt_tokens, completion_tokens, total_tokens,
    experiment_group, garbage_cleaner_count, eval_eliminator_count,
    sampling_success_count, sampling_total_count, spec_prompt_id, use_master_spec
) VALUES (?, ?, ?, ?, ?, ...)
"""

params = (
    skill_id, start_time, duration, prompt_len, code_len,
    ...,
    kwargs.get('ablation_id', 1),                    # ← ablation_id
    ...,
    kwargs.get('spec_prompt_id', None),              # ← 指向 MASTER_SPEC
    1 if kwargs.get('use_master_spec') else 0        # ← 使用标记
)

c.execute(query, params)
conn.commit()
```

---

## 🔄 Ab2 与 Ab3 之间的数据库更新操作

### 关键差异点

| 操作 | Ab2 (MASTER_SPEC Only) | Ab3 (Complete) |
|------|-------------------------|-----------------|
| **MASTER_SPEC 读取** | ✅ 读取相同的 `SkillGenCodePrompt` | ✅ 读取相同的 `SkillGenCodePrompt` |
| **Prompt 组装** | `UNIVERSAL_GEN_CODE_PROMPT + MASTER_SPEC` | `UNIVERSAL_GEN_CODE_PROMPT + MASTER_SPEC` |
| **Regex Healer** | ❌ 禁用 `use_regex_healer=False` | ✅ 启用 `use_regex_healer=True` |
| **AST Healer** | ❌ 禁用 `use_ast_healer=False` | ✅ 启用 `use_ast_healer=True` |
| **experiment_log** | `ablation_id=2` | `ablation_id=3` |
| **修复次数** | 0 (无修复记录) | N (根据修复次数) |
| **是否覆盖 SkillGenCodePrompt** | ❌ 不生成新记录 | ❌ 不生成新记录 |

### 执行流程

```python
# 【两个 Ablation 使用相同的 MASTER_SPEC】
active_prompt = SkillGenCodePrompt.query.filter_by(
    skill_id=skill_id, 
    prompt_type="MASTER_SPEC"
).order_by(SkillGenCodePrompt.created_at.desc()).first()
db_master_spec = active_prompt.prompt_content  # 【相同来源】

# 【组装相同的 Prompt】
prompt = UNIVERSAL_GEN_CODE_PROMPT + f"\n\n### MASTER_SPEC:\n{db_master_spec}"

# 【区别在修复阶段】
if ablation_id == 2:
    # 执行 LLM 输出，不做任何修复
    use_regex_healer = False
    use_ast_healer = False
elif ablation_id == 3:
    # 执行 LLM 输出，应用 Regex + AST 修复
    use_regex_healer = True
    use_ast_healer = True

# 【都会写入 experiment_log，但 ablation_id 不同】
log_entry = ExperimentLog(
    skill_id=skill_id,
    ablation_id=ablation_id,  # ← 2 vs 3
    use_master_spec=True,
    spec_prompt_id=active_prompt.id,
    ...
)
db.session.add(log_entry)
db.session.commit()
```

---

## 🔍 MASTER_SPEC 生成的完整流程

### Phase 1: Architect 生成规格

**触发方式**:
1. `scripts/prompt_factory.py` - 标准化工厂
2. `scripts/sync_skills_files.py` - 科研同步 (run_expert_pipeline)
3. `scripts/ablation_bare_vs_healer.py` - 消融实验准备 (ask_regenerate_prompts)

**示例**: [scripts/sync_skills_files.py](scripts/sync_skills_files.py#L285-L310)

```python
def run_expert_pipeline(skill_ids, arch_model, current_model, ablation_id, model_size_class, prompt_level):
    # 【Step 1: Architect】
    target_tag = 'standard_14b'  # ← 统一标准
    
    for skill_id in tqdm(skill_ids, desc="Phase 1 (Architect)"):
        # 生成 MASTER_SPEC (【INSERT INTO SkillGenCodePrompt】)
        result = generate_v15_spec(skill_id, model_tag=target_tag, architect_model=arch_model)
        
        if result.get('success'):
            prompt_id = result['prompt_id']  # ← 新创建的 SkillGenCodePrompt.id
    
    # 【Step 2: Coder】(使用相同的 MASTER_SPEC)
    execute_coder_phase(skill_ids, current_model, ablation_id, model_size_class, prompt_level)
```

---

### Phase 2: Coder 使用规格

**入口**: [core/code_generator.py](core/code_generator.py#L2050-L2150)

```python
def auto_generate_skill_code(skill_id, queue=None, **kwargs):
    ablation_id = kwargs.get('ablation_id', 3)
    
    # 【读取 MASTER_SPEC】
    active_prompt = SkillGenCodePrompt.query.filter_by(
        skill_id=skill_id, 
        prompt_type="MASTER_SPEC"
    ).order_by(SkillGenCodePrompt.created_at.desc()).first()
    
    db_master_spec = active_prompt.prompt_content if active_prompt else "生成一题简单的整数四则运算。"
    
    # 【三选一：Ab1/Ab2/Ab3】
    if ablation_id == 1:
        prompt = BARE_MINIMAL_PROMPT + f"\n\n### MASTER_SPEC:\n{db_master_spec}"
    elif ablation_id == 2:
        prompt = UNIVERSAL_GEN_CODE_PROMPT + f"\n\n### MASTER_SPEC:\n{db_master_spec}"
    else:  # ablation_id == 3
        prompt = UNIVERSAL_GEN_CODE_PROMPT + f"\n\n### MASTER_SPEC:\n{db_master_spec}"
    
    # 【调用 AI Coder】
    response = client.generate_content(prompt)
    raw_output = response.text
    
    # 【条件修复】
    if use_regex_healer:  # Ab2=False, Ab3=True
        # 执行 Regex 修复
        ...
    if use_ast_healer:    # Ab2=False, Ab3=True
        # 执行 AST 修复
        ...
    
    # 【记录到 experiment_log】
    # (包括 ablation_id, spec_prompt_id, use_master_spec 等)
```

---

## 📊 数据库关键操作汇总

### 写入操作 (INSERT/UPDATE)

| 位置 | 操作 | 表 | 字段 |
|------|------|-----|------|
| [core/prompt_architect.py#412](core/prompt_architect.py#L412) | **INSERT** | `SkillGenCodePrompt` | `id, skill_id, prompt_content, prompt_type, model_tag, created_at` |
| [core/code_generator.py#1996](core/code_generator.py#L1996) | **INSERT** | `experiment_log` | `skill_id, ablation_id, spec_prompt_id, use_master_spec, ...` |
| [scripts/research_runner.py#241](scripts/research_runner.py#L241) | **INSERT** | `execution_samples` | `skill_id, ablation_id, question_text, is_crash, is_logic_correct, ...` |

### 读取操作 (SELECT)

| 位置 | 查询 | 表 | 条件 |
|------|------|-----|------|
| [core/code_generator.py#2076](core/code_generator.py#L2076) | **SELECT** | `SkillGenCodePrompt` | `skill_id, prompt_type='MASTER_SPEC'` |
| [scripts/ablation_bare_vs_healer.py#93](scripts/ablation_bare_vs_healer.py#L93) | **SELECT** | `SkillGenCodePrompt` | `skill_id, prompt_type='MASTER_SPEC'` |
| [scripts/research_runner.py#161](scripts/research_runner.py#L161) | **SELECT** | `execution_samples` | `skill_id, ablation_id` |

---

## 🚀 科研实验执行流程

### 完整的 Ab2 → Ab3 对比实验

```bash
python scripts/ablation_bare_vs_healer.py
```

执行步骤:
1. **询问是否重新生成 MASTER_SPEC**
   - 调用 `generate_v15_spec()` 创建新的 `SkillGenCodePrompt`
   - 写入 `prompt_type='MASTER_SPEC'`, `model_tag='standard_14b'`

2. **Ab2 测试 (ablation_id=2)**
   ```python
   is_ok, msg, metrics = auto_generate_skill_code(
       skill_id, 
       ablation_id=2,          # ← 无 Healer
       model_size_class='14B',
       prompt_level='MASTER_SPEC_Only'
   )
   # 【无修复】-> 可能生成失败代码
   ```

3. **Ab3 测试 (ablation_id=3)**
   ```python
   is_ok, msg, metrics = auto_generate_skill_code(
       skill_id,
       ablation_id=3,          # ← 完整 Healer
       model_size_class='14B',
       prompt_level='Full_Healing'
   )
   # 【开启 Regex + AST 修复】-> 修复失败代码
   ```

4. **对比结果**
   ```
   📊 Ab2 (无 Healer):
   ❌ 生成失败: SyntaxError
   修复次数: 0
   
   📊 Ab3 (完整 Healer):
   ✅ 生成成功
   修复次数: 3 (Regex: 2, AST: 1)
   
   💡 结论: Healer 修复了 3 个错误，成功率提升 100%
   ```

---

## ⚠️ 关键注意事项

### 1. MASTER_SPEC 的唯一性
- **每个 `skill_id` 只有一份最新的 MASTER_SPEC**
- 通过 `order_by(SkillGenCodePrompt.created_at.desc()).first()` 获取最新版本
- Ab1/Ab2/Ab3 都使用**同一份** MASTER_SPEC（这是科学对照的核心）

### 2. 标准化标签
- **Ab2/Ab3 都强制使用 `model_tag='standard_14b'`**
- 这确保了不同模型大小 (7B/14B/Cloud) 面对相同难度的规格
- 避免「规格难度差异」混淆「模型能力差异」

### 3. 消融实验变因隔离
| 变因 | Ab1 | Ab2 | Ab3 |
|-----|-----|-----|-----|
| MASTER_SPEC | ✅ | ✅ | ✅ |
| Prompt 工程 | ❌ (Bare) | ✅ (Universal) | ✅ (Universal) |
| Regex Healer | ❌ | ❌ | ✅ |
| AST Healer | ❌ | ❌ | ✅ |

### 4. 修复门控逻辑
```python
# 【Ab1/Ab2 中被禁用的修复环节】
if use_regex_healer:  # ← Ab2 为 False，Ab3 为 True
    # 即使生成了错误代码也不修复
    ...
```

---

## 📈 关键指标追踪

每次代码生成都会在 `experiment_log` 记录:

```python
{
    'ablation_id': 2 or 3,              # 实验组
    'spec_prompt_id': active_prompt.id, # 指向 MASTER_SPEC
    'use_master_spec': True,            # 使用标记
    'prompt_tokens': int,               # Architect 的 tokens
    'completion_tokens': int,           # Coder 的 tokens
    'total_tokens': int,                # 总 tokens
    'is_executable': True/False,        # 是否可执行
    'healing_duration': float,          # 修复耗时
    'missing_imports_fixed': str,       # 修复内容
    ...
}
```

---

## 🔗 相关文件完整索引

### 核心模块
- **[models.py](models.py)** - 数据库 ORM 定义
  - `SkillGenCodePrompt` (L408-460)
  - `AblationSetting` (L506-512)
  - `ExperimentLog` (L695-737)
  - `ExecutionSample` (L742-774)

### 生成模块
- **[core/prompt_architect.py](core/prompt_architect.py)** - Architect 架构师
  - `generate_v15_spec()` (L370-415)

- **[core/code_generator.py](core/code_generator.py)** - Coder 工程师
  - `auto_generate_skill_code()` (L2050+)
  - MASTER_SPEC 读取 (L2076)
  - experiment_log 写入 (L1996-2045)

### 脚本工具
- **[scripts/prompt_factory.py](scripts/prompt_factory.py)** - 规格生成工厂
- **[scripts/sync_skills_files.py](scripts/sync_skills_files.py)** - 科研同步管理
- **[scripts/ablation_bare_vs_healer.py](scripts/ablation_bare_vs_healer.py)** - 消融实验
- **[scripts/research_runner.py](scripts/research_runner.py)** - 采样执行
- **[upgrade_db.py](upgrade_db.py)** - 数据库初始化

### 数据库初始化
- **[upgrade_db.py](upgrade_db.py)** - Phase 2-4 (L47-95)
  - `ablation_settings` 表创建
  - `execution_samples` 表创建

---

## ✅ 总结

MASTER_SPEC 的完整流程是:

1. **Architect 生成** → 存入 `SkillGenCodePrompt` (prompt_type='MASTER_SPEC')
2. **Ab2/Ab3 共享** → 从数据库读取同一份 MASTER_SPEC
3. **条件修复分离** → Ab2 禁用 Healer, Ab3 启用 Healer
4. **日志追踪** → 记录到 `experiment_log` (ablation_id=2/3)
5. **对比分析** → 量化 Healer 的贡献价值

**关键质控点**:
- ✅ 所有 Ablation 使用同一份 MASTER_SPEC
- ✅ 模型标签统一为 'standard_14b'
- ✅ 修复机制严格按 ablation_id 控制
- ✅ 所有实验数据完整记录到数据库

