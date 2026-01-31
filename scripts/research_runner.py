# -*- coding: utf-8 -*-
"""
=============================================================================
模組名稱 (Module Name): scripts/research_runner.py
功能說明 (Description): 執行大規模題目採樣，數據存入 execution_samples 後自動
                        匯出 Excel 報表。
                        [V1.6] 保留原始 LaTeX 字串 (Column C) 並在後方新增渲染圖。
執行語法 (Usage): python scripts/research_runner.py
版本資訊 (Version): V1.6 (Raw + Render Comparison Edition)
=============================================================================
"""
import os
import sys
import time
import sqlite3
import importlib.util
import glob
import io
import base64
import re
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt

# ==========================================
# 1. 環境初始化 (Environment Setup)
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(current_dir)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

SKILLS_DIR = os.path.join(PROJECT_ROOT, 'skills')
REPORTS_DIR = os.path.join(PROJECT_ROOT, 'reports')
DB_PATH = os.path.join(PROJECT_ROOT, 'instance', 'kumon_math.db')
PROTECTED_FILES = {"Example_Program.py", "__init__.py", "base_skill.py", "Example_Program_Research.py"}

# 確保目錄存在
os.makedirs(REPORTS_DIR, exist_ok=True)

def get_skill_menu():
    """ 掃描 skills 目錄並產出選單 """
    files = glob.glob(os.path.join(SKILLS_DIR, "*.py"))
    skill_list = [os.path.basename(f).replace('.py', '') for f in files 
                  if os.path.basename(f) not in PROTECTED_FILES]
    return sorted(skill_list)

# ==========================================
# 2. LaTeX 渲染核心
# ==========================================
def render_latex_to_buffer(latex_str):
    """
    將題目字串渲染為圖片 Buffer。
    [V2.2] 使用 matplotlib mathtext 真正渲染 LaTeX 數學式，修復重疊問題
    """
    try:
        # 設定 matplotlib 使用支持中文的字體
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei UI', 'Microsoft JhengHei', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['mathtext.fontset'] = 'stix'  # 使用 STIX 數學字體
        plt.rcParams['mathtext.default'] = 'regular'
        
        if not latex_str:
            return None
        
        # 創建圖片 - 提高解析度
        fig = plt.figure(figsize=(18, 2.8), dpi=150)
        fig.patch.set_alpha(0)
        ax = fig.add_subplot(111)
        
        # 簡化方案：直接一次性渲染整個字串（matplotlib 會自動處理 $ 包裹的數學式）
        # 統一使用 15pt 字體避免大小不一致
        ax.text(0.02, 0.5, latex_str,
               fontsize=15,
               ha='left', va='center',
               transform=ax.transAxes,
               wrap=False)
        
        ax.axis('off')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        
        # 存入 Buffer - 提高輸出品質
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.15, dpi=120)  # 提高 DPI
        plt.close(fig)
        
        buf.seek(0)
        return buf
    except Exception as e:
        print(f"⚠️ 渲染失敗 [{latex_str[:40]}...]: {str(e)}")
        return None

