"""Pruebas del script de publicacion en X.

Lo que se comprueba aqui es la parte que no depende de X: como se mide la
longitud de un post (X cuenta las URLs como 23 caracteres y los emojis como
dos), como se arma el texto a partir de una oferta y como se lleva el estado
de lo ya publicado.

Para el descubrimiento de los ids de operacion y la subida de imagen hace
falta una sesion real de x.com: eso se prueba a mano con
`python3 publicar_x.py --revisar`.
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("publicar_x", RAIZ / "publicar_x.py")
px = importlib.util.module_from_spec(spec)
spec.loader.exec_module(px)

fallos = 0


def check(nombre, condicion, detalle=""):
    global fallos
    if condicion:
        print("  OK   " + nombre)
    else:
        fallos += 1
        print("  FALLO " + nombre + " -> " + str(detalle))


# ── Ofertas de ejemplo, con la forma que tienen en data/*.json ──
OFERTA = {
    "id": 10617,
    "date": "2026-10-19T16:00:48+00:00",
    "title": "BOLSO BANDOLERA DKNY BRYANT AVE \U0001f5a4\u2728",
    "price": "39.01 \u20ac",
    "old_price": "99.00 \u20ac",
    "discount": "-61%",
    "amazon_url": "https://www.amazon.es/dp/B0F9B3BKZ4?tag=gangas029-21",
    "image": "https://cdn4.telesco.pe/file/AB.jpg",
    "categoria": "ropa-y-calzado",
    "description": ("\u00a1Elegancia a precio incre\u00edble! Bolso DKNY negro con logotipo, "
                    "dise\u00f1o moderno y bandolera ajustable. \u00a1Aprovecha esta ofertaza! "
                    "\U0001f5a4\u2728 Canal: https://t.me/GangasOfertasChollos"),
    "brand": "BOLSO BANDOLERA",
    "gtin": "",
    "mpn": "",
}

print("\n== 1. Longitud del post: las reglas de X ==")
check("texto normal cuenta 1 por caracter", px.longitud_post("hola") == 4, px.longitud_post("hola"))
check("la URL cuenta como 23", px.longitud_post("https://a.com/xyz") == 23, px.longitud_post("https://a.com/xyz"))
check("URL y texto se suman", px.longitud_post("a https://a.com/b") == 2 + 23, px.longitud_post("a https://a.com/b"))
check("el emoji cuenta como 2", px.longitud_post("\U0001f5a4") == 2, px.longitud_post("\U0001f5a4"))
check("la letra acentuada cuenta como 1", px.longitud_post("\u00e1") == 1, px.longitud_post("\u00e1"))
check("el euro cuenta como 1", px.longitud_post("39,01 \u20ac") == 7, px.longitud_post("39,01 \u20ac"))
check("el limite es 280", px.LIMITE_POST == 280, px.LIMITE_POST)

print("\n== 2. Precio: el JSON lo guarda con punto, X en español con coma ==")
check("39.01 -> 39,01", px._precio_es("39.01 \u20ac") == "39,01 \u20ac", px._precio_es("39.01 \u20ac"))
check("los miles se separan con punto", px._precio_es("1299.00 \u20ac") == "1.299,00 \u20ac",
      px._precio_es("1299.00 \u20ac"))
check("un precio de dos cifras no cambia", px._precio_es("16.17 \u20ac") == "16,17 \u20ac",
      px._precio_es("16.17 \u20ac"))
check("sin precio devuelve vacio", px._precio_es("") == "", px._precio_es(""))
check("el simbolo del euro queda separado", px._precio_es("9.99\u20ac") == "9,99 \u20ac",
      px._precio_es("9.99\u20ac"))
check("el precio anterior y el actual se sacan de la descripcion",
      px._precios_de_descripcion("Ropa y calzado Precio recomendado: 59,95 \u20ac 31,95 \u20ac")
      == ("59,95 \u20ac", "31,95 \u20ac"),
      px._precios_de_descripcion("Ropa y calzado Precio recomendado: 59,95 \u20ac 31,95 \u20ac"))
check("una descripcion sin precios no devuelve nada",
      px._precios_de_descripcion("Solo una descripcion cualquiera") == ("", ""),
      px._precios_de_descripcion("Solo una descripcion cualquiera"))

print("\n== 3. La descripcion: se quita el final de Telegram ==")
limpia = px._limpiar_descripcion(OFERTA["description"])
check("no deja la URL del canal", "t.me" not in limpia, limpia)
check("no deja la palabra Canal", "Canal" not in limpia, limpia)
check("conserva el texto de verdad", limpia.startswith("\u00a1Elegancia"), limpia)
check("un aviso de publicidad no cuenta como descripcion",
      px._limpiar_descripcion("Publicidad/Enlace afiliado El precio puede cambiar.") == "",
      px._limpiar_descripcion("Publicidad/Enlace afiliado El precio puede cambiar."))
check("la categoria y los precios no cuentan como descripcion",
      px._limpiar_descripcion("Ropa y calzado Precio recomendado: 59,95 \u20ac 31,95 \u20ac "
                              "Canal: https://t.me/GangasOfertasChollos") == "",
      px._limpiar_descripcion("Ropa y calzado Precio recomendado: 59,95 \u20ac 31,95 \u20ac "
                              "Canal: https://t.me/GangasOfertasChollos"))
check("una descripcion de verdad se conserva",
      px._limpiar_descripcion("Zapatillas comodas. Precio recomendado: 59,95 \u20ac 31,95 \u20ac")
      .startswith("Zapatillas"),
      px._limpiar_descripcion("Zapatillas comodas. Precio recomendado: 59,95 \u20ac 31,95 \u20ac"))
check("sin descripcion devuelve vacio", px._limpiar_descripcion("") == "", px._limpiar_descripcion(""))

print("\n== 4. El post que se arma ==")
texto = px.componer_post(OFERTA)
print("\n" + texto + "\n")
check("cabe en 280", px.longitud_post(texto) <= 280, px.longitud_post(texto))
check("lleva el titulo", "DKNY" in texto, texto)
check("lleva el precio con coma", "39,01 \u20ac" in texto, texto)
check("lleva el precio anterior", "99,00 \u20ac" in texto, texto)
check("lleva el descuento", "-61%" in texto, texto)
check("lleva el enlace de afiliado", "gangas029-21" in texto, texto)
check("lleva la descripcion", "Elegancia" in texto, texto)
check("no arrastra el final de Telegram", "t.me" not in texto, texto)
check("lleva hashtags", "#Amazon" in texto, texto)
check("el hashtag de la categoria", "#Moda" in texto, texto)
preguntas_en_texto = [p for p in px.PREGUNTAS if p in texto]
check("lleva una pregunta de la lista", len(preguntas_en_texto) == 1, preguntas_en_texto)
if preguntas_en_texto:
    pregunta = preguntas_en_texto[0]
    check("el precio actual va primero", texto.index("Ahora:") < texto.index(pregunta), texto)
    check("el precio anterior va en el bloque de precios",
          texto.index("Antes:") < texto.index(pregunta), texto)
    check("el descuento va en el bloque de precios",
          texto.index("-61%") < texto.index(pregunta), texto)
    check("la pregunta va antes del titulo", texto.index(pregunta) < texto.index("DKNY"), texto)
    check("la descripcion va despues de la pregunta",
          texto.index("Elegancia") > texto.index(pregunta), texto)
    check("el enlace queda al final", texto.rstrip().endswith("gangas029-21"), texto)
check("dos preguntas seguidas no se repiten",
      px.pregunta_aleatoria() != px.pregunta_aleatoria())
check("los enlaces no se repiten",
      px._enlaces_de(dict(OFERTA, enlaces=[OFERTA["amazon_url"], "https://ejemplo.com/x"]))
      == [OFERTA["amazon_url"], "https://ejemplo.com/x"],
      px._enlaces_de(dict(OFERTA, enlaces=[OFERTA["amazon_url"], "https://ejemplo.com/x"])))
sin_antes = dict(OFERTA, old_price="", description="Ropa y calzado Precio recomendado: "
                                                     "99,00 \u20ac 39,01 \u20ac")
check("si falta el precio anterior se toma de la descripcion",
      "Antes: 99,00 \u20ac" in px.componer_post(sin_antes), px.componer_post(sin_antes))
otra_oferta = dict(OFERTA, old_price="", description="Ropa y calzado Precio recomendado: "
                                                     "9,99 \u20ac 7,45 \u20ac")
check("no se mezcla el precio de otra oferta",
      "Antes: 9,99 \u20ac" not in px.componer_post(otra_oferta), px.componer_post(otra_oferta))

print("\n== 4b. El enlace va en una respuesta, no en el post principal ==")
sin_enlace = px.componer_post(OFERTA, incluir_enlaces=False)
check("el post principal no lleva el enlace", "amazon.es" not in sin_enlace, sin_enlace)
check("tampoco lleva la URL del canal", "t.me" not in sin_enlace, sin_enlace)
check("el post principal sigue llevando el titulo", "DKNY" in sin_enlace, sin_enlace)
respuesta = px.componer_respuesta(OFERTA)
check("la respuesta lleva el enlace", OFERTA["amazon_url"] in respuesta, respuesta)
check("la respuesta cabe en 280", px.longitud_post(respuesta) <= 280, px.longitud_post(respuesta))
check("la respuesta tiene una introduccion", "enlace" in respuesta.lower(), respuesta)
check("la respuesta empieza por 'Enlace:'", respuesta.startswith("Enlace:"), respuesta)
check("la respuesta anuncia el canal de Telegram",
      "No te pierdas nada" in respuesta and "https://t.me/" in respuesta, respuesta)
check("una oferta sin enlaces no genera respuesta",
      px.componer_respuesta({"id": 1, "title": "x"}) == "",
      px.componer_respuesta({"id": 1, "title": "x"}))
con_url = dict(OFERTA, description="Mira esto https://ejemplo.com/x antes de comprar")
check("no queda una URL suelta en la descripcion",
      "ejemplo.com" not in px.componer_post(con_url, incluir_enlaces=False),
      px.componer_post(con_url, incluir_enlaces=False))
con_dominio = dict(OFERTA, description="Mira amazon.es/dp/B0F9B3BKZ4 antes de comprar")
check("no queda un dominio suelto en la descripcion",
      "amazon.es" not in px.componer_post(con_dominio, incluir_enlaces=False),
      px.componer_post(con_dominio, incluir_enlaces=False))
varios = dict(OFERTA, enlaces=[OFERTA["amazon_url"], "https://ejemplo.com/x"])
respuesta_varios = px.componer_respuesta(varios)
check("la respuesta lleva todos los enlaces",
      "amazon.es" in respuesta_varios and "ejemplo.com" in respuesta_varios, respuesta_varios)
variables = px._variables_publicar("hola", [], reply_to="123")
check("la respuesta lleva el id del post original",
      variables.get("reply", {}).get("in_reply_to_tweet_id") == "123", variables)
check("el post normal no lleva reply", "reply" not in px._variables_publicar("hola", []),
      px._variables_publicar("hola", []))

print("\n== 5. Titulos largos: se recortan, no se desbordan ==")
larga = dict(OFERTA)
larga["title"] = "COLCHON DE ESPUMA 135 CM CON ALMOHADA EXTRAIBLE Y TEJIDO TRANPIRABLE " \
                 "CERTIFICADO OEKO TEX PARA USO DIARIO EN HABITACIONES DOBLES " \
                 "GRIS CLARO CON CARCASA LAVABLE A MAQUINA Y GUARDA PROTECTOR DE 40 CM"
larga["description"] = "Colchon viscoelastico de espuma HR de alta densidad con nucleo de " \
                       "coco y fibra termoreguladora, transpirable, indeformable y con " \
                       "sistema de ventilacion lateral para un descanso profundo y silencioso " \
                       "durante toda la noche, con fundatxt suave y lavable a 40 grados."
texto_largo = px.componer_post(larga)
check("el post largo tambien cabe", px.longitud_post(texto_largo) <= 280, px.longitud_post(texto_largo))
check("no se pierde el enlace", "gangas029-21" in texto_largo, texto_largo)
check("no se pierden los hashtags", "#Amazon" in texto_largo, texto_largo)

print("\n== 6. Recortar no parte emojis por la mitad ==")
recortado = px._recortar("\U0001f5a4\U0001f5a4\U0001f5a4 texto", 4)
check("respeta el limite", px.longitud_post(recortado) <= 4, px.longitud_post(recortado))
check("no deja emojis rotos", "\ufffd" not in recortado, recortado)

print("\n== 7. Ofertas sin precio o sin descripcion ==")
pobre = dict(OFERTA)
pobre["price"] = ""
pobre["old_price"] = ""
pobre["discount"] = ""
pobre["description"] = ""
texto_pobre = px.componer_post(pobre)
check("se arma igualmente", px.longitud_post(texto_pobre) <= 280, texto_pobre)
check("sin la linea de precios", "\U0001f4b8" not in texto_pobre, texto_pobre)
check("con el enlace", "gangas029-21" in texto_pobre, texto_pobre)

print("\n== 8. El catalogo de verdad: todas las ofertas caben ==")
catalogo = RAIZ / "data" / "general.json"
if catalogo.exists():
    ofertas = json.loads(catalogo.read_text(encoding="utf-8"))
    desbordadas = [o for o in ofertas if px.longitud_post(px.componer_post(o)) > 280]
    check(f"las {len(ofertas)} ofertas de general.json caben en 280", not desbordadas, desbordadas[:2])
    sin_enlaces = [o for o in ofertas
                   if px.longitud_post(px.componer_post(o, incluir_enlaces=False)) > 280]
    check(f"las {len(ofertas)} ofertas caben sin los enlaces", not sin_enlaces, sin_enlaces[:2])
    respuestas_largas = [o for o in ofertas
                         if px.componer_respuesta(o)
                         and px.longitud_post(px.componer_respuesta(o)) > 280]
    check(f"las respuestas de las {len(ofertas)} ofertas caben en 280",
          not respuestas_largas, respuestas_largas[:2])
else:
    print("  (sin data/general.json, se salta)")

print("\n== 9. Estado: no se publica dos veces la misma oferta ==")
tmp = Path(tempfile.mkdtemp())
estado_original = px.ESTADO_PATH
px.ESTADO_PATH = tmp / "estado_x.json"
try:
    estado = px.leer_estado()
    check("sin archivo devuelve estado vacio", estado.get("publicados") == {}, estado)
    estado["publicados"]["10617"] = {"tweet_id": "123", "fecha": "2026-10-19"}
    px.guardar_estado(estado)
    releido = px.leer_estado()
    check("guarda y vuelve a leer", "10617" in releido["publicados"], releido)
    check("guarda el id del post", releido["publicados"]["10617"]["tweet_id"] == "123", releido)
    px.registrar_publicacion(releido, {"id": 7, "title": "x"}, "999", "CreateTweet",
                             franja=datetime(2026, 10, 26, 8, 0))
    releido = px.leer_estado()
    check("guarda la franja ya publicada",
          releido.get("ultima_franja") == "2026-10-26T08:00", releido)
    check("guarda la oferta publicada en la franja", "7" in releido["publicados"], releido)
finally:
    px.ESTADO_PATH = estado_original
    shutil.rmtree(tmp, ignore_errors=True)

print("\n== 10. Las ofertas se leen de mas reciente a mas antigua ==")
tmp = Path(tempfile.mkdtemp())
archivo = tmp / "prueba.json"
archivo.write_text(json.dumps([
    {"id": 1, "title": "a", "amazon_url": "u"},
    {"id": 9, "title": "b", "amazon_url": "u"},
    {"id": 5, "title": "c", "amazon_url": "u"},
]), encoding="utf-8")
try:
    leidas = px.cargar_ofertas(archivo=str(archivo))
    check("la mas reciente primero", [o["id"] for o in leidas] == [9, 5, 1], [o["id"] for o in leidas])
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("\n== 11. Las operaciones de X se leen del JavaScript ==")
JS = ('e.exports={queryId:"wR5Z_lEibLvkew3tF9w-Sg",operationName:"CreateTweet",'
      'operationType:"mutation",metadata:{featureSwitches:["flag_uno","flag_dos"],'
      'fieldToggles:["withAlgo"]}}')
operacion = px._operacion_de_x(JS, "CreateTweet")
check("sale el id de la operacion", operacion and operacion["queryId"] == "wR5Z_lEibLvkew3tF9w-Sg", operacion)
check("sale el nombre", operacion and operacion["operationName"] == "CreateTweet", operacion)
check("salen las banderas", operacion and operacion["featureSwitches"] == ["flag_uno", "flag_dos"], operacion)
check("salen los field toggles", operacion and operacion["fieldToggles"] == ["withAlgo"], operacion)
check("una operacion que no esta devuelve None", px._operacion_de_x(JS, "CreateNota") is None)
check("el formato viejo tambien se entiende",
      px._id_de_operacion('params:{id:`ABC123`,metadata:{},name:`createTweetMutation`,'
                          'operationKind:`mutation`}', "createTweetMutation") == "ABC123")

print("\n== 12. El cuerpo de la peticion: como lo manda la web ==")
operacion = {"queryId": "ABC", "operationName": "CreateTweet", "operationType": "mutation",
             "featureSwitches": ["flag_uno"], "fieldToggles": ["withAlgo"]}
cuerpo = px._cuerpo_publicar(operacion, px._variables_publicar("hola", []))
check("las variables van como objeto", isinstance(cuerpo["variables"], dict), cuerpo)
check("lleva el texto", cuerpo["variables"]["tweet_text"] == "hola", cuerpo)
check("lleva las imagenes vacias", cuerpo["variables"]["media"]["media_entities"] == [], cuerpo)
check("las banderas van aparte", cuerpo["features"] == {"flag_uno": True}, cuerpo)
check("los field toggles van aparte", cuerpo["fieldToggles"] == {"withAlgo": True}, cuerpo)
check("lleva el id de la operacion", cuerpo["queryId"] == "ABC", cuerpo)

vieja = {"queryId": "XYZ", "operationName": "createTweetMutation", "operationType": "mutation",
         "featureSwitches": [], "fieldToggles": []}
cuerpo_viejo = px._cuerpo_publicar(vieja, px._variables_publicar("hola", []))
check("la mutacion vieja lleva las banderas en las variables",
      "__relay_internal__pv__xclientsfeaturesappviewerisloggedinrelayprovider"
      in cuerpo_viejo["variables"], cuerpo_viejo)
check("la mutacion vieja no lleva features", "features" not in cuerpo_viejo, cuerpo_viejo)

print("\n== 13. Si una operacion no va, se prueba la otra ==")
candidatas = px._operaciones_publicar({"CreateTweet": operacion})
check("se prueban las dos", len(candidatas) == 2, [c["operationName"] for c in candidatas])
check("la de ahora va la primera", candidatas[0]["operationName"] == "CreateTweet", candidatas)
check("la vieja va la segunda", candidatas[1]["operationName"] == "createTweetMutation", candidatas)
sin_operaciones = px._operaciones_publicar({})
check("sin operaciones se usa la mutacion vieja guardada",
      [c["operationName"] for c in sin_operaciones] == ["createTweetMutation"], sin_operaciones)
con_preferencia = px._operaciones_publicar({"CreateTweet": operacion},
                                            preferida="createTweetMutation")
check("la mutacion vieja nunca se pone delante",
      [c["operationName"] for c in con_preferencia] == ["CreateTweet", "createTweetMutation"],
      [c["operationName"] for c in con_preferencia])

print("\n== 14. Las respuestas de X se entienden ==")
check("el error de cuota se reconoce",
      px._errores_de_x({"errors": [{"message": "Authorization: You have reached your daily "
                                          "limit for sending Tweets and messages. (344)"}]})
      .find("(344)") > 0)
check("el error de automatizacion se reconoce",
      "automated" in px._errores_de_x({"errors": [{"message": "This request looks like it might "
                                                     "be automated. (226)"}]}))
check("el id del post se saca del formato nuevo",
      px._extraer_id_post({"data": {"create_tweet": {"tweet_results": {"result": {
          "rest_id": "12345"}}}}}) == "12345")
check("el id del post se saca del formato viejo",
      px._extraer_id_post({"data": {"create_tweet": {"results": [{"result": {
          "legacy": {"id_str": "67890"}}}]}}}) == "67890")

print("\n== 15. Las instrucciones del timeline se buscan donde esten ==")
nuevo = {"data": {"user": {"result": {"timeline": {"timeline": {"instructions": [
    {"type": "TimelineClearCache"}, {"entries": []}]}}}}}}
check("la forma nueva", len(px._instrucciones(nuevo)) == 2, px._instrucciones(nuevo))
viejo_forma = {"data": {"user_result_by_screen_name": {"result": {
    "profile_with_timeline_v2": {"timeline": {"timeline": {"instructions": [{"type": "x"}]}}}}}}}
check("la forma vieja", len(px._instrucciones(viejo_forma)) == 1, px._instrucciones(viejo_forma))
check("sin timeline no hay instrucciones", px._instrucciones({"data": {}}) == [])

print("\n== 16. Franjas horarias: una oferta en cada una ==")
HORAS = [8 * 60, 12 * 60, 17 * 60, 21 * 60]
check("por la manana va a la de las 08:00",
      px.proxima_franja(datetime(2026, 10, 26, 7, 0), HORAS) == datetime(2026, 10, 26, 8, 0))
check("a las 09:00 la siguiente es la de las 12:00",
      px.proxima_franja(datetime(2026, 10, 26, 9, 0), HORAS) == datetime(2026, 10, 26, 12, 0))
check("a las 22:00 la siguiente es manana a las 08:00",
      px.proxima_franja(datetime(2026, 10, 26, 22, 0), HORAS) == datetime(2026, 10, 27, 8, 0))
check("el margen deja llegar a una franja recien pasada",
      px.proxima_franja(datetime(2026, 10, 26, 8, 1), HORAS, margen=120)
      == datetime(2026, 10, 26, 8, 0))
check("sin margen, una franja pasada se salta",
      px.proxima_franja(datetime(2026, 10, 26, 8, 1), HORAS)
      == datetime(2026, 10, 26, 12, 0))
check("tras publicar no se repite la franja actual",
      px.proxima_franja(datetime(2026, 10, 26, 8, 0), HORAS, estricta=True)
      == datetime(2026, 10, 26, 12, 0))
check("las horas se leen y se ordenan",
      px._parsear_horas("17:00, 08:00, 12:00, 21:00") == HORAS,
      px._parsear_horas("17:00, 08:00, 12:00, 21:00"))
check("una hora invalida se ignora",
      px._parsear_horas("08:00, 25:00, 12:00") == [8 * 60, 12 * 60],
      px._parsear_horas("08:00, 25:00, 12:00"))
check("sin horas validas se usan las de por defecto",
      px._parsear_horas("nada") == HORAS, px._parsear_horas("nada"))

print("\n" + "=" * 56)
print("TODO CORRECTO" if fallos == 0 else f"{fallos} FALLOS")
sys.exit(1 if fallos else 0)
