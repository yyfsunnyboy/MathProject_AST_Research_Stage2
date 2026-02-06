#!/usr/bin/env python
# -*- coding: utf-8 -*-
from skills.gh_ApplicationsOfDerivatives_14B_Ab3 import generate

for i in range(3):
    result = generate()
    q = result['question_text']
    print(f'【題目 {i+1}】')
    print(f'原始: {repr(q)}')
    print(f'顯示: {q}')
    
    # 檢查中文是否被包在 $ 裡
    import re
    latex_blocks = re.findall(r'\$([^$]*)\$', q)
    print(f'LaTeX 塊數: {len(latex_blocks)}')
    
    for j, block in enumerate(latex_blocks):
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', block))
        print(f'  塊 {j+1}: {block[:50]}... | 有中文? {has_chinese}')
    
    print()
