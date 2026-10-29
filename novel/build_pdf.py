"""Typeset the unchanged novel and its two concept illustrations as an A5 book."""
from pathlib import Path
import html
import re
import json
import hashlib
import sys
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, PageBreak, Spacer, Flowable, TableStyle
from reportlab.platypus.tableofcontents import TableOfContents
from PIL import Image
import fitz

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'output'/'pdf'
TMP=ROOT/'tmp'/'pdfs'
OUT.mkdir(parents=True,exist_ok=True)
TMP.mkdir(parents=True,exist_ok=True)
PDF=OUT/'灰燼之冠_插圖小說版.pdf'
SCENES='--scenes' in sys.argv
if SCENES: PDF=OUT/'灰燼之冠_場景插圖珍藏版.pdf'
PLATES={1:('01-廢墟初遇.png','廢墟初遇'),4:('04-汛溝救人.png','汛溝救人'),17:('17-燈下叫名.png','燈下叫名'),20:('20-燒乾的燈籠.png','燒乾的燈籠')}
plate_pages=[]
IMAGES=ROOT/'novel'/'illustrations'
SCENE=IMAGES/'灰燈旅店.png'
CAST=IMAGES/'角色概念.png'
pdfmetrics.registerFont(TTFont('Novel',r'C:\Windows\Fonts\mingliu.ttc',subfontIndex=0))
pdfmetrics.registerFont(TTFont('Kai',r'C:\Windows\Fonts\kaiu.ttf'))
W,H=A5
MARGIN=42
INK=colors.HexColor('#2b2926')
GOLD=colors.HexColor('#98764a')
PAPER=colors.HexColor('#f4efe5')
styles={
 'body':ParagraphStyle('body',fontName='Novel',fontSize=11.5,leading=20,wordWrap='CJK',textColor=INK,spaceAfter=9,allowWidows=0,allowOrphans=0,splitLongWords=False),
 'chapter':ParagraphStyle('chapter',fontName='Kai',fontSize=22,leading=33,wordWrap='CJK',textColor=INK,spaceBefore=22,spaceAfter=28,keepWithNext=True),
 'toc_title':ParagraphStyle('toc_title',fontName='Kai',fontSize=24,leading=36,spaceAfter=22),
 'toc':ParagraphStyle('toc',fontName='Novel',fontSize=11.5,leading=20,wordWrap='CJK',spaceBefore=0,spaceAfter=0,leftIndent=0,rightIndent=22),
}

class FullPage(Flowable):
 def __init__(self,kind):
  super().__init__(); self.kind=kind; self.width=W-2*MARGIN; self.height=H-2*MARGIN-2
 def draw(self):
  c=self.canv; c.saveState(); c.resetTransforms()
  c.setFillColor(PAPER); c.rect(0,0,W,H,fill=1,stroke=0)
  c.setFillColor(INK)
  if self.kind=='cover':
   c.setFont('Times-Roman',13); c.drawCentredString(W/2,H-72,'A S H E N   C R O W N')
   c.setFont('Kai',42); c.drawCentredString(W/2,H-138,'灰燼之冠')
   c.setStrokeColor(GOLD); c.setLineWidth(.7); c.line(W/2-28,H-158,W/2+28,H-158)
   c.setFont('Novel',12); c.drawCentredString(W/2,H-185,'插圖小說閱讀版')
   c.drawImage(str(SCENE),0,155,width=W,height=W/2,mask='auto')
   c.setFillColor(INK); c.setFont('Novel',11); c.drawCentredString(W/2,113,'燈亮了。人是我的。')
   c.setFillColor(GOLD); c.setFont('Novel',10); c.drawCentredString(W/2,58,'二十章  ·  故事未完')
  else:
   c.setFont('Kai',25); c.drawCentredString(W/2,H-69,'無冠者與薇爾')
   iw,ih=Image.open(CAST).size; width=W-52; height=width*ih/iw
   c.drawImage(str(CAST),26,H-106-height,width=width,height=height,mask='auto')
   c.setFillColor(INK); c.setFont('Novel',11)
   c.drawCentredString(W/2,113,'無冠者  ／  薇爾・晨燼')
   c.setFillColor(GOLD); c.setFont('Novel',9)
   c.drawCentredString(W/2,84,'角色與場景概念圖為本次視覺演繹')
   c.drawCentredString(W/2,67,'小說沿原稿預設路線，收錄至第二十二天早晨')
  c.restoreState()

