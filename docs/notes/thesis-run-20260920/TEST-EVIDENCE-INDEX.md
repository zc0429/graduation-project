# 历史测试证据索引

本轮只读核对记录与原始数据，未重跑下列业务测试。

|日期|证据文件（仓库根目录相对）|结果与范围|
|---|---|---|
|2026-09-07|docs/validation/deploy-test-validation.md|后端73项，69通过4跳过；非公网本机部署|
|2026-09-07|docs/validation/user-experience-test-plan.md|前端23/23、typecheck/build；浏览器44/44；真人体验尚未实施|
|2026-09-07|docs/validation/isolated-functional-validation.md|隔离数据库Mock联调4/4|
|2026-08-25|docs/validation/live-glm-validation.md|最终轮结构化分析5/5、变式3/3；保留历史失败|
|2026-08-26|docs/validation/embedding-rebuild.md|3/3历史向量重建1024维|
|2026-08-26|docs/validation/real-ai-e2e.md|真实浏览器业务链，参考题、变式、练习|
|专项记录所载日期|docs/validation/image-question-recognition.md|8张合成图，首轮7/8，失败即时重试成功|

各批次不得相加成一个通过率。并发性能、长期学习效果、公网部署与真人体验没有完成证据。
