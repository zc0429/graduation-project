package com.example.wrongbook.service.impl;

import com.example.wrongbook.common.BizException;
import com.example.wrongbook.common.LoginUser;
import com.example.wrongbook.common.UserContext;
import com.example.wrongbook.dto.KnowledgePointRequest;
import com.example.wrongbook.dto.QuestionRequest;
import com.example.wrongbook.service.KnowledgePointService;
import com.example.wrongbook.service.QuestionService;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.transaction.annotation.Transactional;

import static org.assertj.core.api.Assertions.*;

@SpringBootTest
@Transactional
class CatalogIntegrityIntegrationTests {
    private static final long USER = 889101L, ROOT = 889201L, LEAF = 889202L, QUESTION = 889301L;
    @Autowired QuestionService questions;
    @Autowired KnowledgePointService knowledge;
    @Autowired JdbcTemplate jdbc;

    @BeforeEach void setup() {
        UserContext.set(new LoginUser(USER, "student"));
        jdbc.update("INSERT INTO knowledge_point(id,subject_id,parent_id,name) VALUES (?,1,0,'审计章节')", ROOT);
        jdbc.update("INSERT INTO knowledge_point(id,subject_id,parent_id,name) VALUES (?,1,?,'审计考点')", LEAF, ROOT);
        jdbc.update("INSERT INTO question(id,user_id,subject_id,stem,answer) VALUES (?,?,1,'原题','原答案')", QUESTION, USER);
    }

    @AfterEach void clear() { UserContext.clear(); }

    private QuestionRequest question(long subject) {
        QuestionRequest request = new QuestionRequest();
        request.setSubjectId(subject); request.setStem("修改后的题干"); request.setAnswer("修改后的答案");
        return request;
    }

    @Test void unknownSubjectCannotCreateQuestionOrPlans() {
        long before = jdbc.queryForObject("SELECT COUNT(*) FROM question WHERE user_id=?", Long.class, USER);
        assertThatThrownBy(() -> questions.create(question(Long.MAX_VALUE))).isInstanceOf(BizException.class);
        assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM question WHERE user_id=?", Long.class, USER)).isEqualTo(before);
        assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM review_plan WHERE user_id=?", Long.class, USER)).isZero();
    }

    @Test void disabledSubjectCannotReplaceCurrentInput() {
        jdbc.update("INSERT INTO subject(id,name,status) VALUES (889401,'审计停用科目',0)");
        assertThatThrownBy(() -> questions.update(QUESTION, question(889401))).isInstanceOf(BizException.class);
        assertThat(jdbc.queryForObject("SELECT stem FROM question WHERE id=?", String.class, QUESTION)).isEqualTo("原题");
        assertThat(jdbc.queryForObject("SELECT subject_id FROM question WHERE id=?", Long.class, QUESTION)).isEqualTo(1L);
    }

    @Test void leafCannotBecomeParentOfThirdLevel() {
        KnowledgePointRequest request = new KnowledgePointRequest();
        request.setSubjectId(1L); request.setParentId(LEAF); request.setName("不应保存的三级");
        assertThatThrownBy(() -> knowledge.add(request)).isInstanceOf(BizException.class);
        assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM knowledge_point WHERE parent_id=?", Long.class, LEAF)).isZero();
    }

    @ParameterizedTest
    @ValueSource(strings = {"question", "ai_analysis", "learning_content"})
    void referencedLeafCannotBeRemoved(String table) {
        switch (table) {
            case "question" -> jdbc.update("UPDATE question SET knowledge_point_id=? WHERE id=?", LEAF, QUESTION);
            case "ai_analysis" -> jdbc.update("INSERT INTO ai_analysis(question_id,knowledge_point_id) VALUES (?,?)", QUESTION, LEAF);
            case "learning_content" -> jdbc.update("INSERT INTO learning_content(user_id,question_id,knowledge_point_id,input_hash,content) VALUES (?,?,?,REPEAT('a',64),'知识')", USER, QUESTION, LEAF);
            default -> throw new IllegalArgumentException(table);
        }
        assertThatThrownBy(() -> knowledge.remove(LEAF)).isInstanceOf(BizException.class);
        assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM knowledge_point WHERE id=?", Long.class, LEAF)).isEqualTo(1L);
    }

    @Test void unusedLeafAndEmptyChapterCanStillBeRemoved() {
        knowledge.remove(LEAF); knowledge.remove(ROOT);
        assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM knowledge_point WHERE id IN (?,?)", Long.class, ROOT, LEAF)).isZero();
    }
}
