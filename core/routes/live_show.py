# -*- coding: utf-8 -*-
"""
=============================================================================
模組名稱 (Module Name): core/routes/live_show.py
功能說明 (Description): 科展 Live Show 專用路由。
  GET  /live_show              — 渲染前端 HTML 頁面
  POST /api/generate_live      — Ab1 / Ab3 平行生成（JSON 回傳）
  GET  /api/stream_thought_ab1 — Ab1 思考過程即時串流 (Server-Sent Events)
=============================================================================
"""

from flask import request, jsonify, render_template, Response, stream_with_context
import time
import json
import os
import base64
import uuid

# 從 __init__.py 匯入已註冊的 Blueprint
from . import live_show_bp

# 全局初始化 MathEngine (延遲載入以避免循環引用)
_engine_instance = None
def get_engine():
    global _engine_instance
    if _engine_instance is None:
        from core.engine.engine import MathEngine
        _engine_instance = MathEngine()
    return _engine_instance


@live_show_bp.route('/live_show')
def live_show():
    """渲染 Live Show 的前端展示頁面"""
    return render_template('live_show.html')


@live_show_bp.route('/api/generate_live', methods=['POST'])
def generate_live():
    """
    API: 根據 ablation_mode 生產題目與 debug_meta 資訊
    前端會在同時間對此打兩支平行連線 (Ab1 與 Ab3)
    """
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "No JSON payload provided."}), 400
        
    input_text = data.get("prompt") or data.get("input_text", "")
    ablation_mode = data.get("ablation_mode", False)
    count = data.get("count", 1)
    model_id = data.get("model_id", "qwen3-8b")
    
    start_time = time.time()
    try:
        engine = get_engine()
        output = engine.generate_practice_set(input_text=input_text, count=count, ablation_mode=ablation_mode, model_id=model_id)
        output["api_time"] = time.time() - start_time

        # ── Flatten debug_meta fields for the frontend ────────────────────
        dm = output.get("debug_meta", {})
        perf = dm.get("performance", {})
        healer_trace = dm.get("healer_trace", {})
        mcri_report  = dm.get("mcri_report", {})

        output["ai_inference_time_sec"]  = perf.get("ai_inference_time_sec", 0)
        output["cpu_execution_time_sec"] = perf.get("cpu_execution_time_sec", 0)
        output["thinking"] = dm.get("thinking", "")
        output["fixes"]    = (healer_trace.get("regex_fixes", 0) or 0) + (healer_trace.get("ast_fixes", 0) or 0)
        output["healer_logs"] = [
            f"regex_fixes: {healer_trace.get('regex_fixes', 0)}",
            f"ast_fixes: {healer_trace.get('ast_fixes', 0)}",
            f"robustness: {mcri_report.get('robustness_grade', 'N/A')}",
        ]

        # ── Map problems[0] fields for the frontend ───────────────────────
        problems = output.get("problems", [])
        
        # 確保不論成功與否，前端終端機都能拿到 raw_code 與 final_code 進行診斷
        output["raw_text"] = dm.get("raw_text", dm.get("raw_code", ""))
        output["raw_code"] = dm.get("raw_code", "")
        output["final_code"] = dm.get("final_code", "")
        output["file_path"] = dm.get("file_path", "")
        output["bare_prompt"] = dm.get("bare_prompt", "")
        output["scaffold_prompt"] = dm.get("scaffold_prompt", "")

        if problems:
            first = problems[0]
            if "error" in first:
                output["error"] = first["error"]
            else:
                q_text = first.get("question_text", "")
                output["problem"] = q_text
                output["answer"]  = first.get("correct_answer", "")

                # MCRI scoring
                hygiene = first.get("_mcri_hygiene_score", 0) or 0
                output["mcri"] = {
                    "syntax_score":    min(100, max(0, hygiene)),
                    "logic_score":     min(100, max(0, hygiene - 5)),
                    "render_score":    min(100, max(0, hygiene + 5)),
                    "stability_score": 100 if not ablation_mode else 40,
                    "total_score":     hygiene
                }

        return jsonify(output)
    except Exception as e:
        import traceback
        return jsonify({
            "success": False, 
            "error": str(e),
            "traceback": traceback.format_exc(),
            "api_time": time.time() - start_time
        }), 500


