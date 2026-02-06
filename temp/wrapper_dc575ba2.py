import sys
import os
import json
import importlib.util

sys.path.append('e:/Python/MathProject_AST_Research')

try:
    spec = importlib.util.spec_from_file_location("temp_mod", r"e:/Python/MathProject_AST_Research/temp/dyn_sample_dc575ba2.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    if not hasattr(module, 'generate'):
        print(json.dumps({'status': 'error', 'msg': 'Function generate not found'}))
        sys.exit(0)
        
    for i in range(3):
        res = module.generate()
        if not isinstance(res, dict) or 'question_text' not in res or 'answer' not in res:
             print(json.dumps({'status': 'error', 'msg': 'Invalid return format'}))
             sys.exit(0)
             
    print(json.dumps({'status': 'ok'}))
    
except Exception as e:
    print(json.dumps({'status': 'error', 'msg': str(e)}))
