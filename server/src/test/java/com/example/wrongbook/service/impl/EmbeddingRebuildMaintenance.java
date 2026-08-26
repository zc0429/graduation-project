package com.example.wrongbook.service.impl;

import com.example.wrongbook.entity.Question;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.service.EmbeddingService;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.util.StringUtils;
import org.springframework.web.client.RestClientResponseException;

import java.util.ArrayList;
import java.util.List;

/** Test-scoped maintenance runner for auditing and rebuilding historical question embeddings. */
final class EmbeddingRebuildMaintenance {

    static final int REQUIRED_DIMENSIONS = 1024;

    private final QuestionMapper questionMapper;
    private final EmbeddingService embeddingService;
    private final ObjectMapper objectMapper;

    EmbeddingRebuildMaintenance(
            QuestionMapper questionMapper,
            EmbeddingService embeddingService,
            ObjectMapper objectMapper) {
        this.questionMapper = questionMapper;
        this.embeddingService = embeddingService;
        this.objectMapper = objectMapper;
    }

    List<Question> loadActiveSnapshots() {
        return questionMapper.selectActiveEmbeddingSnapshots();
    }

    AuditReport auditAll() {
        return auditSnapshots(loadActiveSnapshots());
    }

    AuditReport auditSnapshots(List<Question> questions) {
        long nullCount = 0;
        long invalidJsonCount = 0;
        long nonFiniteVectorCount = 0;
        long dimensions256 = 0;
        long dimensions512 = 0;
        long dimensions1024 = 0;
        long dimensions2048 = 0;
        long otherDimensions = 0;

        for (Question question : questions) {
            if (question.getEmbedding() == null) {
                nullCount++;
                continue;
            }
            List<Double> vector = parseStoredVector(question.getEmbedding());
            if (vector == null) {
                invalidJsonCount++;
                continue;
            }
            if (!isFiniteVector(vector)) {
                nonFiniteVectorCount++;
            }
            switch (vector.size()) {
                case 256 -> dimensions256++;
                case 512 -> dimensions512++;
                case 1024 -> dimensions1024++;
                case 2048 -> dimensions2048++;
                default -> otherDimensions++;
            }
        }

        return new AuditReport(
                questions.size(), nullCount, invalidJsonCount, nonFiniteVectorCount,
                dimensions256, dimensions512, dimensions1024, dimensions2048, otherDimensions);
    }

    RebuildReport rebuildAll() {
        return rebuildSnapshots(loadActiveSnapshots());
    }

    RebuildReport rebuildSnapshots(List<Question> questions) {
        long success = 0;
        long failed = 0;
        long stale = 0;
        long skipped = 0;
        List<ItemIssue> issues = new ArrayList<>();

        for (Question question : questions) {
            Long questionId = question.getId();
            String stemSnapshot = question.getStem();
            if (!StringUtils.hasText(stemSnapshot)) {
                skipped++;
                issues.add(new ItemIssue(
                        questionId, "skipped", "BlankStem", false, null, false));
                continue;
            }
            try {
                List<Double> vector = embeddingService.embed(stemSnapshot);
                requireValidEmbedding(vector);
                String embeddingJson = objectMapper.writeValueAsString(vector);
                int affectedRows = questionMapper.updateEmbeddingIfStemUnchanged(
                        questionId, stemSnapshot, embeddingJson);
                if (affectedRows == 1) {
                    success++;
                } else if (affectedRows == 0) {
                    stale++;
                    issues.add(new ItemIssue(
                            questionId, "stale", "StemChanged", false, null, true));
                } else {
                    throw new IllegalStateException("条件更新影响了多条题目记录");
                }
            } catch (Exception failure) {
                failed++;
                RestClientResponseException httpFailure = findHttpFailure(failure);
                issues.add(new ItemIssue(
                        questionId,
                        "failed",
                        failure.getClass().getSimpleName(),
                        httpFailure != null,
                        httpFailure == null ? null : httpFailure.getStatusCode().value(),
                        false));
            }
        }

        return new RebuildReport(
                questions.size(), success, failed, stale, skipped, List.copyOf(issues));
    }

    private List<Double> parseStoredVector(String value) {
        if (!StringUtils.hasText(value)) {
            return null;
        }
        try {
            JsonNode root = objectMapper.readTree(value);
            if (root == null || !root.isArray()) {
                return null;
            }
            List<Double> vector = new ArrayList<>(root.size());
            for (JsonNode element : root) {
                if (element.isNull()) {
                    vector.add(null);
                } else if (element.isNumber()) {
                    vector.add(element.doubleValue());
                } else {
                    return null;
                }
            }
            return vector;
        } catch (Exception ignored) {
            return null;
        }
    }

    private void requireValidEmbedding(List<Double> vector) {
        if (vector == null || vector.size() != REQUIRED_DIMENSIONS || !isFiniteVector(vector)) {
            throw new InvalidEmbeddingException();
        }
    }

    private boolean isFiniteVector(List<Double> vector) {
        return vector.stream().allMatch(value -> value != null && Double.isFinite(value));
    }

    private RestClientResponseException findHttpFailure(Throwable failure) {
        Throwable current = failure;
        while (current != null) {
            if (current instanceof RestClientResponseException responseException) {
                return responseException;
            }
            if (current.getCause() == current) {
                break;
            }
            current = current.getCause();
        }
        return null;
    }

    record AuditReport(
            long total,
            long nullCount,
            long invalidJsonCount,
            long nonFiniteVectorCount,
            long dimensions256,
            long dimensions512,
            long dimensions1024,
            long dimensions2048,
            long otherDimensions) {

        boolean isUnified1024() {
            return total == dimensions1024
                    && nullCount == 0
                    && invalidJsonCount == 0
                    && nonFiniteVectorCount == 0;
        }
    }

    record RebuildReport(
            long total,
            long success,
            long failed,
            long stale,
            long skipped,
            List<ItemIssue> issues) {
    }

    record ItemIssue(
            Long questionId,
            String outcome,
            String errorType,
            boolean httpStatusError,
            Integer httpStatus,
            boolean stale) {
    }

    private static final class InvalidEmbeddingException extends RuntimeException {
    }
}
