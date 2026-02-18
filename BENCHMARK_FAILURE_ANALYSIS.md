# Benchmark 失败原因分析与修正报告

## 问题诊断

### Benchmark 结果分析
```
Example 2/9: [integers_L1_ab2] Ab:Ab2
[Scoring] Program: 24.50/50 | Math: 0.00/50 | Total: 24.50/100

Example 6/9: [integers_L2_ab3] Ab:Ab3
[ERROR] temp_gen_07ee5d44.py 缺少 generate() 函數
 -> Load Failed (Score: 0)

Example 8/9: [integers_L3_ab2] Ab:Ab2
[ERROR] temp_gen_4bae76a5.py 缺少 generate() 函數
 -> Load Failed (Score: 0)
```

**核心问题**：Ab2 和 Ab3 的 AI **自己实现了 IntegerOps 类**，然后忘记写 generate() 函数。

---

## 根本原因

### SKILL.md 表述差异

| 单元 | 原表述 | AI 理解 | 结果 |
|------|--------|---------|------|
| 根式 | "嚴禁寫任何 import 語句！系統已注入 RadicalOps" | 不能 import，直接用 API | ✅ 正常工作 |
| 整数/分数 | "系統已注入輔助 API（推薦使用）" | 可选功能，我可以自己实现 | ❌ 自己写类 |

### 错误的 AI 理解过程

**AI 的推理**：
1. "系統已注入 API（推薦使用）" → 这是推荐，不是必须
2. "你也可以不使用 API" → 那我自己实现更好
3. 开始写 `class IntegerOps:` ...
4. 写完 IntegerOps 后，忘记写 generate() 函数
5. 代码提交，缺少 generate()，加载失败

**证据**：
```
Example 6/9: [integers_L2_ab3]
🔍 [Pre-Heal] Code: import random from fractions import Fraction  
class IntegerOps:     @staticmethod     def fmt_num(n)...
[ERROR] temp_gen_07ee5d44.py 缺少 generate() 函數
```

---

## 修正方案

### 1. 强化【第一優先規則】

**修正前** ❌:
```markdown
【第一優先規則】只能 import random 和 from fractions import Fraction！其他模組嚴禁 import！
```

**修正后** ✅:
```markdown
【第一優先規則】
- 只能 import random 和 from fractions import Fraction！
- **嚴禁定義任何類（class）**！只寫 generate() 和 check() 兩個函式！
- 系統已注入 IntegerOps，直接用 IntegerOps.xxx() 即可！
```

**改进点**：
- ✅ 明确禁止定义类
- ✅ 强调只写两个函数
- ✅ 说明系统已注入，直接用

---

### 2. 重写【核心規則】说明

**修正前** ❌:
```markdown
1. **系統已注入輔助 API（推薦使用）**：
   ...
   ⚠️ 你也可以不使用 API，但必須確保程式碼正確
```

**修正后** ✅:
```markdown
1. **系統已注入 IntegerOps API，直接調用（嚴禁自己定義）**：
   
   使用範例：
   ```python
   import random  # 只 import 這兩個
   from fractions import Fraction
   
   def generate(level=1, **kwargs):  # 直接寫函式，不要先定義類
       a = IntegerOps.random_nonzero(-20, 20)  # 直接調用
   ```
   
   ⚠️ **絕對禁止**：
   - ❌ 自己寫 `class IntegerOps` → 浪費時間且會導致缺少 generate()！
   - ❌ 寫 `def fmt_num(...)` 等輔助函式 → 不需要，直接用 API！
   - ✅ 如果不想用 API，可以手動寫邏輯，但須確保正確
```

**改进点**：
- ✅ 改"推薦使用"为"直接調用（嚴禁自己定義）"
- ✅ 示例代码展示"直接寫函式，不要先定義類"
- ✅ **絕對禁止**部分明确后果："會導致缺少 generate()！"
- ✅ 保留灵活性："如果不想用 API，可以手動寫"

---

### 3. 增强【常見錯誤警告】

**修正前** ❌:
```markdown
【常見錯誤警告】
❌ 忘記確保除法整除 → 會產生小數答案
❌ 負數沒用括號 → LaTeX 顯示錯誤
```

**修正后** ✅:
```markdown
【常見錯誤警告】
❌ **自己定義 IntegerOps 類** → 浪費時間且會導致缺少 generate() 函數！
❌ 忘記確保除法整除 → 會產生小數答案
❌ 負數沒用括號 → LaTeX 顯示錯誤
```

**改进点**：
- ✅ 把最严重的错误放在第一位
- ✅ 加粗强调
- ✅ 明确后果

---

### 4. 修正【程式要求】

**修正前** ❌:
```markdown
1. 請寫成兩個函式：
   - def generate(level=1, **kwargs): 生成題目
   - def check(user_answer, correct_answer): 檢查答案
```

**修正后** ✅:
```markdown
1. ⚠️ **只需寫兩個函式（不要定義其他類）**：
   - def generate(level=1, **kwargs): 生成題目
   - def check(user_answer, correct_answer): 檢查答案
```

**改进点**：
- ✅ 强调"只需"和"不要定義其他類"
- ✅ 加 ⚠️ 警告符号

---

## 对比：根式单元的优秀设计

### 根式单元为什么表现好？

