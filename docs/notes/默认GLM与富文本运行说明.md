# 默认GLM与富文本运行说明

## 正常运行

默认 `LLM_PROVIDER=glm`，文本模型 `glm-5.3-flash`；图片识题默认开启，独立图片客户端默认同一模型标识。指定型号使用 `thinking.type=enabled`、`reasoning_effort=low`，依据是既有图片Spike记录；本轮只做离线HTTP结构验证，没有新联网能力结论。Embedding保持 `embedding-3 / 1024`，不改历史向量与表结构。

| 配置项 | 用法 |
|---|---|
| `LLM_API_KEY` | 真实GLM必需，只从环境或未跟踪.env注入 |
| `LLM_CHAT_MODEL` | 默认glm-5.3-flash，代码保留准确标识 |
| `LLM_EMBEDDING_MODEL` / `LLM_EMBEDDING_DIMENSIONS` | 保持embedding-3 / 1024 |
| `IMAGE_RECOGNITION_ENABLED` | 默认true |
| `IMAGE_RECOGNITION_API_KEY` | 可单独设置，缺省复用LLM_API_KEY |
| `IMAGE_RECOGNITION_MODEL` | 默认glm-5.3-flash |
| `IMAGE_RECOGNITION_MAX_BYTES` | 默认5242880，JPG/PNG/WebP检查 |

已有显式配置仍覆盖默认值，应自行检查本机未跟踪.env是否残留Mock或旧模型配置，不把密钥内容贴进日志。缺密钥不阻止手录和数据查看，AI请求明确失败，无Mock回退；错误不含Key或上游原始响应。无效密钥、权限、网络、限流与超时仍可能使真实请求失败。

## 离线与测试

离线显式设置 `LLM_PROVIDER=mock`、`IMAGE_RECOGNITION_ENABLED=false`。Maven固定test profile，test与deploy-test配置使用Mock并关闭图片联网；前端冒烟使用固定响应。图片Mock成功只说明表单流程通过。

真实入口由 `RUN_LIVE_LLM_TESTS`、`RUN_LIVE_IMAGE_RECOGNITION_TESTS`、`RUN_EMBEDDING_REBUILD` 和Gate5开关隔离，普通回归不要打开。获得密钥后，在专用测试库显式运行既有 `LiveGlmValidationTests` 和 `LiveQuestionRecognitionTests`；记录实际模型、阶段成功和失败，不记录认证头。还要用真实题图核对候选及浏览器回填，合成图片通过不能代替真实照片或手写题验收。本轮这些联网步骤未执行。

## 富文本与历史数据

沿用 `question.stem TEXT`，无DDL和批量迁移。新增、编辑共用Tiptap，DOMPurify和Jsoup分别限制标签，不允许事件、属性、内嵌图像或外链；原题图继续用独立附件。

提示词、Embedding、RAG参考片段、复习摘要及XLSX使用统一纯文本，保留换行，上下标表示为 `^(...)`、`_(...)`。旧纯文本保留数学比较符号与换行，展示时转义。识别候选先按纯文本转义后送入编辑器，不能作为可信HTML插入。题干改变仍使旧AI派生数据失效，历史练习和复习计划保留。
