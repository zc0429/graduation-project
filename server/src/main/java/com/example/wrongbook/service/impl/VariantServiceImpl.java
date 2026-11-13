package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.wrongbook.common.BizException;
import com.example.wrongbook.common.ResultCode;
import com.example.wrongbook.common.UserContext;
import com.example.wrongbook.entity.KnowledgePoint;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.entity.VariantQuestion;
import com.example.wrongbook.mapper.KnowledgePointMapper;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.mapper.VariantQuestionMapper;
import com.example.wrongbook.service.LlmClient;
import com.example.wrongbook.service.VariantService;
import com.example.wrongbook.util.QuestionContent;
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
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;

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
    private final LearningResourceAccess resourceAccess;

    @Override
    public List<VariantQuestion> generate(Long questionId) {
        return resourceAccess.serialized(questionId, () -> generateOrReuse(questionId));
    }

    private List<VariantQuestion> generateOrReuse(Long questionId) {
        Question question = checkOwnQuestion(questionId);
        List<VariantQuestion> stored = list(questionId);
        List<VariantQuestion> available = stored.stream().filter(v -> !Boolean.TRUE.equals(v.getPracticed())).toList();
        if (!available.isEmpty()) return available;
        llmClient.verifyReady();
        String kpName = "未归类";
        if (question.getKnowledgePointId() != null) {
            KnowledgePoint kp = knowledgePointMapper.selectById(question.getKnowledgePointId());
            if (kp != null) {
                kpName = kp.getName();
            }
        }
        String history = stored.stream().skip(Math.max(0, stored.size() - 100))
                .map(v -> QuestionContent.plainText(v.getStem()))
                .map(t -> t.substring(0, Math.min(80, t.length())))
                .collect(java.util.stream.Collectors.joining("\n"));
        String prompt = MockLlmClient.TASK_VARIANT + "\n"
                + "已生成题目（不要重复，改变具体条件，不仅修改措辞）：\n" + history + "\n"
                + "原题题干：" + QuestionContent.plainText(question.getStem()) + "\n"
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
            AtomicReference<List<VariantQuestion>> chosen = new AtomicReference<>(variants);
            transactionTemplate.executeWithoutResult(status -> {
                Question currentQuestion = questionMapper.selectByIdForUpdate(questionId);
                if (!matchesVariantInput(question, currentQuestion)) {
                    throw new IllegalStateException("原题输入已变化，放弃写入旧变式题");
                }
                List<VariantQuestion> current = list(questionId);
                List<VariantQuestion> reusable = current.stream().filter(v -> !Boolean.TRUE.equals(v.getPracticed())).toList();
                if (!reusable.isEmpty()) { chosen.set(reusable); return; }
                Set<String> stems = new HashSet<>();
                current.forEach(v -> stems.add(normalizedStem(v.getStem())));
                for (VariantQuestion variant : variants) {
                    if (!stems.add(normalizedStem(variant.getStem()))) {
                        throw new IllegalArgumentException("模型返回重复题目，未保存");
                    }
                    if (variantQuestionMapper.insert(variant) != 1) {
                        throw new IllegalStateException("变式题保存失败");
                    }
                }
            });
            return chosen.get();
        } catch (Exception e) {
            logVariantFailure(questionId, e);
            throw new BizException("变式题生成失败，请稍后重试");
        }
    }

    @Override
    public List<VariantQuestion> list(Long questionId) {
        checkOwnQuestion(questionId);
        List<VariantQuestion> variants = variantQuestionMapper.selectList(new LambdaQueryWrapper<VariantQuestion>()
                .eq(VariantQuestion::getQuestionId, questionId)
                .orderByAsc(VariantQuestion::getId));
        Set<Long> practiced = resourceAccess.practicedVariants(variants);
        variants.forEach(v -> v.setPracticed(practiced.contains(v.getId())));
        return variants;
    }

    private String normalizedStem(String text) {
        return QuestionContent.plainText(text).replaceAll("\\s+", "");
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
            String plainStem = QuestionContent.plainText(stem.asText()).trim();
            if (plainStem.isBlank() || plainStem.length() > 2000 || answer.asText().length() > 8000) {
                throw new IllegalArgumentException("变式题内容长度不合格");
            }
            variant.setStem(plainStem);
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
        return resourceAccess.ownQuestion(questionId);
    }
}
