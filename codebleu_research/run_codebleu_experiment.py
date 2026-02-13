import os
import glob
from compute_codebleu import compute_structural_codebleu

# 設定路徑
BASE_DIR = r"C:\MathProject_AST_Research\codebleu_research"
REF_DIR = os.path.join(BASE_DIR, "references")
SKILLS_DIR = os.path.join(BASE_DIR, "skills")  # 請建立這個資料夾放入 Ab1/Ab2/Ab3

def load_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def run_experiment():
    # 1. 讀取 Golden Template
    # 假設你的 Golden 檔名是 jh_數學1上_FourArithmeticOperationsOfIntegers_GOLDEN.py
    golden_path = os.path.join(REF_DIR, "jh_數學1上_FourArithmeticOperationsOfIntegers_GOLDEN.py")
    
    if not os.path.exists(golden_path):
        print(f"❌ 錯誤: 找不到 Golden Template: {golden_path}")
        return

    golden_code = load_file(golden_path)
    print(f"✅ 成功讀取 Golden Template ({len(golden_code)} chars)")
    print("-" * 80)
    print(f"{'File Name':<40} | {'Total':<6} | {'N-gram':<6} | {'W-Ngram':<6} | {'AST':<6} | {'DataFlow':<6}")
    print("-" * 80)

    # 2. 讀取 skills 資料夾下的所有 .py 檔案進行測試
    # 這裡假設你會把 Ab1, Ab2, Ab3 的檔案放在 skills 資料夾
    if not os.path.exists(SKILLS_DIR):
        print(f"❌ 請建立資料夾 {SKILLS_DIR} 並放入要測試的 Ab1/Ab2/Ab3 檔案")
        return

    test_files = glob.glob(os.path.join(SKILLS_DIR, "*.py"))
    
    if not test_files:
        print("❌ skills 資料夾是空的，請放入要測試的 .py 檔案")
        return

    # 3. 執行評測
    for file_path in sorted(test_files):
        filename = os.path.basename(file_path)
        gen_code = load_file(file_path)
        
        # 計算分數
        res = compute_structural_codebleu(gen_code, golden_code)
        
        if "error" in res:
            print(f"{filename:<40} | ERROR: {res['error']}")
        else:
            # 格式化輸出
            print(f"{filename:<40} | "
                  f"{res['total_score']:.4f} | "
                  f"{res['ngram']:.4f} | "
                  f"{res['weighted_ngram']:.4f} | "
                  f"{res['syntax_ast']:.4f} | "  # 這是 L5 的重點
                  f"{res['dataflow']:.4f}")   # 這是 L5 的重點

if __name__ == "__main__":
    run_experiment()