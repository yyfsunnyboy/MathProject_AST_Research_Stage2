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
        if problems:
            first = problems[0]
            if "error" in first:
                output["error"] = first["error"]
            else:
                q_text = first.get("question_text", "")
                output["problem"] = q_text
                output["answer"]  = first.get("correct_answer", "")
                output["raw_code"] = dm.get("raw_code", "")

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
    ab1_prompt = (
        f"請寫一個名為 `generate(level=1)` 的 Python 函式，回傳包含題目的字典。\n"
        f"字典格式必須要有 `question_text` 與 `correct_answer`。\n"
        f"請參考以下例題的風格隨機出題：\n{prompt_text}\n"
        f"直接印出含 generate(level) 的 Python 程式碼，不需解釋。"
    )

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
            bare_prompt = (
                f"請寫一個名為 `generate(level=1)` 的 Python 函式，回傳包含題目的字典。\\n"
                f"字典格式必須要有 `question_text` 與 `correct_answer`。\\n"
                f"請參考以下例題的風格隨機出題：\\n{ocr_text}\\n"
                f"直接印出含 generate(level) 的 Python 程式碼，不需解釋。"
            )
            
            try:
                skill_path = engine.scaler._get_skill_path(skill_name)
                skill_md_path = os.path.join(skill_path, "SKILL.md")
                if os.path.exists(skill_md_path):
                    with open(skill_md_path, "r", encoding="utf-8") as f:
                        skill_spec = f.read()
                    scaffold_prompt = f"{skill_spec}\\n\\n[系統會自動在此注入難度動態調整與安全運算防護網指令...]"
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
