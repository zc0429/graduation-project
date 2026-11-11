# 业务流程图：导师审阅稿（2026-11-11，第三轮）

基于最新 `dev@6c667e0`，在 `codex/business-flow-review-20261111` / [PR #1](https://github.com/zc0429/graduation-project/pull/1) 修订。**尚待导师确认，未合并 dev。图3.3按导师目标业务表达，实现边界见配套审计表。**

## 直接审阅与打印

- [三页 A4 PDF](业务流程图-A4审阅版.pdf)：横向，按“实际大小／100%”打印。
- [三页可编辑 draw.io](业务流程图-三页可编辑.drawio)：原生节点、连接线、标签与泳道，非整页图片。
- [审计、原话追踪与修改报告](审计与修改报告.md)：18项需求、12组问题、代码实现边界及验证结论。
- [绘图口径与实现边界](需求复核与绘图规范.md)。
- [本次修改与逐页视觉复核](../../../validation/business-flow-review-20261111-r3/修改与视觉复核.md)。

| 图 | 可编辑源 | SVG | 300 dpi PNG | 单页 A4 PDF |
|---|---|---|---|---|
| 3.2 错题录入与AI分析 | [draw.io](01-错题录入与AI分析.drawio) | [SVG](01-错题录入与AI分析.svg) | [PNG](01-错题录入与AI分析.png) | [PDF](01-错题录入与AI分析.pdf) |
| 3.3 知识学习、练习与复习（目标） | [draw.io](02-学习练习与复习.drawio) | [SVG](02-学习练习与复习.svg) | [PNG](02-学习练习与复习.png) | [PDF](02-学习练习与复习.pdf) |
| 3.4 管理与学情查看 | [draw.io](03-管理与学情查看.drawio) | [SVG](03-管理与学情查看.svg) | [PNG](03-管理与学情查看.png) | [PDF](03-管理与学情查看.pdf) |

## 阅读说明

1. 图3.2将填写、图片辅助、补全与提交合在录入环节，未新增独立确认步骤；识图返回平台处理后回填，不自动保存正式错题。保存后平台准备分析上下文、处理和存储模型输出，再展示知识点与解析。失败保留已存数据。
2. 图3.3显式选择知识学习或做题练习，两类资源均先查平台。有资源直接复用；不足或未练题耗尽后请求模型。模型结果由平台校验、入库并关联，再给学生使用。阅读与实际作答分别处理，两者均可循环，复习完成需要单独确认。
3. 图面不使用实现状态符号、脚注或目标说明；知识内容生成/缓存、未练题筛选和耗尽后生成等目标与现有代码的差异统一记录在审计表中。成对B为标准同页连接点，承接生成失败后的继续／退出路径。
4. 图3.4只有一个开始和一个结束；当前登录角色决定进入管理员或教师路径，两者没有先后依赖，也不要求双方都完成后才能结束。
5. 生成批量、复习次数和日期、掌握度规则等参数留在论文详细设计；图内仅保留必要业务步骤。

## 复现与编辑

生成源为 [build_business_flow_review.py](../../../../scripts/documents/build_business_flow_review.py)，[JSON](业务流程图.json) 是同次生成的节点/路径清单。只改本审阅目录，不调用旧正式图稿生成器。

```bash
python scripts/documents/build_business_flow_review.py --export --drawio /path/to/drawio
python scripts/documents/validate_business_flow_review.py
```

依赖：Python（PyMuPDF、Pillow、fontTools、Playwright）、Chromium、draw.io desktop（本轮32.6.10），以及 Noto Serif CJK SC 常规/粗体字体。Linux验证脚本默认 `/usr/bin/chromium`。SVG使用标准文本并嵌入字体子集；PDF保留可渲染字形，PNG无需字体。draw.io编辑时建议安装完整的 [Noto CJK Serif字体](https://github.com/notofonts/noto-cjk)，并检查自定义折线和独立分支标签；SVG嵌入子集仅覆盖本稿文字，新增文字后须重新生成。字体授权见 [FONT-LICENSE.txt](FONT-LICENSE.txt)。

[第三轮验证目录](../../../validation/business-flow-review-20261111-r3/)保留本次修改前源图/PDF、文件哈希及修改后逐页渲染；[第二轮证据](../../../validation/business-flow-review-20261111-r2/)完整保留，包括会议来源、视频对照帧与历史检查结果。headless Electron在完成导出后以SIGILL退出，该环境问题如实记录在 [export-log.json](export-log.json)；全部交付文件另经解析、浏览器/PDF渲染及逐页检查，不据此声称交互式编辑保存或实体打印已经验收。

本轮未改已通过开题报告、正式论文插图、DFD、后端功能、原始实验与历史验证。导师审阅、实体打印和后续实现仍与本轮数字稿检查分开。
