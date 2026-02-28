# -*- coding: utf-8 -*-
"""
Math-Master: AI-Driven Education Platform (2026 YC-Awards Project)
Module: Environment Sanitizer & Aseptic Bootloader
-------------------------------------------------------------------------
【功能描述】
本腳本為 Math-Master 專案的「核心啟動器」。其主要任務是實施「環境無菌化 (Aseptic Booting)」，
解決 Large Language Models (LLM) 在 JIT (Just-in-Time) 代碼生成過程中常見的
「指令污染 (Instruction Pollution)」與「模組快取 (Module Caching)」問題。

【核心技術亮點】
1. 物理隔離 (Physical Isolation): 強制清空所有動態生成的 Python 腳本，防止舊題型邏輯殘留。
2. 顯存重置 (VRAM Reset): 透過 Ollama API 強制卸載模型，抹除 5060 Ti 上的視覺上下文快取。
3. 零快取啟動 (Zero-Cache Execution): 禁用 Python 的 pyc 編譯機制，確保每一行代碼都是即時解析。
-------------------------------------------------------------------------
Author: Math-Master Dev Team
Date: 2026-02-28
"""

import os
import shutil
import sys
import subprocess
import time

def sanitize_environment():
    # 設置標題裝飾
    print("="*60)
    print("      Math-Master 2026 - 環境無菌化啟動程序啟動中...")
    print("="*60)

    # 1. 清理 Python 字節碼快取
    # 目的：防止 Python 執行舊版編譯後的 .pyc 檔案，確保新邏輯立即生效
    print("\n🧹 [Step 1/4] 正在掃描並清理 Python 檔案快取 (__pycache__)...")
    cache_count = 0
    for root, dirs, files in os.walk('.'):
        for d in dirs:
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d))
                cache_count += 1
    print(f"   >>> 成功清理 {cache_count} 個快取節點，確保邏輯純淨。")

    # 2. 初始化 JIT 存儲空間
    # 目的：移除所有舊的 generate_live_xxx.py，保證演示現場只會看到最新的題目腳本
    print("\n🗑️ [Step 2/4] 正在重置 JIT 動態程式碼儲存區 (generated_scripts)...")
    gen_path = "./generated_scripts"
    if os.path.exists(gen_path):
        shutil.rmtree(gen_path)
    os.makedirs(gen_path, exist_ok=True)
    print("   >>> 資料夾已完成物理重置，防止「舊模板污染」現象發生。")

    # 3. 釋放 GPU 顯存與上下文記憶
    # 目的：重啟 Qwen3-VL 的神經元狀態，避免它「記得」之前的絕對值題目
    print("\n🧠 [Step 3/4] 正在對 RTX 5060 Ti 執行顯存重置 (VRAM Reset)...")
    try:
        # 強制停止模型以清空 Ollama 內部的 Context Window
        # 這能有效解決 AI 因上下文慣性導致的「題目複雜化」Bug
        subprocess.run(["ollama", "stop", "qwen3-vl"], capture_output=True, check=True)
        print("   >>> Ollama 模型已強制卸載，視覺記憶區(Vision Context)已完全清空。")
    except Exception as e:
        print(f"   >>> [警報] 顯存重置失敗，請確認 Ollama 服務是否正常啟動。")

    # 4. 啟動 Web 核心
    # 目的：以 -B 參數啟動，徹底停用 Python 的寫入快取行為
    print("\n🚀 [Step 4/4] 正在以『零快取模式 (Zero-Cache Mode)』啟動 Flask 核心...")
    print("-" * 60)
    print("【系統狀態】後端服務即將於 127.0.0.1:5000 運行。")
    print("【特別指示】演示期間請勿手動修改 generated_scripts 內容。")
    print("-" * 60 + "\n")

    # 延遲 1 秒確保所有資源釋放完畢
    time.sleep(1)

    # 使用 sys.executable 確保使用當前環境的 Python
    # -B 參數：不寫入 .pyc 檔案
    # -u 參數：強制標準輸出 (stdout) 不緩衝，方便即時觀察 AI 日誌
    try:
        subprocess.run([sys.executable, "-B", "-u", "app.py"])
    except KeyboardInterrupt:
        print("\n\n🛑 [系統停止] Math-Master 已安全關閉。")

if __name__ == "__main__":
    sanitize_environment()