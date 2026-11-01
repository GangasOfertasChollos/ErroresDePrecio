"""Pruebas del reparto de ofertas por categoria (sin tocar Telegram).

Comprueba tres cosas:

1. Que el diccionario y el mapeo de temas son coherentes entre si.
2. Que las trampas tipicas del castellano no mandan una oferta a la categoria
   equivocada: "gelatina" no es "gel", "barbacoa" no es "barba", "un poco" no es
   la marca POCO, "sin cable" no es electronica.
3. Que una muestra de titulos reales del canal cae en la categoria esperada.
   Los titulos salen de data/general.json, que son ofertas de verdad.

Uso:  python tests/test_reenvio_categorias.py
"""
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import clasificador
import reenvioCategorias as reenvio

fallos = 0


def check(nombre, condicion, detalle=""):
    global fallos
    if condicion:
        print("  OK   " + nombre)
    else:
        fallos += 1
        print("  FALLO " + nombre + " -> " + str(detalle))


def categoria(texto):
    return clasificador.clasificar(texto)


DICCIONARIO = clasificador.cargar_diccionario()
PATRONES = clasificador.precompilar_patrones(DICCIONARIO)
TEMAS = reenvio.cargar_temas()

print("\n== 1. Diccionario y temas coherentes ==")
check("hay 6 categorias", len(DICCIONARIO) == 6, list(DICCIONARIO))
check("todas tienen palabras", all(DICCIONARIO.values()),
      [c for c, p in DICCIONARIO.items() if not p])
check("todas tienen tema", reenvio.validar_temas(TEMAS, DICCIONARIO) == [],
      reenvio.validar_temas(TEMAS, DICCIONARIO))
check("los ids de tema no se repiten", len(set(TEMAS.values())) == len(TEMAS), TEMAS)
check("General tiene tema", clasificador.CATEGORIA_GENERAL in TEMAS, TEMAS)

# Sin duplicados que solo cambien en tildes o mayusculas: "pantalon" y
# "pantalón" son la misma palabra al normalizar y solo despistan al revisar.
duplicados = []
for cat, palabras in DICCIONARIO.items():
    normalizadas = [clasificador.normalizar(p) for p in palabras]
    duplicados += [f"{cat}:{p}" for p in set(normalizadas)
                   if normalizadas.count(p) > 1]
check("el diccionario no repite palabras normalizadas", not duplicados, duplicados)

print("\n== 2. Normalizacion ==")
check("tildes fuera", clasificador.normalizar("Pantalón Bañador") == "pantalon banador",
      clasificador.normalizar("Pantalón Bañador"))
check("mayusculas fuera", clasificador.normalizar("NIKE") == "nike")
check("enye como n", clasificador.normalizar("niño") == "nino")
check("texto vacio", categoria("") == "general")
check("solo espacios", categoria("   ") == "general")

print("\n== 3. Palabra completa: no vale el principio de otra palabra ==")
trampas = [
    ("Gelatina de fresa", "general", "gel"),
    ("Salsa barbacoa para costillas", "general", "barba"),
    ("Reglamento de fútbol sala", "general", "regla"),
    ("Un poco de todo para casa", "general", "poco"),
    ("Aspiradora sin cable 2000W", "general", "cable"),
    ("Pelota de tenis Wilson", "juguetes-infantil", "pelo"),
    ("Peluche de peluche grande", "juguetes-infantil", "pelo"),
]
for texto, esperado, palabra in trampas:
    obtenido = categoria(texto)
    check(f"{texto!r} -> {esperado} (no por {palabra!r})", obtenido == esperado, obtenido)

