#!/usr/bin/env python3
"""Build the 2027-template-aligned opening-report DOCX/PDF from Markdown."""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.fonts import addMapping
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    LongTable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "docs" / "thesis" / "开题报告.md"
DEFAULT_DOCX = ROOT / "output" / "docx" / "云南工商学院毕业设计开题报告-赵灿.docx"
DEFAULT_PDF = ROOT / "output" / "pdf" / "云南工商学院毕业设计开题报告-赵灿.pdf"

FONT_DIR = Path(r"C:\Windows\Fonts")
FONT_SIMSUN = FONT_DIR / "simsun.ttc"
FONT_SIMSUN_BOLD = FONT_DIR / "simsunb.ttf"
FONT_SIMHEI = FONT_DIR / "simhei.ttf"
FONT_TIMES = FONT_DIR / "times.ttf"
FONT_TIMES_BOLD = FONT_DIR / "timesbd.ttf"

INLINE_TOKEN_RE = re.compile(r"(\*\*.*?\*\*|`.*?`|\[\d+\])")
REF_RE = re.compile(r"^\[\d+\]")
CITATION_RE = re.compile(r"\[(\d+)(?:\s*[-—]\s*(\d+))?\]")
REFERENCE_NUMBER_RE = re.compile(r"^\[(\d+)\]\s", re.MULTILINE)
EXPECTED_SCHEDULE = (
    "1. 开题报告：2026 年 09 月 16 日至 2026 年 09 月 24 日",
    "2. 完成初稿：2026 年 09 月 25 日至 2026 年 11 月 15 日",
    "3. 完成终稿：2026 年 11 月 16 日至 2026 年 12 月 20 日",
    "4. 答辩：2027 年 03 月 17 日至 2027 年 03 月 31 日",
)


@dataclass
class Block:
    kind: str
    text: str


@dataclass
class ReportSource:
    college: str
    class_name: str
    name: str
    student_id: str
    teacher: str
    title: str
    blocks: list[Block]


def _strip_markdown(text: str) -> str:
    return text.replace("**", "").replace("`", "").strip()


def _validate_reference_order(raw: str) -> None:
    body, separator, references = raw.partition("## 六、主要参考文献")
    if not separator:
        raise ValueError("Opening report reference section is missing")

    first_appearance: list[int] = []
    for match in CITATION_RE.finditer(body):
        start = int(match.group(1))
        end = int(match.group(2) or start)
        if end < start:
            raise ValueError(f"Invalid descending citation range: {match.group(0)}")
        for number in range(start, end + 1):
            if number not in first_appearance:
                first_appearance.append(number)

    reference_numbers = [int(number) for number in REFERENCE_NUMBER_RE.findall(references)]
    expected = list(range(1, len(reference_numbers) + 1))
    if reference_numbers != expected:
        raise ValueError(
            f"Reference list must be numbered continuously: {reference_numbers}"
        )
    if first_appearance != expected:
        raise ValueError(
            "Citations must follow first-appearance order; "
            f"found {first_appearance}, expected {expected}"
        )


def _validate_literature_review(raw: str) -> None:
    _, marker, tail = raw.partition("## 二、文献综述")
    if not marker:
        raise ValueError("Opening report literature-review section is missing")
    review, marker, _ = tail.partition("## 三、研究内容")
    if not marker:
        raise ValueError("Opening report research-content section is missing")

    _, marker, domestic_tail = review.partition("**国内研究现状**")
    if not marker:
        raise ValueError("Domestic-research subsection is missing")
    domestic, marker, foreign_tail = domestic_tail.partition("**国外研究现状**")
    if not marker:
        raise ValueError("Foreign-research subsection must follow domestic research")
    foreign, marker, _ = foreign_tail.partition("**总结**")
    if not marker:
        raise ValueError("Literature-review summary is missing")

    def cited_paragraph_count(text: str) -> int:
        return sum(
            1
            for line in text.splitlines()
            if line.strip() and CITATION_RE.search(line)
        )

    foreign_count = cited_paragraph_count(foreign)
    domestic_count = cited_paragraph_count(domestic)
    if foreign_count < 3 or domestic_count < 10:
        raise ValueError(
            "Literature review must contain individually cited summaries for "
            f"at least 3 foreign and 10 Chinese sources; found {foreign_count} and {domestic_count}"
        )


