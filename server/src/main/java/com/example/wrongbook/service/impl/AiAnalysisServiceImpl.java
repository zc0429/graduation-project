package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.example.wrongbook.common.BizException;
import com.example.wrongbook.common.UserContext;
import com.example.wrongbook.entity.AiAnalysis;
import com.example.wrongbook.entity.KnowledgePoint;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.mapper.AiAnalysisMapper;
import com.example.wrongbook.mapper.KnowledgePointMapper;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.service.AiAnalysisService;
import com.example.wrongbook.service.EmbeddingService;
import com.example.wrongbook.service.LlmClient;
import com.example.wrongbook.service.MessageService;
import com.example.wrongbook.service.RagService;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;

import java.util.List;
import java.util.concurrent.Executor;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class AiAnalysisServiceImpl implements AiAnalysisService {

    private final AiAnalysisMapper aiAnalysisMapper;
    private final QuestionMapper questionMapper;
    private final KnowledgePointMapper knowledgePointMapper;
    private final EmbeddingService embeddingService;
    private final RagService ragService;
    private final LlmClient llmClient;
    private final ObjectMapper objectMapper;
    private final MessageService messageService;
    private final TransactionTemplate transactionTemplate;
    @Qualifier("aiTaskExecutor")
    private final Executor aiTaskExecutor;

    @Override
    public void trigger(Long questionId) {
        Question question = checkOwnQuestion(questionId);
        AiAnalysis exist = findByQuestionId(questionId);
        if (exist != null && exist.getStatus() == 0) {
            return;
        }
        if (exist == null) {
            AiAnalysis record = new AiAnalysis();
            record.setQuestionId(question.getId());
            record.setStatus(0);
            aiAnalysisMapper.insert(record);
        } else {
            exist.setStatus(0);
            exist.setKnowledgePointId(null);
            exist.setErrorCause(null);
            exist.setAnalysis(null);
            exist.setReferenceIds(null);
            aiAnalysisMapper.updateById(exist);
        }
        aiTaskExecutor.execute(() -> doAnalyze(questionId));
    }

    @Override
    public AiAnalysis getByQuestion(Long questionId) {
        checkOwnQuestion(questionId);
        return findByQuestionId(questionId);
    }

    /**
     * 异步执行解析（论文 4.1 异步化约定）：立即返回，后台回写状态；
     * 失败置 status=2 不影响错题基本数据（论文 3.5 可靠性约定）。
     * 通过显式线程池提交，避免同类内自调用导致 @Async 代理失效。
     */
    private void doAnalyze(Long questionId) {
        AiAnalysis record = findByQuestionId(questionId);
        if (record == null) {
            log.info("AI 解析任务已失效，忽略执行，questionId={}", questionId);
            return;
        }
        try {
            Thread.sleep(1500);
            Question question = questionMapper.selectById(questionId);
            if (question == null || !isActiveRecord(record)) {
                log.info("AI 解析任务已失效，忽略执行，questionId={}", questionId);
                return;
            }
            // 1. 计算题干向量；完成前只保存在当前输入快照中
            List<Double> vector = embeddingService.embed(question.getStem());
            String embedding = objectMapper.writeValueAsString(vector);
            question.setEmbedding(embedding);
            // 2. RAG 检索同科目相似参考题
            List<Question> references = ragService.retrieveSimilar(question, 3);
            // 3. 组装提示词（含该科目二级考点候选）并调用大模型
            List<KnowledgePoint> candidates = knowledgePointMapper.selectList(
                    new LambdaQueryWrapper<KnowledgePoint>()
                            .eq(KnowledgePoint::getSubjectId, question.getSubjectId())
                            .ne(KnowledgePoint::getParentId, 0));
            String prompt = buildPrompt(question, candidates, references);
            String content = llmClient.chat(prompt);
            // 4. 解析结构化 JSON 结果
            JsonNode json = objectMapper.readTree(stripMarkdownFence(content));
            Long knowledgePointId = json.hasNonNull("knowledgePointId")
                    ? json.get("knowledgePointId").asLong() : null;
            Integer difficulty = json.hasNonNull("difficulty") ? json.get("difficulty").asInt() : null;
            String errorCause = json.path("errorCause").asText(null);
            String analysis = json.path("analysis").asText(null);
            String referenceIds = objectMapper.writeValueAsString(
                    references.stream().map(Question::getId).collect(Collectors.toList()));
            String llmModel = llmClient.model();
            String kpName = null;
            if (knowledgePointId != null) {
                KnowledgePoint kp = knowledgePointMapper.selectById(knowledgePointId);
                kpName = kp == null ? null : kp.getName();
            }
            String finalKpName = kpName;
            boolean completed = Boolean.TRUE.equals(transactionTemplate.execute(status -> {
                int questionRows = questionMapper.update(null, matchingInput(question)
                        .set(Question::getEmbedding, embedding)
                        .set(Question::getKnowledgePointId, knowledgePointId)
                        .set(Question::getDifficulty, difficulty));
                if (questionRows != 1) {
                    status.setRollbackOnly();
                    return false;
                }
                int analysisRows = aiAnalysisMapper.update(null, new LambdaUpdateWrapper<AiAnalysis>()
                        .eq(AiAnalysis::getId, record.getId())
                        .eq(AiAnalysis::getQuestionId, questionId)
                        .eq(AiAnalysis::getStatus, 0)
                        .set(AiAnalysis::getKnowledgePointId, knowledgePointId)
                        .set(AiAnalysis::getErrorCause, errorCause)
                        .set(AiAnalysis::getAnalysis, analysis)
                        .set(AiAnalysis::getReferenceIds, referenceIds)
                        .set(AiAnalysis::getLlmModel, llmModel)
                        .set(AiAnalysis::getStatus, 1));
                if (analysisRows != 1) {
                    status.setRollbackOnly();
                    return false;
                }
                messageService.send(question.getUserId(), "system", "错题解析完成",
                        "你录入的错题已完成 AI 解析"
                                + (finalKpName == null ? "。" : "，归类知识点为「" + finalKpName + "」，难度 "
                                + (difficulty == null ? "未知" : difficulty) + "，前往错题详情页查看。"));
                return true;
            }));
            if (!completed) {
                log.info("AI 解析任务输入已过期，放弃回写，questionId={}", questionId);
            }
        } catch (Exception e) {
            log.error("AI 解析失败，questionId={}", questionId, e);
            aiAnalysisMapper.update(null, new LambdaUpdateWrapper<AiAnalysis>()
                    .eq(AiAnalysis::getId, record.getId())
                    .eq(AiAnalysis::getQuestionId, questionId)
                    .eq(AiAnalysis::getStatus, 0)
                    .set(AiAnalysis::getStatus, 2)
                    .set(AiAnalysis::getLlmModel, llmClient.model()));
        }
    }

    private boolean isActiveRecord(AiAnalysis record) {
        AiAnalysis current = aiAnalysisMapper.selectById(record.getId());
        return current != null && current.getStatus() == 0
                && current.getQuestionId().equals(record.getQuestionId());
    }

    private LambdaUpdateWrapper<Question> matchingInput(Question question) {
        LambdaUpdateWrapper<Question> wrapper = new LambdaUpdateWrapper<Question>()
                .eq(Question::getId, question.getId())
                .eq(Question::getSubjectId, question.getSubjectId())
                .eq(Question::getStem, question.getStem());
        if (question.getAnswer() == null) {
            wrapper.isNull(Question::getAnswer);
        } else {
            wrapper.eq(Question::getAnswer, question.getAnswer());
        }
        return wrapper;
    }

    private String buildPrompt(Question question, List<KnowledgePoint> candidates, List<Question> references) {
        StringBuilder sb = new StringBuilder();
        sb.append(MockLlmClient.TASK_ANALYZE).append("（RAG）\n");
        sb.append("题干：").append(question.getStem()).append("\n");
        if (question.getAnswer() != null) {
            sb.append("答案：").append(question.getAnswer()).append("\n");
        }
        sb.append("候选知识点：\n");
        for (KnowledgePoint kp : candidates) {
            sb.append(kp.getId()).append(':').append(kp.getName()).append("\n");
        }
        sb.append("参考题目：\n");
        for (Question ref : references) {
            String stem = ref.getStem();
            sb.append("- ").append(stem.length() > 50 ? stem.substring(0, 50) + "…" : stem).append("\n");
        }
        sb.append("要求：输出 JSON，含 knowledgePointId/errorCause/analysis/difficulty(1-5)");
        return sb.toString();
    }

    /** 兼容真实大模型可能输出的 ```json 包裹 */
    private String stripMarkdownFence(String content) {
        String s = content.trim();
        if (s.startsWith("```")) {
            s = s.replaceFirst("^```(json)?\\s*", "").replaceFirst("\\s*```$", "");
        }
        return s;
    }

    private AiAnalysis findByQuestionId(Long questionId) {
        return aiAnalysisMapper.selectOne(
                new LambdaQueryWrapper<AiAnalysis>().eq(AiAnalysis::getQuestionId, questionId));
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
