package com.example.wrongbook.experiment.gate5;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

final class Gate5Models {

    private Gate5Models() {
    }

    record RetrievalResult(
            List<String> caseIds,
            List<Long> questionIds,
            List<String> groups,
            int firstRelevantRank,
            double hitAt3,
            double recallAt3,
            double mrrAt3,
            int relevantCount) {
    }

    record AnalysisResult(
            String caseId,
            long questionId,
            Long predictedKnowledgePointId,
            String predictedKnowledgePointName,
            boolean exactMatch,
            Integer difficulty,
            Integer status,
            String llmModel,
            String errorCause,
            String analysis,
            List<String> referenceCaseIds,
            long durationMs,
            String failureReason,
            int conceptHit,
            int conceptTotal,
            double conceptCoverage) {

        boolean successful() {
            return status != null && status == 1 && failureReason == null;
        }
    }

    record RecommendResult(
            List<String> caseIds,
            List<Long> questionIds,
            List<String> groups,
            int actualK,
            double hitAt5,
            double recallAt5,
            int relevantCount) {
    }

    record AblationOutput(
            String condition,
            boolean schemaSuccess,
            String errorCause,
            String analysis,
            int responseLength,
            int conceptHit,
            int conceptTotal,
            double conceptCoverage,
            long durationMs,
            String failureReason) {

        boolean successful() {
            return schemaSuccess && failureReason == null;
        }
    }

    record AblationPair(String caseId, AblationOutput ragOff, AblationOutput ragOn) {
    }

    record CaseResult(
            Gate5Dataset.Case dataset,
            long questionId,
            RetrievalResult rag,
            AnalysisResult analysis,
            RecommendResult recommend) {
    }

    record ExperimentResult(
            String experiment,
            String generatedAt,
            String gitCommit,
            String datasetSha256,
            String chatModel,
            String embeddingModel,
            int embeddingDimensions,
            int embeddingSuccess,
            int embeddingFailure,
            List<CaseResult> cases,
            List<AblationPair> ablations,
            List<FailureEvent> failureHistory) {
    }

    record FailureEvent(
            String phase,
            String caseId,
            String condition,
            String timestamp,
            String reason) {
    }

    static final class Checkpoint {
        public String datasetSha256;
        public Map<String, AnalysisResult> analyses = new LinkedHashMap<>();
        public Map<String, AblationOutput> ablations = new LinkedHashMap<>();
        public List<FailureEvent> failureHistory = new ArrayList<>();

        public Checkpoint() {
        }

        Checkpoint(String datasetSha256) {
            this.datasetSha256 = datasetSha256;
        }
    }
}
