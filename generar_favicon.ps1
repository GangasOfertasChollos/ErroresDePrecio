# generar_favicon.ps1
# Genera el juego de favicon PNG desde icono.jpg y enlaza los <link rel="icon">
# en todas las paginas del sitio.
#
# POR QUE HACE FALTA
# ------------------
# icono.jpg estaba sin usar: 648x576 en la raiz, 143 KB, JPG (sin canal alfa) y
# referenciado por ninguna pagina. Un JPG no vale como favicon: los formatos que
# aceptan los navegadores son PNG (con alfa) o ICO, y hace falta el juego de
# tamanos estandar porque cada uno lo pide por separado.
#
# Ademas BlackFriday/index.html (y el resto de la seccion) declaraba:
#   <link rel="apple-touch-icon" href="assets/img/logo.svg">
# iOS no acepta SVG en apple-touch-icon: necesita PNG. Ese tag no funcionaba en
# ningun dispositivo Apple del sitio. Aqui se sustituye por el PNG de 180x180.
#
# LOS TAMANOS
# -----------
#   16, 32, 48    favicon de pestana. En escritorio y Chrome se piden a 32.
#   180           apple-touch-icon (iOS lo pasa por 180x180 en el icono de inicio)
#   192           icono de instalacion de PWA y de Windows
#
# COMO EL RECORTE
# ---------------
# La original es 648x576 (proporcion 9:8, no cuadrada). Los favicon tienen que
# ser cuadrados, asi que se recorta al alto completo (576px) y se centra en
# horizontal: el personaje queda centrado y se pierden 36px por lado, que es
# fondo de mapa. El recorte va ligeramente hacia arriba para no dejar el borde
# inferior con las piernas cortadas de forma visible.
#
# USO
# ---
#   powershell -ExecutionPolicy Bypass -File generar_favicon.ps1
#   powershell -ExecutionPolicy Bypass -File generar_favicon.ps1 -SoloGenerar

