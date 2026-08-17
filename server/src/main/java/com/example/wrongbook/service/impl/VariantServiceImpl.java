package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.wrongbook.common.BizException;
import com.example.wrongbook.common.UserContext;
import com.example.wrongbook.entity.KnowledgePoint;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.entity.VariantQuestion;
import com.example.wrongbook.mapper.KnowledgePointMapper;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.mapper.VariantQuestionMapper;
import com.example.wrongbook.service.LlmClient;
import com.example.wrongbook.service.VariantService;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class VariantServiceImpl implements VariantService {

    private final VariantQuestionMapper variantQuestionMapper;
    private final QuestionMapper questionMapper;
    private final KnowledgePointMapper knowledgePointMapper;
    private final LlmClient llmClient;
    private final ObjectMapper objectMapper;

    @Override
    public List<VariantQuestion> generate(Long questionId) {
        Question question = checkOwnQuestion(questionId);
        String kpName = "未归类";
        if (question.getKnowledgePointId() != null) {
            KnowledgePoint kp = knowledgePointMapper.selectById(question.getKnowledgePointId());
            if (kp != null) {
                kpName = kp.getName();
            }
        }
        String prompt = MockLlmClient.TASK_VARIANT + "\n"
                + "原题题干：" + question.getStem() + "\n"
                + "原题答案：" + (question.getAnswer() == null ? "" : question.getAnswer()) + "\n"
                + "知识点：" + kpName + "\n"
                + "要求：输出 JSON，variants 数组含 3 道变式（stem/answer/difficulty）";
        try {
            JsonNode json = objectMapper.readTree(stripMarkdownFence(llmClient.chat(prompt)));
            List<VariantQuestion> saved = new ArrayList<>();
            for (JsonNode node : json.path("variants")) {
                VariantQuestion variant = new VariantQuestion();
                variant.setQuestionId(questionId);
                variant.setStem(node.path("stem").asText());
                variant.setAnswer(node.path("answer").asText(null));
                variant.setDifficulty(node.hasNonNull("difficulty") ? node.get("difficulty").asInt() : null);
                variantQuestionMapper.insert(variant);
                saved.add(variant);
            }
            return saved;
        } catch (Exception e) {
            log.error("变式题生成失败，questionId={}", questionId, e);
            throw new BizException("变式题生成失败，请稍后重试");
        }
    }

    @Override
    public List<VariantQuestion> list(Long questionId) {
        checkOwnQuestion(questionId);
        return variantQuestionMapper.selectList(new LambdaQueryWrapper<VariantQuestion>()
                .eq(VariantQuestion::getQuestionId, questionId)
                .orderByAsc(VariantQuestion::getId));
    }

    private String stripMarkdownFence(String content) {
        String s = content.trim();
        if (s.startsWith("```")) {
            s = s.replaceFirst("^```(json)?\\s*", "").replaceFirst("\\s*```$", "");
        }
        return s;
    }

    private Question checkOwnQuestion(Long questionId) {
        Question question = questionMapper.selectById(questionId);
        if (question == null) {
            throw new BizException("错题不存在");
        }
        if (!"admin".equals(UserContext.getRole()) && !question.getUserId().equals(UserContext.getUserId())) {
            throw new BizException("无权访问该错题");
        }
        return question;
    }
}