def _validate_schedule(raw: str) -> None:
    _, marker, tail = raw.partition("## 五、研究工作进展计划")
    if not marker:
        raise ValueError("Opening report schedule section is missing")
    schedule, marker, _ = tail.partition("## 六、主要参考文献")
    if not marker:
        raise ValueError("Opening report reference section is missing")
    schedule_lines = tuple(
        line.strip() for line in schedule.splitlines() if re.match(r"^\d+\.\s", line.strip())
    )
    if schedule_lines != EXPECTED_SCHEDULE:
        raise ValueError(
            "Opening-report schedule is not the latest approved four-item schedule: "
            f"{schedule_lines}"
        )


def parse_source(path: Path) -> ReportSource:
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()

    metadata: dict[str, str] = {}
    for line in lines:
        if not line.startswith("|") or "---" in line or "项目" in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 4:
            metadata[cells[0].replace("　", "").replace(" ", "")] = cells[1]
            metadata[cells[2].replace("　", "").replace(" ", "")] = cells[3]

    blocks: list[Block] = []
    started = False
    current_section = ""
    for original in lines:
        line = original.strip()
        if line.startswith("## 一、"):
            started = True
        if not started:
            continue
        if line.startswith("## 指导教师意见"):
            break
        if not line or line == "---":
            continue
        if line.startswith("## "):
            current_section = _strip_markdown(line[3:])
            if not current_section.endswith("："):
                current_section += "："
            blocks.append(Block("section", current_section))
            continue
        if line.startswith("### "):
            text = _strip_markdown(line[4:])
            if current_section.startswith("一、"):
                text = re.sub(r"^（[12]）", "", text)
            blocks.append(Block("subheading", text))
            continue
        if re.fullmatch(r"\*\*.+\*\*", line):
            blocks.append(Block("label", _strip_markdown(line)))
            continue
        if line.startswith("- "):
            blocks.append(Block("bullet", line[2:].strip()))
            continue
        if REF_RE.match(line):
            blocks.append(Block("reference", line))
            continue
        if re.match(r"^\d+\.\s", line):
            blocks.append(Block("numbered", line))
            continue
        if line.startswith(">"):
            continue
        blocks.append(Block("paragraph", line))

    required = {
        "二级学院": "人工智能学院",
        "专业及班级": "2023 级【本科】软件工程 1 班",
        "姓名": "赵灿",
        "学号": "23612801026",
        "指导教师": "胡韬",
        "题目名称": "基于智谱GLM模型的AI错题分析与学习推荐系统设计与实现",
    }
    for key, fallback in required.items():
        metadata.setdefault(key, fallback)

    if len([b for b in blocks if b.kind == "reference"]) < 15:
        raise ValueError("Opening report must contain at least 15 references")
    _validate_reference_order(raw)
    _validate_literature_review(raw)
    _validate_schedule(raw)
    if "10 张物理表" not in raw:
        raise ValueError("Opening report must retain the proposed 10-table design scope")
    forbidden = ("【待写】", "120 份", "112 份", "104 份", "5 名学生", "3 名教师")
    found = [token for token in forbidden if token in raw]
    if found:
        raise ValueError(f"Unverified placeholders or survey claims remain: {found}")
    timeline_forbidden = (
        "冻结代码",
        "冻结实现",
        "现有代码",
        "当前代码",
        "当前实现",
        "当前数据库",
        "当前仓库",
        "已有验证记录",
        "验证记录为准",
        "真实接口验证",
        "已通过智谱",
        "Gate5",
        "Merge Ready",
        "Codex",
    )
    timeline_found = [token for token in timeline_forbidden if token in raw]
    if timeline_found:
        raise ValueError(f"Post-implementation wording remains in opening report: {timeline_found}")
    revision_commentary_forbidden = (
        "为避免只罗列作者与题名",
        "逐项核对研究内容是否",
        "使研究内容能够在论文",
    )
    revision_commentary_found = [
        token for token in revision_commentary_forbidden if token in raw
    ]
    if revision_commentary_found:
        raise ValueError(
            "Reviewer-response wording remains in opening report: "
            f"{revision_commentary_found}"
        )

    return ReportSource(
        college=metadata["二级学院"],
        class_name=metadata["专业及班级"],
        name=metadata["姓名"].replace("　", ""),
        student_id=metadata["学号"],
        teacher=metadata["指导教师"],
        title=metadata["题目名称"],
        blocks=blocks,
    )


