# 隔离数据库完整功能验证记录

## 验证范围

- 日期：2026-09-07
- 后端：JDK 21.0.11、Spring Boot 3.5.16、MySQL 8.0.40
- 前端联调：Node.js 24.19.0、Playwright
- 范围：现有后端完整测试与 `wrongbook_e2e` 真实后端联调
- 不在本轮范围：Gate5 重跑、真实 GLM、真实图片识别、Embedding 重建、公网部署和用户体验测试

## 数据库隔离

本轮未启动或复用日常开发用的 `MySQL80` 服务。开发实例保持停止，默认端口为 3306，数据目录由其既有服务配置管理。

验证使用独立初始化的临时 MySQL 实例：

- 数据目录：`D:\Dev\mysql-test\wrongbook-validation-20260907\data`
- 监听地址：`127.0.0.1`
- 端口：3307
- 后端测试库：`wrongbook_test`
- E2E 联调库：`wrongbook_e2e`
- 测试账号：仅被授予上述两个 schema 的权限，没有全局权限
- 密码：运行时随机生成，仅保存在对应进程环境中，未写入仓库、日志或文档

验证完成后，后端和临时 MySQL 均已停止，8080、3306、3307 均无监听。临时实例的初始化 root 凭据已替换为未保存的一次性随机值。主机策略拒绝递归删除临时数据目录，因此该目录仍保留，但没有注册服务、没有可复用凭据，也不会自动启动。

新增 `application-test.yml`，数据库连接只读取 `TEST_DB_URL`、`TEST_DB_USERNAME`、`TEST_DB_PASSWORD`，模型提供方固定为 Mock，图片识别固定关闭，上传目录固定在 `target/test-uploads`。Maven Surefire 默认激活 `test` profile；缺少专用测试密码时启动失败，不会回退到 `dev` 数据库。

## 开关状态

本轮明确保持以下开关为 `false`：

- `RUN_GATE5_EXPERIMENT`
- `RUN_LIVE_LLM_TESTS`
- `RUN_LIVE_IMAGE_RECOGNITION_TESTS`
- `RUN_EMBEDDING_REBUILD`
- `RUN_REAL_AI_E2E`

`LLM_PROVIDER=mock`，未调用任何联网模型，也未修改 Gate5 数据集、人工评价或结果文件。

## 后端完整测试

执行 `server/mvnw.cmd test`，日志确认所有 Spring 上下文使用 `test` profile 并连接 3307 端口的 `wrongbook_test`。

结果：

- 总计：70
- 通过：66
- 失败：0
- 错误：0
- 跳过：4

4 个跳过项分别为 Gate5 真实实验、真实 GLM 验证、真实图片识别和 Embedding 重建入口，均由既有显式 opt-in 条件控制，属于预期跳过，没有为本轮验证新增跳过。

## `wrongbook_e2e` 真实后端联调

后端以 `test` profile、`wrongbook_e2e` 和 Mock AI 启动，健康检查返回 `status=ok`。执行 `web/npm run e2e:integration`：

- 学生错题创建、编辑、练习、携带 JWT 导出和删除：通过
- 教师仅可访问聚合学情并被禁止创建错题：通过
- 管理员访问真实管理入口：通过
- 私有题图仅通过所属学生鉴权详情返回：通过

结果：4/4 通过。E2E 创建的两道题均按业务逻辑软删除为 `status=0`，没有活动测试题残留；后端测试专用夹具残留为 0。

## 失败与处置

正式测试与 E2E 均无失败。准备临时实例时首次连接曾被 MySQL 拒绝，原因是初始化账号为 `root@localhost`，而首个启动命令启用了 `skip-name-resolve`，导致来自 `127.0.0.1` 的账号匹配失败。该问题发生在 schema 创建和测试执行之前；移除该启动参数后，独立实例正常启动。它不是系统业务缺陷，也未触及开发数据。

## 部署前必须处理

1. 建立明确的测试部署 profile，不使用默认 `dev` profile，并关闭面向开发环境的自动种子数据初始化。
2. 将允许携带凭据的通配 CORS 收敛为测试部署前端的明确来源，或使用同源反向代理。
3. 设置稳定且保密的 `JWT_SECRET`，避免重启后会话全部失效。
4. 禁用或替换 `data.sql` 中已知密码的演示账号，避免测试部署环境暴露固定凭据。
5. 将 `UPLOAD_DIR` 指向持久化且权限受控的目录，并验证重启后的图片可用性与访问边界。
6. 系统冻结复测时使用项目约定的 Node.js 22，消除当前 Node.js 24 与既定工具链的版本差异。

本轮未发现需要立即修改的业务阻断缺陷，不进行无关重构。下一阶段应先完成受限的测试部署环境安全配置与启动/重启验证，再进入小规模用户体验测试。
