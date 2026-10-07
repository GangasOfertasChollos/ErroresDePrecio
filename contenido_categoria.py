"""Contenido editorial de las paginas de catalogo (ropa, moviles, gaming...).

Por que existe
--------------
Las paginas de catalogo se generaban solo con un <h1>, un subtitulo y un
contenedor <section id="ofertas"> vacio que se rellenaba con fetch() desde
data/<slug>.json. En el HTML servido no habia ni una sola oferta: todo el
contenido util lo anadia el JavaScript en el navegador.

Para un crawler eso son paginas de 40 palabras de texto propio, que es
exactamente el perfil de "thin content" que Google no premia. Los tres
competidores que ya posicionan (GangaGato, GangaMan, Chollometro) sirven
contenido en el HTML: articulos de texto, fichas por producto y paginas de
categoria con texto propio. Nosotros no teniamos nada de eso.

Este modulo es la unica fuente del texto de las categorias. generar_categorias.py
lo importa, igual que importa el menu y el pie de plantilla_comun.py. Si el
texto viviera dentro de la plantilla, un cambio de copy obligaria a editar el
generador entero, que es justo lo que paso con el CSS y el JS antes de que
existieran assets/ y plantilla_comun.py.

Regla de estilo: nada de afirmaciones que el sitio no pueda sostener.
validar_sitio.py-vigilado (seccion 6) falla si aparecen frases como
"monitoriza Amazon" o "24/7". El catalogo se alimenta del canal de Telegram,
no de un rastreo de Amazon, y el copy lo dice en vez de fingir lo contrario.
Esa honestidad es ademas una ventaja: los textos de la competencia suelen
prometer cosas que no pueden documentar.
"""

# Cada entrada: slug -> contenido editorial de la pagina.
#
# Campos:
#   titulo_seo   <title> completo (no incluir el dominio a mano, se anade)
#   descripcion  meta description (<=160 caracteres, es lo que se ve en Google)
#   h1           titular de la pagina
#   intro        2-3 parrafos de entrada, respuesta directa a la intencion de
#                busqueda de quien llega a la pagina
#   secciones    lista de (h2, [parrafos]) -> el bloque largo de la pagina
#   como_elegir  lista de (h3, parrafo) -> guia de compra util y concreta
#   faq          lista de (pregunta, respuesta) -> se marca ademas con FAQPage
#   relacionados  slugs de otras paginas del catalogo para enlazar
#
# Los enlaces internos entre categorias (campo "relacionados" y las referencias
# dentro del texto) son deliberados: reparten autoridad entre las paginas del
# catalogo y le dicen al crawler que ninguna es una pagina suelta.

