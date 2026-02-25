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
    DEFAULT_PROVIDER = 'local' 

    # [實驗專用] 模型參數倉庫 (Coder Presets)
    # 用途：供 scripts/run_experiment.py 透過 Key 直接讀取並動態切換
    # 結構：Dictionary { 'safe-name': { config } }
    CODER_PRESETS = {
        # 1. Google Gemini (Cloud)
        'gemini-3-flash': {
            'provider': 'google',
            'model': 'gemini-3-flash-preview',
            'temperature': 0.1,
            'max_tokens': 65536,
            'description': 'Gemini 3.0 Flash Preview (SOTA Cloud)',

            # ★★★ [NEW] 安全設定：全部關閉 (BLOCK_NONE) ★★★
            # 這能防止模型因為誤判 "危險內容" 而拒絕生成數學題目
            'safety_settings': [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                },
            ]            
        },

        # 2. Qwen 3 14B (Local) [Thinking Disabled via Modelfile]
        'qwen3-14b': {
            'provider': 'local',
            'model': 'qwen3-14b-nothink:latest', # [Updated] User specific custom model
            'temperature': 0.3,                  # [Note] Keep slight creativity to avoid logic loops
            'max_tokens': 2048,                  # User requested 2048 to prevent truncation
            'extra_body': {
                'num_ctx': 32768,
                'num_gpu': -1,            
                'num_batch': 512,         
                'num_thread': 8,
                'keep_alive': "30m",
                'top_k': 40,
                'top_p': 0.9,
                'repeat_penalty': 1.1,
            },
            'description': 'Qwen3-14B (No-Think Custom)'
        },

        # 3. Qwen 2.5 14B (Local) - Legacy
        'qwen2.5-coder-14b': {
            'provider': 'local',
            'model': 'qwen2.5-coder:14b', 
            'temperature': 0.7,
            'max_tokens': 2048,
            'extra_body': {
                'num_ctx': 16384,
                'num_gpu': -1,
                'num_batch': 1024,
                'num_thread': 8,
                'num_predict': 2048,
                'keep_alive': "30m",
                'top_k': 10,
                'top_p': 0.9,
                'repeat_penalty': 1.15,
            },
            'description': 'Qwen 2.5 Coder 14B (Local)'
        },

        # 4. Qwen 3 8B (Local) [Thinking Allowed]
        'qwen3-8b': {
            'provider': 'local',
            'model': 'qwen3:8b',          # User's Qwen 3 8B model
            'temperature': 0.1,           # Low temp for stability
            'max_tokens': 8192,           # Increased to 8192 because Qwen3 uses extensive <think> blocks that easily hit 2048 and truncate.
            'extra_body': {
                'num_ctx': 32768,
                'num_gpu': -1,
                'num_batch': 1024,        # 8B is lighter, can handle larger batch
                'num_thread': 8,
                'keep_alive': "30m",
                'top_k': 40,
                'top_p': 0.95,
                'repeat_penalty': 1.1,
            },
            'description': 'Qwen3-8B (Thinking Allowed)'
        }
    }

    # ★ 系統角色指派
    # 這是 Web 介面預設使用的設定
    # 注意：run_experiment.py 執行時，會強制覆蓋這裡的 'coder'
    MODEL_ROLES = {
        'architect': {
            'provider': 'google',
            'model': 'gemini-2.5-flash', 
            'temperature': 0.7,
            'max_tokens': 1500,
        },
        
        # 預設工程師 (Qwen 3)
        'coder': CODER_PRESETS['qwen3-14b'], 
        
        'tutor': {
            'provider': 'local',
            'model': 'phi3.5'
        },
        
        'vision_analyzer': {
            'provider': 'gemini', 
            'model': 'gemini-2.5-flash' 
        },

        'default': CODER_PRESETS['qwen3-8b']
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

    # ==========================================
    # [NEW] 實驗參數設定 (Experiment Configuration)
    # ==========================================
    # 用途：統一管理評分、生成等實驗過程中的超時和穩定性參數
    # 優點：一次配置，全系統套用；換電腦或模型時只需改這裡，無需改程式碼
    
    EXECUTION_TIMEOUT = 10      # 評分時代碼執行的秒數限制 (原 5s -> 建議 10s)
    OLLAMA_TIMEOUT = 600        # 本地模型推理超時限制 (原 300s -> 建議 600s)
    STABILITY_REPS = 3          # L1.2 穩定性測試重複次數