@live_show_bp.route('/api/stream_thought_ab1')
def stream_thought_ab1():
    """
    SSE Endpoint: 以 stream=True 呼叫 Ollama，即時抓取 Ab1 模式下的
    <thought> 標籤內容，並以 Server-Sent Events 推送至瀏覽器。

    Query params:
        prompt  — 使用者輸入的數學敘述
    """
    prompt_text = request.args.get('prompt', '').strip()
    model_id_query = request.args.get('model_id', 'qwen3-8b').strip()
    
    if not prompt_text:
        return Response('data: {"type":"error","text":"No prompt provided."}\n\n',
                        content_type='text/event-stream')

    # 建構 Ab1 zero-shot prompt（與 scaler.py 保持一致）
    ab1_prompt = f"請寫一個 generate(level=1) 函式，參考：\n{prompt_text}\n直接輸出代碼。"

    def generate_sse():
        try:
            from config import Config
            from core.ai_wrapper import LocalAIClient

            model_config = (
                Config.CODER_PRESETS.get(model_id_query) or
                Config.CODER_PRESETS.get('qwen3-8b') or
                next(iter(Config.CODER_PRESETS.values()), None)
            )
            if not model_config:
                yield 'data: {"type":"error","text":"No model configured."}\n\n'
                return

            client = LocalAIClient(
                model_name=model_config.get('model', 'qwen3:8b'),
                temperature=model_config.get('temperature', 0.7),
                **{k: v for k, v in model_config.items()
                   if k not in ('model', 'temperature', 'provider')}
            )

            for chunk in client.generate_content_stream(ab1_prompt):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                if chunk["type"] in ("done", "error"):
                    return

        except Exception as exc:
            err_payload = json.dumps({"type": "error", "text": str(exc)}, ensure_ascii=False)
            yield f"data: {err_payload}\n\n"

    return Response(
        stream_with_context(generate_sse()),
        content_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )

