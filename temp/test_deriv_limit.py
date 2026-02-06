#!/usr/bin/env python
"""驗證微分次數限制"""
import sys
sys.path.insert(0, '.')
from skills.gh_ApplicationsOfDerivatives_14b_Ab2 import generate as gen_ab2
from skills.gh_ApplicationsOfDerivatives_14b_Ab3 import generate as gen_ab3

import re

print("驗證微分次數限制（應該最多 3 次）")
print("=" * 60)

deriv_count = {}
for trial in range(20):
    result = gen_ab2()
    # 從題目中提取導數符號
    q = result['question_text']
    matches = re.findall(r"f(\^{\((\d+)\)}|\'{1,2})", q)
    for match in matches:
        if match[1]:
            order = int(match[1])
        elif match[0] == "''" :
            order = 2
        elif match[0] == "'":
            order = 1
        else:
            continue
        deriv_count[order] = deriv_count.get(order, 0) + 1

print("Ab2 - 導數次數分布：")
for order in sorted(deriv_count.keys()):
    print(f"  f^({order})(x): {deriv_count[order]} 次")

if max(deriv_count.keys()) <= 3:
    print("✅ PASS - 所有導數次數都 ≤ 3")
else:
    print(f"❌ FAIL - 發現 {max(deriv_count.keys())} 次導數")
