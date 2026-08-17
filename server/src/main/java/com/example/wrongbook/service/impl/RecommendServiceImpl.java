package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.wrongbook.common.BizException;
import com.example.wrongbook.common.UserContext;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.service.RagService;
import com.example.wrongbook.service.RecommendService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class RecommendServiceImpl implements RecommendService {

    private static final int TOP_N = 5;

    private final QuestionMapper questionMapper;
    private final RagService ragService;

    @Override
    public List<Question> similar(Long questionId) {
        Question question = checkOwnQuestion(questionId);
        // Mock 策略：同知识点 + 相近难度优先；不足时用语义向量检索补足
        // 预留：接入真实 Embedding 模型后可改为纯向量余弦相似度排序
        Map<Long, Question> result = new LinkedHashMap<>();
        if (question.getKnowledgePointId() != null) {
            List<Question> sameKp = questionMapper.selectList(new LambdaQueryWrapper<Question>()
                    .eq(Question::getKnowledgePointId, question.getKnowledgePointId())
                    .ne(Question::getId, questionId));
            int difficulty = question.getDifficulty() == null ? 3 : question.getDifficulty();
            sameKp.stream()
                    .sorted(Comparator.comparingInt(q -> Math.abs(
                            (q.getDifficulty() == null ? 3 : q.getDifficulty()) - difficulty)))
                    .limit(TOP_N)
                    .forEach(q -> result.put(q.getId(), q));
        }
        if (result.size() < TOP_N) {
            ragService.retrieveSimilar(question, TOP_N).forEach(q -> result.putIfAbsent(q.getId(), q));
        }
        return new ArrayList<>(result.values()).stream().limit(TOP_N).toList();
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
