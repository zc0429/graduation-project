package com.example.wrongbook.service.impl;

import com.example.wrongbook.config.LlmProperties;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.service.EmbeddingService;
import com.example.wrongbook.service.LlmClient;
import com.example.wrongbook.service.RagService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.TimeUnit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.assertAll;

/**
 * Manual maintenance entry for rebuilding every active question with real GLM embedding-3 vectors.
 * Disabled unless RUN_EMBEDDING_REBUILD=true is present in the Maven process environment.
 */
@Tag("embedding-rebuild")
@SpringBootTest(properties = {
        "app.llm.provider=glm",
        "app.llm.embedding-model=embedding-3",
        "app.llm.embedding-dimensions=1024",
        "spring.sql.init.mode=never",
        "mybatis-plus.configuration.log-impl=org.apache.ibatis.logging.nologging.NoLoggingImpl"
})
@EnabledIfEnvironmentVariable(named = "RUN_EMBEDDING_REBUILD", matches = "(?i)true")
class EmbeddingRebuildMaintenanceLiveTests {

    @Autowired
    private QuestionMapper questionMapper;

    @Autowired
    private EmbeddingService embeddingService;

    @Autowired
    private RagService ragService;

    @Autowired
    private LlmClient llmClient;

    @Autowired
    private LlmProperties llmProperties;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    @Timeout(value = 30, unit = TimeUnit.MINUTES)
    void auditsRebuildsAndVerifiesAllActiveQuestionEmbeddings() throws Exception {
        assertThat(llmClient).isInstanceOf(OpenAiCompatibleLlmClient.class);
        assertThat(llmProperties.getProvider()).isEqualTo("glm");
        assertThat(llmProperties.getEmbeddingModel()).isEqualTo("embedding-3");
        assertThat(llmProperties.getEmbeddingDimensions())
                .isEqualTo(EmbeddingRebuildMaintenance.REQUIRED_DIMENSIONS);

        EmbeddingRebuildMaintenance maintenance =
                new EmbeddingRebuildMaintenance(questionMapper, embeddingService, objectMapper);
        EmbeddingRebuildMaintenance.AuditReport before = maintenance.auditAll();
        printMetric("audit-before", before);

        EmbeddingRebuildMaintenance.RebuildReport rebuild = maintenance.rebuildAll();
        printMetric("rebuild", rebuild);

        EmbeddingRebuildMaintenance.AuditReport after = maintenance.auditAll();
        printMetric("audit-after", after);

        RagSanityReport ragSanity = runRagSanity(maintenance.loadActiveSnapshots());
        printMetric("rag-sanity", ragSanity);

        assertAll("历史 embedding-3 统一重建",
                () -> assertThat(before.total()).as("重建前 active question").isPositive(),
                () -> assertThat(rebuild.total()).isEqualTo(before.total()),
                () -> assertThat(rebuild.total()).isEqualTo(
                        rebuild.success() + rebuild.failed() + rebuild.stale() + rebuild.skipped()),
                () -> assertThat(rebuild.failed()).isZero(),
                () -> assertThat(rebuild.stale()).isZero(),
                () -> assertThat(rebuild.skipped()).isZero(),
                () -> assertThat(rebuild.success()).isEqualTo(before.total()),
                () -> assertThat(after.total()).isEqualTo(before.total()),
                () -> assertThat(after.isUnified1024()).isTrue(),
                () -> assertThat(ragSanity.passed()).isTrue());
    }