CONTENIDO = {
    "ropa-y-calzado": {
        "titulo_seo": "Ofertas de ropa y zapatillas en Amazon | GangasOfertas",
        "descripcion": (
            "Ofertas y chollos de ropa, zapatillas y complementos en Amazon España. "
            "Camisetas, chaquetas, zapatillas y moda con descuento real, publicados en el canal."
        ),
        "h1": "Ofertas de ropa y zapatillas en Amazon España",
        "intro": [
            "La ropa y el calzado son la categoría donde más se nota la diferencia entre un descuento real y uno de escaparate: en una tienda de moda el «antes» se infla con facilidad, así que una cifra enorme en la etiqueta no significa nada por sí sola. En esta página recoges las ofertas de ropa y calzado que se publican en nuestro canal de Telegram, con el precio detectado y el enlace directo a la ficha de Amazon España.",
            "La selección incluye camisetas, pantalones, vaqueros, chaquetas, abrigos, sudaderas, zapatillas, botas, sandalias y complementos como bolsos, mochilas, gafas de sol o cinturones. Cada oferta aparece aquí en cuanto se anuncia en el canal, sin esperas.",
            "Lo importante de mirar ropa en oferta no es solo el precio: la talla se agota rápido y una devolución en tienda cuesta tiempo y transporte. Por eso publicamos el precio y el enlace, y teAliamos a comprobar la disponibilidad en la ficha antes de comprar.",
        ],
        "secciones": [
            (
                "Cómo saber si una oferta de ropa es real",
                [
                    "Un descuento del 50% en un producto cuyo «antes» no reconoces es el primer aviso. La forma rápida de comprobarlo es mirar el histórico del producto: si el «antes» coincide con el precio habitual de las últimas semanas, la rebaja es auténtica; si el precio subió días antes para luego «rebajarse», es una oferta decorativa.",
                    "En ropa es especialmente importante fijarse en quién vende. Una oferta gestionada por Amazon directamente («Vendido y enviado por Amazon») mantiene las condiciones de devolución estándar. Un vendedor externo puede tener condiciones distintas y una reputación que conviene mirar antes de pagar.",
                    "La marca también es una pista. Las prendas de marca con descuento alto suelen ser de temporadas anteriores o de lotes de cierre de stock; las colecciones del año no bajan así. Si buscas algo concreto y el descuento es del 80%, casi siempre es stock antiguo.",
                    "Y ojo con los precios tachados enERVADOR: un mismo producto puede aparecer con dos «antes» distintos según la plataforma. Por eso en esta web mostramos el precio que se detectó al publicar la oferta, y no uno arrastrado de otra fuente.",
                ],
            ),
            (
                "Zapatillas y calzado: dónde suele estar el chollo",
                [
                    "El calzado es uno de los rubros con más rotación de stock en Amazon España. Las zapatillas de Running, las de deporte y las de moda comparten casi siempre el mismo problema: hay muchas tallas y el stock se reparte de forma desigual. Una marca que está de sobra en la 42 puede estar a cero en la 40.",
                    "Los descuentos más limitados suelen aparecer cuando un color o una talla se agota. Es el momento en el que los revendedores de Outlet y los vendedores de marca Bajan precio para vaciar la última unidad. Si te sirve cualquier talla, es el momento de comprar; si solo te sirve una concreta, conviene vigilar el ASIN durante unos días.",
                    "Un consejo práctico con el calzado: mira el tipo de devolución antes de comprar. Muchas ofertas de Outlet en Amazon permiten devolver en tienda, lo que hace mucho más asumible una talla que no acaba de encajar.",
                ],
            ),
            (
                "Ropa de temporada y cómo aprovechar los restos de stock",
                [
                    "Los descuentos grandes en ropa suelen llegar cuando una temporada termina, no cuando empieza. Es el caso de las colecciones de invierno cuando llega la primavera, o al revés. En esas ventanas los descuentos reales llegan al 40-60% sobre el precio original, que es donde se compra bien sin esperar a un evento.",
                    "El origen del descuento importa: el precio más bajo de un producto suele venir de la variante concreta (color o talla), no del modelo entero. Por eso dos personas pueden ver precios muy distintos para «la misma» sudadera.",
                    "Para que la oferta te sirva, revisa la fecha de la oferta que publicamos. Si tiene más de unos días, es probable que la talla concreta ya no esté disponible aunque la referencia siga viva.",
                ],
            ),
            (
                "Complementos y accesorios: donde mejor se raja la diferencia",
                [
                    "Bolsos, mochilas, gafas de sol, cinturones y bufandas son la parte del catálogo donde el descuento real y la utilidad se mezclan menos. Son productos con un precio de referencia estable, así que una bajada del 30% es más fácil de comprobar que un 70% en una prenda de temporada.",
                    "En gafas de sol y complementos de marca, vigila que el vendedor sea Amazon o un distribuidor autorizado. Las imitaciones con descuento alto son el problema clásico de esta categoría.",
                ],
            ),
        ],
        "como_elegir": [
            ("Comprueba la talla antes que nada", "El descuento más grande se lo lleva quien aún tiene la talla. En cuanto publicas la oferta, revisa si tu talla aparece disponible y no esperes: las unidades se agotan por talla, no por modelo."),
            ("Vigila quién es el vendedor", "La etiqueta «Vendido y enviado por Amazon» mantiene la devolución estándar y la garantía. Un vendedor externo con pocas valoraciones y un precio demasiado bajo es una combinación que conviene evitar."),
            ("Mira el histórico si el descuento es alto", "Por encima del 50% en moda, casi siempre hay una historia detrás: stock antiguo, devoluciones o una marca que sube y baja precios. El histórico del producto te dice cuál de las tres."),
            ("Elige el momento de la temporada", "Los restos de stock se vacían al final de la temporada, no al principio. Si no tienes prisa, esperar unos meses puede bajarte el precio de la misma prenda."),
        ],
        "faq": [
            (
                "¿Cada cuánto se actualizan las ofertas de ropa?",
                "En cuanto se publica una oferta nueva en el canal de Telegram. No hay un horario fijo: si no ha entrado nada nuevo, la lista no cambia. Si prefieres enterarte en el momento, suscríbete al canal.",
            ),
            (
                "¿Los precios que ve aquí son los definitivos?",
                "Son los precios detectados en el mensaje del canal en el momento de publicarlo. Amazon puede cambiarlos en cualquier momento y, en ropa, la disponibilidad depende de la talla concreta. El precio final y la disponibilidad son siempre los de la ficha de Amazon.",
            ),
            (
                "¿Cómo sé si un descuento del 70% es real?",
                "Mira el histórico del producto. Si el «antes» coincide con el precio habitual de las últimas semanas, el descuento es real; si el precio se infló poco antes, es una oferta de ventana. En ropa el descuento alto suele ser stock de temporadas anteriores, no una rebaja sobre el precio del momento.",
            ),
            (
                "¿Puedo devolver una prenda comprada en oferta?",
                "Sí, las condiciones de devolución dependen de quién es el vendedor y de si la oferta viene de Amazon Outlet o de un vendedor externo. Compra en Amazon directamente siempre es la opción con menos sorpresas en la devolución.",
            ),
        ],
        "relacionados": ["general", "gaming-consolas", "papeleria-oficina"],
    },

    "moviles-electronica": {
        "titulo_seo": "Ofertas de móviles y electrónica en Amazon | GangasOfertas",
        "descripcion": (
            "Chollos y ofertas de smartphones, portátiles, auriculares y electrónica en Amazon España. "
            "Tecnología al mejor precio, publicados en el canal de Telegram."
        ),
        "h1": "Ofertas de móviles y electrónica en Amazon España",
        "intro": [
            "La electrónica es la categoría donde los descuentos grandes se repiten: es la que más veces aparece en el canal, y la que más técnicamente exige mirar el histórico. Un portátil a la mitad de precio puede ser una bajada legítima o un «antes» inflado hace dos semanas, y la diferencia entre ambas cosas se decide en un gráfico, no en la etiqueta.",
            "Aquí recoges las ofertas de smartphones, portátiles, monitores, auriculares, smartwatch, carga y electrónica doméstica que se anuncian en @GangasOfertasChollos, con el precio detectado y el enlace directo a Amazon España.",
            "Los precios de tecnología bajan con frecuencia y las ofertas duran poco. Únete al canal si quieres recibirlas en el móvil en cuanto se publiquen, sin tener que volver a esta página.",
        ],
        "secciones": [
            (
                "Móviles: el precio oficial casi nunca es el precio real",
                [
                    "Un smartphone nuevo sale al precio oficial unas semanas y luego baja. Las opciones libres de fábrica duran poco y las de operador incluyen un compromiso que muchas veces no compensa si ya tienes una tarifa buena. Cuando veas un móvil con descuento, comprueba si el precio incluye IVA y si es una unidad libre o una oferta asociada a una financiación.",
                    "Los móviles de gama alta son los que más bajan de golpe: es habitual ver una rebaja del 20-30% en el modelo del año anterior cuando aparece el nuevo. Ese es un descuento con estructura, no un error, y se puede planificar. Los del 70-80% en gama alta suelen ser lotes reacondicionados o unidades con stock antiguo.",
                    "Un detalle que conviene mirar en cualquier móvil: la garantía. Las unidades «renovadas» o devueltas tienen una garantía distinta de la nueva y esa diferencia debe estar clara. Cuando sea así, el descuento se compara con la garantía corta, no con la misma referencia nueva.",
                ],
            ),
            (
                "Portátiles y ordenadores: mira el precio por debajo de la carcasa",
                [
                    "En portátiles y ordenadores el descuento de la etiqueta muchas veces esconde un precio anterior inflado. Un portátil de 900€ puesto a 620€ sigue siendo caro si hace tres meses estaba a 750€.",
                    "El consejo más útil en esta categoría es el mismo: gráfico de historial. Si el mínimo del último año está en 520€ y la oferta está en 620, sabes que no es el mejor momento. Si el mínimo histórico era 700€ y ahora está en 620, estás ante una bajada real aunque no parezca espectacular.",
                    "También conviene mirar la memoria y el disco en la propia ficha del canal, porque las ofertas de tecnología suelen ser de un modelo concreto. Un portátil con 16GB de RAM no es comparable con otro de 8GB aunque los dos se anuncien como «portátil de 15 pulgadas».",
                ],
            ),
            (
                "Auriculares, smartwatch y audio: la categoría más barata de revisar",
                [
                    "Audio y wearables son las categorías donde más se repiten las ofertas, y donde el descuento suele ser genuino. Los auriculares con cancelación de ruido bajan de forma escalonada, y los smartwatch tienen una curva de precio marcada por cada generación.",
                    "Para los auriculares, la diferencia entre un modelo de un año y otro más antiguo suele ser la batería y el códec. Si no te importa el último códec, un modelo anterior con la misma cancelación suele ser la compra racional.",
                    "En los smartwatch hay que mirar la marca: los de la misma gama de Apple, Samsung o Garmin bajan siguiendo un patrón que se puede anticipar. Los modelos que acaban de salir apenas bajan; los de la generación anterior son los que entran en oferta.",
                ],
            ),
            (
                "Carga y accesorios: revisar por seguridad, no solo por precio",
                [
                    "Cargadores, cables y baterías externas son ofertas frecuentes y con descuento amplio, pero aquí el precio no lo es todo. Un cargador barato que no cumple la potencia anunciada o una batería externa sin certificación puede ser un problema real.",
                    "Cuando veas una oferta de este tipo, comprueba que la potencia y el estándar de carga son los que necesitas (por ejemplo, USB-C con la potencia suficiente para tu portátil). La etiqueta del canal recoge el título del producto, que ya incluye esas especificaciones.",
                ],
            ),
        ],
        "como_elegir": [
            ("Fíjate en el mínimo histórico, no en el descuento", "Un −40% sobre un precio inflado puede salir más caro que un −20% sobre el precio real. Lo que cuenta es la distancia entre el precio actual y el mínimo del último año."),
            ("Comprueba si es nuevo, devuelto o reacondicionado", "La diferencia de precio entre una unidad nueva y una devuelta es real, pero también lo es la diferencia de garantía. Compara productos equivalentes, no el mismo nombre con letras distintas."),
            ("Vigila la fecha de la oferta", "La tecnología se actualiza rápido. Una oferta de hace una semana puede tener ya un modelo superior por el mismo precio. Para lo caro, la paciencia paga."),
            ("Fíjate en las especificaciones antes que en la categoría", "Que dos productos se anuncien como «portátil de 15» no significa que sean comparables. La RAM, el disco y la pantalla deciden el precio real."),
        ],
        "faq": [
            (
                "¿Cada cuánto se actualizan las ofertas de electrónica?",
                "Cada vez que se publica algo nuevo en el canal. La electrónica es de las categorías que más entradas genera, así que la lista cambia con frecuencia.",
            ),
            (
                "¿El precio que aparece aquí sigue siendo válido?",
                "Es el precio detectado al publicar la oferta. Como la tecnología cambia de precio casi a diario, confirma siempre el precio final en la ficha de Amazon antes de comprar.",
            ),
            (
                "¿Cómo sé si un descuento del 60% en un portátil es real?",
                "Necesitas el historial de precios del producto. Si el «antes» es el precio habitual de las últimas semanas, el descuento es real; si el precio subió justo antes de la oferta, es una oferta de ventana. En nuestra web mostramos el precio tal como se detectó, sin retocarlo.",
            ),
            (
                "¿Publicáis también productos reacondicionados?",
                "Publicamos lo que llega al canal, y puede incluir unidades devueltas o reacondicionadas si así se anuncian. El título del producto indica el estado, y conviene comprobar la garantía antes de comprar.",
            ),
        ],
        "relacionados": ["general", "gaming-consolas", "papeleria-oficina"],
    },

    "gaming-consolas": {
        "titulo_seo": "Ofertas de PS5, Switch y Xbox en Amazon | GangasOfertas",
        "descripcion": (
            "Chollos y ofertas de PS5, Nintendo Switch, Xbox, mandos y videojuegos en Amazon España. "
            "Gaming al mejor precio, con las gangas más recientes."
        ),
        "h1": "Ofertas de PS5, Switch, Xbox y videojuegos",
        "intro": [
            "El gaming tiene una particularidad frente al resto de categorías: el catálogo es pequeño y muy conocido. Eso significa que casi todo el mundo sabe cuánto debería costar una PS5 o un juego concreto, y que un «descuento» que no cuadra salta a la vista.",
            "En esta página están las ofertas de consolas, mandos y videojuegos que se publican en el canal, con el precio detectado y el enlace a Amazon España. Cuando un juego baja a su mínimo histórico, aquí lo ves junto al resto de gangas.",
            "En gaming, la diferencia entre una buena compra y una mala casi nunca está en la oportunidad: está en saber si el precio es el mínimo real. Por eso insistimos en mostrar el precio tal como se detectó, sin redondear ni inflar.",
        ],
        "secciones": [
            (
                "Consolas: cuándo comprar y cuándo esperar",
                [
                    "Los detalles más antiguos (con disco o sin disco) bajan bastante más que las nuevas. Los juegos físicos son otra historia: bajan cuando el problema de las rebajas digitales se hace notar.",
                    "Un error frecuente es esperar el «gran descuento» de la consola en un momento en el que la consola ya ha bajado bastante y el precio de los juegos es lo que queda por caer. Si lo que te interesa son juegos, el momento dulce suele ser antes que el de la consola.",
                    "Los dispositivos portátiles de la talla Steam Deck o el ecosistema de Switch concentran ofertas con descuento alto y, en general, bien de precio, porque hay más stock circulando. Es de las categorías donde más veces se ve el chollo legítimo.",
                ],
            ),
            (
                "Videojuegos: el mínimo histórico es la única referencia válida",
                [
                    "En juegos, la comparación entre plataformas y formatos (físico, digital, deluxe, edición coleccionista) hace que «el mismo juego» tenga precios muy distintos. Por eso el único dato útil es el mínimo histórico de la referencia exacta que estás mirando.",
                    "Los juegos que acaban de salir rara vez bajan: están en su momento de lanzamiento. Los que tienen un año o más son los que entran en oferta, especialmente los que no son de AAA y los que proceden de la generación anterior.",
                    "Un detalle sobre los precios de los juegos: las rebajas de las plataformas de consola suelen caer en las mismas fechas para todo el catálogo, así que «cuándo comprar» importa menos que «qué plataforma tiene el precio más bajo». Una misma oferta en PS5 y en Xbox puede tener precios muy separados.",
                ],
            ),
            (
                "Mandos y accesorios: pequeñas compras con buen descuento",
                [
                    "Mandos, juegos de la generación anterior, comandos con cable y accesorios son ofertas frecuentes con descuentos que van del 30 al 60%. Son compras de poco importe y bajo riesgo, así que la tentación natural es comprar varias.",
                    "Hay una diferencia práctica entre un mando con cable y uno inalámbrico que conviene tener en cuenta antes de comprar: el inalámbrico necesita pilas o carga, y un mando cuyo Bluetooth se corta a mitad de partida es una compra mala por muy barato que salga. Los mandos con cable, en cambio, son la opción aburrida a la que casi nunca se le rompe la batería. Si vas a comprar dos o tres, el cable puede salirte más rentable.",
                    "El consejo aquí es el mismo de siempre: mira el mínimo del mando. Un mando de PS5 tiene un precio bastante estable y una bajada del 40% es real solo si se acerca al mínimo del último año.",
                ],
            ),
            (
                "Accessorios de consola y cuándo esperar a la nueva generación",
                [
                    "Los accesorios de consola (cargadores, bases, soportes y audífonos con cable) siguen el calendario de cada generación. Cuando se acerca una consola nueva, los accesorios de la anterior entran en oferta porque dejan de ser el producto que la gente quiere. Ese es el momento en el que un cargador o unos auriculares de la PS5 bajan de verdad.",
                    "Si compras una consola usada, los accesorios de la generación anterior suelen ser la compra más fácil: funcionan igual de bien y cuestan la mitad. El error típico es comprar accesorios de la consola nueva pensando que servirán para la que ya tienes.",
                ],
            ),
        ],
        "como_elegir": [
            ("El mínimo histórico manda", "En gaming los precios son públicos y conocidos. La pregunta correcta no es «¿cuánto descuenta?» sino «¿está en su mínimo histórico?». El precio actual, compáralo con el gráfico."),
            ("Cuidado con las ediciones y formatos", "El mismo juego en digital, físico o deluxe tiene precios muy distintos. Compara la referencia exacta que estás mirando, no el nombre del juego."),
            ("Los juegos del año rara vez bajan", "Si el juego es muy nuevo, es normal que no esté en oferta. Los chollos reales están en los títulos con más de un año."),
            ("Comprueba si el precio es el de tu plataforma", "La misma oferta puede estar a un precio en PS5 y a otro muy distinto en Xbox o Switch. Antes de comprar, comprueba que estás mirando tu plataforma."),
        ],
        "faq": [
            (
                "¿Cada cuánto se actualizan las ofertas de gaming?",
                "En cuanto se publica algo en el canal. Las rebajas de juegos suelen concentrarse en temporadas altas y en fechas de lanzamiento, así que la lista cambia con frecuencia en esos momentos.",
            ),
            (
                "¿Los juegos que publicáis están en su mínimo histórico?",
                "Publicamos lo que se detecta en el canal. No filtramos por mínimo histórico, así que comprueba el historial del juego antes de decidir: nuestro papel es mostrar el precio detectado, no prometer que es el más bajo posible.",
            ),
            (
                "¿Publicáis juegos digitales o físicos?",
                "Publicamos lo que llega al canal, que puede ser de ambos formatos. El formato se indica en el título del producto.",
            ),
            (
                "¿Merece la pena comprar consolas en oferta?",
                "Depende de la generación. Las consolas de la generación anterior bajan de forma notable cuando se acerca una nueva, y las ediciones más antiguas son las que más bajan. Si te interesan sobre todo los juegos, el descuento en juegos suele ser más interesante que el de la consola.",
            ),
        ],
        "relacionados": ["general", "moviles-electronica"],
    },

    "higiene-cuidado-personal": {
        "titulo_seo": "Ofertas de higiene y belleza en Amazon | GangasOfertas",
        "descripcion": (
            "Chollos y ofertas de champús, perfumes, cosmética y afeitadoras en Amazon España. "
            "Higiene y belleza al mejor precio, publicados en el canal."
        ),
        "h1": "Ofertas de higiene, belleza y cuidado personal",
        "intro": [
            "Higiene y cuidado personal es la categoría donde los descuentos se repiten con más constancia, porque son productos de consumo que se recompran. Un champú, una crema o un desodorante que bajan un 40% aparecen una y otra vez a lo largo del año.",
            "Aquí tienes las ofertas de champús, perfumes, cosméticos, afeitadoras, cepillos y cuidado facial que se anuncian en @GangasOfertasChollos, con el precio detectado y el enlace directo a Amazon España.",
            "Un apunte importante en esta categoría: los perfumes y la cosmética de marca tienen precios muy estables, así que un descuento del 70% suele significar que no es el producto que pensabas o que hay una diferencia de tamaño. Comprueba siempre el formato y el número de unidades en la ficha.",
        ],
        "secciones": [
            (
                "Perfumes y cosmética: el descuento más alto, el más sospechoso",
                [
                    "Perfumes y cosméticos de marca son productos cuyo precio de referencia está muy bien definido. Un perfume de 50€ que aparece a 18€ no es una oferta de 64%: es un producto distinto (otro tamaño, otra presentación o una imitación) o un precio inflado.",
                    "En esta categoría el primer filtro no es el descuento sino el formato. Un «pack de 3» a un precio que parece de una unidad es un precio distinto. Compara el precio por mililitro o por unidad, que es el único que permite comparar.",
                    "La cosmética de cuidado facial y los productos de farmacia tienen precios más variables y bajan con más libertad. Ahí un descuento del 30-40% es habitual y, si el vendedor es Amazon o un distribuidor fiable, es una compra segura.",
                ],
            ),
            (
                "Higiene diaria y afeitadoras: chollo frecuente y de bajo riesgo",
                [
                    "Cuchillas de afeitar, desodorantes, geles de ducha, cepillos de dientes y afeitadoras son ofertas que aparecen con mucha frecuencia y con descuentos claros. Son productos de precio estable y con marca reconocible, así que la rebaja es fácil de comprobar.",
                    "En afeitadoras y máquinas de cortar pelo, los modelos de un año o más atrás son los que bajan. Las marcas muchas veces renuevan su gama completa cada pocos años, y el modelo anterior queda en descuento con buena frecuencia.",
                    "Los productos de packs (packs de champú, packs de desodorante) suelen ofrecer la mejor relación precio-unitario. Ojo al cálculo: divide el precio total entre el número de unidades antes de comparar con la unidad suelta.",
                ],
            ),
            (
                "Cuidado facial y productos de temporada",
                [
                    "El cuidado facial es una categoría con rotación alta y donde los descuentos reales son frecuentes, especialmente en formatos grandes (tubos de 200ml en lugar de 50ml) y en sets.",
                    "La protección solar merece atención aparte porque se compra en Primavera y Verano y porque los descuentos en el canal son menos habituales que en otras categorías de belleza. Cuando publicamos una oferta de protector solar, el descuento suele ser real porque el producto caduca y hay que liquidarlo.",
                ],
            ),
            (
                "Perfume, cosmética y productos de farmacia: dónde está el chollo real",
                [
                    "En perfumes, un descuento alto no significa lo mismo que un descuento alto en ropa. Un perfume de 80€ que aparece a 30€ suele ser un formato más pequeño o una venta a un tercero; conviene comparar el precio por mililitro antes que el porcentaje.",
                    "La cosmética de farmacia es la parte de esta categoría donde más chollos legítimos aparecen, porque los productos tienen fecha de caducidad y la farmacia liquida antes de perderlos. Ahí un 30-40% es real, y el vendedor suele ser fiable.",
                    "Un apunte sobre los productos de higiene ecológico y natural: su precio es más alto y baja menos, así que un descuento del 20% en un producto que antes costaba 25€ suele ser mejor compra que un 50% en un producto convencional que siempre costó 10€. Lo que importa es el precio que vas a pagar, no el porcentaje.",
                ],
            ),
        ],
        "como_elegir": [
            ("Compara el precio por unidad", "En packs y formatos grandes, el precio por mililitro o por unidad es el único número comparable. Un pack puede parecer barato y salir más caro por unidad."),
            ("Comprueba el formato y las unidades", "El descuento más alto en belleza suele venir de un cambio de tamaño o de un pack. Lee el título y la ficha antes de decidir que es una ganga."),
            ("Fíate del vendedor en cosmética", "Perfumes y cosméticos de marca, mejor comprados en Amazon directamente o en un distribuidor autorizado. Ahí los descuentos son menos interesantes pero el producto es fiable."),
            ("Los productos de farmacia bajan en temporada", "La protección solar y otros productos de farmacia que caducan liquidan hacia su fecha. Es cuando toca comprar."),
        ],
        "faq": [
            (
                "¿Cada cuánto se actualizan las ofertas de higiene y belleza?",
                "Cada vez que se publica algo nuevo en el canal. Es una categoría con bastante rotación, así que la lista cambia con frecuencia.",
            ),
            (
                "¿Por qué veo descuentos del 70% en perfumes?",
                "Porque casi nunca es el mismo producto. Suele ser un formato más pequeño, un pack, una imitación o un precio de referencia inflado. Comprueba el tamaño, el número de unidades y quién es el vendedor antes de darlo por bueno.",
            ),
            (
                "¿Los precios de estos productos son fiables?",
                "Son los precios detectados en el canal en el momento de publicarlo. En una categoría con tantos packs y formatos, confirma siempre el formato y el precio por unidad en la ficha de Amazon.",
            ),
        ],
        "relacionados": ["general", "ropa-y-calzado", "papeleria-oficina"],
    },

    "juguetes-infantil": {
        "titulo_seo": "Ofertas de juguetes en Amazon España | GangasOfertas",
        "descripcion": (
            "Chollos y ofertas de juguetes, LEGO, juegos de mesa y puericultura en Amazon España. "
            "Juguetes e infantil al mejor precio, publicados en el canal."
        ),
        "h1": "Ofertas de juguetes, juegos y puericultura",
        "intro": [
            "Los juguetes tienen un calendario propio: el mercado se mueve por fechas (Navidad, cumpleaños, vuelta al cole) y eso hace que los descuentos se concentrate en momentos concretos del año. Los de puericultura (pañales, chupetes, cochecitos) tienen un ciclo de compra constante y bajan más por volumen que por oportunidad.",
            "Esta página recoge las ofertas de juguetes, juegos de mesa, LEGO, muñecas y puericultura que se anuncian en el canal, con el precio detectado y el enlace directo a Amazon España.",
            "En juguetes, dos cosas importan más que el descuento: la edad recomendada y el estado del producto. Un juguete de 50€ a 25€ que es una devolución puede no ser una oferta sino una oportunidad de comprar algo que no ibas a comprar. Aun así, es un chollo.",
        ],
        "secciones": [
            (
                "LEGO y juguetes de marca: los descuentos más claros",
                [
                    "Los juguetes de marca (LEGO, Playmobil, Barbie, Hot Wheels) tienen precios de referencia muy estables y bajan siguiendo un patrón: los juegos del año apenas bajan, y los de temporadas anteriores entran en oferta con descuentos del 30-50%.",
                    "Los sets grandes de LEGO son los que más descuento ofrecen, y también los que más stock acumulan: hay muchísimas unidades del mismo set en circulación. Cuando un set popular baja, es de los chollos más fiables de la categoría porque el stock es amplio y la“ oferta se nota en el precio.",
                    "Un consejo: comprueba los accesorios. Los sets que vienen con piezas adicionales o con minifiguras exclusivas suben de precio cuando se retiran. Si ves una subida repentina de un set, puede ser una pieza de colección y no una oferta.",
                ],
            ),
            (
                "Juegos de mesa y juguetes educativos: los más estables",
                [
                    "Los juegos de mesa son, junto con los juguetes educativos, la parte más estable de la categoría. Los juegos de mesa bien valorados mantienen su precio durante años y bajan en campañas concretas (Navidad, Cyber Week).",
                    "Los juegos de reglas para peques (memory, puzzles, clasificación) bajan con más frecuencia y suelen ser compras de precio bajo y riesgo bajo. El descuento típico va del 20 al 40%.",
                    "Los puzzles y juegos de construcción son la categoría donde más se nota el precio por calidad: un puzzle de 1000 piezas de una marca buena no se equipara a uno genérico aunque el descuento sea el mismo.",
                ],
            ),
            (
                "Puericultura: el descuento está en el volumen",
                [
                    "Pañales, artículos de bebé y productos de puericultura son compras recurrentes. El chollo no está tanto en una oferta puntual como en los multipacks y en las marcas con descuento permanente (que no son un chollo, sino el precio normal).",
                    "Cuando publicamos una oferta de pañales o de un producto de bebé, lo que suele marcar la diferencia es el precio por unidad en el multipack, no el precio del paquete. Un paquete de 40 pañales a 20€ son 0,50€ por pañal; ese es el número que hay que mirar.",
                    "Los productos de Baby que tienen fecha de caducidad (cosmética infantil, alimentos) se liquidan hacia su fecha, lo que genera ofertas reales. Los que no caducan (juguetes, ropa de bebé) bajan por stock.",
                ],
            ),
        ],
        "como_elegir": [
            ("La edad recomendada manda", "Un juguete con descuento que no sirve para la edad del niño es un chollo que no es una ganga. Comprueba la edad antes que el precio."),
            ("Menos unidades, a menudo, es mejor chollo", "En las marcas de juguetes, los packs grandes no siempre son la mejor compra: a veces una unidad concreta a 30€ sale mejor que un pack de tres a 40€. Compara el precio por unidad."),
            ("Cuidado con las piezas de colección", "Los sets con elementos exclusivos suben de precio en lugar de bajar. Si un set conocido ha subido, no es una oferta."),
            ("Comprueba el estado del producto", "Los juguetes de devoluciones o con caja dañada aparecen a precio muy bajo. Son una oportunidad real, pero comprueba que el producto esté completo y que la devolución esté permitida."),
        ],
        "faq": [
            (
                "¿Cada cuánto se actualizan las ofertas de juguetes?",
                "En cuanto se publica algo en el canal. En esta categoría las ofertas se concentran en la campaña de Navidad y antes de la vuelta al cole, así que en esos momentos hay más movimiento.",
            ),
            (
                "¿Los juguetes que publicáis son nuevos?",
                "Publicamos lo que llega al canal. Puede incluir unidades devueltas si así se anuncian. Comprueba el estado y que la devolución esté permitida antes de comprar.",
            ),
            (
                "¿Por qué las ofertas de pañales no tienen tanto descuento?",
                "Porque en productos de consumo el descuento suele estar en el precio por unidad del multipack, no en la etiqueta. Un paquete al mismo precio pero con más unidades es el chollo real, aunque el porcentaje de la etiqueta parezca bajo.",
            ),
        ],
        "relacionados": ["general", "papeleria-oficina", "higiene-cuidado-personal"],
    },

    "papeleria-oficina": {
        "titulo_seo": "Ofertas de papelería y oficina en Amazon | GangasOfertas",
        "descripcion": (
            "Chollos y ofertas de papelería, material escolar y oficina en Amazon España. "
            "Cuadernos, bolígrafos y escritorio al mejor precio."
        ),
        "h1": "Ofertas de papelería, material escolar y oficina",
        "intro": [
            "Papelería y oficina es una categoría poco glamorosa pero muy rentable en búsquedas: la gente la busca antes de la vuelta al cole y cuando monta su espacio de trabajo, y los precios bajan de forma notable en esas fechas. Los descuentos aquí no suelen ser de un 70% monetario, pero se repiten y son fáciles de comprobar.",
            "Aquí están las ofertas de cuadernos, bolígrafos, papelería escolar, sillas y material de escritorio que se anuncian en @GangasOfertasChollos, con el precio detectado y el enlace directo a Amazon España.",
            "La diferencia entre esta categoría y las demás es que el precio de referencia está muy claro: un cuaderno de 50 hojas cuesta lo que cuesta. Eso hace que el chollo real se detecte mirando dos cosas: el precio por unidad (en packs) y si el descuento corresponde a una marca concreta.",
        ],
        "secciones": [
            (
                "Material escolar: la vuelta al cole es la fecha clave",
                [
                    "El material escolar baja de precio entre julio y septiembre, que es cuando se prepara la vuelta al cole. Es la ventana más ancha de ofertas de la categoría, y suele empezar antes que cualquier campaña grande.",
                    "En este momento lo que más se busca son los packs de material escolar, que agrupan bolígrafos, cuadernos,Marcadores y otros basics. El precio por unidad es el dato clave: un pack de 30 bolígrafos a 9€ (0,30€ cada uno) es mejor compra que tres paquetes sueltos aunque la etiqueta diga lo mismo.",
                    "Los productos de marca (Bic, Stabilo, Faber-Castell) y los productos genéricos tienen precios muy distintos. En papelería, la marca se nota menos en la calidad que en el precio, así que los packs de genéricos bien valorados suelen ser la compra más inteligente.",
                ],
            ),
            (
                "Escritorio y sillas: compras grandes, descuentos claros",
                [
                    "Sillas de oficina, escritorios y peripherals son compras de mayor importe y con descuento más visible. Una silla de oficina puede bajar un 30-40% y un escritorio elevable un 20-30% en momentos concretos.",
                    "El punto de atención aquí es el envío. Los muebles y sillas suelen tener envío más caro o restringido, y eso puede borrar la ventaja del descuento. Comprueba el coste de envío total antes de decidir.",
                    "En escritorios, la tendencia actual hacia los escritorios regulables en altura ha creado un mercado con mucha rotación, y las ofertas de esa categoría aparecen con frecuencia en el canal.",
                ],
            ),
            (
                "Cuadernos, papelería y pequeño material: compras de impulso",
                [
                    "Los cuadernos, agendas y libretas son compras pequeñas donde lo que importa es el precio por hoja y la calidad del papel. Los cuadernos de Econfil o Oxford son los más buscados y bajan con frecuencia.",
                    "El pequeño material (rotuladores, marcadores, grapadoras) son compras de bajo importe. Aquí la lógica es de volumen: no merece la pena optimizarlos mucho, pero un pack a buen precio es una compra fácil.",
                    "Las agendas y planners son otra categoría con ciclo propio: bajan en enero, cuando empieza el año, y en septiembre, antes de la vuelta al cole.",
                ],
            ),
            (
                "Papelería, material escolar y la vuelta al cole: cuándo comprar",
                [
                    "La vuelta al cole es, con diferencia, el mejor momento para comprar material escolar. Entre julio y septiembre los precios bajan más que en ninguna otra época del año, y ahí es donde aparecen las ofertas de packs de material más competitivas.",
                    "Fuera de esa ventana, el precio del material escolar se mantiene estable todo el año y las ofertas son puntuales. Si no tienes prisa y puedes comprar en agosto, es la decisión más inteligente que puedes tomar en esta categoría.",
                    "En papelería de oficina (papel, tinta, carpetas) el patrón es diferente: no hay estacionalidad, pero sí rotación constante. Los productos de marca tienen precio fijo, y los genéricos bajan cuando hay exceso de stock. Comprueba la diferencia de precio por unidad antes de decidir.",
                ],
            ),
        ],
        "como_elegir": [
            ("Divide el precio del pack entre las unidades", "Es el consejo más útil de toda la categoría. Casi todas las ofertas buenas de papelería son packs, y el precio por unidad es lo que las hace buenas o no."),
            ("La vuelta al cole es tu fecha", "Entre julio y septiembre bajan los precios del material escolar. Si no tienes prisa, esa es la ventana más barata del año para esta categoría."),
            ("Cuenta con el envío en muebles", "En sillas y escritorios, el envío puede comerse el descuento. Mira el precio final con envío antes de decidir."),
            ("Marca y genérico: no siempre es todo", "En papería básica la diferencia entre marca y genérico es menor que en otras categorías, y el pack de genéricos bien valorados suele ganar. En escritorios y sillas, la marca sí importa."),
        ],
        "faq": [
            (
                "¿Cada cuánto se actualizan las ofertas de papelería?",
                "En cuanto se publica algo en el canal. En esta categoría el movimiento se concentra entre julio y septiembre, con la vuelta al cole, y en enero con las agendas.",
            ),
            (
                "¿Por qué los descuentos en papelería parecen más bajos?",
                "Porque en productos de pequeño importe el chollo está en el precio por unidad de un pack, no en el porcentaje de la etiqueta. Un pack de material escolar puede tener un 15% de descuento y ser una ganga si el precio por unidad es bajo.",
            ),
            (
                "¿Los escritorios y sillas se envían gratis?",
                "Depende del producto y del vendedor. En muebles y sillas el envío suele tener coste y a veces supera la diferencia entre el precio de oferta y el habitual. Comprueba el precio total con envío antes de comprar.",
            ),
        ],
        "relacionados": ["general", "juguetes-infantil", "moviles-electronica"],
    },

    "general": {
        "titulo_seo": "Chollos y ofertas de Amazon España | GangasOfertas",
        "descripcion": (
            "Chollos, ofertas y errores de precio de Amazon España en un solo feed: "
            "ropa, tecnología, gaming y juguetes. Actualizado desde el canal."
        ),
        "h1": "Todos los chollos y ofertas de Amazon España",
        "intro": [
            "Esta es la lista completa: todo lo que se publica en el canal de Telegram, ordenado de más reciente a más antiguo y sin filtrar por categoría. Si buscas una sección concreta, las páginas de categorías te van mejor; si buscas ver todo lo que hay ahora mismo, quédate aquí.",
            "El feed se actualiza en cuanto entra una oferta nueva en el canal. No hay un horario: lo que se publica en Telegram aparece aquí. Cada oferta incluye el título del producto, el precio detectado, el descuento si lo conocemos y el enlace directo a Amazon España.",
            "Un recordatorio honesto sobre cómo funciona esta web: no rastreamos Amazon ni seguimos sus precios de forma continua. Recopilamos las ofertas que se anuncian en nuestro canal de Telegram, y Amazon es quien decide en cada momento si ese precio sigue disponible. Lo que ves aquí es real, pero puede caducar en minutos.",
        ],
        "secciones": [
            (
                "Qué puedes encontrar en este feed",
                [
                    "El feed completo mezcla todas las categorías: ropa y calzado, móviles y electrónica, gaming y consolas, higiene y cuidado personal, juguetes e infantil, y papelería y oficina. Cada oferta va etiquetada con su categoría, así que puedes filtrar mentalmente por donde te interese.",
                    "Entre las ofertas que publicamos hay de dos tipos: chollos con descuento claro y, de vez en cuando, errores de precio. Los errores de precio son más albuminantes y duran minutos; los chollos con descuento duran más.",
                    "No verificamos cada oferta contra el historial de precios antes de publicarla: publicamos lo que llega al canal. Eso significa que el descuento que ves es el que se detecto, y puede haber ofertas cuyo «antes» esté inflado. Para compras importantes, comprueba el historial.",
                ],
            ),
            (
                "Cómo aprovechar mejor este feed",
                [
                    "Los chollos más Linguisticsinteropue se agotan rápido, así que la velocidad importa. Si ves una oferta que te interesa, ve al enlace pronto: esperar a «confirmarlo» significa volver a tiempo y que ya no esté.",
                    "Para no perderte nada, lo más efectivo es el canal de Telegram. Cada oferta que aparece aquí sehaw publicado antes en el canal, y en Telegram llegas a ella en el momento en que se publica. La web es para consultar con calma; el canal es para la velocidad.",
                    "Si compras mucho aquí, activa las alertas de precio de Amazon o de herramientas como Keepa para los productos que ya tienes fichados. Para lo que aún no conoces, el canal es más útil, porque te avisa de cosas que no estabas buscando.",
                ],
            ),
            (
                "La diferencia entre un chollo y un error de precio",
                [
                    "Un chollo es un producto a un precio claramente inferior al habitual, dentro de lo razonable. Un error de precio es un fallo del sistema: el producto aparece a una fracción de su precio, muchas veces la décima parte, por un error de decimales o una conversión de divisas mal hecha.",
                    "Los errores de precio son ilmante lifeless, duran minutos u horas, y Amazon puede cancelar el pedido si detecta el error. La consecuencia práctica es la misma en ambos casos: si lo ves, actúa rápido y compra poca cantidad (una o dos unidades), porque un pedido grande a precio de error es la forma más fácil de que te lo cancelen.",
                    "Si tienes dudas sobre si una oferta es un error de precio o una estafa, mira quién es el vendedor. Un precio erróneo en Amazon, vendido por Amazon, es un error. Un precio imposible en una tienda desconocida es, casi con toda probabilidad, una estafa.",
                ],
            ),
        ],
        "como_elegir": [
            ("Mira el precio y la fecha juntos", "Una oferta de hace una semana puede tener ya un sustituto más barato por el mismo precio. La fecha es parte de la información del chollo."),
            ("El descuento más alto no es el mejor chollo", "Un 70% sobre un precio inflado puede salir más caro que un 30% sobre el precio real. Lo que manda es el precio final, no el porcentaje."),
            ("Comprueba el vendedor en ofertas grandes", "En ofertas de importe alto, fíjate en si es Amazon directamente o un vendedor externo con buenas valoraciones. Es la diferencia entre una compra tranquila y unasymbols conRJProduct que puede salir mal."),
            ("Para compras importantes, mira el historial", "Publicamos lo que llega al canal sin filtrar por mínimo histórico. Si vas a gastar una cantidad importante, comprobar el gráfico de precios del producto evita sorpresas."),
        ],
        "faq": [
            (
                "¿Cada cuánto se actualiza este feed?",
                "En cuanto se publica una oferta nueva en el canal de Telegram. No hay un horario fijo: si no ha entrado nada nuevo, la lista no cambia.",
            ),
            (
                "¿Estos precios son los definitivos?",
                "Son los detectados en el canal en el momento de publicarse la oferta. Amazon puede cambiarlos cuando quiera, y en un error de precio puede cancelar el pedido. El precio final es siempre el de la ficha de Amazon.",
            ),
            (
                "¿Publicáis los errores de precio o solo chollos?",
                "Publicamos lo que llega al canal, y de vez en cuando llegan errores de precio. No los distinguimos de forma automática, así que parte de las ofertas son rebajas normales y parte son errores. El canal lo indica cuando es un error evidente.",
            ),
            (
                "¿Por qué solo aparecen productos de Amazon?",
                "Porque las ofertas del canal son enlaces de Amazon. Cada oferta publicada lleva su enlace de Amazon España, y por eso todos los precios y descuentos se refieren a Amazon.",
            ),
            (
                "¿Necesito crear una cuenta para ver las ofertas?",
                "No. Ni la web ni el canal requieren registro. Puedes consultar todo y, si quieres alertas en el móvil, unirte al canal de Telegram, que también es gratuito.",
            ),
        ],
        "relacionados": ["moviles-electronica", "ropa-y-calzado", "gaming-consolas"],
    },
}


def claves():
    """Slas de las categorías que tienen contenido editorial."""
    return list(CONTENIDO)