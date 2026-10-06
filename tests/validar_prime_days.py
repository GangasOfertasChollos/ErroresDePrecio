"""Detecta texto corrupto en el HTML generado.

Motivo: el contenido de esta seccion son varios miles de palabras escritas a
mano, y un token puede quedar corrupto (caracteres de otro alfabeto, restos de
unotescritura anterior) sin que se note leyendo el codigo. Este script lo
comprueba de forma mecanica para que no llegue a produccion.

Que busca:
  - caracteres fuera del rango latino usado en espanol (CJK, cirilico, ...)
  - marcadores de texto sin terminar que suelen salir al editar
  - palabras sueltas que no pertenecen a la pagina

Uso:  python tests/validar_prime_days.py
Salida: 0 si todo correcto, 1 si hay texto corrupto.
"""
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SECCION = RAIZ / "PrimeDays"

fallos = []

# Caracteres permitidos: ASCII, latines extendidos (á é í ó ú ñ ü ç), signos de
# puntuacion, flechas, emojis y simbolos tipograficos habituales. Todo lo demas
# (chino, japones, cirilico, arabe, hebreo, devanagari...) es corrupcion.
PERMITIDOS_EXTRA = set(
    "áéíóúüñÁÉÍÓÚÜÑçÇ¿¡«»“”‘’–—…·•€£¥©®™°±×÷≈≤≥→←↑↓↔▪▸►■□●○★☆♦✓″′⁄"
)

# Palabras que delatan un token roto de otra escritura. Se buscan como
# palabra completa (\b) en el texto sin etiquetas.
#
# Nota: antes estaba " edad " entre estas. Es una palabra española legitima
# ("juguetes por edad") y aparecio en contenido real, asi que era un falso
# positivo que no distinguia corrupcion de texto correcto. No se ha
# sustituido por otra: un token roto no es una palabra, lo detectan las
# comprobaciones de alfabetos de mas abajo, que ahora cubren tambien Hangul y
# CJK (ver _es_letra_extranjera).
SOSPECHOSOS_PALABRA = [
    "kernel", "LZWR", "TIMING", "Thereafter", "Command",
]


# Alfabetos que se colaron al escribir y que hay que cazar aunque su nombre
# Unicode NO contenga la palabra LETTER. Sin esto, Hangul y CJK pasaban: sus
# nombres son "HANGUL SYLLABLE .." y "CJK UNIFIED IDEOGRAPH-..", y el filtro
# de abajo los daba por buenos. Se encontraron cuatro justo asi (ver git log).
ALFABETOS_NO_LATINOS = (
    "HANGUL",
    "CJK",
    "IDEOGRAPH",
    "HIRAGANA",
    "KATAKANA",
    "CYRILLIC",
    "GREEK",
    "ARABIC",
    "HEBREW",
    "DEVANAGARI",
    "THAI",
    "ARMENIAN",
    "GEORGIAN",
)


def _es_letra_extranjera(nombre: str) -> bool:
    """True si el caracter es una letra de un alfabeto no latino.

    Se accepta LATIN (con o sin acento) y los simbolos; el resto se marca.
    """
    for prefijo in ALFABETOS_NO_LATINOS:
        if nombre.startswith(prefijo):
            return True
    if "LETTER" not in nombre:
        return False
    # Las letras latinas con acento y la Ø/Đ son legitimas en nombres de
    # producto.
    return not nombre.startswith("LATIN")


def revisar(archivo: Path) -> None:
    texto = archivo.read_text(encoding="utf-8")

    # 1. Caracteres de alfabetos no latinos.
    for num_linea, linea in enumerate(texto.splitlines(), 1):
        for ch in linea:
            if ch in PERMITIDOS_EXTRA or ch.isascii():
                continue
            try:
                nombre = unicodedata.name(ch)
            except ValueError:
                nombre = "desconocido"
            # Emoji y simbolos van bien; lo que buscamos son letras de otros
            # alfabetos, que en un texto en espanol siempre son corrupcion.
            if _es_letra_extranjera(nombre):
                fallos.append(
                    f"{archivo.name}:{num_linea} caracter fuera del español: "
                    f"{ch!r} (U+{ord(ch):04X} {nombre}) en: {linea.strip()[:80]}"
                )

    # 2. Marcadores de texto sin cerrar.
    for num_linea, linea in enumerate(texto.splitlines(), 1):
        if linea.count('"') % 2 or linea.count("«") != linea.count("»"):
            fallos.append(f"{archivo.name}:{num_linea} comillas o angulares sin cerrar: {linea.strip()[:80]}")

    # 3. Palabras sospechosas de tokens rotos.
    plano = re.sub(r"<[^>]+>", " ", texto)
    for palabra in SOSPECHOSOS_PALABRA:
        if re.search(rf"\b{re.escape(palabra)}\b", plano):
            for num_linea, linea in enumerate(plano.splitlines(), 1):
                if re.search(rf"\b{re.escape(palabra)}\b", linea):
                    fallos.append(
                        f"{archivo.name} texto: palabra sospechosa {palabra!r} "
                        f"en: {linea.strip()[:90]}"
                    )
                    break

    # 4. Restos de plantilla sin sustituir. El HTML de esta seccion no lleva
    # estilos en linea, asi que cualquier llave es de la plantilla (generate
    # con str.format deja llaves dobles si se escapan mal).
    if "{{" in texto or "}}" in texto:
        fallos.append(f"{archivo.name}: quedan marcadores de plantilla sin sustituir")

    # 5. Estructura basica.
    if "<h1>" not in texto:
        fallos.append(f"{archivo.name}: no tiene <h1>")
    if texto.count("<h1>") > 1:
        fallos.append(f"{archivo.name}: tiene {texto.count('<h1>')} H1, deberia tener 1")
    for exigido in ('rel="canonical"', 'name="description"', "og:title", "application/ld+json"):
        if exigido not in texto:
            fallos.append(f"{archivo.name}: falta {exigido}")
    if 'href="https://t.me/GangasOfertasChollos"' not in texto:
        fallos.append(f"{archivo.name}: sin enlaces al canal de Telegram")


def main() -> int:
    paginas = sorted(SECCION.glob("*.html"))
    if not paginas:
        print(f"FALLO: no hay paginas en {SECCION}. Ejecuta generar_prime_days.py")
        return 1

    print(f"== Texto y estructura de {len(paginas)} paginas ==\n")
    for pagina in paginas:
        antes = len(fallos)
        revisar(pagina)
        if len(fallos) == antes:
            print(f"  OK   {pagina.name}")

    print()
    if fallos:
        for f in fallos:
            print(f"  FALLO {f}")
        print(f"\n{'=' * 60}\n{len(fallos)} problemas de texto")
        return 1
    print("=" * 60)
    print("TODO CORRECTO")
    return 0


if __name__ == "__main__":
    sys.exit(main())