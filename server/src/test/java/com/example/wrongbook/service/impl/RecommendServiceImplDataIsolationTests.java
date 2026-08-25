package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.MybatisConfiguration;
import com.baomidou.mybatisplus.core.metadata.TableInfoHelper;
import com.example.wrongbook.common.LoginUser;
import com.example.wrongbook.common.UserContext;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.service.RagService;
import org.apache.ibatis.builder.MapperBuilderAssistant;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class RecommendServiceImplDataIsolationTests {

    private static final long OWNER_A = 1001L;
    private static final long OWNER_B = 2002L;
    private static final long ADMIN_ID = 9009L;
    private static final long SOURCE_ID = 101L;
    private static final long KNOWLEDGE_POINT_ID = 501L;

    @Mock
    private QuestionMapper questionMapper;

    @Mock
    private RagService ragService;

    private RecommendServiceImpl recommendService;

    @BeforeAll
    static void initializeQuestionMetadata() {
        TableInfoHelper.initTableInfo(new MapperBuilderAssistant(new MybatisConfiguration(), ""), Question.class);
    }

    @BeforeEach
    void setUp() {
        recommendService = new RecommendServiceImpl(questionMapper, ragService);
        UserContext.set(new LoginUser(OWNER_A, "student"));
    }

    @AfterEach
    void tearDown() {
        UserContext.clear();
    }

    @Test
    void sameKnowledgePointCandidatesStayWithinTheSourceOwner() {
        Question source = sourceQuestion(KNOWLEDGE_POINT_ID);
        Question ownCandidate = candidate(102L, OWNER_A, 4);
        Question otherUsersCandidate = candidate(201L, OWNER_B, 3);
        when(questionMapper.selectById(SOURCE_ID)).thenReturn(source);
        when(questionMapper.selectList(any())).thenReturn(List.of(otherUsersCandidate, ownCandidate));
        when(ragService.retrieveSimilar(source, 5)).thenReturn(List.of());

        List<Question> result = recommendService.similar(SOURCE_ID);

        assertThat(result).extracting(Question::getId).containsExactly(ownCandidate.getId());
        assertOwnerBoundKnowledgeQuery(captureQuery(), OWNER_A);
    }

    @Test
    void embeddingFallbackCannotReintroduceAnotherUsersQuestion() {
        Question source = sourceQuestion(null);
        Question ownCandidate = candidate(102L, OWNER_A, 4);
        Question otherUsersCandidate = candidate(201L, OWNER_B, 3);
        when(questionMapper.selectById(SOURCE_ID)).thenReturn(source);
        when(ragService.retrieveSimilar(source, 5)).thenReturn(List.of(otherUsersCandidate, ownCandidate));

        List<Question> result = recommendService.similar(SOURCE_ID);

        assertThat(result).extracting(Question::getId).containsExactly(ownCandidate.getId());
        verify(questionMapper, never()).selectList(any());
    }

    @Test
    void adminUsesTheSourceQuestionOwnerAsTheCandidateBoundary() {
        UserContext.set(new LoginUser(ADMIN_ID, "admin"));
        Question source = sourceQuestion(KNOWLEDGE_POINT_ID);
        Question ownCandidate = candidate(102L, OWNER_A, 4);
        when(questionMapper.selectById(SOURCE_ID)).thenReturn(source);
        when(questionMapper.selectList(any())).thenReturn(List.of(ownCandidate));
        when(ragService.retrieveSimilar(source, 5)).thenReturn(List.of());

        List<Question> result = recommendService.similar(SOURCE_ID);

        assertThat(result).extracting(Question::getId).containsExactly(ownCandidate.getId());
        LambdaQueryWrapper<Question> query = captureQuery();
        assertOwnerBoundKnowledgeQuery(query, OWNER_A);
        assertThat(query.getParamNameValuePairs()).doesNotContainValue(ADMIN_ID);
    }

    @Test
    void returnsEmptyWhenNoCandidateBelongsToTheSourceOwner() {
        Question source = sourceQuestion(KNOWLEDGE_POINT_ID);
        Question otherUsersCandidate = candidate(201L, OWNER_B, 3);
        when(questionMapper.selectById(SOURCE_ID)).thenReturn(source);
        when(questionMapper.selectList(any())).thenReturn(List.of(otherUsersCandidate));
        when(ragService.retrieveSimilar(source, 5)).thenReturn(List.of(otherUsersCandidate));

        List<Question> result = recommendService.similar(SOURCE_ID);

        assertThat(result).isEmpty();
        assertOwnerBoundKnowledgeQuery(captureQuery(), OWNER_A);
    }

    @SuppressWarnings({"rawtypes", "unchecked"})
    private LambdaQueryWrapper<Question> captureQuery() {
        ArgumentCaptor<Wrapper> captor = ArgumentCaptor.forClass(Wrapper.class);
        verify(questionMapper).selectList(captor.capture());
        return (LambdaQueryWrapper<Question>) captor.getValue();
    }

    private void assertOwnerBoundKnowledgeQuery(LambdaQueryWrapper<Question> query, long ownerId) {
        assertThat(query.getSqlSegment())
                .contains("user_id")
                .contains("knowledge_point_id");
        assertThat(query.getParamNameValuePairs())
                .containsValue(ownerId)
                .containsValue(KNOWLEDGE_POINT_ID)
                .containsValue(SOURCE_ID);
    }

    private Question sourceQuestion(Long knowledgePointId) {
        Question question = candidate(SOURCE_ID, OWNER_A, 3);
        question.setKnowledgePointId(knowledgePointId);
        question.setSubjectId(77L);
        question.setEmbedding("[1.0,0.0]");
        return question;
    }

    private Question candidate(long id, long userId, int difficulty) {
        Question question = new Question();
        question.setId(id);
        question.setUserId(userId);
        question.setKnowledgePointId(KNOWLEDGE_POINT_ID);
        question.setDifficulty(difficulty);
        return question;
    }
}