print("\n== 4. Plurales dentro de la expresion ==")
plurales = [
    ("Cepillos eléctricos Sonicare", "higiene-cuidado-personal"),
    ("Cuchillas de afeitar Gillette", "higiene-cuidado-personal"),
    ("Pantalones vaqueros", "ropa-y-calzado"),
    ("Zapatillas de correr", "ropa-y-calzado"),
    ("Auriculares inalámbricos", "moviles-electronica"),
    ("Juegos de mesa educativos", "juguetes-infantil"),
]
for texto, esperado in plurales:
    check(f"{texto!r} -> {esperado}", categoria(texto) == esperado, categoria(texto))

print("\n== 5. Empates: gana la coincidencia mas especifica ==")
empates = [
    # "papel" es papeleria, pero "papel higienico" es higiene
    ("Papel Higiénico Premium 3 capas", "higiene-cuidado-personal"),
    ("Papel A4 500 hojas", "papeleria-oficina"),
    # "silla de oficina" frente a "silla gaming"
    ("Silla de oficina ergonómica", "papeleria-oficina"),
    ("Silla gaming reclinable", "gaming-consolas"),
    # "monitor" es electronica; "monitor gaming", no
    ("Monitor 27 pulgadas 165Hz", "moviles-electronica"),
    ("Monitor gaming 27 pulgadas", "gaming-consolas"),
    # "reloj" de pulsera frente a "reloj inteligente"
    ("Reloj Festina de cuero", "ropa-y-calzado"),
    ("Reloj inteligente con GPS", "moviles-electronica"),
    # "mando" de consola frente a "mando a distancia"
    ("Mando DualSense para PS5", "gaming-consolas"),
    ("Mando a distancia para TV", "moviles-electronica"),
    # "auriculares" genericos frente a "auriculares gaming"
    ("Auriculares Bluetooth", "moviles-electronica"),
    ("Auriculares gaming con micro", "gaming-consolas"),
]
for texto, esperado in empates:
    check(f"{texto!r} -> {esperado}", categoria(texto) == esperado, categoria(texto))

print("\n== 6. Etiqueta de categoria del canal y negaciones ==")
con_etiqueta = [
    # El canal ya trae a veces su propia etiqueta. No debe mandar sobre el
    # contenido: este juego de mesa esta etiquetado como gaming y es juguetes.
    ("🔥 **Educa - Lince | Juego de Mesa Educativo**\n"
     "📂 *Gaming y consolas*\n\n⚡ Precio actual: 12,99€", "juguetes-infantil"),
    ("🪥 PHILIPS SONICARE – CEPILLOS ELÉCTRICOS\n"
     "📂 *Móviles y electrónica*", "higiene-cuidado-personal"),
    ("🔥 Zapatillas Nike Air\n📂 *Ropa y calzado*", "ropa-y-calzado"),
    # Sin palabras clave en el contenido, la etiqueta es la unica pista.
    ("🔥 Producto sin palabras conocidas\n📂 *Gaming y consolas*", "gaming-consolas"),
    ("🔥 Producto sin palabras conocidas", "general"),
]
for texto, esperado in con_etiqueta:
    check(f"etiqueta: {texto.splitlines()[0][:42]!r} -> {esperado}",
          categoria(texto) == esperado, categoria(texto))

check("se extrae la etiqueta", clasificador.etiqueta_canal("📂 *Ropa y calzado*") == "Ropa y calzado")
check("una linea con carpeta que no es etiqueta se respeta",
      clasificador.etiqueta_canal("📂 Carpeta de archivos A4") == "")

negaciones = [
    ("Limpiador para tapicerías. Sin perfume.", "general"),
    ("Crema hidratante sin perfume", "higiene-cuidado-personal"),
    ("Altavoz bluetooth sin cables", "moviles-electronica"),
]
for texto, esperado in negaciones:
    check(f"negacion: {texto!r} -> {esperado}", categoria(texto) == esperado,
          categoria(texto))

print("\n== 7. Marcas con modelo (POCO, Moto) ==")
marcas = [
    ("Xiaomi POCO X6 Pro 5G", "moviles-electronica"),
    ("POCO F5 256GB", "moviles-electronica"),
    ("Moto G56 5G 512GB", "moviles-electronica"),
]
for texto, esperado in marcas:
    check(f"{texto!r} -> {esperado}", categoria(texto) == esperado, categoria(texto))

