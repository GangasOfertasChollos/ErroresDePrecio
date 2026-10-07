# GangasOfertas.com

Web de ofertas Amazon España y bot de Telegram. Se publica en
**https://gangasofertas.com** (GitHub Pages detrás de Cloudflare).

Un bot escucha el canal de Telegram, extrae el título, el precio y el enlace de
cada oferta, la clasifica por categoría y la guarda en `data/*.json`. La web lee
esos JSON y los muestra en un catálogo por categorías.

> **Qué es y qué no es este proyecto.** No rastrea Amazon ni monitoriza sus
> precios. Recopila las ofertas que se publican en el canal de Telegram; Amazon
> es quien decide en cada momento si ese precio sigue disponible.

## Estructura

```
bot.py                 Bot de Telethon
categorias.json        Diccionario de palabras clave por categoría
data/*.json            Ofertas (generados por el bot)
assets/style.css       Estilos compartidos por todas las páginas
assets/app.js          Carga y render del catálogo (+ JSON-LD dinámico)
assets/icono-tg.css    Componentes comunes a las dos paletas (icono, reduced-motion)
assets/icono-tg.jpg    Icono del canal (esquina superior derecha)
index.html             Portada
<slug>.html            Páginas de catálogo, una por categoría
BlackFriday/           Sección Black Friday 2026 (17 páginas, CSS y assets propios)
PrimeDays/             Sección Amazon Prime Days 2026 (8 páginas, CSS y assets propios)
plantilla_comun.py     Marcado compartido: menú, icono y pie
plantilla_prime_days.py  Equivalente de plantilla_comun.py para PrimeDays/
generar_*.py           Generadores de HTML y sitemap
tests/                 Pruebas del bot, del front y del sitio
CNAME                  Dominio personalizado de GitHub Pages: gangasofertas.com
.gitattributes         CRLF en la raíz, LF en BlackFriday/
```

## Diseño

Dos hojas de estilo, las dos **de fondo claro**:

| | Fichero | Acento |
|---|---|---|
| Sitio principal | `assets/style.css` | naranja Amazon (`--naranja-texto` para texto) |
| Sección Black Friday | `BlackFriday/assets/css/style.css` | negro (`--accent`) |
| Sección Prime Days | `PrimeDays/assets/css/style.css` | negro (`--accent`) + cian `--cyan` para enlaces |

El negro se usa como elemento de marca —barra superior, botones, barra de
marca— sobre fondo blanco. Los colores de marca que no llegan a 4.5:1 sobre
blanco (como el naranja `#ff9900`, que da 2.1:1) están **restringidos a bordes
y rellenos**; para texto se usa el tono oscuro equivalente (`--naranja-texto`).

Todo el color pasa por variables CSS. Si quieres cambiar la paleta, edita el
bloque `:root` de cada hoja y no toques las reglas.

Lo que **no** depende de la paleta vive en `assets/icono-tg.css`, que las dos
hojas cargan: así el icono del canal y la regla de `prefers-reduced-motion`
tienen una sola definición en lugar de una por hoja.

El icono del canal (`assets/icono-tg.jpg`) se inserta **dentro del div que
contiene el `<h1>`** de cada página, no flotando sobre el viewport. Hay cuatro
estructuras de cabecera distintas y todas están contempladas en el CSS:

| Página | Contenedor |
|---|---|
| Portada | `<header class="hero"><div>` |
| Catálogos, SEO, ofertas en vivo | `<header class="cabecera"><div class="wrap">` |
| Secciones Black Friday y Prime Days | `<header class="site-header"><div class="wrap nav">` |
| 404 | `<main class="error404">` |

Esos contenedores son `position: relative`, así que el icono se coloca con
`position: absolute` en su esquina superior derecha. Si añades una cabecera
nueva, añade su selector a esa lista en `assets/icono-tg.css` o el icono
saldrá flotando sobre el contenido.

`plantilla_comun.py` es la única fuente del menú, del icono y del pie. Los
tres generadores la importan, de modo que regenerar las páginas no deshace los
cambios de maquetación y los menús no divergen entre sí.

