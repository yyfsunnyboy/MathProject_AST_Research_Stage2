# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import io

# 設定字體
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Microsoft YaHei UI', 'Microsoft JhengHei', 'DejaVu Sans', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 14

# 测试字符串（已转换上标）
test_text = "已知 f(x) = -5x⁷-7x⁶-7x⁵-6x⁴+7x³-7x-5, 求 f'(x) 的值。"

print(f"渲染文字: {test_text}")
print(f"字符检查: x⁷ x⁶ x⁵ x⁴ x³")

# 創建圖片
fig = plt.figure(figsize=(15, 2), dpi=150)
fig.patch.set_alpha(0)
ax = fig.add_subplot(111)

ax.text(0.05, 0.5, test_text, 
        fontsize=14,
        ha='left', va='center',
        transform=ax.transAxes, wrap=True,
        fontfamily='sans-serif',
        fontweight='normal')

ax.axis('off')
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)

# 保存到文件
plt.savefig('temp/test_render.png', format='png', bbox_inches='tight', pad_inches=0.15, dpi=150)
plt.close(fig)

print("✅ 图片已保存到 temp/test_render.png")
print("请打开查看上标是否正确显示")
