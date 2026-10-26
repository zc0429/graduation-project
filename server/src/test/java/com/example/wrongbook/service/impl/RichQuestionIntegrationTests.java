package com.example.wrongbook.service.impl;

import com.example.wrongbook.common.LoginUser;
import com.example.wrongbook.common.UserContext;
import com.example.wrongbook.dto.PracticeRequest;
import com.example.wrongbook.dto.QuestionRequest;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.service.PracticeService;
import com.example.wrongbook.service.QuestionService;
import com.example.wrongbook.service.ReviewPlanService;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.transaction.annotation.Transactional;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;

import java.io.ByteArrayInputStream;
import java.time.LocalDate;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@Transactional
class RichQuestionIntegrationTests {
    private static final long USER_ID = 97501L;
    @Autowired private QuestionService questions;
    @Autowired private QuestionMapper mapper;
    @Autowired private PracticeService practices;
    @Autowired private ReviewPlanService reviews;
    @Autowired private JdbcTemplate jdbc;

    @BeforeEach
    void setUp() {
        jdbc.update("INSERT INTO `user` (id, username, password, nickname, role) VALUES (?, ?, 'unused', '富文本测试', 'student')",
                USER_ID, "__rich_question__");
        UserContext.set(new LoginUser(USER_ID, "student"));
    }

    @AfterEach
    void clearContext() {
        UserContext.clear();
    }

    @Test
    void storesSanitizedRichTextAndKeepsLearningRecordsAcrossAnEdit() {
        QuestionRequest input = request("<p onclick='x()'>函数 x<sup>2</sup></p><ul><li>求零点</li></ul>");
        long id = questions.create(input);
        assertThat(mapper.selectById(id).getStem()).isEqualTo("<p>函数 x<sup>2</sup></p><ul><li>求零点</li></ul>");
        assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM review_plan WHERE question_id=?", Integer.class, id)).isEqualTo(5);
        PracticeRequest practice = new PracticeRequest();
        practice.setQuestionId(id);
        practice.setIsCorrect(1);
        practices.submit(practice);
        input.setStem("<p><strong>订正</strong> x<sup>2</sup></p>");
        questions.update(id, input);
        assertThat(questions.detail(id).getStem()).contains("<strong>订正</strong>");
        assertThat(mapper.selectById(id).getMastery()).isEqualTo(15);
        assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM practice_record WHERE question_id=?", Integer.class, id)).isEqualTo(1);
        assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM review_plan WHERE question_id=? AND status=0", Integer.class, id)).isEqualTo(5);
    }

    @Test
    void exportsPlainTextAndProvidesPlainReviewSummariesWithExistingTextCompatible() throws Exception {
        long id = questions.create(request("<p>求 x<sup>2</sup></p><p>第二行</p>"));
        jdbc.update("UPDATE review_plan SET plan_date=? WHERE question_id=?", LocalDate.now(), id);
        assertThat(reviews.today()).hasSize(5).allSatisfy(plan ->
                assertThat(plan.getStemSummary()).isEqualTo("求 x^(2)\n第二行"));
        long planId = reviews.today().getFirst().getId();
        reviews.finish(planId);
        assertThat(reviews.today()).hasSize(4);
        assertThat(jdbc.queryForObject("SELECT status FROM review_plan WHERE id=?", Integer.class, planId)).isEqualTo(1);
        assertThat(jdbc.queryForObject("SELECT finish_time IS NOT NULL FROM review_plan WHERE id=?", Boolean.class, planId)).isTrue();
        assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM review_plan WHERE question_id=? AND plan_date=?",
                Integer.class, id, LocalDate.now())).isEqualTo(5);
        MockHttpServletResponse response = new MockHttpServletResponse();
        questions.export(null, null, response);
        try (XSSFWorkbook workbook = new XSSFWorkbook(new ByteArrayInputStream(response.getContentAsByteArray()))) {
            assertThat(workbook.getSheetAt(0).getRow(1).getCell(0).getStringCellValue())
                    .isEqualTo("求 x^(2)\n第二行");
        }
        QuestionRequest legacy = request("纯文本 0 < x < 3\n旧题可编辑");
        questions.update(id, legacy);
        assertThat(questions.detail(id).getStem()).isEqualTo(legacy.getStem());
    }

    private QuestionRequest request(String stem) {
        QuestionRequest value = new QuestionRequest();
        value.setSubjectId(1L);
        value.setStem(stem);
        return value;
    }
}
