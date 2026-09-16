# 论文图表源与导出

对应正文：[毕业论文.md](../毕业论文.md)。审计及证据索引：[论文图表审计与事实基线](../../notes/论文图表审计与事实基线.md)。

| 文件 | 用途 |
|---|---|
| `sources/*.json` | 17 张图的权威可维护源，含文字、坐标、连线、图题元数据和代码证据；截图含原图路径及裁切区域 |
| `svg/*.svg` | 标准 SVG 导入源；设计图是文本和矢量基本图形，截图图版内嵌原 PNG |
| `png/*.png` | 300 dpi 论文插图；没有图题，正文独立编号 |
| `../../../output/pdf/thesis-figures/*.pdf` | 每图独立 PDF 及 34 页 A4 图表校样 |
| `manifest.json` | 逐图证据、尺寸、截图坐标与原始 SHA-256 |
| `fact-baseline.json` | 10 表 80 字段、36 接口及权限、15 个视图组件、人工实验复算结果 |
| `verification.json` | 图表编号、链接、Schema/接口集合、截图哈希等检查结果 |

```powershell
python -X utf8 scripts/documents/build_thesis_figures.py
python -X utf8 scripts/documents/audit_thesis_figures.py
```

从仓库根目录执行，依赖 `reportlab`、`pymupdf`、`Pillow`。默认字体为 Windows 宋体和 Times New Roman；其他平台需设置 `THESIS_SONG_FONT` 和 `THESIS_LATIN_FONT` 指向合法字体文件。字体不复制入库。修改时直接编辑 JSON，构建器不会覆写源文件。截图裁切用于图版布局，原图始终在 `../screenshots/real-glm/` 保留。

设计图以 157.5 mm 宽使用时标注 9 pt；表格校样为五号 10.5 pt、三线表，表 5.11 续页。PNG/SVG/PDF 本身不包含图题；`caption` 仅供正文和独立 A4 校样排版。图源尺寸变更后必须重新目检，不能仅凭脚本通过认定视觉无误。

Visio 状态：本机未注册 Microsoft Visio，尚未实际导入 SVG，也未生成 `.vsdx`。标准 SVG 已通过 XML 及图形渲染检查，不能据此宣称 Visio 实开或原生图元转换已通过。后续可在安装 Visio 的机器上导入并核验文字、箭头和截图裁切，再另存 `.vsdx`。

SVG 截图文件内含完整的原始图片数据，裁切并非脱敏。当前选用的原图经目检只含受控演示信息；如将来原图包含敏感数据，必须先获得真实脱敏副本再制作图版，不能只用裁切遮挡后对外分享。

原始 Gate5 数据与人工评分未修改；原自动摘要的“待评”为历史状态，论文表 6.3 依据人工 CSV 与既有解盲键。所有历史业务测试结果注明日期，本轮只执行图表与证据一致性检查。
