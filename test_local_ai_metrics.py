import sys
import os

# Adds the project root to the python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.ai_wrapper import LocalAIClient

def test_local_ai_metrics():
    print("Testing LocalAIClient metrics...")
    client = LocalAIClient(model_name="qwen2.5-coder:7b") # Use a default or valid model name
    
    try:
        response = client.generate_content("Hello, world!")
        print(f"Response text: {response.text[:50]}...")
        
        # Check latency
        if hasattr(response, 'latency_ms'):
            print(f"✅ Latency: {response.latency_ms} ms")
        else:
            print("❌ Latency missing!")
            
        # Check tokens
        if hasattr(response, 'prompt_tokens'):
            print(f"✅ Prompt Tokens: {response.prompt_tokens}")
        else:
             print("❌ Prompt Tokens missing!")

        if hasattr(response, 'completion_tokens'):
            print(f"✅ Completion Tokens: {response.completion_tokens}")
        else:
             print("❌ Completion Tokens missing!")
             
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_local_ai_metrics()
