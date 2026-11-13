package com.example.wrongbook.service.impl;

import com.example.wrongbook.common.BizException;
import com.example.wrongbook.common.LoginUser;
import com.example.wrongbook.common.UserContext;
import com.example.wrongbook.dto.PracticeRequest;
import com.example.wrongbook.dto.QuestionRequest;
import com.example.wrongbook.service.LearningService;
import com.example.wrongbook.service.LlmClient;
import com.example.wrongbook.service.PracticeService;
import com.example.wrongbook.service.QuestionService;
import com.example.wrongbook.service.VariantService;
import com.example.wrongbook.vo.PracticeResourceVO;
import org.junit.jupiter.api.*;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

@SpringBootTest
class LearningResourceIntegrationTests {
    private static final long USER = 881101L, OTHER = 881102L, QUESTION = 881201L;
    @Autowired LearningService learning;
    @Autowired VariantService variants;
    @Autowired PracticeService practice;
    @Autowired QuestionService questions;
    @Autowired JdbcTemplate jdbc;
    @MockitoBean LlmClient model;
    private final AtomicInteger batches = new AtomicInteger();

    @BeforeEach void setup() {
        cleanup();
        jdbc.update("INSERT INTO question(id,user_id,subject_id,stem,answer) VALUES (?,?,1,?,?)", QUESTION, USER, "求函数的定义域", "满足定义条件的取值集合");
        UserContext.set(new LoginUser(USER, "student"));
        when(model.chat(anyString())).thenAnswer(invocation -> {
            String prompt = invocation.getArgument(0);
            if (prompt.startsWith(MockLlmClient.TASK_KNOWLEDGE)) return "{\"content\":\"定义域是使函数表达式有意义的自变量取值集合，需同时满足各项限制。\"}";
            int n = batches.incrementAndGet();
            return batch(n);
        });
    }
    private String batch(int n) {
        return "{\"variants\":[{\"stem\":\"第"+n+"组题一\",\"answer\":\"答一\",\"difficulty\":2},"
                +"{\"stem\":\"第"+n+"组题二\",\"answer\":\"答二\",\"difficulty\":3},"
                +"{\"stem\":\"第"+n+"组题三\",\"answer\":\"答三\",\"difficulty\":4}]}";
    }
    @AfterEach void cleanup() {
        UserContext.clear();
        jdbc.update("DELETE FROM practice_record WHERE user_id IN (?,?)", USER, OTHER);
        jdbc.update("DELETE FROM learning_content WHERE question_id=?", QUESTION);
        jdbc.update("DELETE FROM review_plan WHERE question_id=?", QUESTION);
        jdbc.update("DELETE FROM variant_question WHERE question_id=?", QUESTION);
        jdbc.update("DELETE FROM ai_analysis WHERE question_id=?", QUESTION);
        jdbc.update("DELETE FROM question WHERE id=?", QUESTION);
    }
    private long count(String table) { return jdbc.queryForObject("SELECT COUNT(*) FROM "+table+" WHERE question_id=?", Long.class, QUESTION); }
    private void answer(PracticeResourceVO target, int correct) {
        PracticeRequest request = new PracticeRequest();
        request.setQuestionId(target.questionId());request.setVariantId(target.variantId());
        request.setIsCorrect(correct);request.setUserAnswer("测试作答");
        practice.submit(request);
    }
    private QuestionRequest edit(String stem, String source) {
        QuestionRequest r=new QuestionRequest();r.setSubjectId(1L);r.setStem(stem);r.setAnswer("满足定义条件的取值集合");r.setSource(source);return r;
    }

