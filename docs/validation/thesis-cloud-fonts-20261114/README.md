# PR #9 云端原字体交付

**Windows云端方案已完成，PDF可编辑文字的原字体排版验证通过。** 本轮不修改论文正文，不需要用户本地运行Codex或Word。

- [原字体版DOCX](../../../output/thesis/thesis-windows-fonts-43541893783-1/毕业论文.docx)
- [原字体版正式PDF](../../../output/thesis/thesis-windows-fonts-43541893783-1/毕业论文.pdf)
- [字体验证报告与限制](字体验证报告.md)
- [成功的Windows运行](https://github.com/zc0429/graduation-project/actions/runs/43541893783)
- [原始Windows字体清单](../thesis-windows-fonts-43541893783-1/font-inventory.json)／[实际PDF字体](../thesis-windows-fonts-43541893783-1/actual-pdf-fonts.json)
- [取回后独立Poppler检查](independent-pdffonts.txt)／[独立字形检查](independent-pdf-fonts.json)
- [Windows文档检查](../thesis-windows-fonts-43541893783-1/document-check.json)／[样式及页码检查](../thesis-windows-fonts-43541893783-1/font-layout-check.json)
- [101页校样](../thesis-windows-fonts-43541893783-1/page-proofs/)／[逐页视觉记录](visual-review.csv)／[交付结论](delivery-result.json)
- [真实运行过程](windows-attempts.json)／[原件保护](protected-files-check.json)／[文件哈希](delivery-manifest.json)

本轮起点为PR #9的`0559bfbbac07f487da7f862662e6c167f1096459`，仍在`codex/thesis-final-quality-20261113`。成功生成源提交为`d117e1989b05921263f61d514b1b7456ff0d1d9b`。最终提交只增加交付、证据与交接说明，生成和验证脚本与成功运行版本一致。

最终PDF101页、正文87页，120目录目标经过两次导出稳定。原字体均实际使用并嵌入：SimSun 3363个文本span、SimHei 250个、Times New Roman 2799个；全部94个摘要与正文页码为9pt SimSun。计数是PDF文本片段，不是字符数或系统测试数量。

已查看全部26张四页校样，另放大PDF第1、10、59、60、72、98页，未发现新增裁切、重叠或异常分页；图表与代码沿用原内容。本轮未重复系统全面审计，不运行系统或GLM测试，不改开题、业务代码、学校原件、参考论文或历史证据，不合并PR。

## 在云端复现

可复用流程为[thesis-windows-fonts.yml](../../../.github/workflows/thesis-windows-fonts.yml)，在本PR分支推送相关排版脚本变更时运行；也可在上述成功运行页使用GitHub的重新运行功能。无需合并到dev，也无需用户本地运行程序。每次使用新的运行ID和attempt目录，不覆盖历史输出。

流程依次检查Windows系统字体；缺少黑体时安装微软官方`Language.Fonts.Hans~~~und-HANS~0.0.1.0`组件；安装经过校验的LibreOffice 25.2.3.2；生成DOCX并迭代导出PDF直至目录稳定；检查实际字体、嵌入元数据、英数字体、页码、文档完整性和版面边界；最后上传文档、校样与真实日志。字体文件本身不进入artifact或Git。

运行日志与成品在Actions中保留14天。本分支已经持久保存正式DOCX/PDF、关键报告和四页校样，不依赖临时artifact链接长期可用。101张原始120dpi PNG来自该artifact，SHA-256见[校样来源记录](proof-integrity.json)；这里不重复提交全部单页PNG。

## 仍存在的限制

本版由Windows上的LibreOffice生成，Microsoft Word引擎及纸质打印未验证。既有28幅图和历史截图是原样保留的栅格素材，图内字体不能由PDF文字字体检查认证；本轮没有重绘或改变历史截图。上述限制不改变已实际完成的PDF可编辑文字原字体验证，也不要求用户依赖本地电脑重新导出。

Windows方案成功，因此未启用Linux替代排版作为本轮成品；Linux现有字体状态不冒充Windows字体安装结果。上一轮字体受限预览和全部失败日志继续保留。