def _set_run_font(run, font_name: str, size: float, bold: bool = False) -> None:
    run.font.name = font_name
    run.font.size = Pt(size)
    run.font.bold = bold
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn("w:ascii"), font_name)
    rfonts.set(qn("w:hAnsi"), font_name)
    rfonts.set(qn("w:eastAsia"), font_name)
    rfonts.set(qn("w:cs"), font_name)


def _add_text_runs(paragraph, text: str, size: float = 12, bold: bool = False,
                   superscript_citations: bool = True) -> None:
    for token in INLINE_TOKEN_RE.split(text):
        if not token:
            continue
        token_bold = bold
        if token.startswith("**") and token.endswith("**"):
            token = token[2:-2]
            token_bold = True
        elif token.startswith("`") and token.endswith("`"):
            token = token[1:-1]
        if superscript_citations and re.fullmatch(r"\[\d+\]", token):
            run = paragraph.add_run(token)
            _set_run_font(run, "Times New Roman", size - 2, False)
            run.font.superscript = True
            continue
        groups = re.findall(r"[\x00-\x7F]+|[^\x00-\x7F]+", token)
        for group in groups:
            ascii_group = all(ord(ch) < 128 for ch in group)
            font = "Times New Roman" if ascii_group else ("黑体" if token_bold else "宋体")
            run = paragraph.add_run(group)
            _set_run_font(run, font, size, token_bold and ascii_group)


def _format_docx_paragraph(paragraph, kind: str) -> None:
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(0)
    fmt.space_after = Pt(0)
    fmt.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    fmt.line_spacing = Pt(20)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if kind == "paragraph":
        fmt.first_line_indent = Pt(24)
    elif kind in {"subheading", "label"}:
        fmt.left_indent = Pt(24)
        fmt.keep_with_next = True
    elif kind in {"bullet", "numbered"}:
        fmt.left_indent = Pt(24)
        fmt.first_line_indent = Pt(-24)
    elif kind == "reference":
        fmt.left_indent = Pt(24)
        fmt.first_line_indent = Pt(-24)
    elif kind == "section":
        fmt.keep_with_next = True


def _set_cell_margins(cell, top=80, start=110, bottom=80, end=110) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for tag, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{tag}"))
        if node is None:
            node = OxmlElement(f"w:{tag}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")
    _reorder_tc_pr(tc_pr)


def _reorder_tc_pr(tc_pr) -> None:
    """Keep table-cell property children in the OOXML schema order."""
    order = {
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
    children = list(tc_pr)
    children.sort(key=lambda child: order.get(child.tag.rsplit("}", 1)[-1], 100))
    for child in list(tc_pr):
        tc_pr.remove(child)
    for child in children:
        tc_pr.append(child)


def _set_cell_borders(cell, **edges) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_borders = tc_pr.first_child_found_in("w:tcBorders")
    if tc_borders is None:
        tc_borders = OxmlElement("w:tcBorders")
        tc_pr.append(tc_borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        if edge not in edges:
            continue
        data = edges[edge]
        tag = qn(f"w:{edge}")
        element = tc_borders.find(tag)
        if element is None:
            element = OxmlElement(f"w:{edge}")
            tc_borders.append(element)
        element.set(qn("w:val"), data.get("val", "single"))
        element.set(qn("w:sz"), str(data.get("sz", 6)))
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), data.get("color", "000000"))
    _reorder_tc_pr(tc_pr)


def _set_cell_text_direction(cell, value="tbRl") -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    text_direction = tc_pr.find(qn("w:textDirection"))
    if text_direction is None:
        text_direction = OxmlElement("w:textDirection")
        tc_pr.append(text_direction)
    text_direction.set(qn("w:val"), value)
    _reorder_tc_pr(tc_pr)


