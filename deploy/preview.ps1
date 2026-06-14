# 公開預覽：本機 Gunicorn + Cloudflare Tunnel（免註冊、免開 port）
# 用法：.\deploy\preview.ps1
# 分享輸出的 https://xxx.trycloudflare.com 給他人即可預覽

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Python = Join-Path $Root "venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Host "找不到 venv，請先執行: python -m venv venv; pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

$CloudflaredDir = Join-Path $Root "tools"
$Cloudflared = Join-Path $CloudflaredDir "cloudflared.exe"
if (-not (Test-Path $Cloudflared)) {
    Write-Host "下載 cloudflared..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Force -Path $CloudflaredDir | Out-Null
    $Url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    Invoke-WebRequest -Uri $Url -OutFile $Cloudflared -UseBasicParsing
}

$Port = if ($env:RUN_PORT) { $env:RUN_PORT } else { "9000" }

Write-Host "設定預覽安全（後台密碼 + 通行碼）..." -ForegroundColor Cyan
& $Python scripts\setup_preview_security.py

$CredsFile = Join-Path $Root "deploy\preview-credentials.local.txt"
if (Test-Path $CredsFile) {
    Get-Content $CredsFile | ForEach-Object {
        if ($_ -match "^PREVIEW_PASSWORD=(.+)$") { $env:PREVIEW_PASSWORD = $Matches[1] }
    }
}

$env:DEBUG = "False"
$env:PREVIEW_MODE = "True"
$env:PREVIEW_READONLY = "True"
$env:ALLOWED_HOSTS = ".trycloudflare.com,localhost,127.0.0.1"
$env:BEHIND_PROXY = "True"
$env:SERVE_MEDIA = "True"
$env:SECURE_SSL_REDIRECT = "False"
$env:SESSION_COOKIE_SECURE = "True"
$env:CSRF_COOKIE_SECURE = "True"

Write-Host "收集靜態檔..." -ForegroundColor Cyan
& $Python manage.py collectstatic --noinput | Out-Null

# 避免 port 9000 被舊程序占用
Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique |
  ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }

Write-Host "啟動 WSGI 伺服器 (port $Port)..." -ForegroundColor Cyan
$ServeArgs = @("scripts\serve.py")
$GunicornProc = Start-Process -FilePath $Python -ArgumentList $ServeArgs -PassThru -WorkingDirectory $Root -WindowStyle Hidden

Start-Sleep -Seconds 3

Write-Host "建立 Cloudflare Tunnel..." -ForegroundColor Cyan
Write-Host "（首次可能需要 10–30 秒，請稍候）" -ForegroundColor Yellow
Write-Host ""

$TunnelLog = Join-Path $Root "tools\tunnel.log"
if (Test-Path $TunnelLog) { Remove-Item $TunnelLog -Force }

$TunnelProc = Start-Process -FilePath $Cloudflared -ArgumentList @(
    "tunnel", "--url", "http://127.0.0.1:$Port", "--logfile", $TunnelLog, "--loglevel", "info"
) -PassThru -WorkingDirectory $Root -WindowStyle Hidden

$PublicUrl = $null
for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Seconds 1
    if (Test-Path $TunnelLog) {
        $log = Get-Content $TunnelLog -Raw -ErrorAction SilentlyContinue
        if ($log -match "(https://[a-z0-9-]+\.trycloudflare\.com)") {
            $PublicUrl = $Matches[1]
            break
        }
    }
}

Write-Host "========================================" -ForegroundColor Green
if ($PublicUrl) {
    Write-Host "  公開預覽網址：" -ForegroundColor Green
    Write-Host "  $PublicUrl" -ForegroundColor White -BackgroundColor DarkGreen
    Write-Host ""
    if ($env:PREVIEW_PASSWORD) {
        Write-Host "  預覽通行碼：$($env:PREVIEW_PASSWORD)" -ForegroundColor Yellow
        Write-Host "  （請私下提供給訪客，勿公開張貼）" -ForegroundColor Yellow
        Write-Host ""
    }
    Write-Host "  產線導覽：$PublicUrl/zone/plant1-production/" -ForegroundColor Cyan
    Write-Host "  VR 展覽館：$PublicUrl/vr/plant1-production/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  後台密碼見：deploy\preview-credentials.local.txt" -ForegroundColor DarkGray
} else {
    Write-Host "  Tunnel 建立中，請查看 log: $TunnelLog" -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "按 Ctrl+C 停止預覽（會關閉 tunnel 與 gunicorn）" -ForegroundColor Yellow

try {
    while ($true) { Start-Sleep -Seconds 5 }
} finally {
    Write-Host "停止服務..." -ForegroundColor Yellow
    if ($TunnelProc -and -not $TunnelProc.HasExited) { Stop-Process -Id $TunnelProc.Id -Force -ErrorAction SilentlyContinue }
    if ($GunicornProc -and -not $GunicornProc.HasExited) { Stop-Process -Id $GunicornProc.Id -Force -ErrorAction SilentlyContinue }
}