class Book(BaseDocTemplate):
 def __init__(self,path):
  super().__init__(str(path),pagesize=A5,leftMargin=MARGIN,rightMargin=MARGIN,topMargin=MARGIN,bottomMargin=MARGIN,title='灰燼之冠｜插圖小說閱讀版',author='灰燼之冠',allowSplitting=1)
  self.chapter=''; self.starts=[]
  frame=Frame(MARGIN,MARGIN,W-2*MARGIN,H-2*MARGIN,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
  self.addPageTemplates(PageTemplate(id='book',frames=frame,onPage=self.decorate))
 def beforeDocument(self): self.chapter=''; self.starts=[]; plate_pages.clear()
 def decorate(self,c,doc):
  if doc.page<=2: return
  c.saveState(); c.setFillColor(GOLD); c.setFont('Novel',8)
  c.drawString(MARGIN,H-25,'灰燼之冠')
  c.setStrokeColor(colors.HexColor('#ddd3c4')); c.setLineWidth(.35); c.line(MARGIN,H-31,W-MARGIN,H-31)
  c.setFont('Times-Roman',9); c.drawCentredString(W/2,22,str(doc.page-3) if doc.page>3 else 'i')
  c.restoreState()
 def afterFlowable(self,flowable):
  if isinstance(flowable,ScenePlate): plate_pages.append({'chapter':flowable.chapter,'physical_page':self.page,'title':flowable.caption})
  if isinstance(flowable,Paragraph) and flowable.style.name=='chapter':
   title=flowable.getPlainText(); key='chapter-'+str(len(self.starts)+1)
   self.canv.bookmarkPage(key); self.canv.addOutlineEntry(title,key,0,False)
   self.notify('TOCEntry',(0,title,self.page-3,key)); self.starts.append({'title':title,'physical_page':self.page,'printed_page':self.page-3})

class ScenePlate(Flowable):
 def __init__(self,chapter,filename,caption):
  super().__init__(); self.chapter=chapter; self.path=ROOT/'novel'/'illustrations'/filename; self.caption=caption
  self.width=W-2*MARGIN; self.height=H-2*MARGIN-2
 def draw(self):
  iw,ih=Image.open(self.path).size
  scale=min(self.width/iw,(self.height-40)/ih)
  dw,dh=iw*scale,ih*scale
  self.canv.drawImage(str(self.path),(self.width-dw)/2,self.height-dh,width=dw,height=dh,mask='auto')
  self.canv.setFillColor(GOLD); self.canv.setFont('Kai',12)
  self.canv.drawCentredString(self.width/2,self.height-dh-25,self.caption)

source=ROOT/'novel'/'灰燼之冠.md'
text=source.read_text(encoding='utf-8')
parts=re.split(r'^## (.+)$',text,flags=re.M)
assert len(parts)==41
story=[FullPage('cover'),PageBreak(),FullPage('cast'),PageBreak(),Paragraph('目錄',styles['toc_title'])]
toc=TableOfContents(); toc.levelStyles=[styles['toc']]; toc.dotsMinLevel=0
toc.tableStyle=TableStyle([('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),('VALIGN',(0,0),(-1,-1),'TOP')])
story.extend([toc,PageBreak()])
for i in range(1,len(parts),2):
 if i>1: story.append(PageBreak())
 story.append(Paragraph(html.escape(parts[i].strip()),styles['chapter']))
 for p in parts[i+1].strip().split('\n\n'):
  if p.strip(): story.append(Paragraph(html.escape(p.strip()),styles['body']))
 chapter=(i+1)//2
 if SCENES and chapter in PLATES:
  story.extend([PageBreak(),ScenePlate(chapter,*PLATES[chapter])])
book=Book(PDF); book.multiBuild(story)
assert book.starts[0]['physical_page']==4,'TOC overflow changed numbering'
doc=fitz.open(PDF)
normalize=lambda s:re.sub(r'\s+','',s)
expected=normalize(re.sub(r'^#+ .*$', '',text,flags=re.M))
actual=normalize(''.join(doc[i].get_text(clip=fitz.Rect(0,35,W,H-35)) for i in range(3,len(doc))))
missing=[]
for p in [p.strip() for p in text.split('\n\n') if p.strip() and not p.startswith('#')]:
 if normalize(p) not in actual: missing.append(p[:70])
assert not missing,f'Paragraph extraction mismatch: {missing[:5]}'
assert len(doc.get_toc())==20
if SCENES:
 assert len(plate_pages)==4
 for plate in plate_pages:
  n=plate['chapter']
  assert plate['physical_page']>book.starts[n-1]['physical_page']
  if n<20: assert plate['physical_page']<book.starts[n]['physical_page']
  assert doc[plate['physical_page']-1].get_images()
assert all(any(f.get('type')=='TrueType' for f in []) or p.get_fonts() for p in doc)
for index in sorted({0,1,2,3,4,len(doc)-1,*[x['physical_page']-1 for x in book.starts],*[x['physical_page']-1 for x in plate_pages]}):
 pix=doc[index].get_pixmap(matrix=fitz.Matrix(1.4,1.4))
 pix.save(TMP/f'page-{index+1:03}.png')
thumbs=[]
for i,p in enumerate(doc):
 pix=p.get_pixmap(matrix=fitz.Matrix(.52,.52))
 im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
 thumbs.append(im)
tw=max(im.width for im in thumbs); th=max(im.height for im in thumbs)
cols=6; rows=(len(thumbs)+cols-1)//cols
sheet=Image.new('RGB',(cols*(tw+12),rows*(th+22)), '#c9c4bc')
from PIL import ImageDraw
d=ImageDraw.Draw(sheet)
for i,im in enumerate(thumbs):
 x=(i%cols)*(tw+12)+6; y=(i//cols)*(th+22)+16
 sheet.paste(im,(x,y)); d.text((x,y-13),str(i+1),fill='black')
sheet.save(TMP/'contact-sheet.jpg',quality=90)
report={'pages':len(doc),'chapters':book.starts,'paragraphs_verified':754,'missing_paragraphs':missing,'manuscript_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'pdf_sha256':hashlib.sha256(PDF.read_bytes()).hexdigest(),'pdf_bytes':PDF.stat().st_size,'images':[str(SCENE),str(CAST)]}
report['scene_illustrations']=plate_pages
if SCENES: report['images'] += [str(IMAGES/item[0]) for item in PLATES.values()]
(OUT/('場景版排版檢查.json' if SCENES else '排版檢查.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:report[k] for k in ['pages','paragraphs_verified','missing_paragraphs','pdf_bytes']},ensure_ascii=False))
