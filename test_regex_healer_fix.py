#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test that RegexHealer.heal() returns stats dict correctly"""

from core.healers.regex_healer import RegexHealer

r = RegexHealer()
code = "import os\nx = 1"
result = r.heal(code)

print(f"Return type: {type(result)}")
print(f"Result length: {len(result)}")

if len(result) == 2:
    code_out, stats = result
    print(f"Code output type: {type(code_out)}")
    print(f"Stats type: {type(stats)}")
    
    if isinstance(stats, dict):
        print(f"Stats dict keys: {stats.keys()}")
        print(f"regex_fix_count: {stats.get('regex_fix_count', 'NOT FOUND')}")
    else:
        print(f"Stats is not a dict: {stats}")
else:
    print(f"Unexpected return length: {len(result)}")
