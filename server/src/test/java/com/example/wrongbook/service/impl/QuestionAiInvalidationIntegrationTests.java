package com.example.wrongbook.service.impl;

import com.example.wrongbook.common.LoginUser;
import com.example.wrongbook.common.UserContext;
import com.example.wrongbook.dto.QuestionRequest;
import com.example.wrongbook.entity.KnowledgePoint;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.mapper.KnowledgePointMapper;
import com.example.wrongbook.mapper.VariantQuestionMapper;
import com.example.wrongbook.service.AiAnalysisService;
import com.example.wrongbook.service.EmbeddingService;
import com.example.wrongbook.service.LlmClient;
import com.example.wrongbook.service.MessageService;
import com.example.wrongbook.service.QuestionService;
import com.example.wrongbook.service.RagService;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.context.bean.override.mockito.MockitoSpyBean;

import java.sql.Statement;
import java.util.List;
import java.util.Objects;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executor;
import java.util.concurrent.TimeUnit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@SpringBootTest
class QuestionAiInvalidationIntegrationTests {

    private static final long USER_ID = 91001L;
    private static final long SUBJECT_A = 92001L;
    private static final long SUBJECT_B = 92002L;
    private static final long KNOWLEDGE_POINT_A = 93001L;
    private static final long KNOWLEDGE_POINT_B = 93002L;
    private static final String STEM_A = "P0 编辑一致性测试题干 A";
    private static final String STEM_B = "P0 编辑一致性测试题干 B";
    private static final String ANSWER_A = "测试答案 A";
    private static final String ANSWER_B = "测试答案 B";
    private static final String SOURCE_A = "测试来源 A";
    private static final String SOURCE_B = "测试来源 B";
    private static final String EMBEDDING_A = "[0.25,0.75]";

    @Autowired
    private QuestionService questionService;

    @Autowired
    private AiAnalysisService aiAnalysisService;

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @MockitoSpyBean
    private VariantQuestionMapper variantQuestionMapper;

    @MockitoBean
    private EmbeddingService embeddingService;

    @MockitoBean
    private RagService ragService;

    @MockitoBean
    private LlmClient llmClient;

    @MockitoBean
    private KnowledgePointMapper knowledgePointMapper;

    @MockitoBean
    private MessageService messageService;

    @MockitoBean(name = "aiTaskExecutor")
    private Executor aiTaskExecutor;

    private long questionId;

    @BeforeEach
    void setUp() {
        questionId = insertFixture();
        UserContext.set(new LoginUser(USER_ID, "student"));
    }

    @AfterEach
    void tearDown() {
        UserContext.clear();
        jdbcTemplate.update("DELETE FROM practice_record WHERE question_id = ?", questionId);
        jdbcTemplate.update("DELETE FROM review_plan WHERE question_id = ?", questionId);
        jdbcTemplate.update("DELETE FROM variant_question WHERE question_id = ?", questionId);
        jdbcTemplate.update("DELETE FROM ai_analysis WHERE question_id = ?", questionId);
        jdbcTemplate.update("DELETE FROM question WHERE id = ?", questionId);
    }

    @Test
    void stemChangeInvalidatesAllAiDerivedData() {
        questionService.update(questionId, request(SUBJECT_A, STEM_B, ANSWER_A, SOURCE_A));

        QuestionState state = loadQuestion();
        assertThat(state.stem()).isEqualTo(STEM_B);
        assertFullyInvalidated(state);
    }

    @Test
    void subjectChangeInvalidatesAllAiDerivedData() {
        questionService.update(questionId, request(SUBJECT_B, STEM_A, ANSWER_A, SOURCE_A));

        QuestionState state = loadQuestion();
        assertThat(state.subjectId()).isEqualTo(SUBJECT_B);
        assertFullyInvalidated(state);
    }

    @Test
    void answerChangeInvalidatesAllAiDerivedData() {
        questionService.update(questionId, request(SUBJECT_A, STEM_A, ANSWER_B, SOURCE_A));

        QuestionState state = loadQuestion();
        assertThat(state.answer()).isEqualTo(ANSWER_B);
        assertFullyInvalidated(state);
    }

    @Test
    void sourceOnlyChangeKeepsAiDerivedData() {
        questionService.update(questionId, request(SUBJECT_A, STEM_A, ANSWER_A, SOURCE_B));

        QuestionState state = loadQuestion();
        assertThat(state.source()).isEqualTo(SOURCE_B);
        assertThat(state.embedding()).isEqualTo(EMBEDDING_A);
        assertThat(state.knowledgePointId()).isEqualTo(KNOWLEDGE_POINT_A);
        assertThat(state.difficulty()).isEqualTo(4);
        assertThat(analysisCount()).isEqualTo(1);
        assertThat(variantCount()).isEqualTo(1);
    }

