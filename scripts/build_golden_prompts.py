# -*- coding: utf-8 -*-
# ==============================================================================
# ID: build_golden_prompts.py
# Version: V1.0 (Automated Golden Prompt Builder)
# Purpose: Auto-generate Golden Prompts by selecting fixed #1 textbook example
#
# [Description]:
#   本程式自動為每個技能生成固定的 Golden Prompts，用於實驗的對照組設計。
#   
#   設計原則：
#   - Ab1/Ab2/Ab3 都使用「同一個例題」（序號最小的第一題）
#   - 確保實驗變因單一：唯一差異 = Ab1(無工具) vs Ab2(Regex堆砌) vs Ab3(Healer修復)
#   - 避免 Prompt 生成的變異，提升實驗的統計有效性
#
# [Output]:
#   - experiments/golden_prompts/temp/{skill_id}_Ab1.txt
#   - experiments/golden_prompts/temp/{skill_id}_Ab2.txt
#   （Ab3 在實驗時複用 Ab2 檔案 + Healer 開關，見 run_experiment.py L673）
# ==============================================================================

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# --- 路徑修正 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app import create_app
from models import db, SkillInfo, TextbookExample, SkillGenCodePrompt
from core.prompts.prompt_builder import PromptBuilder

# --- 日誌設置 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(project_root, 'build_golden_prompts.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- 常數定義 ---
PROMPTS_OUTPUT_DIR = os.path.join(project_root, "experiments", "golden_prompts", "temp")
os.makedirs(PROMPTS_OUTPUT_DIR, exist_ok=True)


def get_first_textbook_example(skill_id: str) -> TextbookExample:
    """
    為指定技能取得序號最小的第一個例題
    
    Args:
        skill_id: 技能 ID
        
    Returns:
        TextbookExample 物件，若無則返回 None
    """
    example = TextbookExample.query.filter_by(skill_id=skill_id).order_by(
        TextbookExample.id.asc()
    ).first()
    
    if example:
        logger.info(f"   ✅ 取得例題 ID={example.id}: {example.problem_text[:50]}...")
        return example
    else:
        logger.warning(f"   ❌ 未找到例題")
        return None


def extract_single_example(problem_text: str) -> str:
    """
    從問題文本中提取「唯一」的單個例題
    
    處理情況：
    - 如果包含「範例：」前綴，只取第一個「範例：」開頭的行
    - 如果有多行，只取第一行
    - 移除多餘的空白和重複例題
    
    Args:
        problem_text: 原始問題文字
        
    Returns:
        清理後的單個例題
    """
    if not problem_text:
        return problem_text
    
    lines = problem_text.strip().split('\n')
    
    # 如果有多行，只取第一行
    if len(lines) > 1:
        logger.info(f"   ⚠️  偵測到多行例題 ({len(lines)} 行)，只保留第一行")
        result = lines[0].strip()
    else:
        result = problem_text.strip()
    
    # 移除「範例：」前綴（若有），為了保持一致性
    if result.startswith("範例："):
        result = result[3:].strip()
        logger.info(f"   ℹ️  移除『範例：』前綴")
    
    return result


def get_master_spec(skill_id: str) -> str:
    """
    從數據庫取得最新的 MASTER_SPEC
    
    Args:
        skill_id: 技能 ID
        
    Returns:
        MASTER_SPEC 字串，若無則返回空字串
    """
    spec = SkillGenCodePrompt.query.filter_by(
        skill_id=skill_id,
        prompt_type="MASTER_SPEC"
    ).order_by(SkillGenCodePrompt.created_at.desc()).first()
    
    if spec:
        logger.info(f"   ✅ 取得 MASTER_SPEC ({len(spec.prompt_content)} chars)")
        return spec.prompt_content
    else:
        logger.warning(f"   ❌ 未找到 MASTER_SPEC，將使用預設值")
        return ""


def generate_ab1_prompt(skill_id: str, master_spec: str, textbook_example: TextbookExample) -> str:
    """
    生成 Ab1 Prompt（Bare - 無工具庫）
    
    Args:
        skill_id: 技能 ID
        master_spec: MASTER_SPEC 字串
        textbook_example: TextbookExample 物件
        
    Returns:
        Ab1 Prompt 字串
    """
    try:
        # 取得技能名稱
        skill = SkillInfo.query.filter_by(skill_id=skill_id).first()
        topic = skill.skill_ch_name if skill else skill_id
        
        # 使用第一個例題，並清理以確保只有單一例題
        raw_example_text = textbook_example.problem_text
        example_text = extract_single_example(raw_example_text)
        
        # 加入「範例：」前綴（若不存在）
        if not example_text.startswith("範例："):
            example_text = f"範例：{example_text}"
        
        # 呼叫 PromptBuilder
        prompt = PromptBuilder.build(
            master_spec=master_spec,
            ablation_id=1,
            skill_id=skill_id,
            textbook_example=example_text,
            topic=topic
        )
        
        logger.info(f"   ✅ Ab1 Prompt 生成完成 ({len(prompt)} chars)")
        return prompt
    except Exception as e:
        logger.error(f"   ❌ Ab1 Prompt 生成失敗: {e}")
        raise


