package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.wrongbook.common.BizException;
import com.example.wrongbook.entity.KnowledgePoint;
import com.example.wrongbook.entity.LearningContent;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.entity.VariantQuestion;
import com.example.wrongbook.mapper.KnowledgePointMapper;
import com.example.wrongbook.mapper.LearningContentMapper;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.service.LearningService;
import com.example.wrongbook.service.LlmClient;
import com.example.wrongbook.service.VariantService;
import com.example.wrongbook.util.QuestionContent;
import com.example.wrongbook.vo.LearningContentVO;
import com.example.wrongbook.vo.PracticeResourceVO;
import com.example.wrongbook.vo.PracticeProgressVO;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;

@Service
@RequiredArgsConstructor
@Slf4j
public class LearningServiceImpl implements LearningService {
    private final LearningResourceAccess access;
    private final LearningContentMapper contentMapper;
    private final QuestionMapper questionMapper;
    private final KnowledgePointMapper knowledgePointMapper;
    private final VariantService variantService;
    private final LlmClient llmClient;
    private final ObjectMapper objectMapper;
    private final TransactionTemplate transactionTemplate;

    @Override
    public LearningContentVO knowledge(Long questionId) {
        return access.serialized(questionId, () -> knowledgeWithinLock(questionId));
    }

    private LearningContentVO knowledgeWithinLock(Long questionId) {
        Question question = access.ownQuestion(questionId);
        String hash = inputHash(question);
        LearningContent cached = find(questionId);
        if (cached != null && hash.equals(cached.getInputHash())) return view(cached, true);
        // Cache hits remain available even when no model credential is configured.
        llmClient.verifyReady();
        String prompt = MockLlmClient.TASK_KNOWLEDGE + "\n"
                + "围绕以下原题与知识点提供中文知识讲解，说明概念、适用条件和常见误区，不虚构学生作答步骤。\n"
                + "题干：" + QuestionContent.plainText(question.getStem()) + "\n"
                + "参考答案：" + (question.getAnswer() == null ? "" : question.getAnswer()) + "\n"
                + "知识点：" + knowledgeName(question) + "\n"
                + "只返回JSON对象，必须且仅含一个字符串字段content，内容为非空纯文本，不超过16000字符。";
        try {
            JsonNode json = objectMapper.reader().with(DeserializationFeature.FAIL_ON_TRAILING_TOKENS)
                    .readTree(llmClient.chat(prompt));
            if (json == null || !json.isObject() || json.size() != 1 || !json.has("content")
                    || !json.get("content").isTextual()) throw new IllegalArgumentException("知识内容结构不合格");
            String content = QuestionContent.plainText(json.get("content").asText()).trim();
            if (content.isBlank() || content.length() > 16000 || !content.matches("(?s).*[\\u4e00-\\u9fff].*")) {
                throw new IllegalArgumentException("知识内容为空或不合格");
            }
            return transactionTemplate.execute(status -> {
                Question current = questionMapper.selectByIdForUpdate(questionId);
                if (current == null || !hash.equals(inputHash(current))) {
                    throw new IllegalStateException("题目内容已变化，请重新学习");
                }
                LearningContent row = find(questionId);
                // Recheck inside the short write transaction for concurrent requests on other instances.
                if (row != null && hash.equals(row.getInputHash())) return view(row, true);
                boolean insert = row == null;
                if (insert) row = new LearningContent();
                row.setUserId(question.getUserId());
                row.setQuestionId(questionId);
                row.setKnowledgePointId(question.getKnowledgePointId());
                row.setInputHash(hash);
                row.setContent(content);
                int count = insert ? contentMapper.insert(row) : contentMapper.updateById(row);
                if (count != 1) throw new IllegalStateException("知识内容保存失败");
                return view(row, false);
            });
        } catch (Exception failure) {
            log.warn("知识学习资源获取失败，questionId={}，errorType={}", questionId, failure.getClass().getSimpleName());
            throw new BizException("知识内容暂时无法生成，已有错题已保留，可查看解析或稍后重试");
        }
    }

    @Override
    public PracticeResourceVO nextPractice(Long questionId) {
        return access.serialized(questionId, () -> {
            Question q = access.ownQuestion(questionId);
            if (!access.originalPracticed(questionId)) {
                return new PracticeResourceVO(q.getId(), null, q.getStem(), q.getAnswer(), q.getDifficulty(), "original");
            }
            List<VariantQuestion> variants = variantService.list(questionId);
            VariantQuestion available = variants.stream().filter(v -> !Boolean.TRUE.equals(v.getPracticed())).findFirst().orElse(null);
            String source = "existing";
            if (available == null) {
                List<VariantQuestion> supplied = variantService.generate(questionId);
                if (supplied.isEmpty()) throw new BizException("暂无可用练习题，可重做已练题或稍后重试");
                available = supplied.getFirst();
                source = "generated";
            }
            return new PracticeResourceVO(null, available.getId(), available.getStem(), available.getAnswer(), available.getDifficulty(), source);
        });
    }

    @Override
    public PracticeProgressVO progress(Long questionId) {
        access.ownQuestion(questionId);
        List<Long> practiced = variantService.list(questionId).stream()
                .filter(v -> Boolean.TRUE.equals(v.getPracticed())).map(VariantQuestion::getId).toList();
        return new PracticeProgressVO(access.originalPracticed(questionId), practiced);
    }

    private LearningContent find(Long questionId) {
        return contentMapper.selectOne(new LambdaQueryWrapper<LearningContent>().eq(LearningContent::getQuestionId, questionId));
    }

    private LearningContentVO view(LearningContent row, boolean reused) {
        return new LearningContentVO(row.getId(), row.getQuestionId(), row.getKnowledgePointId(), row.getContent(), reused);
    }

    private String knowledgeName(Question q) {
        KnowledgePoint kp = q.getKnowledgePointId() == null ? null : knowledgePointMapper.selectById(q.getKnowledgePointId());
        return kp == null ? "未归类，依据原题说明相关知识" : kp.getName();
    }

    private String inputHash(Question q) {
        try {
            byte[] bytes = objectMapper.writeValueAsBytes(new Object[]{q.getId(), q.getUserId(), q.getSubjectId(),
                    q.getKnowledgePointId(), q.getStem(), q.getAnswer(), knowledgeName(q)});
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
        } catch (Exception e) { throw new IllegalStateException("学习资源快照构建失败", e); }
    }
}
