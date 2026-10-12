from pathlib import Path
import json,base64,urllib.request,urllib.error,time,concurrent.futures,sys
ROOT=Path(__file__).resolve().parents[1]; A=ROOT/'analysis'; C=A/'claude';C.mkdir(exist_ok=True)
import os
KEY=os.environ.get('ANTHROPIC_API_KEY','').strip()
if not KEY:raise RuntimeError('Set ANTHROPIC_API_KEY in the environment')
def call(model,content,name,max_tokens=14000):
 dest=C/(name+'.json')
 if dest.exists():return json.loads(dest.read_text())
 payload={'model':model,'max_tokens':max_tokens,'stream':True,'thinking':{'type':'between_tools' if 'sonnet-5-5' in model else 'adaptive'},'messages':[{'role':'user','content':content}]}
 if 'opus-5-5' in model:payload['output_config']={'effort':'low'}
 for attempt in range(4):
  req=urllib.request.Request('https://api.anthropic.com/v1/messages',data=json.dumps(payload).encode(),headers={'x-api-key':KEY,'anthropic-version':'2023-06-01','Content-Type':'application/json'},method='POST')
  try:
   with urllib.request.urlopen(req,timeout=240) as response:
    chunks=[];d={'model':model,'usage':{}}
    for line in response:
     if not line.startswith(b'data: '):continue
     event=json.loads(line[6:])
     if event.get('type')=='message_start':d.update(event['message'])
     if event.get('type')=='content_block_delta' and event.get('delta',{}).get('type')=='text_delta':
      chunks.append(event['delta']['text'])
      if len(chunks)%100==0:(C/(name+'.partial.txt')).write_text(''.join(chunks))
     if event.get('type')=='message_delta':d['usage'].update(event.get('usage',{}));d.update(event.get('delta',{}))
     if event.get('type')=='error':raise RuntimeError(str(event))
    d['content']=[{'type':'text','text':''.join(chunks)}]
   text='\n'.join(x['text'] for x in d['content'] if x['type']=='text');(C/(name+'.response.json')).write_text(json.dumps(d,ensure_ascii=False))
   if text.startswith('```'):text=text.split('\n',1)[1].rsplit('```',1)[0]
   if d.get('stop_reason')=='max_tokens':raise ValueError('Output truncated at token limit; split this request instead of repeating it')
   parsed=json.loads(text);dest.write_text(json.dumps(parsed,ensure_ascii=False,indent=2));print(name,'OK',d.get('usage'),flush=True);return parsed
  except ValueError:
   raise
  except urllib.error.HTTPError as e:
   msg=e.read(1500).decode();print(name,'HTTP',e.code,msg,flush=True)
   if e.code not in (429,500,502,503,529):raise RuntimeError(msg)
  except Exception as e:print(name,type(e).__name__,str(e)[:300],flush=True)
  time.sleep(3*(attempt+1))
 raise RuntimeError('Failed '+name)
def text(s):return {'type':'text','text':s}
def fileblock(p):
 data=base64.b64encode(p.read_bytes()).decode()
 if p.suffix=='.pdf':return {'type':'document','source':{'type':'base64','media_type':'application/pdf','data':data}}
 return {'type':'image','source':{'type':'base64','media_type':'image/jpeg','data':data}}
messages=json.loads((A/'messages.json').read_text());books=json.loads((A/'original_workbooks.json').read_text());inventory=json.loads((A/'inventory.json').read_text())
contextbooks=[{'file':b['file'],'sheets':[s for s in b['sheets'] if s['name'] in ['مرداد','شهریور','مجموع','تراکنش‌ها','تطبیق','راهنما']]} for b in books]
if sys.argv[1]=='context':
 call('claude-sonnet-5-5',[text('Read ALL these Persian association accounting Telegram messages, original workbook cells and text reports. Return ONLY concise JSON (less than6000 tokens) with keys entity_accounts (names/cards/IBANs known to belong to association/custodian, evidence message IDs), accounting_policy, commitments, conflicts, account_observations, revenue_controls, significant_message_transactions (ONLY message-only money events not covered by an attachment). DO NOT reproduce all workbook rows or all attachment mappings; these are retained separately. Identify duplicate accounting entries and ambiguous project/direction/amount/unit. Distinguish receipt vs expenses vs transfers vs summary. Preserve critical exact numbers and IDs.\n'+json.dumps({'messages':messages,'workbooks':contextbooks,'text_reports':{p.name:p.read_text() for p in (ROOT/'sources/telegram export/files').glob('*.txt')}},ensure_ascii=False))],'context',12000)
