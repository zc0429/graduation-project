#!/usr/bin/env python3
"""Rebuild the opening-report DOCX with the official 2027 template's page frames."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_ROW_HEIGHT_RULE, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "tmp" / "opening-report-build" / "base.docx"
DEFAULT_OUTPUT = ROOT / "output" / "docx" / "云南工商学院毕业设计开题报告-赵灿.docx"
OFFICIAL_TEMPLATE = (
    ROOT
    / "docs"
    / "materials"
    / "27届毕业设计学校通知和模板"
    / "附件3：毕业论文（设计）相关模板（2027）"
    / "附件3：毕业论文（设计）内容资料.docx"
)

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


def reorder_ooxml_properties(document: Document) -> None:
    table_order = {
        "tblStyle": 0,
        "tblpPr": 1,
        "tblOverlap": 2,
        "bidiVisual": 3,
        "tblStyleRowBandSize": 4,
        "tblStyleColBandSize": 5,
        "tblW": 6,
        "jc": 7,
        "tblCellSpacing": 8,
        "tblInd": 9,
        "tblBorders": 10,
        "shd": 11,
        "tblLayout": 12,
        "tblCellMar": 13,
        "tblLook": 14,
        "tblCaption": 15,
        "tblDescription": 16,
        "tblPrChange": 17,
    }
    cell_order = {
        "cnfStyle": 0,
        "tcW": 1,
        "gridSpan": 2,
        "hMerge": 3,
        "vMerge": 4,
        "tcBorders": 5,
        "shd": 6,
        "noWrap": 7,
        "tcMar": 8,
        "textDirection": 9,
        "tcFitText": 10,
        "vAlign": 11,
        "hideMark": 12,
        "cellIns": 13,
        "cellDel": 14,
        "cellMerge": 15,
    }

    def reorder(parent, order):
        children = sorted(list(parent), key=lambda child: order.get(child.tag.rsplit("}", 1)[-1], 100))
        for child in list(parent):
            parent.remove(child)
        for child in children:
            parent.append(child)

    for table_properties in document._element.iter(qn("w:tblPr")):
        reorder(table_properties, table_order)
    for cell_properties in document._element.iter(qn("w:tcPr")):
        reorder(cell_properties, cell_order)


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
        font_size = BODY_SIZE
    elif role == "top_field":
        set_paragraph_common(paragraph, align=align or WD_ALIGN_PARAGRAPH.CENTER, line_pt=18)
        font_size = 12
    elif role == "reference":
        set_paragraph_common(paragraph, align=WD_ALIGN_PARAGRAPH.LEFT)
        font_size = BODY_SIZE
    elif role == "signature":
        set_paragraph_common(paragraph, align=align or WD_ALIGN_PARAGRAPH.LEFT)
        font_size = BODY_SIZE
    elif role == "body":
        set_paragraph_common(paragraph, align=align or WD_ALIGN_PARAGRAPH.JUSTIFY, first_line_pt=FIRST_LINE_PT)
        font_size = BODY_SIZE
    elif role == "sub":
        set_paragraph_common(paragraph, align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_line_pt=FIRST_LINE_PT)
        font_size = BODY_SIZE
    else:
        set_paragraph_common(paragraph, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
        font_size = BODY_SIZE
    run = paragraph.add_run(text)
    set_run_font(run, size=font_size, bold=False)


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
    # A break run can be pushed to the next page when the preceding frame uses
    # the full page, creating an accidental blank page. Page-break-before keeps
    # the following frame on the next page without that extra sheet.
    paragraph.paragraph_format.page_break_before = True
    run = paragraph.add_run(" ")
    run.font.size = Pt(1)


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


def _validate_official_template() -> None:
    if not OFFICIAL_TEMPLATE.exists():
        raise FileNotFoundError(OFFICIAL_TEMPLATE)
    template = Document(OFFICIAL_TEMPLATE)
    if len(template.tables) != 4 or len(template.tables[2].rows) != 11:
        raise ValueError("Unexpected 2027 opening-report template structure")
    opening_text = "\n".join(cell.text for row in template.tables[2].rows for cell in row.cells)
    required = ("一、选题背景和意义", "六、主要参考文献", "指导教师意见", "系意见")
    missing = [token for token in required if token not in opening_text]
    if missing:
        raise ValueError(f"2027 opening-report template fields missing: {missing}")


def build(source_path: Path = DEFAULT_SOURCE, output_path: Path = DEFAULT_OUTPUT) -> None:
    _validate_official_template()
    if not source_path.exists():
        raise FileNotFoundError(source_path)
    source_doc = Document(source_path)
    source_top = source_doc.tables[0]
    source_main = source_doc.tables[1]
    row_text = {idx: extract_unique_row_text(source_main, idx) for idx in range(len(source_main.rows))}

    def find_row(prefix: str, start: int = 0) -> int:
        for idx in range(start, len(source_main.rows)):
            if row_text[idx].startswith(prefix):
                return idx
        raise ValueError(f"Required source row not found: {prefix}")

    section_rows = {
        "one": find_row("一、选题背景和意义"),
        "two": find_row("二、文献综述"),
        "three": find_row("三、研究内容"),
        "four": find_row("四、研究方法、研究思路"),
        "five": find_row("五、研究工作进展计划"),
        "six": find_row("六、主要参考文献"),
    }
    ordered_sections = list(section_rows.values())
    if ordered_sections != sorted(ordered_sections):
        raise ValueError(f"Opening-report sections are out of order: {ordered_sections}")
    review_start = len(source_main.rows) - 2
    if section_rows["six"] >= review_start:
        raise ValueError("Opening-report review rows overlap the reference section")

    subheadings = {
        "选题的依据和意义",
        "选题背景",
        "选题意义",
        "拟达到的目的",
        "前言",
        "国外研究现状",
        "国内研究现状",
        "总结",
        "1、通过本系统，我将研究以下问题的解决和实现",
        "2、研究系统以下功能的实现",
        "3、拟定数据库方案（10 张物理表）",
        "研究方法",
        "研究步骤",
        "所需条件",
    }

    def role_for(idx: int) -> str:
        text = row_text[idx]
        if idx in section_rows.values():
            return "main"
        if text in subheadings:
            return "sub"
        if idx > section_rows["six"]:
            return "reference"
        return "body"

    def items(start: int, end: int, *, strip_function_numbers: bool = False,
              transform_plan_numbers: bool = False) -> list[tuple[str, str]]:
        result: list[tuple[str, str]] = []
        for idx in range(start, end):
            text = row_text[idx]
            if strip_function_numbers and re.match(r"^\d+\.\s*", text):
                text = transformed_function(text)
            if transform_plan_numbers and re.match(r"^\d+\.\s*", text):
                text = transformed_progress(text)
            if idx > section_rows["six"]:
                text = transformed_reference(text)
            result.append((text, role_for(idx)))
        return result
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
    school.paragraph_format.space_before = Pt(8)
    school.paragraph_format.space_after = Pt(14)
    run = school.add_run(source_doc.paragraphs[0].text)
    set_run_font(run, east_asia="黑体", latin="黑体", size=16, bold=True)
    report_title = document.add_paragraph()
    set_paragraph_common(report_title, align=WD_ALIGN_PARAGRAPH.CENTER, line_pt=20)
    report_title.paragraph_format.space_after = Pt(14)
    run = report_title.add_run(source_doc.paragraphs[1].text)
    set_run_font(run, east_asia="黑体", latin="黑体", size=16, bold=True)

    top_table = document.add_table(rows=1, cols=4)
    top_widths = [2.5, 4.1, 2.7, 7.35]
    set_table_layout(top_table, top_widths)
    set_table_borders(top_table, enabled=False)
    for index, cell in enumerate(top_table.rows[0].cells):
        clear_cell(cell)
        set_cell_margins(cell, top=0, bottom=0, start=0, end=0)
        add_paragraph(cell, top_values[index], role="top_field", align=WD_ALIGN_PARAGRAPH.LEFT if index in {0, 2} else WD_ALIGN_PARAGRAPH.CENTER)
    set_row_height(top_table.rows[0], 0.65)
    spacer = document.add_paragraph()
    set_paragraph_common(spacer, align=WD_ALIGN_PARAGRAPH.LEFT, line_pt=0)

    page1 = document.add_table(rows=3, cols=6)
    page1_widths = [2.52, 2.88, 2.05, 3.31, 1.95, 3.94]
    set_table_layout(page1, page1_widths)
    set_table_borders(page1, enabled=True)
    style_all_cells(page1)
    for cell, text in zip(page1.rows[0].cells, identity_values):
        clear_cell(cell)
        add_paragraph(cell, text, role="field")
    set_row_height(page1.rows[0], 0.68)
    title_label = page1.rows[1].cells[0]
    title_content = page1.rows[1].cells[1].merge(page1.rows[1].cells[-1])
    clear_cell(title_label)
    clear_cell(title_content)
    add_paragraph(title_label, title_values[0], role="field")
    add_paragraph(title_content, title_values[1], role="field")
    set_cell_width(title_label, page1_widths[0])
    set_cell_width(title_content, sum(page1_widths[1:]))
    set_row_height(page1.rows[1], 1.24)
    section1 = page1.rows[2].cells[0].merge(page1.rows[2].cells[-1])
    clear_cell(section1)
    section1.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
    for text, role in items(section_rows["one"], section_rows["two"]):
        # The source keeps the official semantic grouping, while the approved
        # template rendering shows only “选题背景” and “选题意义”.
        if text in {"选题的依据和意义", "拟达到的目的"}:
            continue
        add_paragraph(section1, text, role=role)
    domestic_start = find_row("国内研究现状", section_rows["two"])
    foreign_start = find_row("国外研究现状", domestic_start)
    summary_start = find_row("总结", foreign_start)

    add_page_break(document)
    domestic_split = min(domestic_start + 7, foreign_start)
    literature_intro = items(section_rows["two"], domestic_start)
    page2_group = literature_intro + items(domestic_start, domestic_split)
    page2 = add_single_column_page(document, [page2_group])
    set_row_height(page2.rows[0], 23.90)

    add_page_break(document)
    page3_group = items(domestic_split, foreign_start)
    page3 = add_single_column_page(document, [page3_group])
    set_row_height(page3.rows[0], 23.90)

    add_page_break(document)
    page4_literature = items(foreign_start, section_rows["three"])
    page4 = add_single_column_page(document, [page4_literature])
    set_row_height(page4.rows[0], 23.90)

    add_page_break(document)
    function_twelve = find_row("12.", section_rows["three"])
    page5_research = items(
        section_rows["three"], function_twelve, strip_function_numbers=True
    )
    page5 = add_single_column_page(document, [page5_research])
    set_row_height(page5.rows[0], 23.90)

    add_page_break(document)
    steps_start = find_row("研究步骤", section_rows["four"])
    page6_research = items(
        function_twelve, section_rows["four"], strip_function_numbers=True
    )
    page6_methods = items(section_rows["four"], steps_start)
    page6 = add_single_column_page(document, [page6_research, page6_methods])
    set_row_height(page6.rows[0], 8.00)
    set_row_height(page6.rows[1], 16.10)

    add_page_break(document)
    page7_methods = items(steps_start, section_rows["five"])
    page7_plan = items(
        section_rows["five"], section_rows["six"], transform_plan_numbers=True
    )
    page7 = add_single_column_page(document, [page7_methods, page7_plan])
    set_row_height(page7.rows[0], 18.30)
    set_row_height(page7.rows[1], 5.60)

    reference_rows = list(range(section_rows["six"] + 1, review_start))
    if len(reference_rows) < 15:
        raise ValueError(f"Expected at least 15 references, found {len(reference_rows)}")
    reference_split = (len(reference_rows) + 1) // 2

    add_page_break(document)
    page8_refs = [(row_text[section_rows["six"]], "main")]
    page8_refs.extend(
        (transformed_reference(row_text[idx]), "reference")
        for idx in reference_rows[:reference_split]
    )
    page8 = add_single_column_page(document, [page8_refs])
    set_row_height(page8.rows[0], 23.90)

    add_page_break(document)
    page9_refs = [
        (transformed_reference(row_text[idx]), "reference")
        for idx in reference_rows[reference_split:]
    ]
    page9 = add_single_column_page(document, [page9_refs])
    set_row_height(page9.rows[0], 23.90)

    add_page_break(document)
    page10 = document.add_table(rows=2, cols=2)
    review_widths = [0.97, 15.68]
    set_table_layout(page10, review_widths)
    set_table_borders(page10, enabled=True)
    style_all_cells(page10)
    for row_index, source_row_index, label, empty_lines in (
        (0, review_start, "指\n导\n教\n师\n意\n见", 4),
        (1, review_start + 1, "系\n意\n见", 5),
    ):
        label_cell, content_cell = page10.rows[row_index].cells
        clear_cell(label_cell)
        clear_cell(content_cell)
        label_cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        content_cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
        set_cell_margins(label_cell, start=0, end=0)
        p = label_cell.paragraphs[0]
        set_paragraph_common(p, align=WD_ALIGN_PARAGRAPH.CENTER, line_pt=12.5)
        run = p.add_run(label)
        set_run_font(run)
        source_content = source_main.rows[source_row_index].cells[-1]
        review_text = source_content.paragraphs[0].text.split("\n", 1)[0]
        signature_text = source_content.paragraphs[-1].text
        signature_label, _, date_text = signature_text.partition("年")
        add_paragraph(content_cell, review_text, role="signature")
        for _ in range(empty_lines):
            add_empty_line(content_cell)
        add_paragraph(content_cell, signature_label.rstrip(), role="signature")
        add_paragraph(
            content_cell,
            f"年{date_text}" if date_text else "年　　月　　日",
            role="signature",
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
    set_row_height(page10.rows[0], 5.35, exact=True)
    set_row_height(page10.rows[1], 5.60, exact=True)

    document.core_properties.title = "云南工商学院毕业设计开题报告"
    document.core_properties.subject = "赵灿毕业设计开题报告"
    document.core_properties.author = "赵灿"
    document.core_properties.keywords = "开题报告；错题分析；个性化推荐；检索增强生成；知识追踪"
    rendered_text = "\n".join(
        cell.text for table in document.tables for row in table.rows for cell in row.cells
    )
    unexpected_headings = [
        heading
        for heading in ("选题的依据和意义", "拟达到的目的")
        if heading in rendered_text
    ]
    if unexpected_headings:
        raise ValueError(
            "Opening-report export must preserve the approved two-heading layout; "
            f"unexpected headings: {unexpected_headings}"
        )
    settings = document.settings._element
    zoom = settings.find(qn("w:zoom"))
    if zoom is None:
        zoom = OxmlElement("w:zoom")
        settings.insert(0, zoom)
    zoom.set(qn("w:percent"), "100")
    reorder_ooxml_properties(document)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(output_path)
    print(output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.source.resolve(), args.output.resolve())
