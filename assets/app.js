/* ============================================================
   Chollos Ofertas Gangas - carga del catalogo
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
  // El TLD varia (amazon.es, amazon.com, amazon.de...), asi que se comprueba
  // el dominio padre en lugar de una lista fija: asi "amazon.es.evil.com"
  // queda fuera, que un /(^|\.)amazon\.[a-z.]+$/ dejaba pasar.
  function urlSegura(url) {
    try {
      var u = new URL(String(url || ""), window.location.href);
      var partes = u.hostname.toLowerCase().split(".");
      var padre = partes[partes.length - 2] || "";
      if (!/^(amazon|amzn)$/.test(padre)) return "#";
      if (u.protocol !== "https:" && u.protocol !== "http:") return "#";
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

  /* ---------- JSON-LD dinamico: ItemList + Offer detallado ---------- */
  function inyectarSchema(ofertas) {
    var conPrecio = ofertas.filter(function (o) { return precioAMayor(o.price) !== null; });
    if (!conPrecio.length) return;

    var lista = {
      "@context": "https://schema.org",
      "@type": "ItemList",
      "name": (document.querySelector("h1") || {}).textContent || "Ofertas",
      "numberOfItems": conPrecio.length,
      "itemListElement": conPrecio.slice(0, 20).map(function (o, i) {
        var precio = precioAMayor(o.price);
        var oferta = {
          "@type": "ListItem",
          "position": i + 1,
          "item": {
            "@type": "Offer",
            "name": String(o.title || "Oferta Amazon").replace(/\*/g, "").trim(),
            "url": urlSegura(o.amazon_url),
            "priceCurrency": "EUR",
            "price": precio,
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
        // Añadir GTIN/MPN si existe
        if (o.gtin) {
          oferta.item.gtin = o.gtin;
        }
        // Añadir precio anterior si existe
        if (o.old_price) {
          oferta.item.priceSpecification = {
            "@type": "PriceSpecification",
            "price": precio,
            "priceCurrency": "EUR"
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
      var precio = precioAMayor(o.price);
      var img = o.image
        ? '<div class="oferta-img"><img src="' + esc(o.image) + '" alt="' +
          limpiarTitulo(o.title) + '" loading="lazy" decoding="async" itemprop="image"></div>'
        : "";
      // Precio anterior tachado + descuento, cuando el mensaje los trae
      var anterior = o.old_price
        ? '<span class="oferta-precio-antes">' + esc(o.old_price) + "</span>"
        : "";
      var descuento = o.discount
        ? '<span class="oferta-descuento">' + esc(o.discount) + "</span>"
        : "";

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
      return '<article class="oferta" itemscope itemtype="https://schema.org/Offer">' +
          img +
          '<div class="oferta-cuerpo">' +
            '<div class="oferta-titulo" itemprop="name">' + limpiarTitulo(o.title) + "</div>" +
            '<div class="oferta-precios">' + anterior +
              '<span class="oferta-precio" itemprop="price" content="' + (precio || "") + '">' + esc(o.price || "Ver precio") + "</span>" +
              descuento +
            "</div>" +
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
