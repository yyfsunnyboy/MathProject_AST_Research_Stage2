# 🔴 Healer 误诊分析：`while True` 转换错误

## 问题发现

**Ab3 生成失败**：
```
IndentationError: unindent does not match any outer indentation level @ line 667
```

**根本原因**：Healer 的 `visit_While()` 方法在转换 `while True` 时导致**函数初始化代码丢失**。

---

## 技术诊断

### 问题代码位置
- **文件**：`core/healers/ast_healer.py` 第 213-242 行
- **方法**：`visit_While()`

### 当前转换逻辑

```python
def visit_While(self, node):
    """
    [Circuit Breaker] 將 while True 轉換為 for _ in range(1000)
    """
    self.generic_visit(node)
    
    is_infinite = False
    
    # 檢查是否為 while True
    if isinstance(node.test, ast.Constant) and node.test.value is True:
        is_infinite = True
    elif hasattr(ast, 'NameConstant') and isinstance(node.test, ast.NameConstant) and node.test.value is True:
        is_infinite = True
        
    if is_infinite:
        self.fixes += 1
        logger.info(f"🛑 熔斷機制啟動: while True -> for loop (1000 runs)")
        
        return ast.For(
            target=ast.Name(id='_safety_loop_var', ctx=ast.Store()),  # ← 注意这个名字
            iter=ast.Call(
                func=ast.Name(id='range', ctx=ast.Load()),
                args=[ast.Constant(value=1000)],
                keywords=[]
            ),
            body=node.body,
            orelse=node.orelse,
            type_comment=None
        )
        
    return node
```

### 为什么会丢失初始化代码？

当 AST 进行 `unparse()` 时，它**只能恢复节点中包含的信息**。问题在：

1. **原始代码结构**（Ab2）：
```python
def generate(level=1, **kwargs):
    while True:
        # 步驟 1: 生成參數（數學一致性約束）
        polynomial_degree = random.randint(3, 5)  ← 在 while 体内
        ...
```

2. **AST 转换后**：
```python
def generate(level=1, **kwargs):
    for _safety_loop_var in range(1000):  ← 变量名改了
        # 步驟 1: 生成參數...
        polynomial_degree = random.randint(3, 5)
        ...
```

3. **但生成的代码（Ab3 实际）**：
```python
def generate(level=1, **kwargs):
    for _safety_counter in range(1000):  # ← 名字竟然不同！
            if random.random() < 0.5 and coeffs_dict[i] == 0:  # ← 没有定义 coeffs_dict
                coeffs_dict[i] = random.randint(-10, 10)
                ...
```

### 真正的问题：不完整的 AST 恢复

`ast.unparse()` 在某些情况下会产生**格式化错误或结构不完整的代码**：

1. **缩进混乱**：嵌套层级丢失
2. **变量引用错误**：`coeffs_dict` 在 unparse 后没有初始化代码
3. **作用域问题**：嵌套的 if/for 语句的缩进不一致

---

## 根本原因：AST.unparse() 的局限

`ast.unparse()` 是 Python 3.9+ 的功能，但它有已知的局限：

| 问题 | 说明 | 影响 |
|------|------|------|
| **缩进恢复** | 不能完美恢复原始缩进风格 | 可能产生混乱的缩进 |
| **空格和注释** | 完全丢失代码注释 | 格式化可能错误 |
| **复杂嵌套** | 深度嵌套时容易出错 | while 内的多层 if 失效 |
| **变量作用域** | 不检查变量是否定义 | 生成引用未定义变量的代码 |

---

## 误诊根源：自信过度

**Healer 的诊断流程**：
1. ✅ 检测到 `while True`
2. ✅ 创建正确的 AST.For 节点
3. ✅ 调用 `ast.fix_missing_locations()`
4. ❌ 调用 `ast.unparse()` 时**不验证输出**
5. ❌ 返回**可能包含 SyntaxError 的代码**