def _set_repeat_table_width(table, widths_cm: list[float]) -> None:
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_pr = table._tbl.tblPr
    layout = tbl_pr.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tbl_pr.append(layout)
    layout.set(qn("w:type"), "fixed")
    for row in table.rows:
        for index, cell in enumerate(row.cells):
            if index < len(widths_cm):
                cell.width = Cm(widths_cm[index])


def _clear_cell(cell) -> None:
    paragraph = cell.paragraphs[0]
    for run in list(paragraph.runs):
        paragraph._p.remove(run._r)


def _add_docx_block_row(table, block: Block) -> None:
    row = table.add_row()
    cell = row.cells[0].merge(row.cells[-1])
    _clear_cell(cell)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    _set_cell_margins(cell, top=25 if block.kind == "section" else 45,
                      bottom=25 if block.kind == "section" else 45)
    _set_cell_borders(
        cell,
        left={"val": "single", "sz": 6},
        right={"val": "single", "sz": 6},
        top={"val": "single", "sz": 6} if block.kind == "section" else {"val": "nil", "sz": 0},
        bottom={"val": "nil", "sz": 0},
    )
    paragraph = cell.paragraphs[0]
    _format_docx_paragraph(paragraph, block.kind)
    is_bold = block.kind in {"subheading", "label"}
    _add_text_runs(
        paragraph,
        block.text,
        size=12,
        bold=is_bold,
        superscript_citations=block.kind != "reference",
    )


def build_docx(source: ReportSource, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.75)
    section.right_margin = Cm(2.5)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.header_distance = Cm(1.5)
    section.footer_distance = Cm(1.5)

    normal = doc.styles["Normal"]
    normal.font.name = "宋体"
    normal.font.size = Pt(12)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(14)
    r = p.add_run("云南工商学院")
    _set_run_font(r, "黑体", 18, True)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(22)
    r = p.add_run("毕业设计开题报告")
    _set_run_font(r, "黑体", 18, True)

    info = doc.add_table(rows=1, cols=4)
    info.alignment = WD_TABLE_ALIGNMENT.CENTER
    info.autofit = False
    info_widths = [Cm(2.4), Cm(4.6), Cm(2.6), Cm(6.15)]
    labels = ["二级学院：", source.college, "专业及班级：", source.class_name.replace(" 级", "级").replace(" 1 班", "1班")]
    for cell, width, text in zip(info.rows[0].cells, info_widths, labels):
        cell.width = width
        _set_cell_borders(cell, top={"val": "nil"}, bottom={"val": "nil"}, left={"val": "nil"}, right={"val": "nil"})
        _set_cell_margins(cell, top=0, bottom=80, start=0, end=0)
        para = cell.paragraphs[0]
        para.paragraph_format.space_after = Pt(0)
        _add_text_runs(para, text, 12, False, False)

    table = doc.add_table(rows=0, cols=6)
    widths = [2.2, 2.1, 1.8, 3.3, 2.4, 3.95]

    row = table.add_row()
    values = ["姓　　名", source.name, "学　　号", source.student_id, "指导教师", source.teacher]
    for cell, value in zip(row.cells, values):
        _set_cell_margins(cell, top=90, bottom=90)
        _set_cell_borders(cell, top={"sz": 6}, bottom={"sz": 6}, left={"sz": 6}, right={"sz": 6})
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.space_after = Pt(0)
        _add_text_runs(para, value, 12, False, False)

    row = table.add_row()
    label_cell = row.cells[0]
    title_cell = row.cells[1].merge(row.cells[-1])
    for cell in (label_cell, title_cell):
        _set_cell_margins(cell, top=100, bottom=100)
        _set_cell_borders(cell, top={"sz": 6}, bottom={"sz": 6}, left={"sz": 6}, right={"sz": 6})
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    label_cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_text_runs(label_cell.paragraphs[0], "题目名称", 12, False, False)
    title_cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_text_runs(title_cell.paragraphs[0], source.title, 12, False, False)

    for block in source.blocks:
        _add_docx_block_row(table, block)

    for label, signature, height in (
        ("指导教师意见", "指导教师签名：　　　　　　　　　年　　月　　日", 110),
        ("系意见", "系主任签名：　　　　　　　　　　　年　　月　　日", 85),
    ):
        row = table.add_row()
        row.height = Pt(height)
        left = row.cells[0]
        right = row.cells[1].merge(row.cells[-1])
        _set_cell_text_direction(left)
        for cell in (left, right):
            _set_cell_margins(cell, top=80, bottom=80)
            _set_cell_borders(cell, top={"sz": 6}, bottom={"sz": 6}, left={"sz": 6}, right={"sz": 6})
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        left.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        _add_text_runs(left.paragraphs[0], label, 12, False, False)
        p = right.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after = Pt(0)
        _add_text_runs(p, "审核意见：", 12, False, False)
        p.add_run().add_break(WD_BREAK.LINE)
        p.add_run().add_break(WD_BREAK.LINE)
        p.add_run().add_break(WD_BREAK.LINE)
        sig = right.add_paragraph()
        sig.paragraph_format.space_before = Pt(0)
        sig.paragraph_format.space_after = Pt(0)
        _add_text_runs(sig, signature, 12, False, False)

    _set_repeat_table_width(table, widths)
    doc.core_properties.title = "云南工商学院毕业设计开题报告"
    doc.core_properties.subject = source.title
    doc.core_properties.author = source.name
    doc.core_properties.keywords = "错题分析；个性化推荐；检索增强生成；知识追踪"
    settings = doc.settings._element
    zoom = settings.find(qn("w:zoom"))
    if zoom is None:
        zoom = OxmlElement("w:zoom")
        settings.insert(0, zoom)
    zoom.set(qn("w:percent"), "100")
    doc.save(output)


