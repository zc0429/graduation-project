package com.example.wrongbook.service.impl;

import com.example.wrongbook.service.EmbeddingService;
import com.example.wrongbook.service.LlmClient;
import com.example.wrongbook.util.QuestionContent;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class EmbeddingServiceImpl implements EmbeddingService {

    private final LlmClient llmClient;

    @Override
    public List<Double> embed(String text) {
        return llmClient.embed(QuestionContent.plainText(text));
    }
}
