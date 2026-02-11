import importlib.util

# 直接載入模組
spec = importlib.util.spec_from_file_location(
    "test_module",
    'experiments/results/jh_數學1上_FourArithmeticOperationsOfIntegers/jh_數學1上_FourArithmeticOperationsOfIntegers_qwen2.5-coder-7b_Ab2_run01.py'
)

if spec and spec.loader:
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        print("✅ 模組載入成功")
        print(f"有 generate: {hasattr(module, 'generate')}")
        print(f"有 check: {hasattr(module, 'check')}")
        
        # 測試 generate
        if hasattr(module, 'generate'):
            try:
                result = module.generate()
                print(f"✅ generate() 成功: {list(result.keys())}")
            except Exception as e:
                print(f"❌ generate() 失敗: {e}")
    except Exception as e:
        print(f"❌ 模組載入失敗: {e}")
        import traceback
        traceback.print_exc()
