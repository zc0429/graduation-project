package com.example.wrongbook.service.impl;

import com.example.wrongbook.common.BizException;
import com.example.wrongbook.common.LoginUser;
import com.example.wrongbook.common.UserContext;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.entity.VariantQuestion;
import com.example.wrongbook.mapper.KnowledgePointMapper;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.mapper.VariantQuestionMapper;
import com.example.wrongbook.service.LlmClient;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;
import org.junit.jupiter.params.provider.ValueSource;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InOrder;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.transaction.TransactionStatus;
import org.springframework.transaction.support.TransactionTemplate;

import java.util.List;
import java.util.concurrent.atomic.AtomicLong;
import java.util.function.Consumer;
import java.util.stream.Stream;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.inOrder;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class VariantServiceImplTests {

    private static final long USER_ID = 101L;
    private static final long QUESTION_ID = 202L;
    private static final String VALID_RESPONSE = """
            {"variants":[
              {"stem":"变式题一","answer":"答案一","difficulty":2},
              {"stem":"变式题二","answer":"答案二","difficulty":3},
              {"stem":"变式题三","answer":"答案三","difficulty":4}
            ]}
            """;

    @Mock
    private VariantQuestionMapper variantQuestionMapper;

    @Mock
    private QuestionMapper questionMapper;

    @Mock
    private KnowledgePointMapper knowledgePointMapper;

    @Mock
    private LlmClient llmClient;

    @Mock
    private TransactionTemplate transactionTemplate;

    private VariantServiceImpl variantService;

    @BeforeEach
    void setUp() {
        Question question = new Question();
        question.setId(QUESTION_ID);
        question.setUserId(USER_ID);
        question.setStem("原题");
        question.setAnswer("原答案");
        when(questionMapper.selectById(QUESTION_ID)).thenReturn(question);
        UserContext.set(new LoginUser(USER_ID, "student"));

        variantService = new VariantServiceImpl(variantQuestionMapper, questionMapper,
                knowledgePointMapper, llmClient, new ObjectMapper(), transactionTemplate,
                new LearningResourceAccess(questionMapper, mock(com.example.wrongbook.mapper.PracticeRecordMapper.class)));
    }

    @AfterEach
    void tearDown() {
        UserContext.clear();
    }

    @Test
    void variantPromptReceivesNormalizedQuestionText() {
        Question question = questionMapper.selectById(QUESTION_ID);
        question.setStem("<p>求 x<sup>2</sup></p><p>第二行</p>");
        when(llmClient.chat(anyString())).thenReturn(VALID_RESPONSE);
        variantService.generate(QUESTION_ID);
        org.mockito.ArgumentCaptor<String> prompt = org.mockito.ArgumentCaptor.forClass(String.class);
        verify(llmClient).chat(prompt.capture());
        assertThat(prompt.getValue()).contains("求 x^(2)\n第二行").doesNotContain("<p>", "<sup>");
    }

    @ParameterizedTest
    @ValueSource(strings = {"```JSON\n%s\n```", "``` json\n%s\n```"})
    void validatesAllVariantsBeforeOpeningShortInsertTransaction(String fencedTemplate) {
        when(llmClient.chat(anyString())).thenReturn(fencedTemplate.formatted(VALID_RESPONSE));
        when(questionMapper.selectByIdForUpdate(QUESTION_ID))
                .thenAnswer(invocation -> questionMapper.selectById(QUESTION_ID));
        doAnswer(invocation -> {
            Consumer<TransactionStatus> callback = invocation.getArgument(0);
            callback.accept(mock(TransactionStatus.class));
            return null;
        }).when(transactionTemplate).executeWithoutResult(any());
        AtomicLong ids = new AtomicLong(300L);
        when(variantQuestionMapper.insert(any(VariantQuestion.class))).thenAnswer(invocation -> {
            VariantQuestion variant = invocation.getArgument(0);
            variant.setId(ids.incrementAndGet());
            return 1;
        });

        List<VariantQuestion> result = variantService.generate(QUESTION_ID);

        assertThat(result).hasSize(3);
        assertThat(result).extracting(VariantQuestion::getStem)
                .containsExactly("变式题一", "变式题二", "变式题三");
        assertThat(result).extracting(VariantQuestion::getAnswer)
                .containsExactly("答案一", "答案二", "答案三");
        assertThat(result).extracting(VariantQuestion::getDifficulty)
                .containsExactly(2, 3, 4);
        InOrder order = inOrder(llmClient, transactionTemplate, variantQuestionMapper);
        order.verify(llmClient).chat(anyString());
        order.verify(transactionTemplate).executeWithoutResult(any());
        order.verify(variantQuestionMapper, times(3)).insert(any(VariantQuestion.class));
        verify(questionMapper).selectByIdForUpdate(QUESTION_ID);
    }

    @Test
    void rejectsStaleQuestionInputBeforeAnyInsert() {
        when(llmClient.chat(anyString())).thenReturn(VALID_RESPONSE);
        Question editedQuestion = new Question();
        editedQuestion.setId(QUESTION_ID);
        editedQuestion.setUserId(USER_ID);
        editedQuestion.setStem("模型调用期间已编辑的题干");
        editedQuestion.setAnswer("原答案");
        when(questionMapper.selectByIdForUpdate(QUESTION_ID)).thenReturn(editedQuestion);
        doAnswer(invocation -> {
            Consumer<TransactionStatus> callback = invocation.getArgument(0);
            callback.accept(mock(TransactionStatus.class));
            return null;
        }).when(transactionTemplate).executeWithoutResult(any());

        assertThatThrownBy(() -> variantService.generate(QUESTION_ID))
                .isInstanceOf(BizException.class)
                .hasMessage("变式题生成失败，请稍后重试");

        verify(questionMapper).selectByIdForUpdate(QUESTION_ID);
        verify(variantQuestionMapper, never()).insert(any(VariantQuestion.class));
    }

    @ParameterizedTest
    @MethodSource("invalidResponses")
    void rejectsInvalidResponseBeforeAnyInsert(String response) {
        when(llmClient.chat(anyString())).thenReturn(response);

        assertThatThrownBy(() -> variantService.generate(QUESTION_ID))
                .isInstanceOf(BizException.class)
                .hasMessage("变式题生成失败，请稍后重试");

        verify(transactionTemplate, never()).executeWithoutResult(any());
        verify(variantQuestionMapper, never()).insert(any(VariantQuestion.class));
    }

    private static Stream<String> invalidResponses() {
        return Stream.of(
                "[]",
                """
                        {"variants":[
                          {"stem":"题一","answer":"答一","difficulty":2},
                          {"stem":"题二","answer":"答二","difficulty":3}
                        ]}
                        """,
                VALID_RESPONSE.replace("变式题二", "   "),
                VALID_RESPONSE.replace("答案二", "   "),
                VALID_RESPONSE.replace("\"difficulty\":3", "\"difficulty\":6"),
                VALID_RESPONSE.replace("\"difficulty\":3", "\"difficulty\":3,\"extra\":true")
        );
    }
}
