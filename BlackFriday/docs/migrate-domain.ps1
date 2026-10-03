# ============================================================================
#  Migración de dominio
#  Uso:
#    powershell -ExecutionPolicy Bypass -File docs\migrate-domain.ps1 `
#             -OldPrefix '<dominio-o-prefijo-anterior>' `
#             -NewPrefix '<dominio-nuevo>'
#
#  Sustituye el prefijo de dominio completo en canonicals, og:url, twitter:image,
#  JSON-LD, sitemap.xml, robots.txt, llms.txt, los scripts de auditoría y los
#  documentos. Hace copia de seguridad antes de tocar nada.
#
#  Importante: el prefijo antiguo NO debe llevar barra final. Así
#    .../antiguo/            -> .../nuevo/
#    .../antiguo/faq.html    -> .../nuevo/faq.html
#
#  Los ejemplos de arriba van con marcadores de posicion porque este fichero
#  se incluye a si mismo en el reemplazo. No pongas URLs reales aqui: la
#  proxima migracion los sobreescribiria.
# ============================================================================

param(
  [Parameter(Mandatory = $true)][string]$OldPrefix,
  [Parameter(Mandatory = $true)][string]$NewPrefix,
  [switch]$NoBackup
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

# Normalizar: sin barra final en ninguno de los dos prefijos
$OldPrefix = $OldPrefix.TrimEnd('/')
$NewPrefix = $NewPrefix.TrimEnd('/')

Write-Host "Prefijo antiguo: $OldPrefix" -ForegroundColor Cyan
Write-Host "Prefijo nuevo : $NewPrefix" -ForegroundColor Cyan
Write-Host ""

# --- Ficheros a procesar ---------------------------------------------------
$targets = @()
$targets += Get-ChildItem -Path $root -Filter *.html  -File
$targets += Get-ChildItem -Path $root -Filter sitemap.xml -File
$targets += Get-ChildItem -Path $root -Filter robots.txt  -File
$targets += Get-ChildItem -Path $root -Filter llms.txt   -File
$targets += Get-ChildItem -Path $root -Filter README.md  -File
$targets += Get-ChildItem -Path (Join-Path $root 'docs') -Filter *.ps1 -File
$targets += Get-ChildItem -Path (Join-Path $root 'docs') -Filter *.md  -File
$targets = $targets | Sort-Object FullName -Unique

# --- Comprobación previa: qué contiene cada fichero ------------------------
Write-Host "=== PREVIA ===" -ForegroundColor Cyan
$plan = @()
foreach ($f in $targets) {
  $t = [IO.File]::ReadAllText($f.FullName, [Text.Encoding]::UTF8)
  $n = ([regex]::Matches($t, [regex]::Escape($OldPrefix))).Count
  if ($n -gt 0) {
    $rel = $f.FullName.Substring($root.Length + 1)
    Write-Host ("  {0,-40} {1,4} ocurrencias" -f $rel, $n)
    $plan += [pscustomobject]@{ File = $f; Rel = $rel; Count = $n }
  }
}
Write-Host ""
Write-Host ("Ficheros afectados: {0} | ocurrencias totales: {1}" -f $plan.Count, ($plan | Measure-Object Count -Sum).Sum) -ForegroundColor White
Write-Host ""

if ($plan.Count -eq 0) {
  Write-Host "Nada que hacer: el prefijo antiguo ya no aparece." -ForegroundColor Yellow
  exit 0
}

# --- Copia de seguridad ----------------------------------------------------
# IMPORTANTE: el backup va FUERA de la raiz del sitio. Si se deja dentro,
# el hosting (Cloudflare Pages, GitHub Pages) lo publicaria como duplicado con
# los canonicals antiguos y contaminaria el SEO del dominio real.
if (-not $NoBackup) {
  $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
  $name = Split-Path -Leaf $root
  $backup = Join-Path ([IO.Path]::GetTempPath()) "$name-backup-$stamp"
  foreach ($p in $plan) {
    $dest = Join-Path $backup $p.Rel
    $dir = Split-Path -Parent $dest
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Copy-Item $p.File.FullName $dest -Force
  }
  Write-Host "Copia de seguridad en: $backup" -ForegroundColor Green
  Write-Host "(fuera de la raiz del sitio, no se publicara)" -ForegroundColor DarkGray
  Write-Host ""
}

# --- Sustitución -----------------------------------------------------------
Write-Host "=== SUSTITUCION ===" -ForegroundColor Cyan
$total = 0
foreach ($p in $plan) {
  $t = [IO.File]::ReadAllText($p.File.FullName, [Text.Encoding]::UTF8)
  $t = $t.Replace($OldPrefix, $NewPrefix)
  # UTF-8 sin BOM
  [IO.File]::WriteAllText($p.File.FullName, $t, (New-Object Text.UTF8Encoding $false))
  $total += $p.Count
  Write-Host ("  OK  {0,-40} {1,4}" -f $p.Rel, $p.Count) -ForegroundColor Green
}
Write-Host ""
Write-Host ("Total sustituido: {0}" -f $total) -ForegroundColor White
Write-Host ""

# --- Verificación ----------------------------------------------------------
Write-Host "=== VERIFICACION ===" -ForegroundColor Cyan
$left = @()
foreach ($f in $targets) {
  $t = [IO.File]::ReadAllText($f.FullName, [Text.Encoding]::UTF8)
  if ($t.Contains($OldPrefix)) {
    $left += $f.FullName.Substring($root.Length + 1)
  }
}
if ($left.Count -eq 0) {
  Write-Host "Sin restos del prefijo antiguo." -ForegroundColor Green
} else {
  Write-Host "QUEDAN RESTOS en:" -ForegroundColor Red
  $left | ForEach-Object { Write-Host "   - $_" -ForegroundColor Red }
}

Write-Host ""
Write-Host "Siguiente paso:" -ForegroundColor White
Write-Host "  powershell -ExecutionPolicy Bypass -File docs\check.ps1"
Write-Host "  powershell -ExecutionPolicy Bypass -File docs\seo-check.ps1"