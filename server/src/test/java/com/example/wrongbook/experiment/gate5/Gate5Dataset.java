package com.example.wrongbook.experiment.gate5;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

final class Gate5Dataset {

    private Gate5Dataset() {
    }

    static Path datasetPath() {
        Path fromServer = Path.of("..", "docs", "experiments", "gate5", "dataset.json");
        if (Files.isRegularFile(fromServer)) {
            return fromServer.normalize();
        }
        Path fromRoot = Path.of("docs", "experiments", "gate5", "dataset.json");
        if (Files.isRegularFile(fromRoot)) {
            return fromRoot.normalize();
        }
        throw new IllegalStateException("找不到 Gate5 固定数据集，请从仓库根目录或 server 目录运行测试");
    }

    static Path gate5Directory() {
        return datasetPath().toAbsolutePath().normalize().getParent();
    }

    static List<Case> load(ObjectMapper objectMapper) throws IOException {
        return objectMapper.readValue(datasetPath().toFile(), new TypeReference<>() {
        });
    }

    record Case(
            String caseId,
            long subjectId,
            String subjectName,
            long expectedKnowledgePointId,
            String expectedKnowledgePointName,
            String stem,
            String wrongAnswer,
            String correctAnswer,
            List<List<String>> errorConceptGroups,
            String relevanceGroup,
            boolean ragAblation) {
    }
}
