# 演示流程与现场验收
状态：2026-09-21 已完成本机隔离 Mock 浏览器流程验证，见 [实际结果](CONTINUATION-20260921.md)。本人计时演练与 PowerPoint 原生实开仍待；自动验证不代替本人现场演练。

## 前提
只使用隔离的本机演示库与专用账号。使用既有 deploy-test 配置，通过当前终端注入 DEPLOY_TEST_DB_URL、DEPLOY_TEST_DB_USERNAME、DEPLOY_TEST_DB_PASSWORD、DEPLOY_TEST_JWT_SECRET、DEPLOY_TEST_UPLOAD_DIR、DEPLOY_TEST_CORS_ORIGINS；不把实际凭据写入本文件。JDK21、Maven Wrapper、Node22及npm为业务运行前提。
先确认8081/4175未被其他项目占用；已有服务不擅自终止。仅在专用库手工导入 schema.sql，并建立数学科目、函数一级章节和其下二次函数二级知识点；解析候选只取二级考点，仅建一级分类会解析失败。注册专用学生，不导入 data.sql 中的固定密码账号，不重置或覆盖原Gate5数据。

以下为后续本人演练的启动方式。本轮实际采用打包JAR与独立MySQL实例，具体进程、脚本与结果见续办记录。先完成上述环境变量与数据库准备；本轮临时库随机凭据未保留，不直接复用：
```powershell
Set-Location 'D:/Documents/GitHub/graduation-project-thesis-20260920/server'
$env:LLM_PROVIDER='mock'
$env:IMAGE_RECOGNITION_ENABLED='false'
$env:SPRING_PROFILES_ACTIVE='deploy-test'
$env:SPRING_CONFIG_IMPORT=''
$env:DEPLOY_TEST_PORT='8081'
$env:DEPLOY_TEST_CORS_ORIGINS='http://127.0.0.1:4175'
.\mvnw.cmd spring-boot:run
```
另一个终端：
```powershell
Set-Location 'D:/Documents/GitHub/graduation-project-thesis-20260920/web'
npm ci
$env:VITE_BACKEND_PROXY_TARGET='http://127.0.0.1:8081'
npm run dev -- --host 127.0.0.1 --port 4175 --strictPort
```
deploy-test 不自动初始化数据库，必须先对专用库执行上述准备。先读根README和web/README，检查DB配置以及浏览器实际显示的端口。历史源码中的种子账号不作为公开演示凭据。

## 三分钟流程
|时间|操作|预期观察|证据界限|
|---|---|---|---|
|0:00—0:20|登录本机学生演示账号|仅学生导航；显式说明Mock AI|不是智谱现场结果|
|0:20—1:00|手动保存数学错题|保存后另行进入解析状态；详情可返回|图片识别关闭|
|1:00—1:30|查看解析、参考页签、变式入口|讲解状态与字段，Mock内容仅演示接口链|不把Mock内容用于效果评价|
|1:30—2:00|记录一次正确练习|练习记录新增，原题分值按有界+15更新|基于自评|
|2:00—2:30|进入复习与学情报告|新题首节点未到期时待办可为0；报告读取当前记录|不改数据库日期制造到期|
|2:30—3:00|切换答辩第9/11页|展示2026-08-26真实GLM历史证据与Gate5小样本|明确日期和历史性质|

建议输入：题干“已知二次函数y=x²−6x+5，配方写成(x−3)²+5并判定顶点(3,5)。指出错误并求正确顶点。”
答案“y=(x−3)²−4，顶点(3,−4)，最小值−4；错误是配方遗漏减去9。”
这只是计划演示题，不登记为新研究样本。

## 故障分支和退出
- 数据库/JDK或登录失败：保留错误类别，停止现场动态流程，切到已交付PDF/PPT与历史证据。不得宣称此次动态验证通过。
- Mock输出与题意不符：说明Mock只测流程，切历史真实结果，不临时启用付费GLM。
- 网络失败：本机Mock可继续，历史截图离线查看；不依赖在线模型。
- 变式长时间等待：不要重复点击，说明同步调用边界，切换已有截图。
- 退出只在自己启动的两个终端按Ctrl+C；不结束不明Java/Node/MySQL进程。演示后清理方案需以专用库为范围，不删除历史证据。

## 执行记录
2026-09-21 Codex 自动操作实际浏览器通过，JDK21.0.11/MySQL8.0.40/Node22.23.1；数据库与进程隔离、8项流程观察和退出状态见 CONTINUATION-20260921 及 mock-demo-20260921 中的JSON。本人现场演练日期、5—8分钟计时、PowerPoint版本与实开检查仍待本人填写。
真实用户体验另按 docs/validation/user-experience-test-plan.md 执行；本演示不代替真人评价。
