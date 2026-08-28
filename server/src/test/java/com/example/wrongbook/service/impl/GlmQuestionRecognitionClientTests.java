package com.example.wrongbook.service.impl;

import com.example.wrongbook.common.BizException;
import com.example.wrongbook.config.ImageRecognitionProperties;
import com.example.wrongbook.service.QuestionRecognitionClient;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;

import java.net.http.HttpTimeoutException;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.content;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.header;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withStatus;

class GlmQuestionRecognitionClientTests {

    private static final String IMAGE_DATA_URL = "data:image/png;base64,iVBORw0KGgo=";

    @Test
    void sendsVerifiedMultimodalFormatAndParsesStructuredResponse() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        GlmQuestionRecognitionClient client = client(builder);
        server.expect(requestTo("https://open.bigmodel.cn/api/paas/v4/chat/completions"))
                .andExpect(method(HttpMethod.POST))
                .andExpect(header("Authorization", "Bearer test-image-key"))
                .andExpect(content().json("""
                        {
                          "model":"glm-5.3-flash",
                          "thinking":{"type":"enabled"},
                          "reasoning_effort":"low",
                          "response_format":{"type":"json_object"},
                          "max_tokens":2048,
                          "stream":false
                        }
                        """))
                .andExpect(content().string(org.hamcrest.Matchers.containsString(IMAGE_DATA_URL)))
                .andExpect(content().string(org.hamcrest.Matchers.containsString("数学")))
                .andExpect(content().string(org.hamcrest.Matchers.containsString("物理")))
                .andRespond(withSuccess(response("""
                        {"subjectName":"数学","stem":"求方程 x²-5x+6=0 的解。","studentAnswer":"x=3","source":"课堂练习"}
                        """), MediaType.APPLICATION_JSON));

        QuestionRecognitionClient.Extraction result = client.recognize(
                IMAGE_DATA_URL, List.of("数学", "物理"));

        assertThat(result.subjectName()).isEqualTo("数学");
        assertThat(result.stem()).isEqualTo("求方程 x²-5x+6=0 的解。");
        assertThat(result.studentAnswer()).isEqualTo("x=3");
        assertThat(result.source()).isEqualTo("课堂练习");
        server.verify();
    }

    @Test
    void rejectsMissingResponseField() {
        assertMalformed("""
                {"subjectName":"数学","stem":"一道题","studentAnswer":""}
                """);
    }

    @Test
    void rejectsNonJsonContent() {
        assertMalformed("这不是 JSON");
    }

    @Test
    void rejectsEmptyStem() {
        assertMalformed("""
                {"subjectName":"数学","stem":"  ","studentAnswer":"","source":""}
                """);
    }

    @Test
    void mapsNetworkTimeoutToStableBusinessError() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        GlmQuestionRecognitionClient client = client(builder);
        server.expect(requestTo("https://open.bigmodel.cn/api/paas/v4/chat/completions"))
                .andRespond(request -> {
                    throw new ResourceAccessException("read timeout", new HttpTimeoutException("cancelled"));
                });

        assertThatThrownBy(() -> client.recognize(IMAGE_DATA_URL, List.of("数学")))
                .isInstanceOf(BizException.class)
                .hasMessageContaining("超时或网络不可用");
        server.verify();
    }

    @Test
    void mapsRateLimitAndServerFailureWithoutLeakingUpstreamBody() {
        RestClient.Builder rateLimitBuilder = RestClient.builder();
        MockRestServiceServer rateLimitServer = MockRestServiceServer.bindTo(rateLimitBuilder).build();
        GlmQuestionRecognitionClient rateLimitClient = client(rateLimitBuilder);
        rateLimitServer.expect(requestTo("https://open.bigmodel.cn/api/paas/v4/chat/completions"))
                .andRespond(withStatus(HttpStatus.TOO_MANY_REQUESTS)
                        .contentType(MediaType.APPLICATION_JSON)
                        .body("{\"error\":{\"message\":\"sensitive upstream detail\"}}"));

        assertThatThrownBy(() -> rateLimitClient.recognize(IMAGE_DATA_URL, List.of("数学")))
                .isInstanceOf(BizException.class)
                .hasMessage("图片识别服务繁忙，请稍后重试");

        RestClient.Builder serverErrorBuilder = RestClient.builder();
        MockRestServiceServer serverErrorServer = MockRestServiceServer.bindTo(serverErrorBuilder).build();
        GlmQuestionRecognitionClient serverErrorClient = client(serverErrorBuilder);
        serverErrorServer.expect(requestTo("https://open.bigmodel.cn/api/paas/v4/chat/completions"))
                .andRespond(withStatus(HttpStatus.BAD_GATEWAY));

        assertThatThrownBy(() -> serverErrorClient.recognize(IMAGE_DATA_URL, List.of("数学")))
                .isInstanceOf(BizException.class)
                .hasMessage("图片识别服务暂时不可用，请稍后重试");
        rateLimitServer.verify();
        serverErrorServer.verify();
    }

    private void assertMalformed(String content) {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        GlmQuestionRecognitionClient client = client(builder);
        server.expect(requestTo("https://open.bigmodel.cn/api/paas/v4/chat/completions"))
                .andRespond(withSuccess(response(content), MediaType.APPLICATION_JSON));

        assertThatThrownBy(() -> client.recognize(IMAGE_DATA_URL, List.of("数学")))
                .isInstanceOf(BizException.class)
                .hasMessage("图片识别结果格式异常，请重试或手工录入");
        server.verify();
    }

    private GlmQuestionRecognitionClient client(RestClient.Builder builder) {
        ImageRecognitionProperties properties = new ImageRecognitionProperties();
        properties.setEnabled(true);
        properties.setApiKey("test-image-key");
        return new GlmQuestionRecognitionClient(builder, new ObjectMapper(), properties);
    }

    private String response(String content) {
        try {
            String encoded = new ObjectMapper().writeValueAsString(content);
            return "{\"model\":\"glm-5.3-flash\",\"choices\":[{\"message\":{\"content\":"
                    + encoded + "}}]}";
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }
}
