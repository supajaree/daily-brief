"""Curated publisher headlines via Google News RSS; no scraping, no API key.
Google may omit publishers or limit description text; failures do not manufacture stories.
"""
from urllib.parse import quote
from urllib.request import Request, urlopen
from pathlib import Path
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import xml.etree.ElementTree as ET
import json, html, re, threading, time
ROOT=Path(__file__).resolve().parents[1]
TZ=timezone(timedelta(hours=7))
CACHE=ROOT/'data'/'latest.json'
LOCK=threading.Lock()
SOURCES={
 'thailand': [('ไทยรัฐ','thairath.co.th'),('THE STANDARD','thestandard.co'),('Thai PBS','thaipbs.or.th')],
 'world':[('Reuters','reuters.com'),('BBC','bbc.com'),('Thai PBS','thaipbs.or.th')],
 'finance':[('ประชาชาติธุรกิจ','prachachat.net'),('กรุงเทพธุรกิจ','bangkokbiznews.com'),('THE STANDARD','thestandard.co')],
 'technology':[('TechCrunch','techcrunch.com'),('The Verge','theverge.com'),('THE STANDARD','thestandard.co')],
 'sports':[('BBC Sport','bbc.com'),('Reuters','reuters.com'),('ไทยรัฐ','thairath.co.th')],
 'music':[('Billboard','billboard.com'),('Pitchfork','pitchfork.com'),('Rolling Stone','rollingstone.com')],
 'bts':[('Weverse','weverse.io'),('BIGHIT MUSIC','bighitsmusic.com'),('Billboard','billboard.com')]
}
TERMS={'thailand':'ข่าว ประเทศไทย','world':'world international news','finance':'เศรษฐกิจ การเงิน ตลาดหุ้น','technology':'AI technology news','sports':'กีฬา football sports','music':'music album chart Taylor Swift Ariana Grande Olivia Rodrigo Sabrina Carpenter','bts':'BTS 방탄소년단 tour music'}
LIMIT={'thailand':5,'world':5,'finance':4,'technology':4,'sports':3,'music':5,'bts':3}
ICONS={'thailand':'🇹🇭','world':'🌏','finance':'💰','technology':'🤖','sports':'⚽','music':'🎧','bts':'💜'}

def fetch_one(category,source):
    name,domain=source
    term=TERMS[category]+' site:'+domain
    url='https://news.google.com/rss/search?q='+quote(term)+'&hl='+('th&gl=TH&ceid=TH:th' if category in ('thailand','finance') else 'en&gl=US&ceid=US:en')
    req=Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; DailyBriefReader/1.0)'})
    with urlopen(req, timeout=16) as resp: xml=resp.read(2_000_000)
    root=ET.fromstring(xml)
    results=[]
    for node in root.findall('./channel/item')[:15]:
        title=html.unescape(node.findtext('title') or '').strip()
        src=(node.findtext('source') or name).strip()
        link=(node.findtext('link') or '').strip()
        if not title or not link: continue
        if title.lower().endswith(' - '+src.lower()): title=title[:-(len(src)+3)]
        pub=node.findtext('pubDate') or ''
        try:
            dt=parsedate_to_datetime(pub)
            stamp=dt.timestamp()
            published=dt.astimezone(TZ).strftime('%d/%m/%Y %H:%M')
        except Exception:
            stamp=0
            published=pub
        # RSS description is often unrelated link HTML; do not invent story summaries.
        description=html.unescape(re.sub(r'<[^>]*>',' ',node.findtext('description') or ''))
        description=' '.join(description.split())
        if title in description or len(description)<35: description='อ่านรายละเอียดเพิ่มเติมและตรวจสอบข้อมูลล่าสุดจากเว็บไซต์ต้นทาง'
        else: description=description[:260]
        results.append({'title':title,'summary':description,'source':name,'url':link,'icon':ICONS[category], 'published':published,'published_unix':stamp})
    return results

def generate(force=False):
    with LOCK:
        today=datetime.now(TZ).date().isoformat()
        if CACHE.exists() and not force:
            try:
                old=json.loads(CACHE.read_text(encoding='utf-8'))
                if old.get('date')==today and old.get('thailand'):return old
            except (ValueError,OSError): pass
        data={'date':today,'type':'rss','thailand':[],'world':[],'finance':[],'technology':[], 'sports':[], 'music':[], 'bts':[], 'knowledge':[], 'history':[], 'quick':[], 'games':[], 'generated_at':datetime.now(TZ).isoformat(), 'warnings':[], 'thought':'พาดหัวจาก RSS อาจมีข้อมูลไม่ครบ โปรดอ่านและตรวจสอบข่าวจากลิงก์ต้นทาง'}
        raw={k:[] for k in SOURCES}
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures={pool.submit(fetch_one,category,s): (category,s[0]) for category,ss in SOURCES.items() for s in ss}
            for f in as_completed(futures):
                category,source=futures[f]
                try: raw[category].extend(f.result())
                except Exception as e:data['warnings'].append(f'{category}/{source}: {type(e).__name__}')
        for category,items in raw.items():
            seen=set()
            for item in sorted(items,key=lambda x:x['published_unix'],reverse=True):
                key=re.sub(r'\W+','',item['title'].lower())[:65]
                if key in seen:continue
                seen.add(key)
                item.pop('published_unix',None)
                data[category].append(item)
                if len(data[category])>=LIMIT[category]:break
        # Maintain separate BTS news and also combine within existing Music Radar card.
        data['music']+=data['bts']
        if not (data['thailand'] or data['world']):
            raise RuntimeError('Cannot retrieve current news. Existing published news should be preserved.')
        CACHE.parent.mkdir(parents=True,exist_ok=True)
        return data
