# 真实智谱 GLM 验证记录

> 验证日期：2026-08-25
>
> 验证分支：`codex/live-glm-validation`
>
> 正式联网模型：智谱 `glm-4.7-flash` + `embedding-3`
>
> 结论：最终同一轮真实验证全部通过；本轮未使用 DeepSeek 联网能力。

## 1. 验证目标与范围

本次验证不以 Mock 响应替代模型结果，覆盖以下真实链路：

1. 最小 Chat JSON 连通性与实际响应模型确认；
2. `embedding-3` 的 1024 维真实向量；
3. 5 个固定错题样本的结构化分析；
4. 错题、AI 分析、知识点、难度、分析向量、模型标识和 RAG 引用的完整回写；
5. 基于真实向量的同用户、同科目 RAG 检索；
6. 3 道 Variant 生成、字段校验、事务写入及数据库回读；
7. 默认不联网的后端与前端全量回归；
8. API Key、日志、文档、隔离测试数据和本地进程清理。

真实接口口径参考智谱官方的[API 概览](https://docs.bigmodel.cn/cn/api/introduction)、[对话补全](https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8)、[`embedding-3`](https://docs.bigmodel.cn/cn/guide/models/embedding/embedding-3) 与[错误码说明](https://docs.bigmodel.cn/cn/faq/api-code)。

## 2. 配置与安全边界

| 项目 | 验证值 |
|---|---|
| Provider | `glm` |
| Base URL | `https://open.bigmodel.cn/api/paas/v4` |
| Chat 模型 | `glm-4.7-flash` |
| Embedding 模型 | `embedding-3` |
| Embedding 维度 | 1024 |
| Chat 输出 | `response_format=json_object`、关闭 thinking、非流式 |
| Chat 输出上限 | 4096 tokens |
| 连接/读取超时 | 10 秒 / 90 秒 |
| Live 开关 | 仅 `RUN_LIVE_LLM_TESTS=true` 时启用 |

API Key 只通过本地 `server/.env` 注入，验证指标不打印提示词、响应正文、Authorization、完整向量或 Key。最终验证和回归结束后，已从 `server/.env` 移除本轮 GLM 与 live 配置，保留原有数据库/JWT 本地配置。

## 3. 最终真实验证结果

最终执行命令对应的 Maven 结果为 `BUILD SUCCESS`，耗时约 10 分 52 秒。

| 阶段 | 结果 | 关键证据 |
|---|---|---|
| 最小 Chat | 通过 | 第 1 次阶段尝试成功；实际模型 `glm-4.7-flash`；原始 JSON、无 Markdown 围栏、字段和值正确；82381 ms |
| Embedding | 通过 | 2 次真实请求；模型 `embedding-3`；1024 维；全部有限；两向量不同；余弦值 0.584779705192893；820 ms |
| RAG | 通过 | 返回 2 个真实候选；同用户同科目；排除源题；两候选均出现；相似度有限、不同并降序；相关题排第 1；224 ms |
| 结构化分析 | 5/5 | 同一轮共 5 次阶段尝试，首次失败 0；请求、JSON、知识点、难度、文本、向量、模型和引用均 5/5 |
| Variant | 通过 | 第 1 次阶段尝试成功；生成 3 条、持久化 3 条、数据库回读 3 条；字段与难度范围全部有效；24575 ms |

### 3.1 五个固定结构化样本

| 样本 | 阶段尝试 | 结果 | 延迟 |
|---|---:|---|---:|
| 一次函数斜率符号 | 1 | 全部校验通过 | 63890 ms |
| 二次函数判别式 | 1 | 全部校验通过 | 64474 ms |
| 三角形全等条件 | 1 | 全部校验通过；客户端内部经历 1 次 `1305` 退避 | 19886 ms |
| 圆的切线性质 | 1 | 全部校验通过；客户端内部经历 1 次 `1305` 退避 | 19863 ms |
| 一次函数待定系数 | 1 | 全部校验通过 | 7641 ms |

最终汇总为：`total=5`、`attempts=5`、`initialFailures=0`、`success=5`、`jsonParsed=5`、`knowledgePointValid=5`、`difficultyValid=5`、`fieldsValid=5`、`embeddingValid=5`、`modelConfirmed=5`、`referenceIdsValid=5`，平均延迟 35150.8 ms。

### 3.2 完整 AI 错题分析链

每个成功样本均通过服务层异步入口执行，并核验：

- `ai_analysis.status=1`；
- 知识点 ID 属于当前科目的候选集合，且与错题回填一致；
- 难度是 1–5 的整数；
- 错因与解析是非空中文文本；
- 错题写入 1024 维有限向量；
- `llm_model=glm-4.7-flash`；
- RAG 引用 ID 可回查、属于同一学生且不包含源题；
- 过期输入或无效结构不会写成成功状态。

### 3.3 RAG 与 Variant

RAG 使用真实 `embedding-3` 向量构造一个源题、一个语义相关候选和一个较远候选，验证了所有权隔离、源题排除、余弦排序和相关题优先，不以固定 Mock 分数代替。

Variant 在模型调用和完整 JSON 校验后才进入短事务；事务内锁定原题并核对用户、科目、知识点、题干和答案快照，再一次性插入 3 条。最终通过服务重新读取数据库，确认数量、题干、答案、难度和题目关联均有效。并发编辑时旧响应不得回写；删除路径的统一锁顺序属于后续“其余事务边界”任务，不在本轮扩大修改。

## 4. 客户端与结构化输出加固

### 4.1 有限重试矩阵

| 失败类型 | 客户端是否自动重试 | 策略 |
|---|---|---|
| 连接失败、DNS、连接超时 | 是 | 最多 3 次 HTTP 尝试，500/1000 ms 退避 |
| HTTP 5xx | 是 | 最多 3 次 HTTP 尝试，500/1000 ms 退避 |
| HTTP 429 且业务码 `1305` | 是 | 最多 3 次 HTTP 尝试，15/30 秒退避 |
| 读取超时 | 否 | 不自动重放非幂等 Chat 请求 |
| 用户限流 `1302`、额度类或其他 4xx | 否 | 立即保留真实失败 |

Live 验证器在客户端边界之外允许每个 Chat/分析/Variant 阶段最多 1 次显式恢复尝试，每次尝试都单独输出指标；本次最终轮没有触发阶段级恢复。普通测试默认关闭联网。

### 4.2 结构校验

- Chat 与 Embedding 响应必须携带并匹配请求模型；
- Embedding 必须是恰好 1024 个有限数值；
- AI 分析根对象必须且仅含 4 个约定字段，知识点必须来自候选集合，难度必须为 1–5 整数，两个文本字段必须非空且包含中文；
- Variant 根对象和每个条目必须且仅含约定字段，数组必须恰好 3 项，题干/答案非空，难度必须为 1–5 整数；
- 大小写或空格不同的 JSON Markdown 围栏仅做兼容清理，并记录不含正文的警告；
- HTTP、结构和兜底异常日志只记录状态码与异常类型，不记录异常正文或完整堆栈。

## 5. 失败证据与修复过程

本次未删除失败样本，也没有用挑选成功响应替代固定集结果。关键失败均保留如下：

| 阶段 | 真实失败证据 | 处理与结论 |
|---|---|---|
| 初始最小 Chat | 一次 HTTP 200 但未满足固定 schema；另一次 60 秒读取超时 | 收紧 JSON 指令，并依据真实 76–82 秒成功响应把读取边界调为 90 秒 |
| 初始 5 样本 | 4/5 请求并解析为 JSON，但结构字段 0/5 合格；另 1 个为 `1305` | 提示词改为精确 schema，服务端新增独立强校验；无效结果保持失败状态 |
| 初始 Variant | HTTP 返回后因 difficulty 不是 1–5 整数被拒绝，0 条持久化 | 收紧提示词和三条全量预校验；最终真实 3/3 通过 |
| 修复后完整轮次 1 | Chat、Embedding、RAG、Variant 通过；分析 4/5，第 1 个样本连续 3 次 `1305` | 保留该轮，未删除失败样本 |
| 修复后完整轮次 2 | 分析仍为 4/5；最小 Chat 与 Variant 各出现一次 90 秒读取超时 | 保留该轮；确认读取超时不由客户端重放 |
| 最终完整轮次 | Chat、Embedding、RAG、分析 5/5、Variant 3/3 全部通过 | 同一轮固定集 `attempts=5`、`initialFailures=0`，不是跨轮拼接的 5/5 |

验证期间还观察到智谱平台 `1302`、`1305` 和读取延迟波动。它们被作为外部服务限制记录，不改写为本地成功，也未切换到 DeepSeek 绕过。

## 6. 回归测试

真实验证完成后切回 `LLM_PROVIDER=mock` 且设置 `RUN_LIVE_LLM_TESTS=false`：

- 后端：36 项，35 通过、0 失败、0 错误、真实联网项按开关跳过 1；
- 结构与事务相关定向回归：28/28 通过；
- 前端类型检查：通过；
- 前端 Vitest：8 个文件、23/23 通过；
- 前端生产构建：通过，仅保留既有的大包体积警告。

## 7. 清理与泄密检查

- `server/.env` 命中 `.gitignore` 的 `**/.env`，且不在 `git ls-files` 中；
- 用真实 Key 做精确字符串扫描：可提交文件命中 0，Surefire 测试日志命中 0；
- `.env.example` 只含占位符，不含真实 Key；
- 日志和本文不含完整 Key、Authorization、完整响应正文或向量数组；
- 验证完成后已从 `server/.env` 删除本轮 GLM 与 live 配置；
- 隔离用户名、错题、分析、Variant、消息等测试数据已由 `finally` 清理；
- 本轮专用 MySQL 进程已停止，陈旧 PID 文件已清理。

## 8. 复现方式

真实测试必须先把本地 `.env` 中的变量安全加载到 Maven 进程环境，再显式启用开关；不要在命令行历史、日志或文档中粘贴 Key。

```powershell
$env:RUN_LIVE_LLM_TESTS = 'true'
.\mvnw.cmd '-Dtest=LiveGlmValidationTests' test
```

普通回归必须关闭真实联网：

```powershell
$env:RUN_LIVE_LLM_TESTS = 'false'
$env:LLM_PROVIDER = 'mock'
.\mvnw.cmd test
```

后续仍需使用真实 `embedding-3` 重建历史题目向量，并重跑业务 E2E 与论文证据截图；现有自动化和设计截图仍属于 Mock 流程证据，不能冒充本次真实模型验证结果。
