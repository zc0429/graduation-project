package com.example.wrongbook.service;

import java.util.List;

/** 独立视觉模型客户端，不属于现有文本分析 LlmClient 主链。 */
public interface QuestionRecognitionClient {

    Extraction recognize(String imageDataUrl, List<String> subjectNames);

    record Extraction(String subjectName, String stem, String studentAnswer, String source) {
    }
}