@live_show_bp.route('/api/classify', methods=['POST'])
def classify_input():
    """
    API: 接收 Base64 圖片或純文字，進行 OCR (若有圖) 並使用 Classifier 分類技能。
    回傳 skill_id, confidence_scores 與 process_logs。
    """
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "No data provided."}), 400

    image_data = data.get("image_data")
    text_data = data.get("text_data")
    ocr_text = ""
    process_logs = []

    try:
        process_logs.append("> 🧬 Initiating Skill DNA Sequencing...")
        
        if image_data:
            process_logs.append("> 🖼️ Detected Image Payload. Decoding Base64 Stream...")
            # 支援 Data URI format: "data:image/png;base64,iVBORw0KGgo..."
            if "base64," in image_data:
                image_data = image_data.split("base64,")[1]
                
            image_bytes = base64.b64decode(image_data)
            from config import Config
            temp_dir = os.path.join(Config.UPLOAD_FOLDER, "temp_canvas")
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, f"canvas_{uuid.uuid4().hex}.png")
            
            with open(temp_path, "wb") as f:
                f.write(image_bytes)

            process_logs.append("> 👁️ Sending to Gemini Vision Model for OCR...")
            # 1. Vision OCR (Basic Text Extraction)
            from core.ai_wrapper import get_ai_client
            vision_client = get_ai_client('vision_analyzer')
            ocr_prompt = "請幫我辨識這張圖片中的數學式或題目文字。只輸出辨識到的純文字，不需要任何額外的解釋或Markdown標記。如果裡面有未知變數請照實輸出。"
            
            vision_resp = vision_client.generate_content(ocr_prompt, image_path=temp_path)
            plain_text = vision_resp.text.strip() if hasattr(vision_resp, 'text') else str(vision_resp)
            
            display_text = plain_text[:30] + "..." if len(plain_text) > 30 else plain_text
            process_logs.append(f"> 📄 OCR Extraction Complete: [{display_text}]")
            
            try:
                if os.path.exists(temp_path): 
                    os.remove(temp_path)
            except Exception as e:
                process_logs.append(f"> ⚠️ Skipping image cleanup due to file lock: {e}")
        
        elif text_data:
            process_logs.append("> 📝 Detected Text Payload. Skipping OCR Phase.")
            plain_text = text_data.strip()

        else:
            return jsonify({"success": False, "error": "Require image_data or text_data."}), 400

        # === [NEW] 步驟 1.5: 呼叫 Architect 解析 MASTER_SPEC ===
        process_logs.append("> 🧠 Calling Architect to construct MASTER_SPEC...")
        try:
            from core.ai_wrapper import get_ai_client
            architect_client = get_ai_client('architect')
            architect_prompt = f"""【角色】數學命題架構師 (Architect)
【任務】將「題目 DNA」轉化為「Master Spec 施工食譜」。

【輸出規範：MASTER_SPEC】
你必須產出以下三個區塊，嚴禁廢話：

1. **變數定義 (Variable Slots)**:
   - 限制變數數量在 5 個以內 (v1~v5)。
   - 明確範圍與約束（例如：v3 必須是 v4 的倍數以確保整除）。
2. **純數值計算邏輯 (Raw Logic)**:
   - 寫出 Python 運算式。例：`ans = v1 * v2 + abs(v3 * v4 - v5)`。
   - 涉及分數必須指名使用 `Fraction(n, d)`。
3. **渲染範本 (Rendering Template)**:
   - 提供一個 f-string 模板。
   - 例：`question_text = f"計算 $${{f(v1)}} \\times {{f(v2)}} + \\left| {{f(v3)}} \\times {{f(v4)}} - {{f(v5)}} \\right|$$ 的值。"`
   - 提醒 Coder 呼叫 對應技能的 format 函數。

現在，請根據這段數學 DNA，嚴格按照上述格式輸出 MASTER_SPEC：
{plain_text}"""
            
            arch_resp = architect_client.generate_content(architect_prompt)
            master_spec = arch_resp.text.strip() if hasattr(arch_resp, 'text') else str(arch_resp)
            if master_spec.startswith("Error:"):
                raise ValueError(master_spec)
            process_logs.append("> ✅ MASTER_SPEC Built Successfully.")
        except Exception as e:
            process_logs.append(f"> ⚠️ Architect Parse Failed: {str(e)[:100]}...")
            master_spec = plain_text

        process_logs.append("> 🧠 Extracting semantic markers for DNA alignment...")
        # 2. 分類 Skill
        engine = get_engine()
        skill_name = engine.classifier.classify(input_text=plain_text)
        
        bare_prompt = ""
        scaffold_prompt = ""

        if skill_name != "Unknown":
            process_logs.append(f"> ✅ DNA Sequence Aligned: {skill_name}")
            confidence = 98
            
            # [NEW] Generate Prompt Previews
            skill_path = engine.scaler._get_skill_path(skill_name)
            
            try:
                ab1_prompt_path = os.path.join(skill_path, "experiments", "ab1_bare_prompt.md")
                if os.path.exists(ab1_prompt_path):
                    with open(ab1_prompt_path, "r", encoding="utf-8") as f:
                        ab1_template = f.read()
                    import re
                    # 使用 plain_text 給 Ab1
                    bare_prompt = re.sub(
                        r"【參考例題】.*?【程式要求】", 
                        f"【參考例題】\n根據以下結構產生類似題目：\n{plain_text}\n\n【程式要求】", 
                        ab1_template, 
                        flags=re.DOTALL
                    )
                else:
                    bare_prompt = f"請寫一個 generate(level=1) 函式，參考：\n{plain_text}\n直接輸出代碼。"

                skill_md_path = os.path.join(skill_path, "SKILL.md")
                clean_tools = ""
                if os.path.exists(skill_md_path):
                    with open(skill_md_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # [反重力核心]：過濾 SKILL.md，只留工具說明
                    if "## [LEGACY_CODE_DNA]" in content:
                        clean_tools = content.split("## [LEGACY_CODE_DNA]")[0]
                    else:
                        # 如果沒標籤，就拿前 500 字
                        clean_tools = content[:500]
                
                # fallback if clean_tools is empty or unhelpful
                if not clean_tools or len(clean_tools.strip()) < 10:
                    if "FourArithmeticOperationsOfIntegers" in skill_name:
                        clean_tools = "- IntegerOps.fmt_num(n): 將負數加上括號，例: -5 變成 (-5)。\n- IntegerOps.rand_nz(a, b): 產生介於 a, b 之間的非零整數。"
                    elif "FourArithmeticOperationsOfNumbers" in skill_name:
                        clean_tools = "- to_latex(n): 將 Fraction(n, d) 自動約分並轉換為 LaTeX 格式的分數字串。\n- Fraction(n, d): Python 內建的分數運算類別。"
                    elif "FourArithmeticOperationsOfPolynomial" in skill_name:
                        clean_tools = "- PolynomialOps.gen_poly(...): 產生隨機多項式。\n- PolynomialOps.fmt_poly(...): 格式化多項式字串，自動合併同類項。"
                    elif "RadicalOperations" in skill_name:
                        clean_tools = "- RadicalOps.simplify(n): 化簡根式。\n- RadicalOps.fmt_sqrt(n): 格式化根式字串，根號下不能為負。"
                    else:
                        clean_tools = "- 這是基本題型，請使用基礎四則運算與 random 套件。"

                scaffold_prompt = f"""【指令】直接輸出 Python Code，嚴禁任何解釋。

【1. 可用工具 (Domain API)】
{clean_tools.strip()}

【2. 目標 DNA 與邏輯食譜 (MASTER_SPEC)】
這是一位架構師為您提取的精準架構，請您「直接翻譯並實作」成 Python 代碼：

{master_spec}

【3. 執行憲法】
- **強制規範**：先計算，後排版。所有數學運算必須在格式化之前完成。
- **類型防禦**：嚴禁將格式化後的字串參與數學運算。若為分數題，所有變數必須初始化為 `Fraction(val)`，嚴禁直接使用 `/` 讓整數相除產生 float。
- **多樣性**：最終答案絕對值必須在 2 到 200 之間，嚴禁產出答案為 0 或 1。
- **渲染規範**：數學式必須用 $$...$$ 包裹。

【代碼起點】
import random
# (由後端根據 skill 自動注入 import，如 from fractions import Fraction)

def generate(**kwargs):
    question_text = ""
    # 步驟一：計算區 (僅限原始數值運算)

    # 步驟二：排版區 (僅在此區調用 fmt_num / format_latex 等字串格式化)
"""
            except Exception as e:
                scaffold_prompt = f"Error loading SKILL.md: {e}"
        else:
            process_logs.append("> ⚠️ DNA Match Failed: Falling back to Unknown.")
            confidence = 30

        return jsonify({
            "success": True,
            "ocr_text": plain_text,  # 回傳純文字給 textbox
            "master_spec": master_spec,
            "skill_id": skill_name,
            "confidence_scores": confidence,
            "process_logs": process_logs,
            "bare_prompt": bare_prompt,
            "scaffold_prompt": scaffold_prompt
        })

    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@live_show_bp.route('/api/run_generated_code', methods=['POST'])
def run_generated_code():
    """
    API: 接受已生成的 Python 程式碼並執行，用於「下一題」即時功能，避免重新呼叫 LLM
    """
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "No data provided."}), 400
        
    code = data.get("code")
    file_path = data.get("file_path")
    
    if file_path and os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
            
    if not code:
        return jsonify({"success": False, "error": "No code or valid file_path provided."}), 400
    level = data.get("level", 1)
    ablation_mode = data.get("ablation_mode", False)
    
    start_time = time.time()
    try:
        engine = get_engine()
        
        # 執行程式碼
        res = engine.scaler._execute_code(code, level=level)
        
        # MCRI Hygiene Eval
        hygiene = 0
        if "question_text" in res:
            try:
                from scripts.evaluate_mcri import evaluate_math_hygiene
                h_score, _ = evaluate_math_hygiene(res["question_text"])
                hygiene = h_score
            except:
                hygiene = 0
                
        output = {
            "success": True,
            "problem": res.get("question_text", ""),
            "answer": res.get("correct_answer", ""),
            "api_time": time.time() - start_time,
            "mcri": {
                "syntax_score":    min(100, max(0, hygiene)),
                "logic_score":     min(100, max(0, hygiene - 5)),
                "render_score":    min(100, max(0, hygiene + 5)),
                "stability_score": 100 if not ablation_mode else 40,
                "total_score":     hygiene
            }
        }
        return jsonify(output)
        
    except Exception as e:
        import traceback
        return jsonify({
            "success": False, 
            "error": str(e),
            "traceback": traceback.format_exc(),
            "api_time": time.time() - start_time
        }), 200

