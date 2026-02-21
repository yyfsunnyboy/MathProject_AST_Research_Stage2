# -*- coding: utf-8 -*-
"""
=============================================================================
模組名稱 (Module Name): core/routes/__init__.py
功能說明 (Description): 路由模組初始化，負責定義 Flask Blueprints (core_bp, practice_bp) 並匯入所有子路由模組。
執行語法 (Usage): 由系統調用
版本資訊 (Version): V2.0
更新日期 (Date): 2026-01-13
維護團隊 (Maintainer): Math AI Project Team
=============================================================================
"""
from flask import Blueprint
core_bp = Blueprint('core', __name__, template_folder='../../templates')
practice_bp = Blueprint('practice', __name__)
live_show_bp = Blueprint('live_show', __name__)

# 這一行會去讀取你的 admin.py 與 live_show.py 等等
from . import auth, admin, practice, classroom, analysis, exam, live_show