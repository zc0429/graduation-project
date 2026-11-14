# Draft PR #9 字体与排版续审交付

在[Draft PR #9](https://github.com/zc0429/graduation-project/pull/9)原分支继续，起点`e211f65552eda38634cf98aeb359d7f74a4a9403`。字体规范按用户本轮确认直接执行，不再推测或请求确认。

**已完成DOCX字体/样式修复及受限环境预览复核；尚未完成宋体、黑体及Microsoft Word原环境终验。** Times New Roman已合法安装并验证实际用于PDF；当前仍缺少可验证授权的SimSun、SimHei字体包，因此正式PDF导出默认被阻止，交付PDF明确命名为“字体受限预览”。

- [更新后的DOCX](../../../output/thesis/thesis-font-layout-20261113/毕业论文.docx)
- [字体受限预览PDF](../../../output/thesis/thesis-font-layout-20261113/毕业论文-字体受限预览.pdf)
- [字体环境排查、合法来源与验证范围](字体环境排查与验证范围.md)
- [修改前后对照与问题清单](排版修改前后对照.md)
- [逐章最终对照与视觉复核](逐章最终对照与视觉复核.md)
- [实际样式及PDF字形检查](font-layout-check.json)／[常规文档检查](document-check.json)
- [原字体缺失检查](original-font-probe.json)／[Times New Roman安装记录](times-new-roman-installation.json)
- [实际渲染PDF字体检查](pdf-font-render-check.json)／[最终执行状态](final-checks.json)
- [112项图表代码文献最终页码索引](图表代码文献页码索引.csv)
- [逐页校样](page-proofs/)／[逐页视觉记录](visual-review.csv)／[文件哈希](delivery-manifest.json)
- [最终PDF与已审校样的101页像素一致性](visual-proof-integrity.json)

最终预览101页、九章正文87页，120个目录目的地、28图、26张正文逻辑表、31段275行核心代码及27篇文献。正文源稿与本轮起点逐字节一致，论文语言沿用上一轮49处修订；开题、系统业务代码、原始材料、历史实验、测试证据及旧输出均不修改。只更新排版生成/核验工具与新交付，不重跑或累计系统测试，不合并PR。

## 复现

Python环境需安装`python-docx`、`lxml`、`Pillow`、`PyMuPDF`、`fonttools`、`brotli`；另需`fontconfig`、`pdffonts`。本轮使用已有Docker镜像`graduation-thesis-tools:20261112`中的LibreOffice 25.2.3.2。字体安装与许可来源见专项报告；字体文件不提交Git。

```bash
export THESIS_DELIVERY_ID=thesis-font-layout-20261113
export THESIS_PYTHON="$PWD/.local/audit-venv/bin/python"
export THESIS_PDF_BACKEND=docker
export THESIS_FONT_DIR=/home/agent/.local/share/fonts/graduation-originals

# 正式模式：未安装全部原字体时以退出码2停止，不生成正式PDF。
scripts/cloud/export-thesis-pdf.sh
```

以下命令仅生成明确标记的受限预览，不代表取得宋体、黑体或Word排版验收：

```bash
export THESIS_ALLOW_SUBSTITUTE_PREVIEW=1
"$THESIS_PYTHON" scripts/documents/build_thesis_delivery.py
scripts/cloud/export-thesis-pdf.sh
"$THESIS_PYTHON" scripts/documents/update_delivery_page_map.py
"$THESIS_PYTHON" scripts/documents/build_thesis_delivery.py
scripts/cloud/export-thesis-pdf.sh
"$THESIS_PYTHON" scripts/documents/validate_thesis_delivery.py
"$THESIS_PYTHON" scripts/documents/audit_thesis_font_layout.py
"$THESIS_PYTHON" scripts/documents/render_thesis_audit.py
```

所有本轮目录均为新路径。`build-final.log`、`export-final.log`、`page-map-final.log`、`document-validation.log`、`font-layout-validation.log`、`render.log`记录最终执行；`formal-export-blocked.log`保留正式导出被正确阻止的记录。字体工具首轮缺Brotli、核验脚本首轮误把目录当作章标题、页码索引初次将正文引用计入题注的问题及修正也分别保留日志，不冒称首次全部通过。

正式归档应在具备合法宋体、黑体、Times New Roman与Microsoft Word的环境中打开DOCX，更新全部域，重新检查目录页码、分页、校徽、图表及引用后导出。若使用云端，字体授权须覆盖该环境。字体规范本身已经确认，未验证事项是安装与真实渲染环境。
