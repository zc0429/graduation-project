package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.service.RagService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class RagServiceImpl implements RagService {

    private final QuestionMapper questionMapper;
    private final ObjectMapper objectMapper;

    @Override
    public List<Question> retrieveSimilar(Question question, int topN) {
        List<Double> target = parseVector(question.getEmbedding());
        if (target == null) {
            return List.of();
        }
        Long ownerId = question.getUserId();
        List<Question> pool = questionMapper.selectList(new LambdaQueryWrapper<Question>()
                .eq(Question::getUserId, ownerId)
                .eq(Question::getSubjectId, question.getSubjectId())
                .ne(Question::getId, question.getId())
                .isNotNull(Question::getEmbedding));
        // 应用内内存余弦相似度计算（论文 4.1 数据层约定），万级题库规模下可满足性能
        return pool.stream()
                .filter(q -> ownerId.equals(q.getUserId()))
                .map(q -> Map.entry(q, cosine(target, parseVector(q.getEmbedding()))))
                .filter(e -> e.getValue() > 0)
                .sorted(Map.Entry.<Question, Double>comparingByValue().reversed())
                .limit(topN)
                .map(Map.Entry::getKey)
                .collect(Collectors.toList());
    }

    private List<Double> parseVector(String embedding) {
        if (!StringUtils.hasText(embedding)) {
            return null;
        }
        try {
            return objectMapper.readValue(embedding, new TypeReference<>() {
            });
        } catch (Exception e) {
            log.warn("向量解析失败：{}", e.getMessage());
            return null;
        }
    }

    private double cosine(List<Double> a, List<Double> b) {
        if (a == null || b == null || a.size() != b.size()) {
            return 0;
        }
        double dot = 0, na = 0, nb = 0;
        for (int i = 0; i < a.size(); i++) {
            dot += a.get(i) * b.get(i);
            na += a.get(i) * a.get(i);
            nb += b.get(i) * b.get(i);
        }
        return (na == 0 || nb == 0) ? 0 : dot / (Math.sqrt(na) * Math.sqrt(nb));
    }
}
