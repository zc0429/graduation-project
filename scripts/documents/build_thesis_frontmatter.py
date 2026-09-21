"""Fill known author facts in the official cover/declaration; leave signatures blank."""
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}


def replace_text(node, value):
    texts = node.xpath('.//w:t', namespaces=NS)
    assert texts
    texts[0].text = value
    for text in texts[1:]:
        text.text = ''


def main():
    template = next((ROOT / 'docs/materials/27届毕业设计学校通知和模板').rglob('*内容资料.docx'))
    source = (ROOT / 'docs/thesis/毕业设计封面与诚信声明.md').read_text(encoding='utf-8')
    facts = dict(line.split('：', 1) for line in source.splitlines() if '：' in line)
    output = ROOT / 'output/docx/毕业设计封面与诚信声明-待签署.docx'
    with ZipFile(template) as original:
        tree = etree.fromstring(original.read('word/document.xml'))
        body = tree.find('w:body', NS)
        nodes = list(body)
        section = deepcopy(body.find('w:sectPr', NS))
        # The first page is the cover and the second is the declaration.
        assert ''.join(nodes[2].xpath('.//w:t/text()', namespaces=NS)) == '本科毕业论文（设计）'
        assert '诚信声明' in ''.join(nodes[12].xpath('.//w:t/text()', namespaces=NS))
        assert '任务书' in ''.join(nodes[32].xpath('.//w:t/text()', namespaces=NS))
        for node in nodes[30:]:
            body.remove(node)
        body.append(section)
        replace_text(nodes[2], facts['材料类型'])
        replace_text(nodes[5], facts['论文题目'])
        # Break at a phrase boundary rather than splitting 学习推荐 across lines.
        title_text=nodes[5].xpath('.//w:t', namespaces=NS)[0]
        first, last=facts['论文题目'].split('与学习推荐', 1)
        title_text.text=first
        title_text.addnext(etree.Element('{'+W+'}br'))
        second=etree.Element('{'+W+'}t');second.text='与学习推荐'+last
        title_text.getnext().addnext(second)
        # Printing instructions are not spacer rows: retaining empty paragraphs
        # here pushes the cover's date onto a separate otherwise blank page.
        body.remove(nodes[3])
        body.remove(nodes[6])
        rows = nodes[9].findall('w:tr', NS)
        for row, key in zip(rows, ['学院', '专业', '班级', '学号', '姓名', '指导教师', '授予学位']):
            replace_text(row.findall('w:tc', NS)[1], facts[key])
        replace_text(nodes[10], facts['完成年月'] or '年   月')
        replace_text(nodes[12], '毕业设计诚信声明')
        declaration = source.split('## 诚信声明\n\n', 1)[1].split('\n\n', 1)[0]
        assert declaration == ''.join(nodes[14].xpath('.//w:t/text()', namespaces=NS))
        replace_text(nodes[23], '作者签名：')
        # Preserve all unrelated template parts, fonts, spacing and the blank date.
        output.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(output, 'w', ZIP_DEFLATED) as target:
            for name in original.namelist():
                data = original.read(name)
                if name == 'word/document.xml':
                    data = etree.tostring(tree, xml_declaration=True, encoding='UTF-8', standalone=True)
                elif name == 'word/styles.xml':
                    styles=etree.fromstring(data)
                    order='name aliases basedOn next link autoRedefine hidden uiPriority semiHidden unhideWhenUsed qFormat locked personal personalCompose personalReply rsid pPr rPr tblPr trPr tcPr tblStylePr'.split()
                    rank={name:i for i,name in enumerate(order)}
                    for style in styles.findall('w:style',NS):
                        style[:]=sorted(style,key=lambda x:rank.get(etree.QName(x).localname,999))
                    data=etree.tostring(styles,xml_declaration=True,encoding='UTF-8',standalone=True)
                target.writestr(name, data)
    print(output)


if __name__ == '__main__':
    main()
