# 最少复现
已实测Windows、Python3.12.14、Node24.19.0、LibreOffice26.8.0.3。本轮是文档工作；业务运行要求仍以根README的JDK21/MySQL8/Node22为准。
工作目录：D:/Documents/GitHub/graduation-project-thesis-20260920。
Python和Node来自Codex bundled runtime；Python额外安装pymupdf、defusedxml到被忽略的.tools/python。其他所用库python-docx/lxml/Pillow由bundle提供；PPT使用bundle的@oai/artifact-tool。项目根node_modules是本机runtime的junction，不打包。
以下命令在本轮实际执行过同类调用；重新运行先确认产物无人工修改并备份。

```powershell
$runtime='C:/Users/can/.cache/codex-runtimes/codex-primary-runtime/dependencies'
$py="$runtime/python/python.exe"
$env:PYTHONUTF8='1'
$env:PYTHONPATH=(Resolve-Path '.tools/python').Path
& $py scripts/documents/build_thesis_review.py
$docSkill='C:/Users/can/.codex/plugins/cache/openai-primary-runtime/documents/26.909.12148/skills/documents'
$env:PATH="C:/Program Files/LibreOffice/program;$runtime/bin-overrides;$runtime/bin-fallbacks;"+$env:PATH
& $py "$docSkill/render_docx.py" output/docx/论文审阅版.docx --output_dir tmp/thesis-review-check --emit_pdf
```
复核新PDF后复制到output/pdf。若实际分页变化，按PDF标题大纲更新page-map.json并重建目录缓存；缓存只适用于对应版本，不盲目沿用。最终页码与字段检查：
```powershell
& $py scripts/documents/verify_thesis_review.py
```
这不是Word原生域更新，后续步骤见DOCUMENT-QA。验证器故障边界在其报告开头显式标注。
PPT避免覆盖最终化文件，先生成到新路径：
```powershell
$env:RUNTIME_NODE_MODULES="$runtime/node/node_modules"
$env:RUNTIME_NODE="$runtime/node/bin/node.exe"
$env:RUNTIME_BIN_DIR="$runtime/bin-fallbacks"
$env:DEFENSE_OUTPUT='tmp/defense-new/答辩审阅版.pptx'
& $env:RUNTIME_NODE scripts/documents/build_defense.mjs
$pptSkill='C:/Users/can/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations'
& $py "$pptSkill/container_tools/render_slides.py" tmp/defense-new/答辩审阅版.pptx --output_dir tmp/defense-new-render --width 1280 --height 720
```
各机技能/runtime路径可能不同，先用load_workspace_dependencies定位，不将这些绝对路径视为通用安装位置。必要时以当前用户本地配置建立node_modules junction；不下载/打包整个运行库。
通过新一轮内容、结构和逐页视觉检查后再替换交付件，并复制对应validation.json。历史基线检查脚本不能代替最终PDF/图片检查。
所有检查完成、已创建本地提交、工作区干净后：
```powershell
& $py scripts/documents/package_thesis_handoff.py
```
生成增量bundle与带SHA256清单的本地ZIP，脚本不上传文件。无需任何模型API Key或数据库凭据即可复现文档导出；真实演示另按DEMO-RUNBOOK。
