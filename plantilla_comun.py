"""Marcado compartido por los generadores de HTML.

Antes cada plantilla repetia el pie, el icono y el menu a mano, y una correccion
habia que replicarla en varios sitios. Ahora ambos generadores importan de aqui,
que es la unica fuente que hay que editar.

La seccion BlackFriday mantiene su propia plantilla ( BlackFriday/assets/css ),
pero comparte la misma estructura de enlaces.
"""

CANAL = "https://t.me/GangasOfertasChollos"

# Juego de iconos de la pagina. Se declara aqui para que los tres generadores
# emitan lo mismo y no se desincronicen: antes cada plantilla tenia su propia
# linea y bastaba cambiar una para que divergieran.
#
# Los PNG se generan con generar_favicon.ps1 desde icono.jpg. Se piden los
# cuatro tamanos porque cada navegador elige el suyo: 16 y 32 para la pestana,
# 192 para PWA y Windows, y 180 para apple-touch-icon (iOS exige PNG ahi; antes
# BlackFriday declaraba un SVG en ese tag y no funcionaba en ningun Apple).
#
# El SVG va el ultimo como red de seguridad: los navegadores que soportan SVG lo
# prefieren sobre el PNG, y los demas cogen el de 32.
#
# `prefijo` permite resolver desde BlackFriday/, donde hace falta "../assets/".
ICONOS = """<link rel="icon" href="{p}favicon-32x32.png" sizes="32x32" type="image/png">
<link rel="icon" href="{p}favicon-16x16.png" sizes="16x16" type="image/png">
<link rel="icon" href="{p}icon-192.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="{p}apple-touch-icon.png">
<link rel="icon" href="{p}favicon.svg" type="image/svg+xml">"""

AVISO_AFILIADOS = (
    "Este sitio utiliza enlaces de afiliado de Amazon. Al comprar a través de "
    "nuestros enlaces podemos recibir una pequeña comisión sin coste adicional para ti."
)

# Icono de Telegram. Va dentro del div que contiene el <h1> de la pagina, no
# despues de <body>: en assets/icono-tg.css ese contenedor es la referencia de
# posicionamiento, asi que fuera de el el icono se situa sobre el viewport.
# `prefijo` permite usarlo desde BlackFriday/ ("../assets/...").
ICONO_TG = (
    '<a class="icono-tg" href="{canal}" target="_blank" rel="noopener" '
    'aria-label="Únete al canal de Telegram @GangasOfertasChollos" '
    'title="Canal de Telegram @GangasOfertasChollos">'
    '<img src="{prefijo}assets/icono-tg.jpg" alt="" width="180" height="160"></a>'
)

# Menu unico del sitio. Es la UNica definicion: generar_categorias.py y
# generar_seo.py la importan de aqui. Antes cada uno tenia su propia copia y
# basta cambiar una entrada para que los menus divergieran entre paginas.
NAV = [
    ("index.html", "Inicio"),
    ("general.html", "Todas"),
    ("ropa-y-calzado.html", "Ropa"),
    ("moviles-electronica.html", "Móviles"),
    ("gaming-consolas.html", "Gaming"),
    ("higiene-cuidado-personal.html", "Higiene"),
    ("juguetes-infantil.html", "Juguetes"),
    ("papeleria-oficina.html", "Papelería"),
    ("categorias.html", "Categorías"),
    # El hub de guias va despues de "Categorias": es donde se busca una
    # respuesta ("como detectar un error de precio"), no un producto, asi que
    # tiene menos peso en la navegacion de compra que las categorias.
    ("guias.html", "Guías"),
    # La seccion de campana va al final del menu: es una pagina tematica, no una
    # categoria del catalogo, y asi no compite con las entradas de arriba por el
    # espacio del nav en pantallas medianas.
    ("BlackFriday/index.html", "Black Friday"),
]


def nav_html(actual: str = "", sangria: str = "      ") -> str:
    """Menu en HTML. `actual` es la ruta de la pagina en curso: se marca con
    aria-current para que la pagina actual sea identificable de un vistazo."""
    lineas = []
    for href, label in NAV:
        marca = ' aria-current="page"' if href == actual else ""
        lineas.append(f'{sangria}<a href="{href}"{marca}>{label}</a>')
    return "\n".join(lineas)

PIE = """<footer class="pie">
  <div class="wrap">
    <nav class="footer-links" aria-label="Enlaces del sitio">
      <div class="footer-links__grupo">
        <strong>Ofertas</strong>
        <a href="general.html">Todas las ofertas</a>
        <a href="categorias.html">Todas las categorías</a>
        <a href="moviles-electronica.html">Móviles y electrónica</a>
        <a href="ropa-y-calzado.html">Ropa y calzado</a>
        <a href="gaming-consolas.html">Gaming y consolas</a>
        <a href="higiene-cuidado-personal.html">Higiene y cuidado personal</a>
        <a href="juguetes-infantil.html">Juguetes e infantil</a>
        <a href="papeleria-oficina.html">Papelería y oficina</a>
      </div>
      <div class="footer-links__grupo">
        <strong>Black Friday 2026</strong>
        <a href="BlackFriday/index.html">Guía completa</a>
        <a href="black-friday-2026.html">Ofertas en vivo</a>
        <a href="BlackFriday/fecha-black-friday-2026.html">Fecha y calendario</a>
        <a href="BlackFriday/como-aprovechar-black-friday.html">Cómo aprovecharlo</a>
        <a href="BlackFriday/faq.html">Preguntas frecuentes</a>
      </div>
      <div class="footer-links__grupo">
        <strong>Guías</strong>
        <a href="guias.html">Todas las guías</a>
        <a href="ofertas-reales-vs-descuentos-falsos.html">Oferta real o descuento falso</a>
        <a href="como-detectar-errores-de-precio-amazon.html">Cómo detectar errores de precio</a>
        <a href="amazon-warehouse-outlet-y-devoluciones.html">Amazon Warehouse y Outlet</a>
        <a href="cuando-comprar-en-amazon-espana.html">Cuándo comprar en Amazon</a>
        <a href="guia-completa-chollos-amazon.html">Guía completa de chollos</a>
        <a href="mejores-canales-telegram-ofertas.html">Canales de Telegram de ofertas</a>
        <a href="BlackFriday/metodologia.html">Cómo trabajamos</a>
        <a href="BlackFriday/sobre-nosotros.html">Sobre nosotros</a>
      </div>
      <div class="footer-links__grupo">
        <strong>Canal y legal</strong>
        <a href="https://t.me/GangasOfertasChollos" target="_blank" rel="noopener">@GangasOfertasChollos en Telegram</a>
        <a href="BlackFriday/canal-telegram-ofertas.html">Cómo funciona el canal</a>
        <a href="BlackFriday/aviso-legal.html">Aviso legal</a>
        <a href="BlackFriday/politica-privacidad.html">Política de privacidad</a>
      </div>
    </nav>
    <p>© 2026 GangasOfertas.com · Amazon España · Actualizado automáticamente desde Telegram</p>
    <p class="pie__aviso">{aviso}</p>
  </div>
</footer>""".replace("{aviso}", AVISO_AFILIADOS)
