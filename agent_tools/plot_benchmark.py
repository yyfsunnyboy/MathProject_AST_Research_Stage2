import matplotlib.pyplot as plt
import os

def plot_benchmark_results():
    # 數據準備 (基於實驗結果)
    versions = ['v0 (Bare Prompt)', 'v1 (Scaffold)', 'v2 (Full Healing)']
    pass_rates = [0, 40, 100]
    colors = ['#ff4d4d', '#ffcc00', '#28a745'] # 紅 -> 黃 -> 綠

    # 設定圖表風格
    plt.figure(figsize=(10, 6))
    bars = plt.bar(versions, pass_rates, color=colors, width=0.6)

    # 添加標題與標籤
    plt.title('Agent Skill Benchmark: Pass Rate Improvement (Qwen-14B)', fontsize=16, fontweight='bold', pad=20)
    plt.ylabel('Pass Rate (%)', fontsize=12)
    plt.ylim(0, 110) # 預留空間給標籤
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # 在柱狀圖上方標註數值
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 2,
                 f'{height}%',
                 ha='center', va='bottom', fontsize=14, fontweight='bold')

    # 添加趨勢箭頭或說明 (可選)
    plt.annotate('Syntax Errors\n(Markdown, Braces)', 
                 xy=(0, 5), xytext=(0, 20),
                 ha='center', va='bottom', arrowprops=dict(arrowstyle='->', color='red'))
                 
    plt.annotate('Format Issues\n(JSON Truncation)', 
                 xy=(1, 45), xytext=(1, 60),
                 ha='center', va='bottom', arrowprops=dict(arrowstyle='->', color='orange'))

    plt.annotate('100% Reliable\n(Healer Fixed All)', 
                 xy=(2, 102), xytext=(2, 85),
                 ha='center', va='top', color='white', fontweight='bold')

    # 存檔
    output_path = os.path.join(os.path.dirname(__file__), '..', 'benchmark_result.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ 圖表已生成: {os.path.abspath(output_path)}")
    print("📊 這張圖表清晰展示了從 0% 到 100% 的巨大進步！")

if __name__ == "__main__":
    try:
        plot_benchmark_results()
    except ImportError:
        print("❌ 缺少 matplotlib 庫。正在嘗試安裝...")
        os.system("pip install matplotlib")
        plot_benchmark_results()