    @Test
    void derivedDeleteFailureRollsBackQuestionAndAllDerivedChanges() {
        doThrow(new IllegalStateException("forced variant delete failure"))
                .when(variantQuestionMapper).delete(any());

        assertThatThrownBy(() -> questionService.update(
                questionId, request(SUBJECT_A, STEM_B, ANSWER_A, SOURCE_A)))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("forced variant delete failure");

        QuestionState state = loadQuestion();
        assertThat(state.subjectId()).isEqualTo(SUBJECT_A);
        assertThat(state.stem()).isEqualTo(STEM_A);
        assertThat(state.answer()).isEqualTo(ANSWER_A);
        assertThat(state.embedding()).isEqualTo(EMBEDDING_A);
        assertThat(state.knowledgePointId()).isEqualTo(KNOWLEDGE_POINT_A);
        assertThat(state.difficulty()).isEqualTo(4);
        assertThat(analysisCount()).isEqualTo(1);
        assertThat(variantCount()).isEqualTo(1);
    }

    @Test
    void staleAsyncTaskCannotWriteOldResultsAfterQuestionEdit() throws Exception {
        CountDownLatch embeddingStarted = new CountDownLatch(1);
        CountDownLatch releaseEmbedding = new CountDownLatch(1);
        when(embeddingService.embed(STEM_A)).thenAnswer(invocation -> {
            embeddingStarted.countDown();
            if (!releaseEmbedding.await(5, TimeUnit.SECONDS)) {
                throw new IllegalStateException("timed out waiting to continue stale task");
            }
            return List.of(1.0, 0.0);
        });
        stubSuccessfulAiResponse();

        aiAnalysisService.trigger(questionId);
        Runnable task = captureSubmittedTask();
        CompletableFuture<Void> runningTask = CompletableFuture.runAsync(task);

        assertThat(embeddingStarted.await(5, TimeUnit.SECONDS)).isTrue();
        try {
            questionService.update(questionId, request(SUBJECT_A, STEM_B, ANSWER_A, SOURCE_A));
        } finally {
            releaseEmbedding.countDown();
        }
        runningTask.get(10, TimeUnit.SECONDS);

        QuestionState state = loadQuestion();
        assertThat(state.stem()).isEqualTo(STEM_B);
        assertFullyInvalidated(state);
        verify(messageService, never()).send(any(), anyString(), anyString(), anyString());
    }

    @Test
    void unchangedQuestionStillCompletesAiAnalysisNormally() {
        when(embeddingService.embed(STEM_A)).thenReturn(List.of(1.0, 0.0));
        stubSuccessfulAiResponse();

        aiAnalysisService.trigger(questionId);
        captureSubmittedTask().run();

        QuestionState state = loadQuestion();
        AnalysisState analysis = loadAnalysis();
        assertThat(state.embedding()).isEqualTo("[1.0,0.0]");
        assertThat(state.knowledgePointId()).isEqualTo(KNOWLEDGE_POINT_B);
        assertThat(state.difficulty()).isEqualTo(5);
        assertThat(analysis.status()).isEqualTo(1);
        assertThat(analysis.knowledgePointId()).isEqualTo(KNOWLEDGE_POINT_B);
        assertThat(analysis.errorCause()).isEqualTo("测试错因");
        assertThat(analysis.analysis()).isEqualTo("测试解析");
        verify(messageService).send(eq(USER_ID), eq("system"), eq("错题解析完成"), anyString());
    }

    @ParameterizedTest
    @ValueSource(strings = {
            "{\"text\":\"wrong schema\"}",
            "{\"knowledgePointId\":93001,\"errorCause\":\"测试错因\",\"analysis\":\"测试解析\",\"difficulty\":3,\"extra\":\"not allowed\"}"
    })
    void invalidStructuredResponseCannotBePersistedAsSuccess(String response) {
        when(embeddingService.embed(STEM_A)).thenReturn(List.of(1.0, 0.0));
        when(ragService.retrieveSimilar(any(Question.class), eq(3))).thenReturn(List.of());
        stubKnowledgePointCandidates();
        when(llmClient.chat(anyString())).thenReturn(response);
        when(llmClient.model()).thenReturn("test-model");

        aiAnalysisService.trigger(questionId);
        captureSubmittedTask().run();

        QuestionState state = loadQuestion();
        AnalysisState analysis = loadAnalysis();
        assertThat(state.embedding()).isEqualTo(EMBEDDING_A);
        assertThat(state.knowledgePointId()).isEqualTo(KNOWLEDGE_POINT_A);
        assertThat(state.difficulty()).isEqualTo(4);
        assertThat(analysis.status()).isEqualTo(2);
        verify(messageService, never()).send(any(), anyString(), anyString(), anyString());
    }

    private void stubSuccessfulAiResponse() {
        when(ragService.retrieveSimilar(any(Question.class), eq(3))).thenReturn(List.of());
        stubKnowledgePointCandidates();
        when(llmClient.chat(anyString())).thenReturn("""
                {"knowledgePointId":93002,"errorCause":"测试错因","analysis":"测试解析","difficulty":5}
                """);
        when(llmClient.model()).thenReturn("test-model");
    }

    private void stubKnowledgePointCandidates() {
        when(knowledgePointMapper.selectList(any())).thenReturn(List.of(
                knowledgePoint(KNOWLEDGE_POINT_A, "测试知识点 A"),
                knowledgePoint(KNOWLEDGE_POINT_B, "测试知识点 B")));
    }

