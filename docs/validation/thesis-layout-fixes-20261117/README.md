# 论文三项版式修复（2026-11-17）

分支 `claude/thesis-voice-cleanup-20261117`；基线 `6aedd02c03771bf3e376ab07f63ca9f9609f7f1b`；实现提交 `d137919a91a44fc2e766b7cb00c533d2f5cdd0b2`。Draft PR #10 保持草稿，不合并。

## 修改

以仓库 `docs/materials/参考论文/论文正文/参考论文1.pdf` 为对照，只改导出层与四张图源。

- 三个目录均用中文黑体、英文数字 Times New Roman。主目录章条目及点线、页码为 14 磅；其他条目为 12 磅。表目录、图目录缓存采用 TOC 2，隐藏 TC 条目也改为二级，避免 Word 更新域后回退为 TOC 1 的 14 磅。
- 图 3.6、3.7、3.8、3.9 分别补闭 6、7、5、4 个存储符号，共 22 个。此分支原 `final-master` 目录没有这四份 SVG，现从已提交的完整 SVG 提取为独立图源，再只替换存储框；其他节点、连线、文字、画布尺寸均保留。构建器为这四图读取新图源，新增 `--figures` 参数，支持只更新指定图及其 manifest 条目。其余 16 图及对应 manifest 记录逐字节不变。
- Thesis Code 改为宋体／Times New Roman 10.5 磅、固定 15 磅行距、无底纹；首段上边框、各段左右边框、末段下边框拼成黑色闭合框。保留每条原始代码文本及前导空格，长行自动折行时续行沿用原行缩进。
- 同步 Windows PDF 字体校验、字体版式审计与终稿检查。移除不再使用的 Courier New 字体要求及代码区字体豁免；英文数字统一接受 Times New Roman。新增目录直接格式检查，以及每段代码边框位置和无底纹检查，保留原有源码、正文、分页与图表校验。

正文 `docs/thesis/毕业论文.md` SHA-256 保持 `1dea4d2f0b167f8aa453735c2495936468870d31088644cb07bc1e63d1472937`。21 段代码、237 个代码段落（含省略标记与空行）、28 图、29 表、27 篇文献不变。实现提交中仅 14 个既有导出脚本／派生图文件有变化，新增四个 SVG；其余 1794 个既有文件未变。开题、业务代码与历史验证材料未改。

## 本地预演

Linux 使用 Noto Serif CJK SC、Noto Sans CJK SC、Liberation Serif 作为明确标注的预览替代字体。为避开母版内不完整的嵌入黑体子集，临时渲染副本移除了嵌入字体引用；交付 DOCX 保留母版包部件。本地预览为 98 页，仅作预演，不作为正式页数。

- `build_thesis_border_figures.py --figures 3.6 3.7 3.8 3.9`：通过。
- `check_thesis_border_polish.py --figures-only`：通过；20 图、139 个矩形、最小原图白边 92 px。
- 完整导出两次后 177 个目录目标稳定。
- `validate_thesis_delivery.py`、`check_thesis_master_final.py`、完整 `check_thesis_border_polish.py`：通过。
- `audit_thesis_font_layout.py`：DOCX 样式、177 条目录直接格式及 237 行代码核对通过；在 PDF 必须实际使用 Times New Roman 的断言处停止，符合本地缺原字体的环境事实。未放宽该断言，正式结果以 Windows 为准。
- 另按实际 PDF 文字与绘图指令核查 177 条目录字号、21 个无底纹闭合代码框与完整代码字符，均通过。

本地结果与范围核对见 `scope-and-local-checks.json`、`local-preview/`。

## Windows 正式导出

运行 [Thesis Windows original fonts #13](https://github.com/zc0429/graduation-project/actions/runs/44067465137)，源提交 `d137919`。**Success**，总耗时 5 分 42 秒；artifact `thesis-windows-fonts-44067465137-1`（ID `14320549105`）。

- 新正式 DOCX 对应 Windows 导出的 PDF 为 **100 页**，全纵向 A4；主目录 3 页、表目录 1 页、图目录 1 页。
- SimSun／SimHei／Times New Roman 均实际使用并嵌入。未知字体、中文字体、英文数字字体、页码字体四类错误分别为 **0／0／0／0**；Courier New 不再作为代码字体，也不再要求其实际出现。
- 177 个目录目标经 2 次导出稳定。`validate_thesis_delivery` 中的 120 指主目录，另含 57 个表／图目录目标，合计 177。
- `validate_thesis_delivery.py`、`audit_thesis_font_layout.py`、`check_thesis_master_final.py`、`check_thesis_border_polish.py` 全部通过；页界错误 0，保护文件变化 0，源稿哈希不变。
- 追加核对正式 PDF 的 177 条目录字号、21 个代码框的四边连续性、10.5 磅字号、无底纹及代码字符完整性，全部通过。24 个受影响页面的六张校样已逐张目视检查，未见裁切、框线中断或文字丢失。见 `actual-layout-check.json`、`visual-proofs/`；未宣称此次重看全部 100 页。

正式交付：

- [毕业论文.docx](../../../output/thesis/thesis-windows-fonts-44067465137-1/毕业论文.docx)，SHA-256 `07cb64e4845d8de0dea9a6f4d53665d8e5bed165971b7aab5763bd28ba47be84`。
- [毕业论文.pdf](../../../output/thesis/thesis-windows-fonts-44067465137-1/毕业论文.pdf)，SHA-256 `6daa233cb24ae69a66431348f4fd51445c9cc3aba145cc138733c1de192240fa`。
- [Windows 原始报告与日志](../thesis-windows-fonts-44067465137-1/)，保留 Windows JSON/日志/页码索引（入库文本只统一换行与行尾空白）；完整 100 页预览及 300 dpi 图表校样见 [Actions artifact](https://github.com/zc0429/graduation-project/actions/runs/44067465137/artifacts/14320549105)（平台保留至 2026-12-01）。原始 ZIP SHA-256：`a29007e1f00ff7e8f9b3f1034bd4adb54e437213aa6a1c603c48069df71e8ae4`，DOCX/PDF 入库字节与原始包完全相同。

本次页数以 Windows LibreOffice 25.2.3.2 从该 DOCX 实际导出的 PDF 为准；未经 Microsoft Word 引擎或纸质打印核验，图内 Noto 栅格字体沿用原流程。