> `404.html` usa **rutas absolutas** a propósito: GitHub Pages lo sirve a
> cualquier profundidad (por ejemplo `/BlackFriday/no-existe.html`), donde una
> ruta relativa como `general.html` apuntaría a `/BlackFriday/general.html` y
> no existiría. Los validadores no lo detectan porque resuelven siempre contra
> la raíz del repositorio.

La sección Black Friday tiene su propia hoja porque su diseño original era
oscuro; se migró a claro cambiando `--bg` a `#ffffff` y `--accent` a negro, y
ajustando los ~29 colores que estaban fijados en las reglas.

## Secciones de campaña

Hay dos secciones que cubren campañas concretas, y son hermanas: mismo
generador de contenido, mismo tipo de página, mismo patrón de enlazado, y se
enlazan mutuamente desde el menú porque el lector es el mismo.

| | Black Friday | Prime Days |
|---|---|---|
| Campaña | 27 de noviembre de 2026 | 6 y 7 de octubre de 2026 |
| Generador | `BlackFriday/` (HTML ya generado) | `generar_prime_days.py` |
| Plantilla | incluida en la sección | `plantilla_prime_days.py` |
| Análisis SEO | `BlackFriday/docs/SEO-STRATEGY.md` | `PrimeDays/docs/SEO-STRATEGY.md` |

**Sobre las fechas.** Cada sección publica la fecha de su campaña y el
historial, pero **solo los datos que tienen fuente**, y la fuente se enlaza en
la propia página. La sección Prime Days se corrigió por esto: un borrador
anterior afirmaba que Amazon no había anunciado la fecha de octubre de 2026,
que era cierto cuando se escribió y dejó de serlo antes de publicarse. El
principio no cambió (no inventar fechas); lo que cambió es el dato. Cuando
Amazon confirme la edición de 2027, se editan las constantes `FECHA_INICIO_2026`
y `FECHA_FIN_2026` de `generar_prime_days.py` y se vuelve a generar.

> La sección Prime Days marca la campaña como «en marcha» y lleva una cuenta
> atrás. **Eso es correcto el 6 y el 7 de octubre y falso después.** Está todo
> en `cuenta_atras()` y en el hero de `PAGINA_INDEX`, y las fechas que aparecen
> en la tabla del sitemap (`daily`) deben bajar a `weekly` el 8 de octubre.

### Tablas anchas dentro de `.prose`

La columna de texto mide 74ch. Una tabla de cuatro o cinco columnas dentro de
ella parte cada celda en tres o cuatro palabras y deja de ser legible, así que
`tabla(..., ancho_completo=True)` la saca a un `.wrap` completo. Las tablas de
dos columnas caben sin problema dentro de `.prose`.

## Dominio

`CNAME` fija `gangasofertas.com` como dominio de GitHub Pages, así que **todos
los canonical, `og:url` y el `sitemap.xml` deben apuntar a
`https://gangasofertas.com/`**. La URL de GitHub (`*.github.io`) queda
despublicada: si alguna vez se vuelve a subir, Google verá dos versiones del
mismo contenido.

El host canónico es el **apex sin `www`**. `www.gangasofertas.com` se redirige al
apex con una regla de Cloudflare, porque GitHub Pages solo tiene verificado el
apex y proxiar `www` devolvía un error 522.

## Puesta en marcha

```bash
pip install -r requirements.txt
cp .env.example .env      # rellena API_ID, API_HASH y TELEGRAM_CHANNEL
python bot.py
```

La primera vez Telegram pedirá un código de confirmación: el bot lo avisa por
consola y por `bot.log`. Si ejecutas el bot como servicio y se cuelga esperando
ese código, borra `sesion_json_bot.session` y autorízalo en una terminal
interactiva.

### El catálogo se reconstruye en cada arranque

Al arrancar, el bot hace tres cosas, en este orden:

1. **Lee** los últimos `BACKFILL_LIMIT` (100) mensajes del canal.
2. **Borra todas las ofertas y todas las imágenes**: los JSON de `data/` se
   vacían y `data/images/` se elimina entero.
3. **Vuelve a publicar** esas ofertas en los JSON, ya saneadas, y las sube a
   git.

