"""Clasificacion de ofertas por categoria.

Modulo compartido por bot.py (catalogo de la web) y reenvioCategorias.py (grupo
de Telegram) para que una misma oferta caiga en la misma categoria en los dos
sitios. El diccionario de palabras clave es categorias.json: se edita ahi y no
hay que tocar codigo.

Reglas de clasificacion:

* Se ignoran tildes, mayusculas y el tipo de letra: el texto y las palabras
  clave se normalizan antes de comparar, asi que "pantalón" y "pantalon" son
  lo mismo.
* La coincidencia es por palabra completa, con plural tolerado en cada palabra
  de la expresion ("cepillos eléctricos" encuentra "cepillo eléctrico").
  Deliberadamente NO se permite que una palabra clave sea solo el principio de
  otra: "gel" no debe mandar "gelatina" a higiene, ni "pelo" mandar "pelota".
* Gana la categoria con mas palabras clave distintas. Si hay empate gana la que
  tenga la coincidencia mas larga (la mas especifica) y, si persiste, la que
  aparezca antes en categorias.json. Por eso "papel higienico" gana a "papel" y
  "silla gaming" gana a "silla de oficina".
* Las marcas que se escriben con un modelo detras ("POCO X6", "Moto G56") van
  en PATRONES_EXTRA y no en el diccionario: "poco" a secas es una palabra
  corriente en castellano y mandaria a moviles cualquier oferta que dijera
  "un poco de...".
"""

import json
import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
DICCIONARIO_PATH = RAIZ / 'categorias.json'

# Categoria de descarte cuando ninguna palabra clave coincide.
CATEGORIA_GENERAL = 'general'

# Algunos posts del canal llevan su propia etiqueta de categoria en una linea
# aparte ("📂 *Gaming y consolas*"). Es metadato, no descripcion del producto: si
# se deja en el texto, sus palabras compiten con el contenido y mandan el post a
# esa categoria aunque el producto sea otro (un juego de mesa acababa en gaming
# por su propia etiqueta). Solo se quita la linea del icono de carpeta en
# cursiva, que es el formato de la etiqueta; una frase normal con 📂 se respeta.
RE_ETIQUETA_CANAL = re.compile(r'^[ \t]*📂[ \t]*\*[^*\n]+\*[ \t]*$', re.MULTILINE)

# "Sin perfume", "libre de alcohol": la palabra clave aparece, pero el producto
# presume de NO llevarla. Sin esto, un quitamanchas "sin perfume" acaba en
# higiene por la palabra "perfume".
RE_NEGACION = re.compile(r'\b(?:sin|libre de)\s+(?:un |una |el |la |los |las )?$')

# Patrones que no son palabras sueltas sino marca + modelo. Se aplican sobre el
# texto ya normalizado (minusculas y sin tildes), asi que se escriben asi.
PATRONES_EXTRA = {
    'moviles-electronica': (
        r'poco\s+[xfcm]\d',   # POCO X6, POCO F5, POCO M6, POCO C65
        r'moto\s+[ge]\d',     # Moto G56, Moto E14
    ),
}


def normalizar(texto):
    """Pasa a minusculas y elimina tildes/diacriticos para comparar igual.

    La enye tambien se convierte en "n", por eso en el diccionario no se usan
    palabras que cambien de significado al hacerlo ("uñas" -> "unas").
    """
    descompuesto = unicodedata.normalize('NFD', texto or '')
    return ''.join(c for c in descompuesto
                   if unicodedata.category(c) != 'Mn').lower()


def _patron_expresion(expresion):
    """Compila una expresion del diccionario con limites de palabra.

    Cada palabra de la expresion admite plural (s/es) para no tener que
    duplicar cada termino. Los limites son por palabra completa: `gel` no
    coincide con `gelatina` y `nota` no coincide con `notable`.
    """
    piezas = []
    for palabra in expresion.split():
        piezas.append(re.escape(palabra) + r'(?:s|es)?')
    return re.compile(r'(?<!\w)' + r'\s+'.join(piezas) + r'(?!\w)')