    @Test void knowledgePersistsAndReusesWithoutModelReadiness() {
        var first=learning.knowledge(QUESTION);
        assertThat(first.reused()).isFalse();assertThat(first.id()).isNotNull();assertThat(count("learning_content")).isEqualTo(1);
        doThrow(new BizException("缺少模型密钥")).when(model).verifyReady();
        var second=learning.knowledge(QUESTION);
        assertThat(second.reused()).isTrue();assertThat(second.id()).isEqualTo(first.id());assertThat(second.content()).isEqualTo(first.content());
        verify(model,times(1)).chat(anyString());verify(model,times(1)).verifyReady();
    }
    @Test void originalAndStoredUnpracticedResourcesPrecedeGenerationThenCycle() {
        var original=learning.nextPractice(QUESTION);
        assertThat(original.questionId()).isEqualTo(QUESTION);assertThat(original.source()).isEqualTo("original");verify(model,never()).chat(anyString());
        answer(original,0); // A wrong answer still counts as an actual practice attempt.
        var first=learning.nextPractice(QUESTION);assertThat(first.source()).isEqualTo("generated");answer(first,1);
        var second=learning.nextPractice(QUESTION);assertThat(second.source()).isEqualTo("existing");assertThat(second.variantId()).isNotEqualTo(first.variantId());answer(second,0);
        var third=learning.nextPractice(QUESTION);assertThat(third.source()).isEqualTo("existing");answer(third,1);
        verify(model,times(1)).chat(anyString());
        var fourth=learning.nextPractice(QUESTION);assertThat(fourth.source()).isEqualTo("generated");assertThat(fourth.variantId()).isNotIn(first.variantId(),second.variantId(),third.variantId());
        assertThat(count("variant_question")).isEqualTo(6);verify(model,times(2)).chat(anyString());
        assertThat(learning.progress(QUESTION).originalPracticed()).isTrue();assertThat(learning.progress(QUESTION).practicedVariantIds()).hasSize(3);
    }
    @Test void repeatedDeliveryDoesNotMarkAnUnansweredQuestionPracticed() {
        var a=learning.nextPractice(QUESTION);var b=learning.nextPractice(QUESTION);
        assertThat(a).isEqualTo(b);assertThat(learning.progress(QUESTION).originalPracticed()).isFalse();verify(model,never()).chat(anyString());
    }
    @Test void explicitRepeatKeepsHistoryAndDoesNotCallModel() {
        var original=learning.nextPractice(QUESTION);answer(original,0);answer(original,1);
        assertThat(count("practice_record")).isEqualTo(2);verify(model,never()).chat(anyString());
    }
    @Test void legacyVariantEndpointReusesUntilActualRecordsExhaustThePool() {
        var first=variants.generate(QUESTION);var second=variants.generate(QUESTION);
        assertThat(second).extracting(v->v.getId()).containsExactlyElementsOf(first.stream().map(v->v.getId()).toList());
        assertThat(count("variant_question")).isEqualTo(3);verify(model,times(1)).chat(anyString());
    }
    @Test void anotherStudentsPracticeCannotConsumeMyResource() {
        var pool=variants.generate(QUESTION);
        jdbc.update("INSERT INTO practice_record(user_id,variant_id,is_correct) VALUES (?,?,1)", OTHER,pool.getFirst().getId());
        assertThat(variants.list(QUESTION).getFirst().getPracticed()).isFalse();
        assertThat(learning.progress(QUESTION).practicedVariantIds()).isEmpty();
    }
    @ParameterizedTest @ValueSource(strings={"student","teacher","admin"})
    void otherUsersAndNonStudentRolesCannotReadOrGenerateResources(String role) {
        UserContext.set(new LoginUser("student".equals(role)?OTHER:USER,role));
        assertThatThrownBy(()->learning.knowledge(QUESTION)).isInstanceOf(BizException.class);
        assertThatThrownBy(()->learning.nextPractice(QUESTION)).isInstanceOf(BizException.class);
        assertThatThrownBy(()->learning.progress(QUESTION)).isInstanceOf(BizException.class);
        assertThatThrownBy(()->variants.generate(QUESTION)).isInstanceOf(BizException.class);
        verify(model,never()).chat(anyString());assertThat(count("learning_content")).isZero();
    }
    @ParameterizedTest @ValueSource(strings={"[]","{\"content\":\"\"}","{\"content\":123}","{\"content\":\"知识\",\"extra\":true}","{\"content\":\"知识\"} {}","{\"content\":\"<p></p>\"}"})
    void rejectsInvalidKnowledgeBeforePersistence(String response) {
        when(model.chat(anyString())).thenReturn(response);
        assertThatThrownBy(()->learning.knowledge(QUESTION)).isInstanceOf(BizException.class);
        assertThat(count("learning_content")).isZero();
        assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM question WHERE id=? AND status=1",Long.class,QUESTION)).isEqualTo(1);
    }
    @Test void failedGenerationKeepsOldResourcesAvailableForExplicitRepeat() {
        var original=learning.nextPractice(QUESTION);answer(original,1);
        var first=learning.nextPractice(QUESTION);answer(first,1);answer(learning.nextPractice(QUESTION),1);answer(learning.nextPractice(QUESTION),1);
        when(model.chat(anyString())).thenThrow(new IllegalStateException("simulated timeout"));
        assertThatThrownBy(()->learning.nextPractice(QUESTION)).isInstanceOf(BizException.class);
        assertThat(count("variant_question")).isEqualTo(3);assertThat(variants.list(QUESTION)).allMatch(v->v.getPracticed());
        answer(first,0);assertThat(learning.progress(QUESTION).practicedVariantIds()).hasSize(3);
    }
    @Test void duplicateBatchRollsBackEveryInsertedVariant() {
        when(model.chat(anyString())).thenReturn(batch(1).replace("第1组题二","第1组题一"));
        assertThatThrownBy(()->variants.generate(QUESTION)).isInstanceOf(BizException.class);
        assertThat(count("variant_question")).isZero();
    }
    @Test void alreadyStoredStemsAreNotSavedAsNewQuestionsAfterExhaustion() {
        var pool=variants.generate(QUESTION);
        for(var v:pool) answer(new PracticeResourceVO(null,v.getId(),v.getStem(),v.getAnswer(),v.getDifficulty(),"existing"),1);
        when(model.chat(anyString())).thenReturn(batch(1));
        assertThatThrownBy(()->variants.generate(QUESTION)).isInstanceOf(BizException.class);
        assertThat(count("variant_question")).isEqualTo(3);
    }
    @Test void contentEditInvalidatesKnowledgeAndSourceOnlyEditKeepsIt() {
        var a=learning.knowledge(QUESTION);
        questions.update(QUESTION,edit("求函数的定义域","新的来源"));
        assertThat(learning.knowledge(QUESTION).id()).isEqualTo(a.id());verify(model,times(1)).chat(anyString());
        questions.update(QUESTION,edit("求分式函数的定义域","新的来源"));
        assertThat(count("learning_content")).isZero();assertThat(learning.knowledge(QUESTION).reused()).isFalse();verify(model,times(2)).chat(anyString());
    }
    @Test void staleKnowledgeResponseCannotWriteAfterAnEdit() {
        when(model.chat(anyString())).thenAnswer(invocation->{jdbc.update("UPDATE question SET stem='题干已变化' WHERE id=?",QUESTION);return "{\"content\":\"旧题的知识内容\"}";});
        assertThatThrownBy(()->learning.knowledge(QUESTION)).isInstanceOf(BizException.class);assertThat(count("learning_content")).isZero();
    }
    @Test void deleteQuestionAlsoRemovesItsKnowledgeCache() {
        learning.knowledge(QUESTION);questions.remove(QUESTION);assertThat(count("learning_content")).isZero();
        assertThatThrownBy(()->learning.knowledge(QUESTION)).isInstanceOf(BizException.class);
    }
    @Test void concurrentKnowledgeRequestsShareOneGeneratedRecord() throws Exception {
        CountDownLatch entered=new CountDownLatch(1),release=new CountDownLatch(1),secondStarted=new CountDownLatch(1);
        when(model.chat(anyString())).thenAnswer(invocation->{entered.countDown();if(!release.await(10,TimeUnit.SECONDS))throw new IllegalStateException("test timeout");return "{\"content\":\"并发生成的知识内容\"}";});
        try(ExecutorService executor=Executors.newFixedThreadPool(2)) {
            Callable<com.example.wrongbook.vo.LearningContentVO> task=()->{UserContext.set(new LoginUser(USER,"student"));try{return learning.knowledge(QUESTION);}finally{UserContext.clear();}};
            var first=executor.submit(task);assertThat(entered.await(10,TimeUnit.SECONDS)).isTrue();
            var second=executor.submit(()->{secondStarted.countDown();return task.call();});assertThat(secondStarted.await(10,TimeUnit.SECONDS)).isTrue();release.countDown();
            assertThat(first.get(10,TimeUnit.SECONDS).id()).isEqualTo(second.get(10,TimeUnit.SECONDS).id());
        } finally {release.countDown();}
        verify(model,times(1)).chat(anyString());assertThat(count("learning_content")).isEqualTo(1);
    }
}