def generate_ab2_prompt(skill_id: str, master_spec: str, textbook_example: TextbookExample) -> str:
    """
    生成 Ab2 Prompt（Engineered - 含工具庫）
    注意：Ab3 會複用此檔案 + Healer 開關
    
    Args:
        skill_id: 技能 ID
        master_spec: MASTER_SPEC 字串
        textbook_example: TextbookExample 物件（用於參考例題）
        
    Returns:
        Ab2 Prompt 字串
    """
    try:
        # 使用第一個例題，並清理以確保只有單一例題
        raw_example_text = textbook_example.problem_text
        example_text = extract_single_example(raw_example_text)
        
        # 加入「範例：」前綴（若不存在）
        if not example_text.startswith("範例："):
            example_text = f"範例：{example_text}"
        
        # 呼叫 PromptBuilder（Ab2 不使用 textbook_example 參數）
        prompt = PromptBuilder.build(
            master_spec=master_spec,
            ablation_id=2,
            skill_id=skill_id
        )
        
        # 在 MASTER_SPEC 前添加課本例題參考
        # 找到 "### MASTER_SPEC:" 位置，在前面插入例題
        if "### MASTER_SPEC:" in prompt:
            textbook_ref = f"""【參考例題】
以下是該技能的課本真題範例（用於理解題型特徵）：
{example_text}

"""
            prompt = prompt.replace("### MASTER_SPEC:", textbook_ref + "### MASTER_SPEC:")
        
        # [NEW] Append the strict no-think and no-markdown constraints for Qwen
        prompt += "\n\n❌ 輸出 Markdown 代碼塊 → 直接寫 code\n⚠️ Output Python code ONLY. No introduction. No comments. No thinking.\n/no_think"

        logger.info(f"   ✅ Ab2 Prompt 生成完成 ({len(prompt)} chars)")
        return prompt
    except Exception as e:
        logger.error(f"   ❌ Ab2 Prompt 生成失敗: {e}")
        raise


def save_golden_prompt(skill_id: str, ablation_id: int, prompt_text: str) -> bool:
    """
    保存 Golden Prompt 到檔案
    
    Args:
        skill_id: 技能 ID
        ablation_id: Ablation ID (1=Ab1, 2=Ab2)
        prompt_text: Prompt 文字
        
    Returns:
        True 若保存成功，否則 False
    """
    try:
        # 決定檔案名稱
        if ablation_id == 1:
            filename = f"{skill_id}_Ab1.txt"
        else:
            filename = f"{skill_id}_Ab2.txt"
        
        filepath = os.path.join(PROMPTS_OUTPUT_DIR, filename)
        
        # 保存檔案
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(prompt_text)
        
        logger.info(f"   ✅ 保存到: {filename}")
        return True
    except Exception as e:
        logger.error(f"   ❌ 保存失敗: {e}")
        return False


def build_golden_prompts_for_skill(skill_id: str) -> bool:
    """
    為單一技能生成並保存 Golden Prompts (Ab1 + Ab2)
    
    Args:
        skill_id: 技能 ID
        
    Returns:
        True 若成功，否則 False
    """
    logger.info(f"\n🔨 處理技能: {skill_id}")
    
    try:
        # Step 1: 取得 MASTER_SPEC
        logger.info("  Step 1: 取得 MASTER_SPEC")
        master_spec = get_master_spec(skill_id)
        if not master_spec:
            logger.warning("  ⚠️  警告：MASTER_SPEC 為空，繼續進行...")
        
        # Step 2: 取得第一個例題
        logger.info("  Step 2: 取得第一個例題（序號最小）")
        textbook_example = get_first_textbook_example(skill_id)
        if not textbook_example:
            logger.error("  ❌ 失敗：無可用的教科書例題")
            return False
        
        # Step 3: 生成 Ab1 Prompt
        logger.info("  Step 3: 生成 Ab1 Prompt")
        ab1_prompt = generate_ab1_prompt(skill_id, master_spec, textbook_example)
        saved = save_golden_prompt(skill_id, 1, ab1_prompt)
        if not saved:
            logger.error("  ❌ 失敗：Ab1 Prompt 保存失敗")
            return False
        
        # Step 4: 生成 Ab2 Prompt
        logger.info("  Step 4: 生成 Ab2 Prompt")
        ab2_prompt = generate_ab2_prompt(skill_id, master_spec, textbook_example)
        saved = save_golden_prompt(skill_id, 2, ab2_prompt)
        if not saved:
            logger.error("  ❌ 失敗：Ab2 Prompt 保存失敗")
            return False
        
        # Step 5: 註記
        logger.info("  ✅ [Note] Ab3 將在實驗時複用 Ab2.txt + Healer 開關")
        logger.info(f"✅ 技能 {skill_id} 完成！\n")
        return True
        
    except Exception as e:
        logger.error(f"❌ 技能 {skill_id} 處理失敗: {e}\n")
        return False


