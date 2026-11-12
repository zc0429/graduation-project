# 第3章需求分析审阅包

本包基于 `dev@6c667e0`，用于阶段一需求审阅，不是已完成全部目标功能的终稿。

- [第3章独立阅读稿](第3章-需求分析审阅稿.md)与[完整论文](../毕业论文.md)中的第3章同源。
- [审计、九章映射与实施顺序](../../notes/毕设审计与实施顺序-20261112.md)。
- [需求实现与验收追踪](需求实现与验收追踪.md)区分已有能力、目标缺口与待执行验证。
- 图3.2—3.4：[业务图A4 PDF](business-flow/业务流程图-A4审阅版.pdf)、[三页可编辑源文件](business-flow/业务流程图-三页可编辑.drawio)。精确复制PR #1的 `d72b382` 候选，不代表合并或导师确认。
- 图3.1及3.5—3.9：[用例与DFD图册](figures/需求分析图册-A4.pdf)，同目录保留各页原生draw.io、嵌入字体SVG、300dpi PNG及A4 PDF。
- [本轮验证记录](../../validation/requirements-20261112/README.md)包含逐页观察、截图、接口平衡、原文件保护与业务图来源哈希。

## 图形约定

业务图沿用导师要求的黑白泳道图。用例图使用参与者、系统边界和用例椭圆，关联线不表示先后关系。DFD使用外部实体矩形、加工椭圆和双横线数据存储，箭头只表示有名称的数据传递。

0层分图3.6、3.7，P4的1层分图3.8、3.9；每组两幅共同构成一层，相同数据存储编号指同一对象，不是复制的数据库表。图中D4包含尚未实现的知识内容目标，详细边界见正文与追踪表。共有参与者按接口字段和角色权限分配；合并绘制不赋予管理员报告权限或教师维护权限。

图中文字采用可嵌入的思源宋体同系 Noto Serif CJK SC，许可证见同目录FONT-LICENSE.txt。它用于独立图形可移植显示，不等同于学校正式论文的宋体/Times New Roman排版验收。

## 重建和跨端阅读

Python需要PyMuPDF、fontTools和Playwright，系统安装Noto Serif CJK字体、Chromium及draw.io Desktop。构建命令：

```sh
python scripts/documents/build_requirements_review.py --drawio /path/to/drawio
python scripts/documents/validate_requirements_review.py
```

脚本从仓库根定位路径，验证脚本的Chromium路径为Linux环境值，Windows可直接使用导出的PDF/SVG和原生draw.io，重新验证时通过 `--chromium` 指定浏览器可执行路径。draw.io文件使用真正节点及端点关联，不是整页图片；本轮通过官方命令行读取导出，未据此宣称完成桌面GUI手动编辑保存验收。
