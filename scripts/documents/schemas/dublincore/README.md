# 离线 XML 规范依赖

这些文件于 2026-09-21 从 Dublin Core 与 W3C 官方站点取得，内容未经修改；精确 URL 与 SHA256 见 `sources.json`，原文件中的来源、版权和说明保留。

`verify_docx_offline.py` 将原 OOXML XSD 的远程导入地址映射到这些本地文件，并校验 SHA256。未映射的网络地址会报错，不悄悄跳过；相对导入由本地目录解析。

运行仍需要本机 docx 技能提供的 OOXML 标准规范集；此目录仅补其外部依赖，不是全部 OOXML 规范。
