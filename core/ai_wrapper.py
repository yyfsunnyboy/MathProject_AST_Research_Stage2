
# -*- coding: utf-8 -*-
"""
=============================================================================
模組名稱 (Module Name): core/ai_wrapper.py
功能說明 (Description): AI 模型驅動層 (AI Driver Layer)，負責將業務邏輯與底層 AI 供應商 (Google/Ollama) 解耦，並根據角色 (Role) 自動調度合適的模型。
執行語法 (Usage): 由系統調用
版本資訊 (Version): V3.0 (Modernized & Cleaned)
更新日期 (Date): 2026-02-13
維護團隊 (Maintainer): Math AI Project Team
=============================================================================
"""
# ==============================================================================

import os
import requests
import json
import logging
from flask import current_app
from config import Config

# --- SDK Import Strategy ---
# Priority: New SDK (google.genai) > Old SDK (google.generativeai)
try:
    from google import genai as new_genai
    HAS_NEW_SDK = True
except ImportError:
    new_genai = None
    HAS_NEW_SDK = False

try:
    import google.generativeai as old_genai
    HAS_OLD_SDK = True
except ImportError:
    old_genai = None
    HAS_OLD_SDK = False

# 設定 Logger
logger = logging.getLogger(__name__)

class LocalAIClient:
    """
    處理 Local Ollama API 的客戶端
    負責與本地運行的 Ollama 服務 (預設 Port 11434) 進行通訊。
    """
    def __init__(self, model_name, temperature=0.7, **kwargs):
        # [Config Adaption] 自動讀取 config.py 中的 LOCAL_API_URL，若無則使用預設值
        self.api_url = getattr(Config, 'LOCAL_API_URL', "http://localhost:11434/api/generate")
        self.model = model_name
        self.temperature = temperature
        
        # [V2.1 Refactor] 動態接收配置參數
        self.max_tokens = kwargs.get('max_tokens', 4096)
        self.extra_options = kwargs.get('extra_body', {})

    def generate_content(self, prompt):
        # 基礎 options
        options = {
            "temperature": self.temperature,
            "num_predict": self.max_tokens,
            "num_ctx": 8192  # Default fallback
        }
        
        # 合併 extra_body 中的參數 (如 num_ctx, num_gpu 等)
        # config.py 的設定優先權高於預設值
        if self.extra_options:
            options.update(self.extra_options)

        # [V2.2 Refactor] Support 'system' parameter in extra_body
        system_prompt = None
        if "system" in options:
             system_prompt = options.pop("system") # Remove from options, move to top-level
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": options
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        
        # [DEBUG] Check Payload Options
        # print(f"[DEBUG OLLAMA PAYLOAD]: num_predict={options.get('num_predict')}, num_ctx={options.get('num_ctx')}")
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=1200) # [FIX] Increase timeout for Thinking Models
            response.raise_for_status()
            result = response.json()
            
            # [DEBUG] Print raw result from Ollama
            print(f"[DEBUG OLLAMA RAW]: {str(result)[:500]}")
            
            # 取出 Ollama 回傳的真正內容與 token 計數
            generated_text = result.get("response", "")
            
            # [Fallback] 針對 Thinking Model (如 Qwen 3 / DeepSeek R1)
            # 如果 response 為空 (因為截斷或模型特性)，但有 thinking 内容，嘗試從 thinking 中提取
            if not generated_text and result.get("thinking"):
                print("[WARN] Response empty, falling back to 'thinking' content...")
                # 將 thinking 內容視為生成的文本，後續由 code_generator 的 cleanup 函數去提取代碼
                generated_text = result.get("thinking")
            prompt_tokens = result.get("prompt_eval_count", 0)
            completion_tokens = result.get("eval_count", 0)
            
            # 建立一個帶 usage 的 MockResponse（模擬 OpenAI / Gemini 風格）
            class MockResponse:
                def __init__(self, text, prompt_t, comp_t):
                    self.text = text
                    self.usage = type('Usage', (), {})()   # 簡單的 namespace
                    self.usage.prompt_tokens = prompt_t
                    self.usage.completion_tokens = comp_t
                    self.usage.total_tokens = prompt_t + comp_t
            
            return MockResponse(generated_text, prompt_tokens, completion_tokens)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Local AI (Ollama) Error: {str(e)}\n請確認 Ollama 是否正在運行於 {self.api_url}"
            logger.error(error_msg)
            class MockResponse:
                def __init__(self, text): 
                    self.text = error_msg
                    self.usage = type('Usage', (), {})()
                    self.usage.prompt_tokens = 0
                    self.usage.completion_tokens = 0
            return MockResponse(error_msg)

