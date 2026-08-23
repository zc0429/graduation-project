package com.example.wrongbook.service.impl;

import com.example.wrongbook.config.LlmProperties;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.content;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.header;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class OpenAiCompatibleLlmClientTests {

    @Test
    void parsesGlmChatResponseAndSendsJsonMode() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        OpenAiCompatibleLlmClient client = new OpenAiCompatibleLlmClient(
                builder, glmProperties());
        server.expect(requestTo("https://open.bigmodel.cn/api/paas/v4/chat/completions"))
                .andExpect(method(HttpMethod.POST))
                .andExpect(header("Authorization", "Bearer test-api-key"))
                .andExpect(content().json("""
                        {
                          "model": "glm-4.7-flash",
                          "thinking": {"type": "disabled"},
                          "response_format": {"type": "json_object"},
                          "stream": false
                        }
                        """))
                .andRespond(withSuccess("""
                        {"model":"glm-4.7-flash","choices":[{"message":{"content":"{\\"analysis\\":\\"ok\\"}"}}]}
                        """, MediaType.APPLICATION_JSON));

        assertThat(client.chat("任务：错题解析")).isEqualTo("{\"analysis\":\"ok\"}");
        assertThat(client.model()).isEqualTo("glm-4.7-flash");
        server.verify();
    }

    @Test
    void parsesGlmEmbeddingResponseWithConfiguredDimensions() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        OpenAiCompatibleLlmClient client = new OpenAiCompatibleLlmClient(
                builder, glmProperties());
        server.expect(requestTo("https://open.bigmodel.cn/api/paas/v4/embeddings"))
                .andExpect(method(HttpMethod.POST))
                .andExpect(content().json("""
                        {"model":"embedding-3","input":"一元二次方程","dimensions":1024}
                        """))
                .andRespond(withSuccess("""
                        {"model":"embedding-3","data":[{"index":0,"embedding":[0.25,-0.5,0.75]}]}
                        """, MediaType.APPLICATION_JSON));

        assertThat(client.embed("一元二次方程")).containsExactly(0.25, -0.5, 0.75);
        assertThat(client.embeddingModelLabel()).isEqualTo("embedding-3-1024");
        server.verify();
    }

    @Test
    void deepseekUsesDeterministicLocalEmbeddingAndRealChatModelName() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        LlmProperties properties = new LlmProperties();
        properties.setProvider("deepseek");
        properties.setApiKey("test-api-key");
        OpenAiCompatibleLlmClient client = new OpenAiCompatibleLlmClient(builder, properties);
        server.expect(requestTo("https://api.deepseek.com/chat/completions"))
                .andExpect(method(HttpMethod.POST))
                .andExpect(content().json("""
                        {
                          "model":"deepseek-v4-flash",
                          "thinking":{"type":"disabled"},
                          "response_format":{"type":"json_object"}
                        }
                        """))
                .andRespond(withSuccess("""
                        {"model":"deepseek-v4-flash","choices":[{"message":{"content":"{\\"variants\\":[]}"}}]}
                        """, MediaType.APPLICATION_JSON));

        List<Double> first = client.embed("函数 单调性");
        List<Double> second = client.embed("函数 单调性");

        assertThat(client.chat("任务：变式题生成")).isEqualTo("{\"variants\":[]}");
        assertThat(first).hasSize(256).containsExactlyElementsOf(second);
        assertThat(first.stream().mapToDouble(v -> v * v).sum()).isCloseTo(1.0, within(1.0e-12));
        assertThat(client.embeddingModelLabel()).isEqualTo("local-char-ngram-256-v1");
        assertThat(client.model()).isEqualTo("deepseek-v4-flash");
        server.verify();
    }

    private LlmProperties glmProperties() {
        LlmProperties properties = new LlmProperties();
        properties.setProvider("glm");
        properties.setApiKey("test-api-key");
        return properties;
    }

    private static org.assertj.core.data.Offset<Double> within(double value) {
        return org.assertj.core.data.Offset.offset(value);
    }
}
