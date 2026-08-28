package com.example.wrongbook.service.impl;

import com.example.wrongbook.common.BizException;
import com.example.wrongbook.common.LoginUser;
import com.example.wrongbook.common.UserContext;
import com.example.wrongbook.dto.PracticeRequest;
import com.example.wrongbook.dto.QuestionRequest;
import com.example.wrongbook.entity.ReviewPlan;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.mapper.ReviewPlanMapper;
import com.example.wrongbook.service.PracticeService;
import com.example.wrongbook.service.QuestionService;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.bean.override.mockito.MockitoSpyBean;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.isNull;
import static org.mockito.Mockito.doThrow;

@SpringBootTest
class FinalDeliveryCoreIntegrationTests {

    private static final long USER_ID = 96001L;
    private static final long SUBJECT_ID = 96001L;
    private static final long QUESTION_ID = 96001L;
    private static final String CREATE_SOURCE = "__final_delivery_create_tx__";

    @Autowired
    private QuestionService questionService;

    @Autowired
    private PracticeService practiceService;

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @MockitoSpyBean
    private ReviewPlanMapper reviewPlanMapper;

    @MockitoSpyBean
    private QuestionMapper questionMapper;

    @BeforeEach
    void setUp() {
        cleanFixtures();
        jdbcTemplate.update("INSERT INTO `user` (id, username, password, nickname, role, status) "
                        + "VALUES (?, ?, ?, ?, 'student', 1)",
                USER_ID, "__final_delivery_student__", "unused", "冻结审计学生");
        jdbcTemplate.update("INSERT INTO subject (id, name, code, sort, status) VALUES (?, ?, ?, 999, 1)",
                SUBJECT_ID, "冻结审计科目", "FINAL_AUDIT");
        jdbcTemplate.update("INSERT INTO question (id, user_id, subject_id, stem, answer, source, mastery, status) "
                        + "VALUES (?, ?, ?, ?, ?, ?, 0, 1)",
                QUESTION_ID, USER_ID, SUBJECT_ID, "冻结审计练习题", "答案", "__final_delivery_practice__");
        UserContext.set(new LoginUser(USER_ID, "student"));
    }

    @AfterEach
    void tearDown() {
        UserContext.clear();
        cleanFixtures();
    }

    @Test
    void questionCreateRollsBackWhenReviewPlanCreationFails() {
        doThrow(new IllegalStateException("forced review plan failure"))
                .when(reviewPlanMapper).insert(any(ReviewPlan.class));

        assertThatThrownBy(() -> questionService.create(questionRequest()))
                .isInstanceOf(IllegalStateException.class)
                .hasMessage("forced review plan failure");

        Integer count = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM question WHERE source = ?", Integer.class, CREATE_SOURCE);
        assertThat(count).isZero();
    }

    @Test
    void practiceRejectsQuestionAndVariantSubmittedTogether() {
        PracticeRequest request = practiceRequest();
        request.setQuestionId(QUESTION_ID);
        request.setVariantId(123456L);

        assertThatThrownBy(() -> practiceService.submit(request))
                .isInstanceOf(BizException.class)
                .hasMessage("错题与变式题必须且只能选择一项");

        assertThat(practiceCount()).isZero();
    }

    @Test
    void practiceRecordRollsBackWhenMasteryUpdateFails() {
        doThrow(new IllegalStateException("forced mastery update failure"))
                .when(questionMapper).update(isNull(), any());
        PracticeRequest request = practiceRequest();
        request.setQuestionId(QUESTION_ID);

        assertThatThrownBy(() -> practiceService.submit(request))
                .isInstanceOf(IllegalStateException.class)
                .hasMessage("forced mastery update failure");

        assertThat(practiceCount()).isZero();
        assertThat(mastery()).isZero();
    }

    @Test
    void repeatedPracticeUsesBoundedAtomicMasteryUpdates() {
        PracticeRequest first = practiceRequest();
        first.setQuestionId(QUESTION_ID);
        PracticeRequest second = practiceRequest();
        second.setQuestionId(QUESTION_ID);

        practiceService.submit(first);
        practiceService.submit(second);

        assertThat(practiceCount()).isEqualTo(2);
        assertThat(mastery()).isEqualTo(30);
    }

    private QuestionRequest questionRequest() {
        QuestionRequest request = new QuestionRequest();
        request.setSubjectId(SUBJECT_ID);
        request.setStem("创建事务回滚测试题");
        request.setAnswer("测试答案");
        request.setSource(CREATE_SOURCE);
        return request;
    }

    private PracticeRequest practiceRequest() {
        PracticeRequest request = new PracticeRequest();
        request.setUserAnswer("测试作答");
        request.setIsCorrect(1);
        request.setDuration(10);
        return request;
    }

    private int practiceCount() {
        return jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM practice_record WHERE user_id = ? AND question_id = ?",
                Integer.class, USER_ID, QUESTION_ID);
    }

    private int mastery() {
        return jdbcTemplate.queryForObject(
                "SELECT mastery FROM question WHERE id = ?", Integer.class, QUESTION_ID);
    }

    private void cleanFixtures() {
        jdbcTemplate.update("DELETE FROM practice_record WHERE user_id = ?", USER_ID);
        jdbcTemplate.update("DELETE FROM review_plan WHERE user_id = ?", USER_ID);
        jdbcTemplate.update("DELETE FROM question WHERE user_id = ? OR source = ?", USER_ID, CREATE_SOURCE);
        jdbcTemplate.update("DELETE FROM subject WHERE id = ?", SUBJECT_ID);
        jdbcTemplate.update("DELETE FROM `user` WHERE id = ?", USER_ID);
    }
}