    private KnowledgePoint knowledgePoint(long id, String name) {
        KnowledgePoint knowledgePoint = new KnowledgePoint();
        knowledgePoint.setId(id);
        knowledgePoint.setSubjectId(SUBJECT_A);
        knowledgePoint.setParentId(1L);
        knowledgePoint.setName(name);
        return knowledgePoint;
    }

    private Runnable captureSubmittedTask() {
        var captor = org.mockito.ArgumentCaptor.forClass(Runnable.class);
        verify(aiTaskExecutor).execute(captor.capture());
        return captor.getValue();
    }

    private void assertFullyInvalidated(QuestionState state) {
        assertThat(state.embedding()).isNull();
        assertThat(state.knowledgePointId()).isNull();
        assertThat(state.difficulty()).isNull();
        assertThat(state.mastery()).isEqualTo(64);
        assertThat(analysisCount()).isZero();
        assertThat(variantCount()).isZero();
        assertThat(reviewPlanCount()).isEqualTo(1);
        assertThat(practiceCount()).isEqualTo(1);
    }

    private long insertFixture() {
        KeyHolder keyHolder = new GeneratedKeyHolder();
        jdbcTemplate.update(connection -> {
            var statement = connection.prepareStatement("""
                    INSERT INTO question
                        (user_id, subject_id, knowledge_point_id, stem, answer, source,
                         difficulty, mastery, embedding, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """, Statement.RETURN_GENERATED_KEYS);
            statement.setLong(1, USER_ID);
            statement.setLong(2, SUBJECT_A);
            statement.setLong(3, KNOWLEDGE_POINT_A);
            statement.setString(4, STEM_A);
            statement.setString(5, ANSWER_A);
            statement.setString(6, SOURCE_A);
            statement.setInt(7, 4);
            statement.setInt(8, 64);
            statement.setString(9, EMBEDDING_A);
            return statement;
        }, keyHolder);
        long id = Objects.requireNonNull(keyHolder.getKey()).longValue();
        jdbcTemplate.update("""
                INSERT INTO ai_analysis
                    (question_id, knowledge_point_id, error_cause, `analysis`, reference_ids, llm_model, status)
                VALUES (?, ?, '旧错因', '旧解析', '[]', 'old-model', 1)
                """, id, KNOWLEDGE_POINT_A);
        jdbcTemplate.update("""
                INSERT INTO variant_question (question_id, stem, answer, difficulty)
                VALUES (?, '旧变式题', '旧答案', 4)
                """, id);
        jdbcTemplate.update("""
                INSERT INTO review_plan (user_id, question_id, review_stage, plan_date, status)
                VALUES (?, ?, 1, CURRENT_DATE, 0)
                """, USER_ID, id);
        jdbcTemplate.update("""
                INSERT INTO practice_record (user_id, question_id, user_answer, is_correct, duration)
                VALUES (?, ?, '历史作答', 1, 30)
                """, USER_ID, id);
        return id;
    }

    private QuestionRequest request(long subjectId, String stem, String answer, String source) {
        QuestionRequest request = new QuestionRequest();
        request.setSubjectId(subjectId);
        request.setStem(stem);
        request.setAnswer(answer);
        request.setSource(source);
        return request;
    }

    private QuestionState loadQuestion() {
        return jdbcTemplate.queryForObject("""
                        SELECT subject_id, stem, answer, source, embedding,
                               knowledge_point_id, difficulty, mastery
                        FROM question WHERE id = ?
                        """,
                (resultSet, rowNum) -> new QuestionState(
                        resultSet.getLong("subject_id"),
                        resultSet.getString("stem"),
                        resultSet.getString("answer"),
                        resultSet.getString("source"),
                        resultSet.getString("embedding"),
                        resultSet.getObject("knowledge_point_id", Long.class),
                        resultSet.getObject("difficulty", Integer.class),
                        resultSet.getInt("mastery")),
                questionId);
    }

    private AnalysisState loadAnalysis() {
        return jdbcTemplate.queryForObject("""
                        SELECT knowledge_point_id, error_cause, `analysis`, status
                        FROM ai_analysis WHERE question_id = ?
                        """,
                (resultSet, rowNum) -> new AnalysisState(
                        resultSet.getObject("knowledge_point_id", Long.class),
                        resultSet.getString("error_cause"),
                        resultSet.getString("analysis"),
                        resultSet.getInt("status")),
                questionId);
    }

    private int analysisCount() {
        return count("ai_analysis");
    }

    private int variantCount() {
        return count("variant_question");
    }

    private int reviewPlanCount() {
        return count("review_plan");
    }

    private int practiceCount() {
        return count("practice_record");
    }

    private int count(String table) {
        return Objects.requireNonNull(jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM " + table + " WHERE question_id = ?", Integer.class, questionId));
    }

    private record QuestionState(
            long subjectId,
            String stem,
            String answer,
            String source,
            String embedding,
            Long knowledgePointId,
            Integer difficulty,
            int mastery) {
    }

    private record AnalysisState(Long knowledgePointId, String errorCause, String analysis, int status) {
    }
}
