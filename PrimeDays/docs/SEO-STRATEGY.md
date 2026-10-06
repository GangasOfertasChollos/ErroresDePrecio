# Estrategia SEO — Amazon Prime Days 2026 · GangasOfertas.com

**Dominio:** `https://gangasofertas.com/PrimeDays/`
**Fecha del análisis:** 6 de octubre de 2026 (día 1 de la campaña)
**Stack:** HTML/CSS/JS estático, sin dependencias, sin build
**Generador:** `generar_prime_days.py` · **Plantilla:** `plantilla_prime_days.py`

---

## 1. El dato que cambia la estrategia

Amazon **confirmó por escrito** que la campaña de otoño va del **martes 6 al miércoles 7
de octubre de 2026**, 48 horas seguidas. La fuente es su propio despacho, en la versión
en español:

> «Prime Big Deal Days regresa del 6 al 7 de octubre: Esto es lo que puedes esperar»
> — aboutamazon.com/news/retail/amazon-prime-big-deals-day-2026-cuando-octubre-6-7

De ahí salen: las fechas, las 48 horas, las más de 35 categorías y los 22 países
participantes (España incluida). La edición de verano (23 al 26 de junio de 2026) sale del
anuncio equivalente.

### Por qué esto importa más que cualquier otra decisión

Un borrador anterior de esta sección afirmaba que *«Amazon no ha anunciado la fecha»*. Al
6 de octubre eso ya era falso, y era el peor error posible en una página de ofertas:

- manda a la gente a comprar un día que no hay descuento,
- la gente no vuelve y el topical se pierde para siempre,
- mientras tanto los competidores sí publican la fecha correcta y se llevan el clic.

La regla que se mantiene **no** es «no publicar fechas», que era una reacción defensiva a
un dato que ya no existía, sino:

> **Una fecha solo se publica si tiene fuente, y la fuente se enlaza.**

Las fechas históricas van siempre con su año. Las de 2026 son las dos únicas publicadas, y
las dos son las que tienen anuncio. El análisis completo de esto está en la cabecera de
`generar_prime_days.py`.

---

## 2. Competidores: fortalezas, debilidades y el hueco

Analizados en la SERP española de «amazon prime days 2026», «fiesta de ofertas prime» y
«prime big deal days».

| Competidor | Tipo | Fortaleza | Debilidad (nuestro ángulo) |
|---|---|---|---|
| **Xataka** | Editorial tech | Fecha correcta, autoridad alta, responde rápido a la fecha | Pieza de noticias: se escribe una vez y no se actualiza. En una ventana de 48 h un artículo del martes ya no dice nada válido el miércoles. Mucho widget de Amazon, cero metodología |
| **Hola** | Lifestyle/moda | Enfoque de temporada, buen gancho visual | Prioriza moda; no cubre electrónica ni la parte técnica del método. Tampoco es un canal de avisos |
| **ELLE** | Lifestyle | Da el rango exacto (00:00 del 6 a 23:59 del 7) | Contenido editorial sin ninguna oferta verificable. Sin canal, sin forma de enterarse en el momento |
| **La Vanguardia (comprar)** | Prensa de compras | Menciona las ofertas anticipadas desde septiembre y el precio de Prime en España | Noticia: caduca el día siguiente. Una sola pieza, sin seguimiento durante la campaña |
| **AS.com / Showroom** | Affiliate de listas | muchísimos enlaces, «hasta 83%», mucho volumen | **Listas estáticas**: se quedan vacías en horas. El % gigante sin comprobar que el ahorro sea real. Puro afiliado |
| **idealo** | Comparador | El mejor producto del sector (alertas de precio reales) | **Se contradice**: en el mismo texto dice que las fechas están confirmadas para el 6 y 7 de octubre y también que «a falta de confirmación oficial se prevé en octubre». El objetivo es que te registres en su alerta |
| **Consumer Reports** | Testing | Análisis de calidad de producto, muy buen sesgo anti-amazonazo | Solo en inglés, no compite en la SERP española |
| **Amazon (oficial)** | Fuente primaria | Las fechas y el número de categorías, sin intermediarios |Escrito para el mercado de EE. UU.: precios en dólares, hora del Pacífico. **No dice si un descuento es real ni si es inflado** |

### El hueco, resumido

Ningún competidor ocupa **información en vivo + descuento verificado + canal de Telegram**.

1. Todos son **estáticos**. Publican una lista el día que arranca la campaña; a las 48 h
   esa lista es un documento muerto, y sus artículos no se refrescan.
2. Ninguno **distingue el descuento real del inflado**. Repiten el «hasta 80%» de Amazon sin
   comprobar el precio de referencia. Es el hueco de calidad más grande del tema.
3. Ninguno cubre **los tres nombres** del evento. Cada medio usa uno: Xataka y Hola,
   «Fiesta de Ofertas Prime»; Amazon, «Prime Big Deal Days»; el resto, «Prime Day». Nadie
   los cubre a la vez, así que quien busca cualquiera de los tres no encuentra una página
   que le resuelva la duda.
