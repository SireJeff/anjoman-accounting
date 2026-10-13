from pathlib import Path
import json,re,collections,math
ROOT=Path(__file__).resolve().parents[1]; A=ROOT/'analysis'
def jalali_to_gregorian(jy,jm,jd):
 jy+=1595;days=-355668+365*jy+(jy//33)*8+((jy%33+3)//4)+jd+(jm-1)*31 if jm<7 else -355668+365*jy+(jy//33)*8+((jy%33+3)//4)+jd+(jm-7)*30+186
 gy=400*(days//146097);days%=146097
 if days>36524:
  days-=1;gy+=100*(days//36524);days%=36524
  if days>=365:days+=1
 gy+=4*(days//1461);days%=1461
 if days>365:gy+=(days-1)//365;days=(days-1)%365
 gd=days+1;month_days=[0,31,29 if gy%4==0 and (gy%100!=0 or gy%400==0) else 28,31,30,31,30,31,31,30,31,30,31];gm=1
 while gm<=12 and gd>month_days[gm]:gd-=month_days[gm];gm+=1
 return f'{gy:04d}-{gm:02d}-{gd:02d}'
assert jalali_to_gregorian(1404,5,2)=='2025-07-24'
d=json.loads((A/'claude/reconciled.json').read_text());issues=[]
for t in d['ledger']:
 for k in ['date_jalali','date_gregorian','period_jalali','duplicate_of','tracking_id']:t.setdefault(k,None)
 t['project']=t.get('project') or 'Unassigned'
 for k in ['counterparty','description_fa','description_en','category','cash_account','review_reason','notes','evidence_basis']:t[k]=t.get(k) or ''
 for k in ['sources','message_ids']:t[k]=t.get(k) or []
 for k in ['amount_original','amount_toman']:
  v=t.get(k);t[k]=float(v) if isinstance(v,(int,float)) and math.isfinite(v) else None
 exact=re.fullmatch(r'(14\d\d)/(\d{1,2})/(\d{1,2})',t.get('date_jalali') or '')
 if exact:
  jy,jm,jd=map(int,exact.groups())
  if 1<=jm<=12 and 1<=jd<=31:
   iso=jalali_to_gregorian(jy,jm,jd)
   if t['date_gregorian'] and t['date_gregorian']!=iso:issues.append({'id':t['id'],'check':'Gregorian date corrected','previous':t['date_gregorian'],'new':iso})
   t['date_gregorian']=iso;t['date_jalali']=f'{jy:04d}/{jm:02d}/{jd:02d}';t['period_jalali']=f'{jy:04d}/{jm:02d}'
 else:t['date_gregorian']=None
 if t['period_jalali']:
  p=re.fullmatch(r'(14\d\d)/(\d{1,2})',t['period_jalali'])
  if p:t['period_jalali']=f'{int(p[1]):04d}/{int(p[2]):02d}'
 if t['amount_original'] is not None and t.get('unit_original') in ['rial','toman']:
  converted=t['amount_original']/(10 if t['unit_original']=='rial' else 1)
  if t['amount_toman'] is not None and abs(t['amount_toman']-converted)>0.05:issues.append({'id':t['id'],'check':'Currency mismatch','original':t['amount_original'],'unit':t['unit_original'],'toman':t['amount_toman'],'expected':converted})
 if t['status']=='Supported' and (t['amount_toman'] is None or t['direction'] not in ['Receipt','Payment','Internal transfer']):issues.append({'id':t['id'],'check':'Unsupported supported transaction'})
ids=[t['id'] for t in d['ledger']];assert len(ids)==len(set(ids))
for t in d['ledger']:
 if t['duplicate_of'] and t['duplicate_of'] not in ids:issues.append({'id':t['id'],'check':'Missing duplicate target','target':t['duplicate_of']})
summary={}
for direction in ['Receipt','Payment','Internal transfer','Unknown']:
 for status in ['Supported','Review','Duplicate','Invoice only','Summary only']:
  rows=[t for t in d['ledger'] if t['direction']==direction and t['status']==status];summary[direction+'|'+status]={'count':len(rows),'amount':round(sum(t['amount_toman'] or 0 for t in rows),2)}
summary['receipt_composition']={'former_board_handover':sum(t['amount_toman'] or 0 for t in d['ledger'] if t['status']=='Supported' and t['direction']=='Receipt' and t['category']=='Opening funds')};summary['receipt_composition']['other_supported_receipts']=summary['Receipt|Supported']['amount']-summary['receipt_composition']['former_board_handover']
summary['net_cash_activity']=round(summary['Receipt|Supported']['amount']-summary['Payment|Supported']['amount'],2)
summary['ledger_records']=len(ids);summary['issue_count']=len(d['issues'])
(A/'final_data.json').write_text(json.dumps(d,ensure_ascii=False,indent=2));(A/'validation.json').write_text(json.dumps({'checks':issues,'summary':summary},ensure_ascii=False,indent=2));print(json.dumps({'checks':issues,'summary':summary},ensure_ascii=False))
