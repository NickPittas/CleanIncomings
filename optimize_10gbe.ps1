# 10GbE SMB Performance Optimization Script
# Run as Administrator to optimize Windows for 10GbE SMB operations

Write-Host "🚀 Optimizing Windows for 10GbE SMB Performance..." -ForegroundColor Green

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "This script requires Administrator privileges. Please run as Administrator."
    exit 1
}

Write-Host "✅ Administrator privileges confirmed" -ForegroundColor Green

# TCP Optimizations for 10GbE
Write-Host "`n🌐 Configuring TCP settings for 10GbE..." -ForegroundColor Yellow
try {
    netsh int tcp set global autotuninglevel=normal
    netsh int tcp set global chimney=enabled  
    netsh int tcp set global rss=enabled
    netsh int tcp set global netdma=enabled
    netsh int tcp set global dca=enabled
    Write-Host "✅ TCP settings optimized" -ForegroundColor Green
} catch {
    Write-Warning "❌ Failed to configure TCP settings: $_"
}

# SMB Client Optimizations
Write-Host "`n📁 Configuring SMB client for maximum speed..." -ForegroundColor Yellow
try {
    Set-SmbClientConfiguration -EnableMultiChannel $true -Force
    Set-SmbClientConfiguration -MaxBufferSize 16777216 -Force  # 16MB buffers
    Set-SmbClientConfiguration -LargeMtu $true -Force
    Set-SmbClientConfiguration -EnableInsecureGuestLogons $false -Force
    Write-Host "✅ SMB client optimized" -ForegroundColor Green
} catch {
    Write-Warning "❌ Failed to configure SMB client: $_"
}

# Network Adapter Optimizations
Write-Host "`n🔌 Checking network adapter settings..." -ForegroundColor Yellow
$adapters = Get-NetAdapter | Where-Object {$_.Status -eq "Up" -and $_.LinkSpeed -like "*Gbps*"}

foreach ($adapter in $adapters) {
    $name = $adapter.Name
    $speed = $adapter.LinkSpeed
    Write-Host "🔍 Optimizing adapter: $name ($speed)" -ForegroundColor Cyan
    
    try {
        # Enable advanced features if available
        Set-NetAdapterAdvancedProperty -Name $name -DisplayName "*Jumbo*" -DisplayValue "9014" -ErrorAction SilentlyContinue
        Set-NetAdapterAdvancedProperty -Name $name -DisplayName "*RSS*" -DisplayValue "Enabled" -ErrorAction SilentlyContinue
        Set-NetAdapterAdvancedProperty -Name $name -DisplayName "*LSO*" -DisplayValue "Enabled" -ErrorAction SilentlyContinue
        Write-Host "✅ Adapter $name optimized" -ForegroundColor Green
    } catch {
        Write-Warning "⚠️ Some advanced features may not be available on $name"
    }
}

# Display current SMB configuration
Write-Host "`n📊 Current SMB Configuration:" -ForegroundColor Cyan
Get-SmbClientConfiguration | Select-Object EnableMultiChannel, MaxBufferSize, LargeMtu

Write-Host "`n🎯 ULTRA-AGGRESSIVE CleanIncomings Settings for 10GbE:" -ForegroundColor Magenta
Write-Host "• Copy Threads: 32-48 threads (to match xcopy performance)" -ForegroundColor White
Write-Host "• Scan Threads: 12-16 threads" -ForegroundColor White
Write-Host "• Files ≥1MB will use ultra-fast copy mode automatically" -ForegroundColor White
Write-Host "• 256MB buffers for maximum speed" -ForegroundColor White

Write-Host "`n🚀 10GbE optimization complete!" -ForegroundColor Green
Write-Host "💡 Restart the application to apply all changes." -ForegroundColor Yellow 