def main(target_skill_ids=None):
    """
    主程式：生成指定技能的 Golden Prompts
    
    Args:
        target_skill_ids: 技能 ID 列表，若為 None 則詢問用戶
    """
    
    app = create_app()
    
    with app.app_context():
        logger.info("="*70)
        logger.info("🚀 Golden Prompt 自動生成工具")
        logger.info("   原則：Ab1/Ab2/Ab3 都使用序號最小的「第一個例題」")
        logger.info("   目的：控制變因，確保實驗的統計有效性")
        logger.info("="*70)
        
        # --- 1. 取得所有技能 ---
        all_skills = SkillInfo.query.all()
        if not all_skills:
            logger.error("❌ 數據庫中沒有技能資料")
            return
        
        # --- 2. 決定要處理的技能 ---
        if target_skill_ids:
            # 從參數指定的技能 ID 篩選
            selected_skills = [s for s in all_skills if s.skill_id in target_skill_ids]
            if not selected_skills:
                logger.error(f"❌ 找不到指定的技能: {target_skill_ids}")
                return
        else:
            # 交互式詢問用戶
            logger.info(f"\n📚 可用技能列表 ({len(all_skills)} 個):")
            for i, skill in enumerate(all_skills[:10], 1):  # 只顯示前 10 個
                logger.info(f"   [{i}] {skill.skill_id} - {skill.skill_ch_name}")
            logger.info(f"   ... 等等 ({len(all_skills) - 10} 個技能)")
            
            print("\n")
            print("[0] 全部（生成所有技能的 Golden Prompts）")
            print("[skill_id] 選擇特定技能（例如 jh_數學1上_FourArithmeticOperationsOfIntegers）")
            choice = input("\n👉 請輸入 (0 表示全部，或輸入 skill_id): ").strip()
            
            if choice == '0':
                selected_skills = all_skills
            else:
                # 嘗試按 skill_id 查詢
                skill = SkillInfo.query.filter_by(skill_id=choice).first()
                if skill:
                    selected_skills = [skill]
                else:
                    logger.error(f"❌ 找不到技能: {choice}")
                    return
        
        logger.info(f"\n🎯 已選擇 {len(selected_skills)} 個技能")
        for skill in selected_skills[:5]:  # 只顯示前 5 個
            logger.info(f"   - {skill.skill_id}")
        if len(selected_skills) > 5:
            logger.info(f"   ... 等等 ({len(selected_skills) - 5} 個技能)")
        
        # --- 3. 執行生成 ---
        logger.info("\n" + "="*70)
        logger.info("🔄 開始生成 Golden Prompts...")
        logger.info("="*70)
        
        success_count = 0
        fail_count = 0
        
        for skill in selected_skills:
            if build_golden_prompts_for_skill(skill.skill_id):
                success_count += 1
            else:
                fail_count += 1
        
        # --- 4. 摘要報告 ---
        logger.info("\n" + "="*70)
        logger.info("✅ Golden Prompt 生成完成！")
        logger.info(f"   成功: {success_count} 個技能")
        logger.info(f"   失敗: {fail_count} 個技能")
        logger.info(f"   輸出目錄: {PROMPTS_OUTPUT_DIR}")
        logger.info("="*70)
        
        # --- 5. 列出已生成的檔案 ---
        logger.info("\n📄 已生成的 Golden Prompt 檔案:")
        for filename in sorted(os.listdir(PROMPTS_OUTPUT_DIR)):
            if filename.endswith('.txt'):
                filepath = os.path.join(PROMPTS_OUTPUT_DIR, filename)
                filesize = os.path.getsize(filepath)
                logger.info(f"   - {filename} ({filesize} bytes)")
        
        logger.info("\n💡 下一步：執行 python scripts/run_experiment.py 進行實驗")


if __name__ == "__main__":
    import sys
    
    # 支援命令行參數: python build_golden_prompts.py skill_id1 skill_id2 ...
    if len(sys.argv) > 1:
        target_skills = sys.argv[1:]
        logger.info(f"命令行模式：為 {len(target_skills)} 個技能生成 Golden Prompts")
        main(target_skill_ids=target_skills)
    else:
        logger.info("互動模式：請選擇要處理的技能")
        main()
