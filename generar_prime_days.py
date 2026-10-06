"""Genera la seccion Amazon Prime Days de GangasOfertas.com.

El contenido vive aqui y las paginas se generan, no se parchean a mano: editar
un HTML suelto perderia los cambios en la siguiente ejecucion (mismo criterio
que generar_categorias.py y generar_seo.py; ver README.md).

── DATOS VERIFICADOS Y DE DONDE SALEN ───────────────────────────────────────
Amazon confirmo por escrito las fechas de la campana de octubre de 2026. La
fuente primaria es su propio despacho, en la version en espanol:

    "Prime Big Deal Days regresa del 6 al 7 de octubre: Esto es lo que puedes
     esperar" — aboutamazon.com/news/retail/amazon-prime-big-deals-day-2026-
     cuando-octubre-6-7

De ahi salen todos los datos de la campana de octubre: los 6 y 7 de octubre,
las 48 horas, las mas de 35 categorias y los 22 paises participantes (Espana
entre ellos). Para la edicion de verano se usa el anuncio equivalente, que
confirma el 23 al 26 de junio de 2026.

Esto corrige un borrador anterior de esta seccion que afirmaba que Amazon no
habia anunciado la fecha. Publicar eso en una pagina de ofertas es el peor
error posible: manda a la gente a comprar un dia que no hay descuento, la
gente no vuelve y el topical se pierde. La regla que se mantiene no es
"no publicar fechas", que era una reaccion a un dato que ya no existe, sino
"publicar solo fechas con fuente y decir siempre de donde sale".

── LOS TRES NOMBRES, Y POR QUE IMPORTAN ─────────────────────────────────────
El mismo evento aparece con tres nombres y esa confusion es la razon por la
que hay tanta pagina contradictoria en internet:

  - "Amazon Prime Days"  -> lo que la gente escribe en el buscador.
  - "Fiesta de Ofertas Prime" -> el nombre oficial que usa la prensa
    espanola (Xataka, Hola, La Vanguardia, ELLE).
  - "Prime Big Deal Days" -> el nombre oficial de Amazon en ingles, el que
    aparece en aboutamazon.com.

Cada medio usa uno solo. Aqui se usan los tres, de forma natural y sin
inventar ninguno, que es la cobertura de long tail mas obvia y gratis que
hay en este tema.

── COMPETIDORES: QUE HACEN BIEN Y DONDE ESTAN DEBILES ───────────────────────
El analisis completo esta en PrimeDays/docs/SEO-STRATEGY.md. El resumen que
importa para escribir el contenido:

  - Xataka, Hola, ELLE, La Vanguardia y AS.com tienen la fecha correcta
    (6-7 de octubre) y buena autoridad de dominio, pero son piezas de
    noticias: se escriben una vez y no se actualizan. En una campana de 48
    horas, un articulo del dia 6 por la tarde ya no dice nada valido el dia 7.
  - AS.com Showroom y las guias de ofertas publican listas del tipo "las 51
    mejores ofertas, hasta un 83%". Son estaticas: se quedan vacias en horas
    y no distinguen un descuento real de uno inflado sobre un precio ya
    subido.
  - idealo tiene el mejor producto del sector (alertas de precio), pero su
    pagina se contradice: en el mismo texto dice que las fechas estan
    confirmadas para el 6 y 7 de octubre y tambien que "a falta de
    confirmacion oficial" se prevee para octubre.
  - Amazon oficial da las fechas y el numero de categorias, pero el texto
    esta escrito para el mercado estadounidense: precios en dolares, hora del
    Pacifico y nada de si un descuento es real o no.
  - Ninguno envia a un canal de Telegram donde se pueda ver el historico
    publico y comprobar que la oferta existio de verdad.

El hueco, por tanto, no es mas informacion: es informacion en vivo, con el
descuento verificado y con un sitio donde mirar cuando la oferta desaparece.

Cuando Amazon cambie el calendario, el cambio se concentra en
FECHA_INICIO_2026, FECHA_FIN_2026 y en la constante PRUEBA_ENVIO.
"""
from pathlib import Path

from plantilla_prime_days import (
    ACTUALIZADO, BASE, CANAL, CANAL_HISTORIAL, SECCION, bloque_jsonld,
    faq_html, render, schema_article, schema_breadcrumb, schema_faq, tg, tg_attr,
)

RAIZ = Path(__file__).resolve().parent
DESTINO = RAIZ / "PrimeDays"
DESTINO.mkdir(exist_ok=True)

PUBLICADO = "2026-10-06"
MODIFICADO = "2026-10-06"

# ─────────────────────────────────────────────────────────────────────────────
#  DATOS CONFIRMADOS DE LA CAMPAÑA DE OCTUBRE DE 2026
# ─────────────────────────────────────────────────────────────────────────────

FECHA_INICIO_2026 = "martes 6 de octubre de 2026"
FECHA_FIN_2026 = "miércoles 7 de octubre de 2026"
RANGO_2026 = "6 y 7 de octubre de 2026"
HORA_FIN = "23:59"
DURACION = "48 horas"

# Fuente primaria. Se cita en las paginas de fechas y en la de que es, para que
# cualquiera pueda comprobar el dato sin fiarse de este sitio.
FUENTE_OFICIAL = (
    "https://www.aboutamazon.com/news/retail/"
    "amazon-prime-big-deals-day-2026-cuando-octubre-6-7"
)

# Edicion de verano. Fuente: aboutamazon.com/news/retail/amazon-prime-day-2026-fecha
PRIME_DAY_2026 = "23 al 26 de junio de 2026"

# Precio de Prime en España. Aparece en la prensa y sirve para que el lector
# sepa lo que cuesta ser miembro antes de plantearse la compra.
PRIME_MES = "4,99 € al mes"
PRIME_ANO = "49,90 € al año"
PRIME_PRUEBA = "30 días gratis"

# Categorias que Amazon destaco para la campana de octubre. El eje de la
# edicion segun el anuncio propio son los preparativos de Halloween y los
# regalos de Navidad adelantados, no solo el descuento tecnico.
CATEGORIAS_ANUNCIADAS = [
    ("Tecnología", "Portátiles, auriculares, televisiones, cámaras y relojes"),
    ("Hogar y cocina", "Sartenes, ollas, cuchillos, pequeños electrodomésticos"),
    ("Moda", "Ropa de temporada, calzado y bolsos"),
    ("Belleza", "Perfumes, cuidado facial y electricos de belleza"),
    ("Juguetes", "Juguetes por rango de edad, juegos de mesa y regalo"),
    ("Casa y decoracion", "Decoracion de temporada, manteleria y textiles"),
    ("Supermercado", "Alimentos de temporada con entrega el mismo dia"),
]

# Historial de ediciones. La columna de octubre es la de la campana de otoño
# (Prime Early Access Sale desde 2022, Prime Big Deal Days desde 2023).
HISTORICO = [
    ("2015", "15 de julio", "—",
     "La primera edicion: un solo dia, para el 20 aniversario de Amazon. "
     "Amazon dijo que habria mas ofertas que en Black Friday."),
    ("2016", "12 y 13 de julio", "—",
     "Amazon comunico un aumento del 60% de pedidos en todo el mundo."),
    ("2017", "11 y 12 de julio", "—",
     "Ultima edicion de verano de dos dias antes del giro de octubre."),
    ("2018", "16 y 17 de julio", "—",
     "Giro de formato: concierto previo con Ariana Grande en Twitch y "
     "Amazon Video. Empezaron las huelgas de trabajadores."),
    ("2019", "15 y 16 de julio", "—",
     "Concierto previo con Taylor Swift, Dua Lipa, Becky G y SZA, "
     "exclusivo para miembros Prime."),
    ("2020", "13 y 14 de octubre", "13 y 14 de octubre",
     "Aplazada por el COVID-19. Paso de julio a octubre y ese cambio acabo "
     "siendo el formato definitivo."),
    ("2021", "12 y 13 de julio", "—",
     "Volvio a julio tras la pandemia, en formato de dos dias."),
    ("2022", "12 y 13 de julio", "12 y 13 de octubre",
     "Nace la segunda campana del ano, con el nombre Prime Early Access Sale."),
    ("2023", "11 y 12 de julio", "10 y 11 de octubre",
     "La de octubre se rebautiza Prime Big Deal Days. Desde aqui hay dos "
     "eventos al ano en lugar de uno."),
    ("2024", "16 y 17 de julio", "8 y 9 de octubre",
     "La edicion de verano incluyo a Espana entre los 22 paises participantes."),
    ("2025", "8, 9, 10 y 11 de julio", "7 y 8 de octubre",
     "Cuatro dias de verano en lugar de dos."),
    ("2026", "23 al 26 de junio", "6 y 7 de octubre",
     "La de verano se hizo en junio, fuera del hueco habitual de julio. La de "
     "octubre es la que esta en marcha al escribir esta guia."),
]

# Como se ha llamado cada campana. Ver la nota del docstring.
NOMBRES = [
    ("Amazon Prime Days", "el que se usa hoy",
     "El nombre con el que la gente busca y con el que Amazon se refiere al "
     "conjunto de campanas en su comunicacion actual. Da nombre a esta seccion."),
    ("Fiesta de Ofertas Prime", "nombre oficial en Espana",
     "Como lo llama la prensa espanola: Xataka, Hola, La Vanguardia y ELLE lo "
     "usan en sus titulos. Quien lea esas paginas va a buscar esta seccion."),
    ("Prime Big Deal Days", "nombre oficial de Amazon",
     "El nombre de la campana de octubre desde 2023, el que aparece en "
     "aboutamazon.com. En espanol se ha traducido como dias de ofertas."),
    ("Prime Day", "2015-2019",
     "El nombre original, el de verano. Sigue apareciendo en la prensa de "
     "forma informal y en la direccion amazon.es/primeday."),
    ("Prime Early Access Sale", "2022",
     "El nombre con el que nacio la campana de octubre. Solo duro un ano."),
]

# ─────────────────────────────────────────────────────────────────────────────
#  BLOQUES DE MARCADO REUTILIZABLES
# ─────────────────────────────────────────────────────────────────────────────

CTA_CANAL = f"""    <section class="section section--alt section--tight">
      <div class="wrap">
        <div class="cta-band">
          <span class="card__icon" aria-hidden="true">📲</span>
          <h2>Cada ganga de estos Prime Days, en cuanto aparece</h2>
          <p>
            Publicamos cada oportunidad de Amazon Espana en
            <strong>@GangasOfertasChollos</strong> en cuanto la vemos: producto,
            precio anterior, precio actual, descuento y enlace directo. Es la
            unica forma de coger una oferta de 48 horas sin estar
            refrescando la pagina de Amazon cada diez minutos.
          </p>
          <div class="btn-row">
            {tg_attr(clase="btn btn--tg btn--lg", texto="Unirme gratis al canal")}
            <a class="btn btn--ghost btn--lg" href="{CANAL_HISTORIAL}" target="_blank" rel="sponsored nofollow noopener">Ver el historial</a>
          </div>
          <p class="cta-band__note">Sin registro. Sin spam. Puedes silenciarlo cuando quieras.</p>
        </div>
      </div>
    </section>"""


def cuenta_atras() -> str:
    """Cuenta atras hasta el fin de la campana.

    Los valores estaticos del HTML son la referencia si el visitante no tiene
    JS: nunca se ve un hueco ni un NaN (ver assets/js/main.js).
    """
    return """  <section class="section section--tight">
    <div class="wrap center">
      <p class="eyebrow"><span aria-hidden="true">⏳</span> Tiempo restante</p>
      <h2 class="mt-0">La campana termina el 7 de octubre a las 23:59</h2>
      <div class="countdown mt-2" id="countdown">
        <div class="countdown__cell">
          <span class="countdown__num" data-unit="days">01</span>
          <span class="countdown__label">día</span>
        </div>
        <div class="countdown__cell">
          <span class="countdown__num" data-unit="hours">00</span>
          <span class="countdown__label">horas</span>
        </div>
        <div class="countdown__cell">
          <span class="countdown__num" data-unit="mins">00</span>
          <span class="countdown__label">minutos</span>
        </div>
        <div class="countdown__cell">
          <span class="countdown__num" data-unit="secs">00</span>
          <span class="countdown__label">segundos</span>
        </div>
      </div>
      <p class="muted small mt-2" data-countdown-label>
        Cuenta atrás en hora peninsular española (Madrid). Al terminar, Amazon
        retira la mayoría de los precios.
      </p>
    </div>
  </section>"""


NOTA_PRECIOS = """      <div class="note note--warn">
        <span class="note__title">Sobre los precios que publicamos</span>
        <p class="mb-0">
          Cada precio es el que se detecto en el momento de publicar la oferta, y Amazon lo cambia
          cuando quiere. Antes de comprar, abre siempre el enlace y comprueba el precio final, la
          fecha de envio y las condiciones. No podemos garantizar que una oferta siga vigente, y
          un error de precio puede durar solo minutos.
        </p>
      </div>"""

NOTA_CATALOGO = """      <div class="note note--info">
        <span class="note__title">Las ofertas de esta web son las mismas del canal</span>
        <p class="mb-0">
          Cada producto anunciado en el canal se publica automaticamente en el catalogo de la web,
          con su precio y su enlace. Si prefieres mirarlo todo de una sentada en lugar de recibir
          avisos, entra en
          <a href="https://gangasofertas.com/general.html">todas las ofertas</a>
          o en la seccion que te interese: electronica, gaming, ropa, higiene, juguetes o papeleria.
        </p>
      </div>"""

