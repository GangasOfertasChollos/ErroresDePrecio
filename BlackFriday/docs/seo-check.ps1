# ============================================================================
#  Auditoría SEO
#  Uso:  powershell -ExecutionPolicy Bypass -File docs\seo-check.ps1
#  Comprueba: unicidad de title/description, longitud, canonicals,
#  jerarquía de encabezados, schema, enlazado interno y presencia de CTA.
# ============================================================================

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$site = 'https://gangasofertas.com/BlackFriday'
$errors = @()
$warns = @()

$pages = @{}
foreach ($f in (Get-ChildItem -Path $root -Filter *.html -File | Sort-Object Name)) {
  $pages[$f.Name] = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
}

Write-Host "=== 1. TITULOS Y DESCRIPCIONES ===" -ForegroundColor Cyan

foreach ($name in ($pages.Keys | Sort-Object)) {
  $t = $pages[$name]
  $is404 = $name -eq '404.html'

  $title = if ($t -match '(?s)<title>(.*?)</title>') { $Matches[1].Trim() } else { '' }
  $desc = if ($t -match '(?s)<meta name="description" content="(.*?)">') { $Matches[1].Trim() } else { '' }
  $canon = if ($t -match 'rel="canonical" href="([^"]+)"') { $Matches[1] } else { '' }
  $h1 = ([regex]::Matches($t, '<h1[\s>]')).Count

  $flag = 'OK '
  $notes = @()

  if ([string]::IsNullOrWhiteSpace($title)) { $notes += 'sin title'; $flag = 'ERR' }
  elseif ($title.Length -gt 65) { $notes += "title largo ($($title.Length))"; if ($flag -eq 'OK ') { $flag = 'WARN' } }
  elseif ($title.Length -lt 25) { $notes += "title corto ($($title.Length))"; if ($flag -eq 'OK ') { $flag = 'WARN' } }

  if ([string]::IsNullOrWhiteSpace($desc)) { $notes += 'sin description'; $flag = 'ERR' }
  else {
    $len = $desc.Length
    if ($len -gt 170) { $notes += "description larga ($len)"; if ($flag -eq 'OK ') { $flag = 'WARN' } }
    elseif ($len -lt 90) { $notes += "description corta ($len)"; if ($flag -eq 'OK ') { $flag = 'WARN' } }
  }

  if ([string]::IsNullOrWhiteSpace($canon)) { $notes += 'sin canonical'; $flag = 'ERR' }
  if (-not $is404 -and $canon -and -not $canon.StartsWith($site)) { $notes += 'canonical fuera del dominio'; $flag = 'ERR' }
  if ($h1 -ne 1) { $notes += "h1 = $h1"; $flag = 'ERR' }

  $line = "{0} {1,-42} {2,3} car.  {3,3} car. desc" -f $flag, $name, $title.Length, $desc.Length
  if ($notes.Count) { $line += "  (" + ($notes -join '; ') + ')' }
  Write-Host $line
  if ($flag -eq 'ERR') { $errors += "$name : $($notes -join '; ')" }
  elseif ($flag -eq 'WARN') { $warns += "$name : $($notes -join '; ')" }
}

Write-Host ""
Write-Host "=== 2. UNICIDAD ===" -ForegroundColor Cyan

$titles = @{}
$descs = @{}
foreach ($name in ($pages.Keys | Sort-Object)) {
  $t = $pages[$name]
  if ($t -match '(?s)<title>(.*?)</title>') {
    $ti = $Matches[1].Trim()
    if ($titles.ContainsKey($ti)) { $errors += "Title duplicado entre $($titles[$ti]) y $name" ; Write-Host "ERR title duplicado: $name" -ForegroundColor Red }
    else { $titles[$ti] = $name }
  }
  if ($t -match '(?s)<meta name="description" content="(.*?)">') {
    $de = $Matches[1].Trim()
    if ($descs.ContainsKey($de)) { $errors += "Description duplicada entre $($descs[$de]) y $name"; Write-Host "ERR description duplicada: $name" -ForegroundColor Red }
    else { $descs[$de] = $name }
  }
}
Write-Host ("Paginas revisadas: {0} | titles unicos: {1} | descriptions unicas: {2}" -f $pages.Count, $titles.Count, $descs.Count)

Write-Host ""
Write-Host "=== 3. SCHEMA / DATOS ESTRUCTURADOS ===" -ForegroundColor Cyan

