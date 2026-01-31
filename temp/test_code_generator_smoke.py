
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Ensure project root is in path (relative to temp/ script)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

# Try to import app, handling potential import errors due to environment
try:
    from app import app
except ImportError as e:
    print(f"Failed to import app: {e}")
    sys.exit(1)

from core.code_generator import auto_generate_skill_code

class TestCodeGenerator(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    @patch('core.code_generator.get_ai_client')
    def test_auto_generate_flow(self, mock_get_client):
        """Smoke test for auto_generate_skill_code with mocked AI"""
        print("\n[Test] Starting Code Generator Smoke Test...")
        
        # 1. Setup Mock AI Response
        mock_response = MagicMock()
        mock_response.text = """
```python
import random

def generate():
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    question_text = f"Calculate {a} + {b}"
    answer = str(a + b)
    return {
        "question_text": question_text,
        "answer": answer
    }
```
"""
        # Mock nested attributes for token usage
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50
        
        mock_client = MagicMock()
        mock_client.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        # 2. Call the function
        skill_id = "test_smoke_skill"
        output_path = os.path.join(project_root, "temp", "test_generated_skill.py")
        
        # Ensure temp dir exists
        temp_dir = os.path.dirname(output_path)
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        print(f"[Test] Calling auto_generate_skill_code for {skill_id}...")
        # We pass ablation_id=1 for a simple path
        success, msg, stats = auto_generate_skill_code(
            skill_id, 
            ablation_id=1, 
            custom_output_path=output_path
        )
        
        print(f"[Test] Result: Success={success}, Msg={msg}, Stats={stats}")
        
        # 3. Verification
        if not success:
            print(f"❌ Generation failed: {msg}")
        
        if os.path.exists(output_path):
             print(f"✅ Output file created at {output_path}")
             with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "def generate():" in content:
                    print("✅ Content verification passed (generate function found)")
                else:
                    print("❌ Content verification failed")
        else:
            print("❌ Output file not created")

        # Returns
        self.assertTrue(os.path.exists(output_path))

if __name__ == "__main__":
    unittest.main()