**1. 第一行就明确禁止**：
```markdown
【第一優先規則】嚴禁寫任何 import 語句！系統已注入 RadicalOps，直接用 RadicalOps.xxx()。
```

**2. API 文档标题就强调**：
```markdown
【系統已注入的輔助函式（API）】（嚴禁重新定義，直接調用）
```

**3. 错误警告直接威胁**：
```markdown
❌ 自己寫 import random → 嚴禁！系統已注入
❌ 不使用 RadicalOps API → 直接 0 分
```

**4. 检查清单确认**：
```markdown
✅ 無 import 語句（系統已注入）
✅ 只使用 RadicalOps API，無自寫邏輯
```

**关键差异总结**：

| 方面 | 根式单元 | 整数/分数单元（修正前） | 整数/分数单元（修正后） |
|------|---------|----------------------|----------------------|
| **禁止定义类** | ✅ 隐含（禁 import） | ❌ 未明确 | ✅ 明确禁止 |
| **API 强制性** | ✅ "直接用" | ⚠️ "推薦使用" | ✅ "直接調用（嚴禁定義）" |
| **后果说明** | ✅ "直接 0 分" | ❌ 无 | ✅ "會導致缺少 generate()" |
| **示例代码** | ✅ 只有函数 | ⚠️ 未强调 | ✅ "直接寫函式，不要先定義類" |

---

## 修正后的预期效果

### 修正内容总结

✅ **整数单元** (jh_數學1上_FourArithmeticOperationsOfIntegers/SKILL.md)
- 第一優先規則：加入"嚴禁定義任何類"
- 核心規則：改"推薦使用"为"直接調用（嚴禁自己定義）"
- 常見錯誤：新增"自己定義 IntegerOps 類"警告
- 程式要求：强调"只需寫兩個函式（不要定義其他類）"

✅ **分数单元** (jh_數學1上_FourArithmeticOperationsOfNumbers/SKILL.md)
- 同步应用所有修正

✅ **根式单元** (jh_數學2上_FourOperationsOfRadicals/SKILL.md)
- 保持不变（原设计已经很好）

---

### 重新测试预期

**Ab1 (Bare Prompt)**:
- 预期：60~75%（无变化，不提供 API）

**Ab2 (Scaffold + Regex)**:
- **修正前**：24.5/100 ❌ (AI 自己写 IntegerOps 类)
- **修正后预期**：80~95% ✅ (AI 正确使用 API)

**Ab3 (Full AST Healer)**:
- **修正前**：0/100 (缺少 generate()) 或 91.2/100（如果没自己写类）
- **修正后预期**：85~95% ✅ (稳定使用 API + AST 修复)

---

## 验证建议

### 1. 快速验证
```powershell
# 运行整数单元测试 (Level 1 即可快速验证)
python agent_tools/benchmark.py

# 选择：
# [1] 整数四則運算
# 选择模型（建议用 Gemini 2.5 Flash）
```

### 2. 观察重点
- **Ab2 是否还会自己定义 IntegerOps？**
  - 查看日志：`[Pre-Heal] Code: ...`
  - 应该看到：`def generate(level=1` 而不是 `class IntegerOps:`

- **Ab2 分数是否提升？**
  - 目标：从 24.5 提升到 80+ 分

- **Ab3 是否不再缺少 generate()？**
  - 应该看到成功执行，而不是 `[ERROR] 缺少 generate() 函數`

### 3. 对比分析
```
修正前：
Ab1: 10.5 → Ab2: 24.5 → Ab3: 91.2 (不稳定，有时 0 分)
问题：Ab2 性能差，Ab3 不稳定

修正后预期：
Ab1: 60~70 → Ab2: 80~90 → Ab3: 85~95
趋势：Ab2 显著提升，Ab3 稳定性提升
```

---

## 核心设计教训

### ✅ 好的 Prompt 设计
1. **第一句话就说清楚最重要的事**
   - ❌ 埋在文档中间
   - ✅ "【第一優先規則】嚴禁定義任何類！"

2. **明确禁止比建议更有效**
   - ❌ "推薦使用 API"
   - ✅ "直接調用（嚴禁自己定義）"

3. **说明后果比说明规则更有效**
   - ❌ "不要自己写类"
   - ✅ "自己写類會導致缺少 generate() 函數！"

4. **示例代码要展示正确路径**
   - ❌ 只展示 API 使用
   - ✅ 展示完整结构："直接寫函式，不要先定義類"

5. **保持灵活性但设置护栏**
   - ❌ "必须使用 API"（过于严格）
   - ✅ "推薦用 API，如不用須手動確保正確"（有护栏的灵活）

---

## 总结

**问题本质**：AI 误解了"推薦使用"，认为可以自己实现 IntegerOps，导致浪费 token 写类，最后忘记写 generate()。

**解决方案**：参考根式单元的严格设计，在多个位置强调：
1. 第一優先規則：嚴禁定義類
2. 核心規則：直接調用（嚴禁自己定義）
3. 常見錯誤：警告后果
4. 示例代码：展示正确结构

**预期效果**：Ab2 从 24.5 分提升到 80+ 分，Ab3 稳定在 85~95 分。

---

**日期**：2026-02-18  
**状态**：✅ 已修正，等待验证