print("\n== 8. Titulos reales del canal ==")
# (titulo, categoria esperada). Salen de data/general.json; se han revisado a
# mano. Si un cambio en el diccionario mueve uno de estos, el test lo dice.
CORPUS = [
    ("Beter – Pinzas de depilar para cejas de punta cangrejo", "higiene-cuidado-personal"),
    ("GARNIER DELIAL – PROTECTOR SOLAR FACIAL FPS 50+", "higiene-cuidado-personal"),
    ("Philips Lumea serie 8000, dispositivo de depilación IPL", "higiene-cuidado-personal"),
    ("BENBOY – PANTALONES IMPERMEABLES PARA MUJER", "ropa-y-calzado"),
    ("Biotherm Homme, Day Control, Desodorante Spray 72 h", "higiene-cuidado-personal"),
    ("BREVILLE – SANDWICHERA Y PLANCHA PARA PANINIS", "general"),
    ("GREENS STEEL – PACK 4 VASOS DE ACERO INOXIDABLE", "general"),
    ("Reebok Zapatillas Unisex Aztec II", "ropa-y-calzado"),
    ("SONGMICS Perchero de Pie, Organizador para Ropa", "ropa-y-calzado"),
    ("DR. BECKMANN – QUITAMANCHAS PARA TAPICERÍA 400 ML", "general"),
    ("Rimmel London Lasting Finish lip liner, delineador de labios", "higiene-cuidado-personal"),
    ("NIKE – CAMISETA DEPORTIVA PARA HOMBRE", "ropa-y-calzado"),
    ("Anzarun Lite, Sneaker Unisex Adulto", "ropa-y-calzado"),
    ("L'Oréal Paris Revitalift Filler Crema Hidratante", "higiene-cuidado-personal"),
    ("PHILIPS SONICARE DIAMONDCLEAN 9000 – CEPILLOS ELÉCTRICOS", "higiene-cuidado-personal"),
    ("PTHTECHUS Reloj Inteligente Niños con Llamadas Bluetooth", "moviles-electronica"),
    ("PHILIPS ONEBLADE 360 – RECORTADORA Y AFEITADORA ELÉCTRICA", "higiene-cuidado-personal"),
    ("JACK & JONES Jjiglenn Jjoriginal Vaqueros Slim", "ropa-y-calzado"),
    ("Miquelrius - Agenda Escolar 2026 2027", "papeleria-oficina"),
    ("ZECAMIN – SENSORES INTELIGENTES PARA PUERTAS Y VENTANAS", "general"),
    ("Educa - Lince 70 Imágenes | Juego de Mesa Educativo", "juguetes-infantil"),
    ("Moulinex Easy Fry XL Surface, Freidora de Aire 2200 W", "general"),
    ("BRAUN SERIE 6 – AFEITADORA ELÉCTRICA PARA HOMBRE", "higiene-cuidado-personal"),
    ("BSEED Interruptor de luz 2 Gang 1 Vía", "general"),
    ("OFERTA 3x2", "general"),
    ("Zapatillas Rumba Negro", "ropa-y-calzado"),
    ("La Roche-Posay, Effaclar H Iso-Biome Crema Limpiadora", "higiene-cuidado-personal"),
    ("Educa - Set con 2 Puzzles de 1000 Piezas para Adultos", "juguetes-infantil"),
    ("Festina Reloj Hombre Analógico Solar de Cuero", "ropa-y-calzado"),
    ('bvate Ordenador Portátil 14" Win11 8GB 256GB SSD', "moviles-electronica"),
    ("MELLERWARE – FREIDORA SIN ACEITE CRUNCHY PLUS 5,5 L", "general"),
    ("TOSHIBA Microondas Digital con Grill 25L", "general"),
    ("Mibro Aeropace Reloj Inteligente para Correr con GPS", "moviles-electronica"),
    ("Mujer Essentials Big Logo French Terry Loose Hoodie", "ropa-y-calzado"),
    ("32 Piezas Decoración Halloween Luminosa", "general"),
    ("537 Western Bootcut - Jeans Hombre", "ropa-y-calzado"),
    ("BEL AIR HOME Ventilador de Techo ASGARD Blanco", "general"),
    ("Palmer's Aceite de Coco para el Cuerpo - 150 ml", "higiene-cuidado-personal"),
    ("Skechers Arch Fit City Catch Mujer Sandali", "ropa-y-calzado"),
    ("RIMMEL LONDON – BASE DE MAQUILLAJE KIND & FREE", "higiene-cuidado-personal"),
    ("CHECKME ARMFIT – TENSIÓMETRO DIGITAL CON BLUETOOTH", "moviles-electronica"),
    ("STRONG – ROUTER WiFi 4G LTE CON SIM", "moviles-electronica"),
    ("PUMA Anzarun Lite, Zapatillas Unisex adulto", "ropa-y-calzado"),
    ("Receptor Bluetooth Coche Manos Libres", "moviles-electronica"),
    ("HUANUO Soporte Monitor Doble, Brazo Monitor de Escritorio", "moviles-electronica"),
    ("BALLERINA – BAYETAS AMARILLAS 3+1 GRATIS", "general"),
    ("TRINORDIC Esterilla de acampada hinchable", "general"),
    ("Auriculares Inalámbricos Deportivos, 60H, 28 Modos EQ", "moviles-electronica"),
    ("Battlefield 1 Revolution [GRA XBOX ONE]", "gaming-consolas"),
    ("ABRILA - Ventilador De Pie Siluro 50w", "general"),
    ("NaturVital - Champú Eco Purificante, Vegano, 300ml", "higiene-cuidado-personal"),
    ("HG Armour Comp SS Camiseta para Hombre", "ropa-y-calzado"),
    ("CeraVe Crema Reparadora de Manos", "higiene-cuidado-personal"),
    ("150 Piezas Bloques Magneticos", "juguetes-infantil"),
    ("LOGITECH H390 – AURICULARES CON MICRÓFONO USB", "moviles-electronica"),
    ("SUAAT – TABLET INFANTIL 9” ANDROID 15 (ROJA)", "moviles-electronica"),
    ("e.l.f. Expert Liquid Liner, a prueba de manchas", "higiene-cuidado-personal"),
    ("Jabón De Manos En Espuma Arándano Azul 250 Ml", "higiene-cuidado-personal"),
    ("Aspirador de Mano, 28000PA Aspiradora de Coche Sin Cable", "general"),
    ("Hombre Runfalcon 5 Zapatillas de Correr", "ropa-y-calzado"),
    ("Yuson Girl Camisetas Manga Corta Mujer", "ropa-y-calzado"),
    ("TOPFINEL – CORTINAS BLANCAS 2 PIEZAS", "general"),
    ("JATA JEBT1500 - Batidora de vaso de 1,5 litros", "general"),
    ("Joma Camiseta Manga Corta Championship", "ropa-y-calzado"),
    ("MAM – CHUPETES ORIGINAL NOCHE 0-2 MESES", "juguetes-infantil"),
    ("Razer BlackShark V2 Pro para PC - Auriculares premium para deportes electrónicos", "gaming-consolas"),
    ("LEXIBOOK, Stitch Micrófono Bluetooth, MIC240D", "moviles-electronica"),
    ("MAOYING – MASAJEADOR ANTICELULÍTICO 4 EN 1", "general"),
    ("TRAUMHEIM – LIMPIADOR A VAPOR DE MANO 1200W", "general"),
    ("PTHTECHUS – RELOJ INTELIGENTE INFANTIL CON LLAMADAS", "moviles-electronica"),
    ("APPLE AIRPODS MAX – AURICULARES INALÁMBRICOS USB-C", "moviles-electronica"),
    ("FLAREMORE – HOMBRERA TÉRMICA CON MASAJE", "general"),
    ("Papel Higiénico Premium 3 capas COLHOGAR, 18 rollos", "higiene-cuidado-personal"),
    ("Sony WH-CH520, Auriculares de diadema Bluetooth", "moviles-electronica"),
    ("Pizarra Magnética Pared Grande Doble Cara", "papeleria-oficina"),
    ("Natural Honey, Gel de Ducha con Extracto de Coco", "higiene-cuidado-personal"),
    ("COUTZON – 100 BLOQUES DE CONSTRUCCIÓN MAGNÉTICOS", "juguetes-infantil"),
    ("Shark PowerDetect Clean & Empty, Aspiradora sin Cable", "general"),
    ("Joseph Joseph Tabla de drenaje extensible", "general"),
    ("Nike Nigeria Home Camiseta de fútbol Niños", "ropa-y-calzado"),
    ("MY ARCADE Máquina Retro Arcade X Mini", "gaming-consolas"),
    ("G-STAR Camiseta Eyben Slim V Top para Mujer", "ropa-y-calzado"),
    ("Listerine Cuidado Total Enjuague Bucal con Flúor", "higiene-cuidado-personal"),
    ("Tesla Plancha IR400GP, 3100W, Suela Cerámica", "general"),
    ("TIGER BALM ROJO – BÁLSAMO ORIGINAL 19 G", "higiene-cuidado-personal"),
    ("Rush 05", "general"),
    ("Massana, Zapatillas Unisex adulto, Negro", "ropa-y-calzado"),
    ("Moto g56 5G 24GB/512GB Gris", "moviles-electronica"),
    ("Vans Ward Platform, Zapatillas Mujer", "ropa-y-calzado"),
    ("CALENDARIO DE ADVIENTO DE PERFUMES 2026", "higiene-cuidado-personal"),
    ("Swarovski Pendientes Millenia, Blancos", "ropa-y-calzado"),
    ("Bufanda Pañuelo Cuello Mujer Elegante de Seda", "ropa-y-calzado"),
    ("PHB - HILO DENTAL PHB PTFE 50 M", "higiene-cuidado-personal"),
    ("Batidora Amasadora Vospeed 1500W", "general"),
    ("Esselte Índices numéricos de plástico, Tamaño A4", "papeleria-oficina"),
]
for titulo, esperado in CORPUS:
    obtenido = clasificador.clasificar(titulo, PATRONES)
    check(f"{titulo[:58]!r} -> {esperado}", obtenido == esperado,
          f"obtenido {obtenido}")

print("\n== 9. Mapeo de temas ==")
check("ropa -> 3", reenvio.resolver_tema("ropa-y-calzado", TEMAS) == 3)
check("higiene -> 8", reenvio.resolver_tema("higiene-cuidado-personal", TEMAS) == 8)
check("categoria desconocida -> General",
      reenvio.resolver_tema("no-existe", TEMAS) == TEMAS["general"])
try:
    reenvio.validar_temas({"general": 2}, DICCIONARIO)
    check("falta un tema y se avisa", False, "no ha lanzado ValueError")
except ValueError:
    check("falta un tema y se avisa", True)

print("\n== 10. El bot no guarda credenciales en el codigo ==")
fuente = (RAIZ / "reenvioCategorias.py").read_text(encoding="utf-8")
check("API_HASH sale del .env", not re.search(r"API_HASH\s*=\s*['\"]", fuente))
check("sin espacios duros (U+00A0) del archivo corrupto", "\u00a0" not in fuente)
check("el archivo se puede compilar", compile(fuente, "reenvioCategorias.py", "exec") is not None)

print()
if fallos:
    print(f"FALLOS: {fallos}")
    sys.exit(1)
print("Todo correcto.")
