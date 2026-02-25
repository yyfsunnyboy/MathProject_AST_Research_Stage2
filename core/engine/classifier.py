# -*- coding: utf-8 -*-
import os
import re
import json
from core.ai_wrapper import get_ai_client, call_ai_with_retry
from config import Config

class SkillClassifier:
    """
    SkillClassifier 負責將使用者輸入的題目 (文字或影像) 對應到系統中的 agent_skill。
    """
    def __init__(self, model_role='default'):
        self.client = get_ai_client(model_role)
        self.skills = self._discover_skills()

    def _discover_skills(self):
        """
        動態掃描 agent_skills 目錄，獲取可用技能清單。
        """
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        skills_dir = os.path.join(project_root, "agent_skills")
        skills = []
        if os.path.exists(skills_dir):
            for d in os.listdir(skills_dir):
                if os.path.isdir(os.path.join(skills_dir, d)):
                    skills.append(d)
        return sorted(skills)

    def _get_system_prompt(self):
        """
        構建分類專用的 System Prompt。
        """
        skills_str = "\n".join([f"- {s}" for s in self.skills])
        return f"""你是一個數學題目分類專家。
你的任務是閱讀使用者提供的數學題目（文字或圖片內容），並從下方的「技能清單」中選擇一個最符合該題目的技能名稱。

【技能清單】
{skills_str}

【分類規則】
1. 只輸出技能名稱，不要有任何其他解釋或標點符號。
2. 如果題目完全不屬於清單中的任何一項，請輸出 "Unknown"。
3. 優先根據數學結構判斷（例如：看到根號選 FourOperationsOfRadicals）。

請開始分類："""

    def classify(self, input_text=None, image_path=None):
        """
        進行分類。
        Returns:
            str: 識別出的技能名稱或 "Unknown"
        """
        if not input_text and not image_path:
            return "Unknown"

        prompt = self._get_system_prompt()
        if input_text:
            prompt += f"\n\n題目內容：{input_text}"
        
        try:
            # 視圖模式下調用 AI
            response = call_ai_with_retry(
                self.client, 
                prompt, 
                image_path=image_path,
                max_retries=2,
                verbose=False
            )
            
            result = response.text.strip()
            # 清洗結果，防止 AI 輸出 Markdown 或贅字
            result = re.sub(r'[`"\'\s]', '', result)
            
            # 驗證是否在清單中
            if result in self.skills:
                return result
            else:
                # 模糊比對 (優化：擷取真正的核心特徵，如 FourArithmeticOperationsOfIntegers)
                for s in self.skills:
                    core_name = s.split("_")[-1].lower()
                    # 無論是 LLM 給出包含前綴的完整字串，或是只給出後綴，都能正確對應
                    if core_name in result.lower() or s.lower() in result.lower():
                        return s
                return "Unknown"
                
        except Exception as e:
            print(f"分類失敗: {e}")
            return "Unknown"

if __name__ == "__main__":
    # 簡單測試
    classifier = SkillClassifier()
    print(f"可用技能: {classifier.skills}")
    test_q = "計算根號 2 加上根號 8 的值。"
    print(f"測試題目: {test_q}")
    print(f"分類結果: {classifier.classify(input_text=test_q)}")