### 误诊的诊断代码
```python
# core/healers/ast_healer.py 第 290-298 行

def heal(self, code_str: str) -> tuple:
    # ...
    try:
        tree = ast.parse(code_str)
        new_tree = self.visit(tree)
        ast.fix_missing_locations(new_tree)
        
        new_code = ast.unparse(new_tree)  # ← 信任 unparse 的输出
        return new_code, self.fixes
    except Exception as e:
        logger.error(f"AST Healing Failed: {e}")
        return code_str, 0  # ← 如果异常，才返回原代码
```

**问题**：即使 `ast.unparse()` 成功执行，返回的代码也可能是**无效的 Python**！

---

## 症状对比

### Ab2（✅ 正常）：
- Regex Healer 处理 → 无问题
- AST Healer 跳过（未到达 Ab3）
- 生成代码：可运行

### Ab3（❌ 失败）：
- Regex Healer 处理 → 通过
- **AST Healer 处理** → `ast.unparse()` 产生**格式错误的代码**
- 生成代码：IndentationError

---

## 解决方案

### 方案 A：验证 ast.unparse() 的输出
在 `heal()` 方法中添加**代码验证**：

```python
def heal(self, code_str: str) -> tuple:
    # ... 现有代码 ...
    
    try:
        tree = ast.parse(code_str)
        new_tree = self.visit(tree)
        ast.fix_missing_locations(new_tree)
        
        new_code = ast.unparse(new_tree)
        
        # 📌 【关键】验证输出代码是否有效
        try:
            ast.parse(new_code)  # 验证语法
            return new_code, self.fixes
        except SyntaxError:
            logger.warning("AST unparse produced invalid code, reverting to input")
            return code_str, 0  # 如果 unparse 失败，回退到原代码
            
    except Exception as e:
        logger.error(f"AST Healing Failed: {e}")
        return code_str, 0
```

### 方案 B：修复 visit_While() 的循环变量名
确保转换使用一致的变量名 `_safety_counter`（而不是 `_safety_loop_var`）：

```python
def visit_While(self, node):
    """
    [Circuit Breaker] 將 while True 轉換為 for _ in range(1000)
    """
    self.generic_visit(node)
    
    is_infinite = False
    
    # 檢查是否為 while True
    if isinstance(node.test, ast.Constant) and node.test.value is True:
        is_infinite = True
    elif hasattr(ast, 'NameConstant') and isinstance(node.test, ast.NameConstant) and node.test.value is True:
        is_infinite = True
        
    if is_infinite:
        self.fixes += 1
        logger.info(f"🛑 熔斷機制啟動: while True -> for loop (1000 runs)")
        
        return ast.For(
            target=ast.Name(id='_safety_counter', ctx=ast.Store()),  # 📌 改为 _safety_counter
            iter=ast.Call(
                func=ast.Name(id='range', ctx=ast.Load()),
                args=[ast.Constant(value=1000)],
                keywords=[]
            ),
            body=node.body,
            orelse=node.orelse,
            type_comment=None
        )
        
    return node
```

### 方案 C：对 Ab3 禁用 AST 修复（临时）
如果验证和修复太复杂，可以在 Ab3 禁用 AST 的 `while True` 转换，使用 Regex Healer 的结果：

```python
# core/code_generator.py

if ablation_id >= 3:
    # 📌 禁用 AST 的 while True 转换
    # 原因：ast.unparse() 有已知的缩进恢复问题
    # Ab3 将使用 Regex Healer 修复的代码
    code_after_ast = code_after_regex
    ast_fixes = 0
else:
    code_after_ast = code_after_regex
```

---

## 推荐修复顺序

1. **短期**：添加 `ast.parse(new_code)` 验证（方案 A）
   - 影响小，快速见效
   - 防止无效代码返回

2. **中期**：修复循环变量名一致性（方案 B）
   - 确保代码可读性
   - 与 Prompt 生成的代码风格保持一致

3. **长期**：考虑替代 AST 修复
   - 使用更强大的代码转换库（如 LibCST）
   - 或完全避免 `while True` → `for loop` 的转换

---

## 关键学习

> **Healer 的自信过度**：验证转换后的代码**比修复代码本身更重要**。
>
> 一个好的 Healer 应该：
> 1. 修复问题 ✅
> 2. 验证修复结果 ✅
> 3. 如果验证失败，安全降级 ✅