Lo publicado es por tanto siempre el estado actual del canal: no se acumulan
ofertas caducadas ni retoques a mano, y un JSON corrupto se regenera solo. Lo
mismo pasa al **reconectar** tras una caída de conexión, porque durante el corte
las ofertas se pierden y `events.NewMessage` solo dispara con lo que llega
después.

Detalles que conviene tener presentes:

- **El borrado va después de leer el historial, nunca antes.** Si Telegram
  falla, el canal está vacío o no se puede acceder, se conserva el catálogo
  anterior en lugar de dejar la web vacía y sin repuesto. Hay pruebas de esto
  en `tests/test_flujo.py`.
- **`MAX_OFERTAS` no puede quedar por debajo de `BACKFILL_LIMIT`.** Ambos valen
  100 por defecto, así que de los 100 mensajes leídos se publican hasta 100
  ofertas. Si alguien deja `MAX_OFERTAS` por debajo, el recorte de
  `_guardar_en_archivo` tiraría ofertas que sí se han leído del canal y el
  catálogo recién reiniciado saldría incompleto solo por el límite: el bot lo
  detecta al arrancar, avisa por log y sube `MAX_OFERTAS` a `BACKFILL_LIMIT`.
- **Se descarta lo que no se puede publicar.** Una oferta sin enlace de Amazon,
  sin título o sin precio no llega a los JSON: serían tarjetas rotas o sin
  información. Cada descarte queda anotado en el log con el motivo.

### Al terminar, el bot se verifica

Al cerrar el backfill, `bot.py` comprueba por log lo que de verdad importa al
arrancar, y avisa si algo no cuadra:

```
[VERIFICACION] general.json=100 ofertas (procesadas: 100, leidas del canal: 100); por categoria -> general=100, higiene-cuidado-personal=8, ...
[VERIFICACION] general.json completo: 100/100 ofertas del canal
[VERIFICACION] Cambios publicados en origin/main. GitHub Pages tardara unos minutos en servirlos.
```

- Si `general.json` se queda corto, dice **cuántas** ofertas faltan de las leídas
  y recuerda mirar `MAX_OFERTAS`.
- Si el `git push` falla, avisa de que **la web sigue mostrando el catálogo
  anterior**, en lugar de dejar un JSON correcto en local que nadie ve.
- Si `AUTO_PUBLICAR=0`, avisa de que los JSON son correctos pero la web no se
  actualizará hasta que alguien haga `git push` a mano.

No aborta nunca: el bot sigue escuchando y recogiendo ofertas nuevas aunque el
backfill haya quedado corto.

Con `REINICIAR_CATALOGO=0` se conserva el comportamiento anterior: los JSON se
van llenando de forma incremental y el backfill solo rellena huecos.

## Publicación

La web se sirve desde GitHub Pages, así que los cambios en `data/` tienen que
llegar al repositorio. Hay dos formas:

**Automática (recomendada).** Actívala en `.env`:

```bash
AUTO_PUBLICAR=1
```

El bot hace `git add data/`, `commit` y `push` por su cuenta, agrupando las
subidas cada `PUBLICAR_CADA_SEGUNDOS` (60 por defecto) para no crear un commit
por oferta. Necesita git instalado, el remoto configurado y credenciales de
push (por ejemplo un token o una clave SSH).

**Manual.** Si prefieres no dar acceso al bot:

```bash
git add data/
git commit -m "Actualizar ofertas"
git push
```

## Regenerar el HTML

Las páginas de catálogo y las páginas SEO se generan con scripts para que
todas compartan estructura y estilos. Si cambias una sección, edita el
generador y vuelve a lanzarlo, **en este orden**:

```bash
python generar_categorias.py    # 7 páginas de catálogo
python generar_seo.py           # 4 páginas SEO
python generar_prime_days.py    # 8 páginas de Prime Days
python generar_sitemap.py       # sitemap.xml (verifica que las URLs existen)
```

> Los cuatro generadores se ejecutan siempre en ese orden y en una sola pasada.
> `generar_categorias.py` es la fuente de las 7 páginas de catálogo: si algo
> las modifica a mano, se pierde al regenerarlas. Por eso las páginas se
> regeneran, no se parchean.

