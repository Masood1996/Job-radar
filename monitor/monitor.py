import json, re, hashlib, os, smtplib
from email.message import EmailMessage
from datetime import datetime, timezone
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
ROOT=os.path.dirname(os.path.dirname(__file__)); DATA=os.path.join(ROOT,'docs','data'); COMP=os.path.join(DATA,'companies.json'); OUT=os.path.join(DATA,'jobs.json');
KEYWORDS=['quality control','quality assurance','qc specialist','qa specialist','qc analyst','qa analyst','quality specialist','quality operations','gmp','good manufacturing practice','quality systems','quality compliance','laboratory analyst','laboratory specialist','microbiology','sterile','aseptic','injectable','validation','batch release']
UA='PharmaJobRadar/1.0 (+job monitoring)'
def clean(s): return re.sub(r'\s+',' ',s or '').strip()
def score(title,desc,roles):
 t=(title+' '+desc).lower(); pts=0
 for k in KEYWORDS:
  if k in t: pts+=8
 for r in roles:
  if r.lower() in t: pts+=12
 if any(k in t for k in ['quality control','quality assurance','gmp','quality systems','qc specialist','qa specialist']): pts+=15
 return min(100,pts)
def extract_links(html,base):
 soup=BeautifulSoup(html,'html.parser'); out=[]
 for a in soup.find_all('a',href=True):
  text=clean(a.get_text(' ')); href=urljoin(base,a['href']); blob=(text+' '+href).lower()
  if any(k in blob for k in KEYWORDS) or any(k in blob for k in ['career','vacan','job','position','apply']): out.append((text,href))
 return out
def main():
 companies=json.load(open(COMP)); old=json.load(open(OUT)) if os.path.exists(OUT) else []; oldmap={x['id']:x for x in old}; found=[]
 for c in companies:
  try:
   r=requests.get(c['careers'],headers={'User-Agent':UA},timeout=20,allow_redirects=True); r.raise_for_status()
   soup=BeautifulSoup(r.text,'html.parser'); text=clean(soup.get_text(' ')); links=extract_links(r.text,r.url)
   candidates=links[:200]
   for title,url in candidates:
    blob=(title+' '+url).lower(); s=score(title,text,c['roles'])
    if s<35: continue
    jid=hashlib.sha256((c['name']+'|'+url).encode()).hexdigest()[:16]
    item=oldmap.get(jid,{'id':jid,'status':'new','foundAt':datetime.now(timezone.utc).isoformat()})
    item.update({'company':c['name'],'country':c['country'],'title':title or 'Potential matching vacancy','url':url,'score':s,'description':clean(title)[:220]})
    found.append(item)
  except Exception as e:
   print('WARN',c['name'],e)
 # de-dupe and keep top 300
 by={x['id']:x for x in found}; merged=list(by.values()); merged.sort(key=lambda x:(x['status']=='new',x['score']),reverse=True); json.dump(merged[:300],open(OUT,'w'),ensure_ascii=False,indent=2)
 new=[x for x in merged if x['id'] not in oldmap and x['score']>=55]
 if new and os.getenv('SMTP_HOST') and os.getenv('ALERT_TO'):
  msg=EmailMessage(); msg['Subject']=f'Pharma Job Radar: {len(new)} new match(es)'; msg['From']=os.getenv('SMTP_FROM',os.getenv('SMTP_USER')); msg['To']=os.getenv('ALERT_TO'); body='\n\n'.join(f"{x['company']} ({x['country']})\n{x['title']}\n{x['url']}\nMatch: {x['score']}%" for x in new); msg.set_content(body); 
  with smtplib.SMTP(os.getenv('SMTP_HOST'),int(os.getenv('SMTP_PORT','587'))) as s:
   s.starttls(); s.login(os.getenv('SMTP_USER'),os.getenv('SMTP_PASS')); s.send_message(msg)
 print(f'Scanned {len(companies)} companies; {len(merged)} matches; {len(new)} new high-confidence alerts.')
if __name__=='__main__': main()
