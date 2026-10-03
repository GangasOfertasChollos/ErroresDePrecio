"""Marcado compartido por los generadores de HTML.

Antes cada plantilla repetia el pie, el icono y el menu a mano, y una correccion
habia que replicarla en varios sitios. Ahora ambos generadores importan de aqui,
que es la unica fuente que hay que editar.

La seccion BlackFriday mantiene su propia plantilla ( BlackFriday/assets/css ),
pero comparte la misma estructura de enlaces.
"""

CANAL = "https://t.me/GangasOfertasChollos"

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

# Menu unico del sitio. Es la UNica definicion: generar_categorias.py,
# generar_seo.py y anadir_navegacion.py la importan de aqui. Antes cada uno
# tenia su propia copia y basta cambiar una entrada para que los menus
# divergieran entre paginas.
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
        <a href="chollos-de-amazon.html">Chollos de Amazon</a>
        <a href="errores-de-precio-amazon.html">Errores de precio</a>
        <a href="articulos-rebajados-amazon.html">Artículos rebajados</a>
        <a href="chollos-amazon-telegram.html">Chollos en Telegram</a>
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
