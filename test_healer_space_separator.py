#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test Healer's space separator fix for answers"""

from core.healers.regex_healer import RegexHealer

# Test cases (simulate AI-generated incorrect code)
test_cases = [
    {
        "name": "Comma separator",
        "code": "a = ', '.join(answers)\n"
    },
    {
        "name": "Space separator (single quote)",
        "code": "a = ' '.join(answers)\n"
    },
    {
        "name": "Space separator (double quote)",
        "code": 'a = " ".join(answers)\n'
    },
]

healer = RegexHealer()

print("=" * 70)
print("Healer Space Separator Fix Test")
print("=" * 70)

for test in test_cases:
    print(f"\n【{test['name']}】")
    print(f"Original: {test['code'].strip()}")
    
    fixed, fixes = healer._fix_answer_format(test['code'])
    
    print(f"Fixed:    {fixed.strip()}")
    print(f"Fix count: {fixes}")
    
    # Check if fixed to newline separator
    has_newline = r"'\n'" in fixed or '"\n"' in fixed
    if has_newline and 'join' in fixed:
        print("✅ Fixed to newline separator")
    else:
        print("Status: Check above")

print("\n" + "=" * 70)
