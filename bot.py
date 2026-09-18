import asyncio,json,re
from pathlib import Path
from telethon import TelegramClient,events
API_ID=31029230
API_HASH="027e3d6b82fc3330defc4fcd1ee0a06a"
MI_CANAL="@GangasOfertasChollos"; ROOT=Path(".").resolve(); DATA=ROOT/"data"; IMAGES=ROOT/"images"
def cats(): return json.loads((ROOT/"categorias.json").read_text(encoding="utf8"))
def classify(t):
 s=(t or "").lower(); scores={c:sum(w.lower() in s for w in ws) for c,ws in cats().items()}
 c=max(scores,key=scores.get); return c if scores[c] else "general"
def url(t):
 for u in re.findall(r"https?://\S+",t or ""):
  if "amazon." in u.lower(): return u.rstrip(").,;]}>'\"")
 return ""
async def main_msg(m):
 t=m.raw_text or ""; u=url(t)
 if not u:return
 c=classify(t); p=DATA/f"{c}.json"; a=json.loads(p.read_text(encoding="utf8"))
 if any(x.get("amazon_url")==u for x in a):return
 img=""
 if m.media:
  d=IMAGES/c; d.mkdir(parents=True,exist_ok=True); f=d/f"{m.id}.jpg"
  if await m.download_media(file=str(f)): img=f"images/{c}/{f.name}"
 a.insert(0,{"id":m.id,"date":m.date.isoformat(),"title":t.splitlines()[0][:200],"price":"","amazon_url":u,"categoria":c,"image_url":img})
 for old in a[30:]:
  if old.get("image_url","").startswith("images/"):
   q=ROOT/old["image_url"]
   if q.exists():q.unlink()
 p.write_text(json.dumps(a[:30],ensure_ascii=False,indent=2),encoding="utf8")
client=TelegramClient("gangas_ofertas_bot",API_ID,API_HASH)
@client.on(events.NewMessage(chats=MI_CANAL))
async def h(e): await main_msg(e.message)
client.start(); client.run_until_disconnected()
