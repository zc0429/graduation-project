package com.example.wrongbook.service;

import com.example.wrongbook.entity.Question;

import java.util.List;

/**
 * 检索增强服务（论文 5.3 类设计 (4)）：基于题目向量做余弦相似度检索，
 * 返回同科目相似题作为解析生成的参考依据
 */
public interface RagService {

    /**
     * 检索同科目相似参考题
     *
     * @param question 目标错题（需已计算 embedding）
     * @param topN     返回条数
     */
    List<Question> retrieveSimilar(Question question, int topN);
}