elif sys.argv[1] in ['extract','scan']:
 context=json.loads((C/'context.json').read_text()) if (C/'context.json').exists() else {'entity_accounts':[{'custodian':'محمدحسن شیری / حسن شیری','association_card':'5047061055888966','evidence':'Telegram messages49-50 say association funds kept here; bank Shahr account 400816808774 shows association withdrawals messages28/32. Personal funds are commingled (message39:40,000 toman). Do not assume every custodian personal transfer is association expense without context.'}],'accounting_policy':'Cash receipts/disbursements with separate unpaid invoices and uncertain items. Main unit toman.'}
 files=[f for f in inventory if f['downloaded'] and Path(f['path']).suffix.lower() in ['.jpg','.pdf'] and 'CamScanner' not in f['path']]
 if sys.argv[1]=='scan':
  from pypdf import PdfReader,PdfWriter
  original='telegram export/files/CamScanner 13-05-2026 12.43 (1).pdf';reader=PdfReader(ROOT/'sources'/original);files=[]
  for i in range(0,len(reader.pages),3):
   writer=PdfWriter()
   for page in reader.pages[i:i+3]:writer.add_page(page)
   p=ROOT/'sources'/('scan_pages_%02d-%02d.pdf'%(i+1,min(i+3,len(reader.pages))))
   with p.open('wb') as stream:writer.write(stream)
   files.append({'path':p.name,'message_ids':['message124'],'original_path':original,'original_pages':[i+1,min(i+3,len(reader.pages))]})
 group_size=1 if sys.argv[1]=='scan' else 4
 groups=[files[i:i+group_size] for i in range(0,len(files),group_size)]
 def job(pair):
  idx,group=pair;content=[text('You are extracting Persian accounting evidence. Read EVERY document/image carefully, all PDF pages. Return ONLY JSON {"sources":[{"path":...,"document_type":...,"full_text":...,"transactions":[{"date_jalali":...,"date_gregorian":...,"time":...,"amount_original":number|null,"unit":"rial/toman/unknown","amount_toman":number|null,"sender":...,"recipient":...,"sender_account":...,"recipient_account":...,"tracking_id":...,"direction":"income/expense/internal_transfer/unknown","direction_evidence":...,"description_fa":...,"category":...,"project":...,"payment_status":"final/provisional/failed/invoice_only/unknown","invoice_id":...,"tax_original":...,"line_items":[],"message_ids":[],"uncertainties":[]}],"nontransaction_information":...,"uncertainties":[]} ]}. Extract tracking identifiers as strings. Bank debit on custodian account means cash expense unless internal transfer. If no evidence establishes entity side, use unknown. Invoice proves billing, not payment. Distinguish repeated document from repeated transaction. Dates printed on receipt take precedence over upload dates, preserve conflicts. Main financial unit is TOMAN (10 rials=1 toman). Do NOT infer currency from magnitude. Entity/context evidence:\n'+json.dumps({k:context.get(k) for k in ['entity_accounts','accounting_policy']},ensure_ascii=False))]
  for f in group:
   ids=f['message_ids'];near=[]
   for i,m in enumerate(messages):
    if m['id'] in ids:near.extend(messages[max(0,i-2):i+4]);near.extend(x for x in messages if any(m['id'] in rr for rr in x['reply_to']))
   content.append(text('SOURCE PATH: '+f['path']+'\nOriginal source/pages: '+json.dumps({k:f[k] for k in ['original_path','original_pages'] if k in f})+'\nTelegram associated and nearby messages (proximity is weaker evidence than direct replies): '+json.dumps(near,ensure_ascii=False)))
   content.append(fileblock(ROOT/'sources'/f['path']))
  return call('claude-sonnet-5-5',content,('scan_' if sys.argv[1]=='scan' else 'extract_')+'%02d'%idx,15000)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(job,enumerate(groups)))
