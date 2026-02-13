import logging
import ast
from collections import Counter

# 嘗試引入標準庫
try:
    from codebleu import calc_codebleu
except ImportError:
    calc_codebleu = None

def compute_structural_codebleu(generated_code: str, reference_code: str):
    """
    防彈版 CodeBLEU 計算器
    特色：遇到 tree-sitter 版本錯誤時，自動切換回 Python 原生 AST 計算
    """
    gen_clean = generated_code.strip()
    ref_clean = reference_code.strip()
    
    if not gen_clean or not ref_clean:
        return {"error": "Empty code"}

    # --- 策略 A: 優先嘗試標準 CodeBLEU ---
    try:
        if calc_codebleu:
            result = calc_codebleu(
                references=[ref_clean], 
                predictions=[gen_clean], 
                lang="python",
                weights=(0.1, 0.1, 0.4, 0.4),
                tokenizer=None
            )
            return {
                "total_score": result['codebleu'],
                "ngram": result['ngram_match_score'],
                "weighted_ngram": result['weighted_ngram_match_score'],
                "syntax_ast": result['syntax_match_score'],
                "dataflow": result['dataflow_match_score']
            }
    except Exception as e:
        # 捕捉 TypeError: an integer is required 等所有錯誤
        print(f"[Warning] CodeBLEU failed ({e}), switching to Pure-Python Fallback...")

    # --- 策略 B: 純 Python 原生備援 (Fallback) ---
    # 使用 Python 內建 ast 模組，保證不依賴 C++ 擴充套件
    
    # 1. 計算 N-gram (1-gram 近似)
    def get_tokens(code):
        return [t for t in code.replace('(', ' ').replace(')', ' ').split() if t.strip()]
    
    gen_tokens = get_tokens(gen_clean)
    ref_tokens = get_tokens(ref_clean)
    
    common_tokens = Counter(gen_tokens) & Counter(ref_tokens)
    ngram_score = sum(common_tokens.values()) / max(1, len(gen_tokens))
    
    # 2. 計算 AST Match (核心：比較語法結構樹)
    def get_ast_nodes(code):
        try:
            tree = ast.parse(code)
            # 只提取節點類型名稱 (如 If, For, Assign, Call)
            return [type(node).__name__ for node in ast.walk(tree)]
        except SyntaxError:
            return []

    gen_nodes = get_ast_nodes(gen_clean)
    ref_nodes = get_ast_nodes(ref_clean)
    
    ast_score = 0.0
    if gen_nodes and ref_nodes:
        common_nodes = Counter(gen_nodes) & Counter(ref_nodes)
        ast_score = sum(common_nodes.values()) / max(1, len(gen_nodes))

    # 3. 合成總分
    # 權重模擬: 0.2 (文字) + 0.8 (結構)
    # 註：Fallback 模式無法計算 Dataflow，我們將其權重移給 AST
    total_score = 0.2 * ngram_score + 0.8 * ast_score

    return {
        "total_score": total_score,
        "ngram": ngram_score,
        "weighted_ngram": ngram_score, # 近似值
        "syntax_ast": ast_score,       # Python 原生 AST 分數
        "dataflow": 0.0,               # 備援模式不支援 Dataflow
        "note": "Fallback Mode"
    }