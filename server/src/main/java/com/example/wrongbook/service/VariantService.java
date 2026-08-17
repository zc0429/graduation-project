package com.example.wrongbook.service;

import com.example.wrongbook.entity.VariantQuestion;

import java.util.List;

/**
 * 变式题服务（论文 5.3 类设计 (5)）：以原题题干、答案与知识点为上下文，
 * 经 LlmClient 生成变式练习并保存
 */
public interface VariantService {

    /** 生成变式题（Mock 3 道，追加保存） */
    List<VariantQuestion> generate(Long questionId);

    /** 变式题列表 */
    List<VariantQuestion> list(Long questionId);
}
