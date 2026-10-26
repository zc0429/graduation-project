package com.example.wrongbook.service;

import java.util.List;

/**
 * 大模型网关（论文 5.3 类设计 (3)）：封装文本生成与 Embedding 两类接口，屏蔽模型提供方差异。
 * 可通过 app.llm.provider 在 Mock、智谱 GLM 与 DeepSeek（OpenAI 兼容协议）之间切换。
 */
public interface LlmClient {

    /** Fail before enqueueing work when the real provider has no credential. */
    default void verifyReady() {
    }

    /** 文本生成：输入提示词，输出文本（结构化任务约定输出 JSON 字符串） */
    String chat(String prompt);

    /** 文本语义向量 */
    List<Double> embed(String text);

    /** 模型标识（写入 ai_analysis.llm_model 供追溯） */
    String model();
}
