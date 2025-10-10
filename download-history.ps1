Param(
  [Parameter(Mandatory = $true)]
  [string] $RepoUrl,                             # e.g. https://github.com/igorkhod/crm
  [string] $Branch,                              # optional; if empty, will detect default_branch
  [string[]] $Paths = @("PROJECT_MAP.md","PROJECT_MAP.full.md"),
  [string] $OutDir = ".\history"
)

# ---------- helpers ----------
function Write-Info($msg){ Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn($msg){ Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err ($msg){ Write-Host "[ERR ] $msg" -ForegroundColor Red }

# Parse owner/repo from various URL styles
function Parse-Repo($url){
  # Normalize
  $u = $url.Trim()

  # https://github.com/owner/repo(.git)?
  if ($u -match '^https?://github\.com/([^/]+)/([^/#?]+)'){
    $owner = $Matches[1]
    $repo  = $Matches[2] -replace '\.git$',''
    return @{ owner=$owner; repo=$repo }
  }

  # git@github.com:owner/repo(.git)
  if ($u -match '^git@github\.com:([^/]+)/([^/#?]+)'){
    $owner = $Matches[1]
    $repo  = $Matches[2] -replace '\.git$',''
    return @{ owner=$owner; repo=$repo }
  }

  # ssh://git@github.com/owner/repo(.git)
  if ($u -match '^ssh://git@github\.com/([^/]+)/([^/#?]+)'){
    $owner = $Matches[1]
    $repo  = $Matches[2] -replace '\.git$',''
    return @{ owner=$owner; repo=$repo }
  }

  throw "Не удалось распарсить RepoUrl: $url"
}

$pr = Parse-Repo $RepoUrl
$owner = $pr.owner
$repo  = $pr.repo

# Base API + headers
$apiBase = "https://api.github.com"
$ua = @{ "User-Agent" = "ps-download-history" }
if ($env:GITHUB_TOKEN -and $env:GITHUB_TOKEN.Trim()){
  $ua["Authorization"] = "Bearer $($env:GITHUB_TOKEN)"
  $ua["Accept"]        = "application/vnd.github+json"
}

# Detect default branch if not provided
if (-not $Branch -or -not $Branch.Trim()){
  Write-Info "Detecting default_branch for $owner/$repo ..."
  try{
    $repoInfo = Invoke-RestMethod -Uri "$apiBase/repos/$owner/$repo" -Headers $ua
    $Branch = $repoInfo.default_branch
    Write-Info "Default branch: $Branch"
  }catch{
    Write-Err "Не удалось получить информацию о репозитории. Проверь RepoUrl и доступ. $_"
    exit 1
  }
}

# Ensure out dir
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

# Helper: fetch all commits that touched specific path
function Get-CommitsForPath([string]$path){
  $page=1
  $pp=100
  $result=@()

  while ($true){
    $url = "$apiBase/repos/$owner/$repo/commits?path=$([uri]::EscapeDataString($path))&sha=$([uri]::EscapeDataString($Branch))&per_page=$pp&page=$page"
    try{
      $resp = Invoke-RestMethod -Uri $url -Headers $ua
    }catch{
      Write-Err "Ошибка запроса commits для '$path': $($_.Exception.Message)"
      if ($_.ErrorDetails.Message){
        Write-Err $_.ErrorDetails.Message
      }
      break
    }

    if (-not $resp -or $resp.Count -eq 0){ break }
    $result += $resp
    if ($resp.Count -lt $pp){ break } # last page
    $page++
  }

  return $result
}

# Helper: download file content at given commit SHA
function Download-FileAtSha([string]$path, [string]$sha, [string]$saveTo){
  $url = "$apiBase/repos/$owner/$repo/contents/$([uri]::EscapeDataString($path))?ref=$sha"
  try{
    $contentResp = Invoke-RestMethod -Uri $url -Headers $ua
  }catch{
    Write-Warn "Не удалось получить содержимое для $path @ $sha: $($_.Exception.Message)"
    return $false
  }
  if (-not $contentResp.content){
    Write-Warn "Пустой ответ content для $path @ $sha"
    return $false
  }
  $bytes = [System.Convert]::FromBase64String(($contentResp.content -replace '\s',''))
  [System.IO.File]::WriteAllBytes($saveTo, $bytes)
  return $true
}

foreach($path in $Paths){
  Write-Host ""
  Write-Host "=== Fetching history for: $path ===" -ForegroundColor Green

  $commits = Get-CommitsForPath $path
  if (-not $commits -or $commits.Count -eq 0){
    Write-Warn "Коммитов не найдено для '$path' на ветке '$Branch'. Проверь имя файла/ветку."
    continue
  }

  $dir = Join-Path $OutDir ($path -replace '[\\/]', '_')
  New-Item -ItemType Directory -Path $dir -Force | Out-Null

  # newest→oldest or наоборот — выбери порядок; здесь сделаем oldest→newest
  $ordered = $commits | Sort-Object { $_.commit.author.date }

  $i=0
  foreach($c in $ordered){
    $i++
    $sha = $c.sha
    $ts  = (Get-Date $c.commit.author.date).ToString("yyyyMMdd-HHmmss")
    $ext = [System.IO.Path]::GetExtension($path)
    if (-not $ext){ $ext = ".txt" }
    $name = "{0:D3}-{1}-{2}{3}" -f $i, $ts, $sha.Substring(0,7), $ext
    $saveTo = Join-Path $dir $name

    $ok = Download-FileAtSha -path $path -sha $sha -saveTo $saveTo
    if ($ok){
      Write-Info "Saved: $saveTo"
    }
  }

  Write-Host "=== Done: $path ($i versions) ===" -ForegroundColor Green
}

Write-Host ""
Write-Info "Finished. Files are in: $OutDir"
