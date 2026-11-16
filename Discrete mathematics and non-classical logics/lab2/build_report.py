"""Воспроизводимая генерация отчёта, JSON и полных CSV. Нужен reportlab."""
import csv
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

from logic import DOMAINS, analyze, assignment, entail, evaluate, interpretations, parse, table, value
from variants import VARIANTS

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)
FONT_CANDIDATES = ["/System/Library/Fonts/Supplemental/Arial Unicode.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf"]
font_path = next((p for p in FONT_CANDIDATES if Path(p).exists()), None)
if not font_path:
    raise RuntimeError("Укажите в FONT_CANDIDATES путь к Unicode-шрифту с кириллицей")
pdfmetrics.registerFont(TTFont("Body", font_path))
styles = getSampleStyleSheet()
styles.add(ParagraphStyle("BodyRU", fontName="Body", fontSize=10, leading=15, spaceAfter=9))
styles.add(ParagraphStyle("TitleRU", fontName="Body", fontSize=23, leading=30, spaceAfter=22))
styles.add(ParagraphStyle("HeadingRU", fontName="Body", fontSize=16, leading=22, spaceAfter=14, textColor=colors.HexColor("#163b60")))
styles.add(ParagraphStyle("SmallRU", fontName="Body", fontSize=8, leading=11, spaceAfter=6))
story = []
md = []


def paragraph(text, style="BodyRU"):
    story.append(Paragraph(escape(text).replace("\n", "<br/>"), styles[style]))
    md.append(text + "\n")


