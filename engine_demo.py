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
    print("🌟 歡迎使用 Ivan's Lab 數學題目出題引擎 (科展版) 🌟")
    print("*"*60)
    print("您可以輸入一題題目文字，系統將為您生成專屬練習場。")
    print("(目前支援：整數、分數、根式、多項式、微積分)")
    print("*"*60)
    
    while True:
        user_input = input("\n👉 請輸入題目文字 (或輸入 'exit' 退出): ").strip()
        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("再見！祝您學習愉快！")
            break
            
        if not user_input:
            continue
            
        # 執行引擎
        output = engine.generate_practice_set(input_text=user_input)
        
        if output["success"]:
            print(f"\n✅ 成功識別題型：{output['skill']}\n")
            print("============================================================")
            print("📚 您的專屬練習題目已生成：")
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
                    print(f"題：{result['question_text']}")
                    print(f"解：{result['correct_answer']}\n")
                    
            print("============================================================\n")
        else:
            print(f"\n❌ 抱歉：{output['error']}")

if __name__ == "__main__":
    main()