4. Ninguno envía a un canal con **historial público**, donde se pueda comprobar que la
   oferta existió y cuándo se anunció.

Nuestra posición: **la única sección que da la fecha con su fuente, explica qué baja de
verdad y avisa en el momento**, con el catálogo vivo como respaldo para mirar sin recibir
nada.

---

## 3. Mapa de keywords

| Cluster | Keyword principal | Página | Intención |
|---|---|---|---|
| A — Head | `amazon prime days 2026` | `index.html` | informativa |
| A | `amazon prime days españa` | `index.html` | informativa |
| B — Nombre oficial ES | `fiesta de ofertas prime 2026` | `index.html`, `que-es` | informativa |
| B | `prime day 2026 españa` | `index.html` | informativa |
| C — Fechas | `fechas prime days 2026` | `fechas-amazon-prime-days.html` | informativa |
| C | `cuándo es el prime day 2026` | `fechas-amazon-prime-days.html` | informativa |
| C | `calendario ofertas amazon 2026` | `fechas-amazon-prime-days.html` | informativa |
| D — Comercial | `ofertas prime days 2026` | `ofertas-prime-days-2026.html` | transaccional |
| D | `descuentos amazon octubre 2026` | `ofertas-prime-days-2026.html` | transaccional |
| D | `ofertas amazon por categorías` | `ofertas-prime-days-2026.html` | transaccional |
| E — Calidad / método | `descuentos falsos amazon` | `descuentos-reales-o-falsos.html` | informativa |
| E | `cómo saber si un descuento es real` | `descuentos-reales-o-falsos.html` | informativa |
| E | `errores de precio amazon octubre` | `descuentos-reales-o-falsos.html` | transaccional |
| F — Estrategia | `cómo aprovechar prime days` | `como-aprovechar-prime-days.html` | informativa |
| F | `consejos ofertas amazon octubre` | `como-aprovechar-prime-days.html` | informativa |
| G — Canal | `canal telegram ofertas amazon` | `canal-telegram-ofertas.html` | navegacional |
| H — Educación | `qué es amazon prime days` | `que-es-amazon-prime-days.html` | informativa |
| H | `prime days vs black friday` | `que-es-amazon-prime-days.html` | comparativa |
| I — FAQ | preguntas largas de tail | `faq.html` | informativa |

**Terminos sin cobertura de los competidores, atacados aquí:**

| Término | Dificultad | Página |
|---|---|---|
| `fiesta de ofertas prime` + `amazon prime days` a la vez | Baja | `index.html` (tabla de nombres) |
| `historial prime day por año` | Baja | `fechas-amazon-prime-days.html` (tabla de 12 ediciones) |
| `descuentos reales o falsos prime days` | Baja | `descuentos-reales-o-falsos.html` |
| `prime days 48 horas diferencia black friday` | Baja | `que-es-amazon-prime-days.html` (comparativa) |
| `qué pasa el día después del prime day` | Baja | `fechas-amazon-prime-days.html` |

---

## 4. Arquitectura

```
/PrimeDays/
├── index.html                              ← pillar (3.950 palabras)
├── que-es-amazon-prime-days.html           ← educación + comparativa BF (2.990)
├── fechas-amazon-prime-days.html           ← historial de 12 ediciones (3.020)
├── ofertas-prime-days-2026.html            ← comercial por categoría (2.680)
├── descuentos-reales-o-falsos.html         ← método de verificación (2.810)
├── como-aprovechar-prime-days.html         ← método en 7 pasos (2.630)
├── canal-telegram-ofertas.html             ← el diferenciador (2.290)
├── faq.html                                ← 24 preguntas agrupadas (3.630)
├── robots.txt · llms.txt
└── assets/{css/style.css, js/main.js, img/og-prime-days-2026.png}
```

**Total:** 8 páginas · ~23.900 palabras · `index.html` es el hub.

### Enlazado interno

```
                    index.html  (hub)
        ┌──────────┬──────────┬──────────┬──────────┐
     fechas     ofertas   descuentos  aprovechar   canal
        │           │           │           │          │
        └───────────┴─────┬─────┴───────────┴──────────┘
                          │
                    que-es ──── faq
```

Cada página lleva un bloque «Sigue leyendo» con las otras siete y enlaces en el texto a
las 2–4 páginas que le son complementarias. **Cero huérfanas.**

Enlazado con el resto del sitio (por `../`):

| Desde | Hacia |
|---|---|
| `index.html` raíz | `PrimeDays/index.html` (nav + pie) |
| `plantilla_comun.py` | nav y pie del sitio principal |
| `BlackFriday/index.html` | `PrimeDays/index.html` (nav + tabla de fechas) |
| `PrimeDays/*` | `../index.html`, `../BlackFriday/index.html` (nav + pie) |

Las dos secciones de campaña se enlazan mutuamente para que quien llega por una descubra
la otra: el lector es el mismo y tiene dos campañas distintas en el año.

---

## 5. Decisiones técnicas

### Datos estructurados

