"""
查看 Bare Prompt (ablation_id=1) 的实际内容
"""
import sqlite3
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def show_prompts(ablation_id):
    """显示指定 ablation_id 的 prompt 内容"""
    db_path = 'instance/kumon_math.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取 ablation 描述
    cursor.execute("""
        SELECT ablation_id, ablation_name, description 
        FROM ablation_settings 
        WHERE ablation_id = ?
    """, (ablation_id,))
    
    ablation_info = cursor.fetchone()
    if not ablation_info:
        print(f"❌ 找不到 ablation_id={ablation_id}")
        return
    
    print("=" * 80)
    print(f"📋 Ablation ID: {ablation_info[0]}")
    print(f"📌 名稱: {ablation_info[1]}")
    print(f"💬 描述: {ablation_info[2]}")
    print("=" * 80)
    
    # 获取所有 prompt 类型
    cursor.execute("""
        SELECT prompt_type, content, description 
        FROM ablation_settings 
        WHERE ablation_id = ?
        ORDER BY 
            CASE prompt_type
                WHEN 'system_instruction' THEN 1
                WHEN 'context_builder' THEN 2
                WHEN 'implementation_guide' THEN 3
                WHEN 'output_format' THEN 4
                WHEN 'quality_check' THEN 5
                WHEN 'few_shot_examples' THEN 6
                ELSE 7
            END
    """, (ablation_id,))
    
    prompts = cursor.fetchall()
    
    for prompt_type, content, description in prompts:
        print(f"\n{'─' * 80}")
        print(f"🏷️  Prompt 類型: {prompt_type}")
        print(f"📝 說明: {description or '(無說明)'}")
        print(f"{'─' * 80}")
        print(content)
        print()
    
    conn.close()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='查看 Ablation Prompt 內容')
    parser.add_argument('--ablation-id', type=int, default=1, 
                        help='Ablation ID (預設: 1=Bare Prompt)')
    args = parser.parse_args()
    
    show_prompts(args.ablation_id)
    
    # 顯示對比
    if args.ablation_id == 1:
        print("\n" + "=" * 80)
        print("💡 提示: 查看 Full-Healing (ablation_id=3) 的對比:")
        print("   python scripts/show_bare_prompt.py --ablation-id 3")
        print("=" * 80)
