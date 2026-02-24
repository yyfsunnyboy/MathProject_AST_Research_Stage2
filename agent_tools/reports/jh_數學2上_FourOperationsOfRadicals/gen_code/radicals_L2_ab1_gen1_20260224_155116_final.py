# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 36.73s | Tokens: In=759, Out=1535
# Created At: 2026-02-24 15:51:16
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    question_text = ""
    answer = ""
    correct_answer = ""
    mode = 1
    
    if level == 1:
        a = random.randint(2, 10)
        b = random.randint(2, 10)
        c = random.randint(2, 10)
        d = random.randint(2, 10)
        e = random.randint(2, 10)
        f = random.randint(2, 10)
        g = random.randint(2, 10)
        h = random.randint(2, 10)
        i = random.randint(2, 10)
        j = random.randint(2, 10)
        k = random.randint(2, 10)
        l = random.randint(2, 10)
        m = random.randint(2, 10)
        n = random.randint(2, 10)
        o = random.randint(2, 10)
        p = random.randint(2, 10)
        q = random.randint(2, 10)
        r = random.randint(2, 10)
        s = random.randint(2, 10)
        t = random.randint(2, 10)
        u = random.randint(2, 10)
        v = random.randint(2, 10)
        w = random.randint(2, 10)
        x = random.randint(2, 10)
        y = random.randint(2, 10)
        z = random.randint(2, 10)
        
        term1 = f"\\sqrt{{{a}}}"
        term2 = f"\\sqrt{{{b}}}"
        term3 = f"\\sqrt{{{c}}}"
        term4 = f"\\sqrt{{{d}}}"
        term5 = f"\\sqrt{{{e}}}"
        term6 = f"\\sqrt{{{f}}}"
        term7 = f"\\sqrt{{{g}}}"
        term8 = f"\\sqrt{{{h}}}"
        term9 = f"\\sqrt{{{i}}}"
        term10 = f"\\sqrt{{{j}}}"
        term11 = f"\\sqrt{{{k}}}"
        term12 = f"\\sqrt{{{l}}}"
        term13 = f"\\sqrt{{{m}}}"
        term14 = f"\\sqrt{{{n}}}"
        term15 = f"\\sqrt{{{o}}}"
        term16 = f"\\sqrt{{{p}}}"
        term17 = f"\\sqrt{{{q}}}"
        term18 = f"\\sqrt{{{r}}}"
        term19 = f"\\sqrt{{{s}}}"
        term20 = f"\\sqrt{{{t}}}"
        term21 = f"\\sqrt{{{u}}}"
        term22 = f"\\sqrt{{{v}}}"
        term23 = f"\\sqrt{{{w}}}"
        term24 = f"\\sqrt{{{x}}}"
        term25 = f"\\sqrt{{{y}}}"
        term26 = f"\\sqrt{{{z}}}"
        
        op1 = random.choice(["+", "-"])
        op2 = random.choice(["+", "-"])
        op3 = random.choice(["+", "-"])
        op4 = random.choice(["+", "-"])
        op5 = random.choice(["+", "-"])
        op6 = random.choice(["+", "-"])
        op7 = random.choice(["+", "-"])
        op8 = random.choice(["+", "-"])
        op9 = random.choice(["+", "-"])
        op10 = random.choice(["+", "-"])
        op11 = random.choice(["+", "-"])
        op12 = random.choice(["+", "-"])
        op13 = random.choice(["+", "-"])
        op14 = random.choice(["+", "-"])
        op15 = random.choice(["+", "-"])
        op16 = random.choice(["+", "-"])
        op17 = random.choice(["+", "-"])
        op18 = random.choice(["+", "-"])
        op19 = random.choice(["+", "-"])
        op20 = random.choice(["+", "-"])
        op21 = random.choice(["+", "-"])
        op22 = random.choice(["+", "-"])
        op23 = random.choice(["+", "-"])
        op24 = random.choice(["+", "-"])
        op25 = random.choice(["+", "-"])
        op26 = random.choice(["+", "-"])
        
        question_text = f"化簡 $({term1} {op1} {term2} {op2} {term3} {op3} {term4} {op4} {term5} {op5} {term6} {op6} {term7} {op7} {term8} {op8} {term9} {op9} {term10} {op10} {term11} {op11} {term12} {op12} {term13} {op13} {term14} {op14} {term15} {op15} {term16} {op16} {term17} {op17} {term18} {op18} {term19} {op19} {term20} {op20} {term21} {op21} {term22} {op22} {term23} {op23} {term24} {op24} {term25} {op25} {term26} {op26})$"
        
        correct_answer = f"{term1} {op1} {term2} {op2} {term3} {op3} {term4} {op4} {term5} {op5} {term6} {op6} {term7} {op7} {term8} {op8} {term9} {op9} {term10} {op10} {term11} {op11} {term12} {op12} {term13} {op13} {term14} {op14} {term15} {op15} {term16} {op16} {term17} {op17} {term18} {op18} {term19} {op19} {term20} {op20} {term21} {op21} {term22} {op22} {term23} {op23} {term24} {op24} {term25} {op25} {term26} {op26}"
    
    return {'question_text': question_text, 'answer': answer, 'correct_answer': correct_answer, 'mode': mode}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}