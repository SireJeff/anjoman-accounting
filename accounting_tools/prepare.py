from pathlib import Path
import json,zipfile,xml.etree.ElementTree as ET,hashlib
from lxml import html
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'analysis'
doc=html.parse(str(ROOT/'sources/telegram export/messages.html'))
messages=[]; last_sender=''
for e in doc.xpath('//div[contains(concat(" ",normalize-space(@class)," ")," message ")]'):
 def txt(cls):
  xs=e.xpath('.//div[contains(concat(" ",normalize-space(@class)," ")," '+cls+' ")]')
  return '\n'.join(x.text_content().strip() for x in xs)
 sender=txt('from_name') or last_sender;last_sender=sender
 dates=e.xpath('.//div[contains(@class,"date")]/@title')
 replies=e.xpath('.//div[contains(@class,"reply_to")]//a/@href')
 attachments=[a for a in e.xpath('.//a/@href') if a.startswith(('photos/','files/')) and not '_thumb' in a]
 messages.append({'id':e.get('id'),'sender':sender,'timestamp':dates[0] if dates else None,'text':txt('text'),'reply_to':replies,'attachments':['telegram export/'+a for a in attachments],'service':'service' in e.get('class',''),'unavailable_media':'Not included' in e.text_content()})
(out/'messages.json').write_text(json.dumps(messages,ensure_ascii=False,indent=2))
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'};books=[]
for p in (ROOT/'sources').glob('*.xlsx'):
 z=zipfile.ZipFile(p); ss=[]
 if 'xl/sharedStrings.xml' in z.namelist():
  ss=[''.join(si.itertext()) for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
 rels={x.attrib['Id']:x.attrib['Target'] for x in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
 sheets=[]
 for sh in ET.fromstring(z.read('xl/workbook.xml')).find('s:sheets',ns):
  target=rels[sh.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']];target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
  rows=[]
  for row in ET.fromstring(z.read(target)).findall('.//s:sheetData/s:row',ns):
   cells=[]
   for c in row:
    v=c.find('s:v',ns);v=v.text if v is not None else None
    if c.get('t')=='s' and v is not None:v=ss[int(v)]
    if c.get('t')=='inlineStr' and c.find('s:is',ns) is not None:v=''.join(c.find('s:is',ns).itertext())
    f=c.find('s:f',ns)
    if v is not None or f is not None:cells.append({'cell':c.get('r'),'value':v,'formula':f.text if f is not None else None})
   if cells:rows.append({'row':row.get('r'),'cells':cells})
  sheets.append({'name':sh.get('name'),'rows':rows})
 books.append({'file':p.name,'sheets':sheets})
(out/'original_workbooks.json').write_text(json.dumps(books,ensure_ascii=False,indent=2))
manifest=json.loads((out/'manifest.json').read_text());inventory=[]
for f in manifest['files']:
 p=ROOT/'sources'/f['path'];data=p.read_bytes() if p.exists() else b''
 inventory.append({**f,'downloaded':len(data)==f['size'],'sha256':hashlib.sha256(data).hexdigest() if data else None,'message_ids':[m['id'] for m in messages if f['path'] in m['attachments']]})
(out/'inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2))
print(json.dumps({'messages':len(messages),'unavailable_media':sum(m['unavailable_media'] for m in messages),'workbooks':[{ 'file':b['file'],'sheets':[(s['name'],len(s['rows'])) for s in b['sheets']]} for b in books]},ensure_ascii=False))