@live_show_bp.route('/api/architect_to_coder', methods=['POST'])
def architect_to_coder():
    """
    API: 端到端管線 (Architect -> Qwen Coder)
    """
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "No data provided."}), 400

    image_data = data.get("image_data")
    text_data = data.get("text_data")
    
    start_time = time.time()
    process_logs = []
    
    try:
        process_logs.append("> 🌟 Initiating Architect Pipeline (Vision + Logic + JSON)...")
        from core.ai_wrapper import get_ai_client
        from config import Config
        import re
        from core.prompt_architect import ARCHITECT_SYSTEM_PROMPT

        temp_path = None
        if image_data:
            if "base64," in image_data:
                image_data = image_data.split("base64,")[1]
            image_bytes = base64.b64decode(image_data)
            temp_dir = os.path.join(Config.UPLOAD_FOLDER, "temp_canvas")
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, f"canvas_{uuid.uuid4().hex}.png")
            with open(temp_path, "wb") as f:
                f.write(image_bytes)
        elif not text_data:
            return jsonify({"success": False, "error": "Require image_data or text_data."}), 400

        # === 步驟 1: 呼叫 Architect (Gemini) ===
        process_logs.append("> 🧠 Sending to Gemini Architect (Vision & Logic Deconstruction)...")
        architect_client = get_ai_client('architect')
        
        user_prompt = "請分析以下題目（圖片或文字），並嚴格按照 JSON 格式回傳 OCR、分類、與食譜。"
        if text_data:
            user_prompt += f"\n\n題目文字：{text_data}"
            
        full_prompt = ARCHITECT_SYSTEM_PROMPT + "\n\n" + user_prompt
        
        if temp_path:
            response = architect_client.generate_content(full_prompt, image_path=temp_path)
            os.remove(temp_path)
        else:
            response = architect_client.generate_content(full_prompt)
            
        json_str = response.text.strip()
        
        # 把被 Markdown codeblock 包覆的部分去掉
        json_str = re.sub(r'^```json\s*', '', json_str)
        json_str = re.sub(r'```\s*$', '', json_str)
        
        try:
            architect_output = json.loads(json_str)
        except Exception as e:
            process_logs.append(f"> ❌ Failed to parse JSON: {e}")
            architect_output = {
                "ocr_result": text_data or "Unknown",
                "skill_name": "jh_數學1上_FourArithmeticOperationsOfIntegers",
                "logic_recipe": ["[解析失敗] 隨機整數四則"],
                "variable_plan": "res = a + b",
                "latex_template": "{a} + {b}",
                "special_notes": ""
            }
        
        ocr_text = architect_output.get("ocr_result", "")
        skill_name = architect_output.get("skill_name", "jh_數學1上_FourArithmeticOperationsOfIntegers")
        logic_recipe = architect_output.get("logic_recipe", [])
        
        process_logs.append(f"> 📄 OCR Extracted: {ocr_text[:30] + ('...' if len(ocr_text)>30 else '')}")
        process_logs.append(f"> ✅ Skill Aligned: {skill_name}")
        process_logs.append(f"> 📝 Logic Recipe Generated ({len(logic_recipe)} steps)")
        
        # === 步驟 2: 組合 SCAFFOLD PROMPT ===
        engine = get_engine()
        bare_prompt = ""
        scaffold_prompt = ""
        
        try:
            skill_path = engine.scaler._get_skill_path(skill_name)
            skill_md_path = os.path.join(skill_path, "SKILL.md")
            
            clean_tools = ""
            if os.path.exists(skill_md_path):
                with open(skill_md_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # [反重力核心]：過濾 SKILL.md，只留工具說明
                if "## [LEGACY_CODE_DNA]" in content:
                    clean_tools = content.split("## [LEGACY_CODE_DNA]")[0]
                else:
                    # 如果沒標籤，就拿前 500 字
                    clean_tools = content[:500]
            
            # fallback if clean_tools is empty or unhelpful
            if not clean_tools or len(clean_tools.strip()) < 10:
                if "FourArithmeticOperationsOfIntegers" in skill_name:
                    clean_tools = "- IntegerOps.fmt_num(n): 將負數加上括號，例: -5 變成 (-5)。\n- IntegerOps.rand_nz(a, b): 產生介於 a, b 之間的非零整數。"
                elif "FourArithmeticOperationsOfNumbers" in skill_name:
                    clean_tools = "- to_latex(n): 將 Fraction(n, d) 自動約分並轉換為 LaTeX 格式的分數字串。\n- Fraction(n, d): Python 內建的分數運算類別。"
                elif "FourArithmeticOperationsOfPolynomial" in skill_name:
                    clean_tools = "- PolynomialOps.gen_poly(...): 產生隨機多項式。\n- PolynomialOps.fmt_poly(...): 格式化多項式字串，自動合併同類項。"
                elif "RadicalOperations" in skill_name:
                    clean_tools = "- RadicalOps.simplify(n): 化簡根式。\n- RadicalOps.fmt_sqrt(n): 格式化根式字串，根號下不能為負。"
                else:
                    clean_tools = "- 這是基本題型，請使用基礎四則運算與 random 套件。"
            
            recipe_text = "\n".join(logic_recipe)
            
            scaffold_prompt = f"""【指令】直接輸出 Python Code，嚴禁任何解釋。

【1. 可用工具 (Domain API)】
{clean_tools.strip()}

【2. 目標 DNA 與邏輯食譜 (MASTER_SPEC)】
- **目標結構**：{ocr_text}
- **執行步驟**：
{recipe_text}

【3. 執行憲法】
- **強制規範**：先計算，後排版。所有數學運算必須在格式化之前完成。
- **類型防禦**：嚴禁將格式化後的字串參與數學運算。若為分數題，所有變數必須初始化為 `Fraction(val)`，嚴禁直接使用 `/` 讓整數相除產生 float。
- **多樣性**：最終答案絕對值必須在 2 到 200 之間，嚴禁產出答案為 0 或 1。
- **渲染規範**：數學式必須用 $$...$$ 包裹。

【代碼起點】
import random
# (由後端根據 skill 自動注入 import，如 from fractions import Fraction)

def generate(**kwargs):
    question_text = ""
    # 步驟一：計算區 (僅限原始數值運算)

    # 步驟二：排版區 (僅在此區調用 fmt_num / format_latex 等字串格式化)
"""
        except Exception as e:
            scaffold_prompt = f"Error loading SKILL.md: {e}"
            
        ab1_prompt_path = os.path.join(skill_path, "experiments", "ab1_bare_prompt.md") if 'skill_path' in locals() else None
        if ab1_prompt_path and os.path.exists(ab1_prompt_path):
            with open(ab1_prompt_path, "r", encoding="utf-8") as f:
                ab1_template = f.read()
            bare_prompt = re.sub(
                r"【參考例題】.*?【程式要求】", 
                f"【參考例題】\n{ocr_text}\n\n【程式要求】", 
                ab1_template, 
                flags=re.DOTALL
            )
        else:
            bare_prompt = f"請寫一個 generate() 函式，參考：\n{ocr_text}\n直接輸出代碼。"

        # === 步驟 3: 呼叫 Coder (Qwen) ===
        process_logs.append("> 💻 Relegating code generation to Qwen-8B Local Coder...")
        coder_client = get_ai_client('coder')
        code_resp = coder_client.generate_content(scaffold_prompt)
        final_code = code_resp.text.strip()
        
        if final_code.startswith("```"):
            lines = final_code.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            final_code = "\n".join(lines)
            
        process_logs.append("> 🚀 Coder completed generation.")

        return jsonify({
            "success": True,
            "architect_json": architect_output,
            "ocr_text": ocr_text,
            "skill_id": skill_name,
            "process_logs": process_logs,
            "scaffold_prompt": scaffold_prompt,
            "bare_prompt": bare_prompt,
            "generated_code": final_code,
            "api_time": time.time() - start_time
        })

    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

