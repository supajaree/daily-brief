"""Refresh public RSS once a day; standard library only (no API key)."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).parent))
from rss_engine import generate
root=Path(__file__).resolve().parents[1]
d=root/'data';d.mkdir(exist_ok=True)
result=generate(force=True)
if not (result.get('thailand') or result.get('world')):
    raise RuntimeError('No news fetched: retain last published data')
result['type']='rss'
path=d/(result['date']+'.json')
path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
(d/'latest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
manifest=sorted([p.stem for p in d.glob('20??-??-??.json')],reverse=True)[:120]
(d/'archive.json').write_text(json.dumps({'dates':manifest},ensure_ascii=False,indent=2),encoding='utf8')
print('Updated:',path,'|',sum(len(v) for v in result.values() if isinstance(v,list)),'items')
