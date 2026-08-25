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
