# 图表边框修复与终稿微调交付

在 PR #9 原分支 `codex/thesis-final-quality-20261113` 继续工作，基线为 `d74c52b555fb16341eba6e5e4af15d1bd9571f63`。本轮修复图表生成及指定表格显示，不改论文正文源稿、参考文献源稿、系统业务、开题或历史证据，不合并任何 PR。

- [最新 DOCX](../../../output/thesis/thesis-windows-fonts-43576840299-1/毕业论文.docx) / [最新 PDF](../../../output/thesis/thesis-windows-fonts-43576840299-1/毕业论文.pdf)
- [修改前后清单](修改清单.md) / [视觉复核说明](视觉复核.md) / [逐页记录](visual-review.csv) / [图表实际页码](图表页码索引.csv)
- [Windows 成功运行 43576840299](https://github.com/zc0429/graduation-project/actions/runs/43576840299)，导出源提交 `c18cc911f153a626ece88e549398b7c852d9dc54`；[Draft PR #9](https://github.com/zc0429/graduation-project/pull/9)。

## 修复及验证结果

20 张图从保留的原始 SVG / 场景 JSON 重建。泳道图旧视窗从 x=58 开始，而真实左框位于 x≈53.896，故原资产已截掉左边框；在 Word 中加白边不能恢复这条线。本轮按完整 SVG 几何范围重新计算视窗，仅移除图内标题，保留节点、标签与连线。三张泳道外框闭合，统一 1.6 SVG 单位线宽。所有新图四周保留 24 SVG 单位白边，以 4 倍分辨率输出；原生 PNG 实测白边最少 92px。取消文档嵌图阶段按非白像素紧裁的逻辑，原截图也完整嵌入。

图 6.5 的 `«interface» LlmClient` 使用可正确显示拉丁符号的字体；两条实现关系采用矢量空心三角，虚线接到三角底边，箭头尖端接到接口框。没有用字符模拟箭头。图 5.6 的完整文字几何范围纳入视窗，顶部“每日 08:00 扫描”完整保留。DFD 数据存储采用统一左封口、右开口框，横线右端完整留白。

专项检查覆盖 117 个可见矩形的四边和三张泳道外围框。20 张图在 DOCX 中的像素与新源 PNG 完全一致，无 `srcRect` 裁剪。Windows 最终 PDF 内嵌图实测四周白边最少 **28px**；图像均在实际页面内。详见 [专项自动检查](../thesis-windows-fonts-43576840299-1/border-polish-check.json)、[生成资产与来源哈希](../../thesis/border-polish-20261114/figures/manifest.json) 及 [实际旧图/新图对照](图表修复前后记录.json)。

表 6.13 三处 `DELETE` 均为单行完整单词且位于方法列；表 6.4 三处 `CURRENT_TIMESTAMP` 完整且位于约束列；表 8.7 的三个指定接口分隔顿号均可从最终 PDF 提取；附录代码 7.25/7.26 的 `LearningResources.vue` 完整。文献 [1]/[17] 作者后句点及 [21] 双破折号通过 PDF 核验。原 Markdown 中这些标点和 SQL 字符串本已正确，本轮没有为产生差异重复改写。

## 最终版面与字体

Windows 2022 云端用真实 SimSun、SimHei、Times New Roman 和代码 Courier New 导出，两次导出后 **177 个目录目标**稳定（主目录 120 项，图表目录 57 项）。PDF **101 页、全部纵向 A4**，主目录 3 页，敏感词命中 0。28 图、正文 27 张逻辑表、附录 2 表、31 段 275 行真实代码及 27 篇参考文献保留。代码片段逐段精确比对通过，跨页表题/重复表头等既有检查通过。

相对于基线 100 页，安全留白恢复后自然重排增加 1 页，没有添加正文。图 5.6 现为正文第 35 页，图 6.5 为正文第 49 页；表 6.13 为正文第 52–54 页，表 8.7 为第 86 页，附录索引续表为第 93 页。以新目录和本轮页码 CSV 为准，不沿用用户所见旧版页码定位。

实际 PDF 文本使用 SimSun 3524 段、SimHei 405 段、Times New Roman 2800 段、Courier New 323 段，9 个字体子集均嵌入；中文、英数字及页码字体检查错误均为 0。可查 [嵌入字体身份与使用检查](../thesis-windows-fonts-43576840299-1/actual-pdf-fonts.json)、[独立 Poppler 字体清单](pdf-fonts-poppler.txt)、[总版式检查](../thesis-windows-fonts-43576840299-1/master-final-check.json)。未将受限制字体文件导出或提交。

本轮逐张查看了 28 个受影响实际 PDF 页的 300dpi 渲染和七张整页索引图，并放大核查三张泳道图、状态图和类图。该范围覆盖全部 20 张修复图、指定表格及文献页；不声称本轮人工重审全部 101 页。全部 101 页接受自动页面方向、目录、字体、敏感词、表格及代码检查。

## 保留范围与限制

[1615 项既有文件 SHA-256 校验](protected-final-check.json) 全部不变，包括论文正文及文献源稿、学校模板、已通过开题、历史实验/测试和上轮 DOCX/PDF。11 表 88 字段、39 接口与代码索引未改；本轮未重跑系统/GLM 测试，也未把旧测试计作新成果。AGENTS、交接和进度记录只新增本轮交付入口。

**Microsoft Word 引擎与纸质打印仍未验证。**正文、标题、页码原字体已在 Windows LibreOffice 导出结果中验证；新图内中文仍使用 Noto Serif CJK SC，英数字使用 Times New Roman，栅格图内宋体/黑体未认证，不能据正文原字体通过宣称全图也是学校原字体。该限制单独保留，不影响本轮边框完整性结论。

## 日志与复现

1. 在本分支运行 `scripts/documents/build_thesis_border_figures.py` 重建 20 图；需要 Playwright/Chromium、Pillow 及已记录的图内字体。用 `scripts/documents/check_thesis_border_polish.py --figures-only` 检查原生图。
2. 使用既有 `Thesis Windows original fonts` 工作流在本分支导出。其 Windows PowerShell 入口检查原字体、通过微软官方 Hans 可选字体安装缺失黑体、安装固定 LibreOffice 版本，运行生成器并更新域、稳定页码。
3. 工作流执行常规文档、字体、Master Final 及本轮专项检查，自动保存受影响实际页 300dpi PNG。交付运行已实测成功；重新运行会生成独立运行编号目录。
4. 查看 [原始命令记录](../thesis-windows-fonts-43576840299-1/commands.jsonl)、[Windows 原始日志](windows-job.log)、[运行产物元数据](artifact.json)、[校验摘要](交付自检摘要.json)。下载 ZIP 的 SHA-256 为 `b219f1bd80ca505f86ec1052562e5e91b4fc32023187cb0ff99507092b6b560e`，与 GitHub 产物 digest 一致。

Linux 预检记录在 [linux-preflight](linux-preflight/)，只作为字体受限预检，正式交付来自 Windows 成功运行。预检曾把透明标签命中框误计为可见边框、把名义正文边距误作实际页界，均已修正检查器后重跑；曾试验字符缩进解释后撤回，最终段落格式保持基线。这些诊断日志保留，不写入论文。Windows 产物原始日志/JSON/CSV 保留原字节；CI 当时的 `manual_visual_review_completed=false` 表示 CI 不执行人工视觉检查，本轮后续复核另见本目录记录。

保留 28 个受影响页的完整 300dpi PNG 和全部 101 页整页缩略索引。冗余的 101 张 120dpi 整页图保留在执行环境和原始 Actions ZIP 中，不重复入库。
