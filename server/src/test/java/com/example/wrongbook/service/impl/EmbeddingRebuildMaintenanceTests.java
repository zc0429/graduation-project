package com.example.wrongbook.service.impl;

import com.example.wrongbook.entity.Question;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.service.EmbeddingService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.test.context.bean.override.mockito.MockitoBean;

import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@SpringBootTest(properties = "app.llm.provider=mock")
class EmbeddingRebuildMaintenanceTests {

    private static final String FIXTURE_SOURCE = "__embedding_rebuild_offline_test__";
    private static final String SENTINEL_EMBEDDING = "[9.0,8.0]";

    @Autowired
    private QuestionMapper questionMapper;

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @MockitoBean
    private EmbeddingService embeddingService;

    private final List<Long> fixtureIds = new ArrayList<>();
    private EmbeddingRebuildMaintenance maintenance;

    @BeforeEach
    void setUp() {
        jdbcTemplate.update("DELETE FROM question WHERE source = ?", FIXTURE_SOURCE);
        fixtureIds.clear();
        maintenance = new EmbeddingRebuildMaintenance(questionMapper, embeddingService, objectMapper);
    }

    @AfterEach
    void tearDown() {
        fixtureIds.forEach(id -> jdbcTemplate.update("DELETE FROM question WHERE id = ?", id));
    }

    @Test
    void writesAValid1024DimensionEmbedding() throws Exception {
        String stem = "正常 1024 维写入测试";
        long questionId = insertQuestion(stem);
        List<Double> expected = validVector();
        when(embeddingService.embed(stem)).thenReturn(expected);

        EmbeddingRebuildMaintenance.RebuildReport report =
                maintenance.rebuildSnapshots(List.of(questionMapper.selectById(questionId)));

        assertThat(report.total()).isEqualTo(1);
        assertThat(report.success()).isEqualTo(1);
        assertThat(report.failed()).isZero();
        assertThat(report.stale()).isZero();
        assertThat(report.skipped()).isZero();
        assertThat(readVector(questionId)).containsExactlyElementsOf(expected);
    }

    @Test
    void rejectsNullWrongDimensionAndNonFiniteEmbeddings() {
        List<List<Double>> invalidVectors = new ArrayList<>();
        invalidVectors.add(null);
        invalidVectors.add(validVector(1023));
        invalidVectors.add(vectorWithInvalidValue(null));
        invalidVectors.add(vectorWithInvalidValue(Double.NaN));
        invalidVectors.add(vectorWithInvalidValue(Double.POSITIVE_INFINITY));

        List<Question> snapshots = new ArrayList<>();
        for (int index = 0; index < invalidVectors.size(); index++) {
            String stem = "非法向量拒绝测试 " + index;
            long questionId = insertQuestion(stem);
            snapshots.add(questionMapper.selectById(questionId));
            when(embeddingService.embed(stem)).thenReturn(invalidVectors.get(index));
        }

        EmbeddingRebuildMaintenance.RebuildReport report = maintenance.rebuildSnapshots(snapshots);

        assertThat(report.total()).isEqualTo(invalidVectors.size());
        assertThat(report.failed()).isEqualTo(invalidVectors.size());
        assertThat(report.success()).isZero();
        assertThat(report.stale()).isZero();
        assertThat(report.skipped()).isZero();
        fixtureIds.forEach(id -> assertThat(readEmbedding(id)).isEqualTo(SENTINEL_EMBEDDING));
    }

    @Test
    void doesNotOverwriteAStemChangedOnlyByCase() {
        String originalStem = "Snapshot Case Guard";
        String editedStem = "snapshot Case Guard";
        long questionId = insertQuestion(originalStem);
        when(embeddingService.embed(originalStem)).thenAnswer(invocation -> {
            jdbcTemplate.update("UPDATE question SET stem = ? WHERE id = ?", editedStem, questionId);
            return validVector();
        });

        EmbeddingRebuildMaintenance.RebuildReport report =
                maintenance.rebuildSnapshots(List.of(questionMapper.selectById(questionId)));

        assertThat(report.total()).isEqualTo(1);
        assertThat(report.success()).isZero();
        assertThat(report.failed()).isZero();
        assertThat(report.stale()).isEqualTo(1);
        assertThat(readStem(questionId)).isEqualTo(editedStem);
        assertThat(readEmbedding(questionId)).isEqualTo(SENTINEL_EMBEDDING);
    }

