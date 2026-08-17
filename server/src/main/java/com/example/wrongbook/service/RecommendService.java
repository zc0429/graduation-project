package com.example.wrongbook.service;

import com.example.wrongbook.entity.Question;

import java.util.List;

/**
 * 相似题推荐服务：推荐同知识点、相近难度的题目（top-5）
 */
public interface RecommendService {

    List<Question> similar(Long questionId);
}
