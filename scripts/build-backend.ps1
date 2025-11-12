Param(
    [switch]$Clean,
    [string]$SpecPath = "backend.spec"
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Error "未找到 uv 命令，请先安装 uv（https://docs.astral.sh/uv/）。"
}

if (-not $env:UV_HTTP_TIMEOUT) {
    $env:UV_HTTP_TIMEOUT = "120"
}

if (-not (Test-Path $SpecPath)) {
    Write-Error "Spec 文件 $SpecPath 不存在。"
}

$uvArgs = @("tool", "run")
$toolDependencies = @(
    "aiofiles",
    "python-multipart",
    "fastapi",
    "uvicorn[standard]",
    "sqlmodel",
    "httpx",
    "loguru",
    "langchain",
    "langchain-community",
    "langchain-openai",
    "langchain-ollama",
    "langgraph",
    "pydantic-settings",
    "python-jose[cryptography]",
    "passlib[bcrypt]",
    "civitai-py",
    "pillow"
)

foreach ($dep in $toolDependencies) {
    $uvArgs += @("--with", $dep)
}

$uvArgs += @("--from", "pyinstaller", "pyinstaller", "--noconfirm")
if ($Clean) {
    $uvArgs += "--clean"
}
$uvArgs += $SpecPath

Write-Host "==> 使用 PyInstaller 打包后端（Spec: $SpecPath）"
Write-Host "==> 命令：uv $($uvArgs -join ' ')"

$process = Start-Process -FilePath "uv" -ArgumentList $uvArgs -NoNewWindow -Wait -PassThru
if ($process.ExitCode -ne 0) {
    Write-Error "PyInstaller 打包失败，退出代码：$($process.ExitCode)"
}

$exePath = Join-Path $projectRoot "dist/ComicForgeBackend/ComicForgeBackend.exe"
if (-not (Test-Path $exePath)) {
    Write-Error "未找到打包产物：$exePath"
}

$targetDir = Join-Path $projectRoot "src-tauri/bin"
if (-not (Test-Path $targetDir)) {
    Write-Host "⚠️ 未找到 $targetDir，跳过复制操作（如未来引入 Tauri，可创建该目录）。"
} else {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Copy-Item $exePath -Destination $targetDir -Force
    Write-Host "✅ 已复制可执行文件到 $targetDir"
}

Write-Host "🎉 后端打包完成：$exePath"


