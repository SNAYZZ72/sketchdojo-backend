# Test SketchDojo Metrics
Write-Host "🔍 Testing SketchDojo Application Metrics" -ForegroundColor Cyan
Write-Host "========================================"

# 1. Generate test traffic
Write-Host "1. Generating test traffic..." -ForegroundColor Yellow
1..20 | ForEach-Object {
    Write-Host "Request $_/20"
    try {
        Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing | Out-Null
        Invoke-WebRequest -Uri "http://localhost:8000/api/v1/webtoons/" -UseBasicParsing | Out-Null
        Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing | Out-Null
    } catch {
        Write-Host "Error making request: $_" -ForegroundColor Red
    }
    Start-Sleep -Seconds 1
}

# 2. Check available metrics
Write-Host "`n2. Available SketchDojo Metrics:" -ForegroundColor Yellow
$metrics = (Invoke-WebRequest -Uri "http://localhost:8000/metrics" -UseBasicParsing).Content -split "`n" |
    Where-Object { $_ -match '^sketchdojo_' }
$metrics | Select-Object -Unique | Sort-Object

# 3. Test specific metrics
Write-Host "`n3. Testing specific metrics..." -ForegroundColor Yellow

# Test request count
Write-Host "`nRequest Count:" -ForegroundColor Green
(Invoke-WebRequest -Uri "http://localhost:8000/metrics" -UseBasicParsing).Content -split "`n" |
    Where-Object { $_ -match 'sketchdojo_requests_total' }

# Test active requests
Write-Host "`nActive Requests:" -ForegroundColor Green
(Invoke-WebRequest -Uri "http://localhost:8000/metrics" -UseBasicParsing).Content -split "`n" |
    Where-Object { $_ -match 'sketchdojo_active_requests' }

# Test error count
Write-Host "`nError Count:" -ForegroundColor Green
(Invoke-WebRequest -Uri "http://localhost:8000/metrics" -UseBasicParsing).Content -split "`n" |
    Where-Object { $_ -match 'sketchdojo_errors_total' }

Write-Host "`n✅ Metrics test completed!" -ForegroundColor Cyan
