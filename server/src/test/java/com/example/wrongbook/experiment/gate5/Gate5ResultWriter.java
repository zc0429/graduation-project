package com.example.wrongbook.experiment.gate5;

import com.fasterxml.jackson.databind.ObjectMapper;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.function.Function;
import java.util.stream.Collectors;

final class Gate5ResultWriter {

    private static final String BOM = "\uFEFF";
    private final ObjectMapper objectMapper;

    Gate5ResultWriter(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    void write(Path gate5Directory, Gate5Models.ExperimentResult result) throws Exception {
        Path resultsDirectory = gate5Directory.resolve("results");
        Path manualDirectory = gate5Directory.resolve("manual");
        Files.createDirectories(resultsDirectory);
        Files.createDirectories(manualDirectory);

        objectMapper.writerWithDefaultPrettyPrinter()
                .writeValue(resultsDirectory.resolve("experiment-results.json").toFile(), result);
        writeExperimentCsv(resultsDirectory.resolve("experiment-results.csv"), result.cases());
        writeConfusionCsv(resultsDirectory.resolve("knowledge-point-confusion.csv"), result.cases());
        writeErrorCauseReview(manualDirectory.resolve("error-cause-review.csv"), result.cases());
        writeRagAbReview(manualDirectory.resolve("rag-ab-review.csv"), result);
        writeRagAbKey(resultsDirectory.resolve("rag-ab-key.json"), result.ablations());
        Files.writeString(resultsDirectory.resolve("summary.md"), summary(result), StandardCharsets.UTF_8);
    }

    private void writeExperimentCsv(Path path, List<Gate5Models.CaseResult> cases) throws Exception {
        List<List<?>> rows = new ArrayList<>();
        rows.add(List.of(
                "case_id", "question_id", "subject", "expected_kp_id", "expected_kp_name",
                "predicted_kp_id", "predicted_kp_name", "kp_exact_match", "analysis_status",
                "llm_model", "difficulty", "error_concept_hit", "error_concept_total",
                "error_concept_coverage", "rag_top3_case_ids", "rag_top3_question_ids",
                "rag_top3_groups", "rag_hit_at_3", "rag_recall_at_3",
                "rag_first_relevant_rank", "rag_mrr_at_3", "recommend_top5_case_ids",
                "recommend_top5_question_ids", "recommend_actual_k", "recommend_hit_at_5",
                "recommend_recall_at_5", "recommend_relevant_count", "duration_ms", "failure_reason"));
        for (Gate5Models.CaseResult item : cases) {
            Gate5Models.AnalysisResult analysis = item.analysis();
            rows.add(List.of(
                    item.dataset().caseId(), item.questionId(), item.dataset().subjectName(),
                    item.dataset().expectedKnowledgePointId(), item.dataset().expectedKnowledgePointName(),
                    nullable(analysis.predictedKnowledgePointId()), nullable(analysis.predictedKnowledgePointName()),
                    analysis.exactMatch(), nullable(analysis.status()), nullable(analysis.llmModel()),
                    nullable(analysis.difficulty()), analysis.conceptHit(), analysis.conceptTotal(),
                    decimal(analysis.conceptCoverage()), join(item.rag().caseIds()), join(item.rag().questionIds()),
                    join(item.rag().groups()), decimal(item.rag().hitAt3()), decimal(item.rag().recallAt3()),
                    item.rag().firstRelevantRank(), decimal(item.rag().mrrAt3()),
                    join(item.recommend().caseIds()), join(item.recommend().questionIds()),
                    item.recommend().actualK(), decimal(item.recommend().hitAt5()),
                    decimal(item.recommend().recallAt5()), item.recommend().relevantCount(),
                    analysis.durationMs(), nullable(analysis.failureReason())));
        }
        writeCsv(path, rows);
    }

    private void writeConfusionCsv(Path path, List<Gate5Models.CaseResult> cases) throws Exception {
        Map<ConfusionKey, Long> counts = cases.stream().collect(Collectors.groupingBy(
                item -> new ConfusionKey(
                        item.dataset().expectedKnowledgePointId(),
                        item.dataset().expectedKnowledgePointName(),
                        item.analysis().predictedKnowledgePointId(),
                        item.analysis().predictedKnowledgePointName()),
                LinkedHashMap::new,
                Collectors.counting()));
        List<List<?>> rows = new ArrayList<>();
        rows.add(List.of("expected_kp_id", "expected_kp_name", "predicted_kp_id", "predicted_kp_name", "count"));
        counts.entrySet().stream()
                .sorted(Comparator.comparingLong(entry -> entry.getKey().expectedId()))
                .forEach(entry -> rows.add(List.of(
                        entry.getKey().expectedId(), entry.getKey().expectedName(),
                        nullable(entry.getKey().predictedId()), nullable(entry.getKey().predictedName()),
                        entry.getValue())));
        writeCsv(path, rows);
    }

    private void writeErrorCauseReview(Path path, List<Gate5Models.CaseResult> cases) throws Exception {
        List<List<?>> rows = new ArrayList<>();
        rows.add(List.of(
                "caseId", "subject", "expectedKnowledgePoint", "stem", "wrongAnswer",
                "correctAnswer", "expectedErrorConcepts", "modelErrorCause", "modelAnalysis",
                "manualScore", "manualComment"));
        for (Gate5Models.CaseResult item : cases) {
            rows.add(List.of(
                    item.dataset().caseId(), item.dataset().subjectName(),
                    item.dataset().expectedKnowledgePointName(), item.dataset().stem(),
                    item.dataset().wrongAnswer(), item.dataset().correctAnswer(),
                    item.dataset().errorConceptGroups().stream().map(group -> String.join("|", group))
                            .collect(Collectors.joining(" / ")),
                    nullable(item.analysis().errorCause()), nullable(item.analysis().analysis()), "", ""));
        }
        writeCsv(path, rows);
    }

    private void writeRagAbReview(Path path, Gate5Models.ExperimentResult result) throws Exception {
        Map<String, Gate5Dataset.Case> datasetById = result.cases().stream().collect(Collectors.toMap(
                item -> item.dataset().caseId(), Gate5Models.CaseResult::dataset));
        List<List<?>> rows = new ArrayList<>();
        rows.add(List.of(
                "caseId", "stem", "wrongAnswer", "correctAnswer", "outputA", "outputB",
                "preferred", "reason"));
        for (Gate5Models.AblationPair pair : result.ablations()) {
            Gate5Dataset.Case item = datasetById.get(pair.caseId());
            boolean aIsOn = Gate5Metrics.outputAIsRagOn(pair.caseId());
            Gate5Models.AblationOutput outputA = aIsOn ? pair.ragOn() : pair.ragOff();
            Gate5Models.AblationOutput outputB = aIsOn ? pair.ragOff() : pair.ragOn();
            rows.add(List.of(
                    pair.caseId(), item.stem(), item.wrongAnswer(), item.correctAnswer(),
                    blindOutput(outputA), blindOutput(outputB), "", ""));
        }
        writeCsv(path, rows);
    }

    private void writeRagAbKey(Path path, List<Gate5Models.AblationPair> pairs) throws Exception {
        Map<String, Object> key = new LinkedHashMap<>();
        for (Gate5Models.AblationPair pair : pairs) {
            boolean aIsOn = Gate5Metrics.outputAIsRagOn(pair.caseId());
            key.put(pair.caseId(), Map.of(
                    "A", aIsOn ? "RAG_ON" : "RAG_OFF",
                    "B", aIsOn ? "RAG_OFF" : "RAG_ON"));
        }
        objectMapper.writerWithDefaultPrettyPrinter().writeValue(path.toFile(), key);
    }

    private String summary(Gate5Models.ExperimentResult result) {
        List<Gate5Models.CaseResult> cases = result.cases();
        long analysisSuccess = cases.stream().filter(item -> item.analysis().successful()).count();
        long exactMatches = cases.stream().filter(item -> item.analysis().exactMatch()).count();
        double exactPercentage = mean(cases, item -> item.analysis().exactMatch() ? 1.0 : 0.0);
        double meanCoverage = mean(cases, item -> item.analysis().conceptCoverage());
        double medianCoverage = median(cases.stream().map(item -> item.analysis().conceptCoverage()).toList());
        long zeroCoverage = cases.stream().filter(item -> item.analysis().conceptCoverage() == 0.0).count();
        long fullCoverage = cases.stream().filter(item -> item.analysis().conceptCoverage() == 1.0).count();

        double ragHit = mean(cases, item -> item.rag().hitAt3());
        double ragRecall = mean(cases, item -> item.rag().recallAt3());
        double ragMrr = mean(cases, item -> item.rag().mrrAt3());
        double recommendHit = mean(cases, item -> item.recommend().hitAt5());
        double recommendRecall = mean(cases, item -> item.recommend().recallAt5());

        List<Gate5Models.AblationOutput> off = result.ablations().stream().map(Gate5Models.AblationPair::ragOff).toList();
        List<Gate5Models.AblationOutput> on = result.ablations().stream().map(Gate5Models.AblationPair::ragOn).toList();
        double offCoverage = off.stream().mapToDouble(Gate5Models.AblationOutput::conceptCoverage).average().orElse(0);
        double onCoverage = on.stream().mapToDouble(Gate5Models.AblationOutput::conceptCoverage).average().orElse(0);
        long offSchema = off.stream().filter(Gate5Models.AblationOutput::schemaSuccess).count();
        long onSchema = on.stream().filter(Gate5Models.AblationOutput::schemaSuccess).count();
        double offLength = off.stream().mapToInt(Gate5Models.AblationOutput::responseLength).average().orElse(0);
        double onLength = on.stream().mapToInt(Gate5Models.AblationOutput::responseLength).average().orElse(0);

        StringBuilder summary = new StringBuilder();
        summary.append("# Gate5 小规模 AI / RAG 实验结果\n\n")
                .append("## 实验信息\n\n")
                .append("- 目的：在固定小样本中审计知识点分类、错因关键概念覆盖、RAG 检索、混合相似题推荐及 RAG on/off 输出差异。\n")
                .append("- 日期：").append(formatDate(result.generatedAt())).append("。\n")
                .append("- Git commit：`").append(result.gitCommit()).append("`。\n")
                .append("- Chat 模型：`").append(result.chatModel()).append("`。\n")
                .append("- Embedding：`").append(result.embeddingModel()).append("`，")
                .append(result.embeddingDimensions()).append(" 维。\n")
                .append("- 固定数据集：27 题，数学 12、物理 9、英语 6；9 个叶子知识点各 3 题。\n")
                .append("- Embedding：成功 ").append(result.embeddingSuccess()).append("，失败 ")
                .append(result.embeddingFailure()).append("；成功向量均已验证为 1024 维有限数。\n")
                .append("- 真实 AI 分析：成功 ").append(analysisSuccess).append("，失败 ")
                .append(cases.size() - analysisSuccess).append("；分母始终保留全部 27 题。\n\n")
                .append("## 自动指标\n\n")
                .append("- 本次固定 27 题实验样本中，知识点 exact-match 为 ")
                .append(exactMatches).append("/27（").append(percent(exactPercentage)).append("）。")
                .append("小样本结果不能代表模型总体准确率。\n")
                .append("- 错因关键概念覆盖率（自动代理指标）：平均 ")
                .append(percent(meanCoverage)).append("，中位数 ").append(percent(medianCoverage))
                .append("，0 覆盖 ").append(zeroCoverage).append(" 题，100% 覆盖 ")
                .append(fullCoverage).append(" 题。失败题按 0 覆盖计入全部 27 题分母。\n")
                .append(coverageByKnowledgePoint(cases))
                .append("- RAG retrieval benchmark：Hit@3=").append(decimal(ragHit))
                .append("，Recall@3=").append(decimal(ragRecall))
                .append("，MRR@3=").append(decimal(ragMrr)).append("。\n")
                .append("- 混合相似题 benchmark：Hit@5=").append(decimal(recommendHit))
                .append("，Recall@5=").append(decimal(recommendRecall)).append("。\n\n")
                .append("## RAG on/off 受控消融（固定 6 题）\n\n")
                .append("- RAG OFF：平均概念覆盖率 ").append(percent(offCoverage))
                .append("，schema 成功 ").append(offSchema).append("/6，平均响应长度 ")
                .append(decimal(offLength)).append(" 字符。\n")
                .append("- RAG ON：平均概念覆盖率 ").append(percent(onCoverage))
                .append("，schema 成功 ").append(onSchema).append("/6，平均响应长度 ")
                .append(decimal(onLength)).append(" 字符。\n")
                .append("- ON-OFF 覆盖率差值：").append(signedPercent(onCoverage - offCoverage))
                .append("；平均响应长度差值：").append(signed(onLength - offLength)).append(" 字符。\n")
                .append("- 该部分为受控消融实验 prompt，用于比较是否加入检索上下文，不改变生产业务实现。\n\n")
                .append("## 人工评分状态\n\n")
                .append("错因合理性评分与 RAG A/B 偏好均为**待人工复核**。人工表中的评分、评论、偏好和理由列保持空白；自动概念覆盖率不得替代人工合理性判断。\n\n")
                .append("## 实验限制与不可外推声明\n\n")
                .append("- 本实验仅含 27 道人工设计的受控合成错题，不是公开 benchmark。\n")
                .append("- 模型输出存在随机性，知识点体系仅覆盖当前 9 个叶子节点。\n")
                .append("- 错因关键概念覆盖率只是字符串匹配的自动代理指标，不能证明解释正确或教学有效。\n")
                .append("- 人工合理性评分尚未完成，不得编造或提前报告人工评分结果。\n")
                .append("- 相似题服务是同知识点与难度优先、向量补足的混合推荐，不是纯向量算法。\n")
                .append("- 正式 RAG 候选过滤为同用户 + 同科目，不强制同知识点；本实验的 relevanceGroup 是人工定义的评估标签。\n")
                .append("- 所有比例仅描述本次固定样本，不能外推为 GLM 的总体准确率或一般教学质量。\n");
        if (!result.failureHistory().isEmpty()) {
            summary.append("\n## 失败历史\n\n运行期间共记录 ")
                    .append(result.failureHistory().size())
                    .append(" 条失败尝试；即使后续重试成功，历史仍保留在 `experiment-results.json` 与 `checkpoint.json` 中。\n");
        }
        return summary.toString();
    }

    private String coverageByKnowledgePoint(List<Gate5Models.CaseResult> cases) {
        Map<String, Double> means = cases.stream().collect(Collectors.groupingBy(
                item -> item.dataset().expectedKnowledgePointName(),
                LinkedHashMap::new,
                Collectors.averagingDouble(item -> item.analysis().conceptCoverage())));
        return "- 各知识点平均覆盖率：" + means.entrySet().stream()
                .map(entry -> entry.getKey() + " " + percent(entry.getValue()))
                .collect(Collectors.joining("；")) + "。\n";
    }

    private String blindOutput(Gate5Models.AblationOutput output) {
        if (!output.schemaSuccess()) {
            return "[输出失败：" + output.failureReason() + "]";
        }
        return "错因：" + output.errorCause() + "\n解析：" + output.analysis();
    }

    private void writeCsv(Path path, List<List<?>> rows) throws Exception {
        String content = rows.stream()
                .map(row -> row.stream().map(this::csv).collect(Collectors.joining(",")))
                .collect(Collectors.joining("\r\n", BOM, "\r\n"));
        Files.writeString(path, content, StandardCharsets.UTF_8);
    }

    private String csv(Object value) {
        String text = Objects.toString(value, "");
        return "\"" + text.replace("\"", "\"\"") + "\"";
    }

    private String join(List<?> values) {
        return values.stream().map(Objects::toString).collect(Collectors.joining("|"));
    }

    private String nullable(Object value) {
        return value == null ? "" : value.toString();
    }

    private String decimal(double value) {
        return String.format(Locale.ROOT, "%.6f", value);
    }

    private String percent(double value) {
        return String.format(Locale.ROOT, "%.2f%%", value * 100);
    }

    private String signedPercent(double value) {
        return String.format(Locale.ROOT, "%+.2f%%", value * 100);
    }

    private String signed(double value) {
        return String.format(Locale.ROOT, "%+.2f", value);
    }

    private double mean(List<Gate5Models.CaseResult> cases, Function<Gate5Models.CaseResult, Double> value) {
        return cases.stream().map(value).mapToDouble(Double::doubleValue).average().orElse(0);
    }

    private double median(List<Double> values) {
        List<Double> sorted = values.stream().sorted().toList();
        if (sorted.isEmpty()) {
            return 0;
        }
        int middle = sorted.size() / 2;
        return sorted.size() % 2 == 0
                ? (sorted.get(middle - 1) + sorted.get(middle)) / 2
                : sorted.get(middle);
    }

    private String formatDate(String generatedAt) {
        return DateTimeFormatter.ISO_LOCAL_DATE.withZone(ZoneId.of("Asia/Shanghai"))
                .format(Instant.parse(generatedAt));
    }

    private record ConfusionKey(
            long expectedId,
            String expectedName,
            Long predictedId,
            String predictedName) {
    }
}
