import openpyxl
from openpyxl.drawing.image import Image as XlImage
import os
import io
from PIL import Image

# 讀取最新的Excel
reports_dir = 'reports'
files = [f for f in os.listdir(reports_dir) if 'ApplicationsOfDerivatives_14B_Ab3' in f and f.endswith('.xlsx') and not f.startswith('~')]
files.sort(reverse=True)
# 嘗試第一個檔案，如果被鎖定就用第二個
for xlsx_file in files[:3]:
    try:
        latest_file = os.path.join(reports_dir, xlsx_file)
        wb = openpyxl.load_workbook(latest_file)
        ws = wb.active
        print(f'成功打開: {xlsx_file}')
        break
    except PermissionError:
        print(f'檔案被鎖定: {xlsx_file}，嘗試下一個...')
        continue
else:
    print('無法打開任何檔案')
    exit()

print(f'檔案: {files[0]}')
print(f'圖片物件數: {len(ws._images)}')

if ws._images:
    # 取出第一張圖片
    first_image = ws._images[0]
    print(f'\n第一張圖片的原始資料: {type(first_image)}')
    
    # 嘗試提取圖片 BytesIO
    if hasattr(first_image, 'image'):
        img_data = first_image.image
        if isinstance(img_data, io.BytesIO):
            img_data.seek(0)
            img_bytes = img_data.read()
        else:
            img_bytes = img_data
        
        # 保存到本地
        with open('temp_first_image.png', 'wb') as f:
            f.write(img_bytes)
        
        # 用PIL分析圖片
        img_data.seek(0) if isinstance(img_data, io.BytesIO) else None
        pil_img = Image.open(io.BytesIO(img_bytes))
        
        print(f'圖片大小: {pil_img.size}')
        print(f'圖片模式: {pil_img.mode}')
        
        # 統計顏色數
        if pil_img.mode == 'RGBA':
            colors = pil_img.getcolors(maxcolors=256)
        elif pil_img.mode == 'RGB':
            colors = pil_img.getcolors(maxcolors=256)
        else:
            colors = pil_img.getcolors()
        
        if colors:
            print(f'圖片色彩數: {len(colors)}')
            for i, (count, color) in enumerate(colors[:5]):
                print(f'  顏色 {i+1}: {color} (出現 {count} 次)')
        
        print(f'\n✅ 圖片已保存到: temp_first_image.png')
    else:
        print('無法提取圖片')
