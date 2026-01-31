# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import re

# 設定 matplotlib
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei UI', 'Microsoft JhengHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['mathtext.fontset'] = 'stix'  # 使用 STIX 數學字體
plt.rcParams['mathtext.default'] = 'regular'

# 测试字符串
latex_str = "已知 $f(x) = -3x^{4}-9x^{3}-7x^{2}+3x$, 求 f'(x) 的值。"

print(f"原始: {latex_str}")

# 分離中文和數學式
parts = []
last_end = 0

for match in re.finditer(r'\$([^$]+)\$', latex_str):
    if match.start() > last_end:
        parts.append(('text', latex_str[last_end:match.start()]))
    parts.append(('math', '$' + match.group(1) + '$'))
    last_end = match.end()

if last_end < len(latex_str):
    parts.append(('text', latex_str[last_end:]))

print("分段:")
for i, (t, c) in enumerate(parts):
    print(f"  {i+1}. [{t}] {c}")

# 創建圖片
fig = plt.figure(figsize=(16, 2.5), dpi=150)
fig.patch.set_alpha(0)
ax = fig.add_subplot(111)

x_pos = 0.02
y_pos = 0.5

for part_type, content in parts:
    if part_type == 'math':
        t = ax.text(x_pos, y_pos, content,
                   fontsize=16,
                   ha='left', va='center',
                   transform=ax.transAxes)
    else:
        t = ax.text(x_pos, y_pos, content,
                   fontsize=14,
                   ha='left', va='center',
                   transform=ax.transAxes)
    
    fig.canvas.draw()
    bbox = t.get_window_extent(renderer=fig.canvas.get_renderer())
    x_pos += bbox.width / fig.dpi / fig.get_figwidth() + 0.01

ax.axis('off')
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)

plt.savefig('temp/test_latex.png', format='png', bbox_inches='tight', pad_inches=0.15, dpi=150)
plt.close(fig)

print("✅ LaTeX 渲染完成: temp/test_latex.png")
print("   數學式使用真正的 LaTeX 樣式（上標在上方、分數有分數線）")
