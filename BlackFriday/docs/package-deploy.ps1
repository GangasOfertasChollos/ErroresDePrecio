# ============================================================================
#  Empaquetado para Cloudflare Pages (drag & drop)
#  Uso:
#    powershell -ExecutionPolicy Bypass -File docs\package-deploy.ps1
#    powershell -ExecutionPolicy Bypass -File docs\package-deploy.ps1 -Zip
#
#  Arma una carpeta limpia con SOLO lo que debe subirse y comprueba que no
#  queden restos del dominio anterior. Los proyectos de Pages con drag & drop
#  suben la carpeta completa: cualquier cosa que dejes en la raiz del sitio
#  acaba publicada, incluidos los scripts de este directorio.
# ============================================================================

param(
  [string]$OutDir,
  [switch]$Zip
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

if (-not $OutDir) {
  $OutDir = Join-Path ([IO.Path]::GetTempPath()) 'BlackFriday-deploy'
}

# --- Qué se despliega ------------------------------------------------------
# Deliberadamente: el HTML, los assets y los ficheros de raíz para buscadores.
# Fuera: docs/, README.md y los .ps1 (nada del sitio los enlaza).
$includeFiles = @('*.html', 'sitemap.xml', 'robots.txt', 'llms.txt')

Write-Host "Origen   : $root" -ForegroundColor Cyan
Write-Host "Destino  : $OutDir" -ForegroundColor Cyan
Write-Host ""

# --- Limpiar destino -------------------------------------------------------
if (Test-Path $OutDir) {
  Write-Host "Limpiando destino..." -ForegroundColor DarkGray
  Remove-Item $OutDir -Recurse -Force
}
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

# --- Copiar ----------------------------------------------------------------
Write-Host "=== COPIANDO ===" -ForegroundColor Cyan
$copied = 0
foreach ($pat in $includeFiles) {
  foreach ($f in (Get-ChildItem -Path $root -Filter $pat -File)) {
    Copy-Item $f.FullName (Join-Path $OutDir $f.Name) -Force
    Write-Host ("  + {0,-40} {1,8:N0} B" -f $f.Name, $f.Length)
    $copied++
  }
}

$assetsIn  = Join-Path $root 'assets'
$assetsOut = Join-Path $OutDir 'assets'
Copy-Item $assetsIn $assetsOut -Recurse -Force
$assetsCount = (Get-ChildItem $assetsOut -Recurse -File).Count
$assetsSize  = (Get-ChildItem $assetsOut -Recurse -File | Measure-Object Length -Sum).Sum
Write-Host ("  + {0,-40} {1,8:N0} B  ({2} ficheros)" -f 'assets/', $assetsSize, $assetsCount)
Write-Host ""
Write-Host ("Ficheros copiados: {0} + {1} de assets" -f $copied, $assetsCount) -ForegroundColor White
Write-Host ""

# --- Qué queda fuera (a propósito) -----------------------------------------
$excluded = @()
$excluded += Get-ChildItem -Path $root -Filter *.md  -File  | ForEach-Object { $_.Name }
$excluded += Get-ChildItem -Path $root -Filter *.ps1 -File  | ForEach-Object { $_.Name }
if (Test-Path (Join-Path $root 'docs')) {
  $excluded += Get-ChildItem -Path (Join-Path $root 'docs') -Recurse -File |
               ForEach-Object { 'docs/' + $_.Name }
}
Write-Host "Excluido a proposito:" -ForegroundColor Cyan
$excluded | ForEach-Object { Write-Host "  - $_" -ForegroundColor DarkGray }
Write-Host ""

# --- Comprobaciones de seguridad -------------------------------------------
Write-Host "=== COMPROBACIONES ===" -ForegroundColor Cyan
$fail = 0

# 1. Ningun resto del dominio anterior
$stale = @()
foreach ($f in (Get-ChildItem $OutDir -Recurse -File)) {
  $t = [IO.File]::ReadAllText($f.FullName, [Text.Encoding]::UTF8)
  if ($t -match 'github\.io') { $stale += $f.Name }
}
if ($stale.Count) {
  Write-Host "  FAIL  dominio anterior en: $($stale -join ', ')" -ForegroundColor Red
  $fail++
} else {
  Write-Host "  OK    sin restos de github.io" -ForegroundColor Green
}

# 2. Ningun script dentro del paquete
$scripts = (Get-ChildItem $OutDir -Recurse -File -Include *.ps1,*.md).Count
if ($scripts) {
  Write-Host "  FAIL  hay $scripts ficheros .ps1/.md en el paquete" -ForegroundColor Red
  $fail++
} else {
  Write-Host "  OK    ningun .ps1 ni .md en el paquete" -ForegroundColor Green
}

# 3. Token de Search Console en la portada
$idx = [IO.File]::ReadAllText((Join-Path $OutDir 'index.html'), [Text.Encoding]::UTF8)
if ($idx -match 'google-site-verification') {
  Write-Host "  OK    meta google-site-verification presente en index.html" -ForegroundColor Green
} else {
  Write-Host "  FAIL  falta el meta google-site-verification" -ForegroundColor Red
  $fail++
}

# 4. Canonical de la portada
if ($idx -match 'rel="canonical" href="([^"]+)"') {
  Write-Host "  OK    canonical portada: $($Matches[1])" -ForegroundColor Green
}

# 5. Los 17 HTML presentes
$htmlCount = (Get-ChildItem $OutDir -Filter *.html -File).Count
if ($htmlCount -eq 17) {
  Write-Host "  OK    17 paginas HTML" -ForegroundColor Green
} else {
  Write-Host "  FAIL  hay $htmlCount HTML, se esperaban 17" -ForegroundColor Red
  $fail++
}

# --- Zip opcional ----------------------------------------------------------
if ($Zip) {
  $zip = "$OutDir.zip"
  if (Test-Path $zip) { Remove-Item $zip -Force }
  Compress-Archive -Path (Join-Path $OutDir '*') -DestinationPath $zip -Force
  Write-Host ""
  Write-Host "Zip: $zip ({0:N0} B)" -f (Get-Item $zip).Length -ForegroundColor Green
}

Write-Host ""
if ($fail) {
  Write-Host "PAQUETE NO VALIDO: $fail comprobacion(es) fallida(s)." -ForegroundColor Red
  exit 1
}

Write-Host "PAQUETE LISTO." -ForegroundColor Green
Write-Host ""
Write-Host "Siguiente paso:" -ForegroundColor White
Write-Host "  1. Cloudflare Dashboard > Workers & Pages > <tu proyecto> > Create a new deployment > Upload assets"
Write-Host "  2. Arrastra la CARPETA"
if ($Zip) { Write-Host "     (o prueba con el zip; si el panel lo rechaza, usa la carpeta)" }
Write-Host ""
Write-Host "  $OutDir"
Write-Host ""
Write-Host "Comprueba despues:" -ForegroundColor White
Write-Host "  https://<proyecto>.pages.dev/robots.txt   -> dominio nuevo"
Write-Host "  view-source de la portada                 -> google-site-verification presente"