def _register_pdf_fonts() -> None:
    for path in (FONT_SIMSUN, FONT_SIMSUN_BOLD, FONT_SIMHEI, FONT_TIMES, FONT_TIMES_BOLD):
        if not path.exists():
            raise FileNotFoundError(f"Required font missing: {path}")
    pdfmetrics.registerFont(TTFont("SimSun", str(FONT_SIMSUN), subfontIndex=0))
    pdfmetrics.registerFont(TTFont("SimSunBold", str(FONT_SIMSUN_BOLD)))
    pdfmetrics.registerFont(TTFont("SimHei", str(FONT_SIMHEI)))
    pdfmetrics.registerFont(TTFont("TimesNewRoman", str(FONT_TIMES)))
    pdfmetrics.registerFont(TTFont("TimesNewRomanBold", str(FONT_TIMES_BOLD)))
    addMapping("SimSun", 0, 0, "SimSun")
    addMapping("SimSun", 1, 0, "SimSunBold")
    addMapping("TimesNewRoman", 0, 0, "TimesNewRoman")
    addMapping("TimesNewRoman", 1, 0, "TimesNewRomanBold")


def _font_markup(text: str, bold: bool = False) -> str:
    parts: list[str] = []
    for group in re.findall(r"[\x00-\x7F]+|[^\x00-\x7F]+", text):
        escaped = html.escape(group)
        ascii_group = all(ord(ch) < 128 for ch in group)
        if ascii_group:
            font = "TimesNewRomanBold" if bold else "TimesNewRoman"
        else:
            font = "SimHei" if bold else "SimSun"
        parts.append(f'<font name="{font}">{escaped}</font>')
    return "".join(parts)


def _pdf_markup(text: str, superscript_citations: bool = True) -> str:
    parts: list[str] = []
    for token in INLINE_TOKEN_RE.split(text):
        if not token:
            continue
        token_bold = False
        if token.startswith("**") and token.endswith("**"):
            token = token[2:-2]
            token_bold = True
        elif token.startswith("`") and token.endswith("`"):
            token = token[1:-1]
        if superscript_citations and re.fullmatch(r"\[\d+\]", token):
            parts.append(f'<super>{_font_markup(token)}</super>')
        else:
            parts.append(_font_markup(token, token_bold))
    return "".join(parts)