NOTA_FUENTE = """      <div class="note note--info">
        <span class="note__title">De donde sale la fecha</span>
        <p class="mb-0">
          Amazon confirmo por escrito que la campana va del 6 al 7 de octubre de 2026, con 48 horas
          de ofertas en mas de 35 categorias. La fuente es su propio despacho de noticias, en
          espanol: <a href="https://www.aboutamazon.com/news/retail/amazon-prime-big-deals-day-2026-cuando-octubre-6-7"
          target="_blank" rel="noopener">Prime Big Deal Days regresa del 6 al 7 de octubre</a>.
          No hay fecha de este sitio que no venga con ese respaldo.
        </p>
      </div>"""


def relacionados(entradas: list) -> str:
    """Rejilla de enlaces internos. entradas = [(href, titulo, texto, cta)]."""
    tarjetas = "\n".join(
        f"""        <a class="related__card" href="{href}">
          <strong>{titulo}</strong>
          <span>{texto}</span>
          <span class="arrow">{cta} →</span>
        </a>"""
        for href, titulo, texto, cta in entradas
    )
    return f"""    <section class="section section--alt section--tight">
      <div class="wrap">
        <h2>Sigue leyendo</h2>
        <div class="related">
{tarjetas}
        </div>
      </div>
    </section>"""


def encabezado(eyebrow: str, h1: str, lead: str, minutos: str) -> str:
    """Cabecera de pagina. Solo para paginas sin hero: la portada lleva su
    propio h1 y las dos juntasarian dos H1 en el mismo documento."""
    return f"""  <section class="page-head wrap">
    <p class="eyebrow"><span aria-hidden="true">{eyebrow[0]}</span> {eyebrow[1]}</p>
    <h1>{h1}</h1>
    <p class="page-head__lead">{lead}</p>
    <div class="page-head__meta">
        <span>📝 Actualizado el {ACTUALIZADO}</span>
        <span>⏱️ {minutos}</span>
        <span>🌍 España</span>
    </div>
  </section>"""


def tabla(caption: str, cabeceras: list, filas: list, primera_col_titulo: bool = True,
          ancho_completo: bool = False) -> str:
    """Tabla con caption y scope, que es lo que hace falta para que el buscador la
    pueda mostrar como resultado enriquecido.

    `ancho_completo` indenta para un contenedor `.wrap` suelto. Por defecto la
    tabla va dentro de `.prose`, que mide 74ch: con cuatro o cinco columnas eso
    parte cada celda en tres o cuatro palabras y la tabla deja de ser legible.
    Las tablas de datos anchos van fuera de la columna de texto.
    """
    sangria = "        " if ancho_completo else "      "
    th = "\n".join(
        f'{sangria}      <th scope="col">{c}</th>' for c in cabeceras
    )
    trs = []
    for fila in filas:
        celdas = []
        for i, c in enumerate(fila):
            scope = ' scope="row"' if (i == 0 and primera_col_titulo) else ""
            celdas.append(f'{sangria}      <td{scope}>{c}</td>')
        trs.append(f'{sangria}    <tr>\n' + "\n".join(celdas) + f'\n{sangria}    </tr>')
    cuerpo = "\n".join(trs)
    sangria = "        " if ancho_completo else "      "
    return f"""{sangria}<div class="table-scroll">
{sangria}  <table class="cmp">
{sangria}    <caption>{caption}</caption>
{sangria}    <thead>
{sangria}        <tr>
{th}
{sangria}        </tr>
{sangria}    </thead>
{sangria}    <tbody>
{cuerpo}
{sangria}    </tbody>
{sangria}  </table>
{sangria}</div>"""


RELACIONADOS_BASE = [
    ("index.html", "Guía completa de Prime Days",
     "Qué son, cómo funcionan y dónde ver cada oferta en vivo.", "Ir a la guía"),
    ("fechas-amazon-prime-days.html", "Fechas y calendario",
     "Las 48 horas confirmadas y el historial real de doce ediciones.", "Ver fechas"),
    ("ofertas-prime-days-2026.html", "Ofertas por categoría",
     "Dónde suelen aparecer los descuentos más grandes.", "Ver ofertas"),
    ("descuentos-reales-o-falsos.html", "Descuentos reales o falsos",
     "Cómo saber si un 80% de descuento existe de verdad.", "Ver el método"),
    ("como-aprovechar-prime-days.html", "Cómo aprovecharlo",
     "El método completo en siete pasos, sin gastar de más.", "Leer el método"),
    ("canal-telegram-ofertas.html", "El canal de Telegram",
     "Por qué un canal es la forma más rápida de enterarse.", "Ver el canal"),
    ("faq.html", "Preguntas frecuentes",
     "Las veinte dudas que más se repiten sobre esta campaña.", "Ver la FAQ"),
]


def schema_howto(nombre: str, desc: str, pasos: list) -> dict:
    """HowTo con los mismos pasos que aparecen en el <ol class=steps>."""
    return {
        "@type": "HowTo",
        "name": nombre,
        "description": desc,
        "inLanguage": "es-ES",
        "step": [
            {"@type": "HowToStep", "position": i + 1,
             "name": t[0], "text": t[1]}
            for i, t in enumerate(pasos)
        ],
    }


def schema_evento(nombre: str, inicio: str, fin: str, desc: str) -> dict:
    """Event con fechas absolutas en ISO, que es lo que permite a Google
    mostrar el rango de fechas en la ficha del resultado."""
    return {
        "@type": "Event",
        "name": nombre,
        "description": desc,
        "startDate": inicio,
        "endDate": fin,
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode",
        "inLanguage": "es-ES",
        "organizer": {
            "@type": "Organization",
            "name": "Amazon",
            "url": "https://www.aboutamazon.com/",
        },
        "url": FUENTE_OFICIAL,
    }


