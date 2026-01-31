# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei UI', 'Microsoft JhengHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams['mathtext.default'] = 'regular'

# 测试字符串
test_cases = [
    "已知 $f(x) = -3x^{5}-8x^{4}+6x^{3}-2x^{2}-6x-1$, 求 $f^{4}(x)$ 的值。",
    "計算 $\\frac{2}{3} + \\frac{5}{6}$ 的值。",
    "已知 $f(x) = -3x^{4}-9x^{3}-7x^{2}+3x$, 求 f'(x) 的值。",
]

for i, latex_str in enumerate(test_cases):
    print(f"\n測試 {i+1}: {latex_str}")
    
    fig = plt.figure(figsize=(18, 2.8), dpi=150)
    fig.patch.set_alpha(0)
    ax = fig.add_subplot(111)
    
    # 一次性渲染整個字串
    ax.text(0.02, 0.5, latex_str,
           fontsize=15,
           ha='left', va='center',
           transform=ax.transAxes,
           wrap=False)
    
    ax.axis('off')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    
    output_file = f'temp/test_fixed_{i+1}.png'
    plt.savefig(output_file, format='png', bbox_inches='tight', pad_inches=0.15, dpi=150)
    plt.close(fig)
    print(f"   ✅ 已保存: {output_file}")

print("\n完成！matplotlib 自動處理中文和數學混排，不會重疊")
