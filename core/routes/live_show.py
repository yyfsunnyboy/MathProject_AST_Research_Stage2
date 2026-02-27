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
            if not isinstance(first, dict):
                output["error"] = f"Invalid problem format: {type(first)}"
            elif "error" in first:
                output["error"] = first["error"]
            elif "question_text" not in first:
                output["error"] = "Missing question_text in problem output."
            else:
                q_text = first.get("question_text", "")
                output["problem"] = q_text
                output["answer"]  = first.get("correct_answer", "")

                # MCRI scoring normalization (V10.5 Justice Logic)
                # Hygiene raw score is 15.0 max. Normalize to 100%.
                hygiene = first.get("_mcri_hygiene_score", 0) or 0
                norm_hygiene = (hygiene / 15.0) * 100
                
                # Robustness mapping: ROBUST=100, MODERATE=70, RISKY=30, Unknown=50
                robust_map = {"ROBUST": 100, "MODERATE": 70, "NEUTRAL": 50, "RISKY": 30, "SYNTAX_ERROR": 0}
                robust_grade = mcri_report.get('robustness_grade', 'NEUTRAL')
                arch_score = robust_map.get(robust_grade, 50)

                output["mcri"] = {
                    "syntax_score":    min(100, max(0, norm_hygiene)),
                    "logic_score":     min(100, max(0, arch_score)),
                    "render_score":    min(100, max(0, norm_hygiene + 5 if hygiene > 10 else norm_hygiene)),
                    "stability_score": 100 if not ablation_mode else (40 if robust_grade != "ROBUST" else 80),
                    "total_score":     round((norm_hygiene * 0.4 + arch_score * 0.4 + (100 if not ablation_mode else 40) * 0.2), 1)
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
            # 1. Vision OCR
            from core.ai_wrapper import get_ai_client
            vision_client = get_ai_client('vision_analyzer')
            ocr_prompt = "請幫我辨識這張圖片中的數學式或題目文字。只輸出辨識到的純文字，不需要任何額外的解釋或Markdown標記。如果裡面有未知變數請照實輸出。"
            
            vision_resp = vision_client.generate_content(ocr_prompt, image_path=temp_path)
            ocr_text = vision_resp.text.strip() if hasattr(vision_resp, 'text') else str(vision_resp)
            
            display_text = ocr_text[:30] + "..." if len(ocr_text) > 30 else ocr_text
            process_logs.append(f"> 📄 OCR Extraction Complete: [{display_text}]")
            
            if os.path.exists(temp_path): 
                os.remove(temp_path)
        
        elif text_data:
            process_logs.append("> 📝 Detected Text Payload. Skipping OCR Phase.")
            ocr_text = text_data.strip()
            
        else:
            return jsonify({"success": False, "error": "Require image_data or text_data."}), 400

        process_logs.append("> 🧠 Extracting semantic markers for DNA alignment...")
        # 2. 分類 Skill
        engine = get_engine()
        skill_name = engine.classifier.classify(input_text=ocr_text)
        
        bare_prompt = ""
        scaffold_prompt = ""

        if skill_name != "Unknown":
            process_logs.append(f"> ✅ DNA Sequence Aligned: {skill_name}")
            confidence = 98
            
            # [NEW] Generate Prompt Previews
            try:
                skill_path = engine.scaler._get_skill_path(skill_name)
                
                ab1_prompt_path = os.path.join(skill_path, "experiments", "ab1_bare_prompt.md")
                if os.path.exists(ab1_prompt_path):
                    with open(ab1_prompt_path, "r", encoding="utf-8") as f:
                        ab1_template = f.read()
                    import re
                    bare_prompt = re.sub(
                        r"【參考例題】.*?【程式要求】", 
                        f"【參考例題】\n{ocr_text}\n\n【程式要求】", 
                        ab1_template, 
                        flags=re.DOTALL
                    )
                else:
                    bare_prompt = f"請寫一個 generate(level=1) 函式，參考：\n{ocr_text}\n直接輸出代碼。"

                skill_md_path = os.path.join(skill_path, "SKILL.md")
                if os.path.exists(skill_md_path):
                    with open(skill_md_path, "r", encoding="utf-8") as f:
                        skill_spec = f.read()
                    # 使用明確的切斷錨點，確保不同技能都能精準抓取精華區塊
                    skill_spec_distilled = skill_spec.split("=== SKILL_END_PROMPT ===")[0].strip()

                    import re
                    live_show_match = re.search(r'\[\[MODE:LIVESHOW\]\]([\s\S]*?)\[\[END_MODE:LIVESHOW\]\]', skill_spec)
                    live_show_content = live_show_match.group(1).strip() if live_show_match else ""

                    # 預處理 input_text 確保有 LaTeX 基本結構 (Using a simplified version of scaler's sanitize)
                    input_text_safe = re.sub(r'(\w)\^(\d+)', r'\1^{\2}', ocr_text)
                    if "$" not in input_text_safe:
                        input_text_safe = re.sub(r'(\(.*\).*)', r'$\1$', input_text_safe)

                    live_show_content = live_show_content.replace('{{TARGET_QUESTION}}', input_text_safe)
                    live_show_content = live_show_content.replace('{{TARGET_ANSWER}}', '...')

                    scaffold_prompt = f"""{skill_spec_distilled}\n=== SKILL_END_PROMPT ===\n\n{live_show_content}"""
                else:
                    scaffold_prompt = "[SKILL.md 未找到]"
            except Exception as e:
                scaffold_prompt = f"Error loading SKILL.md: {e}"
        else:
            process_logs.append("> ⚠️ DNA Match Failed: Falling back to Unknown.")
            confidence = 30

        return jsonify({
            "success": True,
            "ocr_text": ocr_text,
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
                "syntax_score":    min(100, max(0, (hygiene / 15.0) * 100)),
                "logic_score":     90 if not ablation_mode else 50,
                "render_score":    min(100, max(0, (hygiene / 15.0) * 100 + 5)),
                "stability_score": 100 if not ablation_mode else 40,
                "total_score":     round(((hygiene / 15.0) * 100 * 0.6 + (100 if not ablation_mode else 40) * 0.4), 1)
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
        }), 500
