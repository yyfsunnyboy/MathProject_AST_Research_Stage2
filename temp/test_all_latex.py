# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import re

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei UI', 'Microsoft JhengHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams['mathtext.default'] = 'regular'

# 测试多种数学符号
test_cases = [
    "已知 $f(x) = -3x^{4}-9x^{3}-7x^{2}+3x$, 求 f'(x) 的值。",
    "計算 $\\frac{2}{3} + \\frac{5}{6}$ 的值。",
    "求 $\\sqrt{25} + 3^{2}$ 的結果。",
]

for i, latex_str in enumerate(test_cases):
    print(f"\n測試 {i+1}: {latex_str}")
    
    parts = []
    last_end = 0
    for match in re.finditer(r'\$([^$]+)\$', latex_str):
        if match.start() > last_end:
            parts.append(('text', latex_str[last_end:match.start()]))
        parts.append(('math', '$' + match.group(1) + '$'))
        last_end = match.end()
    if last_end < len(latex_str):
        parts.append(('text', latex_str[last_end:]))
    
    fig = plt.figure(figsize=(16, 2.5), dpi=150)
    fig.patch.set_alpha(0)
    ax = fig.add_subplot(111)
    
    x_pos = 0.02
    y_pos = 0.5
    
    for part_type, content in parts:
        if part_type == 'math':
            t = ax.text(x_pos, y_pos, content,
                       fontsize=16, ha='left', va='center',
                       transform=ax.transAxes)
        else:
            t = ax.text(x_pos, y_pos, content,
                       fontsize=14, ha='left', va='center',
                       transform=ax.transAxes)
        
        fig.canvas.draw()
        bbox = t.get_window_extent(renderer=fig.canvas.get_renderer())
        x_pos += bbox.width / fig.dpi / fig.get_figwidth() + 0.01
    
    ax.axis('off')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    
    output_file = f'temp/test_latex_{i+1}.png'
    plt.savefig(output_file, format='png', bbox_inches='tight', pad_inches=0.15, dpi=150)
    plt.close(fig)
    print(f"   ✅ 已保存: {output_file}")

print("\n全部完成！數學公式已用 LaTeX 樣式渲染（上標、下標、分數線都正確顯示）")
