# 最少复现
已实测Windows、Python3.12.14、Node24.19.0、LibreOffice26.8.0.3。本轮是文档工作；业务运行要求仍以根README的JDK21/MySQL8/Node22为准。
工作目录：D:/Documents/GitHub/graduation-project-thesis-20260920。
Python和Node来自Codex bundled runtime；Python额外安装pymupdf、defusedxml到被忽略的.tools/python。其他所用库python-docx/lxml/Pillow由bundle提供；PPT使用bundle的@oai/artifact-tool。项目根node_modules是本机runtime的junction，不打包。
以下命令在本轮实际执行过同类调用；重新运行先确认产物无人工修改并备份。先用 `load_workspace_dependencies` 定位当前运行库；`$docSkill`、`$pptSkill` 分别填写本机 documents、presentations 技能的 SKILL.md 所在目录。下列路径变量须按本机结果赋值，不复制其他电脑的用户名或插件版本。

```powershell
$runtime='<本机 load_workspace_dependencies 返回的 dependencies 目录>'
$docSkill='<本机 documents 技能目录>'
$pptSkill='<本机 presentations 技能目录>'
$py="$runtime/python/python.exe"
$env:PYTHONUTF8='1'
$env:PYTHONPATH=(Resolve-Path '.tools/python').Path
& $py scripts/documents/build_thesis_review.py
$env:PATH="C:/Program Files/LibreOffice/program;$runtime/bin/override;$runtime/bin/fallback;"+$env:PATH
& $py "$docSkill/render_docx.py" output/docx/论文审阅版.docx --output_dir tmp/thesis-review-check --emit_pdf
```
复核新PDF后复制到output/pdf。若实际分页变化，按PDF标题大纲更新page-map.json并重建目录缓存；缓存只适用于对应版本，不盲目沿用。最终页码与字段检查：
```powershell
$env:DOCX_VALIDATOR_DIR=Join-Path $env:USERPROFILE '.agents/skills/docx/scripts/office'
& $py scripts/documents/verify_thesis_review.py
```
校验器默认查找当前用户的 `~/.agents/skills/docx/scripts/office`；如技能安装在别处，设置 `DOCX_VALIDATOR_DIR` 指向含 `validators/` 的目录。目录不存在时会在写入审计记录前报错。这不是Word原生域更新，后续步骤见DOCUMENT-QA。标准规范现由 verify_docx_offline.py 使用 scripts/documents/schemas/dublincore 固定的官方文件离线解析，25标准XSD通过；WPS私有数据仅作包检查。可另运行 `& $py scripts/documents/verify_docx_offline.py` 查看逐部件结果。
PPT避免覆盖最终化文件，先生成到新路径：
```powershell
$env:RUNTIME_NODE_MODULES="$runtime/node/node_modules"
$env:RUNTIME_NODE="$runtime/node/bin/node.exe"
$env:RUNTIME_BIN_DIR="$runtime/bin/fallback"
$env:PRESENTATIONS_SKILL_DIR=$pptSkill
$env:RUNTIME_PYTHON=$py
$env:DEFENSE_OUTPUT='tmp/defense-new/答辩审阅版.pptx'
& $env:RUNTIME_NODE scripts/documents/build_defense.mjs
& $py "$pptSkill/container_tools/render_slides.py" tmp/defense-new/答辩审阅版.pptx --output_dir tmp/defense-new-render --width 1280 --height 720
```
答辩生成器必须显式提供 `PRESENTATIONS_SKILL_DIR` 和 `RUNTIME_PYTHON`，缺少配置或路径无效会在创建输出前报错。必要时以当前用户本地配置建立node_modules junction，让 Node 能解析 `@oai/artifact-tool`；不下载/打包整个运行库。跨平台时同时采用本机 Node/Python 可执行文件路径，以上命令为 PowerShell/Windows 示例。
通过新一轮内容、结构和逐页视觉检查后再替换交付件，并复制对应validation.json。历史基线检查脚本不能代替最终PDF/图片检查。
所有检查完成、已创建本地提交、工作区干净后：
```powershell
& $py scripts/documents/package_thesis_handoff.py
```
生成增量bundle与带SHA256清单的本地ZIP，脚本不上传文件。无需任何模型API Key或数据库凭据即可复现文档导出；真实演示另按DEMO-RUNBOOK。