foreach ($name in ($pages.Keys | Sort-Object)) {
  $t = $pages[$name]
  $types = @()
  foreach ($ty in @('FAQPage', 'Article', 'BreadcrumbList', 'Event', 'ItemList', 'HowTo', 'WebSite', 'Organization', 'Definition', 'AboutPage')) {
    if ($t -match [regex]::Escape("`"$ty`"")) { $types += $ty }
  }
  $ok = if ($types.Count -gt 0) { 'OK ' } else { 'ERR' }
  if ($types.Count -eq 0) { $errors += "$name sin JSON-LD" }
  Write-Host ("{0} {1,-42} {2}" -f $ok, $name, ($types -join ', '))
}

Write-Host ""
Write-Host "=== 4. VALIDACION JSON-LD ===" -ForegroundColor Cyan

foreach ($name in ($pages.Keys | Sort-Object)) {
  $t = $pages[$name]
  $blocks = [regex]::Matches($t, '(?s)<script type="application/ld\+json">(.*?)</script>')
  if ($blocks.Count -eq 0) { continue }
  for ($bi = 0; $bi -lt $blocks.Count; $bi++) {
    try {
      $null = $blocks[$bi].Groups[1].Value | ConvertFrom-Json
      Write-Host ("OK  {0} (bloque {1})" -f $name, $bi + 1)
    } catch {
      Write-Host ("ERR {0} bloque {1} : {2}" -f $name, $bi + 1, $_.Exception.Message) -ForegroundColor Red
      $errors += "$name JSON-LD invalido (bloque $($bi+1))"
    }
  }
}

Write-Host ""
Write-Host "=== 5. ENLAZADO INTERNO ===" -ForegroundColor Cyan

$inbound = @{}
foreach ($n in $pages.Keys) { $inbound[$n] = 0 }
foreach ($name in ($pages.Keys | Sort-Object)) {
  foreach ($h in [regex]::Matches($pages[$name], 'href="([a-z0-9\-]+\.html)')) {
    $tg = $h.Groups[1].Value
    if ($inbound.ContainsKey($tg) -and $tg -ne $name) { $inbound[$tg]++ }
  }
}
foreach ($n in ($inbound.Keys | Sort-Object { $inbound[$_] })) {
  if ($n -eq '404.html') { continue }
  $flag = if ($inbound[$n] -eq 0) { 'ERR' } else { 'OK ' }
  if ($inbound[$n] -eq 0) { $errors += "$n sin enlaces entrantes" }
  Write-Host ("{0} {1,-42} {2} enlaces entrantes" -f $flag, $n, $inbound[$n])
}

Write-Host ""
Write-Host "=== 6. CTA AL CANAL DE TELEGRAM ===" -ForegroundColor Cyan

foreach ($name in ($pages.Keys | Sort-Object)) {
  $t = $pages[$name]
  $cta = ([regex]::Matches($t, 'href="https://t\.me/GangasOfertasChollos"')).Count
  $sponsored = ([regex]::Matches($t, 'rel="sponsored nofollow noopener"')).Count
  $flag = if ($cta -gt 0) { 'OK ' } else { 'WARN' }
  if ($cta -eq 0) { $warns += "$name sin CTA al canal" }
  Write-Host ("{0} {1,-42} {2} CTA / {3} con rel sponsored" -f $flag, $name, $cta, $sponsored)
}

Write-Host ""
Write-Host "=== 7. PESO Y RENDIMIENTO ===" -ForegroundColor Cyan

foreach ($name in ($pages.Keys | Sort-Object)) {
  $bytes = (Get-Item (Join-Path $root $name)).Length
  $words = ([regex]::Matches($pages[$name], '(?s)<body.*?</body>') | ForEach-Object {
    $x = [regex]::Replace($_.Value, '(?s)<[^>]+>', ' ')
    ([regex]::Matches($x, '\S+')).Count
  })
  $flag = if ($bytes -lt 130KB) { 'OK ' } else { 'WARN' }
  Write-Host ("{0} {1,-42} {2,7:N0} bytes  {3,5} palabras" -f $flag, $name, $bytes, $words)
}

$css = (Get-Item (Join-Path $root 'assets\css\style.css')).Length
$js = (Get-Item (Join-Path $root 'assets\js\main.js')).Length
$og = (Get-Item (Join-Path $root 'assets\img\og-black-friday-2026.png')).Length
Write-Host ""
Write-Host ("assets: style.css {0:N0} B | main.js {1:N0} B | og-image {2:N0} B" -f $css, $js, $og)

Write-Host ""
Write-Host "=== RESUMEN ===" -ForegroundColor Cyan
Write-Host ("Paginas: {0}" -f $pages.Count) -ForegroundColor White
if ($errors.Count) { Write-Host ("Errores:  " + $errors.Count) -ForegroundColor Red; $errors | ForEach-Object { Write-Host "   - $_" -ForegroundColor Red } }
else { Write-Host "Errores:  0" -ForegroundColor Green }
if ($warns.Count) { Write-Host ("Avisos:   " + $warns.Count) -ForegroundColor Yellow; $warns | ForEach-Object { Write-Host "   - $_" -ForegroundColor Yellow } }
else { Write-Host "Avisos:   0" -ForegroundColor Green }