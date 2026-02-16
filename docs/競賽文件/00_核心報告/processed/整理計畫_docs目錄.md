# 📋 docs/ 目錄整理計畫

**分析日期**: 2026-02-01 22:14

---

## 📂 當前狀況

### **docs/ 根目錄文件**

| 檔案 | 大小 | 分類 | 建議 |
|------|------|------|------|
| **安裝程式（應刪除）** | | | |
| ImageMagick-7.1.2-9-Q16-HDRI-x64-dll.exe | 23 MB | 🗑️ 安裝檔 | **刪除**（已安裝） |
| pandoc-3.8.3-windows-x86_64.msi | 41 MB | 🗑️ 安裝檔 | **刪除**（已安裝） |
| tesseract-ocr-w64-setup-5.4.0.20240606.exe | 50 MB | 🗑️ 安裝檔 | **刪除**（已安裝） |
| **資料庫備份（移到 temp/）** | | | |
| 58FCE000 | 692 KB | 📦 數據備份 | ➡️ temp/ |
| kumon_math_20251217_2323.xlsx | 614 KB | 📦 數據備份 | ➡️ temp/ |
| math_master_backup_國中普高完成.xlsx | 693 KB | 📦 數據備份 | ➡️ temp/ |
| Database_Schema.xlsx | 14 KB | 📦 Schema 舊版 | ➡️ temp/ |
| Database_Schema_Split.xlsx | 14 KB | 📦 Schema 舊版 | ➡️ temp/ |
| Table Schema.xlsx | 21 KB | 📦 Schema 舊版 | ➡️ temp/ |
| Table Schema_20251216_before.txt | 5 KB | 📦 Schema 舊版 | ➡️ temp/ |
| **技術文檔（移到競賽文件/）** | | | |
| 資料庫Table_Schema_20260111.md | 14 KB | 📚 技術文檔 | ➡️ 競賽文件/ |
| 資料庫Table_Schema_20260117.md | 15 KB | 📚 技術文檔 | ➡️ 競賽文件/ |
| 軟體設計文件 (SDD).md | 14 KB | 📚 設計文檔 | ➡️ 競賽文件/ |
| 視覺化學生分析.md | 3 KB | 📚 分析文檔 | ➡️ 競賽文件/ |
| **臨時報告（移到 temp/）** | | | |
| V01_IMPLEMENTATION_SUMMARY.md | 9 KB | 🗑️ 舊版報告 | ➡️ temp/ |
| V46.8_Precision_Fixes_Report.md | 7 KB | 🗑️ 舊版報告 | ➡️ temp/ |
| gemini_pro3_project_context.md | 26 KB | 🗑️ 上下文檔 | ➡️ temp/ |
| backend_workflow_diagram.html | 5 KB | 🗑️ 視覺化 | ➡️ temp/ |
| **安裝說明（移到 temp/）** | | | |
| 如何安裝 ImageMagick.txt | 2 KB | 📝 安裝說明 | ➡️ temp/ |
| 如何安裝 Tesseract OCR程式.txt | 4 KB | 📝 安裝說明 | ➡️ temp/ |

---

## 📂 子目錄分析

### **docs/競賽文件/**（已整理）✅
- 永久保留的核心文檔

### **docs/temp/**（已創建）✅
- 臨時文檔存放處

### **docs/前臺系統分析/**
- 建議：➡️ 移到 temp/archive/

### **docs/後臺系統分析/**
- 建議：➡️ 移到 temp/archive/

---

## 🎯 整理行動

### **階段 1: 刪除安裝檔（釋放 114 MB）** 🗑️

```powershell
Remove-Item "docs/ImageMagick-7.1.2-9-Q16-HDRI-x64-dll.exe"
Remove-Item "docs/pandoc-3.8.3-windows-x86_64.msi"
Remove-Item "docs/tesseract-ocr-w64-setup-5.4.0.20240606.exe"
```

### **階段 2: 移動資料庫備份到 temp/**

```powershell
Move-Item "docs/58FCE000" "docs/temp/"
Move-Item "docs/kumon_math_20251217_2323.xlsx" "docs/temp/"
Move-Item "docs/math_master_backup_國中普高完成.xlsx" "docs/temp/"
Move-Item "docs/Database_Schema*.xlsx" "docs/temp/"
Move-Item "docs/Table Schema*" "docs/temp/"
```

### **階段 3: 移動技術文檔到競賽文件/**

```powershell
Move-Item "docs/資料庫Table_Schema_20260111.md" "docs/競賽文件/"
Move-Item "docs/資料庫Table_Schema_20260117.md" "docs/競賽文件/"
Move-Item "docs/軟體設計文件 (SDD).md" "docs/競賽文件/"
Move-Item "docs/視覺化學生分析.md" "docs/競賽文件/"
```

### **階段 4: 移動臨時報告到 temp/**

```powershell
Move-Item "docs/V01_IMPLEMENTATION_SUMMARY.md" "docs/temp/"
Move-Item "docs/V46.8_Precision_Fixes_Report.md" "docs/temp/"
Move-Item "docs/gemini_pro3_project_context.md" "docs/temp/"
Move-Item "docs/backend_workflow_diagram.html" "docs/temp/"
Move-Item "docs/如何安裝*.txt" "docs/temp/"
```

### **階段 5: 創建 archive/ 並移動舊分析**

```powershell
New-Item -ItemType Directory "docs/temp/archive"
Move-Item "docs/前臺系統分析" "docs/temp/archive/"
Move-Item "docs/後臺系統分析" "docs/temp/archive/"
```

---

## 📊 預期結果

### **整理前**
```
docs/
├── 競賽文件/（21 文件）
├── temp/（17 文件）
├── 前臺系統分析/
├── 後臺系統分析/
└── 根目錄：20 個檔案（總大小 ~114 MB）
```

### **整理後**
```
docs/
├── 競賽文件/（25 文件）← 增加 4 個技術文檔
├── temp/
│   ├── archive/
│   │   ├── 前臺系統分析/
│   │   └── 後臺系統分析/
│   └── 30+ 文件（臨時/備份）
└── 根目錄：0 個檔案 ← 完全清空！
```

**釋放空間**: ~114 MB（刪除安裝檔）

---

## ✅ 執行確認

準備好執行整理了嗎？

**選項**:
1. **自動執行全部**（推薦）
2. **逐步執行**（可確認每一步）
3. **先預覽**（不執行，只看計畫）

---

**下一步**: 執行整理腳本
