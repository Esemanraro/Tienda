param(
  [string]$Repo   = "C:\Users\Homebase\Desktop\tienda",
  [string]$Branch = "main",
  [string]$PyExe  = "C:\Users\Homebase\Desktop\tienda\.venv\Scripts\python.exe"
)

# Fail fast
$ErrorActionPreference = "Stop"

Set-Location $Repo

# Make sure we’re on the right branch
git rev-parse --is-inside-work-tree *> $null
git fetch origin $Branch

# What changed upstream?
$diff = (git diff --name-only HEAD "origin/$Branch") -split "`n" | Where-Object { $_ -ne "" }

# Anything to do?
$ahead = [int](git rev-list "HEAD..origin/$Branch" --count)
if ($ahead -gt 0) {
  Write-Host "🔄 Updates found ($ahead commit(s)). Pulling..."
  # Reset hard (safer than merge for an auto-updater)
  git reset --hard "origin/$Branch"

  # If deps changed, update venv (idempotent)
  if ($diff -contains "requirements.txt") {
    Write-Host "📦 requirements.txt changed → installing deps..."
    & $PyExe -m pip install --upgrade -r "$Repo\requirements.txt"
  }

  # Optional: run migrations if you start using Flask-Migrate later
  # & $PyExe -m flask db upgrade

  Write-Host "✅ Update applied."
} else {
  Write-Host "✅ Already up to date."
}
