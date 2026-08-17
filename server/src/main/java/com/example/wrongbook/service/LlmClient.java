package com.example.wrongbook.service;

import java.util.List;

/**
 * 大模型网关（论文 5.3 类设计 (3)）：封装文本生成与 Embedding 两类接口，屏蔽模型提供方差异。
 * 当前为 Mock 实现；接入真实大模型时新增实现类并将 app.llm.provider 改为对应标识即可：
 * - OpenAiLlmClient（havingValue="openai"，兼容 DeepSeek 等 OpenAI 协议 API）
 * - DashScopeClient（havingValue="dashscope"，通义千问）
 */
public interface LlmClient {

    /** 文本生成：输入提示词，输出文本（结构化任务约定输出 JSON 字符串） */
    String chat(String prompt);

    /** 文本语义向量 */
    List<Double> embed(String text);

    /** 模型标识（写入 ai_analysis.llm_model 供追溯） */
    String model();
}
