/* ============================================================
   GangasOfertas.com - carga del catalogo
   Las paginas de catalogo unicamente declaran:
     <body data-feed="moviles-electronica">
     <h1 data-titulo-feed="...">
   y este script se encarga del resto.
   ============================================================ */
(function () {
  "use strict";

  var cuerpo = document.body;
  var feed = cuerpo.dataset.feed || "general";
  var contenedor = document.getElementById("ofertas");
  var estado = document.getElementById("estado");
  var DATA_URL = "data/" + encodeURIComponent(feed) + ".json";

  /* ---------- utilidades ---------- */
  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  // Solo se permiten enlaces de Amazon o de acortadores de Amazon.
  // Se valida el hostname ENTERO contra dos patrones, no el dominio padre:
  //
  //   Amazon         -> "amazon." seguido de "com" o de un ccTLD de 2 letras,
  //                     y como mucho un label mas ("amazon.com.mx",
  //                     "amazon.co.uk"). Todos los tiendas de Amazon reales
  //                     acaban asi.
  //   Acortadores    -> amzn.to / amzn.eu / amzn.link y amzlink.to / .eu /
  //                     .link. El ultimo es el que usa el canal (bot.py
  //                     DOMINIOS_LINK lo acepta) y antes se bloqueaba aqui:
  //                     la tarjeta salia con href="#" y el boton no llevaba a
  //                     ninguna parte.
  //
  // Mirar solo el penultimo label (el caso de "amazon.es.evil.com") dejaba
  // pasar "amazon.evil" y "amazon.zip": su padre es "amazon" y .evil/.zip son
  // TLDs reales, aunque dearketing, no de Amazon. Exigir que el TLD sea "com" o
  // un ccTLD de 2 letras los deja fuera sin tener que mantener una lista de
  // dominios de Amazon, que cambia cada vez que Amazon abre un pais.
  var RE_HOST_AMAZON = /^(?:[a-z0-9-]+\.)*amazon\.(?:com|[a-z]{2})(?:\.[a-z]{2})?$/;
  var RE_HOST_ACORTADOR = /^(?:[a-z0-9-]+\.)*(?:amzn|amzlink)\.(?:to|eu|link)$/;

  function urlSegura(url) {
    try {
      var u = new URL(String(url || ""), window.location.href);
      if (u.protocol !== "https:" && u.protocol !== "http:") return "#";
      // "amazon.es." con punto final es la misma tienda en forma FQDN y el DNS lo
// resuelve igual, asi que se quita antes de comparar.
      var host = u.hostname.toLowerCase().replace(/\.$/, "");
      if (!RE_HOST_AMAZON.test(host) && !RE_HOST_ACORTADOR.test(host)) return "#";
      return u.href;
    } catch (e) {
      return "#";
    }
  }

  function limpiarTitulo(t) {
    return esc(String(t || "Oferta Amazon").replace(/\*{1,3}/g, "").trim());
  }

  // El bot ya normaliza a "1234.56 €", pero se admiten las dos convenciones
  // por si el JSON se ha editado a mano.
  function precioAMayor(es) {
    var s = String(es == null ? "" : es).replace(/[^\d.,]/g, "");
    if (!s) return null;
    if (s.indexOf(",") >= 0 && s.indexOf(".") >= 0) {
      // con ambos separadores, el que aparece mas a la derecha es el decimal
      s = s.lastIndexOf(",") > s.lastIndexOf(".")
        ? s.replace(/\./g, "").replace(",", ".")
        : s.replace(/,/g, "");
    } else if (s.indexOf(",") >= 0) {
      var decimales = s.slice(s.lastIndexOf(",") + 1);
      s = decimales.length === 2 ? s.replace(",", ".") : s.replace(/,/g, "");
    }
    var n = parseFloat(s);
    return isNaN(n) ? null : n.toFixed(2);
  }

  function fechaLarga(iso) {
    if (!iso) return null;
    var d = new Date(iso);
    return isNaN(d.getTime()) ? null : d.toISOString().slice(0, 10);
  }

  /* ---------- las tres cifras de precio ----------
     En la tarjeta tienen que verse SIEMPRE el precio actual, el precio
     anterior y el porcentaje de descuento. El bot no los deja siempre en sus
     campos: cuando el precio anterior no viene en el formato del canal
     ("🏷️ Antes: ...") lo guarda vacio, aunque el dato sigue ahi dentro del
     texto, del tipo "172,99 € (antes 296,06 €)". Asi que se buscan en cascada
     (campo -> descripcion -> titulo) y, si aun falta el porcentaje, se calcula
     a partir de los dos precios. Lo que no se puede averiguar se pinta como
     hueco explicito, nunca desaparece. */

  var RE_ANTES = /\b(?:antes|pvp|precio\s+anterior|val(?:or|ia)\s+anterior)\b\s*(?:de\s*)?[:\-]?\s*([0-9][0-9.,\u00a0 ]*)\s*(?:\u20ac|eur)?/i;
  // Un "%" suelto no es un descuento ("80% de bateria nueva"), asi que se
  // recoge el primero y se mira el texto que lo rodea: solo vale si el contexto
  // lo marca como rebaja (signo negativo, parentesis, o la palabra al lado).
  var RE_PORCENTAJE = /(\d{1,3}(?:[.,]\d+)?)\s*%/g;
  var RE_PORCENTAJE_EN = /descuento|ahorro|rebaja|\boff\b/i;

  function euros(n) {
    return n.toFixed(2) + " \u20ac";
  }

  function aNumero(valor) {
    var s = precioAMayor(valor);
    return s === null ? null : parseFloat(s);
  }

  // Descripcion y titulo: es donde suele quedarse el precio anterior.
  function textoOferta(o) {
    return String(o.description || "") + " \n " + String(o.title || "");
  }

  function descuentoEnTexto(texto) {
    RE_PORCENTAJE.lastIndex = 0;
    var m;
    while ((m = RE_PORCENTAJE.exec(texto)) !== null) {
      var pct = parseFloat(m[1].replace(",", "."));
      if (!(pct > 0) || pct >= 100) continue;
      var antes = texto.slice(Math.max(0, m.index - 26), m.index);
      var despues = texto.slice(m.index + m[0].length, m.index + m[0].length + 24);
      // "-46%", "(-40%)" o "24% de descuento" entran; "80% de bateria" no.
      if (/[-\u2212\u2013(]\s*$/.test(antes) || RE_PORCENTAJE_EN.test(despues)) {
        return Math.round(pct);
      }
    }
    return null;
  }

  function precioAnteriorDe(o, actual) {
    var candidatos = [o.old_price];
    var m = RE_ANTES.exec(textoOferta(o));
    if (m) candidatos.push(m[1]);
    for (var i = 0; i < candidatos.length; i++) {
      var n = aNumero(candidatos[i]);
      // Solo vale como "antes" si es MAYOR que el precio actual: si no, es
      // ruido del parser y se descarta, porque no hay ninguna rebaja que pintar.
      if (n !== null && n > 0 && (actual === null || n > actual)) return n;
    }
    return null;
  }

  function descuentoDe(o, actual, anterior) {
    var candidatos, i, n;
    // 1. Con los dos precios disponibles, el porcentaje sale de ellos: asi la
    //    cifra resaltada nunca contradice a los precios que se ven al lado.
    if (actual !== null && actual > 0 && anterior !== null && anterior > actual) {
      var pct = Math.round(((anterior - actual) / anterior) * 100);
      return pct > 0 ? pct : null;
    }
    // 2. Si no hay precio anterior, se usa el descuento del bot o el que
    //    aparece escrito en la descripcion o el titulo.
    candidatos = [o.discount];
    var delTexto = descuentoEnTexto(textoOferta(o));
    if (delTexto !== null) candidatos.push(delTexto);
    for (i = 0; i < candidatos.length; i++) {
      n = aNumero(candidatos[i]);
      if (n !== null && n > 0 && n < 100) return Math.round(n);
    }
    return null;
  }

  // Las tres cifras juntas y ya resueltas, para pintar la tarjeta.
  // Los null significan "no se ha podido averiguar": se muestran igual, como
  // hueco, para que la composicion de todas las ofertas sea la misma.
  function preciosDe(o) {
    var actualNum = aNumero(o.price);
    var anteriorNum = precioAnteriorDe(o, actualNum);
    var pct = descuentoDe(o, actualNum, anteriorNum);
    return {
      actualNum: actualNum,
      anteriorNum: anteriorNum,
      actual: o.price ? String(o.price) : (actualNum !== null ? euros(actualNum) : null),
      anterior: anteriorNum === null ? null : euros(anteriorNum),
      descuento: pct === null ? null : "-" + pct + "%"
    };
  }

  /* ---------- JSON-LD dinamico: ItemList + Offer detallado ---------- */
  function inyectarSchema(ofertas) {
    var items = ofertas.map(function (o) {
      return { oferta: o, precios: preciosDe(o) };
    }).filter(function (x) { return x.precios.actualNum !== null; });
    if (!items.length) return;

    var lista = {
      "@context": "https://schema.org",
      "@type": "ItemList",
      "name": (document.querySelector("h1") || {}).textContent || "Ofertas",
      "numberOfItems": items.length,
      "itemListElement": items.slice(0, 20).map(function (x, i) {
        var o = x.oferta;
        var p = x.precios;
        var oferta = {
          "@type": "ListItem",
          "position": i + 1,
          "item": {
            "@type": "Offer",
            "name": String(o.title || "Oferta Amazon").replace(/\*/g, "").trim(),
            "url": urlSegura(o.amazon_url),
            "priceCurrency": "EUR",
            "price": p.actualNum.toFixed(2),
            "availability": "https://schema.org/InStock",
            "itemCondition": "https://schema.org/NewCondition",
            "seller": { "@type": "Organization", "name": "Amazon España" }
          }
        };
        // Añadir imagen si existe
        if (o.image) {
          oferta.item.image = o.image;
        }
        // Añadir descripcion si existe
        if (o.description) {
          oferta.item.description = o.description;
        }
        // Añadir marca si existe
        if (o.brand) {
          oferta.item.brand = { "@type": "Brand", "name": o.brand };
        }
        // Añadir GTIN si existe. Un GTIN solo son digitos con el control validado
        // (ver extraer_gtin en bot.py); los codigos de pieza van en "mpn".
        if (o.gtin) {
          oferta.item.gtin = o.gtin;
        }
        if (o.mpn) {
          oferta.item.mpn = o.mpn;
        }
        // Precio anterior (y por tanto el descuento) si se ha podido averiguar
        if (p.anteriorNum !== null) {
          oferta.item.priceSpecification = {
            "@type": "PriceSpecification",
            "price": p.actualNum.toFixed(2),
            "priceCurrency": "EUR",
            "highPrice": p.anteriorNum.toFixed(2)
          };
        }
        return oferta;
      })
    };

    var script = document.createElement("script");
    script.type = "application/ld+json";
    script.textContent = JSON.stringify(lista);
    document.head.appendChild(script);
  }

  /* ---------- contador de vistas ---------- */
  var _vistas = {};
  try { _vistas = JSON.parse(localStorage.getItem('vistas_ofertas') || '{}'); } catch (e) { _vistas = {}; }
  function guardarVistas() {
    try { localStorage.setItem('vistas_ofertas', JSON.stringify(_vistas)); } catch (e) {}
  }
  function formatearVistas(n) {
    if (n >= 1000000) return (n / 1000000).toFixed(1).replace('.0','') + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1).replace('.0','') + 'K';
    return String(n);
  }

  /* ---------- render ---------- */
  function render(ofertas) {
    if (!Array.isArray(ofertas)) {
      mostrarEstado("El archivo de ofertas tiene un formato no válido.");
      return;
    }
    if (ofertas.length === 0) {
      mostrarEstado(
        "Todavía no hay ofertas publicadas en esta sección. " +
        "Únete al canal de Telegram para recibirlas en cuanto se publiquen."
      );
      return;
    }

    if (estado) estado.remove();

    contenedor.innerHTML = ofertas.map(function (o) {
      var fecha = "";
      if (o.date) {
        var d = new Date(o.date);
        if (!isNaN(d)) fecha = d.toLocaleDateString("es-ES");
      }
      var url = urlSegura(o.amazon_url);
      var img = o.image
        ? '<div class="oferta-img"><img src="' + esc(o.image) + '" alt="' +
          limpiarTitulo(o.title) + '" loading="lazy" decoding="async" itemprop="image"></div>'
        : "";

      // Precio actual, precio anterior y descuento: los tres campos se pintan
      // siempre. Cuando un dato no se ha podido averiguar, se muestra como
      // "hueco" (sin tachar / sin chollo) en vez de desaparecer, para que la
      // tarjeta sea igual de legible en todas las ofertas.
      var p = preciosDe(o);
      var preciosHtml =
        '<div class="oferta-precios">' +
          '<div class="oferta-precio-caja">' +
            '<span class="oferta-precio-etiqueta">Precio actual</span>' +
            '<span class="oferta-precio" itemprop="price" content="' +
              (p.actualNum === null ? "" : p.actualNum.toFixed(2)) + '">' +
              esc(p.actual || "Ver precio") + "</span>" +
          "</div>" +
          '<div class="oferta-precio-caja">' +
            '<span class="oferta-precio-etiqueta">Precio anterior</span>' +
            '<span class="oferta-precio-antes' + (p.anterior ? "" : " es-hueco") + '">' +
              esc(p.anterior || "No disponible") + "</span>" +
          "</div>" +
          '<div class="oferta-precio-caja oferta-precio-caja--descuento' +
              (p.descuento ? "" : " es-hueco") + '">' +
            '<span class="oferta-precio-etiqueta">Descuento</span>' +
            '<span class="oferta-descuento' + (p.descuento ? "" : " es-hueco") + '">' +
              esc(p.descuento || "Sin descuento") + "</span>" +
          "</div>" +
        "</div>";

      // Contador de vistas (localStorage)
      var id = o.id || Math.random().toString(36).slice(2);
      _vistas[id] = (_vistas[id] || 0) + 1;
      guardarVistas();
      var vistasHtml = '<div class="oferta-vistas">👁 ' + formatearVistas(_vistas[id]) + ' vistas</div>';

      // Microdata Schema.org para que Google indexe cada oferta como producto
      var descHtml = o.description
        ? '<div class="oferta-descripcion" itemprop="description">' + esc(o.description) + "</div>"
        : "";
      var brandMeta = o.brand
        ? '<meta itemprop="brand" content="' + esc(o.brand) + '">'
        : "";
      var gtinMeta = o.gtin
        ? '<meta itemprop="gtin" content="' + esc(o.gtin) + '">'
        : "";
      // El MPN (codigo de pieza) va en su propia propiedad: publicar un MPN
      // como "gtin" es informacion falsa, y el bot ya los separa.
      var mpnMeta = o.mpn
        ? '<meta itemprop="mpn" content="' + esc(o.mpn) + '">'
        : "";
      return '<article class="oferta" itemscope itemtype="https://schema.org/Offer">' +
          img +
          '<div class="oferta-cuerpo">' +
            '<div class="oferta-titulo" itemprop="name">' + limpiarTitulo(o.title) + "</div>" +
            preciosHtml +
            '<div class="oferta-meta">' + esc(fecha) + "</div>" +
            vistasHtml +
            descHtml +
          "</div>" +
          '<a class="oferta-comprar" href="' + esc(url) +
            '" target="_blank" rel="nofollow sponsored noopener" itemprop="url">Ver oferta en Amazon</a>' +
          '<meta itemprop="priceCurrency" content="EUR">' +
          '<meta itemprop="availability" content="https://schema.org/InStock">' +
          '<meta itemprop="itemCondition" content="https://schema.org/NewCondition">' +
          '<meta itemprop="seller" content="Amazon España">' +
          brandMeta +
          gtinMeta +
          mpnMeta +
        "</article>";
    }).join("");

    // Si la imagen no carga, se oculta la caja en lugar de dejar un hueco.
    contenedor.addEventListener("error", function (ev) {
      if (ev.target.tagName === "IMG" && ev.target.parentElement) {
        ev.target.parentElement.style.display = "none";
      }
    }, true);

    inyectarSchema(ofertas);
  }

  function mostrarEstado(texto) {
    // Hay dos formas de colocar el mensaje de estado en las páginas:
    //   - Páginas de catálogo: el #estado ES el placeholder, dentro de #ofertas.
    //     Basta con reescribirlo.
    //   - black-friday-2026.html: el #estado es un <p> aparte y "Cargando
    //     ofertas..." vive dentro de #ofertas. Si no se vacía el contenedor,
    //     el texto de carga se queda pegado al lado del error.
    var estadoDentro = estado && estado.parentElement === contenedor;
    if (estadoDentro) {
      estado.textContent = texto;
      return;
    }
    contenedor.innerHTML = "";
    if (estado) {
      estado.textContent = texto;
    } else {
      contenedor.innerHTML = '<div class="estado">' + esc(texto) + "</div>";
    }
  }

  /* ---------- arranque ---------- */
  fetch(DATA_URL + "?v=" + Date.now(), { cache: "no-store" })
    .then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    })
    .then(render)
    .catch(function (err) {
      console.error("Error al cargar " + DATA_URL, err);
      mostrarEstado("No se han podido cargar las ofertas. Inténtalo de nuevo en unos segundos.");
    });
})();
