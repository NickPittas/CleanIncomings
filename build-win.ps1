# Build script for Windows
Write-Host "🚀 Starting build process..." -ForegroundColor Green

# Clean previous builds
if (Test-Path "release") {
    Write-Host "🧹 Cleaning previous build..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force release
}

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
yarn install --frozen-lockfile

# Build the renderer and main process
Write-Host "🔨 Building application..." -ForegroundColor Cyan
yarn build

# Verify build output
if (-not (Test-Path "dist/main.js")) {
    Write-Error "❌ Main process build failed - dist/main.js not found"
    exit 1
}

if (-not (Test-Path "dist/renderer/index.html")) {
    Write-Error "❌ Renderer build failed - dist/renderer/index.html not found"
    exit 1
}

# Package the application
Write-Host "📦 Packaging application..." -ForegroundColor Cyan
yarn package:win

# Check if packaging was successful
if (-not (Test-Path "release\win-unpacked")) {
    Write-Error "❌ Packaging failed - win-unpacked directory not found"
    exit 1
}

Write-Host "✅ Build and package completed successfully!" -ForegroundColor Green
Write-Host "📦 Output directory: $(Resolve-Path "release\win-unpacked")" -ForegroundColor Cyan
Write-Host "
To run the application, execute:
  .\release\win-unpacked\Folder Normalizer.exe
" -ForegroundColor Yellow
