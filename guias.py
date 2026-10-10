"""Contenido de las guias de gangasofertas.com.

Por que un modulo aparte
------------------------
Los cuatro "puente" que genera generar_seo.py (chollos-de-amazon,
errores-de-precio-amazon, articulos-rebajados-amazon,
chollos-amazon-telegram) eran paginas sin contenido propio: un H1, dos
parrafos y una lista de enlaces. Google las leería como thin content, y
ademas competian entre si porque las cuatro intendian posicionar para lo
mismo ("chollos de amazon").

Estas guias son la pieza que faltaba: consultas informativas con respuesta
real. Los competidores de este nicho casi no las tienen:

  - Chollometro publica contenido generado por la comunidad (UGC). Es la
    pagina con mas autoridad del sector (2,3M de usuarios, extension de
    navegador), pero el copy lo escribe la gente: es util para consultas de
    producto, no para consultas de metodo.
  - GangaGato tiene un blog de guias, pero muy corto (posts de ~1200 palabras
    resumidos a pocas lineas) y con muchas afirmaciones que no documenta
    ("verificamos cada oferta manualmente", "monitorizamos 24/7") que este
    proyecto no puede copiar: no serian ciertas.
  - GangaMan tiene un blog generico de compra, no centrado en errores de
    precio.

Las guias de aqui atacan ese hueco: como comprobar un descuento real, como
detectar un error de precio, herramientas para mirar el historial de precios y
como aprovechar Warehouse, Outlet y las devoluciones. Todo lo que se afirma es
comprobable por el lector con la informacion que le damos.

Regla del proyecto: nada de prometer lo que el sitio no hace. validar_sitio.py
falla si aparece "monitoriza Amazon", "24/7" o "100% automatizado" en index.html.
Aqui no cabe: la web recoge lo que se publica en el canal de Telegram, y las
guias lo dicen.
"""

