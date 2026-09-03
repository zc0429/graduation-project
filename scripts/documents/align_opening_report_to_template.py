#!/usr/bin/env python3
"""Rebuild the current opening-report DOCX with the reference PDF's page frames."""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_ROW_HEIGHT_RULE, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "output"
    / "backup"
    / "2026-09-03-before-template-align"
    / "云南工商学院毕业设计开题报告-赵灿-修改前.docx"
)
OUTPUT = ROOT / "output" / "docx" / "云南工商学院毕业设计开题报告-赵灿.docx"

PAGE_WIDTH_CM = 21.0
PAGE_HEIGHT_CM = 29.7
# WPS adds a small positioning offset when exporting tables. These margins were
# calibrated against the reference PDF so the rendered frame lands at x≈61.8/533.8 pt.
LEFT_MARGIN_CM = 2.33
RIGHT_MARGIN_CM = 2.02
TOP_MARGIN_CM = 2.50
BOTTOM_MARGIN_CM = 2.50
FRAME_WIDTH_CM = PAGE_WIDTH_CM - LEFT_MARGIN_CM - RIGHT_MARGIN_CM

BODY_SIZE = 10.5
BODY_LINE_PT = 18.0
FIRST_LINE_PT = 21.0
BORDER_SIZE = "4"  # OOXML eighths of a point: 0.5 pt


def set_table_layout(table, widths_cm: list[float]) -> None:
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.autofit = False
    table.allow_autofit = False
    table.width = Cm(sum(widths_cm))
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:type"), "dxa")
    tbl_w.set(qn("w:w"), str(round(sum(widths_cm) / 2.54 * 1440)))
    tbl_ind = tbl_pr.find(qn("w:tblInd"))
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:type"), "dxa")
    tbl_ind.set(qn("w:w"), "0")
    layout = tbl_pr.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tbl_pr.append(layout)
    layout.set(qn("w:type"), "fixed")
    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths_cm:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(round(width / 2.54 * 1440)))
        grid.append(col)
    for row in table.rows:
        tr_pr = row._tr.get_or_add_trPr()
        if tr_pr.find(qn("w:cantSplit")) is None:
            tr_pr.append(OxmlElement("w:cantSplit"))
        for idx, cell in enumerate(row.cells):
            width = widths_cm[min(idx, len(widths_cm) - 1)]
            cell.width = Cm(width)
            tc_w = cell._tc.get_or_add_tcPr().find(qn("w:tcW"))
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                cell._tc.get_or_add_tcPr().append(tc_w)
            tc_w.set(qn("w:type"), "dxa")
            tc_w.set(qn("w:w"), str(round(width / 2.54 * 1440)))


def set_table_borders(table, *, enabled: bool) -> None:
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.find(qn("w:tblBorders"))
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = borders.find(qn(f"w:{edge}"))
        if tag is None:
            tag = OxmlElement(f"w:{edge}")
            borders.append(tag)
        tag.set(qn("w:val"), "single" if enabled else "nil")
        tag.set(qn("w:sz"), BORDER_SIZE)
        tag.set(qn("w:space"), "0")
        tag.set(qn("w:color"), "000000")