## Imágenes y formato de los mensajes

Las ofertas no guardan imágenes en disco: el campo `image` guarda una **URL**.
Por eso `data/` solo contiene los siete JSON de ofertas y ningún binario.

La miniatura se obtiene con *link unfurling*, el mismo mecanismo que usan
Facebook o WhatsApp al pegar un enlace: se pide la página pública del mensaje
(`https://t.me/<canal>/<id>`) y se lee su etiqueta `og:image`. Se elige esa vía
porque es la única que funciona:

| Vía | Resultado |
|---|---|
| `og:image` de `t.me/canal/ID` | **Sí.** ~0,8 s, sin CAPTCHA, imagen real |
| `og:image` de la ficha de `amazon.es` | No: devuelve una página de CAPTCHA a cualquier cliente automatizado |
| Deducir la URL de la imagen del ASIN | No: el nombre del fichero no es derivable (devuelve un GIF de 1×1) |

> Antes el bot bajaba cada foto a `data/images/` y guardaba la ruta local. Eso
> dejaba 35 MB de binarios en el repositorio y rutas que el navegador no puede
> resolver, así que el paso se eliminó del todo: `extraer_imagen` solo devuelve
> URLs. `limpiar_imagenes_huerfanas()` avisa si ese directorio vuelve a
> aparecer.

Las URLs obtenidas se cachean en memoria, así que el backfill no repite
peticiones. Si el bot no está en el canal no puede construir la URL pública, y
la oferta se publica sin imagen.

Los mensajes del canal tienen una estructura fija que el bot aprovecha, porque
es más fiable que buscar números sueltos:

```
🩹 VANSKIVA – Parche de silicona para cicatrices 4 cm x 1,5 m

💸 Ahora: 13,99 €
🏷️ Antes: 25,99 €
📉 Descuento: -46 %
💰 Ahorras: 12,00 €
🔗

https://www.amazon.es/dp/B0GCQX9YY4?tag=gangas054-21
```

De ahí se extraen el título, el precio de oferta (`price`), el precio original
(`old_price`), el descuento (`discount`) y el enlace. Se aceptan tanto el
enlace directo como los acortadores `amzn.to`, `amzn.eu` y `amzlink.to`.

### Los campos que van a schema.org

`description`, `brand`, `gtin` y `mpn` se publican tal cual como
`itemprop`/JSON-LD, así que un valor inventado es información falsa en los
resultados de Google. De ahí las reglas:

- **`gtin`** solo se rellena con un GTIN de verdad (EAN-8, UPC-A o EAN-13)
  **validado por su dígito de control**. Los hashtags se quitan antes de
  buscar, para que un `#12345678` no se cuele.
- **`mpn`** (código de pieza) va en su **propia** propiedad, no dentro de
  `gtin`: un MPN como `RLC-810A` no es un código de barras. Antes el fallback
  a MPN estaba dentro de `gtin` y **ninguno de los 28 valores que había en
  `data/` era un GTIN**: todos eran hashtags (`Blackfriday26`) o códigos de
  pieza (`HC5880`, `6-Cores`), y se publicaban como `itemprop="gtin"`.
  Se busca fuera de los enlaces, porque el tag de afiliado del propio bot
  (`?tag=gangas054-21`) también tiene guion y dígitos, y también fuera de los
  hashtags.
- **`description`** descarta las líneas que solo son precios
  (`"16,91 € (antes 29,99 €)"`), las etiquetas del canal (`|#Chollos|`, las
  internas como `PRECIO OFERTA`), los enlaces en markdown con la CTA de otro
  bot (`[📉 Miss Avisos...](https://t.me/MissAvisosbot?start=...)`, que se borran
  enteros, con su texto y su URL) y las llamadas a la acción de otros canales
  (`👉 Míralo en Ofertitas.es`). El precio ya vive en sus propios campos.
- **`brand`** descarta los emojis que se cuelan (`⌨️ GXTrust`) y los
  fragmentos que no son una marca (`"Alfombrilla de"`, `"Neceser"`); si no hay
  marca, el campo queda vacío y el frontend lo omite. Tampoco se publica
  `OFERTA AMAZON`, que es el marcador de posición del bot, no una marca.

