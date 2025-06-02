# PowerShell script to run SketchDojo backend in Docker
param (
    [switch]$BuildOnly,
    [switch]$Rebuild
)

# Navigate to the docker directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "🐳 SketchDojo Docker Environment Setup" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Cyan

# Check if .env file exists, create if not
$envFile = ".env"
$parentDir = (Get-Item $scriptPath).Parent.FullName
$envPath = Join-Path $parentDir $envFile

if (-not (Test-Path $envPath)) {
    Write-Host "Creating .env file with default values..." -ForegroundColor Yellow
    @"
# SketchDojo Environment Variables
# Replace with your actual API keys in production

# Security
SECRET_KEY=development_secret_key_replace_in_production
JWT_SECRET=development_jwt_secret_replace_in_production

# AI Services
OPENAI_API_KEY=your_openai_api_key_here
STABILITY_API_KEY=your_stability_api_key_here

# Environment
ENVIRONMENT=development
DEBUG=true
"@ | Out-File -FilePath $envPath -Encoding utf8
    Write-Host "Created .env file. Please edit with your API keys before running again." -ForegroundColor Green
    Write-Host "File location: $envPath" -ForegroundColor Yellow
    exit
}

# Build/rebuild containers if requested
if ($Rebuild) {
    Write-Host "Rebuilding all containers..." -ForegroundColor Yellow
    docker-compose -f docker-compose.yml build --no-cache
} elseif ($BuildOnly) {
    Write-Host "Building containers..." -ForegroundColor Yellow
    docker-compose -f docker-compose.yml build
    exit
}

# Start the containers
Write-Host "Starting SketchDojo backend services..." -ForegroundColor Green
docker-compose -f docker-compose.yml up

# Provide instructions when stopped
Write-Host "`nContainers stopped." -ForegroundColor Yellow
Write-Host "To restart: ./run-docker.ps1" -ForegroundColor Cyan
Write-Host "To rebuild: ./run-docker.ps1 -Rebuild" -ForegroundColor Cyan
