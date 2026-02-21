# -*- coding: utf-8 -*-
"""
============================================================
🚀 Math Learning Engine - Science Fair Demo
============================================================
功能：輸入一題數學題 -> 自動分類 -> 生成「簡單/相同/困難」三種練習題
用法：python engine_demo.py
============================================================
"""
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.engine.engine import MathEngine

def main():
    engine = MathEngine()
    
    print("\n" + "*"*60)
    print("🌟 歡迎使用 Math Lab 數學題目出題引擎 (科展版) 🌟")
    print("*"*60)
    print("您可以輸入一題題目文字，系統將為您生成專屬練習場。")
    print("(目前支援：整數、分數、根式、多項式、微積分)")
    print("*"*60)
    
    while True:
        user_input = input("\n👉 1. 請輸入題目文字 (或輸入 'exit' 退出): ").strip()
        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("再見！祝您學習愉快！")
            break
            
        if not user_input:
            continue
            
        count_input = input("   2. 產生題目數量 (預設 5): ").strip()
        if not count_input:
            count = 5
        else:
            try:
                count = int(count_input)
                if count <= 0:
                    print("請輸入大於 0 的整數。")
                    continue
            except ValueError:
                print("輸入無效，將使用預設數量 5。")
                count = 5
                
        ablation_input = input("   3. 是否開啟 Ab1 原生消融模式？(y/N, 預設 N 啟用 Math Project 防護): ").strip().lower()
        ablation_mode = ablation_input in ['y', 'yes']
                
        # 執行引擎
        output = engine.generate_practice_set(input_text=user_input, count=count, ablation_mode=ablation_mode)
        
        if output["success"]:
            print(f"\n✅ 成功識別題型：{output['skill']}\n")
            print("============================================================")
            print(f"📚 您的專屬 {count} 題練習題目已生成：")
            print("============================================================\n")
            
            for idx, result in enumerate(output["problems"], 1):
                if "error" in result:
                    print(f"[題目 {idx}]")
                    print(f"❌ 生成失敗: {result['error']}")
                    if "traceback" in result:
                        print(result['traceback'])
                    print("")
                else:
                    print(f"[題目 {idx}]")
                    print(f"題：{result.get('question_text', '')}")
                    print(f"解：{result.get('correct_answer', '')}")
                    if "_mcri_hygiene_score" in result:
                        print(f"✨ 符號衛生得分: {result['_mcri_hygiene_score']} ({result.get('_mcri_hygiene_notes', '')})")
                    print("")
                    
            if "debug_meta" in output:
                meta = output["debug_meta"]
                print("============================================================")
                print("🛠️  [Debug Meta] 生成報告")
                print("============================================================")
                perf = meta.get("performance", {})
                print(f"⏱️ 效能: AI 推論 {perf.get('ai_inference_time_sec', 0)}s | CPU 執行 {perf.get('cpu_execution_time_sec', 0)}s")
                healer = meta.get("healer_trace", {})
                print(f"🔧 修復: Regex={healer.get('regex_fixes', 0)}, AST={healer.get('ast_fixes', 0)}")
                mcri = meta.get("mcri_report", {})
                print(f"📊 MCRI 結構強度: {mcri.get('robustness_grade', 'UNKNOWN')} ({mcri.get('robustness_reason', '')})")
                print("============================================================\n")
        else:
            print(f"\n❌ 抱歉：{output['error']}")

if __name__ == "__main__":
    main()
