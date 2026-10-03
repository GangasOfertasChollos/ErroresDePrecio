# ============================================================================
#  Validador de contenido del sitio
#  Uso:  powershell -ExecutionPolicy Bypass -File docs\check.ps1
#  Detecta: caracteres fuera del latinio, HTML mal formado basico,
#           estructura SEO ausente y palabras no españolas conocidas.
# ============================================================================

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

# Palabras que nunca deben aparecer (idiomas o corrupciones tipicas)
$badWords = @(
  'bonnes','souvent','meer-than','ertainas','helped','utterly','competitiveness',
  'launchan','pathology','intensityes','infladopreviously','sounding',
  'MUNDIALES','LOBALS','Feng','either','accumulation','Tapetes de esta',
  'EnAws','picardía','ACH buys'
)

$report = @()

foreach ($file in (Get-ChildItem -Path $root -Filter *.html -File | Sort-Object Name)) {
  $t = [System.IO.File]::ReadAllText($file.FullName, [System.Text.Encoding]::UTF8)
  $issues = @()

  # 1. Caracteres fuera del rango latino (cirilico, CJK, kana, hangul, puntuacion CJK)
  $m = [regex]::Matches($t, '[\u0370-\u04FF\u3000-\u303F\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF\uFF00-\uFFEF]')
  if ($m.Count -gt 0) {
    foreach ($x in $m) {
      $i = $x.Index
      $ctx = $t.Substring([Math]::Max(0, $i - 45), [Math]::Min(95, $t.Length - [Math]::Max(0, $i - 45))) -replace '\s+', ' '
      $issues += "  [NO-LATINO] U+{0:X4} :: {1}" -f [int][char]$x.Value[0], $ctx
    }
  }

  # 2. Palabras sospechosas
  foreach ($w in $badWords) {
    $hits = [regex]::Matches($t, [regex]::Escape($w), 'IgnoreCase')
    foreach ($h in $hits) {
      $i = $h.Index
      $ctx = $t.Substring([Math]::Max(0, $i - 45), [Math]::Min(95, $t.Length - [Math]::Max(0, $i - 45))) -replace '\s+', ' '
      $issues += "  [PALABRA] '$w' :: $ctx"
    }
  }

  # 3. Estructura SEO minima
  $required = [ordered]@{
    'lang="es"'        = $t -match '<html lang="es"'
    'title'            = $t -match '<title>.{15,}</title>'
    'meta description' = $t -match '<meta name="description" content=".{60,}"'
    'canonical'        = $t -match 'rel="canonical"'
    'og:title'         = $t -match 'property="og:title"'
    'og:image'         = $t -match 'property="og:image"'
    'h1 unico'         = ([regex]::Matches($t, '<h1[\s>]')).Count -eq 1
    'enlace al canal'  = $t -match 't\.me/GangasOfertasChollos'
    'viewport'         = $t -match 'name="viewport"'
    'json-ld'          = $t -match 'application/ld\+json'
  }
  foreach ($k in $required.Keys) {
    if (-not $required[$k]) { $issues += "  [SEO] falta o invalido: $k" }
  }

  # 4. Enlaces rotos internos
  foreach ($href in [regex]::Matches($t, 'href="([a-z0-9\-]+\.html)(#[^"]*)?"')) {
    $target = Join-Path $root $href.Groups[1].Value
    if (-not (Test-Path $target)) { $issues += "  [ENLACE] roto: $($href.Groups[1].Value)" }
  }

  # 5. Balance de etiquetas principales
  foreach ($pair in @(@('section','section'), @('div','div'), @('details','details'))) {
    $o = ([regex]::Matches($t, "<$($pair[0])[\s>]")).Count
    $c = ([regex]::Matches($t, "</$($pair[1])>")).Count
    if ($o -ne $c) { $issues += "  [HTML] desbalance: <$($pair[0])>=$o vs </$($pair[1])>=$c" }
  }

  if ($issues.Count -eq 0) {
    Write-Host ("OK   " + $file.Name) -ForegroundColor Green
  } else {
    Write-Host ("FAIL " + $file.Name) -ForegroundColor Red
    $report += $issues
    $issues | ForEach-Object { Write-Host $_ -ForegroundColor Yellow }
  }
}

Write-Host ""
if ($report.Count -eq 0) {
  Write-Host "Todos los archivos HTML pasan la validacion." -ForegroundColor Green
} else {
  Write-Host ("Total de problemas: " + $report.Count) -ForegroundColor Red
}