| Tipo | Páginas | Para qué |
|---|---|---|
| `BreadcrumbList` | 8 | Jerarquía en la SERP |
| `Article` (+`datePublished`/`dateModified`) | 8 | Frescura |
| `FAQPage` | 8 | Rich results. Los `<summary>` y el schema salen de la **misma** variable, así que no pueden divergir |

> No se ha añadido `Event` ni `HowTo` a propósito. Los helpers existen en el generador
> (`schema_evento`, `schema_howto`) pero no se usan: `Event` con fechas de campaña da
> resultados inconsistentes cuando la campaña ya ha terminado, y `HowTo` exige pasos
> imperativos donde aquí hay criterio. Se ha preferido texto y tabla, que además se
> posicionan.

### Imagen social

`assets/img/og-prime-days-2026.png` (1200×630, generada con Chrome headless). Antes de
esto la plantilla reutilizaba la imagen de Black Friday, de modo que al compartir una
página de Prime Days en WhatsApp salía una imagen que decía literalmente «Black Friday
2026». El texto de la imagen es **duradero** a propósito («48 horas de ofertas», «solo para
miembros Prime») y no lleva la cuenta atrás: una imagen con «termina mañana» en la URL es
un activo caducado en cuanto pasa la campaña.

### Enlaces al canal

`rel="sponsored nofollow noopener"` en **todos** los enlaces al canal, incluido el icono de
la esquina. Esto último se corrigió: el icono usaba solo `noopener`, así que la misma
página mezclaba dos criterios para un mismo destino.

### Enlace a la fuente

El anuncio oficial de aboutamazon.com se enlaza desde la portada, desde la página de
fechas y desde la nota «De dónde sale la fecha». Es una citación de fuente primaria, que es
lo que sostiene la afirmación de E-E-A-T de esta sección.

---

## 6. Validación

```powershell
python tests\validar_prime_days.py            # texto, alfabetos, estructura
python tests\validar_prime_days_enlaces.py    # enlaces, JSON-LD, FAQ vs schema, rel del canal
python tests\validar_prime_days_faq.py        # el toggle abre TODOS los <details>
python tests\validar_prime_days_movil.py      # desborde horizontal, viewport, tokens largos
python generar_prime_days.py                  # regenerar
python generar_sitemap.py                     # verificar que las 8 URLs existen
```

Estado actual: **0 fallos** en los cuatro validadores.

### Correcciones que surgieron de la validación

1. **El validador de texto no cazaba Hangul ni CJK.** Su filtro buscaba el substring
   `LETTER` en el nombre Unicode, pero Hangul se llama `HANGUL SYLLABLE ...` y CJK
   `CJK UNIFIED IDEOGRAPH-...`: ninguno contiene `LETTER`, así que los cuatro caracteres
   coreanos que se habían colado en el contenido pasaban el filtro. Corregido con una
   lista explícita de alfabetos (`ALFABETOS_NO_LATINOS`) y verificado con casos de prueba.
2. **Falso positivo ` edad `.** Estaba en la lista de palabras sospechosas y es una palabra
   española legítima («juguetes por edad»). Como no puede distinguir corrupción de texto
   correcto, se quitó. Los tokens rotos los cazan las comprobaciones de alfabetos.
3. **`str.format` no sirve para este HTML.** `PLANTILLA` usaba `{{marcadores}}`, pensados
   para sustitución literal, pero se rellenaba con `.format()`, que imprimía `{cuerpo}` sin
   sustituir. Además el cuerpo es HTML con llaves, que `.format` interpretaría como
   campos. Ahora la sustitución es por `replace` explícito.
4. **El botón «Desplegar todas» no llegaba a todas.** Apuntaba a un contenedor vacío, así que
   desplegaba 0 de 24 `<details>`. Ahora apunta al contenedor que los envuelve a todos, y
   hay un validador que lo comprueba.
5. **Las tablas de cuatro columnas no cabían** en la columna de texto de 74ch: cada celda
   se partía en tres o cuatro palabras. Las tablas anchas se sacan a `.wrap` completo.

---

## 7. Qué falta por hacer

| Tarea | Prioridad |
|---|---|
| Registrar `sitemap.xml` en Search Console | Alta (nada se posiciona sin indexar) |
| Enviar el mapa de enlaces al canal (botón de enlace por sección) | Media |
| Actualizar `dateModified` al cerrar la campaña (8 de octubre) | Alta: si no, la página queda con la fecha del día 1 y envejece mal |
| Reponer el badge «En marcha» por contenido evergreen en `index.html` | Media, tras el 8 de octubre |
| Bajar el `changefreq` de las 8 URLs de `daily` a `weekly` | Media, tras el 8 de octubre |
| Ficha de empresa en Google Business Profile | Baja |

> **Importante:** el badge «En marcha» y el bloque de cuenta atrás son correcto **hoy** y
> falsos el 8 de octubre. Están concentrados en `cuenta_atras()` y en el hero de
> `PAGINA_INDEX`, así que retirarlos es una edición de dos sitios, no una reconstrucción.