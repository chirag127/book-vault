Clear-Host
Write-Host ""
Write-Host "  ================================================================" -ForegroundColor Cyan
Write-Host "   🚀 UNIVERSAL BOOK VAULT — AUTONOMOUS PIPELINE RUNNER" -ForegroundColor Cyan -BackgroundColor Black
Write-Host "  ================================================================" -ForegroundColor Cyan
Write-Host ""

$env:PYTHONPATH = "c:\g\book-vault"

# 1. Clean any leftover lock files safely
try {
    if (Test-Path "c:\g\book-vault\automation\.pipeline.lock") {
        Remove-Item "c:\g\book-vault\automation\.pipeline.lock" -Force -ErrorAction SilentlyContinue
        Write-Host "  [cleanup] Removed stale pipeline lock file." -ForegroundColor DarkGray
    }
} catch {}

# 2. Main Generation Loop (Runs continuously through all ungenerated books)
Write-Host "  ▶ [Phase 1/4] Starting Autonomous Book Generation Engine..." -ForegroundColor Yellow
python -m automation.engines.generate --loop --workers 5

# 3. Post-Processing: Cross-Pillar Graph, Audiobookshelf, Covers, and Web Catalog Data
Write-Host ""
Write-Host "  ▶ [Phase 2/4] Building Cross-Pillar Semantic Graph..." -ForegroundColor Magenta
python -m automation.engines.cross_pillar_graph

Write-Host ""
Write-Host "  ▶ [Phase 3/4] Exporting Audiobookshelf Metadata..." -ForegroundColor Blue
python -m automation.exporters.export_audiobookshelf

Write-Host ""
Write-Host "  ▶ [Phase 4/4] Resolving Verified Book Covers and Rich Metadata..." -ForegroundColor Cyan
python -m automation.exporters.fetch_covers

Write-Host ""
Write-Host "  ▶ Compiling Web Explorer & Dashboard Catalog..." -ForegroundColor Green
python -m automation.exporters.build_site_data

Write-Host ""
Write-Host "  ================================================================" -ForegroundColor Green
Write-Host "   🎉 ALL VAULT BOOKS GENERATED AND PROCESSED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "  ================================================================" -ForegroundColor Green
Write-Host ""
