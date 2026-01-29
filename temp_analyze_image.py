from PIL import Image

# 打開提取的圖片
img = Image.open('temp/first_rendered_image.png')

# 轉換為 RGB 以便分析
img_rgb = img.convert('RGB')
pixels = img_rgb.load()

# 統計顏色
unique_colors = set()
for y in range(img.height):
    for x in range(img.width):
        unique_colors.add(pixels[x, y])

print(f'圖片大小: {img.size}')
print(f'圖片模式: {img.mode}')
print(f'唯一顏色數: {len(unique_colors)}')

# 檢查是否有明顯的黑色文字（表示有內容）
black_like_count = 0
white_like_count = 0
for color in unique_colors:
    r, g, b = color[:3] if len(color) >= 3 else (color[0], color[0], color[0])
    brightness = (r + g + b) // 3
    if brightness < 50:  # 接近黑色
        black_like_count += 1
    elif brightness > 200:  # 接近白色
        white_like_count += 1

print(f'接近黑色的顏色: {black_like_count}')
print(f'接近白色的顏色: {white_like_count}')

# 取樣檢查中心區域的內容
center_colors = []
for y in range(img.height//4, 3*img.height//4):
    for x in range(img.width//4, 3*img.width//4):
        center_colors.append(pixels[x, y])

center_brightness = [(r+g+b)//3 for r, g, b in center_colors if len((r,g,b)) >= 3]
if center_brightness:
    avg_brightness = sum(center_brightness) // len(center_brightness)
    print(f'中心區域平均亮度: {avg_brightness}')
    if avg_brightness < 100:
        print('✅ 圖片中心有深色內容（可能是文字）')
    else:
        print('❌ 圖片中心大多是白色（可能為空）')
