package com.example.wrongbook.service;

import java.util.List;

/**
 * 文本向量服务（论文 5.3 中 AiAnalysisService 依赖的独立服务类）：
 * 封装题干语义向量的计算，供 RAG 检索与相似题推荐复用
 */
public interface EmbeddingService {

    /** 计算文本语义向量 */
    List<Double> embed(String text);
}
