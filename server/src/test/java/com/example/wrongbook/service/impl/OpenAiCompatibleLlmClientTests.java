package com.example.wrongbook.service.impl;

import com.example.wrongbook.config.LlmProperties;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.HttpStatus;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;

import java.net.http.HttpTimeoutException;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.content;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.header;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withStatus;

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
                          "max_tokens": 4096,
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
                .andRespond(withSuccess(embeddingResponse(1024, "0.25", "-0.5", "0.75"),
                        MediaType.APPLICATION_JSON));

        assertThat(client.embed("一元二次方程"))
                .hasSize(1024)
                .startsWith(0.25, -0.5, 0.75);
        assertThat(client.embeddingModelLabel()).isEqualTo("embedding-3-1024");
        server.verify();
    }

    @Test
    void rejectsUnexpectedEmbeddingDimensions() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        OpenAiCompatibleLlmClient client = new OpenAiCompatibleLlmClient(builder, glmProperties());
        server.expect(requestTo("https://open.bigmodel.cn/api/paas/v4/embeddings"))
                .andRespond(withSuccess("""
                        {"model":"embedding-3","data":[{"index":0,"embedding":[0.25,-0.5,0.75]}]}
                        """, MediaType.APPLICATION_JSON));

        assertThatThrownBy(() -> client.embed("维度校验"))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("expected=1024")
                .hasMessageContaining("actual=3");
        server.verify();
    }

    @Test
    void rejectsNonFiniteEmbeddingValues() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        OpenAiCompatibleLlmClient client = new OpenAiCompatibleLlmClient(builder, glmProperties());
        server.expect(requestTo("https://open.bigmodel.cn/api/paas/v4/embeddings"))
                .andRespond(withSuccess(embeddingResponse(1024, "1e309"), MediaType.APPLICATION_JSON));

        assertThatThrownBy(() -> client.embed("有限数校验"))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("NaN 或 Infinity");
        server.verify();
    }

    @Test
    void retriesOneTransientServerFailure() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        OpenAiCompatibleLlmClient client = new OpenAiCompatibleLlmClient(builder, glmProperties());
        server.expect(requestTo("https://open.bigmodel.cn/api/paas/v4/chat/completions"))
                .andRespond(withStatus(HttpStatus.SERVICE_UNAVAILABLE));
        server.expect(requestTo("https://open.bigmodel.cn/api/paas/v4/chat/completions"))
                .andRespond(withSuccess("""
                        {"model":"glm-4.7-flash","choices":[{"message":{"content":"{\\"status\\":\\"ok\\"}"}}]}
                        """, MediaType.APPLICATION_JSON));

        assertThat(client.chat("瞬时失败重试验证")).isEqualTo("{\"status\":\"ok\"}");
        server.verify();
    }

    @Test
    void doesNotReplayChatAfterReadTimeout() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        OpenAiCompatibleLlmClient client = new OpenAiCompatibleLlmClient(builder, glmProperties());
        server.expect(requestTo("https://open.bigmodel.cn/api/paas/v4/chat/completions"))
                .andRespond(request -> {
                    throw new ResourceAccessException(
                            "read timeout", new HttpTimeoutException("request cancelled"));
                });

        assertThatThrownBy(() -> client.chat("读取超时不重放验证"))
                .isInstanceOf(ResourceAccessException.class);
        server.verify();
    }

    @Test
    void doesNotImmediatelyRetryUserRateLimit() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        OpenAiCompatibleLlmClient client = new OpenAiCompatibleLlmClient(builder, glmProperties());
        server.expect(requestTo("https://open.bigmodel.cn/api/paas/v4/chat/completions"))
                .andRespond(withStatus(HttpStatus.TOO_MANY_REQUESTS)
                        .contentType(MediaType.APPLICATION_JSON)
                        .body("{\"error\":{\"code\":\"1302\",\"message\":\"rate limited\"}}"));

        assertThatThrownBy(() -> client.chat("用户级限流不立即重试验证"))
                .isInstanceOf(HttpClientErrorException.TooManyRequests.class);
        server.verify();
    }

    @Test
    void doesNotRetryNonOverloadRateLimit() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        OpenAiCompatibleLlmClient client = new OpenAiCompatibleLlmClient(builder, glmProperties());
        server.expect(requestTo("https://open.bigmodel.cn/api/paas/v4/chat/completions"))
                .andRespond(withStatus(HttpStatus.TOO_MANY_REQUESTS)
                        .contentType(MediaType.APPLICATION_JSON)
                        .body("{\"error\":{\"code\":\"1308\",\"message\":\"usage limit\"}}"));

        assertThatThrownBy(() -> client.chat("额度类限流不重试验证"))
                .isInstanceOf(HttpClientErrorException.TooManyRequests.class);
        server.verify();
    }

    @Test
    void retriesOnePlatformOverload() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        OpenAiCompatibleLlmClient client = new OpenAiCompatibleLlmClient(builder, glmProperties());
        server.expect(requestTo("https://open.bigmodel.cn/api/paas/v4/chat/completions"))
                .andRespond(withStatus(HttpStatus.TOO_MANY_REQUESTS)
                        .contentType(MediaType.APPLICATION_JSON)
                        .body("{\"error\":{\"code\":\"1305\",\"message\":\"overloaded\"}}"));
        server.expect(requestTo("https://open.bigmodel.cn/api/paas/v4/chat/completions"))
                .andRespond(withSuccess("""
                        {"model":"glm-4.7-flash","choices":[{"message":{"content":"{\\"status\\":\\"ok\\"}"}}]}
                        """, MediaType.APPLICATION_JSON));

        assertThat(client.chat("平台过载重试验证")).isEqualTo("{\"status\":\"ok\"}");
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
                          "response_format":{"type":"json_object"},
                          "max_tokens":4096
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

    @Test
    void defaultGlmUsesRequiredThinkingParametersWithoutChangingEmbeddingSpace() {
        LlmProperties properties = new LlmProperties();
        properties.setApiKey("test-api-key");
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        OpenAiCompatibleLlmClient client = new OpenAiCompatibleLlmClient(builder, properties);
        server.expect(requestTo("https://open.bigmodel.cn/api/paas/v4/chat/completions"))
                .andExpect(content().json("""
                        {"model":"glm-5.3-flash","thinking":{"type":"enabled"},"reasoning_effort":"low",
                         "response_format":{"type":"json_object"},"stream":false}
                        """))
                .andRespond(withSuccess("""
                        {"model":"glm-5.3-flash","choices":[{"message":{"content":"{}"}}]}
                        """, MediaType.APPLICATION_JSON));
        assertThat(client.chat("配置验证")).isEqualTo("{}");
        assertThat(client.embeddingModelLabel()).isEqualTo("embedding-3-1024");
        server.verify();
    }

    @Test
    void absentKeyDoesNotStopManualInputButRefusesAiWithoutNetworkOrMockFallback() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        OpenAiCompatibleLlmClient client = new OpenAiCompatibleLlmClient(builder, new LlmProperties());
        assertThatThrownBy(client::verifyReady).hasMessageContaining("LLM_API_KEY");
        assertThatThrownBy(() -> client.chat("题目")).hasMessageContaining("LLM_API_KEY");
        assertThatThrownBy(() -> client.embed("题目")).hasMessageContaining("LLM_API_KEY");
        assertThat(client.model()).isEqualTo("glm-5.3-flash");
        server.verify();
    }

    private LlmProperties glmProperties() {
        LlmProperties properties = new LlmProperties();
        properties.setProvider("glm");
        properties.setChatModel("glm-4.7-flash");
        properties.setApiKey("test-api-key");
        return properties;
    }

    private String embeddingResponse(int size, String... leadingValues) {
        String vector = IntStream.range(0, size)
                .mapToObj(index -> index < leadingValues.length ? leadingValues[index] : "0.0")
                .collect(Collectors.joining(","));
        return "{\"model\":\"embedding-3\",\"data\":[{\"index\":0,\"embedding\":["
                + vector + "]}]}";
    }

    private static org.assertj.core.data.Offset<Double> within(double value) {
        return org.assertj.core.data.Offset.offset(value);
    }
}
