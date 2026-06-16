# Setup GitHub repo & push — DayTrade Pro
# Usage: .\scripts\setup-github.ps1 -Username YOUR_GITHUB_USERNAME

param(
    [Parameter(Mandatory = $true)]
    [string]$Username,

    [string]$RepoName = "daytrade-ihsg"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path "$PSScriptRoot\.."
Set-Location $Root

$RemoteUrl = "https://github.com/$Username/$RepoName.git"
$NewRepoUrl = "https://github.com/new?name=$RepoName&description=DayTrade+Pro+-+Rekomendasi+Saham+IHSG&visibility=public"

Write-Host ""
Write-Host "=== DayTrade Pro — Setup GitHub ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Membuka halaman buat repo baru di browser..."
Write-Host "   URL: $NewRepoUrl"
Write-Host ""
Write-Host "   Di GitHub:" -ForegroundColor Yellow
Write-Host "   - Repository name: $RepoName"
Write-Host "   - Public"
Write-Host "   - JANGAN centang 'Add README' (sudah ada di lokal)"
Write-Host "   - Klik 'Create repository'"
Write-Host ""

Start-Process $NewRepoUrl
Read-Host "Tekan ENTER setelah repo dibuat di GitHub"

# Remove old origin if exists
$existing = git remote get-url origin 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Menghapus remote origin lama: $existing"
    git remote remove origin
}

Write-Host "Menambahkan remote: $RemoteUrl"
git remote add origin $RemoteUrl

Write-Host "Push ke GitHub..."
git branch -M main
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Berhasil! Repo: https://github.com/$Username/$RepoName" -ForegroundColor Green
    Write-Host ""
    Write-Host "Langkah berikutnya — Deploy Render:" -ForegroundColor Cyan
    Write-Host "1. Buka https://dashboard.render.com"
    Write-Host "2. New -> Blueprint -> pilih repo '$RepoName'"
    Write-Host "3. Apply -> tunggu deploy selesai"
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Push gagal. Coba login GitHub:" -ForegroundColor Red
    Write-Host "  git push -u origin main"
    Write-Host ""
    Write-Host "Atau gunakan Personal Access Token sebagai password saat diminta."
    Write-Host "Buat token: https://github.com/settings/tokens"
}