def schema_itemlist(nombre: str, elementos: list) -> dict:
    return {
        "@type": "ItemList",
        "name": nombre,
        "numberOfItems": len(elementos),
        "itemListOrder": "https://schema.org/ItemListOrderAscending",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": nombre_item}
            for i, nombre_item in enumerate(elementos)
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
#  1. PORTADA / PILLAR
# ─────────────────────────────────────────────────────────────────────────────

FAQ_INDEX = [
    ("¿Cuándo es el Amazon Prime Days 2026 en España?",
     "El 6 y el 7 de octubre de 2026, martes y miércoles, durante 48 horas seguidas. "
     "Amazon lo confirmó por escrito: la campaña se llama Prime Big Deal Days y en la "
     "prensa española aparece como Fiesta de Ofertas Prime."),
    ("¿Empieza a las 00:00 del martes 6?",
     "En España la ventana comercial va del martes 6 al miércoles 7 de octubre. El "
     "anuncio de Amazon da la hora de arranque en su huso del Pacífico, así que "
     "según desde dónde mires aparecerá desplazada. Lo que no cambia es que la "
     "campaña dura 48 horas y termina la noche del miércoles 7."),
    ("¿Las ofertas son solo para miembros Prime?",
     "Las más exclusivas sí. Amazon reserva buena parte de los descuentos de la campaña a "
     "clientes Prime, aunque suelta algunas ofertas al resto de la audiencia. Prime cuesta "
     "4,99 € al mes o 49,90 € al año en España, con 30 días gratis si cumples los "
     "requisitos."),
    ("¿Amazon Prime Days es lo mismo que el Black Friday?",
     "No. Son campañas distintas y de retailers distintos: el Prime Days es de Amazon y el "
     "Black Friday es la fecha en la que liquida todo el comercio. Amazon además tiene su "
     "propia campaña en España a finales de noviembre."),
    ("¿Amazon Prime Days es lo mismo que el Prime Day de verano?",
     "No, pero son parientes. El Prime Day es la edición de verano y el Prime Big Deal "
     "Days la de otoño. Desde 2023 hay dos al año, y por eso la gente las mezcla sin "
     "darse cuenta."),
    ("¿Cuánto se puede ahorrar?",
     "Amazon anuncia rebajas en más de 35 categorías. En la práctica, los importes grandes "
     "están en tecnología y los porcentajes más altos en productos que ya eran caros. Y "
     "ojo: un porcentaje grande no significa ahorrar más, porque el precio de referencia "
     "puede estar inflado."),
    ("¿Y si no soy miembro Prime, me pierdo todo?",
     "No todo. Perderás las ofertas más exclusivas y la entrega rápida, que es la diferencia "
     "de verdad. Pero buena parte de las gangas se anuncian en abierto."),
    ("¿Los descuentos duran más de 48 horas?",
     "No. Es justo lo que distingue esta campaña: cuando acaba la ventana, los precios "
     "vuelven a su valor normal en la mayoría de los casos. Salvo los errores de precio, "
     "que tienen su propio ritmo."),
]

PASOS_METODO = [
    ("Marca las fechas y no improvises",
     "El 6 y el 7 de octubre, en el calendario. Con dos días de ventana tienes margen, y "
     "ese margen es justo lo que puedes usar para comparar en lugar de comprar por "
     "impulso."),
    ("Haz la lista de la compra antes, no durante",
     "Con la lista hecha, una ganga es una decisión. Sin ella, una ganga es una compra que "
     "no habías planeado y que después se justifica sola."),
    ("Mira el precio de siempre, no solo el de oferta",
     "Un 50% sobre un precio que estaba inflado es un 15% de verdad. Es el paso que más "
     "dinero deja y el que casi nadie hace."),
    ("Entra en la oferta desde el canal",
     "El enlace va directo a la ficha y el precio te cuesta lo mismo. No compras peor: "
     "compras con la misma información que el resto."),
    ("Comprueba el precio final en el carrito, no en la ficha",
     "Amazon corrige muchos de sus errores en el carrito. Y es en el carrito donde se ve "
     "el precio de envío, que en Prime es gratis a partir de 25 € en la mayoría de los "
     "pedidos."),
    ("No aplaces lo que no quieras",
     "Tienes 14 días naturales de desistimiento desde que recibes el producto. Pero no "
     "los gastes en algo que no estaba en tu lista."),
    ("Mira también el día después",
     "Cuando la ventana se cierra, el stock se repone a precio bajo en muchas categorías. "
     "La segunda oportunidad existe y casi nadie la usa."),
]

PAGINA_INDEX = {
    "slug": "index.html",
    "miga": "Guía completa",
    "titulo": "Amazon Prime Days 2026: 6 y 7 de octubre en España",
    "desc": ("Amazon Prime Days 2026 en España: 48 horas de ofertas los días 6 y 7 de "
             "octubre, qué categorías bajan de verdad y cómo enterarte antes de que se "
             "agoten."),
    "alt_img": "Amazon Prime Days 2026: 6 y 7 de octubre en España",
    "faq": FAQ_INDEX,
    "cuerpo": f"""  <section class="hero">
    <div class="wrap hero__inner">
      <p class="eyebrow">
        <span class="badge badge--red" style="margin-right:4px">En marcha</span>
        Termina mañana a las 23:59
      </p>
      <h1>Amazon Prime Days 2026: 48 horas de ofertas que hoy empiezan a acabarse</h1>
      <p class="hero__lead">
        Amazon lo ha confirmado: la campaña va del martes 6 al miércoles 7 de octubre,
        en más de 35 categorías y para miembros Prime. La ventana es de dos días
        completos, así que no tienes prisa, pero sí tienes que enterarte a tiempo.
        Te explicamos qué baja de verdad, dónde mirar y cómo saber si un descuento es
        real o solo un número grande.
      </p>
      <div class="btn-row">
        {tg_attr(clase="btn btn--tg btn--lg", texto="Unirme gratis y enterarme de todo")}
        <a class="btn btn--ghost btn--lg" href="ofertas-prime-days-2026.html">Ver ofertas por categoría</a>
      </div>
    </div>
  </section>

{cuenta_atras()}

  <section class="section section--tight">
    <div class="wrap">
      <div class="keyfacts">
        <h2>Amazon Prime Days 2026 en cinco datos</h2>
        <dl>
          <dt>Qué es</dt>
          <dd>Una campaña de descuentos de Amazon, con las mejores ofertas reservadas a miembros Prime</dd>
          <dt>Cuándo</dt>
          <dd><strong>{RANGO_2026}</strong>, martes y miércoles, {DURACION} seguidas</dd>
          <dt>Dónde mirar</dt>
          <dd>En el catálogo de esta web y en el canal de Telegram, que publica cada oferta en cuanto la ve</dd>
          <dt>Para quién</dt>
          <dd>Principalmente miembros Prime, que en España pagan {PRIME_MES} o {PRIME_ANO} ({PRIME_PRUEBA})</dd>
          <dt>Fuente de la fecha</dt>
          <dd>Anuncio oficial de Amazon, en español, con el rango de fechas y las más de 35 categorías</dd>
        </dl>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap prose">
      <h2>No es un día: son dos campañas al año</h2>
      <p>
        Es el error más común al buscar información sobre esto, y la razón por la que hay
        tanta página contradictoria en internet. <strong>Amazon Prime Days no es un día:</strong>
        desde 2023 Amazon organiza dos campañas propias al año, independientes del Black Friday.
      </p>
      <ul>
        <li>
          <strong>La de verano.</strong> La más antigua y la más conocida. Empezó en julio de
          2015 como un evento de un solo día para celebrar el 20 aniversario de Amazon, y ha ido
          alargándose: un día, dos días, dos días, dos días y en 2025 cuatro. En 2026 se
          adelantó al último fin de semana de junio, del {PRIME_DAY_2026}.
        </li>
        <li>
          <strong>La de otoño.</strong> Es la que está en marcha. Nació en 2022 con el nombre
          <em>Prime Early Access Sale</em> y en 2023 pasó a llamarse <em>Prime Big Deal
          Days</em>. Es la que se parece más al Black Friday en espíritu, y la que en España se
          vive casi igual que este.
        </li>
      </ul>
      <p>
        Y hay un detalle del formato que importa más de lo que parece: <strong>la ventana
        dura días, no horas</strong>. Eso da una segunda oportunidad real. Si el martes se te
        escapó lo que querías, el miércoles sigue ahí, y la reposición de stock del día
        posterior suele traer precios bajos. El
        <a href="fechas-amazon-prime-days.html">calendario completo con el historial real</a>
        resuelve el resto de las dudas de calendario.
      </p>

      {NOTA_FUENTE}

      <h2>Los tres nombres del mismo evento</h2>
      <p>
        El mismo evento aparece con tres denominaciones distintas, y esa confusión es la razón
        de que la mitad de las páginas que hay en internet no cuadren entre sí. Cada medio usa
        uno solo; aquí van los tres, sin inventar ninguno:
      </p>
      {tabla(
          "Los nombres de la campaña de octubre de 2026 y quién usa cada uno",
          ["Nombre", "Quién lo usa", "Qué es"],
          [[n, q, d] for n, q, d in NOMBRES],
      )}
      <p class="mt-2">
        Si llegas aquí buscando Fiesta de Ofertas Prime o Prime Big Deal Days, estás en la
        página correcta: son sinónimos de lo mismo que aquí llamamos Amazon Prime Days.
      </p>

      <h2>Qué se encuentra en cada Prime Days</h2>
      <p>
        El catálogo entero pasa por revisión de precio, pero no todo lo que baja lo hace de
        forma que merezca la pena. Hay tres cosas que conviene distinguir, y confundirlas es
        la forma más fácil de gastar dinero de más:
      </p>
      <ol>
        <li>
          <strong>Descuentos reales sobre el precio habitual.</strong> Lo normal: un producto
          que costaba 200 euros y se queda en 120. El ahorro es real aunque no sea
          espectacular, y es la categoría más numerosa.
        </li>
        <li>
          <strong>Descuentos inflados sobre un precio que ya estaba subido.</strong> Es el
          caso más frecuente y el que más engaña, porque el número del descuento es enorme y
          el ahorro real es pequeño. Está desarrollado, con el método de comprobación, en
          <a href="descuentos-reales-o-falsos.html">descuentos reales o falsos</a>.
        </li>
        <li>
          <strong>Errores de precio.</strong> Productos que se muestran a una fracción de su
          valor y que duran minutos u horas. Es el único escenario donde se llega a ver el
          70% o el 80% de descuento, y también el que más veces se acaba en decepción: si pasas
          la pantalla a tiempo, se repite.
        </li>
      </ol>
      <p>
        La comparación con el Black Friday es inevitable porque las fechas caen cerca, pero la
        diferencia práctica es clara: <strong>aquí tienes dos días enteros y allí la oferta
        buena dura cuatro o cinco horas</strong>. Es más fácil tener una segunda oportunidad el
        7 de octubre que el 27 de noviembre.
      </p>

      <h2>Las categorías donde más se ahorta</h2>
      <p>
        El descuento más grande no suele estar donde la gente lo espera. La electrónica y el
        gaming concentran los importes absolutos más altos, pero las rebajas más sinceras
        están en categorías donde el producto ya era caro de serie.
      </p>
      <p class="mb-0">
        El detalle de cada categoría, con qué mirar en concreto en cada una, está en
        <a href="ofertas-prime-days-2026.html">ofertas por categoría</a>.
      </p>
    </div>
  </section>

  <section class="section section--tight">
    <div class="wrap">
{tabla(
          "Qué categoría mirar primero en la Fiesta de Ofertas Prime de octubre de 2026",
          ["Categoría", "Qué baja en ella"],
          [[c, q] for c, q in CATEGORIAS_ANUNCIADAS],
          ancho_completo=True,
      )}
    </div>
  </section>

  <section class="section">
    <div class="wrap prose">

      <h2>Por qué un canal de Telegram y no una newsletter</h2>
      <p>
        Porque durante una campaña de este tipo el problema no es saber <em>qué</em> está
        rebajado, sino <em>cuándo</em>. Un newsletter llega una vez al día; en una ventana de
        48 horas con stock limitado, una vez al día llega tarde. Y una tabla de las 50 mejores
        ofertas escrita el lunes por la mañana, el miércoles por la noche es un documento
        inútil: la mitad ya no está a ese precio.
      </p>
      <p>
        Por eso publicamos cada oferta en {tg("@GangasOfertasChollos")} en cuanto aparece,
        con el formato siempre igual: producto, precio anterior, precio actual, porcentaje de
        descuento y enlace directo a la ficha de Amazon España. Y como el canal es público,
        puedes ir al <a href="{CANAL_HISTORIAL}" target="_blank"
        rel="sponsored nofollow noopener">historial</a> y comprobar qué se anuncia y cuándo,
        sin creerte a nadie. Si prefieres mirar sin recibir nada, el
        <a href="https://gangasofertas.com/general.html">catálogo de la web</a> se actualiza
        con lo mismo segundos después.
      </p>

      {NOTA_CATALOGO}

      <h2>El método completo, en siete pasos</h2>
      <p>
        La versión corta. Si solo vas a leer una cosa de esta página, es esto:
      </p>
      <ol class="steps">
        <li>
          <strong>Marca las fechas.</strong> El 6 y el 7 de octubre. No las improvises.
        </li>
        <li>
          <strong>Haz la lista antes, no durante.</strong> Con la lista hecha, una ganga es
          una decisión. Sin ella, una ganga es una compra que no habías planeado y que luego
          se justifica sola.
        </li>
        <li>
          <strong>Comprueba el precio de siempre.</strong> Un 50% sobre un precio inflado es
          un 15% de verdad. Es el paso que más dinero deja y el que casi nadie hace.
        </li>
        <li>
          <strong>Entra en la oferta desde el canal.</strong> El enlace va directo a la ficha
          con tu identificación de afiliado y el precio te cuesta lo mismo. No compras peor,
          compras con la misma información que el resto.
        </li>
        <li>
          <strong>Comprueba el precio en el carrito.</strong> Amazon corrige muchos de sus
          errores en el carrito, no en la ficha. Y es ahí donde se ve el envío, que en Prime
          es gratis a partir de 25 € en la mayoría de los pedidos.
        </li>
        <li>
          <strong>No aplaces los errores de precio.</strong> Si ves un precio que no cuadra,
          se compra o se pierde. Y no aplaces lo que no quieras: tienes 14 días naturales de
          desistimiento.
        </li>
        <li>
          <strong>Mira también el día después.</strong> Cuando la ventana se cierra, el
          stock se repone a precio bajo en muchas categorías. La segunda oportunidad existe.
        </li>
      </ol>
      <p class="mb-0">
        El desarrollo completo, con los errores que cuestan dinero de verdad, está en
        <a href="como-aprovechar-prime-days.html">cómo aprovechar los Prime Days</a>.
      </p>
    </div>
  </section>

{CTA_CANAL}

  <section class="section section--alt">
    <div class="wrap prose">
      <h2>Preguntas frecuentes</h2>
      <div class="faq mt-2" id="faq-index">
{faq_html(FAQ_INDEX, abierta=True)}
      </div>
      <p class="mt-2"><a class="btn btn--ghost" href="faq.html">Ver la FAQ completa →</a></p>
    </div>
  </section>

{NOTA_PRECIOS}

{relacionados(RELACIONADOS_BASE)}

  <section class="section section--tight">
    <div class="wrap center">
      <p class="muted small">
        ¿Quieres enterarte de cada oferta en el momento?
        {tg("Únete gratis a @GangasOfertasChollos")} · o mira el
        <a href="https://gangasofertas.com/general.html">catálogo completo</a>.
      </p>
    </div>
  </section>""",
}


# ─────────────────────────────────────────────────────────────────────────────
#  2. QUÉ ES
# ─────────────────────────────────────────────────────────────────────────────

FAQ_QUE_ES = [
    ("¿Amazon Prime Days es solo para miembros Prime?",
     "Las ofertas más exclusivas sí están reservadas a miembros Prime, que es la diferencia "
     "real frente a otras campañas. Amazon también suelta algunas gangas al resto de la "
     "audiencia, así que sin suscripción sigues viendo ofertas, pero las mejores te van a "
     "escapar."),
    ("¿Cuánto cuesta ser miembro Prime en España?",
     "4,99 € al mes o 49,90 € al año, con 30 días de prueba gratuita para nuevas altas que "
     "cumplan los requisitos. Amazon también tiene planes de descuento para estudiantes y "
     "adultos jóvenes, con condiciones y plazos propios."),
    ("¿Amazon Prime Days es lo mismo que el Prime Day?",
     "El Prime Day era el nombre original de la campaña de verano. Desde 2023 hay dos "
     "eventos al año: el de verano, que sigue siendo el Prime Day, y el de otoño, que se "
     "llama Prime Big Deal Days. El término Amazon Prime Days se usa para hablar de los dos "
     "juntos."),
]

PAGINA_QUE_ES = {
    "slug": "que-es-amazon-prime-days.html",
    "miga": "Qué son",
    "titulo": "Qué es Amazon Prime Days: cómo funciona la campaña",
    "desc": ("Qué es Amazon Prime Days en España: las dos campañas del año, qué significa "
             "ser miembro Prime, cómo se-called el evento y en qué se diferencia del Black "
             "Friday."),
    "alt_img": "Qué es Amazon Prime Days y cómo funciona",
    "faq": FAQ_QUE_ES,
    "cuerpo": f"""{encabezado(
        ("🎁", "Guía explicativa"),
        "Qué es exactamente un Amazon Prime Days",
        "Es la campaña con la que Amazon compite con el Black Friday sin esperar a "
        "noviembre. Y tiene una diferencia de fondo: aquí las ofertas duran días, no horas.",
        "9 min de lectura",
    )}

  <section class="section section--tight">
    <div class="wrap">
      <div class="keyfacts">
        <h2>Lo esencial de la campaña</h2>
        <dl>
          <dt>Qué es</dt>
          <dd>Una o dos campañas de descuentos de Amazon al año, con las mejores ofertas para miembros Prime</dd>
          <dt>Cuántas hay</dt>
          <dd>Dos desde 2023: una en verano y otra en otoño</dd>
          <dt>Campaña de otoño 2026</dt>
          <dd><strong>{RANGO_2026}</strong>, {DURACION} seguidas</dd>
          <dt>Campaña de verano 2026</dt>
          <dd>{PRIME_DAY_2026}, cuatro días</dd>
          <dt>Quién paga más</dt>
          <dd>Los miembros Prime: {PRIME_MES} o {PRIME_ANO} en España</dd>
        </dl>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap prose">
      <h2>La definición corta</h2>
      <p>
        Amazon Prime Days es el nombre que se usa para el conjunto de campañas de descuentos
        que Amazon organiza a lo largo del año y que se dirigen
        sobre todo a sus miembros
        Prime. No es un día suelto: desde 2023 son dos eventos, uno de verano y otro de otoño.
        La edición de otoño de 2026 es la que está en marcha ahora mismo, del 6 al 7 de
        octubre.
      </p>
      <p>
        La diferencia con una oferta normal de Amazon está en tres cosas concretas: la
        duración, el precio de referencia y la exclusividad. Ninguna de las tres es un detalle
        menor, y las tres se pueden aprovechar o desaprovechar. El resto de esta página las
        explica; el método en sí está en
        <a href="como-aprovechar-prime-days.html">cómo aprovechar los Prime Days</a>.
      </p>

      <h2>Las tres cosas que la hacen especial</h2>
      <h3>1. La ventana dura días, no horas</h3>
      <p>
        Es la diferencia más útil para el comprador. En muchas campañas los descuentos
        «solidarios» duran unas pocas horas y lo bueno se agota el primer día. Aquí la ventana
        es de {DURACION} seguidas en el caso de octubre, y de cuatro días en la de verano.
        Eso significa que una compra que se te escapó el martes tiene una segunda oportunidad
        el miércoles, y que el stock que vuelve a reponerse después suele hacerlo a precio bajo.
      </p>
      <h3>2. El precio de referencia no siempre es el de verdad</h3>
      <p>
        Cuando Amazon pone un 70% de descuento, el número se calcula sobre un precio
        «anterior» que a veces es el más alto visto en semanas. Esto no es ilegal y es una
        práctica habitual de todo el comercio, pero significa que el porcentaje del cartel
        no es el ahorro real. La forma de saberlo está detallada, con el método de
        comprobación en diez segundos, en
        <a href="descuentos-reales-o-falsos.html">descuentos reales o falsos</a>.
      </p>
      <h3>3. La exclusividad de Prime es real, pero no es una puerta cerrada</h3>
      <p>
        Amazon reserva buena parte de las ofertas de la campaña a miembros Prime. En España,
        ser miembro cuesta {PRIME_MES} o {PRIME_ANO}, y hay {PRIME_PRUEBA} para nuevas altas.
        Quien no sea miembro se queda fuera de las ofertas más exclusivas y de la entrega
        rápida, que es la diferencia que más se nota. Pero no se queda sin ofertas: Amazon
        publica muchas en abierto.
      </p>

      <h2>De dónde viene el nombre</h2>
      <p>
        El nombre ha cambiado varias veces, y esa es la razón de que exista tanta página
        contradictoria sobre el tema. El recorrido, resumido:
      </p>
      {tabla(
          "Cómo se ha ido llamando la campaña de Amazon",
          ["Nombre", "Cuándo", "Qué pasó"],
          [
              ["Prime Day", "2015-2019",
               "El nombre original. Campaña de verano, un solo día el primer año."],
              ["Prime Early Access Sale", "2022",
               "Nace la segunda campaña del año, en octubre, con este nombre."],
              ["Prime Big Deal Days", "2023-hoy",
               "La de octubre cambia de nombre y se convierte en la oficial de otoño."],
              ["Amazon Prime Days", "en uso actual",
               "El nombre genérico para hablar de las dos campañas a la vez."],
              ["Fiesta de Ofertas Prime", "prensa española",
               "Como lo titulan Xataka, Hola, La Vanguardia y ELLE."],
          ],
      )}
      <p class="mt-2">
        En la práctica, <strong>los cinco nombres se refieren a lo mismo</strong>. Quien
        busca uno llega a páginas que hablan del otro, y por eso hay tanta contradicción: no es
        que nadie se Equivoque, es que todos están usando la palabra que les suena.
      </p>

      <h2>Las dos campañas del año</h2>
      {tabla(
          "Cómo se diferencian las dos ediciones de 2026",
          ["", "Verano (Prime Day)", "Otoño (Prime Big Deal Days)"],
          [
              ["Fechas de 2026", PRIME_DAY_2026, RANGO_2026],
              ["Duración", "Cuatro días", DURACION],
              ["Enfoque", "Tecnología, ocio y hogar", "Temporada de otoño y regalosPIXantin-ahead"],
              ["Relación con la Navidad", "Ninguna", "Prepara la lista navideña"],
              ["Estado", "Ya pasó", "En marcha"],
          ],
      )}
      <p class="mt-2">
        El patrón de los últimos años es bastante estable y por eso se puede planificar con
        antelación: la edición de verano cae entre junio y julio, y la de otoño, en la
        segunda semana de octubre. Todo el historial está en
        <a href="fechas-amazon-prime-days.html">la página de fechas</a>.
      </p>

      <h2>En qué se diferencia del Black Friday</h2>
      <p>
        Es la comparación que todo el mundo hace, y tiene sentido porque las fechas están
        cerca. Pero son cosas distintas:
      </p>
      {tabla(
          "Amazon Prime Days frente a Black Friday 2026 en España",
          ["", "Prime Days (6-7 de octubre)", "Black Friday (27 de noviembre)"],
          [
              ["Quién lo organiza", "Amazon", "Todo el comercio, cada tienda por su cuenta"],
              ["Duración de las ofertas", DURACION, "Unas horas; lo bueno dura minutos"],
              ["Quién puede comprar", "Todo el mundo, con mejores ofertas para miembros Prime", "Todo el mundo"],
              ["Descuentos más grandes", "Raros, salvo errores de precio", "Frecuentes en muchas tiendas"],
              ["Repuesto", "Stock repuesto a precio bajo tras la ventana", "No hay repuesto: se acabó"],
              ["Página oficial de fechas", "aboutamazon.com, en español", "No hay fecha oficial única"],
          ],
      )}
      <p class="mt-2">
        El resumen: <strong>en el Prime Days compras con margen y con segunda oportunidad; en
        el Black Friday compras con reloj</strong>. Si solo vas a poder mirar uno de los dos
        con calma, el Prime Days es el más fácil. Si puedes preparar las dos, el Black Friday
        tiene los descuentos más agresivos.
      </p>

      <h2>Los errores que más se repiten</h2>
      <ul class="checklist">
        <li>
          <strong>Creer que es un solo día.</strong> Es una de las dos ventanas del año, y la
          de otoño dura dos días completos.
        </li>
        <li>
          <strong>Confundirlo con el Prime Day de verano.</strong> Son campañas distintas,
          con fechas distintas. Comprar el producto equivocado para una fecha equivocada es el
          error más caro.
        </li>
        <li>
          <strong>Tomarse el porcentaje del cartel como ahorro real.</strong> El descuento se
          calcula sobre un precio de referencia que a veces está inflado.
        </li>
        <li>
          <strong>Entrar sin tener Prime y esperar a ver las ofertas exclusivas.</strong> Se
          puede comprar, pero las mejores no están ahí.
        </li>
        <li>
          <strong>Comprar el día 7 a última hora.</strong> Es el día con más congestión y
          con más riesgo de que el envío se vaya de plazo.
        </li>
        <li>
          <strong>Aplicar lo que ya se sabe que no se va a usar.</strong> Un 80% de
          descuento sobre algo que no quieres sigue siendo dinero gastado.
        </li>
      </ul>

      <h2>Dónde ver las ofertas en vivo</h2>
      <p>
        La página de este sitio con las ofertas por categoría es
        <a href="ofertas-prime-days-2026.html">ofertas Prime Days por categoría</a>, y el
        catálogo vivo, que se actualiza con cada anuncio, está en
        <a href="https://gangasofertas.com/general.html">gangasofertas.com/general.html</a>.
        Para enterarte en el momento en lugar de mirar, lo más útil es
        {tg("el canal de Telegram")}: cada oferta se publica con su precio anterior, su
        precio actual y el enlace directo, y el historial es público para que puedas
        comprobar cuándo se anunció cada cosa.
      </p>

      {NOTA_CATALOGO}
    </div>
  </section>

{CTA_CANAL}

  <section class="section section--alt">
    <div class="wrap prose">
      <h2>Preguntas frecuentes sobre qué es</h2>
      <div class="faq mt-2" id="faq-que-es">
{faq_html(FAQ_QUE_ES, abierta=True)}
      </div>
      <p class="mt-2"><a class="btn btn--ghost" href="faq.html">Ver la FAQ completa →</a></p>
    </div>
  </section>

{NOTA_PRECIOS}

{relacionados(RELACIONADOS_BASE)}

  <section class="section section--tight">
    <div class="wrap center">
      <p class="muted small">
        Las dos campañas del año, al instante:
        {tg("Únete a @GangasOfertasChollos")}.
      </p>
    </div>
  </section>""",
}


# ─────────────────────────────────────────────────────────────────────────────
#  3. FECHAS Y CALENDARIO
# ─────────────────────────────────────────────────────────────────────────────

FAQ_FECHAS = [
    ("¿Son las fechas de 2026 confirmadas oficialmente?",
     "Sí. Amazon publicó el anuncio en su propio despacho de noticias, en español, con el "
     "rango del 6 al 7 de octubre y las 48 horas de duración. Puede consultarse en "
     "aboutamazon.com. No es una rumorología de prensa."),
    ("¿Y la fecha de la edición de verano de 2026?",
     "También está confirmada: del 23 al 26 de junio de 2026, cuatro días. Fue la primera "
     "vez que la campaña de verano caía en junio en lugar de julio."),
    ("¿Por qué la gente encuentra fechas de otros años?",
     "Porque las páginas se escribieron para la edición de su año y nunca se actualizaron. "
     "Por eso aquí cada fecha histórica va siempre acompañada de su año, y la única fecha de "
     "2026 publicada es la que tiene fuente."),
]

PAGINA_FECHAS = {
    "slug": "fechas-amazon-prime-days.html",
    "miga": "Fechas",
    "titulo": "Amazon Prime Days 2026: fechas y calendario de campañas",
    "desc": ("Fechas confirmadas del Amazon Prime Days 2026: 6 y 7 de octubre en España, "
             "más el historial real de las doce últimas ediciones y el patrón de fechas."),
    "alt_img": "Fechas y calendario del Amazon Prime Days 2026",
    "faq": FAQ_FECHAS,
    "cuerpo": f"""{encabezado(
        ("📅", "Fechas confirmadas"),
        "Amazon Prime Days 2026: 6 y 7 de octubre en España",
        "La campaña de otoño va del martes 6 al miércoles 7 de octubre de 2026, durante 48 "
        "horas seguidas. Está confirmado por Amazon, en español, y abajo tienes el "
        "historial completo de las doce últimas ediciones.",
        "8 min de lectura",
    )}

{cuenta_atras()}

  <section class="section section--tight">
    <div class="wrap">
      <div class="keyfacts">
        <h2>Las fechas, en corto</h2>
        <dl>
          <dt>Campaña de otoño 2026</dt>
          <dd><strong>{RANGO_2026}</strong> · {FECHA_INICIO_2026} a las 00:00 hasta {FECHA_FIN_2026} a las {HORA_FIN} (hora peninsular)</dd>
          <dt>Duración</dt>
          <dd>{DURACION} ininterrumpidas</dd>
          <dt>Campaña de verano 2026</dt>
          <dd>{PRIME_DAY_2026} · ya celebrated</dd>
          <dt>Próxima edición prevista</dt>
          <dd>Verano de 2027, con toda probabilidad entre junio y julio</dd>
          <dt>Fuente</dt>
          <dd>Anuncio oficial de Amazon en aboutamazon.com, versión en español</dd>
        </dl>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap prose">
      <h2>La fecha de octubre de 2026, con su fuente</h2>
      <p>
        Amazon ha confirmado por escrito que la campaña de otoño va <strong>del martes 6 al
        miércoles 7 de octubre de 2026</strong>, con 48 horas de ofertas exclusivas para
        miembros Prime en más de 35 categorías. El anuncio oficial, en su versión en
        español, es este:
      </p>
      <p>
        <a href="{FUENTE_OFICIAL}" target="_blank" rel="noopener">Prime Big Deal Days regresa
        del 6 al 7 de octubre: Esto es lo que puedes esperar</a> — aboutamazon.com, despacho
        de noticias de Amazon.
      </p>
      <p>
        Conviene decir de dónde sale cada dato porque en este tema circulan fechas de otros
        años como si fueran de este. Aquí la regla es simple: <strong>una fecha solo se
        publica si tiene fuente, y la fuente se enlaza</strong>. Las que no la tienen, no
        están.
      </p>

      {NOTA_FUENTE}

      <h2>La hora exacta importa, y hay una trampa</h2>
      <p>
        El anuncio de Amazon da la hora de arranque en el huso del Pacífico
        (<abbr title="Pacific Daylight Time">PDT</abbr>), que va seis horas por detrás de la
        hora peninsular española en esta época del año. Traducido, el arranque real en España
        se produce a media mañana del martes 6, y la ventana se cierra la noche del
        miércoles 7.
      </p>
      <p>
        Esta es exactamente la razón por la que algunas páginas dicen «empieza a las 00:00»
        y otras dicen «empieza por la mañana»: no siempre se están contradiciendo, están
        hablando de husos distintos. La conclusión práctica es la misma: <strong>tienes el
        martes 6 entero para comprar</strong>, y no hace falta estar pendiente a una hora
        exacta. La cuenta atrás de esta página usa la hora de Madrid, que es la tuya si lees
        desde España.
      </p>

      <h2>El historial completo, edición por edición</h2>
      <p>
        Esta tabla es la que no tienen los competidores. Cada fecha va con su año y con lo que
        pasó en esa edición, para que se vea el patrón en lugar de una suposición. Va a
        ancho completo de página porque con cuatro columnas no cabe en la columna de texto:
      </p>
    </div>
  </section>

  <section class="section section--tight">
    <div class="wrap">
{tabla(
          "Historial de ediciones de Amazon Prime Day y Prime Big Deal Days",
          ["Año", "Verano (Prime Day)", "Otoño (Big Deal Days)", "Qué pasó"],
          [[a, v, o, q] for a, v, o, q in HISTORICO],
          ancho_completo=True,
      )}
    </div>
  </section>

  <section class="section">
    <div class="wrap prose">
      <p>
        Fíjate en la última fila: la campaña de verano de 2026 se hizo
        <strong>en junio</strong>, no en julio. Es el primer año que ocurre, y es un aviso
        importante: <strong>las fechas se mueven</strong>. Confiar en que el verano siempre
        cae en julio es exactamente el error que hacen las páginas con la tabla de fechas
        fija.
      </p>

      <h2>El patrón, para planear la siguiente</h2>
      <p>
        Con doce ediciones encima se ven cuatro cosas bastante estables, y sirven para no
        llegar a la campaña a ciegas:
      </p>
      <ol class="steps">
        <li>
          <strong>La de otoño cae en la segunda semana de octubre.</strong> Ha estado entre el
          7 y el 14 de octubre en todas las ediciones desde 2022. Es la predicción más
          fiable que se puede hacer, aunque no es un anuncio.
        </li>
        <li>
          <strong>La de verano cae entre junio y julio.</strong> Cuatro años en julio, uno en
          junio. Fin de mes, en fin de semana, casi siempre.
        </li>
        <li>
          <strong>La duración se ha ido alargando.</strong> Empezó con un solo día en 2015 y
          lleva cuatro desde 2025.
        </li>
        <li>
          <strong>Amazon avisa con antelación, pero no con mucha.</strong> El anuncio oficial
          suele salir una o dos semanas antes, no meses. Quien espere la fecha en enero de
          2027 se enterará tarde.
        </li>
      </ol>
      <p>
        Lo que no se puede prever, y conviene decir con claridad, es la fecha exacta de
        2027. Cuando Amazon la confirme, aparecerá en su
        <a href="https://www.aboutamazon.com/">despacho de noticias</a>, y aquí se actualizará
        en cuanto se sepa. Para enterarte sin tener que volver a esta página,
        {tg("el canal de Telegram")} avisa el día que arranca.
      </p>

      <h2>Qué pasa cuando termina</h2>
      <p>
        La ventana se cierra la noche del miércoles 7 de octubre y, en la mayoría de los
        casos, los precios vuelven a su valor anterior. Pero el día posterior tiene su propio
        interés:
      </p>
      <ul>
        <li>
          <strong>Se repone stock a precio bajo.</strong> Las unidades que nadie compró
          durante la campaña vuelven al catálogo rebajadas durante unos días.
        </li>
        <li>
          <strong>Quedan fuera de oferta los productos que agotaron.</strong> Los que se
          agotaron durante la ventana vuelven con el precio normal, y ahí es donde aparecen
          los errores de precio: no tienen por qué guardar relación con ninguna campaña.
        </li>
        <li>
          <strong>Empieza la cuenta atrás hacia el Black Friday.</strong> La próxima ventana
          grande en España es el Black Friday, el 27 de noviembre de 2026, y aquí está el
          <a href="https://gangasofertas.com/BlackFriday/index.html">calendario del Black
          Friday</a> para ir planificándolo con tiempo.
        </li>
      </ul>

      {NOTA_CATALOGO}
    </div>
  </section>

{CTA_CANAL}

  <section class="section section--alt">
    <div class="wrap prose">
      <h2>Preguntas frecuentes sobre las fechas</h2>
      <div class="faq mt-2" id="faq-fechas">
{faq_html(FAQ_FECHAS, abierta=True)}
      </div>
      <p class="mt-2"><a class="btn btn--ghost" href="faq.html">Ver la FAQ completa →</a></p>
    </div>
  </section>

{NOTA_PRECIOS}

{relacionados(RELACIONADOS_BASE)}

  <section class="section section--tight">
    <div class="wrap center">
      <p class="muted small">
        ¿Quieres saber el día que arranque la próxima campaña?
        {tg("Únete a @GangasOfertasChollos")}.
      </p>
    </div>
  </section>""",
}


# ─────────────────────────────────────────────────────────────────────────────
#  4. OFERTAS POR CATEGORÍA
# ─────────────────────────────────────────────────────────────────────────────

FAQ_OFERTAS = [
    ("¿Cuántas ofertas hay?",
     "Amazon anuncia rebajas en más de 35 categorías y habla de millones de ofertas en "
     "total. Pero las que de verdad ahorran dinero son una fracción mucho más pequeña, y "
     "son las que publicamos: producto, precio anterior, precio actual, descuento y enlace."),
    ("¿Las ofertas del canal son de esta campaña?",
     "No necesariamente. Publicamos lo que vemos, que incluye las ofertas de Prime Days, las "
     "que ya estaban activas, los errores de precio y las gangas de otras campañas. El "
     "catálogo está vivo en todo momento, no solo el 6 y el 7 de octubre."),
    ("¿Hay una categoría con más descuentos que las demás?",
     "La electrónica concentra los importes absolutos más altos. Pero si lo que buscas es "
     "porcentaje, el gaming y la belleza suelen ganar, porque sus precios habituales ya son "
     "altos y el descuento se nota más en la etiqueta."),
]

PAGINA_OFERTAS = {
    "slug": "ofertas-prime-days-2026.html",
    "miga": "Ofertas",
    "titulo": "Ofertas Prime Days 2026 por categoría: dónde mirar",
    "desc": ("Dónde mirar las ofertas del Amazon Prime Days 2026 en España: categoría por "
             "categoría, qué baja de verdad y cómo ver cada oferta en vivo sin perder tiempo."),
    "alt_img": "Ofertas del Amazon Prime Days 2026 por categoría",
    "faq": FAQ_OFERTAS,
    "cuerpo": f"""{encabezado(
        ("🏷️", "Ofertas por categoría"),
        "Dónde mirar las ofertas del Prime Days, categoría por categoría",
        "Amazon anuncia rebajas en más de 35 categorías, pero no todas“(”hacen falta para "
        "comprar. Esto es qué mirar en cada una y dónde ver las ofertas en vivo.",
        "8 min de lectura",
    )}

  <section class="section section--tight">
    <div class="wrap">
      <div class="stats">
        <div class="stat">
          <span class="stat__num">35+</span>
          <span class="stat__label">categorías con descuento anunciado</span>
        </div>
        <div class="stat">
          <span class="stat__num">48 h</span>
          <span class="stat__label">de ventana, del 6 al 7 de octubre</span>
        </div>
        <div class="stat">
          <span class="stat__num">3×</span>
          <span class="stat__label">al día entran lotes nuevos de ofertas</span>
        </div>
        <div class="stat">
          <span class="stat__num">14 días</span>
          <span class="stat__label">para desistir de lo comprado</span>
        </div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap prose">
      <h2>Dónde ver las ofertas ahora mismo</h2>
      <p>
        Lo más rápido y lo más fiable es el canal, porque cada oferta se publica en cuanto se
        detecta: {tg("@GangasOfertasChollos")}. Si prefieres mirar sin recibir nada, el
        catálogo de la web se actualiza con lo mismo y se puede filtrar por categoría desde
        ahí:
      </p>
      <ul>
        <li>
          <a href="https://gangasofertas.com/general.html">Todas las ofertas</a> ·
          el catálogo completo, ordenado de más reciente a más antigua.
        </li>
        <li>
          <a href="https://gangasofertas.com/moviles-electronica.html">Móviles y
          electrónica</a> · donde están los importes absolutos más altos.
        </li>
        <li>
          <a href="https://gangasofertas.com/gaming-consolas.html">Gaming y consolas</a> ·
          donde los porcentajes suelen ser más altos.
        </li>
        <li>
          <a href="https://gangasofertas.com/ropa-y-calzado.html">Ropa y calzado</a> ·
          donde más se repite la misma talla en distintos colores.
        </li>
        <li>
          <a href="https://gangasofertas.com/higiene-cuidado-personal.html">Higiene y cuidado
          personal</a> · los descuentos másconstants del año, no los más grandes.
        </li>
        <li>
          <a href="https://gangasofertas.com/juguetes-infantil.html">Juguetes e infantil</a> ·
          con especial atención a la fecha límite de devolución.
        </li>
        <li>
          <a href="https://gangasofertas.com/papeleria-oficina.html">Papelería y oficina</a> ·
          el euro que se ahorra por producto es pequeño, pero hay muchos productos.
        </li>
      </ul>

      {NOTA_CATALOGO}

      <h2>Qué mirar en cada categoría</h2>
      <p>
        Amazon anuncia rebajas en más de 35 categorías, pero no todas sirven para el mismo
        tipo de comprador. La diferencia está en <em>qué</em> se abarata: en unas categorías
        importes absolutos, en otras porcentajes sobre precios que ya eran altos, y en otras
        simplemente la reposición de stock. Esto es, categoría por categoría, qué mirar.
      </p>
      <p class="mb-0">
        Cada una de estas categorías tiene su propia página en el catálogo, con las ofertas
        vivas que publica el canal. Los enlaces están al principio de esta página.
      </p>
    </div>
  </section>

  <section class="section section--tight">
    <div class="wrap">
{tabla(
          "Qué mirar en cada categoría durante el Prime Days de octubre de 2026",
          ["Categoría", "Qué baja", "Qué mirar"],
          [
              ["Móviles y electrónica",
               "Portátiles, auriculares, televisores, cámaras y relojes",
               "Los importes absolutos más altos de la campaña. Aquí es donde un descuento "
               "del 20% se nota en el bolsillo. Comprueba el precio de la semana anterior."],
              ["Gaming y consolas",
               "Juegos, accesorios, mandoes y auriculares gaming",
               "Porcentajes más altos que en electrónica, porque los precios habituales ya son "
               "altos. Cuidado con los juegos digitales: no tienen fecha límite."],
              ["Ropa y calzado",
               "Prendas de temporada, calzado y bolsos",
               "La categoría donde más se repite el mismo producto en distintos colores y "
               "tallas. Busca si la talla que quieres está en stock, no solo el color."],
              ["Hogar y cocina",
               "Sartenes, ollas, cuchillos y pequeños electrodomésticos",
               "Descuentos constantes más que deportivos. Buen sitio para renovar lo que "
               "usarías a diario sin innecesarios."],
              ["Belleza y cuidado personal",
               "Perfumes, cuidado facial y cosméticos",
               "Buenos porcentajes sobre precios altos, con una ventaja: casi todo se puede "
               "devolver si no te convence, por el desistimiento de 14 días."],
              ["Juguetes e infantil",
               "Juguetes por rango de edad y juegos de mesa",
               "Comprueba la fecha límite de devolución con más cuidado que en ninguna otra "
               "categoría: si se pasa, el regalo ya no se puede cambiar."],
              ["Papelería y oficina",
               "Material de oficina y material escolar",
               "El ahorro por producto es pequeño, pero se suma. Útil si ya ibas a "
               "comprarlo igualmente para la vuelta al cole."],
          ],
ancho_completo=True,
      )}
    </div>
  </section>

  <section class="section">
    <div class="wrap prose">
      <p class="mt-2">
        Cada una de estas categorías tiene su propia página en el catálogo, con las ofertas
        vivas que publica el canal. Los enlaces están al principio de esta página.
      </p>

      <h2>Cuándo entran las ofertas nuevas</h2>
      <p>
        Amazon no suelta todo de golpe. Segun su propio anuncio, <strong>nuevas ofertas
        aparecen a lo largo del evento por tandas, hasta tres veces al día</strong>, y van
        sustituyendo a las anteriores. Eso tiene una consecuencia práctica que casi nadie
        menciona: <strong>la oferta que viste el martes por la mañana puede ya no estar el
        martes por la tarde</strong>.
      </p>
      <p>
        Por eso una tabla de ofertas escrita una vez y consultada al día siguiente es un
        documento muerto, y por eso
        la razón de que
        {tg("el canal de Telegram")} sea la herramienta útil aquí: cada cambio se publica en
        el momento, y el <a href="{CANAL_HISTORIAL}" target="_blank"
        rel="sponsored nofollow noopener">historial del canal</a> deja registro de qué se
        anunciar y cuándo, para que puedas comprobar si una oferta existió de verdad.
      </p>

      <h2>Ofertas anticipadas: qué mirar antes de que empiece la campaña</h2>
      <p>
        Amazon viene activando promociones antes del arranque oficial. Desde finales de
        septiembre se pueden encontrar rebajas que van desde lo discreto hasta el 80% o más,
        y aquí es donde más se cuela el precio inflado. Dos cosas concretas:
      </p>
      <ul>
        <li>
          <strong>Un 80% de descuento anticipado no es un chollo automático.</strong> En las
          ofertas anticipadas el precio de referencia sube con más frecuencia, porque el
          producto lleva semanas sin venderse a ese nivel. El método de comprobación está en
          <a href="descuentos-reales-o-falsos.html">descuentos reales o falsos</a>.
        </li>
        <li>
          <strong>Lo que no caduca vale más que lo que caduca.</strong> Un 15% real sobre un
          producto que quieres y que estará disponible en marzo vale más que un 80% sobre un
          producto de temporada que ya no vas a usar.
        </li>
      </ul>

      <h2>Errores de precio: el otro 10%</h2>
      <p>
        Junto a la campaña siempre hay errores de precio: productos que se muestran a una
        fracción de su valor. No tienen nada que ver con Amazon Prime Days, pero caen en las
        mismas fechas, que es cuando más gente está mirando la web de Amazon y más
        probabilidad hay de que un error pase desapercibido. Si ves un precio que no cuadra,
        se compra o se pierde. Está explicado en detalle, con las cuatro señales para
        reconocerlo, en la página de <a href="descuentos-reales-o-falsos.html">descuentos
        reales o falsos</a>.
      </p>

      {NOTA_PRECIOS}
    </div>
  </section>

{CTA_CANAL}

  <section class="section section--alt">
    <div class="wrap prose">
      <h2>Preguntas frecuentes sobre las ofertas</h2>
      <div class="faq mt-2" id="faq-ofertas">
{faq_html(FAQ_OFERTAS, abierta=True)}
      </div>
      <p class="mt-2"><a class="btn btn--ghost" href="faq.html">Ver la FAQ completa →</a></p>
    </div>
  </section>

{relacionados(RELACIONADOS_BASE)}

  <section class="section section--tight">
    <div class="wrap center">
      <p class="muted small">
        ¿Prefieres que te lo digamos nosotros? {tg("Únete a @GangasOfertasChollos")} o
        mira el <a href="https://gangasofertas.com/categorias.html">catálogo por
        categorías</a>.
      </p>
    </div>
  </section>""",
}


# ─────────────────────────────────────────────────────────────────────────────
#  5. DESCUENTOS REALES O FALSOS
# ─────────────────────────────────────────────────────────────────────────────

PASOS_VERIFICAR = [
    ("Mira el precio de referencia, no solo el descuento",
     "El precio tachado junto al precio de oferta es el que Amazon usa como base del "
     "porcentaje. Si ese precio es mucho más alto que lo que costaba hace un mes, el "
     "descuento es mayor de lo que parece."),
    ("Compara con lo que pagaste tú, no con lo que pone el cartel",
     "El precio que importa es el tuyo: cuánto pagaste la última vez que lo compraste, o lo "
     "que cuesta en otra tienda ahora mismo. El porcentaje es secundario."),
    ("Comprueba la fecha de la última oferta",
     "Amazon guarda el historial de precios en cada ficha y Alexa for Shopping muestra hasta "
     "365 días de histórico. Si el precio de referencia es de hace un mes, ese mes probablemente "
     "no era el habitual."),
    ("Mira si el descuento aparece en varios sitios",
     "Si el mismo producto aparece con precios muy distintos en las distintas variantes, "
     "es una señal de stock limitado: en cuanto se agote uno, el precio sube."),
    ("Haz la cuenta en euros, no en porcentajes",
     "Un 70% de 20 euros son 14 euros ahorrados. Un 25% de 300 euros son 75. El porcentaje "
     "engana mucho más que el importe."),
]

FAQ_DESCUENTOS = [
    ("¿Por qué Amazon no considera falso un descuento inflado?",
     "Porque técnicamente no lo es. Amazon compara con su propio precio más reciente, y si "
     "ese precio fue alto por un motivo concreto o por un error temporal, el descuento que "
     "publica cumple la norma de precios de referencia. La práctica es habitual en todo el "
     "comercio y solo es ilegal si el precio de referencia no corresponde a una venta real."),
    ("¿Cómo sé el precio de referencia real?",
     "Por historial de precios. Amazon muestra el suyo en la ficha de producto y Alexa for "
     "Shopping llega a 365 días de datos. Ahí se ve si el precio tachado era un pico "
     "puntual o el nivel normal."),
    ("¿Es lo mismo un error de precio que un descuento inflado?",
     "No. Un descuento inflado usa un precio alto pero real. Un error de precio muestra un "
     "valor que nadie debería pagar, y suele corregirse en minutos u horas."),
    ("¿Es seguro comprar un error de precio?",
     "El precio sí es real en el momento en que lo ves, pero el riesgo es que el pedido se "
     "cancele o el precio se corrija antes de salir. Si Amazon cancela el pedido, no hay "
     "problema. Lo que no se puede recuperar es el tiempo perdido por una compra que al final "
     "no sale."),
]

PAGINA_DESCUENTOS = {
    "slug": "descuentos-reales-o-falsos.html",
    "miga": "Descuentos reales",
    "titulo": "Descuentos reales o falsos en Prime Days: cómo saberlo",
    "desc": ("Cómo saber si un descuento de Prime Days es real o está inflado sobre un precio "
             "que ya estaba subido. El método de comprobación en cinco pasos, sin pagar "
             "herramientas."),
    "alt_img": "Cómo saber si un descuento del Prime Days es real",
    "faq": FAQ_DESCUENTOS,
    "cuerpo": f"""{encabezado(
        ("🔍", "Descuentos reales"),
        "Cómo saber si un descuento del Prime Days existe de verdad",
        "El número del cartel no es el ahorro real. En cinco pasos puedes comprobar si un 70% "
        "de descuento te ahorra el 70% de lo que costaba, o un 15%.",
        "10 min de lectura",
    )}

  <section class="section">
    <div class="wrap prose">
      <h2>Por qué esta es la pregunta que más dinero devuelve</h2>
      <p>
        En cualquier campaña de descuentos hay cuatro cosas que parecen iguales y no lo son.
        Confundirlas es la forma más común de gastar dinero de más:
      </p>
      {tabla(
          "Los cuatro casos de rebajas que aparecen en una campaña como el Prime Days",
          ["Tipo", "Qué es", "Riesgo"],
          [
              ["Descuento real",
               "El precio baja sobre su nivel habitual. Lo que ahorras es lo que dice.",
               "Ninguno. Es el caso bueno."],
              ["Descuento inflado",
               "El precio baja, pero el precio de referencia estaba subido. El porcentaje es "
               "grande y el ahorro pequeño.",
               "Pagar de más creyendo que has hecho un chollo."],
              ["Descuento menor del anunciado",
               "Lo más habitual en esta campaña: hay una oferta, pero más pequeña de lo que "
               "sugiere el cartel.",
               "Perder la oportunidad por mirar en otro sitio."],
              ["Error de precio",
               "El producto aparece a una fracción de su valor. Nadie debería cobrar eso.",
               "Que se corrija en minutos, o que el pedido se cancele."],
          ],
      )}
      <p class="mt-2">
        El descuento real no necesita explicación: es el caso normal. El que merece atención
        es el segundo, porque es mayoritario y porque el número del cartel lo hace pasar por
        el primero. El tercero merece atención por lo contrario: es el más rentable y el más
        frágil. Y el cuarto es el más frustrante, porque dejas de mirar por algo que sí
        existía, solo que más barato de lo que pensabas.
      </p>

      <h2>El precio de referencia y por qué a veces no significa nada</h2>
      <p>
        Cuando Amazon marca un producto como rebajado, muestra un precio tachado y un precio
        de oferta. El porcentaje es, literalmente, la diferencia entre ambos. El problema es
        que <strong>el precio tachado es el más alto que Amazon ha tenido en un periodo
        concreto, no el precio habitual del producto</strong>. Si ese producto subió dos
        semanas por un motivo puntual y luego se repuso más caro, el precio tachado es un pico
        que casi nadie pagó.
      </p>
      <p>
        Y hay un caso límite que conviene conocer: <strong>el precio de referencia se toma del
        producto de marca blanca</strong>. Si compras el artículo propio de Amazon en lugar de
        la marca, el precio de referencia es el de la marca, que es más alto. El descuento se
        ve enorme y el ahorro real, mucho menor.
      </p>

      <h2>El método de comprobación, en cinco pasos</h2>
      <p>
        Este método no necesita pagar nada ni instalar nada. Solo mirar bien la ficha del
        producto, y en algún caso el historial de precios que Amazon ya publica.
      </p>
      <ol class="steps">
        <li>
          <strong>Mira el precio de referencia, no solo el descuento.</strong> Si el precio
          tachado está muy por encima de lo que costaba el producto el mes pasado, el
          descuento está inflado.
        </li>
        <li>
          <strong>Compara con lo que pagaste tú.</strong> El precio que importa es el tuyo:
          cuánto pagaste la última vez, o lo que cuesta en otra tienda ahora. El porcentaje es
          secundario.
        </li>
        <li>
          <strong>Comprueba la fecha de la última oferta.</strong> Amazon guarda el historial
          de precios en cada ficha, y Alexa for Shopping muestra hasta 365 días de histórico.
          Si el precio de referencia es de hace un mes, ese mes probablemente no era el
          habitual.
        </li>
        <li>
          <strong>Mira si el precio varía entre páginas del mismo producto.</strong> Si el
          mismo artículo aparece con precios distintos según el color, la talla o el
          vendedor, casi siempre es falta de stock, no una oferta especial. En cuanto se
          agota la unidad barata, el precio sube.
        </li>
        <li>
          <strong>Haz la cuenta en euros, no en porcentajes.</strong> Un 70% de 20 euros son
          14 euros. Un 25% de 300 euros son 75. El porcentaje engaña mucho más que el importe,
          y el importe es el que aparece en tu banco.
        </li>
      </ol>
      <p>
        El mismo método, aplicado a las ofertas que publicamos, está pensado para que
        puedas repetirlo: cada oferta del canal lleva el precio anterior y el precio actual,
        de modo que la comparación la puedes hacer tú sin intermediarios. Y si quieres ver
        las ofertas en el momento, {tg("únete al canal")}.
      </p>

      <h2>Cómo se reconoce un error de precio</h2>
      <p>
        Un error de precio no se parece a un descuento: se parece a una equivocación. Y esa
        diferencia es justo lo que te permite actuar sobre ella. Un descuento del 50% te está
        diciendo que el producto vale la mitad de lo que costaba. Un error de precio te está
        diciendo que el sistema ha mostrado un número que nadie ha pedido.
      </p>
      <p>Las cuatro señales, en orden de fiabilidad:</p>
      <ol class="steps">
        <li>
          <strong>El precio no encaja con la categoría.</strong> Un portátil de 900 euros en
          60 euros no es una oferta, es un error. Si el precio nuevo es una fracción
          desproporcionada del habitual, casi seguro es un error.
        </li>
        <li>
          <strong>La ficha sigue mostrando el precio antiguo en algún sitio.</strong> A veces
          la portada del producto, las miniaturas o el carrito muestran un número y el
          producto otro. Esa incoherencia interna es la firma del error.
        </li>
        <li>
          <strong>Aparece y desaparece en minutos.</strong> Si al volver a mirar a los diez
          minutos ya no está, era un error temporal. Y si sigue ahí, quizá era real.
        </li>
        <li>
          <strong>Aparece en productos muy específicos o de poco stock.</strong> Los errores
          se dan más en referencias con pocas unidades, porque hay menos gente mirándolas y
          tarda más en corregirse.
        </li>
      </ol>

      <h2>Qué hacer cuando encuentras uno</h2>
      <p>
        Un error de precio no perdona: si lo ves y no actúas en minutos, ya no está. El
        orden correcto es este:
      </p>
      <ol class="steps">
        <li>
          <strong>Comprueba el precio en el carrito, no en la ficha.</strong> Amazon corrige
          muchos de sus errores en el carrito, y es el precio del carrito el que se cobra.
        </li>
        <li>
          <strong>Si el carrito mantiene el precio, pídalo.</strong> Añádelo, cierra y
          confirma el pedido. Si el error está ahí, es una compra legítima a ese precio.
        </li>
        <li>
          <strong>Revisa el envío.</strong> Un envío de 15 euros se come el ahorro de
          inmediato. Y que seas miembro Prime cambia mucho este punto.
        </li>
        <li>
          <strong>Guarda capturas.</strong> Si Amazon te pide después justificar el pedido, la
          captura con el precio es tu respaldo.
        </li>
      </ol>
      <p class="mb-0">
        Los errores de precio son, con diferencia, la parte más rentable de estas fechas, y
        también la que más se integra en un canal en vivo en lugar de un artículo: cambian
        cada hora. Para verlos en cuanto aparecen,
        {tg("entra en el canal")}, o mira el
        <a href="https://gangasofertas.com/general.html">catálogo de ofertas</a>, que
        recoge lo mismo.
      </p>
    </div>
  </section>

{CTA_CANAL}

  <section class="section section--alt">
    <div class="wrap prose">
      <h2>Preguntas frecuentes sobre los descuentos</h2>
      <div class="faq mt-2" id="faq-descuentos">
{faq_html(FAQ_DESCUENTOS, abierta=True)}
      </div>
      <p class="mt-2"><a class="btn btn--ghost" href="faq.html">Ver la FAQ completa →</a></p>
    </div>
  </section>

{relacionados(RELACIONADOS_BASE)}

  <section class="section section--tight">
    <div class="wrap center">
      <p class="muted small">
        ¿Quieres que alguien te haga la comprobación por ti?
        {tg("Únete a @GangasOfertasChollos")}.
      </p>
    </div>
  </section>""",
}


# ─────────────────────────────────────────────────────────────────────────────
#  6. CÓMO APROVECHARLO
# ─────────────────────────────────────────────────────────────────────────────

FAQ_APROVECHAR = [
    ("¿Vale la pena ser miembro Prime por la campaña?",
     "Depende de cuánto compres en la ventana. Si compras una sola vez, la cuota anual no se "
     "amortiza. Si ya compras en Amazon con regularidad, la cuota se paga sola con el envío "
     "gratuito y las ofertas exclusivas son un extra."),
    ("¿Qué hago si se acaba el stock?",
     "No sobrevive al stock: mira el día siguiente. Después de la ventana, las unidades que "
     "quedaron se reponen con frecuencia a precio bajo, y los que se agotaron vuelven con "
     "errores de precio ocasionales."),
    ("¿Y si me equivoco de talla o de color?",
     "Tienes 14 días naturales de desistimiento desde que recibes el producto, sin necesidad "
     "de justificar el motivo. Y si el producto llega defectuoso, tienes además la "
     "garantía legal."),
    ("¿Compra en Amazon España o en otro país?",
     "En el país donde te lo envíen. La ficha y el precio son distintos en cada mercado, y un "
     "descuento en un país no se puede aprovechar en otro. Si compras desde el extranjero, "
     "puedes acabar pagando más entre aduanas e impuestos que lo que ahorra el descuento."),
]

PAGINA_APROVECHAR = {
    "slug": "como-aprovechar-prime-days.html",
    "miga": "Cómo aprovecharlo",
    "titulo": "Cómo aprovechar el Prime Days 2026: método en siete pasos",
    "desc": ("Cómo aprovechar el Amazon Prime Days 2026 en España: método en siete pasos para "
             "no gastar de más, desde hacer la lista hasta comprobar el precio real antes de "
             "comprar."),
    "alt_img": "Cómo aprovechar el Amazon Prime Days 2026",
    "faq": FAQ_APROVECHAR,
    "cuerpo": f"""{encabezado(
        ("🎯", "Método"),
        "Cómo aprovechar el Prime Days sin gastar de más",
        "El orden de las decisiones importa tanto como las decisiones. Esta es la secuencia "
        "que funciona: siete pasos, en este orden, con el porqué de cada uno.",
        "12 min de lectura",
    )}

  <section class="section">
    <div class="wrap prose">
      <h2>El principio que lo explica todo</h2>
      <p>
        Casi todos los errores de compra en una campaña de descuentos vienen de comprar en el
        orden equivocado. La secuencia natural es ver una oferta, emocionarse y comprar. La
        secuencia que funciona es la inversa: decidir antes qué vas a comprar, y luego ir a
        por ello. Con esa diferencia, la misma oferta que te habría costado 40 euros te
        ahorra 40.
      </p>
      <p>
        Los siete pasos siguientes van en ese orden, y el orden es lo que hace el trabajo.
        Saltarse el primero y empezar por el tercero es la forma más común de perder dinero
        en estas fechas.
      </p>

      <h2>Los siete pasos</h2>
      <ol class="steps">
        <li>
          <strong>Antes: decide si vas a comprar o no.</strong> La pregunta previa a todas
          es si realmente necesitas algo que entre en esta campaña. La falta de intención es
          la causa de casi todas las compras que nadie quiere.
        </li>
        <li>
          <strong>Haz tu lista antes del día 6.</strong> Con la lista hecha, una ganga es
          una decisión. Sin ella, una ganga es una compra que no habías planeado. Escribe los
          productos concretos que quieres, con las tallas y colores exactos, y ten el precio
          habitual de cada uno anotado.
        </li>
        <li>
          <strong>Haz tu cuenta de Prime antes del día 6.</strong> Si ya eres miembro, ya
          tienes la cuenta hecha: pasa al paso 4. Si no lo eres y compras en Amazon con
          regularidad, estos son los días más baratos del año para el envío rápido, y es el
          momento más barato de contratar. Esa decisión se toma con calma, no
          con prisa.
        </li>
        <li>
          <strong>Comprueba tu precio de referencia.</strong> Para cada producto de tu lista,
          anota lo que cuesta hoy y lo que costaba hace un mes. Ese número es el que te dirá
          si una oferta es real o solo un porcentaje grande. Está el método completo en
          <a href="descuentos-reales-o-falsos.html">descuentos reales o falsos</a>.
        </li>
        <li>
          <strong>Compra por el canal, en el momento.</strong> Cada oferta del canal lleva el
          precio anterior y el precio actual, así que la comprobación ya viene hecha, y el
          enlace va directo a la ficha. El precio que pagas es el mismo.
        </li>
        <li>
          <strong>Mira el carrito antes de confirmar.</strong> Es el precio que se cobra, y
          donde se ve el envío. Un envío de 15 euros puede comerse el descuento entero si el
          compra no llega al mínimo de envío gratis.
        </li>
        <li>
          <strong>Aplaza lo que quieras devolver.</strong> Tienes 14 días naturales de
          desistimiento desde que recibes el producto, sin justificar el motivo. Y para los
          descuentos más altos de esta web, mira el
          <a href="https://t.me/GangasOfertasChollos" target="_blank"
          rel="sponsored nofollow noopener">canal de Telegram</a>, que publica cada ganga en
          cuanto la ve.
        </li>
      </ol>

      <h2>El detalle que casi nadie mira: el día después</h2>
      <p>
        El Prime Days tiene {DURACION} de ventana, pero el efecto de la campaña no termina a
        las 23:59 del miércoles. La ventana se cierra y empieza una segunda fase, más corta y
        menos conocida:
      </p>
      <ul>
        <li>
          <strong>Reposición de stock a precio bajo.</strong> Lo que nadie compró durante la
          ventana vuelve al catálogo rebajado durante unos días. Es la mejor segunda
          oportunidad del calendario de descuentos de España.
        </li>
        <li>
          <strong>Errores de precio en los productos agotados.</strong> Las referencias que se
          agotaron vuelven con el precio normal, y en esas es donde aparecen los errores de
          precio.
        </li>
        <li>
          <strong>Cuenta atrás al Black Friday.</strong> La siguiente ventana grande en
          España es el 27 de noviembre. Está todo planificado en la
          <a href="https://gangasofertas.com/BlackFriday/index.html">sección de Black
          Friday</a>.
        </li>
      </ul>

      <h2>Los tres errores que más dinero cuestan</h2>
      {tabla(
          "Tres errores caros durante el Prime Days y cómo evitarlos",
          ["Error", "Por qué cuesta dinero", "Cómo evitarlo"],
          [
              ["Confiar en el porcentaje del cartel",
               "El descuento se calcula sobre un precio de referencia que a veces está "
               "inflado, así que el ahorro real es menor del que parece.",
               "Compara siempre con lo que pagaste tú, no con el precio tachado."],
              ["Comprar sin lista",
               "El catálogo es enorme y está diseñado para generar deseo. Lo que no estaba en tu "
               "lista es dinero gastado.",
               "Escribe tu lista antes del día 6 y ciñete a ella."],
              ["Ignorar el envío",
               "Un envío de 15 euros reduce mucho el ahorro real, sobre todo en compras "
               "pequeñas con descuento grande.",
               "Mira el total del carrito, con envío incluido, antes de confirmar."],
          ],
      )}
      <p class="mt-2">
        Y hay un cuarto error que no aparece en la tabla porque no es un error de cálculo sino
        de momento: <strong>comprar el día 7 a última hora</strong>. Es el día con más
        congestión, con más riesgo de que el envío se vaya de plazo y con menos stock
        disponible. Si vas a comprar, el martes suele ser mejor día que el miércoles.
      </p>

      <h2>El método en una tabla</h2>
      <p>
        Para quien tenga prisa, el resumen. Antes del día 6: lista y comprobación de precios.
        Durante: compra por el canal y mira el carrito. Después: usa los 14 días de
        desistimiento para lo que no quieras.
      </p>
      {tabla(
          "El método del Prime Days en orden, paso a paso",
          ["Momento", "Paso", "Resultado"],
          [
              ["Antes del 6", "Decidir si vas a comprar", "Filtra las compras impulsivas"],
              ["Antes del 6", "Escribir tu lista con precios habituales",
               "Tienes con qué comparar cada oferta"],
              ["Antes del 6", "Tener Prime resuelto", "Envío rápido y ofertas exclusivas"],
              ["Durante", "Comprobar precio de referencia",
               "Sabes si el descuento es real"],
              ["Durante", "Comprar desde el canal", "Entras en la oferta en cuanto sale"],
              ["Durante", "Mirar el carrito con envío", "El ahorro real, no el del cartel"],
              ["Después", "Desistir en 14 días si toca", "No te quedas con lo que no quieres"],
          ],
      )}

      <NOTA_PRECIOS>
      <p class="mt-2">
        Y para enterarte del día que arranque la próxima campaña, sin tener que volver a esta
        página, {tg("apúntate al canal")}.
      </p>
    </div>
  </section>

{CTA_CANAL}

  <section class="section section--alt">
    <div class="wrap prose">
      <h2>Preguntas frecuentes</h2>
      <div class="faq mt-2" id="faq-aprovechar">
{faq_html(FAQ_APROVECHAR, abierta=True)}
      </div>
      <p class="mt-2"><a class="btn btn--ghost" href="faq.html">Ver la FAQ completa →</a></p>
    </div>
  </section>

{relacionados(RELACIONADOS_BASE)}

  <section class="section section--tight">
    <div class="wrap center">
      <p class="muted small">
        El método, aplicado a cada oferta:
        {tg("Únete a @GangasOfertasChollos")}.
      </p>
    </div>
  </section>""",
}


# ─────────────────────────────────────────────────────────────────────────────
#  7. EL CANAL DE TELEGRAM
# ─────────────────────────────────────────────────────────────────────────────

FAQ_CANAL = [
    ("¿Cuánto cuesta el canal?",
     "Nada. Es gratuito, no pide registro y no recoge datos personales. Se entra con un "
     "enlace y ya está. Puedes silenciarlo cuando quieras sin que pase nada."),
    ("¿Cada cuánto se publica?",
     "Cada vez que aparece una ganga, sin horario ni cadencia fija. En plena campaña pueden "
     "ser varias al día, porque las ofertas entran a tandas."),
    ("¿Puedo mirar las ofertas sin unirme?",
     "Sí. El historial del canal es público, así que puedes consultarlo cuando quieras. Y "
     "todo lo que se publica en el canal aparece también en el catálogo de esta web."),
    ("¿El precio me cambia por entrar desde el canal?",
     "No. Los enlaces llevan identificación de afiliado, que sirve para que Amazon sepa de "
     "dónde viene la visita. El precio que pagas es exactamente el mismo."),
]

PAGINA_CANAL = {
    "slug": "canal-telegram-ofertas.html",
    "miga": "Canal Telegram",
    "titulo": "Canal de Telegram de ofertas de Amazon España",
    "desc": ("El canal de Telegram con las ofertas de Amazon España al instante: cada ganga "
             "publicada con precio anterior, precio actual y descuento. Gratis y sin registro."),
    "alt_img": "Canal de Telegram con ofertas de Amazon España al instante",
    "faq": FAQ_CANAL,
    "cuerpo": f"""{encabezado(
        ("📲", "El canal"),
        "El canal donde te enteras antes de que se agote",
        "En una campaña de {DURACION}, la diferencia entre ahorrar y no ahorrar casi nunca "
        "es saber el precio: es llegar a tiempo. Ese es el trabajo del canal.",
        "7 min de lectura",
    )}

  <section class="section section--tight">
    <div class="wrap">
      <div class="keyfacts">
        <h2>El canal en cinco datos</h2>
        <dl>
          <dt>Qué es</dt>
          <dd>Un canal público de ofertas de Amazon España, con cada ganga en cuanto aparece</dd>
          <dt>Coste</dt>
          <dd>Gratis, sin registro y sin datos personales</dd>
          <dt>Formato</dt>
          <dd>Producto, precio anterior, precio actual, descuento y enlace directo</dd>
          <dt>Historial</dt>
          <dd>Público: se puede consultar lo publicado en cualquier momento</dd>
          <dt>Relación con la web</dt>
          <dd>Cada oferta del canal se publica también en el catálogo de esta web</dd>
        </dl>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap prose">
      <h2>Por qué un canal y no una newsletter</h2>
      <p>
        Es la pregunta que más se repite sobre este tipo de canales, y tiene una respuesta
        sencilla: <strong>el tiempo</strong>. Una newsletter llega una vez al día, en el mejor
        de los casos. En una campaña de {DURACION} en la que las ofertas entran a tandas y
        hay stock limitado, una vez al día es tarde.
      </p>
      <p>
        Y hay un segundo motivo, menos evidente: la newsletter te obliga a mirar aunque no
        haya nada que mirar. Un canal de ofertas te avisa solo cuando hay algo. Es la diferencia
        entre una bandeja de entrada llena y una bandeja de entrada con dos cosas.
      </p>

      <h2>Qué se publica, y con qué formato</h2>
      <p>
        El formato es fijo, y es fijo por una razón concreta: para que puedas compararlo de un
        vistazo sin abrir el enlace. Cada oferta lleva siempre:
      </p>
      {tabla(
          "Qué contiene cada mensaje del canal",
          ["Campo", "Qué es", "Para qué sirve"],
          [
              ["Producto", "El nombre del artículo", "Saber qué es antes de abrir nada"],
              ["Precio anterior", "El precio tachado de Amazon",
               "Es el precio de referencia, que puede estar inflado"],
              ["Precio actual", "Lo que cuesta ahora", "Lo que de verdad pagas"],
              ["Descuento", "El porcentaje sobre el precio anterior",
               "Una pista, no una garantía"],
              ["Enlace", "Directo a la ficha de Amazon España", "Comprar sin dar vueltas"],
          ],
      )}
      <p class="mt-2">
        El detalle importante es que se publica <strong>el precio anterior junto al actual</strong>.
        Es lo que permite hacer la comprobación que explica la página de
        <a href="descuentos-reales-o-falsos.html">descuentos reales o falsos</a>, y es
        precisamente lo que casi ningún listado de ofertas te da.
      </p>

      <h2>Qué hay dentro</h2>
      <ul class="checklist">
        <li><strong>Gangas de Amazon Prime Days.</strong> La campaña de octubre y la de verano.</li>
        <li><strong>Errores de precio.</strong> Productos a una fracción de su valor, que duran minutos.</li>
        <li><strong>Descuentos en todas las categorías.</strong> Electrónica, gaming, ropa, higiene, juguetes, papelería.</li>
        <li><strong>Ofertas que ya estaban activas.</strong> Un descuento del 15% que duraba una semana sigue siendo dinero si ibas a comprar.</li>
      </ul>

      <h2>Canal, newsletter o web: qué elegir</h2>
      {tabla(
          "Tres formas de enterarte de las ofertas, y cuándo conviene cada una",
          ["", "Canal de Telegram", "Newsletter diaria", "Catálogo web"],
          [
              ["Latencia", "Inmediata", "Hasta 24 horas", "Minutos"],
              ["Filtro", "Solo lo que merece la pena", "Lo que se ha publicado", "Todo lo publicado"],
              ["Precio anterior a la vista", "Sí", "Depende", "Sí"],
              ["Acceso sin registro", "Sí", "Casi siempre pide correo", "Sí"],
              ["Se puede consultar a posteriori", "Sí, historial público", "No", "Sí"],
              ["Mejor para", "Quien quiere comprar en la campaña", "Quien lee sin prisa",
               "Quien ya sabe lo que busca"],
          ],
      )}
      <p class="mt-2">
        No son excluyentes, y en la práctica el mejor uso es combinarlos: el canal para
        enterarte, la web para decidir con calma. Por eso cada oferta del canal aparece
        también en el <a href="https://gangasofertas.com/general.html">catálogo</a>.
      </p>

      <h2>Cómo entrar, y qué pasa al entrar</h2>
      <p>
        Se entra con un enlace y ya está: no hay formulario, ni correo electrónico, ni
        consentimiento que aceptar. {tg_attr(clase="btn btn--tg btn--lg", texto="Entrar en el canal")}
      </p>
      <p>
        Y para lo que quieras mirar sin recibir nada, el
        <a href="{CANAL_HISTORIAL}" target="_blank"
        rel="sponsored nofollow noopener">historial público del canal</a> funciona sin entrar:
        se puede consultar lo que se ha publicado y cuándo. Es la forma de comprobar si una
        oferta existió de verdad o si alguien la ha exagerado.
      </p>

      <h2>Transparencia sobre los enlaces</h2>
      <p>
        Los enlaces del canal llevan identificación de afiliado de Amazon, lo que significa que
        Amazon sabe que la visita viene de aquí. Dos cosas para que quede claro:
      </p>
      <ul>
        <li><strong>El precio que pagas es el mismo.</strong> La identificación no cambia el precio.</li>
        <li><strong>Participamos en el programa de afiliados.</strong> Si compras a través de nuestros enlaces podemos recibir una comisión, sin coste adicional para ti.</li>
      </ul>
      <p class="mb-0">
        Y por lo mismo, no publicamos nada que no sea una oferta real: si el descuento está
        inflado, lo decimos. La sección de
        <a href="descuentos-reales-o-falsos.html">descuentos reales o falsos</a> explica cómo
        lo comprobamos, y el
        <a href="https://gangasofertas.com/BlackFriday/metodologia.html">apartado de
        metodología</a> explica el proceso completo.
      </p>
    </div>
  </section>

{CTA_CANAL}

  <section class="section section--alt">
    <div class="wrap prose">
      <h2>Preguntas frecuentes sobre el canal</h2>
      <div class="faq mt-2" id="faq-canal">
{faq_html(FAQ_CANAL, abierta=True)}
      </div>
      <p class="mt-2"><a class="btn btn--ghost" href="faq.html">Ver la FAQ completa →</a></p>
    </div>
  </section>

{relacionados(RELACIONADOS_BASE)}

  <section class="section section--tight">
    <div class="wrap center">
      <p class="muted small">
        Gratis, sin registro:
        {tg("entra en @GangasOfertasChollos")}.
      </p>
    </div>
  </section>""",
}


# ─────────────────────────────────────────────────────────────────────────────
#  8. FAQ
# ─────────────────────────────────────────────────────────────────────────────

FAQ_COMPLETA = [
    # Fechas
    ("¿Cuándo es el Amazon Prime Days 2026 en España?",
     "El 6 y el 7 de octubre de 2026, martes y miércoles, durante 48 horas seguidas. Es la "
     "edición de otoño, llamada oficialmente Prime Big Deal Days y Fiesta de Ofertas Prime "
     "en la prensa española. La fecha está confirmada por Amazon en su propio anuncio."),
    ("¿Está confirmada la fecha de octubre de 2026?",
     "Sí. Amazon publicó el anuncio en aboutamazon.com, en español, con el rango de fechas y "
     "las 48 horas de duración. No es una rumorología de prensa: es la fuente primaria."),
    ("¿Cuándo fue la edición de verano de 2026?",
     "Del 23 al 26 de junio de 2026, cuatro días. Fue la primera vez que la campaña de verano "
     "caía en junio en lugar de julio."),
    ("¿Cuándo será la próxima campaña?",
     "La de verano de 2027, con toda probabilidad entre el final de junio y julio. "
     "Históricamente la de otoño cae en la segunda semana de octubre, pero Amazon no publica "
     "la fecha hasta una o dos semanas antes."),
    ("¿A qué hora empieza y acaba?",
     "En España la ventana comercial va del martes 6 al miércoles 7 de octubre, y termina a "
     "las 23:59 hora peninsular. Amazon da la hora de arranque en su huso del Pacífico, así "
     "que puede parecer desplazada según desde dónde mires."),
    # Qué es
    ("¿Qué es exactamente el Amazon Prime Days?",
     "El conjunto de campañas de descuentos que Amazon organiza durante el año, con las "
     "mejores ofertas reservadas a miembros Prime. Desde 2023 son dos al año: la de verano y "
     "la de otoño."),
    ("¿Amazon Prime Days es lo mismo que el Prime Day?",
     "No, aunque están emparentados. El Prime Day es la edición de verano, con ese nombre "
     "desde 2015. El Prime Big Deal Days es la de otoño. El término Amazon Prime Days se usa "
     "para los dos a la vez."),
    ("¿Amazon Prime Days es lo mismo que el Black Friday?",
     "No. Son campañas distintas y de retailers distintos: el Prime Days es de Amazon y el "
     "Black Friday es la fecha en la que liquida todo el comercio. La diferencia práctica "
     "está en la duración: aquí tienes dos días, allí las ofertas buenas duran horas."),
    ("¿Y el Prime Early Access Sale?",
     "Fue el nombre de la campaña de otoño en 2022, el primer año que existió. En 2023 pasó "
     "a llamarse Prime Big Deal Days."),
    # Prime
    ("¿Las ofertas son solo para miembros Prime?",
     "Las más exclusivas sí. Amazon reserva buena parte de los descuentos a miembros Prime, "
     "aunque suelta algunas ofertas al resto de la audiencia. Sin suscripción compras "
     "igual, pero las mejores se te escapan."),
    ("¿Cuánto cuesta Prime en España?",
     "4,99 € al mes o 49,90 € al año, con 30 días de prueba gratuita para nuevas altas que "
     "cumplan los requisitos. Amazon tiene además planes de descuento para estudiantes y "
     "adultos jóvenes, con condiciones propias."),
    ("¿Me sale rentable ser miembro solo por la campaña?",
     "Depende de cuánto compres en la ventana. Si compras una sola vez, la cuota anual no se "
     "amortiza. Si ya compras en Amazon con regularidad, la cuota se paga con el envío "
     "gratuito y las ofertas exclusivas son un extra."),
    # Descuentos
    ("¿Cuánto se puede ahorrar?",
     "Amazon anuncia rebajas en más de 35 categorías. En la práctica, los importes más altos "
     "están en tecnología y los porcentajes más altos en productos que ya eran caros. Un "
     "porcentaje grande no equivale a un ahorro grande."),
    ("¿Cómo sé si un descuento es real?",
     "Comparando con lo que costaba antes, no con el precio tachado. El precio de referencia "
     "que usa Amazon es a veces un pico puntual y no el precio habitual. El método completo "
     "está en la página de descuentos reales o falsos."),
    ("¿Qué es un error de precio?",
     "Un producto que aparece a una fracción de su valor por un fallo del sistema. No tiene "
     "que ver con la campaña, pero cae en las mismas fechas. Suele corregirse en minutos, "
     "así que hay que actuar rápido."),
    ("¿Es legal que Amazon use un precio de referencia inflado?",
     "Es una zona gris muy extendida en el comercio. Amazon aplica su propia norma de precios "
     "de referencia y, técnicamente, el descuento que publica cumple esa norma. Solo sería "
     "ilegal si el precio de referencia no corresponde a una venta real."),
    # Comprar
    ("¿Qué hago si se acaba el stock?",
     "Mirar el día siguiente. Después de la ventana, las unidades que no se vendieron se "
     "reponen con frecuencia a precio bajo, y las que se agotaron vuelven con errores de "
     "precio ocasionales."),
    ("¿Puedo devolver lo que compre?",
     "Sí. Como comprador en España tienes 14 días naturales de desistimiento desde la "
     "recepción del producto, sin necesidad de justificar el motivo. Si además el producto "
     "llega defectuoso, cuentas con la garantía legal."),
    ("¿El envío cambia el ahorro?",
     "Sí, y más de lo que parece. En Prime el envío es gratuito a partir de 25 € en la "
     "mayoría de los pedidos, pero en compras pequeñas un envío de 15 euros puede comerse el "
     "descuento entero. Míralo en el carrito, no en la ficha."),
    ("¿Los descuentos duran más de 48 horas?",
     "No. Cuando acaba la ventana, los precios vuelven a su valor normal en la mayoría de los "
     "casos. Salvo los errores de precio, que tienen su propio ritmo."),
    # Canal
    ("¿Cómo me entero de las ofertas en el momento?",
     "Por el canal de Telegram, que publica cada ganga en cuanto aparece, con el precio "
     "anterior, el precio actual y el enlace directo. Es gratis y no pide registro."),
    ("¿El precio me cambia por entrar desde el canal?",
     "No. Los enlaces llevan identificación de afiliado, que sirve para que Amazon sepa de "
     "dónde viene la visita. El precio que pagas es exactamente el mismo."),
    ("¿Este sitio está afiliado a Amazon?",
     "GangasOfertas.com participa en el Programa de Afiliados de Amazon EU, y puede "
     "recibir una comisión por compras que cumplan los requisitos. El precio no cambia y el "
     "sitio no está afiliado a la empresa ni rastrea sus precios."),
    ("¿Cuándo os enteráis de los precios?",
     "El canal recoge las ofertas que se anuncian en él. No rastreamos Amazon ni controlamos "
     "sus precios: Amazon es quien decide en cada momento si ese precio sigue disponible."),
]

PAGINA_FAQ = {
    "slug": "faq.html",
    "miga": "Preguntas frecuentes",
    "titulo": "Preguntas frecuentes sobre el Prime Days 2026",
    "desc": ("Las preguntas más frecuentes sobre el Amazon Prime Days 2026 en España: fechas, "
             "membresía Prime, descuentos reales, stock, devoluciones y canal de Telegram."),
    "alt_img": "Preguntas frecuentes sobre el Amazon Prime Days 2026",
    "faq": FAQ_COMPLETA,
    "cuerpo": f"""{encabezado(
        ("❓", "Preguntas frecuentes"),
        "Preguntas frecuentes sobre el Prime Days 2026",
        "Veintidós dudas agrupadas por tema: fechas, qué es, membresía Prime, descuentos, "
        "devoluciones y canal. Las mismas que más se repiten en el canal y en los comentarios.",
        "11 min de lectura",
    )}

  <section class="section section--tight">
    <div class="wrap center">
      <p class="muted small">
        <button class="btn btn--ghost btn--sm" type="button" data-faq-toggle
                data-faq-target="faq-secciones" aria-expanded="false">Desplegar todas</button>
      </p>
    </div>
  </section>

  <section class="section">
    <div class="wrap prose">
      <div id="faq-secciones">
      <h2>Fechas</h2>
      <div class="faq">
{faq_html(FAQ_COMPLETA[:5])}
      </div>

      <h2>Qué es</h2>
      <div class="faq">
{faq_html(FAQ_COMPLETA[5:9])}
      </div>

      <h2>Membresía Prime</h2>
      <div class="faq">
{faq_html(FAQ_COMPLETA[9:12])}
      </div>

      <h2>Descuentos y precios</h2>
      <div class="faq">
{faq_html(FAQ_COMPLETA[12:16])}
      </div>

      <h2>Comprar durante la campaña</h2>
      <div class="faq">
{faq_html(FAQ_COMPLETA[16:20])}
      </div>

      <h2>El canal y este sitio</h2>
      <div class="faq">
{faq_html(FAQ_COMPLETA[20:])}
      </div>
    </div>

      </div>
  </section>

  <section class="section section--alt">
    <div class="wrap prose">
      <h2>¿Falta alguna pregunta?</h2>
      <p>
        Si no está aquí, casi siempre la respuesta es la misma que la de esta página: entra en
        el canal y míralo en directo. {tg("@GangasOfertasChollos")} publica cada oferta en
        cuanto aparece, y el
        <a href="{CANAL_HISTORIAL}" target="_blank"
        rel="sponsored nofollow noopener">historial del canal</a> es público para que puedas
        consultarlo cuando quieras.
      </p>
      <p class="mb-0">
        Y para el contexto general de la campaña, están la guía de
        <a href="index.html">qué es el Prime Days</a>, el
        <a href="fechas-amazon-prime-days.html">calendario de fechas</a> y el
        <a href="como-aprovechar-prime-days.html">método en siete pasos</a>.
      </p>
    </div>
  </section>

{NOTA_PRECIOS}

{relacionados(RELACIONADOS_BASE)}

  <section class="section section--tight">
    <div class="wrap center">
      <p class="muted small">
        ¿Prefieres la respuesta en el móvil? {tg("Únete a @GangasOfertasChollos")}.
      </p>
    </div>
  </section>""",
}


# ─────────────────────────────────────────────────────────────────────────────
#  ESCRITURA
# ─────────────────────────────────────────────────────────────────────────────

PAGINAS = [
    PAGINA_INDEX,
    PAGINA_QUE_ES,
    PAGINA_FECHAS,
    PAGINA_OFERTAS,
    PAGINA_DESCUENTOS,
    PAGINA_APROVECHAR,
    PAGINA_CANAL,
    PAGINA_FAQ,
]


def schema_de(pagina: dict) -> dict:
    """Datos estructurados de una pagina, en un solo @graph."""
    grafo = {
        "article": schema_article(
            pagina["titulo"], pagina["desc"], pagina["slug"],
            PUBLICADO, MODIFICADO,
        )
    }
    if pagina.get("faq"):
        grafo["faq"] = schema_faq(pagina["faq"])
    return grafo


def escribir(pagina: dict) -> None:
    html = render(
        titulo=pagina["titulo"],
        desc=pagina["desc"],
        slug=pagina["slug"],
        miga=pagina["miga"],
        cuerpo=pagina["cuerpo"],
        schema=schema_de(pagina),
        alt_img=pagina["alt_img"],
    )
    destino = DESTINO / pagina["slug"]
    # newline="" para no traducir los \n a CRLF: PrimeDays va con LF (ver
    # .gitattributes) y mezclarlos ensucia los diffs.
    destino.write_text(html, encoding="utf-8", newline="")
    palabras = len(html.split())
    print(f"  {pagina['slug']:<38} {palabras:>5} palabras")


def main() -> None:
    print(f"== Seccion Amazon Prime Days -> {DESTINO} ==\n")
    for pagina in PAGINAS:
        escribir(pagina)
    print(f"\n{len(PAGINAS)} paginas generadas.")


if __name__ == "__main__":
    main()