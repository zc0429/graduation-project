# Gate5：20–50 题小规模 AI / RAG 实验

## 实验目标与边界

本实验使用固定 27 道人工设计合成错题，评估智谱 `glm-4.7-flash` 在当前 9 个叶子知识点中的知识点 exact-match、错因关键概念覆盖率（自动代理指标）、正式 RAG top-3 检索指标、混合相似题 top-5 推荐指标，以及 6 题 RAG on/off 受控消融。数据集不是公开 benchmark，结果只描述本次固定小样本，不外推为模型总体能力。

`dataset.json` 在真实模型调用前锁定。27 题由数学 12 题、物理 9 题、英语 6 题组成；9 个现有叶子知识点各 3 题。`ragAblation=true` 的 6 题固定为数学、物理、英语各 2 题，不根据输出结果更换。

实验代码仅位于测试侧，不修改生产业务实现。正式 RAG 候选过滤仍是“同用户 + 同科目”，不强制同知识点；`relevanceGroup` 是本实验人工定义的相关集合标签。相似题服务按“同知识点、相近难度优先，RAG 向量补足”评估并称为“混合相似题推荐”，不是纯向量推荐。

## 指标口径

- 知识点 exact-match：模型预测的叶子知识点 ID 与预设 ID 完全一致。
- 错因关键概念覆盖率（自动代理指标）：`errorCause + analysis` 覆盖的预设概念组数除以概念组总数；组内任一同义表达命中即记 1。该指标不是错因合理性准确率或教学质量评分。
- RAG retrieval benchmark：在完整 27 题候选池准备后，对每题调用正式 `RagService.retrieveSimilar(question, 3)`，计算 Hit@3、Recall@3、MRR@3。
- 混合相似题 benchmark：全部正式分析完成后调用 `RecommendService.similar(questionId)`，计算 Hit@5、Recall@5 和相关结果数。
- RAG on/off：6 道预设题使用同一模型、同一基础指令及同一生成参数，唯一主要区别是是否加入正式 RAG top-3 参考题上下文。此部分使用测试侧受控消融 prompt，不改变生产业务实现，也不声称是生产 `AiAnalysisService` 的完全内部调用。

## 人工评分

`manual/error-cause-review.csv` 的 `manualScore` 与 `manualComment` 必须由人工填写：

- 0：明显错误或与题意矛盾。
- 1：部分合理，但错因或解释不完整。
- 2：错因判断基本正确且解释清楚。

`manual/rag-ab-review.csv` 隐去 ON/OFF 条件，`preferred` 与 `reason` 由人工填写。人工完成盲评后，才可使用 `results/rag-ab-key.json` 解盲。Codex 不填写任何人工评分字段。

## 运行方式

默认 Maven 测试不会联网，Gate5 真实入口只有在 `RUN_GATE5_EXPERIMENT=true` 时启用。后端从已被 Git 忽略的 `server/.env` 读取本机 GLM 与数据库配置；不要输出、修改或清空该文件。

```powershell
cd server
$env:RUN_GATE5_EXPERIMENT="true"
$env:GATE5_MODEL_GAP_SECONDS="15"
.\mvnw.cmd -Dtest=Gate5AiRagExperimentTests test
Remove-Item Env:RUN_GATE5_EXPERIMENT
Remove-Item Env:GATE5_MODEL_GAP_SECONDS
```

运行器使用精确用户名 `__gate5_experiment__` 隔离数据。每次开始时只清理该精确用户上一轮创建的数据；成功后保留本轮用户、27 道错题和分析记录，便于数据库复核。结果目录不保存完整 embedding。

若网络或 API 中断，运行器保留已写入的 `results/checkpoint.json`。再次执行同一数据集时，已成功的 Chat 输出不会重复调用；失败历史保留在 checkpoint 中，未完成或失败项可继续运行。最终公开结果由一次完整 27 题数据集生成。

## 输出

- `results/experiment-results.json`：逐题完整结构化结果。
- `results/experiment-results.csv`：论文分析所需扁平指标，不含 embedding。
- `results/knowledge-point-confusion.csv`：预设与预测知识点计数。
- `results/summary.md`：真实汇总、实验限制与不可外推声明。
- `manual/error-cause-review.csv`：错因人工评分表，评分列留空。
- `manual/rag-ab-review.csv`：RAG A/B 人工盲评表，偏好列留空。
- `results/rag-ab-key.json`：人工评分完成后的解盲键。