def grid(rows, widths=None, size=8):
    wrapped = [[Paragraph(escape(str(c)), ParagraphStyle("cell", fontName="Body", fontSize=size, leading=size+3)) for c in row] for row in rows]
    t = Table(wrapped, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e4edf6")), ("VALIGN", (0,0), (-1,-1), "TOP"), ("GRID", (0,0), (-1,-1), .3, colors.HexColor("#c8d3df")), ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f6f8fb")]), ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6), ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4)]))
    story.append(t)
    story.append(Spacer(1, 10))
    for i, row in enumerate(rows):
        md.append("| " + " | ".join(str(x).replace("\n", " ") for x in row) + " |")
        if i == 0:
            md.append("| " + " | ".join("---" for _ in row) + " |")
    md.append("")


def page():
    story.append(PageBreak())


def csv_write(path, headers, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)


yes = lambda x: "да" if x else "нет"
paragraph("Лабораторная работа № 2", "TitleRU")
paragraph("Интерпретатор многозначных логик и проверка семантических свойств формул", "HeadingRU")
paragraph("Реализация на Python 3.10+. Вариант № 1.")
paragraph("1. Цель и состав работы", "HeadingRU")
paragraph("Разработана программная система для классической логики (CL), сильной трёхзначной логики Клини (K3) и трёхзначной логики Лукасевича (L3). Реализованы проверка синтаксиса, построение дерева формулы, вычисление по оценке, полный перебор интерпретаций, проверка семантических свойств и логического следования, сравнение систем.")
paragraph("Программа logic.py работает в интерактивном режиме и через аргументы командной строки. variants.py содержит исходные примеры: 5 формул и 4 отношения следования первого варианта. В results находятся полные таблицы: 15 CSV для формул, 12 CSV для отношений и сводный JSON.")
paragraph("Выполнен вариант № 1.")
paragraph("2. Синтаксис и алгоритм", "HeadingRU")
paragraph("Переменные: латинская буква или _, далее буквы, цифры и _. Символ f обозначает константу ложности, как в ЛР1. Операции: ¬, ∧, ∨, →; ASCII-аналоги: ~ или !, &, |, ->. Приоритет: ¬ > ∧ > ∨ > →. Импликация ассоциируется влево, как в ЛР1: p→q→r означает (p→q)→r. Скобки меняют порядок вычисления.")
paragraph("Повторно использован анализатор formulas.py из ЛР1: Atom, Implication, primary/expression, NFKC, обозначение ⊃, константа f и левая ассоциативность импликации. Добавлены узлы Negation, Conjunction, Disjunction и уровни приоритета. Адаптер logic.parse преобразует дерево анализатора в вычислительное дерево Node. Узел хранит переменную либо операцию и потомков. При неверном синтаксисе выводится позиция ошибки. Исполнение текста формулы средствами eval не используется.")
paragraph("Для n различных переменных и k значений перебираются kⁿ оценок. При длине дерева m вычисление таблицы требует O(m·kⁿ) времени; хранение таблицы требует O(n·kⁿ) памяти. Следование проверяется поточно, хранится только первый контрпример. Предел: 100 000 оценок; 400 лексем и глубина вложенности до 100.")
page()
paragraph("3. Семантика логических систем", "HeadingRU")
paragraph("Области значений: CL = {0, 1}; K3 = L3 = {0, ½, 1}. Выделенное значение во всех системах только 1. Внутреннее представление 0, 1, 2 масштабировано вдвое: оно соответствует 0, ½, 1 и исключает ошибки округления.")
paragraph("¬a = 1 − a; a ∧ b = min(a,b); a ∨ b = max(a,b). В CL и K3: a → b = max(1 − a,b). В L3: a → b = min(1,1 − a + b).")
grid([["a", "b", "a → b в K3", "a → b в L3"]] + [[value(a), value(b), value(evaluate(parse("p->q"), {"p":a,"q":b}, "K3")), value(evaluate(parse("p->q"), {"p":a,"q":b}, "L3"))] for a in (0,1,2) for b in (0,1,2)], [55,55,190,190])
paragraph("Общезначимость: F=1 на всех оценках. Выполнимость: F=1 хотя бы на одной оценке. Невыполнимость: ни одной оценки со значением 1. Тождественная ложность: F=0 на каждой оценке. Контрпример общезначимости имеет F≠1, включая ½.")
paragraph("Γ ⊨ B тогда и только тогда, когда не существует оценки, где все посылки равны 1, а B≠1. Если совместных моделей посылок нет, следование истинно вакуозно; программа сообщает об этом отдельно. Пустое множество посылок сводит проверку к общезначимости заключения.")
paragraph("Пример различия: p→q при p=q=½ даёт ½ в K3 и 1 в L3. Формула p∧¬p невыполнима во всех трёх системах; тождественно ложна только в CL.")
page()

summary = {"encoding": "Internal truth values: 0=false, 1=half, 2=true; CSV and report use 0, 1/2, 1", "variants": {}}
for number, v in VARIANTS.items():
    target = OUT / f"variant_{number}"
    target.mkdir(exist_ok=True)
    data = {"formulas": [], "relations": []}
    summary["variants"][number] = data
    paragraph(f"Вариант {number}. Исследование формул", "HeadingRU")
    nodes = [parse(s) for s in v["formulas"]]
    for i, n in enumerate(nodes, 1):
        paragraph(f"F{i} = {n}")
    rows = [["Формула", "Логика", "Общезн.", "Выполн.", "Тожд. 0", "Число оценок 0 / ½ / 1"]]
    for i, n in enumerate(nodes, 1):
        item = {"id": f"F{i}", "formula": str(n), "systems": {}}
        data["formulas"].append(item)
        for s in DOMAINS:
            a = analyze(n, s)
            item["systems"][s] = a
            rows.append([f"F{i}", s, yes(a["valid"]), yes(a["satisfiable"]), yes(a["identically_false"]), " / ".join(str(a["counts"].get(k, 0)) for k in ("0", "1/2", "1"))])
            names, vals = table(n, s)
            csv_write(target / f"F{i}_{s}.csv", [*names, "F"], [[*(value(env[k]) for k in names), value(x)] for env, x in vals])
    grid(rows, [48,48,68,65,65,196])
    paragraph("Выполнимость понимается строго как достижение 1. В столбце «Тожд. 0» проверяется равенство нулю на всех оценках. Число оценок ½ для CL равно нулю, поскольку это значение отсутствует в области CL.", "SmallRU")
    for i, n in enumerate(nodes, 1):
        parts = []
        for s in DOMAINS:
            a = analyze(n, s)
            if a["counterexample"] is not None:
                e = a["counterexample"]
                parts.append(f"{s}: {assignment(e)}, F={value(evaluate(n,e,s))}")
        if parts:
            paragraph(f"F{i}, контрпримеры общезначимости: " + "; ".join(parts), "SmallRU")
    page()
    paragraph(f"Вариант {number}. Логическое следование", "HeadingRU")
    for i, (psrc, csrc) in enumerate(v["relations"], 1):
        ps, c = [parse(s) for s in psrc], parse(csrc)
        paragraph(f"R{i}: " + ", ".join(map(str, ps)) + " ⊨ " + str(c))
        rel = {"id": f"R{i}", "premises": list(map(str, ps)), "conclusion": str(c), "systems": {}}
        data["relations"].append(rel)
        for s in DOMAINS:
            r = entail(ps, c, s)
            rel["systems"][s] = r
            text = f"{s}: следование {'выполняется' if r['entails'] else 'не выполняется'}. Моделей посылок {r['premise_models']} из {r['interpretations']}."
            if not r["premises_satisfiable"]:
                text += " Посылки совместно невыполнимы; следование вакуозно."
            if r["counterexample"]:
                counter = r["counterexample"]
                text += f" Контрпример: {assignment(counter['assignment'])}. Посылки: " + ", ".join(map(value, counter["premises"])) + f"; заключение: {value(counter['conclusion'])}."
            paragraph(text, "SmallRU")
            names = sorted(set().union(c.variables(), *(p.variables() for p in ps)))
            csv_rows = []
            for e in interpretations(names, s):
                vs = [evaluate(p,e,s) for p in ps]
                cv = evaluate(c,e,s)
                csv_rows.append([*(value(e[k]) for k in names), *map(value,vs), value(cv), int(all(x==2 for x in vs)), int(all(x==2 for x in vs) and cv!=2)])
            csv_write(target / f"R{i}_{s}.csv", [*names, *(f"A{j}" for j in range(1,len(ps)+1)), "B", "premise_model", "counterexample"], csv_rows)
    paragraph("Значения посылок в контрпримерах перечислены в исходном порядке. В полных CSV сохранены все оценки, значения каждой посылки и заключения, а также признаки модели посылок и контрпримера.", "SmallRU")
    page()
    paragraph(f"Вариант {number}. Сравнительная таблица", "HeadingRU")
    names = sorted(set().union(*(n.variables() for n in nodes)))
    paragraph("В каждой ячейке F указаны значения CL / K3 / L3 в этом порядке. Знак «-» означает: общая оценка содержит ½ и не принадлежит классической области. Полные таблицы каждой отдельной формулы без избыточных переменных сохранены в CSV.", "SmallRU")
    rows = [[*names, *(f"F{i}\nCL / K3 / L3" for i in range(1,6))]]
    for env in interpretations(names, "K3"):
        cells = []
        for n in nodes:
            cells.append(" / ".join(value(evaluate(n,env,s)) if all(x in DOMAINS[s] for x in env.values()) else "-" for s in DOMAINS))
        rows.append([*(value(env[k]) for k in names), *cells])
    grid(rows, [24]*len(names) + [(490-24*len(names))/5]*5, size=7)
    paragraph("На общей двузначной области значения CL, K3 и L3 совпадают для всех формул: семантика операций на 0 и 1 одинакова. Отличия между K3 и L3 возникают из-за импликации на промежуточных значениях; семантические свойства зависят также от области допустимых оценок.", "SmallRU")

paragraph("Вывод", "HeadingRU")
paragraph("Программа реализует оба сценария задания. Полный перебор даёт проверяемые результаты для каждой системы. Различия логик проявляются и в значениях формул, и в общезначимости, и в следовании; невыполнимость не подменяется тождественной ложностью.", "SmallRU")


def footer(canvas, doc):
    canvas.setFont("Body", 8)
    canvas.setFillColor(colors.HexColor("#526478"))
    canvas.drawString(42, 25, "ЛР2 · Интерпретатор многозначных логик")
    canvas.drawRightString(A4[0]-42, 25, str(doc.page))


doc = SimpleDocTemplate(str(OUT / "report.pdf"), pagesize=A4, rightMargin=42, leftMargin=42, topMargin=36, bottomMargin=42, title="Лабораторная работа №2: многозначные логики", author="")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
(OUT / "report.md").write_text("\n".join(md), encoding="utf-8")
(OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print("Готово: report.pdf, report.md, summary.json и 27 CSV в", OUT)
