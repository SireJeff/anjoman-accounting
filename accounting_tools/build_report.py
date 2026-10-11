from pathlib import Path
import json,html,collections
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT,TA_RIGHT
from reportlab.lib.pagesizes import A4,landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'analysis';O=ROOT/'outputs/anjoman-20261010';O.mkdir(parents=True,exist_ok=True)
d=json.loads((A/'final_data.json').read_text());v=json.loads((A/'validation.json').read_text());inv=json.loads((A/'inventory.json').read_text());L=d['ledger'];narr=json.loads((A/'claude/report_narrative.json').read_text())
pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'));pdfmetrics.registerFont(TTFont('DejaVuBold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFontFamily('DejaVu',normal='DejaVu',bold='DejaVuBold',italic='DejaVu',boldItalic='DejaVuBold')
styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='Main',fontName='DejaVu',fontSize=9,leading=14,textColor=colors.HexColor('#253547'),spaceAfter=8));styles.add(ParagraphStyle(name='ReportTitle',fontName='DejaVuBold',fontSize=22,leading=28,textColor=colors.HexColor('#20354D'),spaceAfter=18));styles.add(ParagraphStyle(name='Section',fontName='DejaVuBold',fontSize=13,leading=18,textColor=colors.HexColor('#20354D'),spaceBefore=15,spaceAfter=9));styles.add(ParagraphStyle(name='Cell',fontName='DejaVu',fontSize=7,leading=10,spaceAfter=1));styles.add(ParagraphStyle(name='CellHead',fontName='DejaVuBold',fontSize=7,leading=10,textColor=colors.white));
story=[];md=[]
def fmt(n):return 'Unavailable' if n is None else f'{n:,.1f}'.rstrip('0').rstrip('.')
translations=sorted(narr.get('translation_map',{}).items(),key=lambda item:len(item[0]),reverse=True)
def p(t,style='Main'):
 t=str(t)
 for original,translated in translations:
  if original in t:t=t.replace(original,translated)
 return Paragraph(html.escape(t).replace('\n','<br/>'),styles[style])
