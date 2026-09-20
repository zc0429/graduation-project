# 原始实验复算

2026-09-20，从 docs/experiments/gate5/manual/error-cause-review.csv 与 rag-ab-review.csv 使用csv.DictReader、utf-8-sig、newline空字符串解析；解盲依据results/rag-ab-key.json。

实际结果：27题，46/54，均分46/27=1.7037037037；2分20题，1分6题，0分1题。总分占比不是准确率。6组偏好解盲RAG_ON=2、RAG_OFF=4，无平局，不进行显著性或长期效果推断。

原始自动JSON generatedAt=2026-08-27，人工表属于2026-09-07批次。JSON中的27题、26题知识点命中及检索数据与论文记录一致；本轮未重新请求模型。旧summary人工待评保留为历史。

RAG两组自动覆盖均88.89%，人工偏好不支持一致优势。结构合规、概念覆盖、人工判断属于不同指标，不互相替代。34次失败尝试不代表34道独立错题。现有样本为合成错题，不是学习成绩实验。

本轮复算数据见current-baseline.json的gate5_manual。没有修改原始CSV、JSON、模型输出、解盲键。