class GoogleAIClient:
    """
    處理 Google Gemini API 的客戶端 (Modernized for google.genai SDK)
    負責與 Google Generative AI 服務進行通訊 (需連網)。
    """
    def __init__(self, model_name, temperature=0.7, **kwargs):
        # 1. Config & API Key
        # Try multiple sources: kwargs > Config > environment variable
        api_key = kwargs.get('api_key') or getattr(Config, 'GEMINI_API_KEY', None)
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.error("❌ GEMINI_API_KEY not found! Please check your config.py or .env file.")
            raise ValueError("GEMINI_API_KEY is missing. 無法啟動 Google AI Client。")

        # 2. Model Parameters
        self.model_name = model_name
        self.temperature = temperature
        
        # Robust handling for max_tokens (Default to 8192 if None)
        mt = kwargs.get('max_tokens')
        self.max_tokens = mt if mt is not None else 8192
        
        # Safety Settings
        self.safety_settings = kwargs.get('safety_settings')

        # 3. SDK Initialization (Priority: New > Old)
        self.is_new_sdk = False
        
        # [2026-02-14] Try New SDK first with timeout protection
        # If New SDK fails, fall back to Old SDK with REST transport
        if HAS_NEW_SDK:
            try:
                # [FIX 2026-02-14] Don't set http_options timeout here
                # The New SDK has issues with timeout/deadline configuration
                # We rely on ThreadPoolExecutor timeout in call_ai_with_retry instead
                self.client = new_genai.Client(api_key=api_key)
                self.is_new_sdk = True
                print(f"[DEBUG] GoogleAIClient initialized with New SDK (google.genai) for model: {model_name}")
            except Exception as e:
                import traceback
                print(f"[WARN] New SDK init failed: {e}")
                print(f"[DEBUG] Full traceback:")
                traceback.print_exc()
                if HAS_OLD_SDK:
                    # [FIX] Force REST transport to avoid gRPC hanging on Windows
                    print(f"[INFO] Falling back to Old SDK (REST mode)...")
                    old_genai.configure(api_key=api_key, transport='rest')
                    self.model = old_genai.GenerativeModel(model_name)
                    self.is_new_sdk = False
                else:
                    raise ImportError("New SDK failed and Old SDK not found.")
        
        elif HAS_OLD_SDK:
            # === Old SDK Path (Legacy/Fallback) ===
            # [FIX] Force REST transport to avoid gRPC hanging on Windows
            old_genai.configure(api_key=api_key, transport='rest')
            self.model = old_genai.GenerativeModel(model_name)
            self.is_new_sdk = False
            print(f"[DEBUG] GoogleAIClient initialized with Old SDK (google.generativeai) in REST mode for model: {model_name}")
        
        else:
            raise ImportError("Critical Error: Neither 'google.genai' (New) nor 'google.generativeai' (Old) SDK is installed.")

    def generate_content(self, prompt):
        try:
            # [DEBUG] Print input config to verify parameter passing
            # print(f"[DEBUG] GoogleAIClient.generate_content called. MaxTokens={self.max_tokens}")
            
            if self.is_new_sdk:
                # ---------------------------------------------------------
                # New SDK Usage (google.genai)
                # ---------------------------------------------------------
                try:
                    from google.genai import types
                except ImportError:
                    types = None

                config_params = {"temperature": self.temperature}
                
                # Handle Max Tokens
                if self.max_tokens:
                    config_params["max_output_tokens"] = self.max_tokens

                # Handle Safety Settings
                # Convert dicts to types.SafetySetting for Strong Typing if available
                if self.safety_settings and types:
                    converted_settings = []
                    for s in self.safety_settings:
                        if isinstance(s, dict):
                            try:
                                converted_settings.append(
                                    types.SafetySetting(
                                        category=s.get('category'),
                                        threshold=s.get('threshold')
                                    )
                                )
                            except Exception:
                                # Fallback to dict if conversion fails
                                converted_settings.append(s)
                        else:
                            converted_settings.append(s)
                    config_params["safety_settings"] = converted_settings
                elif self.safety_settings:
                     config_params["safety_settings"] = self.safety_settings

                # Construct Typed Config Object (Best Practice)
                final_config = config_params
                if types:
                    try:
                        final_config = types.GenerateContentConfig(
                            temperature=self.temperature,
                            max_output_tokens=self.max_tokens,
                            stop_sequences=[],  # Explicitly disable stop sequences to prevent premature truncation
                            safety_settings=config_params.get("safety_settings")
                        )
                    except Exception as e:
                        print(f"[WARN] Failed to create GenerateContentConfig object: {e}. Using dict config.")
                        pass
                
                # Call Generate
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=final_config
                )
                
                return response

            else:
                # ---------------------------------------------------------
                # Old SDK Usage (google.generativeai) -> LEGACY PATH
                # ---------------------------------------------------------
                config = old_genai.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    stop_sequences=[]  # Explicitly disable stop sequences to prevent premature truncation
                )
                
                kwargs = {}
                if self.safety_settings:
                    kwargs['safety_settings'] = self.safety_settings

                response = self.model.generate_content(prompt, generation_config=config, **kwargs)
                return response

        except Exception as e:
            error_msg = f"Google AI Error: {str(e)}"
            logger.error(error_msg)
            # Retain robust error handling
            class MockResponse:
                def __init__(self, text): self.text = f"Error: {text}"
            return MockResponse(error_msg)

