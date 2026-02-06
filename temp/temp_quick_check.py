import openpyxl
import io
from PIL import Image
import os

# 讀取最新的Excel
reports_dir = 'reports'
files = [f for f in os.listdir(reports_dir) if 'ApplicationsOfDerivatives_14B_Ab3' in f and f.endswith('.xlsx')]
files.sort(reverse=True)
latest_file = os.path.join(reports_dir, files[0])

# 用 openpyxl 打開
wb = openpyxl.load_workbook(latest_file)
ws = wb.active

# 提取第一張圖片
if ws._images:
    first_img = ws._images[0]
    if hasattr(first_img, 'ref') and isinstance(first_img.ref, io.BytesIO):
        first_img.ref.seek(0)
        img_data = first_img.ref.read()
        
        # 保存 PNG
        with open('temp/first_rendered_image.png', 'wb') as f:
            f.write(img_data)
        
        # 用 PIL 讀取並分析
        first_img.ref.seek(0)
        pil_img = Image.open(first_img.ref)
        print(f'✅ 圖片已保存')
        print(f'圖片大小: {pil_img.size}')
        
        # 檢查是否有黑色文字
        pixels = pil_img.convert('RGB').load()
        black_count = 0
        for y in range(pil_img.height):
            for x in range(pil_img.width):
                r, g, b = pixels[x, y]
                if (r + g + b) < 150:  # 黑色或深色
                    black_count += 1
        
        print(f'黑色像素數: {black_count}')
        if black_count > 1000:
            print('✅ 圖片有可見的文字內容')
        else:
            print('❌ 圖片文字很少或為空')

print(f'\n報表: {files[0]}')
