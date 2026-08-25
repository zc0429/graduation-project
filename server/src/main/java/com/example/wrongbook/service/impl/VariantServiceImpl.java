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
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.util.StringUtils;
import org.springframework.web.client.RestClientResponseException;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

@Slf4j
@Service
@RequiredArgsConstructor
public class VariantServiceImpl implements VariantService {

    private final VariantQuestionMapper variantQuestionMapper;
    private final QuestionMapper questionMapper;
    private final KnowledgePointMapper knowledgePointMapper;
    private final LlmClient llmClient;
    private final ObjectMapper objectMapper;
    private final TransactionTemplate transactionTemplate;

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
                + "输出要求（必须全部满足）：\n"
                + "1. 只输出一个 JSON 对象，不得输出解释、Markdown 或嵌套包装；\n"
                + "2. 根对象必须且仅含 variants 数组，数组必须恰好 3 项；\n"
                + "3. 每项必须且仅含 stem、answer、difficulty；stem 与 answer 为非空字符串；\n"
                + "4. difficulty 必须是 1-5 的数字整数，不得写中文或字符串；\n"
                + "严格按此结构输出："
                + "{\"variants\":[{\"stem\":\"题干1\",\"answer\":\"答案1\",\"difficulty\":3},"
                + "{\"stem\":\"题干2\",\"answer\":\"答案2\",\"difficulty\":3},"
                + "{\"stem\":\"题干3\",\"answer\":\"答案3\",\"difficulty\":3}]}";
        try {
            String content = llmClient.chat(prompt);
            List<VariantQuestion> variants = parseVariants(questionId, content);
            transactionTemplate.executeWithoutResult(status -> {
                Question currentQuestion = questionMapper.selectByIdForUpdate(questionId);
                if (!matchesVariantInput(question, currentQuestion)) {
                    throw new IllegalStateException("原题输入已变化，放弃写入旧变式题");
                }
                for (VariantQuestion variant : variants) {
                    if (variantQuestionMapper.insert(variant) != 1) {
                        throw new IllegalStateException("变式题保存失败");
                    }
                }
            });
            return variants;
        } catch (Exception e) {
            logVariantFailure(questionId, e);
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

    private List<VariantQuestion> parseVariants(Long questionId, String content) throws Exception {
        JsonNode json = objectMapper.readTree(stripMarkdownFence(content));
        if (!json.isObject()) {
            throw new IllegalArgumentException("变式题响应根节点必须是 JSON 对象");
        }
        if (json.size() != 1 || !json.has("variants")) {
            throw new IllegalArgumentException("变式题响应根字段必须与约定结构完全一致");
        }
        JsonNode nodes = json.get("variants");
        if (nodes == null || !nodes.isArray() || nodes.size() != 3) {
            throw new IllegalArgumentException("变式题响应必须包含恰好 3 道题");
        }

        List<VariantQuestion> variants = new ArrayList<>(3);
        for (JsonNode node : nodes) {
            if (!node.isObject()) {
                throw new IllegalArgumentException("变式题条目必须是 JSON 对象");
            }
            if (node.size() != 3
                    || !node.has("stem")
                    || !node.has("answer")
                    || !node.has("difficulty")) {
                throw new IllegalArgumentException("变式题条目字段必须与约定结构完全一致");
            }
            JsonNode stem = node.get("stem");
            JsonNode answer = node.get("answer");
            JsonNode difficulty = node.get("difficulty");
            if (stem == null || !stem.isTextual() || !StringUtils.hasText(stem.asText())) {
                throw new IllegalArgumentException("变式题题干不能为空");
            }
            if (answer == null || !answer.isTextual() || !StringUtils.hasText(answer.asText())) {
                throw new IllegalArgumentException("变式题答案不能为空");
            }
            if (difficulty == null || !difficulty.isIntegralNumber()
                    || !difficulty.canConvertToInt()
                    || difficulty.asInt() < 1 || difficulty.asInt() > 5) {
                throw new IllegalArgumentException("变式题难度必须是 1-5 的整数");
            }

            VariantQuestion variant = new VariantQuestion();
            variant.setQuestionId(questionId);
            variant.setStem(stem.asText().trim());
            variant.setAnswer(answer.asText().trim());
            variant.setDifficulty(difficulty.asInt());
            variants.add(variant);
        }
        return variants;
    }

    private boolean matchesVariantInput(Question snapshot, Question current) {
        return current != null
                && Objects.equals(snapshot.getId(), current.getId())
                && Objects.equals(snapshot.getUserId(), current.getUserId())
                && Objects.equals(snapshot.getSubjectId(), current.getSubjectId())
                && Objects.equals(snapshot.getKnowledgePointId(), current.getKnowledgePointId())
                && Objects.equals(snapshot.getStem(), current.getStem())
                && Objects.equals(snapshot.getAnswer(), current.getAnswer());
    }

    private String stripMarkdownFence(String content) {
        String s = content.trim();
        if (s.startsWith("```")) {
            log.warn("变式题响应包含 Markdown 代码块，已进行兼容清理");
            s = s.replaceFirst("(?i)^```\\s*(?:json)?\\s*", "")
                    .replaceFirst("\\s*```$", "");
        }
        return s;
    }

    private void logVariantFailure(Long questionId, Exception failure) {
        if (failure instanceof RestClientResponseException responseException) {
            log.error("变式题请求失败，questionId={}，httpStatus={}，errorType={}",
                    questionId, responseException.getStatusCode().value(),
                    failure.getClass().getSimpleName());
            return;
        }
        if (failure instanceof IllegalArgumentException) {
            log.error("变式题结构校验失败，questionId={}，errorType={}",
                    questionId, failure.getClass().getSimpleName());
            return;
        }
        log.error("变式题生成失败，questionId={}，errorType={}",
                questionId, failure.getClass().getSimpleName());
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
