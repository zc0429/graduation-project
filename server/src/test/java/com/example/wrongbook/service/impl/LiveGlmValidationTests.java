package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.wrongbook.common.LoginUser;
import com.example.wrongbook.common.UserContext;
import com.example.wrongbook.config.LlmProperties;
import com.example.wrongbook.dto.QuestionRequest;
import com.example.wrongbook.entity.AiAnalysis;
import com.example.wrongbook.entity.KnowledgePoint;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.entity.VariantQuestion;
import com.example.wrongbook.mapper.AiAnalysisMapper;
import com.example.wrongbook.mapper.KnowledgePointMapper;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.service.AiAnalysisService;
import com.example.wrongbook.service.EmbeddingService;
import com.example.wrongbook.service.LlmClient;
import com.example.wrongbook.service.QuestionService;
import com.example.wrongbook.service.RagService;
import com.example.wrongbook.service.VariantService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.util.StringUtils;
import org.springframework.web.client.RestClientResponseException;

import java.sql.Statement;
import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.Executor;
import java.util.concurrent.TimeUnit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.assertAll;

/**
 * 真实智谱链路的手动验证入口。
 *
 * <p>默认测试不会访问网络。仅当显式设置 RUN_LIVE_LLM_TESTS=true 时启用；
 * API Key 继续由 LLM_API_KEY 环境变量提供。测试创建独立学生及错题，并在结束后物理清理。</p>
 */
