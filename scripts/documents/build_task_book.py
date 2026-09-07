#!/usr/bin/env python3
"""Build the current graduation-design task-book DOCX/PDF from Markdown."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_ROW_HEIGHT_RULE, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "docs" / "thesis" / "任务书-AI错题分析与学习推荐系统.md"
DEFAULT_TEMPLATE = ROOT / "docs" / "materials" / "参考论文" / "其他文档" / "任务书参考.docx"
DEFAULT_DOCX = ROOT / "output" / "docx" / "云南工商学院毕业设计任务书-赵灿.docx"
DEFAULT_PDF = ROOT / "output" / "pdf" / "云南工商学院毕业设计任务书-赵灿.pdf"

EXPECTED_SCHEDULE = (
    "1. 开题报告：2026 年 10 月 01 日至 2026 年 10 月 31 日",
    "2. 完成初稿：2026 年 11 月 01 日至 2026 年 12 月 15 日",
    "3. 完成终稿：2026 年 12 月 16 日至 2027 年 03 月 31 日",
    "4. 答辩：2027 年 04 月 15 日至 2027 年 05 月 15 日",
)


@dataclass
class Block:
    kind: str
    text: str


@dataclass
class TaskBookSource:
    title: str
    student_name: str
    student_id: str
    class_name: str
    college: str
    source_type: str
    topic_type: str
    background: list[Block]
    requirements: list[Block]
    schedule: list[Block]


def clean_markdown(text: str) -> str:
    return text.replace("**", "").replace("`", "").strip()


def parse_blocks(lines: list[str]) -> list[Block]:
    blocks: list[Block] = []
    for original in lines:
        line = original.strip()
        if not line or line == "---" or line.startswith("（导出时：") or line.startswith("（本次新增"):
            continue
        if line.startswith("### "):
            blocks.append(Block("heading", clean_markdown(line[4:])))
        elif line.startswith("- "):
            blocks.append(Block("bullet", line[2:].strip()))
        elif re.match(r"^\[\d+\]", line):
            blocks.append(Block("reference", clean_markdown(line)))
        elif re.match(r"^\d+\.\s", line):
            blocks.append(Block("numbered", clean_markdown(line)))
        elif not line.startswith("（"):
            blocks.append(Block("body", line))
    return blocks


def parse_source(path: Path) -> TaskBookSource:
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    metadata: dict[str, str] = {}
    for line in lines:
        if not line.startswith("|") or "---" in line or "项目" in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 4:
            metadata[cells[0].replace(" ", "")] = cells[1]
            metadata[cells[2].replace(" ", "")] = cells[3]

    sections: dict[str, list[str]] = {
        "选题背景及目的": [],
        "工作任务及要求": [],
        "时间安排": [],
    }
    current: str | None = None
    for line in lines:
        if line.startswith("## "):
            heading = line[3:].strip()
            current = heading if heading in sections else None
            continue
        if current is not None:
            sections[current].append(line)

    schedule_lines = tuple(
        line.strip() for line in sections["时间安排"] if re.match(r"^\d+\.\s", line.strip())
    )
    if schedule_lines != EXPECTED_SCHEDULE:
        raise ValueError(f"Task-book schedule is not the approved four-item schedule: {schedule_lines}")

    background = parse_blocks(sections["选题背景及目的"])
    background_text = "".join(block.text for block in background)
    background_cjk_count = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", background_text))
    if background_cjk_count > 800:
        raise ValueError(f"Task-book background exceeds 800 Chinese characters: {background_cjk_count}")
    background_char_count = len(re.sub(r"\s+", "", background_text))
    if not 450 <= background_char_count <= 650:
        raise ValueError(f"Task-book background should remain close to the mentor template: {background_char_count}")

    requirements = parse_blocks(sections["工作任务及要求"])
    requirement_headings = [block.text for block in requirements if block.kind == "heading"]
    expected_headings = ["一、研究目标", "二、研究内容", "三、研究方法", "四、预期成果", "五、参考文献"]
    if requirement_headings != expected_headings:
        raise ValueError(f"Task-book requirement headings must be the approved five parts: {requirement_headings}")
    if len([block for block in requirements if block.kind == "reference"]) != 5:
        raise ValueError("Task book must contain exactly 5 core references")
    requirement_text = "".join(block.text for block in requirements)
    requirement_char_count = len(re.sub(r"\s+", "", requirement_text))
    if not 1500 <= requirement_char_count <= 2100:
        raise ValueError(f"Task-book requirements should remain close to the mentor template: {requirement_char_count}")
    retrospective_tokens = ("以当前实现", "冻结代码", "已有代码", "已有验证记录", "真实代码、10 张物理表")
    retrospective_found = [token for token in retrospective_tokens if token in requirement_text]
    if retrospective_found:
        raise ValueError(f"Retrospective implementation wording remains in the task book: {retrospective_found}")
    forbidden = ("【待写】", "120 份", "112 份", "104 份", "5 名学生", "3 名教师")
    found = [token for token in forbidden if token in raw]
    if found:
        raise ValueError(f"Unverified placeholders or survey claims remain: {found}")

    return TaskBookSource(
        title=metadata.get("题目名称", "基于智谱GLM模型的AI错题分析与学习推荐系统设计与实现"),
        student_name=metadata.get("学生姓名", "赵　灿"),
        student_id=metadata.get("学号", "23612801026"),
        class_name=metadata.get("班级名称", "2023 级【本科】软件工程 1 班"),
        college=metadata.get("学院名称", "人工智能学院"),
        source_type=metadata.get("题目来源", "生产实际（社会实践）题"),
        topic_type=metadata.get("题目类型", "其他"),
        background=background,
        requirements=requirements,
        schedule=parse_blocks(sections["时间安排"]),
    )


def set_run_font(run, *, size: float = 12, bold: bool = False, east_asia: str = "宋体") -> None:
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.font.bold = bold
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn("w:ascii"), "Times New Roman")
    rfonts.set(qn("w:hAnsi"), "Times New Roman")
    rfonts.set(qn("w:cs"), "Times New Roman")
    rfonts.set(qn("w:eastAsia"), east_asia)


def add_inline_runs(paragraph, text: str, *, bold: bool = False) -> None:
    for token in re.split(r"(\*\*.*?\*\*|`.*?`)", text):
        if not token:
            continue
        token_bold = bold
        if token.startswith("**") and token.endswith("**"):
            token = token[2:-2]
            token_bold = True
        elif token.startswith("`") and token.endswith("`"):
            token = token[1:-1]
        run = paragraph.add_run(token)
        set_run_font(run, bold=token_bold, east_asia="黑体" if token_bold else "宋体")


def set_paragraph_format(paragraph, kind: str, *, center: bool = False) -> None:
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(0)
    fmt.space_after = Pt(0)
    fmt.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    fmt.line_spacing = Pt(20)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.JUSTIFY
    if kind == "body":
        fmt.first_line_indent = Pt(24)
    elif kind in {"bullet", "numbered"}:
        fmt.left_indent = Pt(24)
        fmt.first_line_indent = Pt(-24)
    elif kind == "reference":
        fmt.left_indent = Pt(24)
        fmt.first_line_indent = Pt(-24)
    elif kind == "heading":
        fmt.keep_with_next = True


def set_cell_margins(cell, *, top: int = 45, start: int = 85, bottom: int = 45, end: int = 85) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for edge, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_cell_border(cell, **edges) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        if edge not in edges:
            continue
        enabled = edges[edge]
        node = borders.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            borders.append(node)
        node.set(qn("w:val"), "single" if enabled else "nil")
        node.set(qn("w:sz"), "6" if enabled else "0")
        node.set(qn("w:space"), "0")
        node.set(qn("w:color"), "000000")


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


def set_fixed_layout(table, widths_cm: list[float]) -> None:
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    layout = tbl_pr.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tbl_pr.append(layout)
    layout.set(qn("w:type"), "fixed")
    for grid_col, width_cm in zip(table._tbl.tblGrid.gridCol_lst, widths_cm):
        grid_col.set(qn("w:w"), str(Cm(width_cm).twips))
    for column, width_cm in zip(table.columns, widths_cm):
        column.width = Cm(width_cm)
    for row in table.rows:
        for index, cell in enumerate(row.cells):
            if index < len(widths_cm):
                cell.width = Cm(widths_cm[index])


def clear_cell(cell) -> None:
    paragraph = cell.paragraphs[0]
    for run in list(paragraph.runs):
        paragraph._p.remove(run._r)


def add_cell_text(cell, text: str, *, bold: bool = False, center: bool = False) -> None:
    clear_cell(cell)
    paragraph = cell.paragraphs[0]
    set_paragraph_format(paragraph, "heading" if bold else "body", center=center)
    if not center and not bold:
        paragraph.paragraph_format.first_line_indent = None
    add_inline_runs(paragraph, text, bold=bold)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_section(document: Document, label: str, blocks: list[Block]) -> None:
    if not blocks:
        raise ValueError(f"Section has no content: {label}")
    table = document.add_table(rows=len(blocks), cols=2)
    set_fixed_layout(table, [0.95, 14.70])
    for index, (row, block) in enumerate(zip(table.rows, blocks)):
        left, right = row.cells
        left.width = Cm(0.95)
        right.width = Cm(14.70)
        for cell in (left, right):
            set_cell_margins(cell)
            set_cell_border(
                cell,
                top=index == 0,
                bottom=index == len(blocks) - 1,
                left=True,
                right=True,
            )
        clear_cell(right)
        paragraph = right.paragraphs[0]
        set_paragraph_format(paragraph, block.kind)
        add_inline_runs(paragraph, block.text, bold=block.kind == "heading")
        right.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

    label_cell = table.rows[0].cells[0]
    if label != "工作任务及要求":
        for row in table.rows[1:]:
            label_cell = label_cell.merge(row.cells[0])
    clear_cell(label_cell)
    label_cell.vertical_alignment = (
        WD_CELL_VERTICAL_ALIGNMENT.TOP if label == "工作任务及要求" else WD_CELL_VERTICAL_ALIGNMENT.CENTER
    )
    set_cell_margins(label_cell, start=0, end=0)
    paragraph = label_cell.paragraphs[0]
    set_paragraph_format(paragraph, "heading", center=True)
    run = paragraph.add_run("\n".join(label.replace(" ", "")))
    set_run_font(run, bold=True, east_asia="黑体")


def replace_paragraph_text(paragraph, text: str, *, preserve_first_run: bool = False) -> None:
    if preserve_first_run and paragraph.runs:
        paragraph.runs[0].text = text
        for run in list(paragraph.runs[1:]):
            paragraph._p.remove(run._r)
        return
    for run in list(paragraph.runs):
        paragraph._p.remove(run._r)
    paragraph.add_run(text)


def replace_cell_text(cell, text: str) -> None:
    paragraph = cell.paragraphs[0]
    for extra in list(cell.paragraphs[1:]):
        cell._tc.remove(extra._p)
    replace_paragraph_text(paragraph, text)


def replace_cell_blocks(cell, blocks: list[Block]) -> None:
    if not blocks:
        raise ValueError("Template cell content cannot be empty")
    prototype = cell.paragraphs[0]
    prototype_properties = deepcopy(prototype._p.pPr) if prototype._p.pPr is not None else None
    for extra in list(cell.paragraphs[1:]):
        cell._tc.remove(extra._p)
    for index, block in enumerate(blocks):
        paragraph = prototype if index == 0 else cell.add_paragraph()
        if index > 0 and prototype_properties is not None:
            if paragraph._p.pPr is not None:
                paragraph._p.remove(paragraph._p.pPr)
            paragraph._p.insert(0, deepcopy(prototype_properties))
        replace_paragraph_text(paragraph, clean_markdown(block.text))


def build_docx(source: TaskBookSource, output: Path, template: Path) -> None:
    if not template.exists():
        raise FileNotFoundError(f"Mentor task-book template not found: {template}")
    document = Document(template)
    if len(document.tables) != 1 or len(document.tables[0].rows) != 8 or len(document.tables[0].columns) != 7:
        raise ValueError("Mentor task-book template must contain one 8-row, 7-column table")

    replace_paragraph_text(document.paragraphs[0], "云南工商学院", preserve_first_run=True)
    replace_paragraph_text(document.paragraphs[1], "毕业设计任务书", preserve_first_run=True)
    for title_paragraph in document.paragraphs[:2]:
        title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_paragraph.paragraph_format.left_indent = None
        title_paragraph.paragraph_format.right_indent = None
        title_paragraph.paragraph_format.first_line_indent = None
        title_indent = title_paragraph._p.get_or_add_pPr().find(qn("w:ind"))
        if title_indent is not None:
            title_paragraph._p.pPr.remove(title_indent)

    invalid_title_layout = [
        paragraph.text
        for paragraph in document.paragraphs[:2]
        if paragraph.alignment != WD_ALIGN_PARAGRAPH.CENTER
        or paragraph.paragraph_format.left_indent is not None
        or paragraph.paragraph_format.right_indent is not None
        or paragraph.paragraph_format.first_line_indent is not None
        or paragraph._p.get_or_add_pPr().find(qn("w:ind")) is not None
    ]
    if invalid_title_layout:
        raise ValueError(f"Task-book title paragraphs must be centered without indentation: {invalid_title_layout}")

    table = document.tables[0]
    replace_cell_text(table.rows[0].cells[2], source.title)
    replace_cell_text(table.rows[1].cells[2], source.student_name)
    replace_cell_text(table.rows[1].cells[6], source.student_id)
    replace_cell_text(table.rows[2].cells[2], source.class_name)
    replace_cell_text(table.rows[2].cells[6], source.college)
    replace_cell_text(table.rows[3].cells[2], source.source_type)
    replace_cell_text(table.rows[3].cells[6], source.topic_type)
    replace_cell_blocks(table.rows[4].cells[1], source.background)
    replace_cell_blocks(table.rows[5].cells[1], source.requirements)
    replace_cell_blocks(table.rows[6].cells[1], source.schedule)

    table_bold_text = [
        run.text
        for row in table.rows
        for cell in row.cells
        for paragraph in cell.paragraphs
        for run in paragraph.runs
        if run.bold is True and run.text.strip()
    ]
    if table_bold_text:
        raise ValueError(f"Mentor template requires regular-weight table text: {table_bold_text}")
    reference_texts = [block.text for block in source.requirements if block.kind == "reference"]
    if any(re.match(r"^\[\d+\]\s", text) for text in reference_texts):
        raise ValueError("Reference numbers must touch the following author text")

    document.core_properties.title = "云南工商学院毕业设计任务书"
    document.core_properties.subject = source.title
    document.core_properties.author = source.student_name.replace("　", "")
    document.core_properties.keywords = "错题分析；个性化推荐；检索增强生成；知识追踪"
    settings = document.settings._element
    zoom = settings.find(qn("w:zoom"))
    if zoom is None:
        zoom = OxmlElement("w:zoom")
        settings.insert(0, zoom)
    zoom.set(qn("w:percent"), "100")
    reorder_ooxml_properties(document)
    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(output)


def export_pdf(docx_path: Path, pdf_path: Path) -> None:
    soffice = shutil.which("soffice")
    if soffice is None:
        common = Path(r"C:\Program Files\LibreOffice\program\soffice.exe")
        if common.exists():
            soffice = str(common)
    if soffice is None:
        raise FileNotFoundError("LibreOffice soffice is required to export the task-book PDF")

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="task-book-pdf-") as temp_name:
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
            str(docx_path),
        ]
        subprocess.run(command, check=True, capture_output=True)
        generated = temp_dir / f"{docx_path.stem}.pdf"
        if not generated.exists():
            raise FileNotFoundError(generated)
        shutil.copy2(generated, pdf_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--docx", type=Path, default=DEFAULT_DOCX)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    args = parser.parse_args()
    source = parse_source(args.source.resolve())
    docx_path = args.docx.resolve()
    pdf_path = args.pdf.resolve()
    build_docx(source, docx_path, args.template.resolve())
    export_pdf(docx_path, pdf_path)
    print(f"DOCX: {docx_path}")
    print(f"PDF:  {pdf_path}")


if __name__ == "__main__":
    main()