# ==========================================
# 3. Excel 匯出邏輯 (重點修改區)
# ==========================================
def export_to_excel(skill_id, ablation_id=3):
    """ 
    匯出 Excel：
    1. 保留 question_text 原始字串 (C欄)
    2. 新增 渲染後的圖片 (K欄)
    """
    conn = sqlite3.connect(DB_PATH)
    
    query = f"""
        SELECT mode, sample_index, question_text, correct_answer, image_base64,
               is_crash, is_logic_correct, score_complexity, duration_seconds, timestamp
        FROM execution_samples 
        WHERE skill_id = '{skill_id}' AND ablation_id = {ablation_id}
        ORDER BY id DESC LIMIT 20
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    tag_timestamp = time.strftime('%Y%m%d_%H%M')
    # 使用正则表达式移除所有 _Ab\d+ 标记（避免重复）
    base_id = re.sub(r'_Ab\d+', '', skill_id)
    file_name = f"{base_id}_Ab{ablation_id}_{tag_timestamp}.xlsx"
    file_path = os.path.join(REPORTS_DIR, file_name)

    # 使用 xlsxwriter 引擎
    writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
    
    # 建立一個不包含 image_base64 的 DataFrame (文字資料)
    # 注意：這裡保留了 question_text
    display_df = df.drop(columns=['image_base64'])
    
    # 重新命名欄位，讓報表更清楚 (Optional)
    display_df = display_df.rename(columns={'question_text': 'Raw LaTeX Code (原始碼)'})

    display_df.to_excel(writer, sheet_name='ResearchData', index=False)
    
    workbook  = writer.book
    worksheet = writer.sheets['ResearchData']
    
    # -------------------------------------------------------
    # 格式設定 (Visual Tuning)
    # -------------------------------------------------------
    # C欄: 原始 LaTeX 代碼 (設寬一點，方便對照)
    worksheet.set_column('C:C', 45) 
    
    # 定義新欄位位置 (根據 DataFrame 欄位數量推算，或手動指定)
    # 目前 display_df 欄位約 9 個，所以 K=10, L=11
    col_latex_render = 10  # K欄: 數學式預覽
    col_visual_img = 11    # L欄: 題目附圖 (原本的 image_base64)

    # 寫入圖片欄位的標題
    header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'align': 'center', 'valign': 'vcenter'})
    
    worksheet.write(0, col_latex_render, "數學式預覽 (Rendered)", header_format)
    worksheet.write(0, col_visual_img, "幾何/題目附圖 (Visual)", header_format)
    
    worksheet.set_column(col_latex_render, col_latex_render, 35) # 設定預覽欄寬度
    worksheet.set_column(col_visual_img, col_visual_img, 40)     # 設定附圖欄寬度

    print("🎨 正在渲染 LaTeX 數學式並生成 Excel 圖片...")

    # -------------------------------------------------------
    # 圖片處理迴圈
    # -------------------------------------------------------
    for idx, row in df.iterrows():
        row_num = idx + 1
        worksheet.set_row(row_num, 65) # 設定列高，讓圖片顯示清楚

        # --- A. 處理 LaTeX 渲染 (讀取原始 question_text) ---
        q_text = row['question_text']
        if q_text:
            img_buf = render_latex_to_buffer(q_text)
            if img_buf:
                # 插入圖片到 K 欄
                worksheet.insert_image(row_num, col_latex_render, f'latex_{idx}.png', 
                                       {'image_data': img_buf, 'x_scale': 0.8, 'y_scale': 0.8, 'object_position': 2})

        # --- B. 處理 Base64 附圖 (讀取 image_base64) ---
        b64_str = row['image_base64']
        if b64_str and len(b64_str) > 100:
            try:
                img_data = base64.b64decode(b64_str)
                img_file = io.BytesIO(img_data)
                # 插入圖片到 L 欄
                worksheet.insert_image(row_num, col_visual_img, f'vis_{idx}.png', 
                                       {'image_data': img_file, 'x_scale': 0.35, 'y_scale': 0.35, 'object_position': 2})
            except Exception as e:
                worksheet.write(row_num, col_visual_img, "圖片損毀")

    writer.close()
    return file_path

# ==========================================
# 4. 核心採樣流程 (保持不變)
# ==========================================
def run_research_samples(skill_id, n_samples=20, ablation_id=None):
    """
    [科研目標]: 採集 20 道題目數據，分析 14B 模型的出題品質。
    """
    # 自動從 skill_id 推斷 ablation_id（例如：gh_ApplicationsOfDerivatives_Cloud_Ab1 -> 1）
    if ablation_id is None:
        match = re.search(r'_Ab(\d+)', skill_id)
        ablation_id = int(match.group(1)) if match else 3
    
    skill_file = os.path.join(SKILLS_DIR, f"{skill_id}.py")
    
    spec = importlib.util.spec_from_file_location(skill_id, skill_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"\n🧪 啟動科研採樣: {skill_id} (Ablation: {ablation_id})")
    
    for i in tqdm(range(n_samples), desc="採樣進度"):
        start_time = time.time()
        is_crash = 0
        is_logic_correct = 0
        res = {}
        
        try:
            res = module.generate()

            if not isinstance(res, dict):
                print(f"⚠️ 警告: 模式 [{skill_id}] 回傳了非字典格式")
                continue
            
            check_res = module.check(res['correct_answer'], res['correct_answer'])
            is_logic_correct = 1 if check_res.get('correct') else 0
            
        except Exception as e:
            is_crash = 1
            print(f"\n❌ 第 {i+1} 題生成失敗: {str(e)}")

        duration = time.time() - start_time
        q_text = res.get('question_text', '')
        # 簡單複雜度計算
        score = min(10, len(q_text) // 10) if q_text else 0

        cursor.execute("""
            INSERT INTO execution_samples (
                skill_id, mode, sample_index, question_text, correct_answer, 
                image_base64, is_crash, is_logic_correct, score_complexity, 
                duration_seconds, ablation_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            skill_id, 
            res.get('mode', 0), 
            i + 1, 
            q_text, 
            str(res.get('correct_answer', '')),
            res.get('image_base64', ''),
            is_crash, 
            is_logic_correct, 
            score, 
            duration, 
            ablation_id
        ))
        conn.commit()

    conn.close()
    print(f"\n✅ 採樣完成！")

    print(f"\n📦 正在產生科研報表 (含 Raw Code + Render 預覽)...")
    report_path = export_to_excel(skill_id, ablation_id)
    if report_path:
        print(f"✅ 報表已匯出: {report_path}")

if __name__ == "__main__":
    print("="*60)
    print("🔬 Math AI Research Runner (V1.6 - Code & Render Compare)")
    print("="*60)
    
    skills = get_skill_menu()
    if not skills:
        print("❌ skills/ 目錄內沒有可測試的檔案。")
        sys.exit(0)
        
    for i, name in enumerate(skills, 1):
        print(f"   [{i}] {name}")
        
    try:
        choice = int(input(f"\n👉 請選擇要採樣的技能 (1-{len(skills)}): "))
        if 1 <= choice <= len(skills):
            run_research_samples(skills[choice-1])
        else:
            print("❌ 超出範圍。")
    except ValueError:
        print("❌ 請輸入數字。")