# Gangas Ofertas y Chollos

Web de ofertas Amazon España y bot Telethon.

## Datos y Multimedia
- Las ofertas se guardan localmente en `data/*.json` con soporte para el campo `image`.
- Las imágenes de las ofertas se descargan automáticamente en `data/images/`.

## Diccionario
Las palabras de clasificación se editan en `categorias.json` con soporte de búsqueda insensible a mayúsculas y tildes.

## Bot
`bot.py` escucha los mensajes del canal de Telegram, extrae el título limpio, precio, enlace de Amazon, descarga la imagen asociada y actualiza tanto la categoría correspondiente como el feed `general.json`.

## Publicación
```bash
git add data/
git commit -m "Actualizar ofertas e imágenes"
git push
```