### El título nunca es el marcador de posición

Cuando un mensaje del canal no trae un título real, `extraer_titulo` devuelve
`Oferta Amazon` y la oferta se **descarta**. La comparación es
*case-insensitive* porque el canal lo escribe en mayúsculas: con la comparación
exacta, 22 ofertas se publicaban con `title` y `brand` = `"OFERTA AMAZON"`
(14 de 98 en `general.json`, y 6 de 12 —la mitad— en `moviles-electronica.json`).

Cuando un dato no está, el campo va vacío. Es preferible a inventarlo.

## Comprobar los cambios

```bash
python tests/test_bot.py            # extracción, clasificación, escritura, límites
python tests/test_formato_canal.py  # formato real de los mensajes del canal
python tests/test_unfurl.py         # unfurling y caché (red simulada)
python tests/test_flujo.py          # extremo a extremo: mensaje -> JSON -> página
node tests/test_app.js              # render, escapado, whitelist de URLs, JSON-LD
python tests/validar_sitio.py       # enlaces, JSON-LD, HTML, sitemap, afirmaciones
python tests/validar_contenido.py   # volumen y limpieza del copy de cada categoría
python tests/validar_orden.py       # orden ofertas→texto, clases y JSON-LD
python tests/test_publicar_html.py  # el bot regenera y sube el HTML correcto
```

`validar_servido.py` comprueba lo que un crawler recibe de verdad por HTTP, no lo
que hay en disco. Acepta un dominio como argumento:

```bash
python tests/validar_servido.py                          # contra gangasofertas.com
python tests/validar_servido.py http://localhost:8124     # contra un servidor local
```

Contra el sitio desplegado añade dos comprobaciones que en local no tienen
sentido: que las 45 URLs del sitemap responden de verdad (una URL que solo
existe en el repositorio no la encuentra Google) y que el dominio y sus
variantes `www` / `http` resuelven a la misma canónica. Reintenta cada
petición tres veces, porque sin eso un corte de red al leer `general.html`
(~240 KB) se lee como un sitio caído.

`test_publicar_html.py` comprueba que el bot sube el HTML regenerado y que la
lista de páginas no toca `BlackFriday/` ni `PrimeDays/`.

## Generar las páginas

Las páginas de catálogo y las guías no se escriben a mano: el texto vive en
`contenido_categoria.py` y `guias.py`, y los generadores son la única fuente
del HTML.

```bash
python generar_categorias.py   # las 7 páginas de catálogo
python generar_guias.py        # guias.html + 6 artículos
python generar_sitemap.py      # sitemap.xml (verifica que cada URL exista)
```

`generar_categorias.py` lee `data/<slug>.json` y **escribe las ofertas en el
HTML**, no solo en el JSON. Antes las páginas se generaban con un
`<section id="ofertas">` vacío que `app.js` rellenaba con `fetch()`: lo que
recibía un crawler eran cuarenta palabras y ni una sola oferta. Ahora el HTML
llega con las tarjetas ya escritas y `app.js` solo refresca los datos; si el
`fetch` falla, no borra lo que ya hay.

Si se toca la lógica de precios hay que tocar las dos copias: `precios()` en
`generar_categorias.py` y `preciosDe()` en `assets/app.js`. Si divergieran, la
página cambiaría sola al cargar el script.

### El bot regenera el HTML al publicar

Antes el bot escribía los JSON y los subía, pero el HTML se generaba a mano.
Como las páginas se sirven con las ofertas escritas dentro, el repositorio
acababa con los JSON de una tanda y el HTML de la anterior: las ofertas nuevas
no llegaban al crawler hasta que alguien se acordaba de regenerar.

`publicar_en_git()` ahora ejecuta los tres generadores antes del `git add` y
los incluye en el mismo commit:

```
data/*.json + generar_categorias.py + generar_guias.py + generar_sitemap.py
  -> un solo commit -> un solo push
```

Detalles que importan:

- El HTML se regenera **antes** de comprobar si hay cambios. Si solo ha
  cambiado una oferta, el HTML es lo único que va a diferir, y mirando los
  cambios primero el commit saldría vacío.
