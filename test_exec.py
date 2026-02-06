
import os

target_file = r"e:\Python\MathProject_AST_Research\experiments\results\jh_數學1上_FourArithmeticOperationsOfIntegers\jh_數學1上_FourArithmeticOperationsOfIntegers_qwen2.5-coder-14b_Ab3_run04.py"

with open(target_file, "r", encoding="utf-8") as f:
    code = f.read()

print(f"Testing execution of {os.path.basename(target_file)}...")

try:
    # 建立獨立的 namespace
    namespace = {}
    exec(code, namespace)
    
    if 'generate' in namespace:
        print("Function 'generate' found. Executing...")
        try:
            result = namespace['generate']()
            print("Execution Success!")
            print("Result:", result)
        except Exception as e:
            print(f"Runtime Error during generate(): {e}")
    else:
        print("Error: Function 'generate' not found.")

except Exception as e:
    print(f"Compilation/Exec Error: {e}")
