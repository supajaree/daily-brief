"""Daily Brief local server. Standard library only. Run: python server.py"""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import quote
from urllib.request import Request, urlopen
from pathlib import Path
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET
import json, re, html, threading, time

ROOT=Path(__file__).resolve().parent
TZ=timezone(timedelta(hours=7))
CACHE=ROOT/'latest-brief.json'
FEEDS={
 'thailand':('ข่าวประเทศไทย ข่าววันนี้',5,'🇹🇭'),
 'world':('ข่าวต่างประเทศ ข่าวโลก',5,'🌍'),
 'finance':('เศรษฐกิจ การเงิน ตลาดหุ้น',4,'📈'),
 'technology':('เทคโนโลยี AI วิทยาศาสตร์',4,'💻'),
 'sports':('ข่าวกีฬา',3,'🏅'),
 'music':('Taylor Swift Ariana Grande Olivia Rodrigo Sabrina Carpenter album music',3,'🎵'),
 'bts':('BTS 방탄소년단 new album tour official news',2,'💜'),
}
LOCK=threading.Lock()

def get_feed(query, count, icon):
    url='https://news.google.com/rss/search?q='+quote(query)+'&hl=th&gl=TH&ceid=TH:th'
    req=Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; DailyBriefPersonal/1.0)'})
    with urlopen(req,timeout=14) as res: raw=res.read(2_000_000)
    tree=ET.fromstring(raw)
    items=[]
    for node in tree.findall('./channel/item'):
        title=html.unescape(node.findtext('title') or '').strip()
        source=node.findtext('source') or ''
        link=node.findtext('link') or ''
        if title.endswith(' - '+source):title=title[:-(len(source)+3)]
        if not title or not link:continue
        desc=html.unescape(re.sub('<[^>]+>',' ',node.findtext('description') or ''))
        desc=' '.join(desc.split())
        # RSS summaries frequently repeat a list of links and titles; avoid pretending to have AI summaries.
        summary=('อ่านรายละเอียดและตรวจสอบข้อเท็จจริงจากเว็บไซต์ต้นทาง' if len(desc)<30 else desc[:260])
        items.append({'title':title,'summary':summary,'source':source or 'Google News RSS','url':link,'icon':icon,'published':node.findtext('pubDate') or ''})
        if len(items)>=count:break
    return items

def generate(force=False):
    with LOCK:
        today=datetime.now(TZ).date().isoformat()
        if not force and CACHE.exists():
            try:
                old=json.loads(CACHE.read_text(encoding='utf8'))
                if old.get('date')==today and old.get('thailand') and old.get('world'):return old
            except (OSError,ValueError):pass
        data={'date':today,'type':'rss','thailand':[],'world':[],'finance':[],
              'technology':[],'sports':[],'music':[],'knowledge':[],'history':[],
              'quick':[],'thought':'อ่านข่าวอย่างมีวิจารณญาณ ตรวจสอบข้อมูลจากหลายแหล่งเสมอ',
              'generated_at':datetime.now(TZ).isoformat(),'warnings':[]}
        for name,(term,n,icon) in FEEDS.items():
            try:
                target='music' if name=='bts' else name
                data[target]+=get_feed(term,n,icon)
            except Exception as e:
                data['warnings'].append(f'{name}: {type(e).__name__}')
        if not any(data[k] for k in ['thailand','world']):
            raise RuntimeError('ไม่สามารถเชื่อม Google News RSS ได้ ตรวจสอบอินเทอร์เน็ต หรือทดลองใหม่ภายหลัง')
        CACHE.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
        return data

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def do_GET(self):
        if self.path.split('?')[0]=='/api/brief':
            try:
                obj=generate(force='refresh=1' in self.path)
                status=200
            except Exception as e:
                obj={'error':str(e)};status=503
            payload=json.dumps(obj,ensure_ascii=False).encode('utf8')
            self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(payload)))
            self.end_headers();self.wfile.write(payload)
        else:super().do_GET()

def refresh_daily():
    while True:
        try:generate()
        except Exception as exc:print('RSS refresh:',exc)
        time.sleep(3600)

if __name__=='__main__':
    print('Daily Brief เปิดที่ http://localhost:8765')
    print('โปรดเปิดหน้าต่างนี้ไว้ หากต้องการให้เซิร์ฟเวอร์อัปเดตข่าวรายวัน')
    threading.Thread(target=refresh_daily,daemon=True).start()
    ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
