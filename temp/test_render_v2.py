# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import re

# 設定字體
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei UI', 'Microsoft JhengHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 14

# 测试字符串
latex_str = "已知 $f(x) = -5x^{7}-7x^{6}-7x^{5}-6x^{4}+7x^{3}-7x-5$, 求 f'(x) 的值。"
text_version = latex_str.replace('$', '').strip()

# 简化：将 ^{n} 转换为 ^n（去掉花括号，更易读）
text_version = re.sub(r'\^\{(\d)\}', r'^\1', text_version)

print(f"显示文字: {text_version}")

# 創建圖片
fig = plt.figure(figsize=(16, 2.2), dpi=150)
fig.patch.set_alpha(0)
ax = fig.add_subplot(111)

ax.text(0.05, 0.5, text_version, 
        fontsize=15,
        ha='left', va='center',
        transform=ax.transAxes, wrap=True,
        fontfamily='sans-serif',
        fontweight='500')

ax.axis('off')
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)

plt.savefig('temp/test_render_v2.png', format='png', bbox_inches='tight', pad_inches=0.15, dpi=150)
plt.close(fig)

print("✅ 图片已保存到 temp/test_render_v2.png")
print("   显示格式: x^7 x^6 x^5 (保留 LaTeX 风格)")