def _pdf_styles():
    styles = getSampleStyleSheet()
    base = dict(fontName="SimSun", fontSize=12, leading=20, textColor=colors.black,
                spaceBefore=0, spaceAfter=0, wordWrap="CJK")
    return {
        "title": ParagraphStyle("ReportTitle", parent=styles["Normal"], fontName="SimHei",
                                fontSize=18, leading=24, alignment=TA_CENTER,
                                spaceBefore=0, spaceAfter=0),
        "info": ParagraphStyle("Info", parent=styles["Normal"], alignment=TA_LEFT, **base),
        "info_center": ParagraphStyle("InfoCenter", parent=styles["Normal"], alignment=TA_CENTER, **base),
        "section": ParagraphStyle("Section", parent=styles["Normal"], alignment=TA_LEFT,
                                  keepWithNext=True, **base),
        "subheading": ParagraphStyle("Subheading", parent=styles["Normal"], alignment=TA_LEFT,
                                     leftIndent=24, keepWithNext=True, **base),
        "body": ParagraphStyle("Body", parent=styles["Normal"], alignment=TA_JUSTIFY,
                               firstLineIndent=24, **base),
        "list": ParagraphStyle("List", parent=styles["Normal"], alignment=TA_JUSTIFY,
                               leftIndent=24, firstLineIndent=-24, **base),
        "reference": ParagraphStyle("Reference", parent=styles["Normal"], alignment=TA_LEFT,
                                    leftIndent=24, firstLineIndent=-24, **base),
        "vertical": ParagraphStyle("Vertical", parent=styles["Normal"], fontName="SimSun",
                                   fontSize=12, leading=17, alignment=TA_CENTER, wordWrap="CJK"),
    }


def _pdf_block(block: Block, styles) -> Paragraph:
    if block.kind == "section":
        return Paragraph(_pdf_markup(block.text), styles["section"])
    if block.kind in {"subheading", "label"}:
        return Paragraph(_font_markup(_strip_markdown(block.text), True), styles["subheading"])
    if block.kind in {"bullet", "numbered"}:
        return Paragraph(_pdf_markup(block.text), styles["list"])
    if block.kind == "reference":
        return Paragraph(_pdf_markup(block.text, False), styles["reference"])
    return Paragraph(_pdf_markup(block.text), styles["body"])


