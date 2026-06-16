# Deploy ke Hugging Face Spaces (gratis, tanpa kartu kredit)
# Usage: .\scripts\setup-huggingface.ps1 -Username YOUR_HF_USERNAME

param(
    [Parameter(Mandatory = $true)]
    [string]$Username,

    [string]$SpaceName = "daytrade-ihsg"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path "$PSScriptRoot\.."
Set-Location $Root

$SpaceUrl = "https://huggingface.co/spaces/$Username/$SpaceName"
$RemoteUrl = "$SpaceUrl.git"
$NewSpaceUrl = "https://huggingface.co/new-space?name=$SpaceName&sdk=docker"

Write-Host ""
Write-Host "=== DayTrade Pro — Deploy Hugging Face Spaces ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Membuka halaman buat Space baru..."
Write-Host "   URL: $NewSpaceUrl"
Write-Host ""
Write-Host "   Di Hugging Face:" -ForegroundColor Yellow
Write-Host "   - Space name: $SpaceName"
Write-Host "   - SDK: Docker"
Write-Host "   - Visibility: Public"
Write-Host "   - Klik 'Create Space'"
Write-Host ""
Write-Host "2. Buat Access Token (jika belum punya):"
Write-Host "   https://huggingface.co/settings/tokens (permission: Write)"
Write-Host ""

Start-Process $NewSpaceUrl
Read-Host "Tekan ENTER setelah Space dibuat di Hugging Face"

$existing = git remote get-url space 2>$null
if ($LASTEXITCODE -eq 0) {
    git remote remove space
}

Write-Host "Menambahkan remote: $RemoteUrl"
git remote add space $RemoteUrl

Write-Host "Push ke Hugging Face Space..."
Write-Host "(Login: username=$Username, password=Access Token)" -ForegroundColor Yellow
git push space main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Berhasil! Tunggu build di tab Logs (~5-10 menit)" -ForegroundColor Green
    Write-Host "App URL: https://$Username-$SpaceName.hf.space" -ForegroundColor Green
    Start-Process $SpaceUrl
} else {
    Write-Host ""
    Write-Host "Push gagal. Pastikan:" -ForegroundColor Red
    Write-Host "  1. Space sudah dibuat di Hugging Face"
    Write-Host "  2. Access Token dengan permission Write"
    Write-Host "  3. Jalankan: git push space main"
}
