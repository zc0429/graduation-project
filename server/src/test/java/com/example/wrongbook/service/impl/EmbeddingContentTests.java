package com.example.wrongbook.service.impl;

import com.example.wrongbook.service.LlmClient;
import org.junit.jupiter.api.Test;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;

class EmbeddingContentTests {
    @Test
    void normalizesRichTextBeforeCallingTheEmbeddingProvider() {
        LlmClient client = mock(LlmClient.class);
        new EmbeddingServiceImpl(client).embed("<p>求 x<sup>2</sup></p><p>0 &lt; x &lt; 3</p>");
        verify(client).embed("求 x^(2)\n0 < x < 3");
    }
}
