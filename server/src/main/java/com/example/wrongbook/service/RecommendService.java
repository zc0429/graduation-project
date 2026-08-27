package com.example.wrongbook.service;

import com.example.wrongbook.entity.Question;

import java.util.List;

/**
 * 相似题推荐服务：同用户候选中，同知识点、相近难度优先，语义向量结果补足，最终返回 top-5
 */
public interface RecommendService {

    List<Question> similar(Long questionId);
}
