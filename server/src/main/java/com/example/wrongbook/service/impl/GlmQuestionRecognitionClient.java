package com.example.wrongbook.service.impl;

import com.example.wrongbook.common.BizException;
import com.example.wrongbook.config.ImageRecognitionProperties;
import com.example.wrongbook.service.QuestionRecognitionClient;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

@Slf4j
@Component
@ConditionalOnProperty(prefix = "app.image-recognition", name = "enabled", havingValue = "true")
public class GlmQuestionRecognitionClient implements QuestionRecognitionClient {

    private static final Set<String> REQUIRED_FIELDS = Set.of(
            "subjectName", "stem", "studentAnswer", "source");
    private static final int MAX_STEM_LENGTH = 2000;
    private static final int MAX_ANSWER_LENGTH = 2000;
    private static final int MAX_SOURCE_LENGTH = 100;

    private final RestClient restClient;
    private final boolean credentialConfigured;
    private final ObjectMapper objectMapper;
    private final String endpoint;
    private final String model;

    public GlmQuestionRecognitionClient(RestClient.Builder restClientBuilder,
                                        ObjectMapper objectMapper,
                                        ImageRecognitionProperties properties) {
        this.objectMapper = objectMapper;
        this.model = requireText(properties.getModel(), "IMAGE_RECOGNITION_MODEL");
        this.endpoint = stripTrailingSlash(requireText(
                properties.getBaseUrl(), "IMAGE_RECOGNITION_BASE_URL")) + "/chat/completions";
        this.credentialConfigured = StringUtils.hasText(properties.getApiKey());
        if (credentialConfigured) {
            restClientBuilder.defaultHeader("Authorization", "Bearer " + properties.getApiKey().trim());
        }
        this.restClient = restClientBuilder
                .defaultHeader("Content-Type", MediaType.APPLICATION_JSON_VALUE)
                .build();
        log.info("图片识别客户端已启用，model={}", model);
    }

    @Override
    public Extraction recognize(String imageDataUrl, List<String> subjectNames) {
        if (!credentialConfigured) {
            throw new BizException("图片识别未配置 IMAGE_RECOGNITION_API_KEY 或 LLM_API_KEY，请手工录入或联系管理员配置");
        }
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("model", model);
        body.put("messages", List.of(
                Map.of("role", "system", "content", systemPrompt(subjectNames)),
                Map.of("role", "user", "content", List.of(
                        Map.of("type", "text", "text",
                                "提取图片中的一道题，并严格返回指定 JSON。看不清的字段填写空字符串或 null。"),
                        Map.of("type", "image_url", "image_url", Map.of("url", imageDataUrl))))));
        // 真实 Spike 证实 glm-5.3-flash 强制思考，disabled 会返回 1210；使用最低可用强度。
        body.put("thinking", Map.of("type", "enabled"));
        body.put("reasoning_effort", "low");
        body.put("response_format", Map.of("type", "json_object"));
        body.put("max_tokens", 2048);
        body.put("stream", false);

        try {
            JsonNode response = restClient.post()
                    .uri(endpoint)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(body)
                    .retrieve()
                    .body(JsonNode.class);
            return parseResponse(response);
        } catch (BizException e) {
            throw e;
        } catch (ResourceAccessException e) {
            throw new BizException("图片识别请求超时或网络不可用，请稍后重试");
        } catch (HttpClientErrorException.Unauthorized | HttpClientErrorException.Forbidden e) {
            throw new BizException("图片识别服务鉴权失败，请联系管理员检查密钥与模型权限");
        } catch (HttpClientErrorException.TooManyRequests e) {
            throw new BizException("图片识别服务繁忙，请稍后重试");
        } catch (HttpServerErrorException e) {
            throw new BizException("图片识别服务暂时不可用，请稍后重试");
        } catch (RestClientException e) {
            throw new BizException("图片识别请求失败，请稍后重试");
        }
    }

    private Extraction parseResponse(JsonNode response) {
        if (response == null) {
            throw malformed("接口返回空响应");
        }
        JsonNode responseModel = response.path("model");
        if (!responseModel.isTextual() || !model.equalsIgnoreCase(responseModel.asText().trim())) {
            throw malformed("响应模型不符");
        }
        JsonNode content = response.path("choices").path(0).path("message").path("content");
        if (!content.isTextual() || !StringUtils.hasText(content.asText())) {
            throw malformed("响应内容为空");
        }

        JsonNode result;
        try {
            result = objectMapper.readTree(content.asText());
        } catch (JsonProcessingException e) {
            throw malformed("响应不是合法 JSON");
        }
        if (!result.isObject()) {
            throw malformed("JSON 顶层不是对象");
        }
        Set<String> actualFields = new LinkedHashSet<>();
        result.fieldNames().forEachRemaining(actualFields::add);
        if (!actualFields.equals(REQUIRED_FIELDS)) {
            throw malformed("JSON 字段不完整或包含未知字段");
        }

        String subjectName = nullableText(result.get("subjectName"), "subjectName", 50, true);
        String stem = nullableText(result.get("stem"), "stem", MAX_STEM_LENGTH, false);
        String studentAnswer = nullableText(result.get("studentAnswer"), "studentAnswer", MAX_ANSWER_LENGTH, true);
        String source = nullableText(result.get("source"), "source", MAX_SOURCE_LENGTH, true);
        return new Extraction(subjectName, stem, studentAnswer, source);
    }

    private String nullableText(JsonNode value, String field, int maxLength, boolean emptyAllowed) {
        if (value == null || value.isNull()) {
            if (emptyAllowed) {
                return null;
            }
            throw malformed(field + " 不能为空");
        }
        if (!value.isTextual()) {
            throw malformed(field + " 必须是字符串或 null");
        }
        String text = value.asText().trim();
        if (!emptyAllowed && !StringUtils.hasText(text)) {
            throw malformed(field + " 不能为空");
        }
        if (text.length() > maxLength) {
            throw malformed(field + " 超出长度限制");
        }
        return StringUtils.hasText(text) ? text : null;
    }

    private BizException malformed(String detail) {
        log.warn("图片识别响应结构异常：{}", detail);
        return new BizException("图片识别结果格式异常，请重试或手工录入");
    }

    private String systemPrompt(List<String> subjectNames) {
        String candidates = subjectNames.stream().map(name -> "- " + name).reduce((a, b) -> a + "\n" + b).orElse("（无）");
        return """
                你是“错题图片信息提取器”，不是解题助手。
                仅提取图片中真实可见的一道题，不解题，不生成正确答案，不修改学生作答，
                不根据常识补全看不清的内容。看不清或图片中未出现的字段返回空字符串或 null。
                studentAnswer 只表示图片中学生实际写下、勾选或圈出的答案；不能把推理出的答案填入该字段。
                subjectName 只能从下列候选科目中原样选择一个，无法可靠判断则留空：
                %s
                stem 必须包含图片中可见的完整题干、条件、选项和问题。
                source 只在图片明确出现试卷名、作业来源等信息时提取。
                只输出一个 JSON 对象，不输出 Markdown 或其他文字，字段必须且只能是：
                {"subjectName":"","stem":"","studentAnswer":"","source":""}
                """.formatted(candidates);
    }

    private String requireText(String value, String environmentName) {
        if (!StringUtils.hasText(value)) {
            throw new IllegalStateException("启用图片识别时必须设置 " + environmentName);
        }
        return value.trim();
    }

    private String stripTrailingSlash(String value) {
        return value.endsWith("/") ? value.substring(0, value.length() - 1) : value;
    }
}