elif sys.argv[1]=='scan_review':
 scans=[json.loads(p.read_text()) for p in sorted(C.glob('scan_*.json')) if '.response.' not in p.name]
 call('claude-opus-5-5',[text('Independently audit ALL 11 pages of this Persian receipt PDF against Sonnet OCR below. Return ONLY JSON {pages:[{page,document_type,amount_original,unit,amount_toman,date_jalali,time,merchant,payment_status,unique_receipt_identifier,duplicate_of_page:null|number,notes}],corrections:[],canonical_purchases:[],unreadable_fields:[]}. CRITICAL printed fiscal-memory serial S001001000010154 and terminal serial A001001000020043 are common TERMINAL metadata, not UNIQUE invoice IDs. Do NOT conclude duplicates from common fiscal-memory serial or same179000 amount. Compare unique barcode string, time, item count, receipt number and identical images. Several different purchases can have identical amount at18:46/18:47/18:48/18:50/18:56. Establish actual distinct receipts visually across every page. Handwritten last invoice needs careful OCR, avoid a guessed495000 if unreadable. Purchase receipts paid by volunteer may support incurred event cost but not association reimbursement cash until matched. Source context: Telegram message128 says these are late Yalda cookies and items sent by Parnian; message129 says enter these receipts, reply toPDF message124. These may support reimbursement receipts 1.55m and2.5m in photos27/28, must not count both purchases and reimbursement as cash expenses. Sonnet readings:\n'+json.dumps(scans,ensure_ascii=False)),fileblock(ROOT/'sources/telegram export/files/CamScanner 13-05-2026 12.43 (1).pdf')],'scan_review',14000)
elif sys.argv[1]=='reconcile':
 sources=[]
 for p in sorted(C.glob('*.json')):
  if p.name.startswith(('extract_','scan_')) and '.response.' not in p.name:sources.extend(json.loads(p.read_text()).get('sources',[]))
 evidence={'messages':messages,'original_workbooks':contextbooks,'context_analysis':json.loads((C/'context.json').read_text()),'ocr_sources':sources,'scan_independent_review':json.loads((C/'scan_review.json').read_text()),'text_reports':{p.name:p.read_text() for p in (ROOT/'sources/telegram export/files').glob('*.txt')},'inventory':inventory}
 (A/'reconciliation_input.json').write_text(json.dumps(evidence,ensure_ascii=False))
 prompt='''Act as an expert association accountant and evidence reconciler. Analyze EVERY source below. Return ONLY compact JSON. Produce one canonical candidate ledger covering ALL financial events, and separate account observations, commitments and source-report controls. User needs a professional detailed financial report, not invented assurance. All financial output amounts in TOMAN. IMPORTANT: source extraction is fallible; repair classification with full chats and original ledger. Same invoice/payment/reposted photo can support ONE transaction, never multiple. Treat explicit original ledger duplicates (e.g. teacher meeting pastry) carefully. Bank charges distinct from principal only when source supports them. Cash contribution for جشن cash شاباش message111 versus original expense must be flagged, not guessed. Event gross receipts and net settlement cannot both enter cash receipts if double counts; internal transfers between custodian accounts NOT income/expense. 23m receipt versus event sales27.235m versus actual payout requires bridge. Donor personal account payment of expenses requires custody treatment rather than automatic association cash expense. 100,037,800 rial withdrawal in Yalda message115 explicitly expenses/transfer, not income. No dates invented from upload timestamp if actual date unavailable. Workbook-only amounts may be Supported ledger-derived with date only month; unsupported additions must remain Review. Invoices cannot prove cash paid. Counterparty metadata may infer purpose, but label inference and leave uncertain project Review. No external bank statement = cannot claim reconciled closing cash, opening balance unknown. Never include unsupported direction or currency in supported totals. Retain all evidence candidates, including duplicates, and map every financial source to ledger or register. Preserve unknown source date components. Scan pages refer back to original PDF page ranges (scan_pages_01-03.pdf means original pages1-3).
JSON schema:
{
"ledger":[{"id":"TX0001","date_jalali":null,"date_gregorian":null,"period_jalali":"1404/05" or null,"date_basis":"receipt/message/workbook_month/unknown","direction":"Receipt/Payment/Internal transfer/Unknown","amount_original":number|null,"unit_original":"rial/toman/unknown","amount_toman":number|null,"counterparty":"...","description_fa":"...","description_en":"...","category":"Course fees/Donations/Opening funds/Teaching/Administration/Advertising/Printing/Hospitality/Events/Equipment/Supplies/Bank fees/Unclassified/Transfers","project":"...","status":"Supported/Review/Duplicate/Invoice only/Summary only","evidence_basis":"Receipt and message/Receipt only/Message only/Original ledger/Invoice/Report","cash_account":"...","sources":["repo-relative path#page=n or workbook#sheet!cell"],"message_ids":["messageN"],"tracking_id":null,"duplicate_of":null,"review_reason":"...","notes":"..."}],
"issues":[{"id":"ISS001","severity":"High/Medium/Low","title":"...","description":"...","amount_toman":number|null,"transaction_ids":[],"action":"...","sources":[]}],
"invoice_register":[{"id":"INV001","date_jalali":...,"supplier":...,"description_en":...,"gross_toman":number|null,"tax_toman":number|null,"payment_match_ids":[],"status":"Matched payment/Unmatched invoice/Uncertain","sources":[],"notes":...}],
"observations":[{"date":...,"amount_toman":number|null,"type":"reported_balance/report_total/message_summary","description":...,"sources":[]}],
"source_coverage":[{"path":"every relevant source path","treatment":"Extracted/Reconciled/Context only","ledger_ids":[],"note":...}],
"original_ledger_reconciliation":[{"sheet":"مجموع","cell":"B3 or D2","original_amount_toman":number,"ledger_ids":[],"disposition":"Retained/Corrected/Duplicate/Review/Reclassified","explanation":...}],
"policies":[...],"report_sections":[{"title":"...","paragraphs":[...]}],"project_notes":[...]
}
Keep ledger descriptions and notes concise but precise. Full detailed narrative belongs report_sections. Include original financial workbook rows not corroborated as ledger-derived rather than silently discarding. Retain all partial dates as period, never fabricate day1. In ledger include paid items and unresolved items; invoice register contains all vendor invoices, excludes bank transfer receipts. Where invoices prove purchase but payment unconfirmed, leave status Invoice only; do not independently double-count matched expense. Source coverage must cover messages.html, every full image, all four original PDFs and three course text reports, both workbooks. No timestamps based on file upload names. JSON only, no code fences.
'''
 call('claude-opus-5-5',[text(prompt+json.dumps(evidence,ensure_ascii=False))],'reconciled',60000)
