import matplotlib.pyplot as plt
import io

# 測試 Matplotlib 的 bbox_inches 行為
latex_str = r'(2x + 1)(x + 1)^{2}  \quad  P(2, 45)'

fig = plt.figure(figsize=(10, 1.8), dpi=100)
fig.patch.set_alpha(0)

ax = fig.add_subplot(111)
ax.text(0.5, 0.5, f"${latex_str}$", 
        fontsize=11, ha='center', va='center',
        transform=ax.transAxes)
ax.axis('off')

# 第一次嘗試：使用 bbox_inches='tight'
buf1 = io.BytesIO()
plt.savefig(buf1, format='png', bbox_inches='tight', pad_inches=0.15, dpi=100)
buf1.seek(0)

print(f'使用 bbox_inches="tight": {len(buf1.getvalue())} 字節')

# 第二次嘗試：不用 bbox_inches
buf2 = io.BytesIO()
plt.savefig(buf2, format='png', dpi=100)
buf2.seek(0)

print(f'不用 bbox_inches: {len(buf2.getvalue())} 字節')

# 第三次嘗試：用 bbox_inches 但不透明
fig.patch.set_alpha(1)
buf3 = io.BytesIO()
plt.savefig(buf3, format='png', bbox_inches='tight', pad_inches=0.15, dpi=100)
buf3.seek(0)

print(f'不透明 + bbox_inches="tight": {len(buf3.getvalue())} 字節')

plt.close(fig)

# 分析第一個圖片
from PIL import Image
buf1.seek(0)
img = Image.open(buf1)
print(f'\n圖片 1 大小: {img.size}')

# 檢查像素
pixels = img.convert('RGB').load()
black_count = 0
for y in range(img.height):
    for x in range(img.width):
        r, g, b = pixels[x, y]
        if (r + g + b) < 100:  # 黑色
            black_count += 1

print(f'黑色像素數: {black_count}')
if black_count > 100:
    print('✅ 圖片 1 有可見的黑色內容')
    img.save('temp/test_with_tight.png')
else:
    print('❌ 圖片 1 沒有黑色內容')