def get_ai_client(role='default'):
    """
    [Factory Method] AI 客戶端工廠
    根據 config.py 中 MODEL_ROLES 的設定，實例化對應的 Client (Local 或 Google)。
    """
    # 1. 讀取角色設定
    role_config = Config.MODEL_ROLES.get(role, Config.MODEL_ROLES.get('default'))
    
    provider = role_config.get('provider', 'local').lower()
    model_name = role_config.get('model', 'qwen2.5-coder:7b')
    temperature = role_config.get('temperature', 0.7)
    
    # 提取更多配置參數
    max_tokens = role_config.get('max_tokens', 4096)
    extra_body = role_config.get('extra_body', {})
    safety_settings = role_config.get('safety_settings')

    # 2. 智慧派發 (Smart Dispatch)
    if provider in ['google', 'gemini']:
        return GoogleAIClient(model_name, temperature, max_tokens=max_tokens, safety_settings=safety_settings)
    elif provider == 'local':
        return LocalAIClient(model_name, temperature, max_tokens=max_tokens, extra_body=extra_body)
    else:
        logger.warning(f"⚠️ 未知的 Provider: {provider}，強制切換至 Local 模式")
        return LocalAIClient(model_name, temperature, max_tokens=max_tokens, extra_body=extra_body)

def call_ai_with_retry(client, prompt, max_retries=3, retry_delay=5, verbose=False, timeout=None, ablation_id=None):
    """
    [Utility] 帶有自動重試機制的 AI 呼叫函數 (Shared Logic)
    
    Args:
        client: AI Client 實例 (GoogleAIClient 或 LocalAIClient)
        prompt: 提示文本
        max_retries: 最大重試次數
        retry_delay: 重試等待秒數
        verbose: 是否打印重試日誌
        timeout: 單次請求的超時時間（秒），如果為 None 則根據模型和 ablation_id 自動設定
        ablation_id: Ablation 策略 ID (1=Ab1, 2=Ab2, 3=Ab3)，用於動態設定 timeout
    
    Returns:
        response: AI 回傳的 Response 對象 (需自行處理 .text 或 .usage)
    """
    import time
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
    last_exception = None
    
    # [2026-02-14] Dynamic Timeout based on Model Type and Ablation ID
    if timeout is None:
        if isinstance(client, GoogleAIClient):
            # Gemini: Ab1=180s, Ab2/Ab3=120s
            timeout = 180 if ablation_id == 1 else 120
        elif isinstance(client, LocalAIClient):
            # [FIX] LocalAIClient stores model name in 'model' attribute, not 'model_name'
            # Also handle potential attribute mismatch safely
            model_name = getattr(client, 'model', getattr(client, 'model_name', '')).lower()
            if '14b' in model_name:
                # Qwen 14B: Ab1=300s, Ab2/Ab3=240s
                timeout = 300 if ablation_id == 1 else 240
            elif '8b' in model_name:
                # Qwen 8B: Ab1=300s, Ab2/Ab3=120s
                timeout = 300 if ablation_id == 1 else 120
            else:
                # Unknown local model: conservative 300s
                timeout = 300
        else:
            # Unknown client type: conservative 300s
            timeout = 300
    
    for attempt in range(max_retries):
        try:
            if attempt > 0 and verbose:
                 print(f"   🔄 AI 生成重試 (Attempt {attempt+1}/{max_retries})...")
            
            # [執行請求 with Timeout Protection]
            # [FIX 2026-02-14] Manually manage Executor to avoid blocking on __exit__
            # With `with ThreadPoolExecutor`, it calls shutdown(wait=True) which waits for stuck threads
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(client.generate_content, prompt)
            
            try:
                response = future.result(timeout=timeout)
                # Success: Return response and shutdown
                executor.shutdown(wait=False)
                return response
            except FuturesTimeoutError:
                # Timeout: Kill/Abandon the stuck thread immediately
                # Don't wait for it to finish (that defeats the purpose of timeout)
                future.cancel()
                executor.shutdown(wait=False, cancel_futures=True)
                raise TimeoutError(f"AI request timed out after {timeout} seconds")
            except Exception as e:
                # Other error
                executor.shutdown(wait=False)
                raise e
            
        except Exception as e:
            last_exception = e
            if verbose:
                logger.warning(f"⚠️ AI Call Failed (Attempt {attempt+1}): {e}")
            
            if attempt < max_retries - 1:
                if verbose:
                    print(f"   ⚠️ 等待 {retry_delay} 秒後重試...")
                time.sleep(retry_delay)
    
    # 所有重試均失敗
    raise last_exception if last_exception else Exception("AI call failed after all retries")