# slug, h1, title, descripcion meta, icono, resumen de 1 linea (para el hub),
# secciones = (h2, [parrafos])  ·  faq = (pregunta, respuesta)
# enlaces = slugs de categorias a las que conviene mandar al lector
GUIAS = [
    (
        "como-detectar-errores-de-precio-amazon",
        "Cómo detectar errores de precio en Amazon",
        "Cómo detectar errores de precio en Amazon | GangasOfertas",
        "Aprende a detectar errores de precio reales en Amazon: qué señales mirar, cómo comprobar el historial y cuándo comprar.",
        "🔍",
        "Qué son, cómo los reconoces y cómo compruebas que uno es real.",
        [
            (
                "Qué es un error de precio",
                [
                    "Un error de precio es un producto que aparece a un precio muy por debajo de su valor real por un fallo del sistema. No es una promoción ni una oferta prevista: nadie ha decidido venderse ese producto a ese precio. Es un fallo, y por eso desaparece.",
                    "Las causas más habituales son tres. La primera es un error al introducir los decimales: alguien teclea 29,99 en lugar de 299,90 y el producto aparece a una décima parte. La segunda es una conversión de divisas mal aplicada, típica cuando un vendedor internacional tiene el precio base en dólares o en libras. La tercera es un fallo en la actualización automática de precios: Amazon ajusta miles de precios al día y de vez en cuando el algoritmo genera una cifra absurda.",
                    "La diferencia con una oferta normal está en la intención. Una oferta tiene fecha de inicio y de fin, está preparada y suele repetirse cada año. Un error de precio aparece sin avisar, no se anuncia y desaparece en minutos u horas, normalmente de madrugada, cuando hay menos personal revisando.",
                ],
            ),
            (
                "Las cuatro señales de un error de precio real",
                [
                    "Un precio demasiado bajo para ser creíble. Si un televisor de 800€ aparece a 8€, no es un error de precio: es un producto distinto, un error en la ficha o una oferta que Amazon va a cancelar. Los errores que se@cancelan no llegan a enviarse.",
                    "Vendido y enviado por Amazon. Si el producto lo vende y lo envía Amazon directamente, la probabilidad de que el pedido llegue es mucho mayor que si lo vende un tercero. En un marketplace, un vendedor externo puede poner un precio artificialmente bajo y luego cancelar cuando le llega la notificación.",
                    "El descuento es grande pero no absurdo. Una rebaja del 50% sobre el precio habitual es creíble; un 95% casi nunca lo es. Por debajo del 90% de descuento, la probabilidad de que Amazon lo corrija antes de enviar es muy alta.",
                    "El precio anterior existe y es el de verdad. Si la ficha muestra un «antes» que no corresponde al precio habitual de las últimas semanas, no estás ante un error de precio sino ante una oferta de ventana, que es otra cosa y no se cancela.",
                ],
            ),
            (
                "Cómo comprobar el historial de precios",
                [
                    "El dato que decide si una oferta es real es el precio mínimo del producto durante los últimos meses. Ese mínimo solo se ve en un gráfico de historial de precios.",
                    "CamelCamelCamel es la opción más sencilla y funciona sin instalar nada: pegas la URL del producto y ves su evolución. Muestra tres series de precio: el de Amazon, el de terceros nuevos y el de usados. Es la más rápida para una comprobación puntual.",
                    "Keepa es la herramienta de referencia y la más completa. Su extensión añade el gráfico directamente en la ficha de Amazon y guarda los datos de cada producto durante años. La versión gratuita basta para lo que se explica aquí; la de pago añade alertas automáticas y datos de ventas.",
                    "Cómo leer el gráfico: si el mínimo del último año está en 400€ y la oferta está a 620€, la oferta es mala aunque parezca un 30%. Si el mínimo era 700€ y ahora está a 620€, es una bajada real aunque el número no impresione. Lo que compara es distancia al mínimo, no porcentaje sobre un precio inventado.",
                    "Desde 2022 la normativa europea obliga a mostrar el precio más bajo de los últimos 30 días, pero no todas las tiendas lo cumplen correctamente. Por eso el gráfico sigue siendo la referencia y la etiqueta no basta.",
                ],
            ),
            (
                "Cuándo comprar: los horarios que más duran",
                [
                    "La madrugada, entre las 00:00 y las 06:00, es la franja con más errores. Los sistemas de Amazon actualizan precios de noche y los errores tardan más en detectarse porque hay menos gente revisando. También es la hora en la que una compra te sale más cara si aciertas mal el día.",
                    "Los cambios de turno, alrededor de las 14:00-15:00, también dan juego: los vendedores del marketplace actualizan inventario al empezar su jornada y los errores manuales son más frecuentes ahí.",
                    "Los fines de semana y festivos son buenos momentos, porque los equipos de supervisión están reducidos y los errores tardan más en corregirse.",
                    "En todos los casos, la hora buena es la que más dura, no la primera que aparece. Un error de las 03:00 que aguanta dos horas tiene más opciones que uno de las 14:00 que aguanta veinte minutos.",
                ],
            ),
            (
                "Cómo comprar sin que te cancelen el pedido",
                [
                    "Pide una o dos unidades. Comprar veinte unidades de un mismo producto a precio de error es la forma más rápida de que Amazon cancele el pedido entero, y aplica tanto si el producto es unElectrodoméstico como si son veinteidentical unidades de un mismo artículo.",
                    "Usa la compra con un clic si la tienes configurada. Reduce los pasos y el tiempo entre que ves el precio y confirmas el pedido.",
                    "No compares tiendas mientras el error está vivo. Cada minuto cuenta: si el precio es de error, perderlo buscando una alternativa es la peor decisión posible.",
                    "Espera el email de confirmación de envío antes de cantar victoria. Hasta que Amazon no confirma el envío, puede cancelar el pedido y devolverte el dinero. En la práctica, Amazon honra los errores moderados (30-50% sobre el habitual), sobre todo si el producto lo vende Amazon y el pedido ya está en preparación. Los errores extremos se cancelan casi siempre.",
                    "Y recuerda que tienes 14 días para desistir de cualquier compra online sin dar explicaciones, incluso si el pedido llegó tarde o la oferta ya no existe.",
                ],
            ),
        ],
        [
            ("¿Son legales los errores de precio?",
             "Aprovecharlos sí es legal. Si el precio aparece publicado y Amazon acepta el pedido, la compra es válida. Lo que no está permitido es automatizar compras masivas para acaparar stock, que es lo que hizo la famousa del millennium Y2K. Si compras para revender miles de unidades, ahí sí hay problemas."),
            ("¿Amazon siempre cancela los errores de precio?",
             "No. Depende de la magnitud. Amazon tiende a honrar los errores moderados (30-50% sobre el precio habitual) si el pedido ya está en preparación, y cancela los extremos, donde el precio es tan bajo que resulta absurdo. Si ya te han confirmado el envío, las probabilidades de que te lo cancelen bajan mucho."),
            ("¿Cuál es la diferencia entre un error de precio y una oferta falsa?",
             "Un error de precio es un fallo del sistema y desaparece. Una oferta falsa es un precio inflado antes y rebajado después para que el descuento parezca grande. La diferencia se ve en el historial: si el «antes» coincide con el precio habitual, es una oferta real; si el precio subió días antes, es decorativa."),
            ("¿Puedo comprar en Amazon de madrugada y arriesgarme a que no llegue?",
             "Puedes, pero la tasa de cancelación es más alta si el pedido no se envía en el horario laboral. Si tienes la compra con un clic configurada, el riesgo baja bastante. Recuerda que aunque Amazon cancele, te devuelven el dinero."),
        ],
        ["moviles-electronica", "general"],
    ),
    (
        "ofertas-reales-vs-descuentos-falsos",
        "Oferta real o descuento falso: cómo distinguirlos",
        "Oferta real o descuento falso en Amazon | GangasOfertas",
        "Cómo saber si el descuento de un producto es real o si el precio anterior estaba inflado antes de comprar.",
        "📉",
        "El método de un minuto para saber si un −50% es de verdad.",
        [
            (
                "Qué es un descuento inflado",
                [
                    "Un descuento inflado ocurre cuando el vendedor sube el precio unos días antes de la promoción y luego lo «rebaja» al precio que tenía antes. El resultado es que la etiqueta dice 50% de descuento y en realidad no te ahorras nada.",
                    "Esto es más habitual de lo que parece y no es ilegal: si el «antes» se muestra, Amazon da por válido el precio publicado, y lo que no se hace es subir un precio y bajarlo al mismo, sino subiéndolo y bajándolo de verdad unos días después. El problema es que la etiqueta comunica un ahorro que no existe.",
                    "Hay una segunda variante más rara: el precio baja solo un poco respecto a lo habitual, pero la oferta se anuncia como si fuera un chollo enorme porque el «antes» se calcula sobre el precio más alto de los últimos meses en lugar de sobre el habitual.",
                ],
            ),
            (
                "El método de un minuto",
                [
                    "Abre el gráfico de historial del producto. Es lo primero y lo único que importa. Con la extensión de Keepa instalada aparece debajo de la imagen en la propia ficha de Amazon; sin ella, pega la URL en es.camelcamelcamel.com.",
                    "Mira el precio mínimo de los últimos 30 días. Ese es tu precio real de referencia, no el «antes» de la etiqueta.",
                    "Compara. Si el precio actual está cerca o por debajo de ese mínimo, la oferta es real. Si está claramente por encima, el descuento es una oferta de ventana.",
                    "Un ejemplo. Un producto marca «antes 200€, ahora 100€». Si el mínimo del último mes era 100€, acabas de ahorrar la mitad y la oferta es buena. Si el mínimo era 170€ y los 200€ fueron un pico de tres días, te ahorras un 41% respecto a lo normal, no un 50%, y la oferta no era el chollo que parecía.",
                ],
            ),
            (
                "Señales de que el precio es legítimo",
                [
                    "El descuento aparece junto a otras rebajas reales de la misma categoría. Si veinte productos de la misma marca están todos a la mitad y ninguno tiene un «antes» inflado, es una promoción verdadera.",
                    "La fecha del «antes» es antigua y coherente. Si el producto lleva meses en ese precio, el «antes» es real.",
                    "El vendedor es Amazon o un distribuidor autorizado, y no un marketplace con pocas valoraciones.",
                    "El descuento se repite cada cierto tiempo con regularidad. Las rebajas reales en un producto concreto vuelven cada pocas semanas; los picos aislados de tres días, no.",
                ],
            ),
            (
                "Señales de que el precio está inflado",
                [
                    "El «antes» es mucho más alto que cualquier precio que recuerdes. Si el producto costaba siempre 120€ y ahora pone «antes 200€», sospechoso.",
                    "El pico del precio coincide exactamente con la promoción. Si el gráfico muestra que el precio subió justo dos o tres días antes de empezar la oferta, la oferta no es real.",
                    "El precio baja mucho y vuelve a subir en pocos días, sin motivo aparente. Es el patrón típico del precio inflado: se sube, se anuncia el descuento y se vuelve al precio anterior.",
                    "Solo hay una unidad o el envío resulta extraño. Las ofertas falsas suelen combinarse con un producto de stock limitado que no se puede comprar en condiciones normales.",
                ],
            ),
            (
                "Qué hacer cuando el descuento es falso",
                [
                    "Aplica el método igual. Si el gráfico dice que no es una oferta, no lo es, por mucho que diga la etiqueta. Perder cinco minutos mirando el historial es más barato que comprar y arrepentirte.",
                    "Pon una alerta de precio en lugar de comprar la primera vez que lo ves. Si el precio no está en su mínimo, la alerta te avisará cuando baje de verdad.",
                    "No confundas «no es oferta» con «es malo». Un producto que no está en oferta puede seguir siendo la mejor opción si te sirve y es lo que quieres. El precio bajo es el objetivo, pero no la única calidad.",
                ],
            ),
        ],
        [
            ("¿Es ilegal que una tienda infle el precio antes de la oferta?",
             "No mientras el precio real y el «antes» se muestren de forma clara: si subes el precio de verdad y luego lo bajas, la oferta es legal, solo que menos rentable de lo que aparenta. Lo que sí está perseguido es no mostrar el precio anterior real, porque entonces el descuento es engañoso y puede acarrear responsabilidad."),
            ("¿Vale la pena mirar el historial antes de comprar 10€ de cosas?",
             "Para una compra de 10€ no. Mirar el historial es rentable a partir de unos 50€, o cuando vas a meterlo en un pack grande. Para compras pequeñas, el propio precio basta."),
            ("¿Keepa y CamelCamelCamel muestran el mismo precio?",
             "No exactamente. CamelCamelCamel actualiza con más retraso y muestra datos más antiguos; Keepa es más preciso y rápido, pero su versión gratuita tiene límites de consulta. Para decidir una compra, los dos sirven."),
            ("¿Y si el producto no aparece en el historial?",
             "Puede ser un producto nuevo o poco vendido. En ese caso no hay historial y no puedes comprobar nada: no hay más remedio que fiarte del precio actual y del vendedor."),
        ],
        ["general", "moviles-electronica"],
    ),
    (
        "amazon-warehouse-outlet-y-devoluciones",
        "Amazon Warehouse, Outlet y devoluciones: comprar más barato",
        "Amazon Warehouse y Outlet en España | GangasOfertas",
        "Cómo comprar más barato en Amazon España con Warehouse, Outlet, productos reacondicionados y devoluciones.",
        "♻️",
        "Tres secciones de Amazon con descuentos del 20 al 50% que casi nadie mira.",
        [
            (
                "Amazon Warehouse: lo que otros te devolvieron",
                [
                    "Amazon Warehouse es la sección de productos devueltos, reacondicionados y con defectos estéticos menores. El producto funciona con normalidad, pero la caja puede estar dañada o el artículo puede tener una marca. Amazon los clasifica con etiquetas de estado: «Como nuevo», «Muy bueno», «Bueno» y «Aceptable».",
                    "Los descuentos van del 20 al 50% según el estado y el producto. Mantienen la misma política de devolución de 30 días que el resto de Amazon, y en muchos casos se puede devolver en tienda en lugar de enviarlo.",
                    "Para encontrarlo, busca «Amazon Warehouse» en el buscador o entra desde el menú de ofertas. No es una sección separada: son páginas de producto dentro de Amazon con una etiqueta de Warehouse.",
                    "Dónde más compensa mirar: electrónica (sobre todo auriculares, cámaras y ratones devueltos), herramientas y temporada, y en productos de marca con caja dañada. Lo que apenas sale bien es la ropa: una prenda devuelta suele tener una talla que ya no te sirve.",
                ],
            ),
            (
                "Amazon Outlet: liquidaciones de stock",
                [
                    "Outlet es distinto de Warehouse. Aquí los productos son nuevos, sin usar, pero tienen exceso de stock, son de temporada pasada o Amazon quiere rotar inventario rápido. La caja está intacta y el producto no se ha usado.",
                    "Los descuentos son más moderados que en Warehouse, normalmente del 20 al 40%, pero el producto es completamente nuevo, lo que para muchas categorías (electrónica, herramientas, juguetes) es una ventaja frente a un reacondicionado.",
                    "Se encuentra buscando «Amazon Outlet» o desde las ofertas de la página principal. La diferencia con Warehouse es la clave: Outlet es nuevo pero más caro; Warehouse es más barato pero devuelto.",
                ],
            ),
            (
                "Cómo funcionan las devoluciones y por qué son una mina de ofertas",
                [
                    "Cada producto devuelto por un cliente vuelve a entrar en el inventario como devuelto. Si no se revende, acaba en Warehouse o en Outlet con descuento.",
                    "Eso significa que los productos más devueltos son también los que más oportunidades de precio tienen. Los errores más comunes al comprar online (ropa que no te queda, electrónica que no encaja con tu equipo) son los que más stock devuelto generan, y por tanto los que más bajan.",
                    "Un detalle importante sobre las devoluciones: en la mayoría de tiendas online, al retractarte tienes 14 días desde la recepción y no tienes que justificar el motivo. En cambio, las devoluciones por defecto de las tiendas son de 30 días y pueden exigir que el producto esté sin usar. La diferencia importa cuando comparas Outlet con una devolución de 30 días.",
                ],
            ),
            (
                "Cuándo no conviene comprar en Warehouse u Outlet",
                [
                    "Si el producto es de regalo o de una talla que sabes que te va a tener justa, no arriesgues: una devolución en productos de moda y calzado es un engorro y un coste de tiempo alto.",
                    "Si lo necesitas con la máxima garantía, comprueba cuál es. Un reacondicionado puede tener una garantía menor que el nuevo, y eso cambia el cálculo si el producto es caro.",
                    "Si el estado «Aceptable» incluye algo que te importa (la caja, el manual original, un accesorio). Lee siempre la descripción del estado concreta, no solo la etiqueta.",
                    "Y comprueba siempre quién vende: en productos devueltos hay más riesgo de vendedor externo sin garantía que en productos nuevos.",
                ],
            ),
        ],
        [
            ("¿Cuál es la diferencia entre Warehouse y Outlet?",
             "Warehouse son productos devueltos o con defectos estéticos: funcionan, pero no están nuevos. Outlet son productos nuevos con exceso de stock o de temporada pasada: intactos, pero sin las ventajas de precio de un devuelto. Warehouse es más barato; Outlet, más nuevo."),
            ("¿Los productos de Warehouse tienen garantía?",
             "Sí, pero puede ser distinta de la del producto nuevo. Los reacondicionados suelen tener una garantía de un año, mientras que un producto nuevo la tiene de dos. Si el producto es caro o la garantía es importante para ti, compruébalo antes de comprar."),
            ("¿Cuándo se pueden devolver productos comprados en Warehouse?",
             "Suelen seguir la política general de Amazon (30 días), y en muchos casos se puede devolver en tienda. Pero el estado del producto debe ser razonable: si lo has usado de más, la devolución puede ser rechazada."),
            ("¿Merece la pena comprar productos devueltos?",
             "En electrónica y herramientas, casi siempre: funcionan igual y el descuento es real. En ropa y calzado, casi nunca: las tallas de los productos devueltos suelen ser las que a otros no les sirvieron, lo que significa que difícilmente te servirán a ti."),
        ],
        ["moviles-electronica", "general"],
    ),
    (
        "cuando-comprar-en-amazon-espana",
        "Cuándo comprar en Amazon: el calendario de precios",
        "Cuándo comprar en Amazon España | GangasOfertas",
        "El calendario de precios de Amazon: cuándo baja cada categoría y cómo aprovechar las fechas de oferta.",
        "📅",
        "Qué categorías bajan en qué mes, y por qué esperar a veces sale más barato.",
        [
            (
                "El patrón de los treinta días",
                [
                    "La norma más fiable: un producto que baja hoy volverá a bajar dentro de unas semanas. Amazon cambia los precios de forma continua, no solo en eventos. Un portátil que ha bajado un 20% este mes volverá a bajar si esperas.",
                    "Esto cambia la estrategia: si no te urge, no compres la primera vez que ves un descuento. Espera un par de semanas y comprueba si baja más. Si baja más,(has comprado bien) y si no, te has ahorrado el money.",
                    "La excepción son los errores de precio y las ofertas flash, que no se repiten: si ves un error de precio, se acaba el día que lo veas.",
                ],
            ),
            (
                "El calendario por categorías",
                [
                    "Electrónica: baja cuando sale un modelo nuevo. Un móvil o portátil del año anterior baja entre un 20 y un 30% cuando aparece el sustituto, normalmente entre septiembre y diciembre. Los productos que no tienen sucesor claro (accesorios, peripherals específicos) bajan poco.",
                    "Ropa y calzado: baja al final de temporada. Las colecciones de invierno bajan en marzo-abril, las de verano en septiembre-octubre. Es el patrón más predecible de todo Amazon.",
                    "Juguetes: suben antes de Navidad y bajan después. El mes de enero es el mejor para juguetes, y el peor para pagar el precio más alto.",
                    "Papelería y material escolar: baja entre julio y septiembre, con la vuelta al cole. Los productos de papelería no tienen fechas de pico más que esa.",
                    "Juego: los títulos del año no bajan. Los de más de un año sí, y las rebajas de las plataformas suelen caer en las mismas fechas para todo el catálogo. Los juegos físicos bajan más que los digitales.",
                    "Higiene y cuidado personal: baja por packs y por fecha de caducidad, no por calendario. La protección solar baja antes de caducar, en verano.",
                    "Consolas: bajan de forma notable cuando se acerca una nueva generación. Las ediciones con disco bajan más que las digitales.",
                ],
            ),
            (
                "Los eventos de todo el año",
                [
                    "Black Friday (finales de noviembre) y Cyber Monday (el lunes siguiente) son los mayores descuentos del año en muchas categorías. También las Navidades y el Día del Padre tienen su propio pico.",
                    "Prime Day suele tener descuentos moderados y muy buena distribución: los chollos de esa semana están repartidos por muchas categorías, no concentrados en las mismas.",
                    "Los días sin IVA en algunos sectores, el Single's Day (11 de noviembre) y la semana de rebajas de enero (en muchas tiendas, no en Amazon) son ventanas secundarias que conviene mirar.",
                    "Un apunte sobre las rebajas de enero: las rebajas solo aplican a las rebajas, no a los descuentos de Amazon. Es un mito muy extendido que conviene descartar.",
                ],
            ),
            (
                "La regla práctica",
                [
                    "Para compras de más de 100€, espera. Pon una alerta en Keepa y compra cuando llegue al mínimo o cerca. El ahorro suele ser mayor que la prisa.",
                    "Para compras de menos de 30€, no esperes. El descuento posible no compensa el tiempo invertido, y el precio ya es bajo.",
                    "Para errores de precio y ofertas flash, no esperes nada. Se acabó cuando se acabó.",
                    "Para ropa y juguetes, el calendario manda: final de temporada y después de Navidad son las fechas.",
                ],
            ),
        ],
        [
            ("¿Amazon tiene rebajas en enero?",
             "Las rebajas de enero son un concepto de las tiendas de moda, no de Amazon. Amazon baja precios todo el año según su propio calendario, y enero es un buen mes para juguetes (porque la Navidad ya pasó) pero no tiene el evento específico de las rebajas."),
            ("¿Amazon baja los precios de verdad cada pocas semanas?",
             "Sí, en muchas categorías. Los precios de electrónica, ropa y consumibles cambian continuamente. Pero hay productos cuyo precio apenas se mueve en años, como los perfumes de marca o los libros: en esos casos esperar no mejora el precio."),
            ("¿Merece la pena esperar si ya he visto un buen precio?",
             "Si es una compra grande, casi siempre. Si el descuento es del 30% pero el mínimo del año está un 40% más abajo, esperar es claramente mejor. Si el precio ya está en su mínimo histórico, no esperes: no va a bajar más."),
        ],
        ["general", "moviles-electronica"],
    ),
    (
        "guia-completa-chollos-amazon",
        "Guía completa de chollos en Amazon",
        "Guía completa de chollos en Amazon | GangasOfertas",
        "Todo lo que hay que saber para encontrar chollos en Amazon: categorías, herramientas, horarios y cómo.filter el ruido.",
        "🎯",
        "El mapa completo: dónde mirar, con qué herramientas y qué descartar.",
        [
            (
                "Dónde mirar primero en Amazon",
                [
                    "Amazon no tiene una única página de ofertas: el chollo está repartido. Las cuatro zonas donde más se concentran los descuentos reales son la página de ofertas del día, las secciones Outlet y Warehouse, los products con descuento de cupón, y las bajadas de precio de las páginas de marca (por ejemplo, la de PS5 o la de un fabricante).",
                    "Los chollos más grandes no están en la página de ofertas: están en productos concretos que bajan sin anunciarse. Ahí es donde entra el historial de precios: nadie te avisa de una bajada del 25% si no estás mirando el gráfico del producto.",
                    "Las categorías con más rotación de precio en Amazon son electrónica, ropa. Son las que más cambian de precio al mes y donde más oportunidades reales hay. Juguetes, papelería y productos de consumo bajan por estacionalidad, en fechas concretas.",
                ],
            ),
            (
                "Herramientas para no perder nada",
                [
                    "Alertas de precio: para productos que ya tienes fichados. Keepa (extensión de navegador, gratis en su versión básica) y las alertas nativas de Amazon en la ficha de producto son las opciones para empezar.",
                    "Canales de Telegram: para productos que aún no conoces. Es justo lo que cubre @GangasOfertasChollos: publica lo que detecta en el canal, y esta web lo recoge ordenado por categoría. El canal sirve para descubrir; la web, para revisar con calma.",
                    "Comparadores: Idealo compara el precio entre tiendas españolas. Útil cuando quieres saber si el precio de Amazon es el más bajo del mercado o solo el más bajo dentro de Amazon.",
                    "Cashback y tarjetas: no bajan el precio del producto, pero sí el coste final. Si vas a comprar mucho, un programa de cashback bien elegido recupera entre el 2 y el 5% de lo gastado.",
                ],
            ),
            (
                "Cómo filtrar el ruido",
                [
                    "Un descuento alto no es un chollo. Como se explica en la guía de descuentos falsos, el «antes» puede estar inflado. Antes de dar por buena una oferta, comprueba el precio mínimo del producto.",
                    "Cuidado con los productos que suben de precio y vuelven a bajar: son ofertas de ventana, no chollos. Suelen ser la trampa más común.",
                    "Los chollos más fiables tienen tres cosas en común: el vendedor es Amazon o un distribuidor, el descuento es del 20-50% (no del 90%), y el precio baja también en productos similares de la misma marca.",
                    "Y filtra por fecha: una oferta de hace una semana puede tener ya un sustituto más barato por el mismo precio. La fecha es parte de la información del chollo.",
                ],
            ),
            (
                "Los cinco errores más comunes",
                [
                    "Comprar la primera vez que se ve un descuento. Si la compra es de más de 100€, casi siempre hay una bajada mejor en las semanas siguientes.",
                    "Fiarse del porcentaje sin mirar el precio final. Un −70% sobre un precio inflado puede salir más caro que un −25% real.",
                    "Ignorar el vendedor. Un precio demasiado bajo en un marketplace sin valoraciones es una estafa con más probabilidad que un error de precio.",
                    "Comprar en talla que no has comprobado. En ropa y calzado, la unidad se agota por talla: el descuento es real aunque el modelo entero siga disponible.",
                    "Esperar al Black Friday para todo. Hay categorías que bajan más fuera de los eventos (el final de temporada en ropa, por ejemplo), y en los eventos mucha gente satura el stock antes de que llegues.",
                ],
            ),
        ],
        [
            ("¿Cuántas ofertas merece la pena mirar al día?",
             "En el canal se publica lo que se detecta, sin filtrar por un umbral fijo. Lo que sí recomendamos es aplicar un filtro al mirar: un descuento del 15% en un producto de 8€ no merece los dos minutos que cuesta valorarlo. Filtra por importe y por porcentaje, en ese orden."),
            ("¿Es mejor un canal de Telegram o una web de ofertas?",
             "Son cosas distintas. El canal sirve para enterarte al instante de algo que no estabas buscando, y por eso la velocidad importa. La web sirve para revisar con calma, comparar y decidir. En esta web tienes las dos: el aviso inmediato en el canal y el catálogo ordenado aquí."),
            ("¿Necesito pagar por alguna herramienta?",
             "No para empezar. Keepa y CamelCamelCamel tienen versiones gratuitas suficientes, e Idealo es gratis. Las herramientas de pago tienen sentido si compras mucho y quieres alertas automáticas o datos más detallados."),
            ("¿Qué categorías dan más rentabilidad?",
             "Donde más se repite un descuento real y verificable: electrónica, ropa y calzado. Donde menos: productos de marca muy consolidados, donde el precio apenas se mueve. El patrón es: busca donde hay rotación, no donde hay la marca."),
        ],
        ["general", "moviles-electronica", "ropa-y-calzado"],
    ),
    (
        "mejores-canales-telegram-ofertas",
        "Canales de Telegram de ofertas en España",
        "Canales de Telegram de ofertas en España | GangasOfertas",
        "Comparativa de canales de Telegram de ofertas en España: qué cubren, cómo filtran y cuándo conviene cada uno.",
        "📢",
        "Qué mirar en cada tipo de canal antes de decidir cuál seguir.",
        [
            (
                "Qué tipo de canal hay",
                [
                    "Canales que recogen ofertas de muchas tiendas: Amazon, PcComponentes, MediaMarkt, El Corte Inglés, Fnac, Miravia, tiendas de ropa. Son los más útiles si quieres variedad, pero llegan a más tiendas y por tanto más ruido.",
                    "Canales centrados en Amazon: casi todas las ofertas son de Amazon España. Menos ruido y más foco, pero solo ves Amazon.",
                    "Canales de una sola tienda o categoría: los másFactorsOf cleanliness porque el volumen es bajo y casi todo lo que se publica es relevante.",
                    "Canales que verifican el historial antes de publicar: más fiables pero con menos publicaciones. Comprueba el historial antes de comprar, o espera a que alguien lo verifique.",
                ],
            ),
            (
                "Qué mirar en un canal antes de seguirlo",
                [
                    "Frecuencia: un canal que publica diez veces al día con vapourware es peor que uno que publica tres veces con ofertas reales. La calidad se nota en el porcentaje de ofertas que resultan ser buenas.",
                    "Transparencia: un canal serio dice de dónde saca la información y, si usa enlaces de afiliado, lo dice. La falta de transparencia no es mala señal por sí sola, pero conviene saberlo.",
                    "Cobertura: ¿solo Amazon, o también otras tiendas? Si buscas el precio más bajo de un portátil, un canal que cubra PcComponentes te puede ahorrar más que diez ofertas de Amazon.",
                    "Si hay enlace directo: los canales que enlazan directamente a la ficha del producto son más útiles que los que te mandan a una página intermedia.",
                ],
            ),
            (
                "Telegram frente a otras vías",
                [
                    "Telegram tiene la ventaja de la inmediatez: el aviso llega en el momento, sin algoritmo que se lo quite de en medio. Es la razón principal por la que la gente usa canales de ofertas en lugar de newsletters o webs.",
                    "La contrapartida es que Telegram no tiene histórico ni buscador potente: si quieres buscar una oferta que viste hace un mes, no la encontrarás. Para eso está la web, que guarda todo ordenado.",
                    "Los grupos de Telegram tienen la ventaja de la conversación (los miembros comenta precios reales) pero el inconveniente del ruido y de los enlaces de spam.",
                    "WhatsApp funciona parecido a Telegram para ofertas, con la ventaja de que mucha gente ya lo tiene abierto en el móvil. Pero no tiene búsqueda ni archivo, así que la información se pierde igual.",
                ],
            ),
            (
                "Cómo usar varios canales sin volverte loco",
                [
                    "No hace falta seguir veinte canales. Con dos o tres —uno de Amazon, uno general y, si compras tecnología, uno de PcComponentes— ya cubres lo esencial.",
                    "Silencia los que no te interesen y deja las notificaciones activas solo para los dos prioritarios. Es la diferencia entre recibir notificaciones útiles y apagar el canal entero.",
                    "Y vuelve a esta web cuando quieras revisar con calma: aquí están todas las ofertas ordenadas por categoría, con precio, fecha y enlace, sin el ruido del canal.",
                    "Hay un detalle que conviene tener presente al elegir: los canales que cubren muchas tiendas incluyen ofertas de supervisoras y marketplaces pequeños, donde el precio bajo a menudo viene con un vendedor poco fiable. Si compras de importe alto, filtra por tienda y quédate con Amazon y los grandes. Para el resto, el <a href=\"ofertas-reales-vs-descuentos-falsos.html\">método del descuento</a> te protege igual.",
                    "Por último, un consejo sobre el volumen: si un canal publica mucho pero la mayoría de sus ofertas son del mismo producto o de la misma tienda, no te aporta mucho frente a uno más pequeño y variado. La frecuencia solo importa si la calidad acompaña.",
                ],
            ),
        ],
        [
            ("¿Es seguroAML un canal de ofertas en Telegram?",
             "El canal en sí es seguro: es solo un tablón de mensajes. Lo que hay que mirar es el enlace de cada oferta: si apunta a un sitio desconocido en lugar de Amazon, no lo abras. La regla es sencilla: este sitio y los canales fiables solo enlazan a dominios de Amazon, y si un enlace apunta a otro sitio, desconfía."),
            ("¿Cuántos canales debería seguir?",
             "Dos o tres. Con uno de Amazon y uno general cubres casi todo. Seguir muchos no mejora el resultado: solo multiplica el ruido y acabas silenciándolos todos."),
            ("¿Los canales de ofertas son fiables?",
             "Depende del canal. Los que verifican el historial antes de publicar son fiables; los que solo reenvían lo que ven sin comprobar suelen tener una proporción alta de ofertas infladas. En esta web no verificamos el historial antes de publicar, así que muestra el precio tal como lo detecta el canal: comprueba tú el mínimo si la compra es importante."),
        ],
        ["general", "mejores-canales-telegram-ofertas"],
    ),
]