    private RagSanityReport runRagSanity(List<Question> activeQuestions) {
        Map<OwnerSubjectKnowledgePoint, List<Question>> groups = new LinkedHashMap<>();
        for (Question question : activeQuestions) {
            if (question.getKnowledgePointId() == null) {
                continue;
            }
            groups.computeIfAbsent(
                    new OwnerSubjectKnowledgePoint(
                            question.getUserId(), question.getSubjectId(), question.getKnowledgePointId()),
                    ignored -> new ArrayList<>()).add(question);
        }

        for (List<Question> group : groups.values()) {
            if (group.size() < 2) {
                continue;
            }
            for (Question source : group) {
                try {
                    List<Question> results = ragService.retrieveSimilar(source, group.size() - 1);
                    if (results.isEmpty()) {
                        continue;
                    }
                    List<Double> sourceVector = parseVector(source.getEmbedding());
                    List<Double> similarities = results.stream()
                            .map(result -> cosine(sourceVector, parseVector(result.getEmbedding())))
                            .toList();
                    boolean ownerIsolated = results.stream()
                            .allMatch(result -> Objects.equals(source.getUserId(), result.getUserId()));
                    boolean subjectIsolated = results.stream()
                            .allMatch(result -> Objects.equals(source.getSubjectId(), result.getSubjectId()));
                    boolean knowledgePointAligned = results.stream()
                            .allMatch(result -> Objects.equals(
                                    source.getKnowledgePointId(), result.getKnowledgePointId()));
                    boolean sourceExcluded = results.stream()
                            .noneMatch(result -> Objects.equals(source.getId(), result.getId()));
                    boolean dimensionsValid = isValidVector(sourceVector)
                            && results.stream().map(Question::getEmbedding).map(this::parseVector)
                            .allMatch(this::isValidVector);
                    boolean cosineFinite = similarities.stream()
                            .allMatch(value -> Double.isFinite(value) && value > 0);
                    boolean descending = isDescending(similarities);
                    return new RagSanityReport(
                            true,
                            source.getId(),
                            results.stream().map(Question::getId).toList(),
                            similarities,
                            ownerIsolated,
                            subjectIsolated,
                            knowledgePointAligned,
                            sourceExcluded,
                            dimensionsValid,
                            cosineFinite,
                            descending,
                            null);
                } catch (Exception failure) {
                    return new RagSanityReport(
                            true, source.getId(), List.of(), List.of(),
                            false, false, false, false, false, false, false,
                            failure.getClass().getSimpleName());
                }
            }
        }
        return new RagSanityReport(
                false, null, List.of(), List.of(),
                false, false, false, false, false, false, false,
                "NoComparableKnowledgePointGroup");
    }

    private List<Double> parseVector(String value) {
        try {
            return objectMapper.readValue(value, new TypeReference<>() {
            });
        } catch (Exception failure) {
            throw new IllegalStateException("无法解析 sanity check 向量", failure);
        }
    }

    private boolean isValidVector(List<Double> vector) {
        return vector != null
                && vector.size() == EmbeddingRebuildMaintenance.REQUIRED_DIMENSIONS
                && vector.stream().allMatch(value -> value != null && Double.isFinite(value));
    }

    private double cosine(List<Double> first, List<Double> second) {
        if (!isValidVector(first) || !isValidVector(second)) {
            throw new IllegalArgumentException("sanity check 向量无效");
        }
        double dot = 0;
        double firstNorm = 0;
        double secondNorm = 0;
        for (int index = 0; index < first.size(); index++) {
            dot += first.get(index) * second.get(index);
            firstNorm += first.get(index) * first.get(index);
            secondNorm += second.get(index) * second.get(index);
        }
        if (firstNorm == 0 || secondNorm == 0) {
            throw new IllegalArgumentException("sanity check 向量范数为零");
        }
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

    private void printMetric(String phase, Object value) throws Exception {
        ObjectNode output = objectMapper.valueToTree(value);
        output.put("phase", phase);
        System.out.println("EMBEDDING_REBUILD " + objectMapper.writeValueAsString(output));
        System.out.flush();
    }

    private record OwnerSubjectKnowledgePoint(Long userId, Long subjectId, Long knowledgePointId) {
    }

    private record RagSanityReport(
            boolean checked,
            Long sourceQuestionId,
            List<Long> resultQuestionIds,
            List<Double> cosineScores,
            boolean ownerIsolated,
            boolean subjectIsolated,
            boolean knowledgePointAligned,
            boolean sourceExcluded,
            boolean dimensionsValid,
            boolean cosineFinite,
            boolean descending,
            String errorType) {

        boolean passed() {
            return checked
                    && !resultQuestionIds.isEmpty()
                    && ownerIsolated
                    && subjectIsolated
                    && knowledgePointAligned
                    && sourceExcluded
                    && dimensionsValid
                    && cosineFinite
                    && descending
                    && errorType == null;
        }
    }
}
