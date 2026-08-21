Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " STARTING UNIVERSAL BOOK VAULT OVERNIGHT GENERATOR" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$env:PYTHONPATH = "c:\g\book-vault"

# 1. Clean any leftover lock files safely
try {
    if (Test-Path "c:\g\book-vault\automation\.pipeline.lock") {
        Remove-Item "c:\g\book-vault\automation\.pipeline.lock" -Force -ErrorAction SilentlyContinue
    }
} catch {}

# 2. Main Generation Loop (Runs continuously through all ungenerated books)
Write-Host "Launching Continuous Autonomous Generation Loop..." -ForegroundColor Yellow
python -m automation.engines.generate --loop --workers 5

# 3. Post-Processing: Cross-Pillar Graph, Audiobookshelf, and Web Catalog Data
Write-Host "Building Cross-Pillar Semantic Graph..." -ForegroundColor Green
python -m automation.engines.cross_pillar_graph

Write-Host "Exporting Audiobookshelf Metadata..." -ForegroundColor Green
python -m automation.exporters.export_audiobookshelf

Write-Host "Rebuilding Web Catalog and Dashboards..." -ForegroundColor Green
python -m automation.exporters.build_site_data

Write-Host "ALL VAULT BOOKS GENERATED AND PROCESSED SUCCESSFULLY!" -ForegroundColor Green
