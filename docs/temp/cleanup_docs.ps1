# docs/ 目錄自動整理腳本
# 執行日期: 2026-02-01

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  docs/ 目錄整理腳本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$totalSteps = 5
$currentStep = 0

# 階段 1: 刪除安裝檔
$currentStep++
Write-Host "[$currentStep/$totalSteps] 刪除安裝檔（釋放空間）..." -ForegroundColor Yellow

$installFiles = @(
    "docs\ImageMagick-7.1.2-9-Q16-HDRI-x64-dll.exe",
    "docs\pandoc-3.8.3-windows-x86_64.msi",
    "docs\tesseract-ocr-w64-setup-5.4.0.20240606.exe"
)

foreach ($file in $installFiles) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "  ✓ 已刪除: $file" -ForegroundColor Green
    }
}

# 階段 2: 移動資料庫備份到 temp/
$currentStep++
Write-Host "`n[$currentStep/$totalSteps] 移動資料庫備份到 temp/..." -ForegroundColor Yellow

$dbFiles = @(
    "docs\58FCE000",
    "docs\kumon_math_20251217_2323.xlsx",
    "docs\math_master_backup_國中普高完成.xlsx",
    "docs\Database_Schema.xlsx",
    "docs\Database_Schema_Split.xlsx",
    "docs\Table Schema.xlsx",
    "docs\Table Schema_20251216_before.txt"
)

foreach ($file in $dbFiles) {
    if (Test-Path $file) {
        $fileName = Split-Path $file -Leaf
        Move-Item $file "docs\temp\$fileName" -Force
        Write-Host "  ✓ 已移動: $fileName" -ForegroundColor Green
    }
}

# 階段 3: 移動技術文檔到競賽文件/
$currentStep++
Write-Host "`n[$currentStep/$totalSteps] 移動技術文檔到競賽文件/..." -ForegroundColor Yellow

$techDocs = @(
    "docs\資料庫Table_Schema_20260111.md",
    "docs\資料庫Table_Schema_20260117.md",
    "docs\軟體設計文件 (SDD).md",
    "docs\視覺化學生分析.md"
)

foreach ($file in $techDocs) {
    if (Test-Path $file) {
        $fileName = Split-Path $file -Leaf
        Move-Item $file "docs\競賽文件\$fileName" -Force
        Write-Host "  ✓ 已移動: $fileName" -ForegroundColor Green
    }
}

# 階段 4: 移動臨時報告到 temp/
$currentStep++
Write-Host "`n[$currentStep/$totalSteps] 移動臨時報告到 temp/..." -ForegroundColor Yellow

$tempDocs = @(
    "docs\V01_IMPLEMENTATION_SUMMARY.md",
    "docs\V46.8_Precision_Fixes_Report.md",
    "docs\gemini_pro3_project_context.md",
    "docs\backend_workflow_diagram.html"
)

foreach ($file in $tempDocs) {
    if (Test-Path $file) {
        $fileName = Split-Path $file -Leaf
        Move-Item $file "docs\temp\$fileName" -Force
        Write-Host "  ✓ 已移動: $fileName" -ForegroundColor Green
    }
}

# 移動安裝說明
Get-ChildItem "docs\如何安裝*.txt" -ErrorAction SilentlyContinue | ForEach-Object {
    Move-Item $_.FullName "docs\temp\$($_.Name)" -Force
    Write-Host "  ✓ 已移動: $($_.Name)" -ForegroundColor Green
}

# 階段 5: 創建 archive/ 並移動舊分析
$currentStep++
Write-Host "`n[$currentStep/$totalSteps] 整理舊分析目錄..." -ForegroundColor Yellow

if (-not (Test-Path "docs\temp\archive")) {
    New-Item -ItemType Directory "docs\temp\archive" -Force | Out-Null
    Write-Host "  ✓ 已創建: docs\temp\archive\" -ForegroundColor Green
}

$oldDirs = @("docs\前臺系統分析", "docs\後臺系統分析")
foreach ($dir in $oldDirs) {
    if (Test-Path $dir) {
        $dirName = Split-Path $dir -Leaf
        Move-Item $dir "docs\temp\archive\$dirName" -Force
        Write-Host "  ✓ 已移動: $dirName/" -ForegroundColor Green
    }
}

# 完成統計
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  整理完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`n📊 統計:" -ForegroundColor White
Write-Host "  • 已刪除安裝檔: 3 個（釋放 ~114 MB）" -ForegroundColor Gray
Write-Host "  • 已移動到 temp/: ~15 個文件" -ForegroundColor Gray
Write-Host "  • 已移動到競賽文件/: 4 個技術文檔" -ForegroundColor Gray
Write-Host "  • docs/ 根目錄: 已清空 ✓" -ForegroundColor Gray

Write-Host "`n查看結果:" -ForegroundColor White
Write-Host "  docs/競賽文件/  - 永久保留的核心文檔" -ForegroundColor Gray
Write-Host "  docs/temp/      - 臨時文檔和備份" -ForegroundColor Gray
Write-Host ""
