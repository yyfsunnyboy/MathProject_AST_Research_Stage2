# Regex Healer V2.8 快速参考

## 🎯 主要用途

自动修复 AI 生成代码中的两类关键性错误：
1. **重复类定义** - 移除重复的 IntegerOps, FractionOps 等类定义
2. **错误方法调用** - 修复 `ClassName.global_func()` 为 `global_func()`

## ⚡ 快速开始

```python
from core.healers.regex_healer import RegexHealer

# 1. 创建 Healer 实例
healer = RegexHealer()

# 2. 执行修复
fixed_code, stats = healer.heal(your_code)

# 3. 检查修复结果
print(f"移除重复类: {stats.get('duplicates_removed', 0)}")
print(f"修复方法调用: {stats.get('method_calls_fixed', 0)}")
```

## 🔧 V2.8 新功能

### 功能 1: 移除重复类定义

**问题示例**：
```python
class IntegerOps:
    def fmt_num(n): ...
    def random_nonzero(): ...

# ... 100 行代码 ...

class IntegerOps:  # ❌ 重复定义！
    def random_nonzero(): ...
```

**自动修复**：
```python
class IntegerOps:
    def fmt_num(n): ...
    def random_nonzero(): ...

# ... 100 行代码 ...
# (重复定义已自动移除)
```

### 功能 2: 修复错误的方法调用

**问题示例**：
```python
# fmt_num 是全局函数，不是 IntegerOps 的方法
result = IntegerOps.fmt_num(123)  # ❌ AttributeError!
```

**自动修复**：
```python
# 自动修复为直接调用全局函数
result = fmt_num(123)  # ✅ 正确！
```

## 📋 完整修复流程

```
代码输入
    ↓
Step 0   : 移除末尾垃圾 (}, python 等)
Step 0.5 : 修复括号不匹配
Step 1   : 移除 Markdown 代码块
Step 2   : 注入缺失的 import
Step 2.5 : 移除重复类定义        ⭐ V2.8 NEW
Step 2.8 : 修复错误方法调用      ⭐ V2.8 NEW
Step 3   : 修复中文符号等
Step 4   : 移除 input() 调用
    ↓
修复完成的代码 + 统计信息
```

## 📊 修复统计字段

```python
stats = {
    'regex_fix_count': 5,          # 总修复次数
    'duplicates_removed': 1,       # ⭐ 移除的重复类数量
    'method_calls_fixed': 2,       # ⭐ 修复的方法调用数量
    'imports_injected': 1,         # 注入的 import 数量
    'markdown_removed': True,      # 是否移除 Markdown
    'syntax_fixed': True,          # 是否修复语法
    'input_removed': False,        # 是否移除 input()
    'braces_fixed': False,         # 是否修复括号
}
```

## 🎓 使用场景

### 场景 1: Ab3 题目生成失败

**症状**：
```
AttributeError: type object 'IntegerOps' has no attribute 'fmt_num'
```

**解决方案**：
```python
healer = RegexHealer()
fixed_code, stats = healer.heal(ab3_code)
# ✅ 自动修复 IntegerOps.fmt_num() → fmt_num()
```

### 场景 2: 代码中有重复类定义

**症状**：
```
代码中出现多个 class IntegerOps 定义
导致方法调用混乱或失败
```

**解决方案**：
```python
healer = RegexHealer()
fixed_code, stats = healer.heal(code)
# ✅ 自动保留第一个定义，移除后续重复
```

### 场景 3: 批量修复生成的代码

**应用**：
```python
from pathlib import Path
from core.healers.regex_healer import RegexHealer

healer = RegexHealer()
skills_dir = Path('skills')

for py_file in skills_dir.glob('*Ab*.py'):
    code = py_file.read_text(encoding='utf-8')
    fixed_code, stats = healer.heal(code)
    
    if stats['regex_fix_count'] > 0:
        py_file.write_text(fixed_code, encoding='utf-8')
        print(f"✅ {py_file.name}: {stats['regex_fix_count']} 处修复")
```

## ⚙️ 配置选项

### 支持的类名
```python
# 默认检测以下类的重复定义
class_names = [
    'IntegerOps',
    'FractionOps', 
    'RadicalOps',
    'CalculusOps'
]
```

### 支持的全局函数
```python
# 默认修复以下全局函数的错误调用
global_functions = [
    'fmt_num',      # 格式化数字
    'to_latex',     # 转换为 LaTeX
    'safe_eval'     # 安全求值
]
```

## 🔍 调试与验证

### 查看详细修复日志
```python
import logging
logging.basicConfig(level=logging.INFO)

healer = RegexHealer()
fixed_code, stats = healer.heal(code)
# 输出：
#   [RegexHealer V2.8] 偵測到重複的類定義: IntegerOps (共 2 次)
#   [RegexHealer V2.8] 已移除第 2 個重複的 IntegerOps 定義
#   [RegexHealer V2.8] 修復錯誤調用: IntegerOps.fmt_num( → fmt_num( (2 處)
```

### 运行测试套件
```bash
# 测试所有 V2.8 功能
python test_healer_v2_8.py

# 预期输出：
# ✅ PASS: 移除重复类定义
# ✅ PASS: 修复错误方法调用
# ✅ PASS: 完整 heal() 流程
# 总计: 3/3 测试通过
```

## ⚠️ 注意事项

### 不会修复的情况
1. **有意的类继承或重写**（保留）
2. **在不同模块中的同名类**（不跨文件修复）
3. **真正的类方法调用**（如果方法确实在类中定义）

### 安全保证
- ✅ 只修复明确的错误模式
- ✅ 不修改正确的代码
- ✅ 保留原始代码结构和注释
- ✅ 可逆操作（可以通过 git 恢复）

## 📞 故障排查

### 问题 1: 修复后代码仍然报错

**可能原因**：
- 错误不在 Healer 的修复范围内
- 需要 AST Healer 进行更深层次的修复

**解决方案**：
```python
# 1. 先用 RegexHealer
regex_healer = RegexHealer()
code, _ = regex_healer.heal(code)

# 2. 再用 ASTHealer
from core.healers.ast_healer import ASTHealer
ast_healer = ASTHealer()
final_code = ast_healer.heal(code)
```

### 问题 2: 重复类未被移除

**检查项**：
1. 类名是否在支持列表中？
2. 是否真的是重复定义（而非继承）？
3. 查看日志确认是否检测到重复

### 问题 3: 方法调用未被修复

**检查项**：
1. 函数名是否在 global_functions 列表中？
2. 是否确实不在类中定义？
3. 调用格式是否是 `ClassName.func_name()` ？

## 🔗 相关资源

- **完整文档**: `REGEX_HEALER_V2_8_DEPLOYMENT_REPORT.md`
- **测试脚本**: `test_healer_v2_8.py`
- **核心代码**: `core/healers/regex_healer.py`
- **实际案例**: Ab3 题目生成修复

---

**版本**: V2.8  
**更新日期**: 2026-02-08  
**状态**: ✅ 生产就绪