@Tag("live-llm")
@SpringBootTest(properties = "app.llm.provider=glm")
@EnabledIfEnvironmentVariable(named = "RUN_LIVE_LLM_TESTS", matches = "(?i)true")
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class LiveGlmValidationTests {

    private static final String LIVE_USERNAME = "__live_glm_validation__";
    private static final long SUBJECT_ID = 1L;
    private static final Duration ANALYSIS_TIMEOUT = Duration.ofSeconds(300);
    private static final Duration CHAT_REQUEST_COOLDOWN = Duration.ofSeconds(60);
    private static final Duration EXECUTOR_IDLE_TIMEOUT = Duration.ofSeconds(180);
    private static final int MAX_STAGE_ATTEMPTS = 2;
    private static final List<AnalysisCase> ANALYSIS_CASES = List.of(
            new AnalysisCase("一次函数斜率符号",
                    "已知一次函数 y=-2x+3，学生误认为图像随 x 增大而上升。请分析错误。",
                    "图像随 x 增大而下降"),
            new AnalysisCase("二次函数判别式",
                    "解方程 x²-4x+5=0，学生写出两个实数根 1 和 3。请分析错误。",
                    "判别式小于 0，方程无实数根"),
            new AnalysisCase("三角形全等条件",
                    "学生根据两个三角形三组对应角相等，直接判断两个三角形全等。请分析错误。",
                    "AAA 只能证明相似，不能证明全等"),
            new AnalysisCase("圆的切线性质",
                    "圆 O 的半径 OA 与直线 l 交于 A，学生未证明 OA 垂直 l 就断言 l 是切线。请分析错误。",
                    "需证明圆心到直线的距离等于半径，即 OA 垂直 l"),
            new AnalysisCase("一次函数待定系数",
                    "一次函数经过点 (1,3) 和 (2,5)，学生计算斜率为 (5+3)/(2+1)。请分析错误。",
                    "斜率应为纵坐标之差除以横坐标之差，结果为 2")
    );

    @Autowired
    private LlmClient llmClient;

    @Autowired
    private LlmProperties llmProperties;

    @Autowired
    private EmbeddingService embeddingService;

    @Autowired
    private RagService ragService;

    @Autowired
    private AiAnalysisService aiAnalysisService;

    @Autowired
    private VariantService variantService;

    @Autowired
    private QuestionService questionService;

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

    @Autowired
    @Qualifier("aiTaskExecutor")
    private Executor aiTaskExecutor;

    private Long liveUserId;

    @BeforeAll
    void createIsolatedStudent() {
        cleanupPreviousRun();
        KeyHolder keyHolder = new GeneratedKeyHolder();
        jdbcTemplate.update(connection -> {
            var statement = connection.prepareStatement("""
                    INSERT INTO `user` (username, password, nickname, role, class_name, status)
                    VALUES (?, 'live-validation-not-used', 'GLM验证学生', 'student', '隔离验证', 1)
                    """, Statement.RETURN_GENERATED_KEYS);
            statement.setString(1, LIVE_USERNAME);
            return statement;
        }, keyHolder);
        liveUserId = Objects.requireNonNull(keyHolder.getKey()).longValue();
    }

    @AfterAll
    void removeIsolatedStudent() throws InterruptedException {
        try {
            if (liveUserId != null) {
                try {
                    invalidatePendingAnalyses(liveUserId);
                    awaitAiExecutorIdle(EXECUTOR_IDLE_TIMEOUT);
                } finally {
                    cleanupUser(liveUserId);
                }
            }
        } finally {
            UserContext.clear();
        }
    }

    @AfterEach
    void clearUserContext() {
        UserContext.clear();
    }

    @Test
    @Timeout(value = 45, unit = TimeUnit.MINUTES)
    void validatesRealGlmEmbeddingRagAnalysisAndVariantChain() throws Exception {
        UserContext.set(new LoginUser(liveUserId, "student"));
        assertThat(llmClient).isInstanceOf(OpenAiCompatibleLlmClient.class);
        assertThat(llmProperties.getProvider()).isEqualTo("glm");
        assertThat(llmClient.model()).isEqualTo(OpenAiCompatibleLlmClient.GLM_DEFAULT_CHAT_MODEL);
        assertThat(effectiveEmbeddingModel())
                .isEqualTo(OpenAiCompatibleLlmClient.GLM_DEFAULT_EMBEDDING_MODEL);
        assertThat(llmProperties.getEmbeddingDimensions()).isEqualTo(1024);

        List<Double> relatedVector = null;
        List<Double> distantVector = null;
        boolean embeddingRequestsSucceeded = false;
        boolean embeddingSucceeded = false;
        long embeddingStarted = System.nanoTime();
        try {
            relatedVector = embeddingService.embed("一次函数图像与斜率的关系");
            distantVector = embeddingService.embed("圆的切线垂直于经过切点的半径");
            embeddingRequestsSucceeded = true;
            double embeddingCosine = cosine(relatedVector, distantVector);
            assertValidVector(relatedVector);
            assertValidVector(distantVector);
            boolean different = !relatedVector.equals(distantVector);
            boolean cosineValid = Double.isFinite(embeddingCosine);
            embeddingSucceeded = different && cosineValid;
            printMetric("embedding", Map.of(
                    "requestSucceeded", true,
                    "requestCount", 2,
                    "model", effectiveEmbeddingModel(),
                    "dimensions", relatedVector.size(),
                    "finite", true,
                    "different", different,
                    "cosineValid", cosineValid,
                    "cosine", embeddingCosine,
                    "totalLatencyMs", elapsedMillis(embeddingStarted)));
        } catch (Exception | AssertionError failure) {
            Map<String, Object> values = failureMetric(failure, elapsedMillis(embeddingStarted));
            values.put("requestSucceeded", embeddingRequestsSucceeded);
            values.put("requestCount", 2);
            printMetric("embedding", values);
        }

        Long referenceQuestionId = createQuestion(
                "参考题：一次函数 y=3x-1 的斜率为多少？",
                "斜率为 3");
        Long distantQuestionId = createQuestion(
                "参考题：圆的切线与经过切点的半径有什么关系？",
                "二者互相垂直");
        if (embeddingSucceeded) {
            jdbcTemplate.update("UPDATE question SET embedding = ? WHERE id = ?",
                    objectMapper.writeValueAsString(relatedVector), referenceQuestionId);
            jdbcTemplate.update("UPDATE question SET embedding = ? WHERE id = ?",
                    objectMapper.writeValueAsString(distantVector), distantQuestionId);
        }

        Long ragSourceQuestionId = createQuestion(
                "检索题：一次函数 y=-2x+3 的图像随 x 增大如何变化？",
                "图像随 x 增大而下降");
        boolean ragSucceeded = false;
        long ragStarted = System.nanoTime();
        if (!embeddingSucceeded) {
            printMetric("rag", Map.of(
                    "requestSucceeded", false,
                    "skipped", true,
                    "reason", "embedding-prerequisite-failed",
                    "latencyMs", 0));
        } else try {
            List<Double> ragSourceVector = embeddingService.embed(
                    "检索题：一次函数 y=-2x+3 的图像随 x 增大如何变化？");
            assertValidVector(ragSourceVector);
            jdbcTemplate.update("UPDATE question SET embedding = ? WHERE id = ?",
                    objectMapper.writeValueAsString(ragSourceVector), ragSourceQuestionId);
            Question ragSource = questionMapper.selectById(ragSourceQuestionId);
            List<Question> ragResults = ragService.retrieveSimilar(ragSource, 3);
            boolean ownerIsolated = ragResults.stream().allMatch(question -> liveUserId.equals(question.getUserId())
                    && Objects.equals(SUBJECT_ID, question.getSubjectId()));
            boolean sourceExcluded = ragResults.stream()
                    .noneMatch(question -> ragSourceQuestionId.equals(question.getId()));
            Set<Long> resultIds = ragResults.stream().map(Question::getId)
                    .collect(java.util.stream.Collectors.toSet());
            boolean candidatesPresent = resultIds.contains(referenceQuestionId)
                    && resultIds.contains(distantQuestionId);
            List<Double> similarities = ragResults.stream()
                    .map(question -> cosine(ragSourceVector, parseVector(question.getEmbedding())))
                    .toList();
            boolean cosineValid = similarities.stream()
                    .allMatch(value -> Double.isFinite(value) && value > 0);
            boolean cosineSorted = isDescending(similarities);
            boolean distinctScores = similarities.size() >= 2
                    && similarities.getFirst() > similarities.getLast();
            boolean relatedRanksFirst = !ragResults.isEmpty()
                    && referenceQuestionId.equals(ragResults.getFirst().getId());
            ragSucceeded = ragResults.size() >= 2 && ownerIsolated && sourceExcluded
                    && candidatesPresent && cosineValid && cosineSorted
                    && distinctScores && relatedRanksFirst;
            printMetric("rag", Map.of(
                    "requestSucceeded", true,
                    "resultCount", ragResults.size(),
                    "ownerIsolated", ownerIsolated,
                    "sourceExcluded", sourceExcluded,
                    "candidatesPresent", candidatesPresent,
                    "cosineValid", cosineValid,
                    "cosineSorted", cosineSorted,
                    "distinctScores", distinctScores,
                    "relatedRanksFirst", relatedRanksFirst,
                    "latencyMs", elapsedMillis(ragStarted)));
        } catch (Exception | AssertionError failure) {
            printMetric("rag", failureMetric(failure, elapsedMillis(ragStarted)));
        }

        boolean minimalChatSucceeded = false;
        for (int attempt = 1; attempt <= MAX_STAGE_ATTEMPTS && !minimalChatSucceeded; attempt++) {
            if (attempt > 1) {
                waitForChatCooldown();
            }
            boolean chatRequestSucceeded = false;
            long chatStarted = System.nanoTime();
            try {
                String chatContent = llmClient.chat("""
                        固定连通性验证。只输出以下完全一致的 JSON 对象，不得增加、删除、翻译或改名字段：
                        {"status":"ok","purpose":"live-glm-validation"}
                        """);
                chatRequestSucceeded = true;
                boolean markdownFence = chatContent.stripLeading().startsWith("```");
                boolean rawJson = isJsonObject(chatContent);
                JsonNode chatJson = objectMapper.readTree(stripMarkdownFence(chatContent));
                boolean expectedFieldsPresent = chatJson.has("status") && chatJson.has("purpose");
                minimalChatSucceeded = "ok".equals(chatJson.path("status").asText())
                        && "live-glm-validation".equals(chatJson.path("purpose").asText());
                Map<String, Object> values = new LinkedHashMap<>();
                values.put("attempt", attempt);
                values.put("requestSucceeded", true);
                values.put("model", llmClient.model());
                values.put("jsonParsed", true);
                values.put("rawJson", rawJson);
                values.put("markdownFence", markdownFence);
                values.put("expectedFieldsPresent", expectedFieldsPresent);
                values.put("expectedValuesMatch", minimalChatSucceeded);
                values.put("latencyMs", elapsedMillis(chatStarted));
                printMetric("chat", values);
            } catch (Exception failure) {
                Map<String, Object> values = failureMetric(failure, elapsedMillis(chatStarted));
                values.put("attempt", attempt);
                values.put("requestSucceeded", chatRequestSucceeded);
                values.put("jsonParsed", false);
                printMetric("chat", values);
            }
        }

        Set<Long> validKnowledgePointIds = knowledgePointMapper.selectList(
                        new LambdaQueryWrapper<KnowledgePoint>()
                                .eq(KnowledgePoint::getSubjectId, SUBJECT_ID)
                                .ne(KnowledgePoint::getParentId, 0))
                .stream().map(KnowledgePoint::getId).collect(java.util.stream.Collectors.toSet());

        List<AnalysisOutcome> outcomes = new ArrayList<>();
        int analysisAttemptCount = 0;
        int initialFailureCount = 0;
        for (AnalysisCase analysisCase : ANALYSIS_CASES) {
            Long questionId = createQuestion(analysisCase.stem(), analysisCase.answer());
            AnalysisOutcome finalOutcome = null;
            for (int attempt = 1; attempt <= MAX_STAGE_ATTEMPTS; attempt++) {
                analysisAttemptCount++;
                waitForChatCooldown();
                long started = System.nanoTime();
                AnalysisOutcome attemptOutcome;
                try {
                    aiAnalysisService.trigger(questionId);
                    AiAnalysis analysis = waitForAnalysis(questionId, ANALYSIS_TIMEOUT);
                    Question question = questionMapper.selectById(questionId);
                    boolean parsed = analysis != null && Objects.equals(analysis.getStatus(), 1);
                    boolean knowledgePointValid = parsed
                            && analysis.getKnowledgePointId() != null
                            && validKnowledgePointIds.contains(analysis.getKnowledgePointId())
                            && Objects.equals(analysis.getKnowledgePointId(), question.getKnowledgePointId());
                    boolean difficultyValid = parsed
                            && question.getDifficulty() != null
                            && question.getDifficulty() >= 1
                            && question.getDifficulty() <= 5;
                    boolean fieldsValid = parsed
                            && StringUtils.hasText(analysis.getErrorCause())
                            && StringUtils.hasText(analysis.getAnalysis());
                    boolean embeddingValid = parsed && isValidVector(parseVector(question.getEmbedding()));
                    boolean modelConfirmed = parsed && Objects.equals(llmClient.model(), analysis.getLlmModel());
                    boolean referencesValid = parsed
                            && validReferenceIds(analysis.getReferenceIds(), liveUserId, questionId,
                            outcomes.isEmpty() ? referenceQuestionId : null);
                    attemptOutcome = new AnalysisOutcome(
                            questionId, analysisCase.name(), analysis == null ? null : analysis.getStatus(), parsed,
                            knowledgePointValid, difficultyValid, fieldsValid, embeddingValid,
                            modelConfirmed, referencesValid, elapsedMillis(started));
                    Map<String, Object> values = attemptOutcome.toMap();
                    values.put("attempt", attempt);
                    printMetric("analysis-case", values);
                } catch (InterruptedException failure) {
                    Thread.currentThread().interrupt();
                    throw failure;
                } catch (Exception failure) {
                    attemptOutcome = new AnalysisOutcome(
                            questionId, analysisCase.name(), null, false, false, false,
                            false, false, false, false, elapsedMillis(started));
                    Map<String, Object> values = attemptOutcome.toMap();
                    values.put("attempt", attempt);
                    values.putAll(failureMetric(failure, elapsedMillis(started)));
                    printMetric("analysis-case", values);
                }
                awaitAiExecutorIdle(EXECUTOR_IDLE_TIMEOUT);
                finalOutcome = attemptOutcome;
                if (attemptOutcome.fullyValid()) {
                    break;
                }
                if (attempt == 1) {
                    initialFailureCount++;
                }
            }
            outcomes.add(Objects.requireNonNull(finalOutcome));
        }

        long successCount = outcomes.stream().filter(AnalysisOutcome::parsed).count();
        long knowledgePointCount = outcomes.stream().filter(AnalysisOutcome::knowledgePointValid).count();
        long difficultyCount = outcomes.stream().filter(AnalysisOutcome::difficultyValid).count();
        long fieldsCount = outcomes.stream().filter(AnalysisOutcome::fieldsValid).count();
        long embeddingCount = outcomes.stream().filter(AnalysisOutcome::embeddingValid).count();
        long modelCount = outcomes.stream().filter(AnalysisOutcome::modelConfirmed).count();
        long referenceCount = outcomes.stream().filter(AnalysisOutcome::referencesValid).count();
        double averageLatency = outcomes.stream().mapToLong(AnalysisOutcome::latencyMs).average().orElse(0);
        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("total", outcomes.size());
        summary.put("attempts", analysisAttemptCount);
        summary.put("initialFailures", initialFailureCount);
        summary.put("success", successCount);
        summary.put("requestSuccess", successCount);
        summary.put("jsonParsed", successCount);
        summary.put("knowledgePointValid", knowledgePointCount);
        summary.put("difficultyValid", difficultyCount);
        summary.put("fieldsValid", fieldsCount);
        summary.put("embeddingValid", embeddingCount);
        summary.put("modelConfirmed", modelCount);
        summary.put("referenceIdsValid", referenceCount);
        summary.put("averageLatencyMs", averageLatency);
        printMetric("analysis-summary", summary);

        Long validatedQuestionId = outcomes.stream()
                .filter(AnalysisOutcome::fullyValid)
                .map(AnalysisOutcome::questionId)
                .findFirst()
                .orElse(ragSourceQuestionId);

        boolean variantSucceeded = false;
        for (int attempt = 1; attempt <= MAX_STAGE_ATTEMPTS && !variantSucceeded; attempt++) {
            waitForChatCooldown();
            long variantStarted = System.nanoTime();
            try {
                List<VariantQuestion> variants = variantService.generate(validatedQuestionId);
                List<VariantQuestion> persistedVariants = variantService.list(validatedQuestionId);
                boolean countValid = variants.size() == 3 && persistedVariants.size() == 3;
                boolean fieldsValid = persistedVariants.stream().allMatch(variant -> variant.getId() != null
                        && validatedQuestionId.equals(variant.getQuestionId())
                        && StringUtils.hasText(variant.getStem())
                        && StringUtils.hasText(variant.getAnswer())
                        && variant.getDifficulty() != null
                        && variant.getDifficulty() >= 1
                        && variant.getDifficulty() <= 5);
                variantSucceeded = countValid && fieldsValid;
                Map<String, Object> values = new LinkedHashMap<>();
                values.put("attempt", attempt);
                values.put("requestSucceeded", true);
                values.put("count", variants.size());
                values.put("persisted", persistedVariants.size());
                values.put("countValid", countValid);
                values.put("fieldsValid", fieldsValid);
                values.put("latencyMs", elapsedMillis(variantStarted));
                printMetric("variant", values);
            } catch (Exception failure) {
                Map<String, Object> values = failureMetric(failure, elapsedMillis(variantStarted));
                values.put("attempt", attempt);
                printMetric("variant", values);
            }
        }

        boolean embeddingStageSucceeded = embeddingSucceeded;
        boolean chatStageSucceeded = minimalChatSucceeded;
        boolean ragStageSucceeded = ragSucceeded;
        boolean variantStageSucceeded = variantSucceeded;
        assertAll("真实 GLM 全链路验证",
                () -> assertThat(embeddingStageSucceeded).as("Embedding-3 最小验证").isTrue(),
                () -> assertThat(chatStageSucceeded).as("最小 Chat JSON").isTrue(),
                () -> assertThat(ragStageSucceeded).as("真实向量 RAG").isTrue(),
                () -> assertThat(successCount).as("5 个结构化分析样本").isEqualTo(ANALYSIS_CASES.size()),
                () -> assertThat(knowledgePointCount).as("知识点归类").isEqualTo(ANALYSIS_CASES.size()),
                () -> assertThat(difficultyCount).as("难度范围").isEqualTo(ANALYSIS_CASES.size()),
                () -> assertThat(fieldsCount).as("分析字段").isEqualTo(ANALYSIS_CASES.size()),
                () -> assertThat(embeddingCount).as("分析向量").isEqualTo(ANALYSIS_CASES.size()),
                () -> assertThat(modelCount).as("模型留痕").isEqualTo(ANALYSIS_CASES.size()),
                () -> assertThat(referenceCount).as("RAG 引用").isEqualTo(ANALYSIS_CASES.size()),
                () -> assertThat(variantStageSucceeded).as("3 道变式题").isTrue());
    }

    private Long createQuestion(String stem, String answer) {
        QuestionRequest request = new QuestionRequest();
        request.setSubjectId(SUBJECT_ID);
        request.setStem(stem);
        request.setAnswer(answer);
        request.setSource("live-glm-validation");
        return questionService.create(request);
    }

    private AiAnalysis waitForAnalysis(Long questionId, Duration timeout) throws InterruptedException {
        long deadline = System.nanoTime() + timeout.toNanos();
        while (System.nanoTime() < deadline) {
            AiAnalysis analysis = aiAnalysisMapper.selectOne(
                    new LambdaQueryWrapper<AiAnalysis>().eq(AiAnalysis::getQuestionId, questionId));
            if (analysis != null && analysis.getStatus() != null && analysis.getStatus() != 0) {
                return analysis;
            }
            Thread.sleep(200);
        }
        throw new IllegalStateException("AI 解析在 " + timeout.toSeconds() + " 秒内未完成，questionId=" + questionId);
    }

    private boolean validReferenceIds(
            String value, Long ownerId, Long sourceQuestionId, Long requiredReferenceId) {
        if (!StringUtils.hasText(value)) {
            return false;
        }
        try {
            List<Long> ids = objectMapper.readValue(value, new TypeReference<>() {
            });
            if (ids.isEmpty()) {
                return false;
            }
            List<Question> references = questionMapper.selectBatchIds(ids);
            return references.size() == ids.size()
                    && (requiredReferenceId == null || ids.contains(requiredReferenceId))
                    && references.stream().allMatch(question -> ownerId.equals(question.getUserId()))
                    && references.stream().noneMatch(question -> sourceQuestionId.equals(question.getId()));
        } catch (Exception ignored) {
            return false;
        }
    }

    private List<Double> parseVector(String value) {
        if (!StringUtils.hasText(value)) {
            return null;
        }
        try {
            return objectMapper.readValue(value, new TypeReference<>() {
            });
        } catch (Exception ignored) {
            return null;
        }
    }

    private void assertValidVector(List<Double> vector) {
        assertThat(isValidVector(vector)).isTrue();
        assertThat(vector).hasSize(llmProperties.getEmbeddingDimensions());
    }

    private boolean isValidVector(List<Double> vector) {
        return vector != null
                && vector.size() == llmProperties.getEmbeddingDimensions()
                && vector.stream().allMatch(value -> value != null && Double.isFinite(value));
    }

    private double cosine(List<Double> first, List<Double> second) {
        assertThat(first).hasSameSizeAs(second);
        double dot = 0;
        double firstNorm = 0;
        double secondNorm = 0;
        for (int i = 0; i < first.size(); i++) {
            dot += first.get(i) * second.get(i);
            firstNorm += first.get(i) * first.get(i);
            secondNorm += second.get(i) * second.get(i);
        }
        assertThat(firstNorm).isPositive();
        assertThat(secondNorm).isPositive();
        return dot / (Math.sqrt(firstNorm) * Math.sqrt(secondNorm));
    }

    private boolean isDescending(List<Double> values) {
        for (int index = 1; index < values.size(); index++) {
            if (values.get(index - 1) < values.get(index)) {
                return false;
            }
        }
        return true;
    }

    private Map<String, Object> failureMetric(Throwable failure, long latencyMs) {
        Map<String, Object> values = new LinkedHashMap<>();
        values.put("requestSucceeded", false);
        values.put("errorType", failure.getClass().getSimpleName());
        values.put("latencyMs", latencyMs);
        Throwable current = failure;
        while (current != null) {
            if (current instanceof RestClientResponseException responseException) {
                values.put("httpStatus", responseException.getStatusCode().value());
                break;
            }
            if (current.getCause() == current) {
                break;
            }
            current = current.getCause();
        }
        return values;
    }

    private String effectiveEmbeddingModel() {
        return StringUtils.hasText(llmProperties.getEmbeddingModel())
                ? llmProperties.getEmbeddingModel().trim()
                : OpenAiCompatibleLlmClient.GLM_DEFAULT_EMBEDDING_MODEL;
    }

    private long elapsedMillis(long startedNanos) {
        return TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - startedNanos);
    }

    private void waitForChatCooldown() throws InterruptedException {
        Thread.sleep(CHAT_REQUEST_COOLDOWN.toMillis());
    }

    private void invalidatePendingAnalyses(Long userId) {
        jdbcTemplate.update("""
                UPDATE ai_analysis a
                JOIN question q ON q.id = a.question_id
                SET a.status = 2
                WHERE q.user_id = ? AND a.status = 0
                """, userId);
    }

    private void awaitAiExecutorIdle(Duration timeout) throws InterruptedException {
        if (!(aiTaskExecutor instanceof ThreadPoolTaskExecutor taskExecutor)) {
            throw new IllegalStateException("aiTaskExecutor 类型不支持活动任务检查");
        }
        long deadline = System.nanoTime() + timeout.toNanos();
        while (System.nanoTime() < deadline) {
            if (taskExecutor.getActiveCount() == 0 && taskExecutor.getQueueSize() == 0) {
                return;
            }
            Thread.sleep(200);
        }
        throw new IllegalStateException("aiTaskExecutor 在 " + timeout.toSeconds() + " 秒内未空闲");
    }

    private String stripMarkdownFence(String content) {
        String value = content.trim();
        if (value.startsWith("```")) {
            return value.replaceFirst("(?i)^```\\s*(?:json)?\\s*", "")
                    .replaceFirst("\\s*```$", "");
        }
        return value;
    }

    private boolean isJsonObject(String content) {
        try {
            return objectMapper.readTree(content).isObject();
        } catch (Exception ignored) {
            return false;
        }
    }

    private void printMetric(String phase, Map<String, ?> values) throws Exception {
        Map<String, Object> output = new LinkedHashMap<>();
        output.put("phase", phase);
        output.putAll(values);
        System.out.println("LIVE_GLM " + objectMapper.writeValueAsString(output));
        System.out.flush();
    }

    private void cleanupPreviousRun() {
        jdbcTemplate.queryForList(
                        "SELECT id FROM `user` WHERE username = ?", Long.class, LIVE_USERNAME)
                .forEach(this::cleanupUser);
    }

    private void cleanupUser(Long userId) {
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
        jdbcTemplate.update("DELETE FROM `user` WHERE id = ?", userId);
    }

    private record AnalysisCase(String name, String stem, String answer) {
    }

    private record AnalysisOutcome(
            Long questionId,
            String name,
            Integer analysisStatus,
            boolean parsed,
            boolean knowledgePointValid,
            boolean difficultyValid,
            boolean fieldsValid,
            boolean embeddingValid,
            boolean modelConfirmed,
            boolean referencesValid,
            long latencyMs) {

        boolean fullyValid() {
            return parsed && knowledgePointValid && difficultyValid && fieldsValid
                    && embeddingValid && modelConfirmed && referencesValid;
        }

        Map<String, Object> toMap() {
            Map<String, Object> values = new LinkedHashMap<>();
            values.put("name", name);
            values.put("analysisStatus", analysisStatus);
            values.put("parsed", parsed);
            values.put("knowledgePointValid", knowledgePointValid);
            values.put("difficultyValid", difficultyValid);
            values.put("fieldsValid", fieldsValid);
            values.put("embeddingValid", embeddingValid);
            values.put("modelConfirmed", modelConfirmed);
            values.put("referenceIdsValid", referencesValid);
            values.put("latencyMs", latencyMs);
            return values;
        }
    }
}