elif sys.argv[1]=='report':
 d=json.loads((A/'final_data.json').read_text());v=json.loads((A/'validation.json').read_text())
 def strings(x):
  if isinstance(x,str):return [x]
  if isinstance(x,list):return [s for z in x for s in strings(z)]
  if isinstance(x,dict):return [s for k,z in x.items() if k!='description_fa' for s in strings(z)]
  return []
 import re
 translate=list(dict.fromkeys(s for s in strings(d) if re.search(r'[\u0600-\u06ff]',s)))
 call('claude-sonnet-5-5',[text('Write the complete English narrative for this association financial report from FINAL validated ledger and exact totals. Return ONLY JSON {sections:[{title,paragraphs:[]}],translation_map:{"exact original Persian-containing string":"English translation or transliteration"}}. Translate EVERY string in translate_strings exactly, including names/project names; keep source file names as-is but translate Persian worksheet names in readable source references. Narrative needs detailed executive findings; receipts vs operating revenue vs opening association funds; payments by category; year/project risks; original ledger adjustments; project2025/2026 introduction event gross/net/settlement conflict; Yalda expense and reimbursement issues; unconfirmed receipts; commitments and missing statements; concrete prioritized next steps. No claimed audited profit or closing cash. Supported includes clearly disclosed original-ledger-only evidence. Mention extracted but unconfirmed sources and paid reimbursement vs volunteer receipts. Do not repeat every ledger row, invoices and issues are separate full schedules. Exact supported receipts/payments/net from validation summary, no arithmetic guessing. All values toman. No generic stock market/tax advice. Professional, precise, thorough, about1200-1800words. Data:\n'+json.dumps({'final_data':d,'validation':v,'translate_strings':translate},ensure_ascii=False))],'report_narrative',18000)
elif sys.argv[1]=='audit':
 d=json.loads((A/'final_data.json').read_text());v=json.loads((A/'validation.json').read_text());e=json.loads((A/'reconciliation_input.json').read_text())
 call('claude-opus-5-5',[text('Independently audit the FINAL canonical association ledger against all original evidence. Return ONLY JSON {critical_errors:[{id,reason,required_correction}],ledger_patches:[{id,changes:{field:new_value}}],missing_records:[],narrative_corrections:[],checks:[{name,result,details}]}. Check duplicate principal vs fees, volunteer purchases vs reimbursement double-count, gross event totals vs net settlements, dates, bank account ownership, provisional receipts, income vs internal opening transfers, original ledger duplicates, complete source coverage, all message-only amounts. Financial materiality1toman; keep lower precision on source amounts. Do not invent confirmations. Supported only ledger-derived must be accurately disclosed. Prefer Review for unresolved entity ownership even if custodian name matches. Distinguish third-party donor bank fees from association expenses. The fiscal-memory and terminal serial shared across Canbo receipts is NOT a unique transaction. Compare ledger+proposed report against original evidence. Only propose specific evidence-grounded corrections; do not redo entire ledger.\n'+json.dumps({'final_data':d,'validation':v,'report_narrative':json.loads((C/'report_narrative.json').read_text()),'source_evidence':e},ensure_ascii=False))],'final_audit',18000)