def build_pdf(source: ReportSource, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    _register_pdf_fonts()
    styles = _pdf_styles()
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=2.75 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        title="云南工商学院毕业设计开题报告",
        author=source.name,
        subject=source.title,
        creator="graduation-project reproducible document builder",
    )
    width = A4[0] - 2.75 * cm - 2.5 * cm
    story = [
        Paragraph(_font_markup("云南工商学院", True), styles["title"]),
        Spacer(1, 14),
        Paragraph(_font_markup("毕业设计开题报告", True), styles["title"]),
        Spacer(1, 22),
    ]

    college_info = Table(
        [[
            Paragraph(_font_markup("二级学院："), styles["info"]),
            Paragraph(_font_markup(source.college), styles["info"]),
            Paragraph(_font_markup("专业及班级："), styles["info"]),
            Paragraph(_font_markup(source.class_name.replace(" 级", "级").replace(" 1 班", "1班")), styles["info"]),
        ]],
        colWidths=[2.4 * cm, 4.6 * cm, 2.8 * cm, width - 9.8 * cm],
    )
    college_info.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(college_info)

    col_widths = [2.2 * cm, 2.1 * cm, 1.8 * cm, 3.3 * cm, 2.4 * cm, width - 11.8 * cm]
    rows: list[list[object]] = []
    row_heights: list[float | None] = []
    spans: list[tuple] = []
    rules: list[tuple] = []

    rows.append([
        Paragraph(_font_markup("姓　　名"), styles["info_center"]),
        Paragraph(_font_markup(source.name), styles["info_center"]),
        Paragraph(_font_markup("学　　号"), styles["info_center"]),
        Paragraph(_font_markup(source.student_id), styles["info_center"]),
        Paragraph(_font_markup("指导教师"), styles["info_center"]),
        Paragraph(_font_markup(source.teacher), styles["info_center"]),
    ])
    row_heights.append(None)
    rows.append([
        Paragraph(_font_markup("题目名称"), styles["info_center"]),
        Paragraph(_font_markup(source.title), styles["info_center"]), "", "", "", "",
    ])
    row_heights.append(None)
    spans.append(("SPAN", (1, 1), (5, 1)))

    block_index = 0
    while block_index < len(source.blocks):
        block = source.blocks[block_index]
        row_index = len(rows)
        cell_content: object = _pdf_block(block, styles)
        if (
            block.kind in {"subheading", "label"}
            and block_index + 1 < len(source.blocks)
            and source.blocks[block_index + 1].kind in {"paragraph", "bullet", "numbered"}
        ):
            cell_content = [
                _pdf_block(block, styles),
                _pdf_block(source.blocks[block_index + 1], styles),
            ]
            block_index += 1
        rows.append([cell_content, "", "", "", "", ""])
        row_heights.append(None)
        spans.append(("SPAN", (0, row_index), (5, row_index)))
        if block.kind == "section":
            rules.append(("LINEABOVE", (0, row_index), (5, row_index), 0.75, colors.black))
        block_index += 1

    for label, signature, height in (
        ("指<br/>导<br/>教<br/>师<br/>意<br/>见", "指导教师签名：　　　　　　　　　年　　月　　日", 110),
        ("系<br/>意<br/>见", "系主任签名：　　　　　　　　　　　年　　月　　日", 85),
    ):
        row_index = len(rows)
        right = Paragraph(
            _font_markup("审核意见：") + "<br/><br/><br/>" + _font_markup(signature.replace("　", "\u00a0")),
            styles["info"],
        )
        rows.append([Paragraph(_font_markup(label.replace("<br/>", "\n")).replace("\n", "<br/>"), styles["vertical"]), right, "", "", "", ""])
        row_heights.append(height)
        spans.append(("SPAN", (1, row_index), (5, row_index)))
        rules.append(("LINEABOVE", (0, row_index), (5, row_index), 0.75, colors.black))

    table = LongTable(rows, colWidths=col_widths, rowHeights=row_heights, splitByRow=1)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (5, 1), 0.75, colors.black),
        ("BOX", (0, 0), (5, -1), 0.75, colors.black),
        ("LINEBEFORE", (0, 2), (0, -1), 0.75, colors.black),
        ("LINEAFTER", (5, 2), (5, -1), 0.75, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        *spans,
        *rules,
    ]))
    story.append(table)
    doc.build(story)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--docx", type=Path, default=DEFAULT_DOCX)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    args = parser.parse_args()
    source = parse_source(args.source.resolve())
    final_docx = args.docx.resolve()
    final_pdf = args.pdf.resolve()
    draft_dir = ROOT / "tmp" / "opening-report-build"
    draft_dir.mkdir(parents=True, exist_ok=True)
    draft_docx = draft_dir / "base.docx"
    build_docx(source, draft_docx)

    from align_opening_report_to_template import build as align_to_2027_template

    align_to_2027_template(draft_docx, final_docx)

    soffice = shutil.which("soffice")
    if soffice is None:
        common = Path(r"C:\Program Files\LibreOffice\program\soffice.exe")
        if common.exists():
            soffice = str(common)
    if soffice is None:
        raise FileNotFoundError("LibreOffice soffice is required to export the template-aligned PDF")

    final_pdf.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="opening-report-pdf-") as temp_name:
        temp_dir = Path(temp_name)
        profile_dir = temp_dir / "profile"
        profile_dir.mkdir()
        command = [
            soffice,
            f"-env:UserInstallation={profile_dir.resolve().as_uri()}",
            "--headless",
            "--norestore",
            "--convert-to",
            "pdf",
            "--outdir",
            str(temp_dir),
            str(final_docx),
        ]
        subprocess.run(command, check=True, capture_output=True)
        generated_pdf = temp_dir / f"{final_docx.stem}.pdf"
        if not generated_pdf.exists():
            raise FileNotFoundError(generated_pdf)
        shutil.copy2(generated_pdf, final_pdf)
    print(f"DOCX: {args.docx.resolve()}")
    print(f"PDF:  {args.pdf.resolve()}")


if __name__ == "__main__":
    main()