- Las páginas se listan una a una (`_paginas_generadas()`) en vez de usar
  `git add *.html`, porque un pathspec con comodín también alcanzaría
  `BlackFriday/` y `PrimeDays/`.
- Si un generador falla, **no se aborta la subida**: es preferible subir los
  JSON con el HTML viejo a no subir nada. El fallo queda en el log con la salida
  del generador.
- Se puede desactivar con `REGENERAR_HTML=0`, que devuelve el bot al
  comportamiento anterior (solo `data/`).

### Orden dentro de una página de categoría

```
h1 (cabecera)
  h2  Móviles y electrónica en Amazon España   ← cuenta de ofertas
      [grid de tarjetas]
  h2  Ofertas de móviles y electrónica en Amazon España
      h3  Móviles: el precio oficial casi nunca es el precio real
      h3  Cómo elegir y cuándo comprar
      h3  Preguntas frecuentes
```

El listado va **antes** que el texto. Quien llega a una página de categoría
busca precios, y 600-800 palabras antes del primer producto hacen que se vaya.

No cuesta SEO: un crawler recorre la página entera, así que el texto se sigue
leyendo e indexando igual, y el `ItemList` del JSON-LD no depende de la posición.
Lo que sí cambia es la UX, y en una página transaccional manda la intención de
compra. El texto editorial queda como respuesta larga para quien la busca.

`tests/validar_orden.py` fija el orden, las clases del CSS nuevo y que el
JSON-LD siga declarando `ItemList` y `FAQPage`.

Y los de la sección Prime Days:

```bash
python tests/validar_prime_days.py          # texto, alfabetos, estructura por página
python tests/validar_prime_days_enlaces.py  # enlaces, JSON-LD, FAQ vs schema, rel del canal
python tests/validar_prime_days_faq.py      # el toggle despliega todos los <details>
python tests/validar_prime_days_movil.py    # desborde horizontal, viewport, tokens largos
```

> `validar_sitio.py` recorre `RAIZ.glob("*.html")`, así que **no baja a los
> subdirectorios**: ni ve `BlackFriday/` ni ve `PrimeDays/`. Por eso la sección
> tiene sus propios validadores, que sí resuelven las referencias relativas
> contra el directorio de cada HTML.

Las pruebas no necesitan credenciales de Telegram ni conexión: sustituyen el
cliente y el `fetch` por dobles de prueba y trabajan sobre copias en un
directorio temporal. `data/` puede estar vacío; en ese caso `test_app.js` usa
ofertas de ejemplo.

## Configuración

Todo en `.env` (ver `.env.example`):

| Variable | Por defecto | Para qué |
|---|---|---|
| `API_ID` / `API_HASH` | — | Credenciales de Telegram (obligatorias) |
| `TELEGRAM_CHANNEL` | `@GangasOfertasChollos` | Canal que se escucha |
| `MAX_OFERTAS` | `100` | Ofertas guardadas por JSON. Si queda por debajo de `BACKFILL_LIMIT`, el bot lo sube al arrancar |
| `BACKFILL_LIMIT` | `100` | Mensajes del histórico a recuperar al arrancar (`0` desactiva) |
| `REINICIAR_CATALOGO` | `1` | Borrar ofertas e imágenes al arrancar y reconstruirlas desde el canal (`0` conserva lo que haya) |
| `USAR_UNFURL` | `1` | Obtener la miniatura desde la página pública del mensaje (`0` desactiva) |
| `TIMEOUT_UNFURL` | `15` | Segundos de espera al pedir la miniatura |
| `AUTO_PUBLICAR` | `0` | Publica `data/` en git automáticamente |
| `GIT_REMOTO` / `GIT_RAMA` | `origin` / `main` | Destino del push |
| `PUBLICAR_CADA_SEGUNDOS` | `60` | Frecuencia máxima de publicación |

## Categorías

Las palabras de clasificación se editan en `categorias.json`. La búsqueda
ignora tildes y mayúsculas, y las coincidencias son por palabra completa, así
que `pantalón` y `pantalon` funcionan igual. Cuando dos categorías empatan,
gana la que aparece antes en el archivo.