def para(t):story.append(p(t));md.append(str(t)+'\n')
def heading(t):story.append(p(t,'Section'));md.append('## '+t+'\n')
def table(headers,rows,widths):
 grid=[[p(x,'CellHead') for x in headers]]+[[p('' if x is None else x,'Cell') for x in row] for row in rows]
 t=Table(grid,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#20354D')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F1F4F7')]),('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#20354D'))]));story.append(t);story.append(Spacer(1,10));md.append('| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+'\n'.join('| '+' | '.join(str(x or '').replace('\n',' ').replace('|','/') for x in row)+' |' for row in rows)+'\n')
story.append(p('ANJOMAN\nFinancial report','ReportTitle'));para('Physics student association | Reconstructed receipts, payments and reconciliation');para('Report cutoff: 10 October 2026 / 1405/07/18. All amounts in toman unless the original unit is explicitly shown.');para('Prepared from 78 repository source files: 188 Telegram messages, 68 full-size images, four PDFs (including every page of the 11-page CamScanner scan), three course reports and two workbooks.');para('Revision: incorporates user confirmations received 10–11 October 2026. The transaction cutoff remains 10 October 2026.');para('Reporting basis: cash activity reconstructed from available evidence. Supported totals include original-ledger-only records where clearly labeled. Opening association cash and bank-reconciled closing cash remain unavailable. This report does not assert an audit opinion or a complete accrual balance sheet.');
heading('Executive financial summary')
s=v['summary'];table(['Measure','Amount / count','Interpretation'],[['Supported receipts',fmt(s['Receipt|Supported']['amount']),'Cash inflows included in this reconstruction'],['Former-board handover', '11,000,000','Included in receipts; opening funds, not operating revenue'],['Other supported receipts', '101,552,000','Includes donations and ledger-derived event/course receipts'],['Supported payments',fmt(s['Payment|Supported']['amount']),'Cash outflows included in this reconstruction'],['Net supported cash activity',fmt(s['net_cash_activity']),'Receipts less payments, before opening cash'],['Review receipt amounts',fmt(s['Receipt|Review']['amount']),'Excluded until clarified'],['Review payment amounts',fmt(s['Payment|Review']['amount']),'Excluded until clarified'],['Review unclassified amounts',fmt(s['Unknown|Review']['amount']),'Direction unresolved'],['Candidate records',str(len(L)),'Includes supported and excluded candidates'],['Reconciliation issues',str(len(d['issues'])),'Actions documented in issue register']], [165,110,240])
for sec in narr.get('sections',[]):
 heading(sec['title'])
 for q in sec.get('paragraphs',[]):para(q)
heading('Website domain expense and VM budget')
para('Website addendum recorded 11 October 2026. The 3,000,000 toman domain purchase is user-declared with no receipt; its purchase date and funding source are unknown. TX0096 is held in Review, outside supported cutoff cash totals. The VM forecast is also outside actual payments.')
table(['Website item','Amount (toman)','Evidence / basis'],[['Declared alenush.com purchase','3,000,000','User declaration; payment date and funding unknown'],['VM daily rate','65,544','655,440 rial per day divided by 10'],['Three-month VM forecast','6,030,048','92 days at constant rate'],['Domain plus VM budget','9,030,048','Declared domain cost plus VM forecast; not a paid total']],[180,105,230])
table(['Jalali service interval','Days','VM forecast (toman)'],[['1405/05/28 to 1405/06/28',31,'2,031,864'],['1405/06/28 to 1405/07/28',31,'2,031,864'],['1405/07/28 to 1405/08/28',30,'1,966,320'],['Total',92,'6,030,048']],[260,65,190])
para('Alnush VM configuration: 2 vCPU, 4 GB RAM, 30 GB SSD. Service starts 1405/05/28 at 22:56 Asia/Tehran and the three-month horizon ends 1405/08/28 at the same time. Forecast assumes uninterrupted billing at the quoted rate. Actual VM payments, additional fees, tax, credits and downtime were not supplied.')
heading('Monthly receipts and payments')
months=sorted(set(t['period_jalali'] or 'Undated' for t in L));monthly=[]
for month in months:
 rows=[t for t in L if (t['period_jalali'] or 'Undated')==month];rc=sum(t['amount_toman'] or 0 for t in rows if t['status']=='Supported' and t['direction']=='Receipt');pa=sum(t['amount_toman'] or 0 for t in rows if t['status']=='Supported' and t['direction']=='Payment');rv=sum(t['amount_toman'] or 0 for t in rows if t['status']=='Review');monthly.append([month,fmt(rc),fmt(pa),fmt(rc-pa),fmt(rv)])
table(['Jalali month','Receipts','Payments','Net activity','Under review'],monthly,[83,108,108,108,108])
heading('Project cash activity')
projects=sorted(set(t['project'] for t in L));pr=[]
for proj in projects:
 rows=[t for t in L if t['project']==proj];rc=sum(t['amount_toman'] or 0 for t in rows if t['status']=='Supported' and t['direction']=='Receipt');pa=sum(t['amount_toman'] or 0 for t in rows if t['status']=='Supported' and t['direction']=='Payment');rv=sum(t['amount_toman'] or 0 for t in rows if t['status']=='Review');pr.append([proj,fmt(rc),fmt(pa),fmt(rc-pa),fmt(rv)])
table(['Project','Receipts','Payments','Net activity','Under review'],pr,[170,86,86,86,87]);para('Net project cash activity is not an accrual profit measure. Reimbursements are dated when paid; supplier purchases are not counted again when they support the same reimbursement. Gross sales reports and settlements use different measurement bases.');
heading('Cash activity by category')
cr=[]
for category in sorted(set(t['category'] for t in L)):
 rows=[t for t in L if t['category']==category];rc=sum(t['amount_toman'] or 0 for t in rows if t['status']=='Supported' and t['direction']=='Receipt');pa=sum(t['amount_toman'] or 0 for t in rows if t['status']=='Supported' and t['direction']=='Payment');rv=sum(t['amount_toman'] or 0 for t in rows if t['status']=='Review');cr.append([category,fmt(rc),fmt(pa),fmt(rv)])
table(['Category','Receipts','Payments','Under review'],cr,[170,115,115,115])
heading('Summer School 1405 instructor payment register')
table(['ID / date','Instructor / bank payee','Course','Toman','Evidence basis'],[[t['transaction_id']+'\n'+t['date_jalali'],t['instructor']+'\nBank payee: '+t['account_payee'],t['course'],fmt(t['amount_toman']),t['settlement_basis']] for t in d.get('instructor_register',[])],[75,155,105,80,100])
para('Five instructor payments total 11,500,000 toman. The user stated six; the sixth is not yet matched. The 950,000 payment to Zahra Amiri is introduction-event sticker packs, not teaching fees. Payment to Alireza Kachooei is instructor compensation for Abolfazl Ahmadi. The supplied instructor cards were not printed on the IBAN receipts; these matches use recipient names and explicit user confirmation, not an asserted exact card-number match. No additional receipt or income is created from the 35% email statement.')
heading('Supplier invoice matching')
table(['Invoice ID','Supplier / description','Gross','Tax','Payment match / status'],[[t['id'],t['supplier']+'\n'+t['description_en'],fmt(t['gross_toman']),fmt(t['tax_toman']),', '.join(t['payment_match_ids'])+'\n'+t['status']] for t in d['invoice_register']],[58,235,70,60,92]);
heading('Account observations and reported balances')
table(['Date / source','Amount','Observation'],[[str(t.get('date') or 'Undated')+'\n'+', '.join(t.get('sources',[])),fmt(t.get('amount_toman')),t.get('description','')] for t in d.get('observations',[])],[150,90,275]);
heading('Required reconciliation actions')
for issue in d['issues']:
 story.append(KeepTogether([p(issue['id']+' | '+issue['severity']+' | '+issue['title'],'Section'),p(issue['description'])]));md.append('### '+issue['id']+' '+issue['title']+'\n');para('Amount: '+fmt(issue.get('amount_toman'))+'. Transactions: '+(', '.join(issue.get('transaction_ids',[])) or 'Not transaction-specific')+'.');para('Required action: '+issue['action']);para('Evidence: '+', '.join(issue.get('sources',[])))
heading('Bridge from the original workbook totals')
table(['Adjustment','Change to payments (toman)'],[['Original recorded payments','38,638,300'],['Remove duplicate professors meeting pastry (D23)','(1,052,375)'],['Exclude probable duplicate advertising (D12) pending confirmation','(400,000)'],['Exclude ambiguous cash shabash (D29) pending direction confirmation','(300,000)'],['Correct booth refreshments from 230,000 to 235,000','5,000'],['Add documented transfer fee','900'],['Add thread reimbursement','180,000'],['Add Parnian reimbursement installments','4,050,000'],['First reconstruction before folder confirmation','41,121,825'],['Add 19 unique user-confirmed folder expenses','57,963,370'],['Revised supported payments',fmt(s['Payment|Supported']['amount'])]],[370,145])
para('Original receipts of 112,552,000 remain unchanged. Original net cash activity was 73,913,700; after these adjustments it is '+fmt(s['net_cash_activity'])+'. These totals include disclosed original-ledger-only entries and exclude unresolved candidates.')
heading('Original ledger reconciliation')
table(['Source cell','Original (toman)','Transaction IDs','Disposition / explanation'],[[t['sheet']+'!'+t['cell'],fmt(t['original_amount_toman']),', '.join(t['ledger_ids']),t['disposition']+'\n'+t['explanation']] for t in d['original_ledger_reconciliation']],[75,90,85,265]);
heading('Accounting and extraction policies')
for q in d['policies']:para(q if isinstance(q,str) else json.dumps(q,ensure_ascii=False))
para('The five unavailable-media notices already present in the Telegram export are retained as gaps: message5, message24, message132, message133 and message134. No omitted attachment content was invented. Export icons and thumbnail derivatives were excluded from financial evidence.');
story.append(PageBreak());heading('Complete transaction register')
para('This register contains every canonical financial candidate, including Review, Duplicate, Invoice only and Summary only entries. Only Supported Receipt and Payment entries affect the cash summary. Folder expenses now include explicit user confirmation; provisional screens and invoice-only evidence retain their original limitations. Full Persian source text, original amounts, units and references are retained in the workbook and evidence data.');
for i in range(0,len(L),25):
 chunk=L[i:i+25];table(['ID / date','Direction / status','Description / evidence','Toman'],[[t['id']+'\n'+(t['date_jalali'] or t['period_jalali'] or 'Undated'),t['direction']+'\n'+t['status'],t['description_en']+'\n'+t['evidence_basis']+'; '+', '.join(t['message_ids'])+(('\nReview: '+t['review_reason']) if t['review_reason'] else ''),fmt(t['amount_toman'])] for t in chunk],[83,85,255,92])
heading('Evidence inventory and coverage')
coverage={t['path']:t for t in d['source_coverage']};table(['Source ID','Repository file','Ledger references / treatment'],[['SRC'+str(i+1).zfill(3),f['path'],', '.join(coverage.get(f['path'],{}).get('ledger_ids',[]))+'\n'+coverage.get(f['path'],{}).get('treatment','Context only')+'\n'+coverage.get(f['path'],{}).get('note','')] for i,f in enumerate(inv)],[60,250,205]);
heading('Validation and reproducibility')
para('All 78 retrieved source files were byte-verified against their GitHub blob hashes. Jalali dates with a complete supported date were converted programmatically, rather than relying on OCR date conversion. Original data and original formula text are preserved. Source documents and extracted evidence are linked by stable transaction and source IDs. Workbook summary formulas were recalculated and checked against independently calculated ledger totals. The later user-confirmation source is recorded separately from the 78 original files; it establishes expense direction and purpose for the folder and named instructor/sticker payments.');
def footer(canvas,doc):
 canvas.saveState();canvas.setStrokeColor(colors.HexColor('#CAD3DD'));canvas.line(40,35,A4[0]-40,35);canvas.setFont('DejaVu',7);canvas.setFillColor(colors.HexColor('#526171'));canvas.drawString(40,23,'ANJOMAN | Financial report | 10 October 2026 | Toman');canvas.drawRightString(A4[0]-40,23,str(doc.page));canvas.restoreState()
doc=SimpleDocTemplate(str(O/'Anjoman_Financial_Report.pdf'),pagesize=A4,rightMargin=40,leftMargin=40,topMargin=42,bottomMargin=48,title='Anjoman financial report',author='Anjoman',allowSplitting=True)
doc.build(story,onFirstPage=footer,onLaterPages=footer)
(O/'Anjoman_Financial_Report.md').write_text('\n'.join(md));print('Report built')