param(
    [switch]$SoloGenerar
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

$Raiz   = Split-Path -Parent $MyInvocation.MyCommand.Path
$Origen = Join-Path $Raiz "icono.jpg"
$Assets = Join-Path $Raiz "assets"

# Tamano de cada salida. Los favicon de pestana salen cuadrados.
#
# No se genera el 512 aunque lo pida la especificacion de PWA: pesa 501 KB y
# ningun navegador del sitio lo descarga sin que exista un manifest de web app.
# Es un binario muerto en el repo. Si algun dia se anade el manifest, se genera
# entonces con -512.
$Salidas = @(
    @{ n = "favicon-16x16.png";     t = 16  }
    @{ n = "favicon-32x32.png";     t = 32  }
    @{ n = "favicon-48x48.png";     t = 48  }
    @{ n = "apple-touch-icon.png";  t = 180 }
    @{ n = "icon-192.png";          t = 192 }
)

# Recorte cuadrado, calculado a partir del tamano real de la original para que
# el script siga funcionando si el JPG se cambia de dimensiones.
function Get-Crop($img) {
    $alto    = $img.Height
    $ancho   = [Math]::Min($img.Width, $alto)
    $centroX = [int]($img.Width / 2)
    # Un poco hacia arriba: el personaje llena mas la parte alta que la baja, y
    # centrado exacto deja las piernas cortadas por el borde inferior.
    $centroY = [int]($alto * 0.46)
    $top     = [Math]::Max(0, $centroY - [int]($ancho / 2))
    New-Object System.Drawing.Rectangle(
        ($centroX - [int]($ancho / 2)), $top, $ancho, $ancho
    )
}

# ── Generacion ───────────────────────────────────────────────────────────────
if (-not (Test-Path $Origen)) {
    Write-Host "ERROR: no existe $Origen" -ForegroundColor Red
    exit 1
}

$img  = [System.Drawing.Image]::FromFile($Origen)
$crop = Get-Crop $img
Write-Host "origen $($img.Width)x$($img.Height)  ->  recorte $($crop.Width)x$($crop.Height) en ($($crop.X),$($crop.Y))"

function Guardar($cuadro, $tam, $ruta) {
    $bmp = New-Object System.Drawing.Bitmap($tam, $tam)
    $bmp.SetResolution(96, 96)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    # Sin esto el reescalado sale borroso: por defecto .NET usa
    # NearestNeighbor para destinos pequenos y las formas salen dentadas.
    $g.InterpolationMode  = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.SmoothingMode      = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $g.PixelOffsetMode    = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
    $g.Clear([System.Drawing.Color]::Transparent)

    $dest = New-Object System.Drawing.Rectangle(0, 0, $tam, $tam)
    $g.DrawImage($img, $dest, $crop.X, $crop.Y, $crop.Width, $crop.Height,
                 [System.Drawing.GraphicsUnit]::Pixel)
    $g.Dispose()

    $bmp.Save($ruta, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
    $kb = [Math]::Round((Get-Item $ruta).Length / 1KB, 1)
    Write-Host ("  {0,-24} {1,4}x{1,-4} {2,6} KB" -f (Split-Path $ruta -Leaf), $tam, $kb)
}

Write-Host ""
foreach ($s in $Salidas) {
    Guardar $img $s.t (Join-Path $Assets $s.n)
}
$img.Dispose()

if ($SoloGenerar) {
    Write-Host "`nSolo generacion (-SoloGenerar). HTML sin tocar."
    exit 0
}

# ── Enlaces en el HTML ───────────────────────────────────────────────────────
# Los PNG viven SIEMPRE en assets/ de la raiz del repositorio. Las paginas de la
# raiz los alcanzan con "assets/..." y las de BlackFriday, que estan un nivel mas
# abajo, con "../assets/...". El prefijo se calcula desde la PROFUNDIDAD de la
# pagina dentro del repo, no desde su carpeta: por eso se cuenta con split
# sobre la ruta relativa completa y no sobre la carpeta del fichero.
Write-Host "`nEnlazando los links de icono en el HTML:"

$Paginas = @()
$Paginas += Get-ChildItem -Path $Raiz -Filter *.html -File
$Paginas += Get-ChildItem -Path (Join-Path $Raiz "BlackFriday") -Filter *.html -File

# googleXXXX.html es el fichero de verificacion de Search Console: no es una
# pagina, es una linea de texto sin <head> ni <body>. No lleva favicon y no debe
# hacerlo.
$Paginas = $Paginas | Where-Object { $_.Name -notmatch '^google[0-9a-f]+\.html$' }

# Se declara el SVG actual como fallback: los navegadores que soportan SVG lo
# prefieren, y los que no toman el PNG de 32.
$Lineas = @(
    '<link rel="icon" href="{p}favicon-32x32.png" sizes="32x32" type="image/png">'
    '<link rel="icon" href="{p}favicon-16x16.png" sizes="16x16" type="image/png">'
    '<link rel="icon" href="{p}icon-192.png" sizes="192x192" type="image/png">'
    '<link rel="apple-touch-icon" href="{p}apple-touch-icon.png">'
    '<link rel="icon" href="{p}favicon.svg" type="image/svg+xml">'
)
$Bloque = ($Lineas -join "`n") + "`n"

$cambiadas = 0
foreach ($pagina in $Paginas) {
    # Ruta relativa al repo, con separador "/" fijo para que el split de la
    # profundidad no dependa de si Windows usa "\" o "/".
    $rel = $pagina.FullName.Substring($Raiz.Length + 1).Replace('\', '/')
    # Ejemplos: "index.html" -> 0 niveles, "BlackFriday/index.html" -> 1 nivel.
    $profundidad = $rel.Split('/').Length - 1
    $prefijo = ""
    for ($i = 0; $i -lt $profundidad; $i++) { $prefijo += "../" }
    Write-Verbose "  $($rel): prefijo '$prefijo'"

    $c = [System.IO.File]::ReadAllText($pagina.FullName)
    $antes = $c

    # 1. Fuera los links de icono sueltos que hubiera.
    $c = [regex]::Replace($c, '(?m)^\s*<link rel="(icon|apple-touch-icon)"[^>]*>\r?\n?', '')

    # 2. Insertar el bloque nuevo tras la etiqueta stylesheet de icono-tg.css,
    #    que todas las paginas traen y siempre esta en <head>.
    #
    #    Ojo con el ancla: en BlackFriday los dos <link rel="stylesheet"> estan
    #    en la MISMA linea, asi que un ancla que exija el salto de linea al final
    #    (^...>\r?\n) no encuentra nada y la pagina se queda sin favicon. Por eso
    #    seCaptura la etiqueta suelta y se inserta despues, sin exigir el \n.
    # OJO con el nombre: PowerShell no distingue mayusculas en los nombres de
    # variable, asi que escribir $bloque aqui MISMARIA la plantilla $Bloque y la
    # sustituiria. En la primera pagina (una de la raiz, prefijo vacio) el
    # placeholder {p} desaparecia de la plantilla y todas las siguientes
    # heredaban "assets/" sin el "../" de BlackFriday.
    $lineasPagina = $Bloque.Replace("{p}", $prefijo + "assets/")
    $reemplazo = 0

    if ($c -match '<link rel="stylesheet" href="[^\"]*icono-tg\.css"[^>]*>') {
        $c = [regex]::Replace($c, '(<link rel="stylesheet" href="[^\"]*icono-tg\.css"[^>]*>)',
                             { param($m) $m.Groups[1].Value + "`n" + $lineasPagina }, 1)
        $reemplazo = 1
    }
    elseif ($c -match '<link rel="stylesheet"[^>]*>') {
        $c = [regex]::Replace($c, '(<link rel="stylesheet"[^>]*>)',
                             { param($m) $m.Groups[1].Value + "`n" + $lineasPagina }, 1)
        $reemplazo = 1
    }

    if ($reemplazo -eq 0) {
        Write-Host "  AVISO  $($pagina.Name): no encuentro donde insertar" -ForegroundColor Yellow
        continue
    }

    if ($c -ne $antes) {
        [System.IO.File]::WriteAllText($pagina.FullName, $c, (New-Object System.Text.UTF8Encoding $false))
        $cambiadas++
    }
}
Write-Host "  $cambiadas paginas actualizadas"
Write-Host ""
Write-Host "Hecho. Los PNG estan en assets/ y las paginas ya los referencian."