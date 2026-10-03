/* ==========================================================================
   GangasOfertas.com — Black Friday 2026
   JS mínimo y progresivamente mejorado. El sitio funciona sin JS:
   - El FAQ usa <details>/<summary> nativo
   - El countdown muestra texto estático si no hay JS
   ========================================================================== */
(function () {
  "use strict";

  /* ----------------------------------------------------------------------
     1. Menú móvil
     ---------------------------------------------------------------------- */
  var toggle = document.querySelector(".nav__toggle");
  var links = document.getElementById("nav-links");

  if (toggle && links) {
    toggle.addEventListener("click", function () {
      var open = links.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute("aria-label", open ? "Cerrar menú" : "Abrir menú");
    });

    // Cerrar al navegar
    links.addEventListener("click", function (e) {
      if (e.target.closest("a")) {
        links.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });

    // Cerrar al pulsar Escape
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && links.classList.contains("is-open")) {
        links.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.focus();
      }
    });
  }

  /* ----------------------------------------------------------------------
     2. Cuenta atrás → Black Friday 2026 (viernes 27 de noviembre, 00:00
        hora peninsular española, CET/CEST). Se fija a esa fecha local para
        no depender del zona horario del visitante.
     ---------------------------------------------------------------------- */
  var countdown = document.getElementById("countdown");

  if (countdown) {
    // Martínes 27 de noviembre de 2026, 00:00 hora peninsular (Madrid).
    var TARGET = new Date(2026, 10, 27, 0, 0, 0);

    var cells = {
      days: countdown.querySelector('[data-unit="days"]'),
      hours: countdown.querySelector('[data-unit="hours"]'),
      mins: countdown.querySelector('[data-unit="mins"]'),
      secs: countdown.querySelector('[data-unit="secs"]'),
      label: countdown.querySelector('[data-countdown-label]')
    };

    var pad = function (n) { return String(n).padStart(2, "0"); };

    function tick() {
      var now = new Date();
      var diff = TARGET.getTime() - now.getTime();

      if (diff <= 0) {
        if (cells.days) cells.days.textContent = "00";
        if (cells.hours) cells.hours.textContent = "00";
        if (cells.mins) cells.mins.textContent = "00";
        if (cells.secs) cells.secs.textContent = "00";
        if (cells.label) {
          cells.label.textContent = "¡Es Black Friday! Ofertas activas ahora mismo 👇";
        }
        return false; // detiene el intervalo
      }

      var s = Math.floor(diff / 1000);
      var d = Math.floor(s / 86400);
      var h = Math.floor((s % 86400) / 3600);
      var m = Math.floor((s % 3600) / 60);
      var sec = s % 60;

      if (cells.days) cells.days.textContent = pad(d);
      if (cells.hours) cells.hours.textContent = pad(h);
      if (cells.mins) cells.mins.textContent = pad(m);
      if (cells.secs) cells.secs.textContent = pad(sec);

      return true;
    }

    if (tick()) {
      var id = setInterval(function () { if (!tick()) clearInterval(id); }, 1000);
    }

    // Actualizar también los <time> de fechas destacadas de la página.
    var dates = document.querySelectorAll("[data-date-target]");
    if (dates.length) {
      var months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
        "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
      var iso = TARGET.getFullYear() + "-" +
        pad(TARGET.getMonth() + 1) + "-" + pad(TARGET.getDate());
      dates.forEach(function (el) {
        el.textContent = "27 de " + months[TARGET.getMonth()] + " de 2026 (" + iso + ")";
      });
    }
  }

  /* ----------------------------------------------------------------------
     3. FAQ: botón "desplegar todo / plegar todo"
     ---------------------------------------------------------------------- */
  var faqToggle = document.querySelector("[data-faq-toggle]");

  if (faqToggle) {
    faqToggle.addEventListener("click", function () {
      var box = faqToggle.getAttribute("data-faq-target");
      var group = box && document.getElementById(box);
      if (!group) return;

      var items = group.querySelectorAll("details");
      var anyClosed = Array.prototype.some.call(items, function (d) { return !d.open; });

      Array.prototype.forEach.call(items, function (d) { d.open = anyClosed; });
      faqToggle.textContent = anyClosed ? "Plegar todas" : "Desplegar todas";
      faqToggle.setAttribute("aria-expanded", anyClosed ? "true" : "false");
    });
  }

  /* ----------------------------------------------------------------------
     4. Marcar el enlace externo al canal de Telegram
        (no es estrictamente necesario, pero evita abrir en otra pestaña
        al hacer clic en los CTA principales desde la portada)
     ---------------------------------------------------------------------- */
  var tgLinks = document.querySelectorAll('a[href^="https://t.me/GangasOfertasChollos"]');
  Array.prototype.forEach.call(tgLinks, function (a) {
    a.setAttribute("data-channel", "GangasOfertasChollos");
  });

  /* ----------------------------------------------------------------------
     5. Marca la navegación activa según la URL actual
     ---------------------------------------------------------------------- */
  var here = location.pathname.split("/").pop() || "index.html";
  var navA = document.querySelectorAll(".nav__links > a");

  Array.prototype.forEach.call(navA, function (a) {
    var href = a.getAttribute("href");
    if (!href) return;
    var file = href.split("#")[0].split("/").pop();
    if (file && file === here) a.setAttribute("aria-current", "page");
  });
})();