package com.example.wrongbook.experiment.gate5;

import java.text.Normalizer;
import java.util.List;
import java.util.Locale;

final class Gate5Metrics {

    private Gate5Metrics() {
    }

    static Retrieval retrieval(List<String> retrievedGroups, String expectedGroup, int relevantPoolSize) {
        int relevant = 0;
        int firstRank = 0;
        for (int index = 0; index < retrievedGroups.size(); index++) {
            if (expectedGroup.equals(retrievedGroups.get(index))) {
                relevant++;
                if (firstRank == 0) {
                    firstRank = index + 1;
                }
            }
        }
        return new Retrieval(
                relevant > 0 ? 1.0 : 0.0,
                relevantPoolSize == 0 ? 0.0 : (double) relevant / relevantPoolSize,
                firstRank,
                firstRank == 0 ? 0.0 : 1.0 / firstRank,
                relevant);
    }

    static Coverage conceptCoverage(String modelText, List<List<String>> conceptGroups) {
        String normalizedText = normalize(modelText);
        int hits = 0;
        for (List<String> group : conceptGroups) {
            boolean matched = group.stream()
                    .map(Gate5Metrics::normalize)
                    .anyMatch(normalizedText::contains);
            if (matched) {
                hits++;
            }
        }
        return new Coverage(hits, conceptGroups.size(),
                conceptGroups.isEmpty() ? 0.0 : (double) hits / conceptGroups.size());
    }

    static boolean outputAIsRagOn(String caseId) {
        return ((caseId.hashCode() >>> 1) & 1) == 0;
    }

    private static String normalize(String value) {
        return Normalizer.normalize(value == null ? "" : value, Normalizer.Form.NFKC)
                .toLowerCase(Locale.ROOT)
                .replaceAll("\\s+", "");
    }

    record Retrieval(double hit, double recall, int firstRelevantRank, double mrr, int relevantCount) {
    }

    record Coverage(int hitGroups, int totalGroups, double coverage) {
    }
}
