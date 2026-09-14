import os,re,json,html,subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application,MessageHandler,ContextTypes,filters

load_dotenv()
TOKEN=os.getenv("BOT_TOKEN","")
REPO=Path(os.getenv("REPO_DIR",Path(__file__).parent))
MAX=int(os.getenv("MAX_OFFERS","30"))
PUSH=os.getenv("AUTO_PUSH","true").lower() in ("true","1","yes")
CATS={"#general":"general","#videojuegos":"videojuegos","#electronica":"electronica","#informatica":"informatica","#hogar":"hogar","#herramientas":"herramientas","#moda":"moda","#juguetes":"juguetes","#libros":"libros","#cocina":"cocina","#deportes":"deportes","#automovil":"automovil","#mascotas":"mascotas","#belleza":"belleza","#bebe":"bebe","#tv":"tv","#erroresdeprecio":"errores-de-precio"}

def getcat(text):
    for tag,slug in CATS.items():
        if re.search(r"(?<!\w)"+re.escape(tag)+r"(?!\w)",text,re.I): return slug

def geturls(msg):
    text=msg.text or msg.caption or ""; out=[]
    for e in list(msg.entities or [])+list(msg.caption_entities or []):
        if e.type=="url": out.append(text[e.offset:e.offset+e.length])
        elif e.type=="text_link" and e.url: out.append(e.url)
    out += re.findall(r"https?://[^\s<>()]+",text)
    return list(dict.fromkeys(out))

def amazon(urls):
    return next((u.rstrip(".,);]") for u in urls if re.search(r"(amazon\.es|amzn\.to)",u,re.I)),None)

def load(slug):
    try:return json.loads((REPO/"data"/f"{slug}.json").read_text())
    except:return []

def rebuild(slug):
    p=REPO/f"{slug}.html"; items=load(slug); cards=[]
    for x in items:
        cards.append(f'<article class="offer"><div class="offer-title">{html.escape(x["title"])}</div><div class="price">{html.escape(x["price"])}</div><div class="meta">{html.escape(x["date"])}</div><a class="buy" href="{html.escape(x["amazon_url"],quote=True)}" target="_blank" rel="nofollow sponsored noopener">VER OFERTA EN AMAZON</a></article>')
    body="".join(cards) or '<div class="empty">No hay ofertas disponibles todavía.</div>'
    raw=p.read_text()
    raw=re.sub(r'<div id="offers">.*?</div>',f'<div id="offers">{body}</div>',raw,count=1,flags=re.S)
    p.write_text(raw)

def push():
    if not PUSH:return
    subprocess.run(["git","add","."],cwd=REPO)
    if subprocess.run(["git","diff","--cached","--quiet"],cwd=REPO).returncode:
        subprocess.run(["git","commit","-m","Actualizar escaparate"],cwd=REPO)
        subprocess.run(["git","push"],cwd=REPO)

async def channel(update:Update,context:ContextTypes.DEFAULT_TYPE):
    msg=update.channel_post
    if not msg:return
    text=msg.text or msg.caption or ""; slug=getcat(text)
    if not slug:return
    url=amazon(geturls(msg))
    if not url:return
    item={"title":text.strip().splitlines()[0][:220],"price":(re.search(r"(\d{1,4}(?:[.,]\d{1,2})?)\s*€",text) or ["",""])[1]+" €","amazon_url":url,"telegram_message_id":msg.message_id,"date":datetime.now().strftime("%Y-%m-%d %H:%M")}
    items=[x for x in load(slug) if x.get("telegram_message_id")!=msg.message_id]
    items.insert(0,item)
    (REPO/"data"/f"{slug}.json").write_text(json.dumps(items[:MAX],ensure_ascii=False,indent=2))
    rebuild(slug); push()

if __name__=="__main__":
    if not TOKEN: raise SystemExit("Falta BOT_TOKEN en .env")
    app=Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL,channel))
    app.run_polling(allowed_updates=["channel_post"])
