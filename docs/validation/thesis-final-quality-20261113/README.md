> **独立终稿审阅PR**：[Draft PR #9](https://github.com/zc0429/graduation-project/pull/9)，从PR #8派生，指向dev，不合并。

# 毕业论文终稿质量审查交付

本轮基于[Draft PR #8](https://github.com/zc0429/graduation-project/pull/8)最新提交`21da287744a252e7ccae0aadbe5832336c8b3b27`，独立分支`codex/thesis-final-quality-20261113`，目标`dev`，不合并PR。重点为论文语言、论证组织与最终排版；系统代码、已通过开题、学校材料、参考论文、历史验证和旧导出件均不修改。

完成九章与参考论文1、2027学校规范及模板、保留的导师要求和开题方案的逐项对照。发现的主要问题为审计口吻、重复限制说明、开发历史混入正文和截图版本表述含糊，共49处最小文字修订。没有为凑篇幅添加图表、代码或文献。九章、28图、26正文逻辑表、31段275行核心代码、27篇文献保持；99页PDF中正文85页，120个目录目的地已核对。

- [更新后的DOCX](../../../output/thesis/thesis-final-quality-20261113/毕业论文.docx)／[PDF](../../../output/thesis/thesis-final-quality-20261113/毕业论文.pdf)
- [逐章质量审查、规范对照及未完成边界](逐章质量审查.md)
- [问题分类与修改清单](修改清单.md)
- [49处修改前后对照](修改前后对照.md)／[机器可读JSON](修改前后对照.json)
- [28图、26表、31段代码及27篇文献逐项复核](图表代码文献逐项复核.md)
- [99页视觉复核](逐页视觉复核.md)／[逐页记录](visual-review.csv)／[25张校样](page-proofs/)
- [DOCX/PDF自动检查](document-check.json)／[终稿源稿检查及保护结果](quality-check.json)／[交付哈希](delivery-manifest.json)

本轮实际执行的是文档生成、页码回填、文档结构检查、代码摘录与引用核对、1130项既有文件保护校验及逐页渲染查看。未重新执行系统测试、未请求真实GLM；第8章沿用PR #8及明确标识的历史批次，不产生新的系统通过率。

已形成供导师内容审阅的版本。原字体Microsoft Word环境仍未验证；PDF采用合法替代字体。导师尚待确认的资源规则、当前知识讲解真实模型质量等已有边界保留。正式归档前应补原字体Word排版复核和本人学校提交手续，不将本轮称为导师终审通过。

## 可复现验证

需Python依赖`python-docx`、`lxml`、`Pillow`、`PyMuPDF`、`reportlab`、`fonttools`，以及`pdffonts`。PDF导出使用LibreOffice；本环境使用既有`graduation-thesis-tools:20261112`容器镜像和`scripts/cloud/fonts.conf`字体映射。不得把本轮环境文件或模型密钥提交仓库。

以下命令均从仓库根目录运行，始终显式设置新交付ID，避免旧脚本默认目录覆盖历史证据。`THESIS_SONG_FONT`与`THESIS_LATIN_FONT`需指向合法本地字体文件；它们影响封面等排版资源，PDF替代字体取决于LibreOffice环境。

```bash
export THESIS_DELIVERY_ID=thesis-final-quality-20261113
# 将下列Python路径换为装有上述依赖的环境；本轮路径如下。
.local/audit-venv/bin/python scripts/documents/build_thesis_delivery.py
scripts/cloud/export-thesis-pdf.sh
.local/audit-venv/bin/python scripts/documents/update_delivery_page_map.py
.local/audit-venv/bin/python scripts/documents/build_thesis_delivery.py
scripts/cloud/export-thesis-pdf.sh
.local/audit-venv/bin/python scripts/documents/validate_thesis_delivery.py
.local/audit-venv/bin/python scripts/documents/review_thesis_final_quality.py
.local/audit-venv/bin/python scripts/documents/render_thesis_audit.py
```

第1次生成用已保留页码映射；实际PDF提取后再生成并校验缓存稳定。重现文件字节可能受工具版本和时间元数据影响，应同时比较页数、目录、文本与图表，而非强求再次导出二进制哈希相同。原件保护检查则要求原文件字节一致。

日志保留`build-first.log`、`export-first.log`、`page-map-first.log`、`build-final.log`、`export-final.log`、`document-validation.log`、`quality-validation.log`及`render.log`；没有用空日志代替执行。人工检查结论另存，脚本不能自动认证视觉质量或学术质量。