def cargar_diccionario(ruta=None):
    """Lee categorias.json y devuelve {categoria: [palabras clave]}."""
    ruta = Path(ruta) if ruta else DICCIONARIO_PATH
    with open(ruta, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    if not isinstance(datos, dict):
        raise ValueError(f'{ruta} debe contener un objeto JSON categoria -> lista')
    for categoria, palabras in datos.items():
        if not isinstance(palabras, list) or not all(isinstance(p, str) for p in palabras):
            raise ValueError(f'La categoria {categoria!r} de {ruta} debe ser una lista de textos')
    return datos


def precompilar_patrones(diccionario):
    """Normaliza y compila el diccionario una sola vez al arrancar.

    Devuelve {categoria: [(etiqueta, patron)]}. La etiqueta es la palabra o el
    patron extra que ha coincidido, solo para los mensajes de depuracion.

    Se descartan las palabras que ya cubre otra mas corta de la misma categoria
    ("auriculares" sobra si esta "auricular", porque el plural se tolera). Sin
    esto la misma palabra sumaba dos coincidencias y desequilibraba el reparto
    frente a otras categorias.
    """
    patrones = {}
    for categoria, palabras in diccionario.items():
        compilados = []
        for palabra in sorted(palabras, key=lambda p: len(normalizar(p))):
            palabra_norm = normalizar(palabra).strip()
            if not palabra_norm:
                continue
            if any(patron.fullmatch(palabra_norm) for _, patron in compilados):
                continue
            compilados.append((palabra, _patron_expresion(palabra_norm)))
        for extra in PATRONES_EXTRA.get(categoria, ()):
            compilados.append((extra, re.compile(r'(?<!\w)(?:' + extra + r')(?!\w)')))
        patrones[categoria] = compilados
    return patrones


def etiqueta_canal(texto):
    """Devuelve el texto de la etiqueta "📂 *Categoria*" del post, si la trae."""
    encontrado = RE_ETIQUETA_CANAL.search(texto or '')
    if not encontrado:
        return ''
    return encontrado.group(0).replace('📂', '').strip().strip('*').strip()


def _negado(texto_norm, posicion):
    """True si la coincidencia va precedida de "sin" o "libre de"."""
    return bool(RE_NEGACION.search(texto_norm[max(0, posicion - 16):posicion]))


def analizar(texto, patrones_compilados=None):
    """Devuelve, por categoria con alguna coincidencia, la puntuacion y que coincidio.

    La lista sale en el orden del diccionario, que es el que decide los empates
    finales.
    """
    texto_norm = normalizar(RE_ETIQUETA_CANAL.sub('', texto or ''))
    if not texto_norm.strip():
        return []

    patrones_compilados = (patrones_compilados if patrones_compilados is not None
                           else precompilar_patrones(cargar_diccionario()))
    resultados = []
    for categoria, compilados in patrones_compilados.items():
        coincidencias = []
        for etiqueta, patron in compilados:
            encontrado = patron.search(texto_norm)
            if encontrado and not _negado(texto_norm, encontrado.start()):
                coincidencias.append((etiqueta, len(encontrado.group(0))))
        if coincidencias:
            resultados.append({
                'categoria': categoria,
                'puntuacion': len(coincidencias),
                'coincidencia_mas_larga': max(largo for _, largo in coincidencias),
                'coincidencias': [etiqueta for etiqueta, _ in coincidencias],
            })
    return resultados


def _mejor(resultados):
    """Gana la puntuacion; a igualdad, la coincidencia mas larga; despues el orden."""
    return max(resultados, key=lambda r: (r['puntuacion'], r['coincidencia_mas_larga']))


def explicar(texto, patrones_compilados=None):
    """Devuelve la categoria y el detalle util para depurar.

    Si el texto no da ninguna pista se usa la etiqueta que el propio post trae
    ("📂 *Gaming y consolas*"), pero solo como respaldo: cuando el contenido
    tiene palabras clave, manda el contenido. Asi un juego de mesa etiquetado
    por error como gaming sigue yendo a juguetes, y un post sin palabras
    reconocibles no se pierde en General.
    """
    resultados = analizar(texto, patrones_compilados)
    origen = 'texto'

    if not resultados:
        etiqueta = etiqueta_canal(texto)
        if etiqueta:
            resultados = analizar(etiqueta, patrones_compilados)
            origen = 'etiqueta'

    if not resultados:
        return {'categoria': CATEGORIA_GENERAL, 'puntuacion': 0,
                'coincidencias': [], 'todas': [], 'origen': 'ninguno'}

    mejor = _mejor(resultados)
    return {
        'categoria': mejor['categoria'],
        'puntuacion': mejor['puntuacion'],
        'coincidencias': mejor['coincidencias'],
        'todas': resultados,
        'origen': origen,
    }


def clasificar(texto, patrones_compilados=None):
    """Devuelve el slug de la categoria que mejor encaja con el texto."""
    return explicar(texto, patrones_compilados)['categoria']
