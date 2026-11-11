# 业务流程图第三轮证据

本目录对应用户要求精简图面并修复箭头的一轮修订。最终结论见[修改与视觉复核](修改与视觉复核.md)。

- `before.drawio` / `before.pdf`：修改前的三页图；`before-hashes.json`：修改前全部跟踪文件的SHA256。
- `after-pdf-1.png`—`3.png`：最终PDF逐页160dpi渲染。
- `after-svg-1.png`—`3.png`：最终SVG在浏览器中的实际渲染。
- `detail-*.png`：从交付300dpi PNG截取的分支细节，用于检查箭头，不替代整页验证。
- `final-checks.json`：结构、实际SVG线段/箭头、字形边界与交付文件哈希。
- `roundtrip-checks.json`：原生draw.io重新导出XML的数据保持检查。
- `preservation-checks.json`：历史证据、代码和无关文件保护回查。

上一轮证据目录保持原样；新图的验证不得覆盖或借用旧图的通过结论。
