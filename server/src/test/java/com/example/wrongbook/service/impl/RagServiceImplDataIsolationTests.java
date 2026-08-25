package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.MybatisConfiguration;
import com.baomidou.mybatisplus.core.metadata.TableInfoHelper;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.mapper.QuestionMapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.ibatis.builder.MapperBuilderAssistant;
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
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class RagServiceImplDataIsolationTests {

    private static final long OWNER_A = 1001L;
    private static final long OWNER_B = 2002L;
    private static final long SUBJECT_ID = 77L;
    private static final long SOURCE_ID = 101L;

    @Mock
    private QuestionMapper questionMapper;

    private RagServiceImpl ragService;

    @BeforeAll
    static void initializeQuestionMetadata() {
        TableInfoHelper.initTableInfo(new MapperBuilderAssistant(new MybatisConfiguration(), ""), Question.class);
    }

    @BeforeEach
    void setUp() {
        ragService = new RagServiceImpl(questionMapper, new ObjectMapper());
    }

    @Test
    void retrievesOnlyTheSourceOwnersCandidates() {
        Question source = question(SOURCE_ID, OWNER_A, "[1.0,0.0]");
        Question ownCandidate = question(102L, OWNER_A, "[0.9,0.1]");
        Question otherUsersCloserCandidate = question(201L, OWNER_B, "[1.0,0.0]");
        when(questionMapper.selectList(any())).thenReturn(List.of(ownCandidate, otherUsersCloserCandidate));

        List<Question> result = ragService.retrieveSimilar(source, 5);

        assertThat(result).extracting(Question::getId).containsExactly(ownCandidate.getId());
        assertOwnerBoundRagQuery(captureQuery(), OWNER_A);
    }

    @Test
    void returnsEmptyWhenOnlyAnotherUsersCandidateExists() {
        Question source = question(SOURCE_ID, OWNER_A, "[1.0,0.0]");
        Question otherUsersCandidate = question(201L, OWNER_B, "[1.0,0.0]");
        when(questionMapper.selectList(any())).thenReturn(List.of(otherUsersCandidate));

        List<Question> result = ragService.retrieveSimilar(source, 5);

        assertThat(result).isEmpty();
        assertOwnerBoundRagQuery(captureQuery(), OWNER_A);
    }

    @SuppressWarnings({"rawtypes", "unchecked"})
    private LambdaQueryWrapper<Question> captureQuery() {
        ArgumentCaptor<Wrapper> captor = ArgumentCaptor.forClass(Wrapper.class);
        verify(questionMapper).selectList(captor.capture());
        return (LambdaQueryWrapper<Question>) captor.getValue();
    }

    private void assertOwnerBoundRagQuery(LambdaQueryWrapper<Question> query, long ownerId) {
        assertThat(query.getSqlSegment())
                .contains("user_id")
                .contains("subject_id")
                .contains("embedding");
        assertThat(query.getParamNameValuePairs())
                .containsValue(ownerId)
                .containsValue(SUBJECT_ID)
                .containsValue(SOURCE_ID);
    }

    private Question question(long id, long userId, String embedding) {
        Question question = new Question();
        question.setId(id);
        question.setUserId(userId);
        question.setSubjectId(SUBJECT_ID);
        question.setEmbedding(embedding);
        return question;
    }
}
