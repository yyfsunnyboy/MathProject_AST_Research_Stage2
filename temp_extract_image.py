import openpyxl
from openpyxl.drawing.image import Image as XlImage
import os
import io
from PIL import Image

# 讀取最新的Excel
reports_dir = 'reports'
files = [f for f in os.listdir(reports_dir) if 'ApplicationsOfDerivatives_14B_Ab3' in f and f.endswith('.xlsx')]
files.sort(reverse=True)
latest_file = os.path.join(reports_dir, files[0])

# 用 openpyxl 打開
wb = openpyxl.load_workbook(latest_file)
ws = wb.active

# 提取第一張圖片並保存
if ws._images:
    first_img = ws._images[0]
    
    # 嘗試從 ref 屬性（BytesIO）讀取
    if hasattr(first_img, 'ref') and isinstance(first_img.ref, io.BytesIO):
        # 這是 BytesIO 對象
        first_img.ref.seek(0)
        img_data = first_img.ref.read()
        
        # 保存 PNG
        with open('temp/first_rendered_image.png', 'wb') as f:
            f.write(img_data)
        
        # 用 PIL 讀取並顯示信息
        first_img.ref.seek(0)
        pil_img = Image.open(first_img.ref)
        print(f'✅ 第一張圖片已保存到 temp/first_rendered_image.png')
        print(f'圖片大小: {pil_img.size}')
        print(f'圖片模式: {pil_img.mode}')
    else:
        print(f'圖片引用類型: {type(first_img.ref)}')
        if hasattr(first_img, 'ref'):
            print(f'圖片引用: {first_img.ref}')


