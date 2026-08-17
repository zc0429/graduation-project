package com.example.wrongbook.service;

import com.example.wrongbook.entity.AiAnalysis;

/**
 * AI 解析服务（论文 5.3 类设计 (2)）：错题解析流程编排——
 * 向量计算 → RAG 检索参考题 → 组装提示词 → LlmClient 生成 → 结构化解析入库并回填错题
 */
public interface AiAnalysisService {

    /** 触发异步解析（立即返回；重复触发时若正在生成中则忽略） */
    void trigger(Long questionId);

    /** 查询解析结果（学生仅本人错题） */
    AiAnalysis getByQuestion(Long questionId);
}
