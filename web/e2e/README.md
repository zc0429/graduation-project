# 前端自动化验收

自动化分为三层，避免把固定测试数据、真实后端联调和论文截图混为一谈。

## 1. 路由 Mock 界面测试

`npm run e2e:smoke` 使用固定 API 夹具覆盖三角色业务流程与四档响应式视口，
不连接数据库，也不调用真实模型。

`npm run e2e:browsers` 在 Chrome Stable 与 Edge Stable 执行完整桌面套件，
并在 Firefox 执行关键流程烟测。

## 2. 独立数据库联调

`npm run e2e:integration` 只允许连接数据库名精确为 `wrongbook_e2e`、且
`LLM_PROVIDER=mock` 的后端。启动、数据重建和安全检查步骤见 `web/README.md`。
该流程验证真实 API、JWT Axios Blob 导出及三角色边界，不调用真实 GLM。

## 3. 设计证据截图

`npm run e2e:screenshots` 使用 Mock API 生成桌面、平板和手机截图，输出到
`docs/design/vue-rebuild-screenshots/`。每张图片都会显示
“Mock 演示数据 · 非真实 GLM 证据”，且不会写入 `docs/thesis/screenshots/`。

论文最终截图必须在后续真实 GLM 验证完成后单独生成，不得复用本目录的
Mock 设计证据。

## 4. 真实 GLM 浏览器证据

`npm run e2e:real-ai` 是独立的 opt-in 流程。默认未设置
`RUN_REAL_AI_E2E=true` 时整套用例跳过，不会启动前端、连接后端或调用模型。
执行前必须人工确认 8080 端口运行的是 `glm-4.7-flash + embedding-3 / 1024`
后端，并通过进程环境临时注入演示学生密码与种子角色密码；密码不得写入
仓库或验证文档。

```powershell
$env:RUN_REAL_AI_E2E = 'true'
$env:REAL_AI_E2E_PASSWORD = Read-Host '正式证据学生密码' -MaskInput
$env:REAL_AI_E2E_SEED_PASSWORD = Read-Host '本地种子角色密码' -MaskInput
npm run e2e:real-ai
```

该流程使用独立正式证据学生，准备一条同账号真实向量参考题，再从浏览器完成
目标错题录入、真实 GLM 分析、RAG 引用、相似题、3 道真实变式题、一次练习
与掌握度更新，并访问复习、报告、教师和管理员实际页面。安全运行摘要写入已忽略的
`test-results/real-ai/summary.json`，正式截图写入
`docs/thesis/screenshots/real-glm/`。证据账号与带专用来源标记的数据默认保留，
用于后续演示，不混入 Mock fixture。

测试默认会重新分析目标题并新生成 3 道变式，确保本次运行确实调用真实模型。
`REAL_AI_E2E_REUSE=true` 只用于真实调用已成功、但后续纯 UI 断言需要修复时的
恢复复核；该模式复用现有分析、变式和练习记录，不能单独作为一次新的模型调用证据。
