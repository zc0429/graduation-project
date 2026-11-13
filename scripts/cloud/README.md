# Cloud复现

当前交付为`output/thesis/thesis-audit-20261112/`，从PR #5的`ed7d94c`继续审计；历史图和旧导出目录保持原样。以下命令只生成当前审计产物。最终须实际查看全部页面；机器校验不会自动认证视觉质量。更换字体或正文后应再次更新页码映射并校验，直到映射稳定。

本轮系统为Debian 13，无sudo。`./scripts/cloud/setup-thesis-tools.sh`优先使用可用的系统包管理权限，否则构建独立Debian排版工具容器，将合法开源字体复制到用户字体目录；不会复制Windows字体。安装Noto CJK、Liberation、AR PL UMing、fontconfig、LibreOffice Writer及Poppler。字体许可随系统包保留。

```bash
./scripts/cloud/setup-thesis-tools.sh
source .local/thesis-fonts.env
fc-list
fc-match 'AR PL UMing CN'
FONTCONFIG_FILE="$PWD/scripts/cloud/fonts.conf" fc-match '宋体'
FONTCONFIG_FILE="$PWD/scripts/cloud/fonts.conf" fc-match 'Times New Roman'
python scripts/documents/validate_thesis_references.py
python scripts/documents/audit_current_thesis.py
python scripts/documents/build_audited_business_flow.py
python scripts/documents/build_thesis_delivery.py
./scripts/cloud/export-thesis-pdf.sh
python scripts/documents/update_delivery_page_map.py
python scripts/documents/build_thesis_delivery.py
./scripts/cloud/export-thesis-pdf.sh
python scripts/documents/validate_thesis_delivery.py
python scripts/documents/render_thesis_audit.py
```

`THESIS_SONG_FONT`实际为AR PL UMing TrueType轮廓TTC，兼容ReportLab；`THESIS_LATIN_FONT`为Liberation Serif。DOCX样式仍写学校要求的宋体、黑体和Times New Roman；PDF由fonts.conf明确映射到Noto Serif/Sans CJK SC与Liberation Serif。替代字体可用不代表原版宋体或Times New Roman已安装。原版字体最终核验在合法具备这些字体的环境完成。

构建依赖Python的python-docx、lxml、Pillow、PyMuPDF、reportlab、fonttools、playwright；建议独立venv安装，本文档不复制第三方字体到仓库。Docker的vfs存储会产生较多副本，应为排版容器预留至少2GB空间；不要同时保留无需继续运行的临时测试数据库容器。只清理本轮可重建工具缓存，不删除原始导师材料或验证证据。

本轮Java 21运行时包含编译器模块但缺少ct.sym，Maven使用`-Dmaven.compiler.release= -Dmaven.compiler.source=21 -Dmaven.compiler.target=21`完成编译与测试；完整JDK 21环境直接使用常规`./mvnw test`即可。代理设置写入被忽略的`.local/maven-settings.xml`，数据库密码写入本地环境，均不得提交。前端测试使用`npm run test:unit -- --maxWorkers=2`避免云端并行内存过量。浏览器可设`PLAYWRIGHT_CHROMIUM_EXECUTABLE=/usr/bin/chromium`使用Cloud现有Chromium，不影响Windows默认Playwright安装。
