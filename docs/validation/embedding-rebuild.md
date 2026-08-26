# 历史错题 Embedding 审计与重建记录

## 1. 验证范围

- 验证日期：2026-08-26
- 目标数据：`question.status = 1` 的全部有效错题
- Embedding provider：`glm`
- Embedding model：`embedding-3`
- 目标维度：1024
- 维护入口：`EmbeddingRebuildMaintenanceLiveTests`
- 显式开关：仅 Maven 进程环境变量 `RUN_EMBEDDING_REBUILD=true` 时执行

本轮只验证历史向量审计、统一重建和最小 RAG 可用性，不包含浏览器业务 E2E、RAG on/off 效果实验、论文截图或其他安全边界修改。1024 维本身不能证明历史向量来源，因此维护入口会对全部有效错题重建，不按旧向量维度跳过。

## 2. 重建前审计

| 指标 | 数量 |
|---|---:|
| active question 总数 | 3 |
| embedding 为 null | 0 |
| 非法 JSON 或非法数组结构 | 0 |
| 含 null、NaN 或 Infinity 的非有限向量 | 0 |
| 256 维 | 0 |
| 512 维 | 0 |
| 1024 维 | 0 |
| 2048 维 | 0 |
| 其他维度 | 3 |

3 条历史向量均为可解析的 8 维旧向量，不能与正式 `embedding-3 / 1024` 向量混用。维度统计与非有限向量统计是两个审计轴，理论上可以重叠。

## 3. 维护实现与安全边界

维护入口逐题执行以下流程：

1. 按主键顺序读取有效题目的 `id`、`user_id`、`subject_id`、`knowledge_point_id`、`stem` 和旧 `embedding`。
2. 保存题干快照，在数据库事务之外调用 `embeddingService.embed(stem)`。
3. 独立验证返回值非空、恰好 1024 维，且每个元素非 null、NaN 或 Infinity。
4. 序列化后执行单条条件更新；更新条件包含 `id`、`status = 1` 和题干的二进制精确匹配。
5. 影响 1 行记为成功，影响 0 行记为 stale；单题异常只记录题目 ID、错误类型和 HTTP 状态信息，继续处理后续题目。

维护循环没有外层大事务，已成功题目不会因后续单题失败而整体回滚。测试日志关闭题目 Mapper 的 SQL 参数输出，不记录 API Key、Authorization、完整响应正文或完整 embedding 数组。

默认执行 `mvnw.cmd test` 时，真实维护入口按预期跳过；只有显式设置 `RUN_EMBEDDING_REBUILD=true` 才会创建真实 GLM 维护上下文并访问网络。

## 4. 真实重建结果

| 指标 | 数量 |
|---|---:|
| total | 3 |
| success | 3 |
| failed | 0 |
| stale | 0 |
| skipped | 0 |

本轮 3 条有效错题全部使用真实智谱 `embedding-3` 重建成功，没有 HTTP 失败、非法向量、并发题干变化或跳过项。

## 5. 重建后审计

| 指标 | 数量 |
|---|---:|
| active question 总数 | 3 |
| embedding 为 null | 0 |
| 非法 JSON 或非法数组结构 | 0 |
| 非有限向量 | 0 |
| 256 维 | 0 |
| 512 维 | 0 |
| 1024 维 | 3 |
| 2048 维 | 0 |
| 其他维度 | 0 |

重建后全部有效错题均为合法、有限的 1024 维向量。

## 6. RAG sanity check

当前数据库中题目 1 和题目 2 均属于用户 3、数学科目、知识点 3（二次函数）：

- source：题目 1，内容为二次函数与 x 轴交点问题。
- result：题目 2，内容为二次函数顶点与对称轴问题。
- cosine：0.8550252569130666。

检查结果：

- source 未返回自身：通过。
- 结果只属于同一用户：通过。
- 结果只属于同一科目：通过。
- source 与结果向量均为合法 1024 维：通过。
- cosine 为有限正数并可正常计算：通过。
- 返回结果按 cosine 降序：通过；当前同用户同科目组只有 1 个候选。

该结果只证明历史向量已经进入统一的真实向量空间，且现有 RAG 能在该空间正常检索；不构成模型效果 benchmark。

## 7. 离线测试与回归

离线维护测试使用 Mock `EmbeddingService` 和真实 MySQL 条件更新，且只处理测试自行插入并物理清理的隔离数据，覆盖：

1. 正常 1024 维写入。
2. null、错误维度、null 元素、NaN 和 Infinity 拒绝。
3. 仅大小写变化的 stale stem 不覆盖。
4. 单题失败后继续处理后续题目。
5. `total = success + failed + stale + skipped` 汇总恒等式。
6. null、非法 JSON、非有限向量及 256/512/1024/2048/其他维度审计分类。

验证结果：

- 后端默认全量测试：42 项，40 项通过，2 个真实联网入口按预期跳过，0 失败。
- 前端类型检查：通过。
- 前端 Vitest：8 个测试文件、23/23 通过。
- 前端生产构建：通过；保留既有大 chunk 警告，本轮未修改前端。

## 8. 使用命令

在 `server` 目录执行：

```powershell
$env:JAVA_HOME = 'D:\Dev\jdk21'
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
$env:RUN_EMBEDDING_REBUILD = 'true'
.\mvnw.cmd '-Dtest=EmbeddingRebuildMaintenanceLiveTests' test
Remove-Item Env:RUN_EMBEDDING_REBUILD -ErrorAction SilentlyContinue
```

普通离线回归：

```powershell
.\mvnw.cmd test
```

真实 API Key 仅通过未跟踪的 `server/.env` 临时注入。验证完成后已确认 Key 值清理，`.env` 仍被忽略且未跟踪；对全部可提交文件和 Surefire 测试报告的精确扫描均为 0 命中，验证记录和测试输出也未保存完整向量。
