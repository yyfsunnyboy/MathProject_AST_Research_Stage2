# -*- coding: utf-8 -*-
"""
=============================================================================
模組名稱 (Module Name): config.py
功能說明 (Description): 全域配置檔案，集中管理資料庫連線字串、檔案上傳路徑、密鑰設定、以及 AI 模型的角色指派與參數配置。
執行語法 (Usage): 由系統調用
版本資訊 (Version): V2.0
更新日期 (Date): 2026-01-13
維護團隊 (Maintainer): Math AI Project Team
=============================================================================
"""
import os

# 取得目前檔案所在的目錄 (絕對路徑)
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    全域設定檔 (Global Configuration)
    包含：資料庫、檔案上傳、以及科展專用的 AI 雙模組設定
    """

    # ==========================================
    # 1. 資料庫設定 (SQLite)
    # ==========================================
    # 建立 instance 資料夾 (如果不存在)
    instance_path = os.path.join(basedir, 'instance')
    os.makedirs(instance_path, exist_ok=True)
    
    # 構建資料庫檔案的絕對路徑
    db_path = os.path.join(instance_path, 'kumon_math.db')
    
    # 設定連線 URI
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ==========================================
    # 2. 檔案系統設定
    # ==========================================
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    
    # 確保上傳目錄存在
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # ==========================================
    # 3. 安全設定
    # ==========================================
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-me'

    # ==========================================
    # 4. ★★★ AI 雙模組設定 (科展實驗核心) ★★★
    # ==========================================
    
    # AI 模型調度中心
    
    # 預設供應商 (預設用 local 比較省錢)
    DEFAULT_PROVIDER = 'local' 

    # ★ 關鍵修改：角色與模型的對照表
    # 格式：'角色': {'provider': '供應商', 'model': '模型名稱'}
    MODEL_ROLES = {
        'architect': {
            'provider': 'google',
            'model': 'gemini-2.5-flash', 
            'temperature': 0.7, # 稍微高一點，讓它能歸納出不同的題型變化
            'max_tokens': 1500,  # 足夠寫出詳細的設計圖
        },        
        # 1. 工程師：專門寫 Code (精準、強迫症)
        'coder': {
            # 'provider': 'google',        # <--- 改用 Gemini 擔任工程師
            # 'model': 'gemini-2.5-flash',

            'provider': 'local',  
            'model': 'qwen2.5-coder:14b',             
            # --- 核心參數 ---
            'temperature': 0.1,   # 極低溫，確保邏輯鎖死
            'max_tokens': 2048,   # ✅ 優化: 1024 → 2048 (避免複雜代碼被截斷)
            # --- Ollama 特定參數 (透過 extra_body 傳遞) ---
            # 這是 OpenAI SDK 傳遞給 Ollama 的標準方式
            'extra_body': {
                'num_ctx': 8192,       # ✅ 優化: 4096 → 8192 (支持更長上下文)
                'num_gpu': -1,         # 強制使用所有 GPU
                'num_thread': 12,      # ✅ 優化: 6 → 12 (32GB RAM 可支持更多執行緒)
                # 'enable_thinking': False # Qwen Coder 通常沒有這個參數，建議移除以免報錯
            # ✅ 性能優化參數 (針對 RTX 5060 Ti 16GB)
            'num_batch': 1024,     # ✅ 關鍵優化: 256 → 1024 (GPU 利用率 60% → 95%, 速度 +40-50%)
            'num_predict': 2048,   # ✅ 優化: 1024 → 2048 (同 max_tokens)
            'num_keep': 4,         # 保留最近 4 個 token（加速推理）
            'repeat_penalty': 1.15,  # 避免重複代碼
            'top_k': 10,           # ✅ 優化: 20 → 10 (代碼生成更聚焦)
            'top_p': 0.9,          # ✅ 優化: 0.8 → 0.9 (OpenAI Codex 推薦值)
            }
        },
        
        # 2. 助教：專門解釋觀念 (溫柔、話多)
        'tutor': {
            'provider': 'local',
            'model': 'phi3.5'
        },
        
        # 3. 教授：專門解析課本與圖片 (聰明、視力好)
        'vision_analyzer': {
            'provider': 'gemini', 
            'model': 'gemini-1.5-flash' 
        },

        # 4. 預設值 (Default)
        'default': {
            'provider': 'local',
            'model': 'qwen2.5-coder:7b'
        }
    }

    # --- [Cloud] Google Gemini API Key ---
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
    # --- [Local] Ollama API URL ---
    LOCAL_API_URL = "http://localhost:11434/api/generate"
    
    # (舊變數保留以防其他檔案引用報錯，但建議盡快遷移)
    AI_PROVIDER = DEFAULT_PROVIDER
    GEMINI_MODEL_NAME = "gemini-2.5-flash"
    #LOCAL_MODEL_NAME = "qwen2.5-coder:3b"
    LOCAL_MODEL_NAME = "qwen2.5-coder:7b"
    
    # [V2.5 Data Enhancement] Experiment Batch Tag
    EXPERIMENT_BATCH = 'Run_V2.5_Elite'