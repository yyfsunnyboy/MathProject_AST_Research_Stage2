# -*- coding: utf-8 -*-
"""
=============================================================================
模組名稱 (Module Name): demo.py
功能說明 (Description): 育秀盃專用獨立 Live Show 展示包裝腳本。
這是一個輕量級的 Flask 應用程式，專門載入 Live Show 需要的單一路由和資源。
執行語法 (Usage): python demo.py
=============================================================================
"""
import os
import sys

# 強制路徑修正：解決 No module named 'core'
basedir = os.path.abspath(os.path.dirname(__file__))
if basedir not in sys.path:
    sys.path.insert(0, basedir)

from flask import Flask, redirect, url_for
from dotenv import load_dotenv

load_dotenv()

def create_demo_app():
    # 初始化一個乾淨的 Flask App
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    # 載入必要的環境設定
    app.config['SECRET_KEY'] = 'yushou-demo-secret-key-2026'
    
    # 僅載入 Live Show Blueprint
    from core.routes import live_show_bp
    app.register_blueprint(live_show_bp)

    @app.route('/')
    def index():
        # 預設首頁直接導向 Live Show 頁面
        return redirect('/live_show')

    return app

if __name__ == '__main__':
    demo_app = create_demo_app()
    print("==========================================================")
    print("🚀 育秀盃 Live Show 專用伺服器已啟動！")
    print("👉 請使用瀏覽器開啟：http://127.0.0.1:5000/live_show")
    print("==========================================================")
    
    # 關閉自動重載以提高穩定性
    demo_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
