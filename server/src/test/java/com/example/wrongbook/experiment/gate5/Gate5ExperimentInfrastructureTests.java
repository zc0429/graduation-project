package com.example.wrongbook.experiment.gate5;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import static org.assertj.core.api.Assertions.assertThat;

class Gate5ExperimentInfrastructureTests {

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Test
    void fixedDatasetHasRequiredDistributionAndLockedLabels() throws Exception {
        List<Gate5Dataset.Case> cases = Gate5Dataset.load(objectMapper);

        assertThat(cases).hasSize(27);
        assertThat(cases.stream().map(Gate5Dataset.Case::caseId)).doesNotHaveDuplicates();
        assertThat(cases).allSatisfy(item -> {
            assertThat(item.caseId()).isNotBlank();
            assertThat(item.subjectName()).isNotBlank();
            assertThat(item.expectedKnowledgePointName()).isNotBlank();
            assertThat(item.stem()).isNotBlank();
            assertThat(item.wrongAnswer()).isNotBlank();
            assertThat(item.correctAnswer()).isNotBlank();
            assertThat(item.errorConceptGroups()).isNotEmpty().allSatisfy(group ->
                    assertThat(group).isNotEmpty().allSatisfy(term -> assertThat(term).isNotBlank()));
            assertThat(item.relevanceGroup()).isEqualTo("KP-" + item.expectedKnowledgePointId());
        });

        Map<Long, Long> countByKnowledgePoint = cases.stream().collect(Collectors.groupingBy(
                Gate5Dataset.Case::expectedKnowledgePointId, Collectors.counting()));
        assertThat(countByKnowledgePoint).containsOnly(
                Map.entry(2L, 3L), Map.entry(3L, 3L), Map.entry(5L, 3L),
                Map.entry(6L, 3L), Map.entry(8L, 3L), Map.entry(9L, 3L),
                Map.entry(11L, 3L), Map.entry(13L, 3L), Map.entry(14L, 3L));

        List<Gate5Dataset.Case> ablation = cases.stream().filter(Gate5Dataset.Case::ragAblation).toList();
        assertThat(ablation).hasSize(6);
        assertThat(ablation.stream().map(Gate5Dataset.Case::subjectId).collect(Collectors.toSet()))
                .containsExactlyInAnyOrder(1L, 2L, 3L);
        assertThat(ablation.stream().collect(Collectors.groupingBy(
                Gate5Dataset.Case::subjectId, Collectors.counting())))
                .containsOnly(Map.entry(1L, 2L), Map.entry(2L, 2L), Map.entry(3L, 2L));
    }

    @Test
    void calculatesRetrievalMetricsAtK() {
        Gate5Metrics.Retrieval metrics = Gate5Metrics.retrieval(
                List.of("KP-9", "KP-8", "KP-8"), "KP-8", 2);

        assertThat(metrics.hit()).isEqualTo(1.0);
        assertThat(metrics.recall()).isEqualTo(1.0);
        assertThat(metrics.firstRelevantRank()).isEqualTo(2);
        assertThat(metrics.mrr()).isEqualTo(0.5);
        assertThat(metrics.relevantCount()).isEqualTo(2);
    }

    @Test
    void calculatesConceptCoverageWithSynonymsAndNormalization() {
        Gate5Metrics.Coverage coverage = Gate5Metrics.conceptCoverage(
                "应先计算 Δ，它小于 0，所以没有实数根。",
                List.of(List.of("判别式", "Δ"), List.of("<0", "小于0"),
                        List.of("无实数根", "没有实数根")));

        assertThat(coverage.hitGroups()).isEqualTo(3);
        assertThat(coverage.totalGroups()).isEqualTo(3);
        assertThat(coverage.coverage()).isEqualTo(1.0);
    }

    @Test
    void blindLabelsAreStableAndContainBothOrders() throws Exception {
        Set<Boolean> orders = Gate5Dataset.load(objectMapper).stream()
                .filter(Gate5Dataset.Case::ragAblation)
                .map(item -> Gate5Metrics.outputAIsRagOn(item.caseId()))
                .collect(Collectors.toSet());

        assertThat(orders).containsExactlyInAnyOrder(true, false);
    }
}