def set_cell_margins(cell, top: int = 28, start: int = 85, bottom: int = 28, end: int = 85) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.find(qn("w:tcMar"))
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for name, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{name}"))
        if node is None:
            node = OxmlElement(f"w:{name}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_cell_width(cell, width_cm: float) -> None:
    cell.width = Cm(width_cm)
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW"))
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:type"), "dxa")
    tc_w.set(qn("w:w"), str(round(width_cm / 2.54 * 1440)))


def clear_cell(cell) -> None:
    cell.text = ""
    cell.paragraphs[0].clear()


def set_run_font(
    run,
    *,
    east_asia: str = "宋体",
    latin: str = "Times New Roman",
    size: float = BODY_SIZE,
    bold: bool = False,
) -> None:
    run.font.name = latin
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.superscript = False
    r_pr = run._element.get_or_add_rPr()
    r_fonts = r_pr.rFonts
    if r_fonts is None:
        r_fonts = OxmlElement("w:rFonts")
        r_pr.insert(0, r_fonts)
    r_fonts.set(qn("w:ascii"), latin)
    r_fonts.set(qn("w:hAnsi"), latin)
    r_fonts.set(qn("w:eastAsia"), east_asia)
    r_fonts.set(qn("w:cs"), latin)


def set_paragraph_common(
    paragraph,
    *,
    align=WD_ALIGN_PARAGRAPH.JUSTIFY,
    first_line_pt: float = 0,
    left_pt: float = 0,
    line_pt: float = BODY_LINE_PT,
) -> None:
    paragraph.alignment = align
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(0)
    fmt.space_after = Pt(0)
    fmt.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    fmt.line_spacing = Pt(line_pt)
    fmt.left_indent = Pt(left_pt)
    fmt.right_indent = Pt(0)
    fmt.first_line_indent = Pt(first_line_pt)
    fmt.keep_together = False
    fmt.keep_with_next = False
    fmt.widow_control = False


def next_paragraph(cell):
    if len(cell.paragraphs) == 1 and not cell.paragraphs[0].text and not cell.paragraphs[0].runs:
        return cell.paragraphs[0]
    return cell.add_paragraph()


def add_paragraph(cell, text: str, *, role: str = "body", align=None) -> None:
    paragraph = next_paragraph(cell)
    if role == "field":
        set_paragraph_common(paragraph, align=align or WD_ALIGN_PARAGRAPH.CENTER, line_pt=16)
    elif role == "reference":
        set_paragraph_common(paragraph, align=WD_ALIGN_PARAGRAPH.LEFT, first_line_pt=FIRST_LINE_PT)
    elif role == "signature":
        set_paragraph_common(paragraph, align=align or WD_ALIGN_PARAGRAPH.LEFT)
    elif role == "body":
        set_paragraph_common(paragraph, align=align or WD_ALIGN_PARAGRAPH.JUSTIFY, first_line_pt=FIRST_LINE_PT)
    elif role == "sub":
        set_paragraph_common(paragraph, align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_line_pt=FIRST_LINE_PT)
    else:
        set_paragraph_common(paragraph, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    run = paragraph.add_run(text)
    set_run_font(run, size=BODY_SIZE, bold=False)


def add_empty_line(cell) -> None:
    paragraph = next_paragraph(cell)
    set_paragraph_common(paragraph, align=WD_ALIGN_PARAGRAPH.LEFT)
    run = paragraph.add_run("　")
    set_run_font(run)


def add_page_break(document: Document) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    paragraph.paragraph_format.line_spacing = Pt(1)
    run = paragraph.add_run()
    run.font.size = Pt(1)
    run.add_break(WD_BREAK.PAGE)


def style_all_cells(table) -> None:
    for row in table.rows:
        tr_pr = row._tr.get_or_add_trPr()
        if tr_pr.find(qn("w:cantSplit")) is None:
            tr_pr.append(OxmlElement("w:cantSplit"))
        for cell in row.cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)


def set_row_height(row, cm_value: float, *, exact: bool = False) -> None:
    row.height = Cm(cm_value)
    row.height_rule = WD_ROW_HEIGHT_RULE.EXACTLY if exact else WD_ROW_HEIGHT_RULE.AT_LEAST


def add_single_column_page(document: Document, groups: list[list[tuple[str, str]]]):
    table = document.add_table(rows=len(groups), cols=1)
    set_table_layout(table, [FRAME_WIDTH_CM])
    set_table_borders(table, enabled=True)
    style_all_cells(table)
    for row, group in zip(table.rows, groups):
        clear_cell(row.cells[0])
        row.cells[0].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
        for text, role in group:
            add_paragraph(row.cells[0], text, role=role)
    return table


def transformed_function(text: str) -> str:
    text = re.sub(r"^\d+\.\s*", "", text)
    return text.replace("**", "").replace("`", "")


def transformed_progress(text: str) -> str:
    return re.sub(r"^(\d+)\.\s*", lambda m: f"{m.group(1)}．", text)


def transformed_reference(text: str) -> str:
    return re.sub(r"^(\[\d+\])[\t ]+", r"\1", text)


def extract_unique_row_text(table, row_index: int) -> str:
    row = table.rows[row_index]
    seen = set()
    texts = []
    for cell in row.cells:
        key = id(cell._tc)
        if key in seen:
            continue
        seen.add(key)
        texts.append("\n".join(p.text for p in cell.paragraphs).rstrip("\n"))
    return texts[-1] if len(texts) == 1 else " | ".join(texts)


def build() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    source_doc = Document(SOURCE)
    source_top = source_doc.tables[0]
    source_main = source_doc.tables[1]
    row_text = {idx: extract_unique_row_text(source_main, idx) for idx in range(len(source_main.rows))}
    if len(source_main.rows) != 83:
        raise ValueError(f"Unexpected source table shape: {len(source_main.rows)} rows")
    top_values = [cell.text for cell in source_top.rows[0].cells]
    identity_values = [cell.text for cell in source_main.rows[0].cells]
    title_values = []
    seen = set()
    for cell in source_main.rows[1].cells:
        if id(cell._tc) not in seen:
            seen.add(id(cell._tc))
            title_values.append(cell.text)

    document = Document()
    section = document.sections[0]
    section.page_width = Cm(PAGE_WIDTH_CM)
    section.page_height = Cm(PAGE_HEIGHT_CM)
    section.top_margin = Cm(TOP_MARGIN_CM)
    section.bottom_margin = Cm(BOTTOM_MARGIN_CM)
    section.left_margin = Cm(LEFT_MARGIN_CM)
    section.right_margin = Cm(RIGHT_MARGIN_CM)
    section.header_distance = Cm(1.5)
    section.footer_distance = Cm(1.5)
    normal = document.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(BODY_SIZE)
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")

    school = document.add_paragraph()
    set_paragraph_common(school, align=WD_ALIGN_PARAGRAPH.CENTER, line_pt=18)
    school.paragraph_format.space_after = Pt(10)
    run = school.add_run(source_doc.paragraphs[0].text)
    set_run_font(run, east_asia="宋体", latin="宋体", size=12, bold=True)
    report_title = document.add_paragraph()
    set_paragraph_common(report_title, align=WD_ALIGN_PARAGRAPH.CENTER, line_pt=20)
    report_title.paragraph_format.space_after = Pt(12)
    run = report_title.add_run(source_doc.paragraphs[1].text)
    set_run_font(run, east_asia="黑体", latin="黑体", size=16, bold=True)

    top_table = document.add_table(rows=1, cols=4)
    top_widths = [2.5, 4.1, 2.7, 7.35]
    set_table_layout(top_table, top_widths)
    set_table_borders(top_table, enabled=False)
    for index, cell in enumerate(top_table.rows[0].cells):
        clear_cell(cell)
        set_cell_margins(cell, top=0, bottom=0, start=0, end=0)
        add_paragraph(cell, top_values[index], role="field", align=WD_ALIGN_PARAGRAPH.LEFT if index in {0, 2} else WD_ALIGN_PARAGRAPH.CENTER)
    set_row_height(top_table.rows[0], 0.65)
    spacer = document.add_paragraph()
    set_paragraph_common(spacer, align=WD_ALIGN_PARAGRAPH.LEFT, line_pt=22)

    page1 = document.add_table(rows=4, cols=6)
    page1_widths = [2.52, 2.88, 2.05, 3.31, 1.95, 3.94]
    set_table_layout(page1, page1_widths)
    set_table_borders(page1, enabled=True)
    style_all_cells(page1)
    for cell, text in zip(page1.rows[0].cells, identity_values):
        clear_cell(cell)
        add_paragraph(cell, text, role="field")
    set_row_height(page1.rows[0], 0.78)
    title_label = page1.rows[1].cells[0]
    title_content = page1.rows[1].cells[1].merge(page1.rows[1].cells[-1])
    clear_cell(title_label)
    clear_cell(title_content)
    add_paragraph(title_label, title_values[0], role="field")
    add_paragraph(title_content, title_values[1], role="field")
    set_cell_width(title_label, page1_widths[0])
    set_cell_width(title_content, sum(page1_widths[1:]))
    set_row_height(page1.rows[1], 1.10)
    section1 = page1.rows[2].cells[0].merge(page1.rows[2].cells[-1])
    clear_cell(section1)
    section1.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
    for idx, role in ((2, "main"), (4, "sub"), (5, "body"), (6, "sub"), (7, "body"), (9, "body")):
        add_paragraph(section1, row_text[idx], role=role)
    literature_intro = page1.rows[3].cells[0].merge(page1.rows[3].cells[-1])
    clear_cell(literature_intro)
    literature_intro.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
    for idx, role in ((10, "main"), (11, "sub"), (12, "body")):
        add_paragraph(literature_intro, row_text[idx], role=role)
    set_row_height(page1.rows[3], 5.45)

    add_page_break(document)
    page2_group = [(row_text[idx], "sub" if idx in {13, 17} else "body") for idx in range(13, 21)]
    page2 = add_single_column_page(document, [page2_group])
    set_row_height(page2.rows[0], 24.10)

    add_page_break(document)
    page3_summary = [(row_text[21], "sub"), (row_text[22], "body")]
    page3_research = [(row_text[23], "main")]
    for idx in range(24, 37):
        text = transformed_function(row_text[idx]) if idx >= 31 else row_text[idx]
        page3_research.append((text, "sub" if idx in {24, 29} else "body"))
    page3 = add_single_column_page(document, [page3_summary, page3_research])
    set_row_height(page3.rows[0], 4.30)
    set_row_height(page3.rows[1], 19.80)

    add_page_break(document)
    page4_research = []
    for idx in range(37, 47):
        text = transformed_function(row_text[idx]) if idx <= 43 else row_text[idx]
        page4_research.append((text, "sub" if idx == 44 else "body"))
    page4_methods = [(row_text[47], "main")]
    for idx in range(48, 52):
        page4_methods.append((row_text[idx], "sub" if idx in {48, 50} else "body"))
    page4 = add_single_column_page(document, [page4_research, page4_methods])
    set_row_height(page4.rows[0], 13.50)
    set_row_height(page4.rows[1], 10.60)

    add_page_break(document)
    page5_methods = [(row_text[52], "sub"), (row_text[53], "body")]
    page5_plan = [(row_text[54], "main")]
    page5_plan.extend((transformed_progress(row_text[idx]), "body") for idx in range(55, 60))
    page5_refs = [(row_text[60], "main")]
    page5_refs.extend((transformed_reference(row_text[idx]), "reference") for idx in range(61, 68))
    page5 = add_single_column_page(document, [page5_methods, page5_plan, page5_refs])
    set_row_height(page5.rows[0], 6.50)
    set_row_height(page5.rows[1], 3.00)
    set_row_height(page5.rows[2], 13.62)

    add_page_break(document)
    page6 = document.add_table(rows=3, cols=2)
    page6_widths = [1.0, 15.65]
    set_table_layout(page6, page6_widths)
    set_table_borders(page6, enabled=True)
    style_all_cells(page6)
    refs_cell = page6.rows[0].cells[0].merge(page6.rows[0].cells[1])
    clear_cell(refs_cell)
    refs_cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
    for idx in range(68, 81):
        add_paragraph(refs_cell, transformed_reference(row_text[idx]), role="reference")
    for row_index, source_row_index, label in ((1, 81, "指\n导\n教\n师\n意\n见"), (2, 82, "系\n意\n见")):
        label_cell, content_cell = page6.rows[row_index].cells
        clear_cell(label_cell)
        clear_cell(content_cell)
        label_cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        content_cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_margins(label_cell, start=0, end=0)
        p = label_cell.paragraphs[0]
        set_paragraph_common(p, align=WD_ALIGN_PARAGRAPH.CENTER)
        run = p.add_run(label)
        set_run_font(run)
        source_content = source_main.rows[source_row_index].cells[-1]
        review_text = source_content.paragraphs[0].text.split("\n", 1)[0]
        signature_text = source_content.paragraphs[-1].text
        add_paragraph(content_cell, review_text, role="signature")
        add_empty_line(content_cell)
        add_empty_line(content_cell)
        add_paragraph(content_cell, signature_text, role="signature")
    set_row_height(page6.rows[1], 3.75, exact=True)
    set_row_height(page6.rows[2], 3.15, exact=True)

    document.core_properties.title = "云南工商学院毕业设计开题报告"
    document.core_properties.subject = "赵灿毕业设计开题报告"
    document.core_properties.author = "赵灿"
    document.core_properties.keywords = "开题报告；错题分析；个性化推荐；检索增强生成；知识追踪"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()
