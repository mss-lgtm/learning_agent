# 下载并安装Inno Setup 6
# 用于生成Windows安装包

$url = "https://jrsoftware.org/download.php/is.exe"
$output = "$env:TEMP\innosetup.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "下载 Inno Setup 6" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否已安装
$isccPath = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($isccPath) {
    Write-Host "Inno Setup 6 已安装: $isccPath" -ForegroundColor Green
    exit 0
}

Write-Host "正在下载 Inno Setup 6..." -ForegroundColor Yellow
Write-Host "下载地址: $url"
Write-Host ""

try {
    # 使用BITS传输（更快）
    Import-Module BitsTransfer -ErrorAction SilentlyContinue
    if (Get-Command Start-BitsTransfer -ErrorAction SilentlyContinue) {
        Start-BitsTransfer -Source $url -Destination $output -DisplayName "下载 Inno Setup"
    } else {
        # 备用下载方式
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
    }

    Write-Host "下载完成" -ForegroundColor Green
    Write-Host ""
    Write-Host "正在安装 Inno Setup 6..." -ForegroundColor Yellow

    # 静默安装
    Start-Process -FilePath $output -ArgumentList "/VERYSILENT /NORESTART /SUPPRESSMSGBOXES" -Wait

    # 验证安装
    $isccPath = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1

    if ($isccPath) {
        Write-Host "安装成功: $isccPath" -ForegroundColor Green
    } else {
        Write-Host "安装可能成功，请手动检查" -ForegroundColor Yellow
    }

} catch {
    Write-Host "下载或安装失败: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "请手动下载安装 Inno Setup 6:" -ForegroundColor Yellow
    Write-Host "https://jrsoftware.org/isdl.php"
}

# 清理
if (Test-Path $output) {
    Remove-Item $output -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
