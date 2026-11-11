"""Portable Markdown subset to PDF. No external TeX or proprietary tools required."""
from pathlib import Path
import re
from html import escape
import matplotlib
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate,Paragraph,Spacer,PageBreak,Image,Table,TableStyle,
                               Preformatted,KeepTogether)
from reportlab.platypus.tableofcontents import TableOfContents

class ReportDoc(SimpleDocTemplate):
    def afterFlowable(self,flowable):
        if isinstance(flowable,Paragraph) and flowable.style.name=='Heading1':
            self.notify('TOCEntry',(0,flowable.getPlainText(),self.page))

def create_pdf(root,files):
    fonts=Path(matplotlib.get_data_path())/'fonts'/'ttf'
    for name,file in [('Body','DejaVuSerif.ttf'),('BodyBold','DejaVuSerif-Bold.ttf'),
                      ('Sans','DejaVuSans.ttf'),('SansBold','DejaVuSans-Bold.ttf'),('Mono','DejaVuSansMono.ttf')]:
        if name not in pdfmetrics.getRegisteredFontNames(): pdfmetrics.registerFont(TTFont(name,str(fonts/file)))
    pdfmetrics.registerFontFamily('Body',normal='Body',bold='BodyBold',italic='Body',boldItalic='BodyBold')
    st=getSampleStyleSheet()
    for key in ['BodyText','Normal']:
        st[key].fontName='Body'; st[key].fontSize=10.5; st[key].leading=15; st[key].spaceAfter=7
    st['BodyText'].alignment=TA_JUSTIFY
    for key,size in [('Title',22),('Heading1',18),('Heading2',13)]:
        st[key].fontName='SansBold';st[key].fontSize=size;st[key].leading=size*1.35
        st[key].textColor=colors.black;st[key].spaceAfter=10;st[key].spaceBefore=12
        st[key].keepWithNext=True
    st.add(ParagraphStyle('Cell',fontName='Sans',fontSize=8.1,leading=11,spaceAfter=0))
    st.add(ParagraphStyle('CellHead',fontName='SansBold',fontSize=8.1,leading=11))
    st.add(ParagraphStyle('Formula',fontName='Mono',fontSize=8.2,leading=12,spaceBefore=6,spaceAfter=9))
    st.add(ParagraphStyle('CaptionSmall',fontName='Sans',fontSize=9,leading=12,spaceAfter=10))
    width=A4[0]-36*mm
    doc=ReportDoc(str(root/'report.pdf'),pagesize=A4,leftMargin=18*mm,rightMargin=18*mm,
                  topMargin=17*mm,bottomMargin=18*mm,title='Методы оптимизации Вариант 13',
                  author='Кртян Левон',subject='ЛР 1 2 3 и задания со звёздочкой 10 и 6')
    story=[Spacer(1,14*mm),Paragraph('Методы оптимизации',st['Title']),
           Paragraph('Комплекс лабораторных работ<br/>Вариант 13',st['Heading2']),
           Spacer(1,7*mm),Paragraph('Кртян Левон<br/>Группа Б24-517<br/>2026 год',st['BodyText']),
           Paragraph('Индивидуализация',st['Heading2']),
           Paragraph('N = 7, Q = 1, Y = 26<br/>V = 1 + ((17N + 7Q + Y) mod 20) = 13<br/>seed = 10000 + 100Q + N = 10107',st['BodyText']),
           Paragraph('Три работы и два задания со звёздочкой',st['Heading2']),
           Paragraph('Непрерывная модель кредитования; календарные перевозки с запасами; выбор поставщиков с объёмными скидками. Дополнения: полная двойственная задача (№ 10) и сравнение двух MILP формулировок (№ 6).',st['BodyText']),
           Paragraph('Содержание',st['Heading2'])]
    toc=TableOfContents();toc.levelStyles=[ParagraphStyle('TOC',fontName='Body',fontSize=10.5,leading=17,spaceAfter=3)]
    story.append(toc)
    story.extend([Spacer(1,9*mm),Paragraph('Основание',st['Heading2']),Paragraph('Кузьмин А. А. «Методы оптимизации. Линейное программирование». Комплекс лабораторных работ, 14 страниц. Масштаб, состав экспериментов и задания со звёздочкой выбраны по этому материалу.',st['BodyText'])])

    def inline(s):
        s=escape(s)
        return re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)

    def table(lines):
        data=[[x.strip() for x in line.strip().strip('|').split('|')] for line in lines]
        data=[data[0]]+data[2:]
        cols=len(data[0]); weights=[]
        for j in range(cols):
            length=max(len(row[j]) for row in data)
            weights.append(min(24,max(7,length*.7)))
        total=sum(weights); widths=[width*w/total for w in weights]
        cells=[[Paragraph(inline(v),st['CellHead'] if i==0 else st['Cell']) for v in row] for i,row in enumerate(data)]
        t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6edf0')),
              ('GRID',(0,0),(-1,-1),.4,colors.HexColor('#D9D9D9')),
              ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),5),
              ('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),
              ('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        return t

    for filename in files:
        story.append(PageBreak())
        lines=(root/'reports'/filename).read_text(encoding='utf-8').splitlines();i=0
        while i<len(lines):
            s=lines[i].strip()
            if not s:i+=1;continue
            if s.startswith('# '):story.append(Paragraph(inline(s[2:]),st['Heading1']));i+=1
            elif s.startswith('## '):story.append(Paragraph(inline(s[3:]),st['Heading2']));i+=1
            elif s.startswith('```'):
                code=[];i+=1
                while i<len(lines) and not lines[i].startswith('```'):code.append(lines[i]);i+=1
                story.append(KeepTogether([Preformatted('\n'.join(code),st['Formula'],maxLineLength=93)]));i+=1
            elif s.startswith('|'):
                rows=[]
                while i<len(lines) and lines[i].strip().startswith('|'):rows.append(lines[i]);i+=1
                t=table(rows)
                story.append(KeepTogether([t]) if len(rows)<=14 else t);story.append(Spacer(1,8))
            elif s.startswith('!['):
                match=re.match(r'!\[(.*?)\]\((.*?)\)',s)
                from PIL import Image as PILImage
                img=root/'reports'/match.group(2);w,h=PILImage.open(img).size
                hpt=width*h/w
                story.append(KeepTogether([Image(str(img),width=width,height=hpt),Paragraph(inline(match.group(1)),st['CaptionSmall'])]));i+=1
            else:
                parts=[s];i+=1
                while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','```','|','![')):
                    parts.append(lines[i].strip());i+=1
                story.append(Paragraph(inline(' '.join(parts)),st['BodyText']))
    story.append(PageBreak());story.append(Paragraph('Источники и воспроизводимость',st['Heading1']))
    for txt in [
        'Исходное задание: Кузьмин А. А. «Методы оптимизации. Линейное программирование». Общие требования - с. 1-3; ЛР 1 - с. 4-6; ЛР 2 - с. 7-9; ЛР 3 - с. 10-12; задания со звёздочкой - с. 13; вопросы к защите - с. 14.',
        'Интерфейс HiGHS проверен по официальной документации: https://ergo-code.github.io/HiGHS/stable/interfaces/python/example-py/ . Использованы HighsLp, passModel, run, getSolution, getInfo и встроенное сохранение логов. Никакие численные результаты не взяты из документации: все получены кодом этого комплекта.',
        'Основная команда: python main.py --generate . Отдельная повторная проверка сохранённых планов: python check_results.py . Данные хранятся в data/, исходный код в src/, протоколы и таблицы в results/, редактируемые отчёты в reports/.',
        'Версии фактического расчёта: Python 3.12.14, NumPy 2.3.5, HiGHS 1.15.1, Matplotlib 3.11.2, ReportLab 4.4.9. Прямые версии зафиксированы в requirements.txt, полное окружение вычислительного комплекта - в requirements-lock.txt. Аппаратная среда указана в results/environment.json.',
        'Данные синтетические и воспроизводимые. Качество формализации и численная оптимальность не означают достоверности модели реального банка, логистической сети или поставщика. Для оценки A методический материал также требует успешной защиты всех трёх работ и не менее двух заданий со звёздочкой до зачётной недели.'
    ]:story.append(Paragraph(inline(txt),st['BodyText']))
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont('Sans',8);canvas.setFillColor(colors.HexColor('#555555'))
        canvas.drawString(18*mm,10*mm,'Кртян Левон  |  Б24-517  |  Вариант 13')
        canvas.drawRightString(A4[0]-18*mm,10*mm,str(doc.page));canvas.restoreState()
    doc.multiBuild(story,onFirstPage=footer,onLaterPages=footer)
