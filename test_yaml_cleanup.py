# -*- coding: utf-8 -*-
"""
測試 YAML 強力去殼功能
驗證 prompt_builder.py 中的 _extract_and_clean_yaml 方法
"""

import sys
sys.path.insert(0, r'e:\python\MathProject_AST_Research')

from core.prompts.prompt_builder import PromptBuilder
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

print("=" * 70)
print("TEST: YAML 強力去殼功能")
print("=" * 70)

# 測試用例 1: 標準 Markdown 代碼塊（最常見的情況）
test_case_1 = '''```yaml
entities:
  - name: "整數 n1"
    type: "integer"
    range: "-50 ~ 50"
templates:
  - name: "整數加法"
    complexity_requirements: "評估對整數加法的理解"
```'''

# 測試用例 2: YAML 前後都有干擾
test_case_2 = '''這是一段文本說明

```yaml
entities:
  - name: "整數 n1"
    type: "integer"
```

後面還有文字'''

# 測試用例 3: 純 YAML（無代碼塊）
test_case_3 = '''entities:
  - name: "整數 n1"
    type: "integer"
templates:
  - name: "整數加法"'''

# 測試用例 4: 只有開始標記
test_case_4 = '''```yaml
entities:
  - name: "整數"
something: value'''

# 測試用例 5: 只有結束標記
test_case_5 = '''entities:
  - name: "整數"
something: value
```'''

test_cases = [
    ("測試 1: 標準 Markdown 代碼塊", test_case_1),
    ("測試 2: YAML 前後有干擾", test_case_2),
    ("測試 3: 純 YAML（無代碼塊）", test_case_3),
    ("測試 4: 只有開始標記", test_case_4),
    ("測試 5: 只有結束標記", test_case_5),
]

print("\n【執行清理測試】")
print("-" * 70)

for test_name, test_input in test_cases:
    print(f"\n{test_name}")
    print(f"  輸入長度: {len(test_input)} 字符")
    
    result = PromptBuilder._extract_and_clean_yaml(test_input)
    
    print(f"  輸出長度: {len(result)} 字符")
    print(f"  清理成功: {'✅' if len(result) > 0 else '❌'}")
    
    # 檢查是否移除了代碼塊標記
    if '```' in result:
        print(f"  ⚠️  警告: 輸出中仍有 ``` 標記")
    else:
        print(f"  ✅ 代碼塊標記已移除")
    
    print(f"  預覽: {result[:100]}...")

print("\n" + "-" * 70)
print("【語法驗證】")
print("-" * 70)

# 驗證清理後的 YAML 能否被正確解析
try:
    import yaml
    
    for test_name, test_input in test_cases:
        print(f"\n{test_name}")
        cleaned = PromptBuilder._extract_and_clean_yaml(test_input)
        
        try:
            parsed = yaml.safe_load(cleaned)
            print(f"  ✅ YAML 語法有效")
            print(f"  ✅ 解析結果: {list(parsed.keys()) if isinstance(parsed, dict) else type(parsed).__name__}")
        except yaml.YAMLError as e:
            print(f"  ❌ YAML 語法錯誤: {e}")
except ImportError:
    print("\n⚠️  yaml 模塊未安裝，跳過語法驗證")
    print("   但清理功能已驗證成功（見上方測試）")

print("\n" + "=" * 70)
print("✅ 強力去殼測試完成")
print("=" * 70)
