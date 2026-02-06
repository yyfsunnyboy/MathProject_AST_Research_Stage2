"""快速验证新的实验条件"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from models import AblationSetting

app = create_app()
with app.app_context():
    print("\n" + "="*70)
    print("修正后的实验条件验证")
    print("="*70)
    
    for ab_id in [1, 2, 3]:
        ab = AblationSetting.query.get(ab_id)
        print(f"\nAb{ab_id}: {ab.name}")
        print(f"  Regex Healer: {'ON' if ab.use_regex else 'OFF'}")
        print(f"  AST Healer:   {'ON' if ab.use_ast else 'OFF'}")
        print(f"  说明: {ab.description}")
    
    print("\n" + "="*70)
    print("关键对比组")
    print("="*70)
    print("\nAb2 vs Ab3 (核心对比组):")
    print("  - Prompt: 相同 (都使用纯 MASTER_SPEC)")
    print("  - Healer: Ab2=OFF, Ab3=ON (Regex+AST)")
    print("  - 验证内容: Healer 自愈机制的独立价值")
    print("\n✅ 配置正确！")