    @Test
    void continuesAfterOneFailureAndKeepsSummaryCountsMutuallyExclusive() throws Exception {
        String firstStem = "批处理成功题一";
        String failedStem = "批处理失败题";
        String laterStem = "批处理成功题二";
        String staleStem = "Batch Stale Stem";
        long firstId = insertQuestion(firstStem);
        long failedId = insertQuestion(failedStem);
        long laterId = insertQuestion(laterStem);
        long staleId = insertQuestion(staleStem);
        long blankId = insertQuestion(" ");
        List<Double> validVector = validVector();
        when(embeddingService.embed(firstStem)).thenReturn(validVector);
        when(embeddingService.embed(failedStem)).thenThrow(new IllegalStateException("offline failure"));
        when(embeddingService.embed(laterStem)).thenReturn(validVector);
        when(embeddingService.embed(staleStem)).thenAnswer(invocation -> {
            jdbcTemplate.update("UPDATE question SET stem = ? WHERE id = ?", "batch Stale Stem", staleId);
            return validVector;
        });

        List<Question> snapshots = List.of(
                questionMapper.selectById(firstId),
                questionMapper.selectById(failedId),
                questionMapper.selectById(laterId),
                questionMapper.selectById(staleId),
                questionMapper.selectById(blankId));
        EmbeddingRebuildMaintenance.RebuildReport report = maintenance.rebuildSnapshots(snapshots);

        assertThat(report.total()).isEqualTo(5);
        assertThat(report.success()).isEqualTo(2);
        assertThat(report.failed()).isEqualTo(1);
        assertThat(report.stale()).isEqualTo(1);
        assertThat(report.skipped()).isEqualTo(1);
        assertThat(report.total())
                .isEqualTo(report.success() + report.failed() + report.stale() + report.skipped());
        assertThat(readVector(firstId)).hasSize(EmbeddingRebuildMaintenance.REQUIRED_DIMENSIONS);
        assertThat(readEmbedding(failedId)).isEqualTo(SENTINEL_EMBEDDING);
        assertThat(readVector(laterId)).hasSize(EmbeddingRebuildMaintenance.REQUIRED_DIMENSIONS);
        assertThat(readEmbedding(staleId)).isEqualTo(SENTINEL_EMBEDDING);
        assertThat(readEmbedding(blankId)).isEqualTo(SENTINEL_EMBEDDING);
        verify(embeddingService, never()).embed(" ");
    }

    @Test
    void auditsNullInvalidNonFiniteAndExpectedDimensionBuckets() throws Exception {
        List<Question> snapshots = List.of(
                snapshot(1L, null),
                snapshot(2L, "not-json"),
                snapshot(3L, objectMapper.writeValueAsString(validVector(256))),
                snapshot(4L, objectMapper.writeValueAsString(validVector(512))),
                snapshot(5L, objectMapper.writeValueAsString(validVector(1024))),
                snapshot(6L, objectMapper.writeValueAsString(validVector(2048))),
                snapshot(7L, objectMapper.writeValueAsString(validVector(8))),
                snapshot(8L, "[1e309,0.0]"));

        EmbeddingRebuildMaintenance.AuditReport report = maintenance.auditSnapshots(snapshots);

        assertThat(report.total()).isEqualTo(8);
        assertThat(report.nullCount()).isEqualTo(1);
        assertThat(report.invalidJsonCount()).isEqualTo(1);
        assertThat(report.nonFiniteVectorCount()).isEqualTo(1);
        assertThat(report.dimensions256()).isEqualTo(1);
        assertThat(report.dimensions512()).isEqualTo(1);
        assertThat(report.dimensions1024()).isEqualTo(1);
        assertThat(report.dimensions2048()).isEqualTo(1);
        assertThat(report.otherDimensions()).isEqualTo(2);
        assertThat(report.isUnified1024()).isFalse();
    }

    private long insertQuestion(String stem) {
        KeyHolder keyHolder = new GeneratedKeyHolder();
        jdbcTemplate.update(connection -> {
            var statement = connection.prepareStatement("""
                    INSERT INTO question
                        (user_id, subject_id, stem, answer, source, mastery, embedding, status)
                    VALUES (99001, 99001, ?, '离线测试答案', ?, 0, ?, 1)
                    """, Statement.RETURN_GENERATED_KEYS);
            statement.setString(1, stem);
            statement.setString(2, FIXTURE_SOURCE);
            statement.setString(3, SENTINEL_EMBEDDING);
            return statement;
        }, keyHolder);
        long questionId = Objects.requireNonNull(keyHolder.getKey()).longValue();
        fixtureIds.add(questionId);
        return questionId;
    }

    private Question snapshot(long id, String embedding) {
        Question question = new Question();
        question.setId(id);
        question.setEmbedding(embedding);
        return question;
    }

    private List<Double> validVector() {
        return validVector(EmbeddingRebuildMaintenance.REQUIRED_DIMENSIONS);
    }

    private List<Double> validVector(int dimensions) {
        List<Double> vector = new ArrayList<>(dimensions);
        for (int index = 0; index < dimensions; index++) {
            vector.add(((index % 17) + 1) / 100.0);
        }
        return vector;
    }

    private List<Double> vectorWithInvalidValue(Double invalidValue) {
        List<Double> vector = validVector();
        vector.set(37, invalidValue);
        return vector;
    }

    private String readEmbedding(long questionId) {
        return jdbcTemplate.queryForObject(
                "SELECT embedding FROM question WHERE id = ?", String.class, questionId);
    }

    private String readStem(long questionId) {
        return jdbcTemplate.queryForObject(
                "SELECT stem FROM question WHERE id = ?", String.class, questionId);
    }

    private List<Double> readVector(long questionId) throws Exception {
        return objectMapper.readValue(readEmbedding(questionId), new TypeReference<>() {
        });
    }
}
