package com.example.wrongbook.experiment.gate5;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.wrongbook.common.LoginUser;
import com.example.wrongbook.common.UserContext;
import com.example.wrongbook.config.LlmProperties;
import com.example.wrongbook.entity.AiAnalysis;
import com.example.wrongbook.entity.KnowledgePoint;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.mapper.AiAnalysisMapper;
import com.example.wrongbook.mapper.KnowledgePointMapper;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.service.AiAnalysisService;
import com.example.wrongbook.service.EmbeddingService;
import com.example.wrongbook.service.LlmClient;
import com.example.wrongbook.service.RagService;
import com.example.wrongbook.service.RecommendService;
import com.example.wrongbook.service.impl.OpenAiCompatibleLlmClient;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.util.StringUtils;
import org.springframework.web.client.RestClientResponseException;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.sql.Statement;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.TimeUnit;
import java.util.function.Function;
import java.util.stream.Collectors;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Gate5 真实小样本实验入口。默认禁用，只在 RUN_GATE5_EXPERIMENT=true 时联网。
 */
@Tag("gate5-live")
@SpringBootTest(properties = {
        "app.llm.provider=glm",
        "app.llm.chat-model=glm-4.7-flash",
        "app.llm.embedding-model=embedding-3",
        "app.llm.embedding-dimensions=1024",
        "spring.sql.init.mode=always",
        "mybatis-plus.configuration.log-impl=org.apache.ibatis.logging.nologging.NoLoggingImpl"
})
@EnabledIfEnvironmentVariable(named = "RUN_GATE5_EXPERIMENT", matches = "(?i)true")
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class Gate5AiRagExperimentTests {

    private static final String EXPERIMENT_USERNAME = "__gate5_experiment__";
    private static final String EXPERIMENT_SOURCE = "Gate5固定27题实验";
    private static final int REQUIRED_DIMENSIONS = 1024;
    private static final int RELEVANT_POOL_SIZE = 2;
    private static final Duration ANALYSIS_TIMEOUT = Duration.ofSeconds(240);
    private static final int MAX_CASE_ATTEMPTS = 2;

    @Autowired
    private LlmClient llmClient;
    @Autowired
    private LlmProperties llmProperties;
    @Autowired
    private EmbeddingService embeddingService;
    @Autowired
    private RagService ragService;
    @Autowired
    private RecommendService recommendService;
    @Autowired
    private AiAnalysisService aiAnalysisService;
    @Autowired
    private QuestionMapper questionMapper;
    @Autowired
    private AiAnalysisMapper aiAnalysisMapper;
    @Autowired
    private KnowledgePointMapper knowledgePointMapper;
    @Autowired
    private JdbcTemplate jdbcTemplate;
    @Autowired
    private ObjectMapper objectMapper;

    private Long experimentUserId;

    @AfterAll
    void clearContext() {
        UserContext.clear();
    }

    @Test
    @Timeout(value = 90, unit = TimeUnit.MINUTES)
    void runsFixedTwentySevenCaseExperiment() throws Exception {
        verifyRealModelConfiguration();
        List<Gate5Dataset.Case> cases = Gate5Dataset.load(objectMapper);
        String datasetSha256 = sha256(Gate5Dataset.datasetPath());
        Path resultsDirectory = Gate5Dataset.gate5Directory().resolve("results");
        Files.createDirectories(resultsDirectory);
        Gate5Models.Checkpoint checkpoint = loadCheckpoint(resultsDirectory, datasetSha256);
        ChatPacer chatPacer = new ChatPacer(modelGapSeconds());

        experimentUserId = recreateExperimentUser();
        UserContext.set(new LoginUser(experimentUserId, "student"));
        Map<String, Question> questions = createAllQuestions(cases);

        Map<String, String> embeddingFailures = prepareCompleteEmbeddingPool(cases, questions);
        saveEmbeddingAudit(resultsDirectory, questions, embeddingFailures);
        assertThat(embeddingFailures)
                .as("27 题完整 embedding 候选池必须准备成功")
                .isEmpty();

        Map<String, Gate5Models.RetrievalResult> retrievals = benchmarkRag(cases, questions);
        Map<Long, KnowledgePoint> knowledgePoints = loadKnowledgePoints();
        Map<String, Gate5Models.AnalysisResult> analyses = runProductionAnalyses(
                cases, questions, knowledgePoints, checkpoint, resultsDirectory, chatPacer);
        Map<String, Gate5Models.RecommendResult> recommendations = benchmarkRecommendations(cases, questions);
        List<Gate5Models.AblationPair> ablations = runAblations(
                cases, questions, retrievals, checkpoint, resultsDirectory, chatPacer);

        List<Gate5Models.CaseResult> caseResults = cases.stream()
                .map(item -> new Gate5Models.CaseResult(
                        item,
                        questions.get(item.caseId()).getId(),
                        retrievals.get(item.caseId()),
                        analyses.get(item.caseId()),
                        recommendations.get(item.caseId())))
                .toList();
        Gate5Models.ExperimentResult result = new Gate5Models.ExperimentResult(
                "Gate5 20-50题小规模AI/RAG实验",
                Instant.now().toString(),
                gitCommit(),
                datasetSha256,
                llmClient.model(),
                llmProperties.getEmbeddingModel(),
                llmProperties.getEmbeddingDimensions(),
                questions.size() - embeddingFailures.size(),
                embeddingFailures.size(),
                caseResults,
                ablations,
                List.copyOf(checkpoint.failureHistory));
        new Gate5ResultWriter(objectMapper).write(Gate5Dataset.gate5Directory(), result);

        printProgress("complete", Map.of(
                "date", LocalDate.now().toString(),
                "cases", cases.size(),
                "analysisSuccess", analyses.values().stream().filter(Gate5Models.AnalysisResult::successful).count(),
                "analysisFailure", analyses.values().stream().filter(value -> !value.successful()).count(),
                "ablationOutputs", ablations.size() * 2));
    }

    private void verifyRealModelConfiguration() {
        assertThat(llmClient).isInstanceOf(OpenAiCompatibleLlmClient.class);
        assertThat(llmProperties.getProvider()).isEqualTo("glm");
        assertThat(llmClient.model()).isEqualTo("glm-4.7-flash");
        assertThat(llmProperties.getEmbeddingModel()).isEqualTo("embedding-3");
        assertThat(llmProperties.getEmbeddingDimensions()).isEqualTo(REQUIRED_DIMENSIONS);
    }

    private Long recreateExperimentUser() {
        List<Long> existingIds = jdbcTemplate.queryForList(
                "SELECT id FROM `user` WHERE username = ?", Long.class, EXPERIMENT_USERNAME);
        existingIds.forEach(this::cleanupExperimentUserByExactId);

        KeyHolder keyHolder = new GeneratedKeyHolder();
        jdbcTemplate.update(connection -> {
            var statement = connection.prepareStatement("""
                    INSERT INTO `user` (username, password, nickname, role, class_name, status)
                    VALUES (?, 'gate5-not-used', 'Gate5实验学生', 'student', 'Gate5隔离实验', 1)
                    """, Statement.RETURN_GENERATED_KEYS);
            statement.setString(1, EXPERIMENT_USERNAME);
            return statement;
        }, keyHolder);
        return Objects.requireNonNull(keyHolder.getKey()).longValue();
    }

    private void cleanupExperimentUserByExactId(Long userId) {
        List<Long> questionIds = jdbcTemplate.queryForList(
                "SELECT id FROM question WHERE user_id = ?", Long.class, userId);
        for (Long questionId : questionIds) {
            jdbcTemplate.update("DELETE FROM practice_record WHERE question_id = ?", questionId);
            jdbcTemplate.update("DELETE FROM review_plan WHERE question_id = ?", questionId);
            jdbcTemplate.update("DELETE FROM variant_question WHERE question_id = ?", questionId);
            jdbcTemplate.update("DELETE FROM ai_analysis WHERE question_id = ?", questionId);
            jdbcTemplate.update("DELETE FROM question WHERE id = ?", questionId);
        }
        jdbcTemplate.update("DELETE FROM practice_record WHERE user_id = ?", userId);
        jdbcTemplate.update("DELETE FROM message WHERE user_id = ?", userId);
        jdbcTemplate.update("DELETE FROM `user` WHERE id = ? AND username = ?", userId, EXPERIMENT_USERNAME);
    }

    private Map<String, Question> createAllQuestions(List<Gate5Dataset.Case> cases) {
        Map<String, Question> result = new LinkedHashMap<>();
        for (Gate5Dataset.Case item : cases) {
            Question question = new Question();
            question.setUserId(experimentUserId);
            question.setSubjectId(item.subjectId());
            question.setStem(item.stem());
            question.setAnswer(item.correctAnswer());
            question.setSource(EXPERIMENT_SOURCE + ":" + item.caseId());
            question.setMastery(0);
            question.setStatus(1);
            questionMapper.insert(question);
            result.put(item.caseId(), question);
        }
        return result;
    }

    private Map<String, String> prepareCompleteEmbeddingPool(
            List<Gate5Dataset.Case> cases, Map<String, Question> questions) throws Exception {
        Map<String, String> failures = new LinkedHashMap<>();
        for (Gate5Dataset.Case item : cases) {
            Question question = questions.get(item.caseId());
            Exception lastFailure = null;
            for (int attempt = 1; attempt <= MAX_CASE_ATTEMPTS; attempt++) {
                try {
                    List<Double> vector = embeddingService.embed(question.getStem());
                    assertValidVector(vector);
                    String serialized = objectMapper.writeValueAsString(vector);
                    jdbcTemplate.update("UPDATE question SET embedding = ? WHERE id = ? AND user_id = ?",
                            serialized, question.getId(), experimentUserId);
                    question.setEmbedding(serialized);
                    printProgress("embedding", Map.of(
                            "caseId", item.caseId(), "attempt", attempt,
                            "dimensions", vector.size(), "finite", true));
                    lastFailure = null;
                    break;
                } catch (Exception failure) {
                    lastFailure = failure;
                    printProgress("embedding-failure", Map.of(
                            "caseId", item.caseId(), "attempt", attempt,
                            "reason", safeFailure(failure)));
                }
            }
            if (lastFailure != null) {
                failures.put(item.caseId(), safeFailure(lastFailure));
            }
        }
        return failures;
    }

    private void assertValidVector(List<Double> vector) {
        assertThat(vector).hasSize(REQUIRED_DIMENSIONS)
                .allSatisfy(value -> assertThat(value).isNotNull().isFinite());
    }

    private void saveEmbeddingAudit(
            Path resultsDirectory, Map<String, Question> questions, Map<String, String> failures) throws Exception {
        Map<String, Object> audit = new LinkedHashMap<>();
        audit.put("model", llmProperties.getEmbeddingModel());
        audit.put("requiredDimensions", REQUIRED_DIMENSIONS);
        audit.put("total", questions.size());
        audit.put("success", questions.size() - failures.size());
        audit.put("failure", failures.size());
        audit.put("allFinite", failures.isEmpty());
        audit.put("failures", failures);
        objectMapper.writerWithDefaultPrettyPrinter()
                .writeValue(resultsDirectory.resolve("embedding-audit.json").toFile(), audit);
    }

    private Map<String, Gate5Models.RetrievalResult> benchmarkRag(
            List<Gate5Dataset.Case> cases, Map<String, Question> questions) {
        Map<Long, String> caseIdByQuestionId = questions.entrySet().stream().collect(Collectors.toMap(
                entry -> entry.getValue().getId(), Map.Entry::getKey));
        Map<String, Gate5Dataset.Case> caseById = cases.stream().collect(Collectors.toMap(
                Gate5Dataset.Case::caseId, Function.identity()));
        Map<String, Gate5Models.RetrievalResult> result = new LinkedHashMap<>();
        for (Gate5Dataset.Case item : cases) {
            Question source = questionMapper.selectById(questions.get(item.caseId()).getId());
            List<Question> retrieved = ragService.retrieveSimilar(source, 3);
            List<String> retrievedCaseIds = retrieved.stream()
                    .map(Question::getId).map(caseIdByQuestionId::get).toList();
            List<String> groups = retrievedCaseIds.stream()
                    .map(caseById::get).map(Gate5Dataset.Case::relevanceGroup).toList();
            Gate5Metrics.Retrieval metrics = Gate5Metrics.retrieval(
                    groups, item.relevanceGroup(), RELEVANT_POOL_SIZE);
            Gate5Models.RetrievalResult retrieval = new Gate5Models.RetrievalResult(
                    retrievedCaseIds,
                    retrieved.stream().map(Question::getId).toList(),
                    groups,
                    metrics.firstRelevantRank(),
                    metrics.hit(),
                    metrics.recall(),
                    metrics.mrr(),
                    metrics.relevantCount());
            result.put(item.caseId(), retrieval);
            printProgress("rag", Map.of(
                    "caseId", item.caseId(), "top3", retrievedCaseIds,
                    "hit", metrics.hit(), "recall", metrics.recall(), "mrr", metrics.mrr()));
        }
        return result;
    }

    private Map<String, Gate5Models.AnalysisResult> runProductionAnalyses(
            List<Gate5Dataset.Case> cases,
            Map<String, Question> questions,
            Map<Long, KnowledgePoint> knowledgePoints,
            Gate5Models.Checkpoint checkpoint,
            Path resultsDirectory,
            ChatPacer chatPacer) throws Exception {
        Map<String, Gate5Models.AnalysisResult> results = new LinkedHashMap<>();
        Map<Long, String> caseIdByQuestionId = questions.entrySet().stream().collect(Collectors.toMap(
                entry -> entry.getValue().getId(), Map.Entry::getKey));
        for (Gate5Dataset.Case item : cases) {
            Question question = questions.get(item.caseId());
            Gate5Models.AnalysisResult saved = checkpoint.analyses.get(item.caseId());
            if (saved != null && saved.successful()) {
                Gate5Models.AnalysisResult hydrated = hydrateSavedAnalysis(
                        item, question, saved, questions, knowledgePoints);
                results.put(item.caseId(), hydrated);
                printProgress("analysis-resume", Map.of("caseId", item.caseId(), "status", 1));
                continue;
            }

            Gate5Models.AnalysisResult finalResult = null;
            for (int attempt = 1; attempt <= MAX_CASE_ATTEMPTS; attempt++) {
                chatPacer.awaitTurn();
                long started = System.nanoTime();
                try {
                    aiAnalysisService.trigger(question.getId());
                    AiAnalysis analysis = waitForAnalysis(question.getId(), ANALYSIS_TIMEOUT);
                    chatPacer.markCompleted();
                    finalResult = captureAnalysis(
                            item, question.getId(), analysis, knowledgePoints, caseIdByQuestionId,
                            elapsedMillis(started));
                    if (finalResult.successful()) {
                        break;
                    }
                    recordFailure(checkpoint, "analysis", item.caseId(), null,
                            finalResult.failureReason());
                } catch (Exception failure) {
                    chatPacer.markCompleted();
                    String reason = safeFailure(failure);
                    finalResult = failedAnalysis(item, question.getId(), elapsedMillis(started), reason);
                    recordFailure(checkpoint, "analysis", item.caseId(), null, reason);
                }
                saveCheckpoint(resultsDirectory, checkpoint);
            }
            results.put(item.caseId(), finalResult);
            if (finalResult != null && finalResult.successful()) {
                checkpoint.analyses.put(item.caseId(), finalResult);
            }
            saveCheckpoint(resultsDirectory, checkpoint);
            printProgress("analysis", Map.of(
                    "caseId", item.caseId(),
                    "status", finalResult == null ? -1 : finalResult.status(),
                    "exactMatch", finalResult != null && finalResult.exactMatch(),
                    "coverage", finalResult == null ? 0.0 : finalResult.conceptCoverage()));
        }
        return results;
    }

    private Gate5Models.AnalysisResult hydrateSavedAnalysis(
            Gate5Dataset.Case item,
            Question question,
            Gate5Models.AnalysisResult saved,
            Map<String, Question> questions,
            Map<Long, KnowledgePoint> knowledgePoints) throws Exception {
        List<Long> referenceIds = saved.referenceCaseIds().stream()
                .map(questions::get).filter(Objects::nonNull).map(Question::getId).toList();
        jdbcTemplate.update("""
                UPDATE question SET knowledge_point_id = ?, difficulty = ? WHERE id = ? AND user_id = ?
                """, saved.predictedKnowledgePointId(), saved.difficulty(), question.getId(), experimentUserId);
        jdbcTemplate.update("""
                INSERT INTO ai_analysis
                    (question_id, knowledge_point_id, error_cause, `analysis`, reference_ids, llm_model, status)
                VALUES (?, ?, ?, ?, ?, ?, 1)
                """,
                question.getId(), saved.predictedKnowledgePointId(), saved.errorCause(), saved.analysis(),
                objectMapper.writeValueAsString(referenceIds), saved.llmModel());
        KnowledgePoint kp = knowledgePoints.get(saved.predictedKnowledgePointId());
        return new Gate5Models.AnalysisResult(
                item.caseId(), question.getId(), saved.predictedKnowledgePointId(),
                kp == null ? saved.predictedKnowledgePointName() : kp.getName(),
                saved.predictedKnowledgePointId() != null
                        && saved.predictedKnowledgePointId() == item.expectedKnowledgePointId(),
                saved.difficulty(), 1, saved.llmModel(), saved.errorCause(), saved.analysis(),
                saved.referenceCaseIds(), saved.durationMs(), null,
                saved.conceptHit(), saved.conceptTotal(), saved.conceptCoverage());
    }

    private AiAnalysis waitForAnalysis(Long questionId, Duration timeout) throws InterruptedException {
        long deadline = System.nanoTime() + timeout.toNanos();
        while (System.nanoTime() < deadline) {
            AiAnalysis analysis = aiAnalysisMapper.selectOne(new LambdaQueryWrapper<AiAnalysis>()
                    .eq(AiAnalysis::getQuestionId, questionId));
            if (analysis != null && analysis.getStatus() != null && analysis.getStatus() != 0) {
                return analysis;
            }
            Thread.sleep(750);
        }
        throw new IllegalStateException("AnalysisTimeout");
    }

    private Gate5Models.AnalysisResult captureAnalysis(
            Gate5Dataset.Case item,
            long questionId,
            AiAnalysis analysis,
            Map<Long, KnowledgePoint> knowledgePoints,
            Map<Long, String> caseIdByQuestionId,
            long durationMs) throws Exception {
        if (analysis == null || !Objects.equals(analysis.getStatus(), 1)) {
            return failedAnalysis(item, questionId, durationMs,
                    analysis == null ? "MissingAnalysisRecord" : "AnalysisStatus" + analysis.getStatus());
        }
        String combined = analysis.getErrorCause() + "\n" + analysis.getAnalysis();
        Gate5Metrics.Coverage coverage = Gate5Metrics.conceptCoverage(combined, item.errorConceptGroups());
        KnowledgePoint predicted = knowledgePoints.get(analysis.getKnowledgePointId());
        List<Long> referenceIds = StringUtils.hasText(analysis.getReferenceIds())
                ? objectMapper.readValue(analysis.getReferenceIds(), new TypeReference<>() {
                })
                : List.of();
        List<String> referenceCaseIds = referenceIds.stream()
                .map(caseIdByQuestionId::get).filter(Objects::nonNull).toList();
        Question updatedQuestion = questionMapper.selectById(questionId);
        return new Gate5Models.AnalysisResult(
                item.caseId(), questionId, analysis.getKnowledgePointId(),
                predicted == null ? null : predicted.getName(),
                Objects.equals(analysis.getKnowledgePointId(), item.expectedKnowledgePointId()),
                updatedQuestion.getDifficulty(), analysis.getStatus(), analysis.getLlmModel(),
                analysis.getErrorCause(), analysis.getAnalysis(), referenceCaseIds,
                durationMs, null, coverage.hitGroups(), coverage.totalGroups(), coverage.coverage());
    }

    private Gate5Models.AnalysisResult failedAnalysis(
            Gate5Dataset.Case item, long questionId, long durationMs, String reason) {
        return new Gate5Models.AnalysisResult(
                item.caseId(), questionId, null, null, false, null, 2,
                llmClient.model(), null, null, List.of(), durationMs, reason,
                0, item.errorConceptGroups().size(), 0.0);
    }

    private Map<String, Gate5Models.RecommendResult> benchmarkRecommendations(
            List<Gate5Dataset.Case> cases, Map<String, Question> questions) {
        Map<Long, String> caseIdByQuestionId = questions.entrySet().stream().collect(Collectors.toMap(
                entry -> entry.getValue().getId(), Map.Entry::getKey));
        Map<String, Gate5Dataset.Case> caseById = cases.stream().collect(Collectors.toMap(
                Gate5Dataset.Case::caseId, Function.identity()));
        Map<String, Gate5Models.RecommendResult> results = new LinkedHashMap<>();
        for (Gate5Dataset.Case item : cases) {
            List<Question> recommended = recommendService.similar(questions.get(item.caseId()).getId());
            List<String> caseIds = recommended.stream().map(Question::getId).map(caseIdByQuestionId::get).toList();
            List<String> groups = caseIds.stream().map(caseById::get)
                    .map(Gate5Dataset.Case::relevanceGroup).toList();
            Gate5Metrics.Retrieval metrics = Gate5Metrics.retrieval(
                    groups, item.relevanceGroup(), RELEVANT_POOL_SIZE);
            results.put(item.caseId(), new Gate5Models.RecommendResult(
                    caseIds,
                    recommended.stream().map(Question::getId).toList(),
                    groups,
                    recommended.size(),
                    metrics.hit(),
                    metrics.recall(),
                    metrics.relevantCount()));
        }
        return results;
    }

    private List<Gate5Models.AblationPair> runAblations(
            List<Gate5Dataset.Case> cases,
            Map<String, Question> questions,
            Map<String, Gate5Models.RetrievalResult> retrievals,
            Gate5Models.Checkpoint checkpoint,
            Path resultsDirectory,
            ChatPacer chatPacer) throws Exception {
        Map<Long, Question> questionById = questions.values().stream().collect(Collectors.toMap(
                Question::getId, Function.identity()));
        List<Gate5Models.AblationPair> pairs = new ArrayList<>();
        for (Gate5Dataset.Case item : cases.stream().filter(Gate5Dataset.Case::ragAblation).toList()) {
            Gate5Models.AblationOutput off = runAblationCondition(
                    item, "OFF", List.of(), checkpoint, resultsDirectory, chatPacer);
            List<Question> references = retrievals.get(item.caseId()).questionIds().stream()
                    .map(questionById::get).filter(Objects::nonNull).toList();
            Gate5Models.AblationOutput on = runAblationCondition(
                    item, "ON", references, checkpoint, resultsDirectory, chatPacer);
            pairs.add(new Gate5Models.AblationPair(item.caseId(), off, on));
        }
        return pairs;
    }

    private Gate5Models.AblationOutput runAblationCondition(
            Gate5Dataset.Case item,
            String condition,
            List<Question> references,
            Gate5Models.Checkpoint checkpoint,
            Path resultsDirectory,
            ChatPacer chatPacer) throws Exception {
        String key = item.caseId() + ":" + condition;
        Gate5Models.AblationOutput saved = checkpoint.ablations.get(key);
        if (saved != null && saved.successful()) {
            printProgress("ablation-resume", Map.of("caseId", item.caseId(), "condition", condition));
            return saved;
        }

        Gate5Models.AblationOutput finalOutput = null;
        for (int attempt = 1; attempt <= MAX_CASE_ATTEMPTS; attempt++) {
            chatPacer.awaitTurn();
            long started = System.nanoTime();
            try {
                String content = llmClient.chat(buildAblationPrompt(item, references));
                chatPacer.markCompleted();
                finalOutput = parseAblationOutput(
                        item, condition, content, elapsedMillis(started));
                if (finalOutput.successful()) {
                    break;
                }
                recordFailure(checkpoint, "ablation", item.caseId(), condition,
                        finalOutput.failureReason());
            } catch (Exception failure) {
                chatPacer.markCompleted();
                String reason = safeFailure(failure);
                finalOutput = failedAblation(item, condition, elapsedMillis(started), reason);
                recordFailure(checkpoint, "ablation", item.caseId(), condition, reason);
            }
            saveCheckpoint(resultsDirectory, checkpoint);
        }
        if (finalOutput != null && finalOutput.successful()) {
            checkpoint.ablations.put(key, finalOutput);
        }
        saveCheckpoint(resultsDirectory, checkpoint);
        printProgress("ablation", Map.of(
                "caseId", item.caseId(), "condition", condition,
                "schemaSuccess", finalOutput != null && finalOutput.schemaSuccess(),
                "coverage", finalOutput == null ? 0.0 : finalOutput.conceptCoverage()));
        return finalOutput;
    }

    private String buildAblationPrompt(Gate5Dataset.Case item, List<Question> references) {
        StringBuilder prompt = new StringBuilder();
        prompt.append("受控错题分析实验。\n")
                .append("题干：").append(item.stem()).append('\n')
                .append("学生错误作答：").append(item.wrongAnswer()).append('\n')
                .append("正确答案：").append(item.correctAnswer()).append('\n')
                .append("候选知识点：\n");
        loadKnowledgePoints().values().stream()
                .filter(kp -> Objects.equals(kp.getSubjectId(), item.subjectId()))
                .forEach(kp -> prompt.append(kp.getId()).append(':').append(kp.getName()).append('\n'));
        if (!references.isEmpty()) {
            prompt.append("检索参考题上下文：\n");
            for (Question reference : references) {
                prompt.append("- ").append(reference.getStem())
                        .append("；正确答案：").append(reference.getAnswer()).append('\n');
            }
        }
        prompt.append("输出要求：只输出一个 JSON 对象；必须且仅包含 knowledgePointId、errorCause、analysis、difficulty 四个字段；")
                .append("knowledgePointId 必须是候选数字 ID；errorCause 与 analysis 必须是非空中文字符串；")
                .append("difficulty 必须是 1-5 的整数。")
                .append("严格结构：{\"knowledgePointId\":候选数字ID,\"errorCause\":\"错因\",\"analysis\":\"解析\",\"difficulty\":3}");
        return prompt.toString();
    }

    private Gate5Models.AblationOutput parseAblationOutput(
            Gate5Dataset.Case item, String condition, String content, long durationMs) {
        try {
            JsonNode json = objectMapper.readTree(stripFence(content));
            boolean schemaSuccess = json.isObject()
                    && json.size() == 4
                    && json.path("knowledgePointId").isIntegralNumber()
                    && json.path("errorCause").isTextual()
                    && StringUtils.hasText(json.path("errorCause").asText())
                    && json.path("analysis").isTextual()
                    && StringUtils.hasText(json.path("analysis").asText())
                    && json.path("difficulty").isIntegralNumber()
                    && json.path("difficulty").asInt() >= 1
                    && json.path("difficulty").asInt() <= 5;
            if (!schemaSuccess) {
                return failedAblation(item, condition, durationMs, "SchemaValidationFailure");
            }
            String errorCause = json.path("errorCause").asText().trim();
            String analysis = json.path("analysis").asText().trim();
            Gate5Metrics.Coverage coverage = Gate5Metrics.conceptCoverage(
                    errorCause + "\n" + analysis, item.errorConceptGroups());
            return new Gate5Models.AblationOutput(
                    condition, true, errorCause, analysis,
                    errorCause.length() + analysis.length(),
                    coverage.hitGroups(), coverage.totalGroups(), coverage.coverage(),
                    durationMs, null);
        } catch (Exception failure) {
            return failedAblation(item, condition, durationMs, "JsonParseFailure");
        }
    }

    private Gate5Models.AblationOutput failedAblation(
            Gate5Dataset.Case item, String condition, long durationMs, String reason) {
        return new Gate5Models.AblationOutput(
                condition, false, null, null, 0, 0,
                item.errorConceptGroups().size(), 0.0, durationMs, reason);
    }

    private Map<Long, KnowledgePoint> loadKnowledgePoints() {
        return knowledgePointMapper.selectList(new LambdaQueryWrapper<KnowledgePoint>()
                        .ne(KnowledgePoint::getParentId, 0))
                .stream().collect(Collectors.toMap(KnowledgePoint::getId, Function.identity()));
    }

    private Gate5Models.Checkpoint loadCheckpoint(Path resultsDirectory, String datasetSha256) throws Exception {
        Path path = resultsDirectory.resolve("checkpoint.json");
        if (!Files.isRegularFile(path)) {
            return new Gate5Models.Checkpoint(datasetSha256);
        }
        Gate5Models.Checkpoint checkpoint = objectMapper.readValue(path.toFile(), Gate5Models.Checkpoint.class);
        if (!Objects.equals(datasetSha256, checkpoint.datasetSha256)) {
            throw new IllegalStateException("数据集已变化，拒绝复用旧 Gate5 checkpoint");
        }
        return checkpoint;
    }

    private void saveCheckpoint(Path resultsDirectory, Gate5Models.Checkpoint checkpoint) throws Exception {
        objectMapper.writerWithDefaultPrettyPrinter()
                .writeValue(resultsDirectory.resolve("checkpoint.json").toFile(), checkpoint);
    }

    private void recordFailure(
            Gate5Models.Checkpoint checkpoint, String phase, String caseId, String condition, String reason) {
        checkpoint.failureHistory.add(new Gate5Models.FailureEvent(
                phase, caseId, condition, Instant.now().toString(), reason));
    }

    private int modelGapSeconds() {
        String configured = System.getenv("GATE5_MODEL_GAP_SECONDS");
        if (!StringUtils.hasText(configured)) {
            return 15;
        }
        int seconds = Integer.parseInt(configured.trim());
        if (seconds < 0 || seconds > 120) {
            throw new IllegalArgumentException("GATE5_MODEL_GAP_SECONDS 必须在 0-120 之间");
        }
        return seconds;
    }

    private String sha256(Path path) throws Exception {
        byte[] digest = MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path));
        return HexFormat.of().formatHex(digest);
    }

    private String gitCommit() {
        try {
            Process process = new ProcessBuilder("git", "rev-parse", "HEAD")
                    .directory(Gate5Dataset.gate5Directory().getParent().getParent().getParent().toFile())
                    .redirectErrorStream(true)
                    .start();
            String output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8).trim();
            return process.waitFor() == 0 ? output : "unknown";
        } catch (Exception failure) {
            return "unknown";
        }
    }

    private String safeFailure(Exception failure) {
        if (failure instanceof RestClientResponseException response) {
            return failure.getClass().getSimpleName() + "-HTTP-" + response.getStatusCode().value();
        }
        return failure.getClass().getSimpleName();
    }

    private String stripFence(String content) {
        String value = content == null ? "" : content.trim();
        if (value.startsWith("```")) {
            return value.replaceFirst("(?i)^```\\s*(?:json)?\\s*", "")
                    .replaceFirst("\\s*```$", "");
        }
        return value;
    }

    private long elapsedMillis(long started) {
        return TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - started);
    }

    private void printProgress(String phase, Map<String, ?> values) {
        try {
            Map<String, Object> safe = new LinkedHashMap<>(values);
            safe.put("phase", phase);
            System.out.println("GATE5 " + objectMapper.writeValueAsString(safe));
            System.out.flush();
        } catch (Exception ignored) {
            System.out.println("GATE5 {\"phase\":\"progress-serialization-failure\"}");
        }
    }

    private static final class ChatPacer {
        private final long gapMillis;
        private long lastCompletedAt;

        private ChatPacer(int gapSeconds) {
            this.gapMillis = TimeUnit.SECONDS.toMillis(gapSeconds);
        }

        private void awaitTurn() throws InterruptedException {
            long remaining = gapMillis - (System.currentTimeMillis() - lastCompletedAt);
            if (lastCompletedAt > 0 && remaining > 0) {
                Thread.sleep(remaining);
            }
        }

        private void markCompleted() {
            lastCompletedAt = System.currentTimeMillis();
        }
    }
}
