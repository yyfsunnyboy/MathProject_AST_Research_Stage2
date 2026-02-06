
import sys
import os
import traceback

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Testing core.code_generator import...")

try:
    from core.code_generator import auto_generate_skill_code, _advanced_healer, ASTHealer
    print("✅ Successfully imported core.code_generator components!")
    
    # Optional: Inspect ASTHealer signature
    import inspect
    sig = inspect.signature(ASTHealer.__init__)
    print(f"ASTHealer.__init__ signature: {sig}")
    
    if 'ai_client' in sig.parameters:
        print("✅ ASTHealer accepts 'ai_client' parameter (Semantic Healing ready).")
    else:
        print("❌ ASTHealer MISSING 'ai_client' parameter!")

    print("\nAttempting to instantiate ASTHealer with a mock client...")
    class MockAI:
        pass
    healer = ASTHealer(ai_client=MockAI())
    print(f"✅ ASTHealer instantiated. Fixes count: {healer.fixes}")
    
    if hasattr(healer, 'semantic_heal'):
        print("✅ ASTHealer has 'semantic_heal' method.")
    else:
        print("❌ ASTHealer MISSING 'semantic_heal' method!")

except Exception as e:
    print("❌ Failed to import or verify code_generator.")
    traceback.print_exc()
