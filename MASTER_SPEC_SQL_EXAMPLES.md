# MASTER_SPEC 数据库操作详细示例

**创建日期**: 2026-01-29

---

## 📋 快速参考

### 表关系图

```
TextbookExample          SkillGenCodePrompt          experiment_log
    ↓                           ↓                          ↑
    └─→ Architect ──→ generate_v15_spec() ───→ INSERT/SELECT ───→
                                                     ↓
                                                 Coder ──→ auto_generate_skill_code()
                                                              ↓
                                                         INSERT exp_log
                                                              
AblationSetting (配置表)
    ↓
    └─→ ablation_id = 1/2/3 ──→ 控制 Healer 开关
```

---

## 🔧 SQL 操作详解

### 1. INSERT INTO SkillGenCodePrompt (生成 MASTER_SPEC)

**位置**: [core/prompt_architect.py#412-418](core/prompt_architect.py#L412)

**SQL 等价形式**:
```sql
-- 【Architect 生成规格时】
INSERT INTO skill_gencode_prompt (
    skill_id,
    prompt_content,
    prompt_type,
    system_prompt,
    user_prompt_template,
    model_tag,
    architect_model,
    created_at,
    is_active,
    version
) VALUES (
    'gh_ApplicationsOfDerivatives_14b',           -- skill_id
    '【MASTER_SPEC 完整内容...】',                 -- prompt_content
    'MASTER_SPEC',                                 -- prompt_type 标记
    '【ARCHITECT_SYSTEM_PROMPT...】',             -- system_prompt
    '【user_prompt...】',                         -- user_prompt_template
    'standard_14b',                                -- model_tag (统一标准)
    'google',                                      -- architect_model
    datetime('now'),                               -- created_at
    1,                                             -- is_active
    1                                              -- version
);
```

**Python ORM 形式** (实际代码):
```python
new_prompt_entry = SkillGenCodePrompt(
    skill_id='gh_ApplicationsOfDerivatives_14b',
    prompt_content=spec_content,        # AI 生成的规格
    prompt_type="MASTER_SPEC",
    system_prompt=ARCHITECT_SYSTEM_PROMPT,
    user_prompt_template=user_prompt,
    model_tag='standard_14b',           # ← 关键：统一标准标签
    architect_model='google',
    created_at=datetime.now()
)
db.session.add(new_prompt_entry)
db.session.commit()
prompt_id = new_prompt_entry.id  # 用于后续 experiment_log 关联
```

---

### 2. SELECT SkillGenCodePrompt (读取 MASTER_SPEC)

**位置**: [core/code_generator.py#2076](core/code_generator.py#L2076)

**SQL 等价形式**:
```sql
-- 【Coder 需要规格时】
SELECT 
    id, 
    skill_id,
    prompt_content,     -- ← 获取完整的 MASTER_SPEC
    model_tag,
    created_at
FROM skill_gencode_prompt
WHERE 
    skill_id = 'gh_ApplicationsOfDerivatives_14b'
    AND prompt_type = 'MASTER_SPEC'
ORDER BY created_at DESC
LIMIT 1;  -- ← 获取最新版本
```

**Python ORM 形式** (实际代码):
```python
# 【Ab2 和 Ab3 都使用这个查询】
active_prompt = SkillGenCodePrompt.query.filter_by(
    skill_id='gh_ApplicationsOfDerivatives_14b',
    prompt_type="MASTER_SPEC"
).order_by(SkillGenCodePrompt.created_at.desc()).first()

if active_prompt:
    spec_id = active_prompt.id                    # ← 记录 ID
    spec_content = active_prompt.prompt_content   # ← 获取内容
    model_tag = active_prompt.model_tag           # ← 'standard_14b'
else:
    spec_content = "生成一题简单的整数四则运算。"  # 默认值
```

**返回数据示例**:
```python
{
    'id': 42,
    'skill_id': 'gh_ApplicationsOfDerivatives_14b',
    'prompt_content': '''
    domain: algebra.calculus
    
    entities:
      - function: polynomial or exponential
        constraints: differentiable, real-valued
      
      - point: real number
        constraints: within domain of f
    
    operators: [+, -, *, /, derivative, power]
    
    templates:
      - name: "Find Critical Points"
        complexity_requirements: |
          - 必须包含二阶导数
          - 必须使用链式法则
        ...
    ''',
    'model_tag': 'standard_14b',
    'created_at': '2026-01-29 10:15:30'
}
```

---

### 3. INSERT INTO experiment_log (记录实验)

**位置**: [core/code_generator.py#1996-2045](core/code_generator.py#L1996)

#### Ab2 的 INSERT

```sql
-- 【Ab2: 无 Healer 的实验记录】
INSERT INTO experiment_log (
    skill_id,
    start_time,
    duration_seconds,
    prompt_len,
    code_len,
    is_success,
    error_msg,
    repaired,
    model_name,
    model_size_class,
    prompt_level,
    raw_response,
    final_code,
    score_syntax,
    score_math,
    score_visual,
    healing_duration,
    is_executable,
    ablation_id,              -- ← 关键：2
    missing_imports_fixed,
    resource_cleanup_flag,
    prompt_tokens,
    completion_tokens,
    total_tokens,
    experiment_group,
    garbage_cleaner_count,
    eval_eliminator_count,
    sampling_success_count,
    sampling_total_count,
    spec_prompt_id,           -- ← 指向 SkillGenCodePrompt.id (42)
    use_master_spec           -- ← 使用标记: 1
) VALUES (
    'gh_ApplicationsOfDerivatives_14b',
    1706459400.5,
    12.35,
    1250,                     -- UNIVERSAL_GEN_CODE_PROMPT 长度
    542,
    0,                        -- is_success: 生成失败（Ab2 无 Healer）
    'SyntaxError: unexpected indent at line 15',
    0,                        -- repaired: 没有修复
    'gemini-1.5-flash',
    '14B',
    'MASTER_SPEC_Only',
    '【LLM 原始输出（包含错误）】',
    NULL,                     -- final_code: 无（未修复）
    0.0,
    0.0,
    0.0,
    0.0,                      -- healing_duration: 0（无修复）
    0,                        -- is_executable: 0（失败）
    2,                        -- ← ablation_id: 2
    '',
    0,
    1250,
    850,
    2100,
    'A2',
    0,
    0,
    0,
    0,
    42,                       -- ← spec_prompt_id: 指向 MASTER_SPEC
    1                         -- ← use_master_spec: 1
);
```

#### Ab3 的 INSERT

```sql
-- 【Ab3: 完整 Healer 的实验记录】
INSERT INTO experiment_log (
    skill_id,
    start_time,
    duration_seconds,
    prompt_len,
    code_len,
    is_success,
    error_msg,
    repaired,
    model_name,
    model_size_class,
    prompt_level,
    raw_response,
    final_code,
    score_syntax,
    score_math,
    score_visual,
    healing_duration,
    is_executable,
    ablation_id,              -- ← 关键：3
    missing_imports_fixed,
    resource_cleanup_flag,
    prompt_tokens,
    completion_tokens,
    total_tokens,
    experiment_group,
    garbage_cleaner_count,
    eval_eliminator_count,
    sampling_success_count,
    sampling_total_count,
    spec_prompt_id,           -- ← 指向相同的 SkillGenCodePrompt.id (42)
    use_master_spec           -- ← 使用标记: 1
) VALUES (
    'gh_ApplicationsOfDerivatives_14b',
    1706459415.2,            -- 稍后开始
    14.82,                   -- 稍长（修复耗时）
    1250,                    -- 相同的 Prompt 长度
    542,
    1,                       -- is_success: 生成成功（修复后）
    '',                      -- error_msg: 空
    1,                       -- repaired: 1（已修复）
    'gemini-1.5-flash',
    '14B',
    'Full_Healing',
    '【LLM 原始输出（包含错误）】',
    '【修复后的正确代码】',   -- final_code: 有修复后的代码
    1.0,
    0.95,
    0.9,
    2.47,                    -- healing_duration: 修复耗时
    1,                       -- is_executable: 1（成功）
    3,                       -- ← ablation_id: 3
    'matplotlib,numpy',      -- missing_imports_fixed
    1,                       -- resource_cleanup_flag
    1250,
    950,                     -- 额外的修复 token
    2200,
    'A3',
    2,                       -- 修复计数
    1,                       -- 修复计数
    1,
    1,
    42,                      -- ← spec_prompt_id: 指向相同的 MASTER_SPEC (42)
    1                        -- ← use_master_spec: 1
);
```

**对比分析 (SQL)**:
```sql
-- 比较 Ab2 vs Ab3 的实验结果
SELECT 
    ablation_id,
    COUNT(*) as total_runs,
    SUM(is_success) as success_count,
    ROUND(SUM(is_success) * 100.0 / COUNT(*), 2) as success_rate,
    AVG(duration_seconds) as avg_duration,
    SUM(missing_imports_fixed != '') as fixed_imports_count,
    AVG(prompt_tokens) as avg_prompt_tokens
FROM experiment_log
WHERE 
    skill_id = 'gh_ApplicationsOfDerivatives_14b'
    AND spec_prompt_id = 42        -- ← 相同的 MASTER_SPEC
    AND ablation_id IN (2, 3)      -- ← Ab2 vs Ab3
GROUP BY ablation_id
ORDER BY ablation_id;

-- 预期结果:
-- ablation_id | total_runs | success_count | success_rate | avg_duration | fixed_imports_count | avg_prompt_tokens
-- 2           | 5          | 0             | 0.00         | 12.5         | 0                   | 1250
-- 3           | 5          | 5             | 100.00       | 14.8         | 2                   | 1250
```

---

### 4. UPDATE SkillGenCodePrompt (版本管理)

**场景**: 更新 MASTER_SPEC 内容（重新生成）

```sql
-- 【不推荐：直接 UPDATE】
UPDATE skill_gencode_prompt
SET 
    prompt_content = '【新的 MASTER_SPEC 内容】',
    version = version + 1,
    created_at = datetime('now')
WHERE 
    skill_id = 'gh_ApplicationsOfDerivatives_14b'
    AND prompt_type = 'MASTER_SPEC'
    AND is_active = 1;

-- 【推荐：插入新版本，标记旧版本为非活跃】
-- Step 1: 标记旧版本
UPDATE skill_gencode_prompt
SET is_active = 0
WHERE 
    skill_id = 'gh_ApplicationsOfDerivatives_14b'
    AND prompt_type = 'MASTER_SPEC'
    AND is_active = 1;

-- Step 2: 插入新版本
INSERT INTO skill_gencode_prompt (...) VALUES (...);
```

**Python 实现** (generate_v15_spec):
```python
# 自动覆盖策略：新 INSERT 会被查询时通过 ORDER BY DESC 自动选中
new_prompt_entry = SkillGenCodePrompt(
    skill_id=skill_id,
    prompt_content=spec_content,  # ← 新内容
    prompt_type="MASTER_SPEC",
    created_at=datetime.now()
)
db.session.add(new_prompt_entry)
db.session.commit()
# 查询时自动获取最新的：
# .order_by(SkillGenCodePrompt.created_at.desc()).first()
```

---

## 📊 实验数据查询示例

### 1. 查询特定技能的所有 MASTER_SPEC 版本

```sql
SELECT 
    id,
    skill_id,
    prompt_type,
    model_tag,
    created_at,
    LENGTH(prompt_content) as spec_length,
    is_active
FROM skill_gencode_prompt
WHERE 
    skill_id = 'gh_ApplicationsOfDerivatives_14b'
    AND prompt_type = 'MASTER_SPEC'
ORDER BY created_at DESC;
```

**预期结果**:
```
id | skill_id | prompt_type | model_tag | created_at | spec_length | is_active
43 | gh_ApplicationsOfDerivatives_14b | MASTER_SPEC | standard_14b | 2026-01-29 11:30:45 | 3521 | 1
42 | gh_ApplicationsOfDerivatives_14b | MASTER_SPEC | standard_14b | 2026-01-29 10:15:30 | 3450 | 1
41 | gh_ApplicationsOfDerivatives_14b | MASTER_SPEC | standard_14b | 2026-01-29 09:00:00 | 3400 | 1
```

### 2. 查询 Ab2 vs Ab3 的成功率对比

```sql
SELECT 
    ablation_id,
    CASE ablation_id
        WHEN 2 THEN 'Ab2 (MASTER_SPEC Only, No Healer)'
        WHEN 3 THEN 'Ab3 (Full Healing)'
    END as experiment_name,
    COUNT(*) as total_tests,
    SUM(CASE WHEN is_executable = 1 THEN 1 ELSE 0 END) as success_count,
    ROUND(SUM(CASE WHEN is_executable = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate_percent,
    AVG(healing_duration) as avg_healing_time,
    MAX(healing_duration) as max_healing_time,
    SUM(CASE WHEN missing_imports_fixed != '' THEN 1 ELSE 0 END) as import_fixes_needed
FROM experiment_log
WHERE 
    skill_id = 'gh_ApplicationsOfDerivatives_14b'
    AND ablation_id IN (2, 3)
    AND spec_prompt_id = 42  -- ← 相同 MASTER_SPEC
GROUP BY ablation_id
ORDER BY ablation_id;
```

**预期结果**:
```
ablation_id | experiment_name | total_tests | success_count | success_rate_percent | avg_healing_time | max_healing_time | import_fixes_needed
2           | Ab2 (MASTER_SPEC Only, No Healer) | 10 | 0 | 0.00 | 0.0 | 0.0 | 0
3           | Ab3 (Full Healing) | 10 | 10 | 100.00 | 2.15 | 3.45 | 7
```

### 3. 追踪特定 MASTER_SPEC 的使用情况

```sql
SELECT 
    e.ablation_id,
    e.model_size_class,
    COUNT(*) as usage_count,
    SUM(e.is_executable) as success_count,
    ROUND(AVG(e.prompt_tokens + e.completion_tokens), 0) as avg_total_tokens,
    p.created_at as spec_created_at,
    p.model_tag as spec_model_tag
FROM experiment_log e
LEFT JOIN skill_gencode_prompt p ON e.spec_prompt_id = p.id
WHERE 
    e.spec_prompt_id IS NOT NULL
    AND e.use_master_spec = 1
GROUP BY e.ablation_id, e.model_size_class
ORDER BY e.ablation_id, usage_count DESC;
```

---

## 🔐 关键 SQL 约束

### 外键关系

```sql
-- experiment_log 的 spec_prompt_id 外键约束
ALTER TABLE experiment_log
ADD CONSTRAINT fk_spec_prompt
FOREIGN KEY (spec_prompt_id) 
REFERENCES skill_gencode_prompt(id);

-- 删除 MASTER_SPEC 时的级联影响
ON DELETE SET NULL  -- 实验记录保留但失去引用
```

### 唯一性约束

```sql
-- 同一 skill_id 的 MASTER_SPEC 只有一份「活跃」
CREATE UNIQUE INDEX idx_active_master_spec 
ON skill_gencode_prompt(skill_id, prompt_type) 
WHERE is_active = 1 AND prompt_type = 'MASTER_SPEC';
```

---

## 🎯 完整数据流示例

### 场景：为 3 个 Ablation 的 20 个技能生成数据

#### Step 1: 生成 MASTER_SPEC

```python
# [Phase 1: Architect]
for skill_id in SELECTED_20_SKILLS:
    result = generate_v15_spec(skill_id, model_tag='standard_14b')
    # INSERT INTO skill_gencode_prompt VALUES (
    #     ..., skill_id, 'MASTER_SPEC', spec_content, ...
    # )
    # 返回: prompt_id
```

**SQL 结果**:
```
skill_gencode_prompt 表新增 20 条记录 (id: 101-120)
每个 skill 一条最新的 MASTER_SPEC 记录
```

#### Step 2: 执行 Ab2 测试

```python
for skill_id in SELECTED_20_SKILLS:
    for trial in range(5):  # 5 次试验
        # 【读取 MASTER_SPEC】
        active_prompt = SkillGenCodePrompt.query.filter_by(
            skill_id=skill_id, prompt_type='MASTER_SPEC'
        ).first()
        spec_id = active_prompt.id
        
        # 【执行 Ab2 (无 Healer)】
        is_ok, msg, metrics = auto_generate_skill_code(
            skill_id, 
            ablation_id=2,
            # ... 其他参数
        )
        
        # 【记录到 experiment_log】
        # INSERT INTO experiment_log VALUES (
        #     skill_id, ablation_id=2, spec_prompt_id=spec_id, 
        #     is_executable=is_ok, ...
        # )
```

**SQL 结果**:
```
experiment_log 表新增 20 × 5 = 100 条记录 (ablation_id=2)
spec_prompt_id 指向 skill_gencode_prompt 的 id (101-120)
```

#### Step 3: 执行 Ab3 测试

```python
# 相同逻辑，但 ablation_id=3
# 【关键】spec_prompt_id 指向相同的 MASTER_SPEC
for skill_id in SELECTED_20_SKILLS:
    for trial in range(5):
        # 【读取相同的 MASTER_SPEC】
        active_prompt = SkillGenCodePrompt.query.filter_by(
            skill_id=skill_id, prompt_type='MASTER_SPEC'
        ).first()
        spec_id = active_prompt.id  # ← 相同
        
        # 【执行 Ab3 (完整 Healer)】
        is_ok, msg, metrics = auto_generate_skill_code(
            skill_id,
            ablation_id=3,
            # ... 其他参数
        )
        
        # 【记录到 experiment_log】
        # INSERT INTO experiment_log VALUES (
        #     skill_id, ablation_id=3, spec_prompt_id=spec_id,  ← 相同
        #     is_executable=is_ok, ...
        # )
```

**SQL 结果**:
```
experiment_log 表新增 20 × 5 = 100 条记录 (ablation_id=3)
所有记录的 spec_prompt_id 与 Ab2 指向相同的 MASTER_SPEC (id: 101-120)
```

#### Step 4: 对比分析

```sql
-- 【最终对比查询】
SELECT 
    skill_gencode_prompt.skill_id,
    ab2.success_rate as ab2_success_rate,
    ab3.success_rate as ab3_success_rate,
    (ab3.success_rate - ab2.success_rate) as improvement_percent,
    skill_gencode_prompt.id as spec_id
FROM skill_gencode_prompt
LEFT JOIN (
    SELECT 
        spec_prompt_id,
        ROUND(SUM(is_executable) * 100.0 / COUNT(*), 2) as success_rate
    FROM experiment_log
    WHERE ablation_id = 2
    GROUP BY spec_prompt_id
) ab2 ON skill_gencode_prompt.id = ab2.spec_prompt_id
LEFT JOIN (
    SELECT 
        spec_prompt_id,
        ROUND(SUM(is_executable) * 100.0 / COUNT(*), 2) as success_rate
    FROM experiment_log
    WHERE ablation_id = 3
    GROUP BY spec_prompt_id
) ab3 ON skill_gencode_prompt.id = ab3.spec_prompt_id
WHERE skill_gencode_prompt.prompt_type = 'MASTER_SPEC'
ORDER BY improvement_percent DESC;

-- 预期结果：
-- skill_id | ab2_success_rate | ab3_success_rate | improvement_percent | spec_id
-- gh_ApplicationsOfDerivatives_14b | 0.00 | 100.00 | 100.00 | 101
-- ... (其他 19 个技能)
```

---

## 📝 常见操作查询

### 检查 MASTER_SPEC 是否存在

```python
def check_master_spec_exists(skill_id):
    spec = SkillGenCodePrompt.query.filter_by(
        skill_id=skill_id,
        prompt_type='MASTER_SPEC',
        is_active=True
    ).first()
    return spec is not None, spec.id if spec else None
```

### 获取 MASTER_SPEC 内容

```python
def get_master_spec_content(skill_id):
    spec = SkillGenCodePrompt.query.filter_by(
        skill_id=skill_id,
        prompt_type='MASTER_SPEC'
    ).order_by(SkillGenCodePrompt.created_at.desc()).first()
    
    return spec.prompt_content if spec else None
```

### 统计 MASTER_SPEC 使用次数

```python
def count_master_spec_usage(spec_prompt_id):
    return db.session.query(ExperimentLog).filter_by(
        spec_prompt_id=spec_prompt_id
    ).count()
```

---

## ✅ 验证清单

生成 MASTER_SPEC 后，检查:

- [ ] `SkillGenCodePrompt` 表有新记录
- [ ] `prompt_type = 'MASTER_SPEC'`
- [ ] `model_tag = 'standard_14b'`
- [ ] `prompt_content` 非空且长度 > 500 字符
- [ ] `created_at` 是最新时间戳

Ab2/Ab3 实验后，检查:

- [ ] `experiment_log` 有相应 ablation_id 的记录
- [ ] `spec_prompt_id` 指向正确的 `SkillGenCodePrompt.id`
- [ ] `use_master_spec = 1`
- [ ] Ab2: `is_executable` 较低（0-20%）
- [ ] Ab3: `is_executable` 较高（80-100%）
- [ ] Ab3 的 `healing_duration` > 0

