# 2026-11-17论文截图回放工具

只用于已授权的隔离截图库，不改变业务源码或历史GLM证据。实际系统基线、输入、输出与SQL例外见 `docs/validation/thesis-screenshots-20261117/README.md`。

- `archive_replay.py`：仅监听127.0.0.1:8091，回放仓库真实GLM留档；未知任务失败，不发起外部请求。
- `prepare_history.py`：从当前学生空题库起执行真实API流程。拒绝覆盖现有历史；固定场景日为2026-11-17，不能在其它日期不加调整直接重跑。
- `capture.mjs`：实际登录UI，DPR2截图。包含一次错误作答，会改变练习记录及掌握度，不是只读脚本，不应重复执行现有库。
- `capture_report_regions.mjs`：补充报告区域截图，原完整截图另存；保持像素比例，不改UI数据。
- `verify_history.py`：数据库/接口/原始档案交叉核对，生成业务来源记录。周报告随系统日期变化，现有记录对应截图当日。
- `install_captures.py`：校验候选SHA后安装八张已审阅图，更新provenance/manifest，保留历史原图。
- `check_delivery.py`：对指定 `THESIS_DELIVERY_ID` 导出的DOCX/PDF核对八图像素、裁切、来源哈希、正文允许改动、表格底色和受保护原件；Linux替代字体预演另设 `THESIS_ALLOW_SUBSTITUTE_PREVIEW=1`。

本地账号和数据库配置位于忽略的 `.local/thesis-screenshots-20261117/`，不入库。实际运行使用前端4175、后端8080、MySQL3307；后端GLM基础URL指向本地回放器，不设置真实密钥。完整脚本顺序为准备、首次截图、报告区域截图、数据回读核验、安装、文档导出与校验；不要用截图脚本反复改变已验收数据。
