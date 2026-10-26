package com.example.wrongbook.service.impl;

import com.example.wrongbook.config.LlmProperties;
import com.example.wrongbook.common.BizException;
import com.example.wrongbook.service.LlmClient;
import com.fasterxml.jackson.databind.JsonNode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnExpression;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import java.net.ConnectException;
import java.net.UnknownHostException;
import java.net.http.HttpConnectTimeoutException;
import java.net.http.HttpTimeoutException;
import java.text.Normalizer;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Pattern;

/** 智谱 GLM 与 DeepSeek 共用的 OpenAI-compatible HTTP 客户端。 */
@Slf4j
@Component
@ConditionalOnExpression("'${app.llm.provider:glm}' == 'glm' or '${app.llm.provider:glm}' == 'deepseek'")
public class OpenAiCompatibleLlmClient implements LlmClient {

    static final String GLM_DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4";
    static final String GLM_DEFAULT_CHAT_MODEL = "glm-5.3-flash";
    static final String GLM_DEFAULT_EMBEDDING_MODEL = "embedding-3";
    static final String DEEPSEEK_DEFAULT_BASE_URL = "https://api.deepseek.com";
    static final String DEEPSEEK_DEFAULT_CHAT_MODEL = "deepseek-v4-flash";
    static final String LOCAL_EMBEDDING_MODEL = "local-char-ngram-256-v1";

    private static final int LOCAL_EMBEDDING_DIMENSIONS = 256;
    private static final int CHAT_MAX_TOKENS = 4096;
    private static final int FNV_OFFSET_BASIS = 0x811c9dc5;
    private static final int FNV_PRIME = 0x01000193;
    private static final int MAX_HTTP_ATTEMPTS = 3;
    private static final long TRANSIENT_RETRY_DELAY_MILLIS = 500;
    private static final long RATE_LIMIT_RETRY_DELAY_MILLIS = 15000;
    private static final Pattern PLATFORM_OVERLOAD_CODE = Pattern.compile(
            "\\\"code\\\"\\s*:\\s*(?:\\\"1305\\\"|1305)(?!\\d)");

    private final RestClient restClient;
    private final boolean credentialConfigured;
    private final String provider;
    private final String baseUrl;
    private final String chatModel;
    private final String embeddingModel;
    private final int embeddingDimensions;

    public OpenAiCompatibleLlmClient(RestClient.Builder restClientBuilder, LlmProperties properties) {
        this.provider = requireProvider(properties.getProvider());
        this.baseUrl = stripTrailingSlash(defaultIfBlank(properties.getBaseUrl(),
                isGlm() ? GLM_DEFAULT_BASE_URL : DEEPSEEK_DEFAULT_BASE_URL));
        this.chatModel = defaultIfBlank(properties.getChatModel(),
                isGlm() ? GLM_DEFAULT_CHAT_MODEL : DEEPSEEK_DEFAULT_CHAT_MODEL);
        this.embeddingModel = isGlm()
                ? defaultIfBlank(properties.getEmbeddingModel(), GLM_DEFAULT_EMBEDDING_MODEL)
                : LOCAL_EMBEDDING_MODEL;
        this.embeddingDimensions = isGlm()
                ? requireEmbeddingDimensions(properties.getEmbeddingDimensions())
                : LOCAL_EMBEDDING_DIMENSIONS;
        this.credentialConfigured = StringUtils.hasText(properties.getApiKey());
        if (credentialConfigured) {
            restClientBuilder.defaultHeader("Authorization", "Bearer " + properties.getApiKey().trim());
        }
        this.restClient = restClientBuilder
                .defaultHeader("Content-Type", MediaType.APPLICATION_JSON_VALUE)
                .build();
        log.info("LLM provider={}，chatModel={}，embeddingModel={}",
                provider, chatModel, embeddingModelLabel());
    }

    @Override
    public void verifyReady() {
        if (!credentialConfigured) {
            throw new BizException("未配置 LLM_API_KEY，真实 AI 服务不可用；可手工录入，或显式配置 Mock 离线模式");
        }
    }

    @Override
    public String chat(String prompt) {
        verifyReady();
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("model", chatModel);
        body.put("messages", List.of(
                Map.of("role", "system", "content", "你是错题分析助手。严格按用户要求输出一个 JSON 对象，不要输出 Markdown。"),
                Map.of("role", "user", "content", prompt)));
        if (isGlm() && "glm-5.3-flash".equalsIgnoreCase(chatModel)) {
            // Existing image Spike verified this model does not accept disabled thinking.
            body.put("thinking", Map.of("type", "enabled"));
            body.put("reasoning_effort", "low");
        } else {
            body.put("thinking", Map.of("type", "disabled"));
        }
        body.put("response_format", Map.of("type", "json_object"));
        body.put("temperature", 0.2);
        body.put("max_tokens", CHAT_MAX_TOKENS);
        body.put("stream", false);

        JsonNode response = post("/chat/completions", body);
        requireResponseModel(response, chatModel, "Chat");
        JsonNode content = response.path("choices").path(0).path("message").path("content");
        if (!content.isTextual() || !StringUtils.hasText(content.asText())) {
            throw new IllegalStateException("大模型响应缺少 choices[0].message.content");
        }
        return content.asText();
    }

    @Override
    public List<Double> embed(String text) {
        verifyReady();
        if (!isGlm()) {
            return localEmbedding(text);
        }
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("model", embeddingModel);
        body.put("input", text);
        if (GLM_DEFAULT_EMBEDDING_MODEL.equalsIgnoreCase(embeddingModel)) {
            body.put("dimensions", embeddingDimensions);
        }
        JsonNode response = post("/embeddings", body);
        requireResponseModel(response, embeddingModel, "Embedding");
        JsonNode embedding = response.path("data").path(0).path("embedding");
        if (!embedding.isArray() || embedding.isEmpty()) {
            throw new IllegalStateException("Embedding 响应缺少 data[0].embedding");
        }
        List<Double> vector = new ArrayList<>(embedding.size());
        embedding.forEach(value -> {
            if (!value.isNumber()) {
                throw new IllegalStateException("Embedding 响应包含非数值元素");
            }
            double number = value.asDouble();
            if (!Double.isFinite(number)) {
                throw new IllegalStateException("Embedding 响应包含 NaN 或 Infinity");
            }
            vector.add(number);
        });
        if (vector.size() != embeddingDimensions) {
            throw new IllegalStateException("Embedding 响应维度不符：expected="
                    + embeddingDimensions + "，actual=" + vector.size());
        }
        return vector;
    }

    @Override
    public String model() {
        return chatModel;
    }

    String embeddingModelLabel() {
        return isGlm() ? embeddingModel + "-" + embeddingDimensions : embeddingModel;
    }

    private JsonNode post(String path, Map<String, Object> body) {
        for (int attempt = 1; attempt <= MAX_HTTP_ATTEMPTS; attempt++) {
            try {
                JsonNode response = restClient.post()
                        .uri(baseUrl + path)
                        .contentType(MediaType.APPLICATION_JSON)
                        .body(body)
                        .retrieve()
                        .body(JsonNode.class);
                if (response == null) {
                    throw new IllegalStateException("大模型接口返回空响应");
                }
                return response;
            } catch (RestClientException e) {
                if (attempt == MAX_HTTP_ATTEMPTS || !isTransient(e)) {
                    throw e;
                }
                long retryDelay = retryDelayMillis(e, attempt);
                log.warn("大模型请求第 {} 次失败，将在 {}ms 后重试，path={}，errorType={}",
                        attempt, retryDelay, path, e.getClass().getSimpleName());
                waitBeforeRetry(retryDelay);
            }
        }
        throw new IllegalStateException("大模型请求未执行");
    }

    private boolean isTransient(RestClientException exception) {
        if (exception instanceof ResourceAccessException) {
            return isConnectionFailure(exception);
        }
        if (exception instanceof HttpClientErrorException.TooManyRequests rateLimit) {
            return PLATFORM_OVERLOAD_CODE.matcher(rateLimit.getResponseBodyAsString()).find();
        }
        return exception instanceof HttpServerErrorException;
    }

    private boolean isConnectionFailure(Throwable failure) {
        Throwable current = failure;
        while (current != null) {
            if (current instanceof HttpConnectTimeoutException
                    || current instanceof ConnectException
                    || current instanceof UnknownHostException) {
                return true;
            }
            if (current instanceof HttpTimeoutException) {
                return false;
            }
            if (current.getCause() == current) {
                break;
            }
            current = current.getCause();
        }
        return false;
    }

    private long retryDelayMillis(RestClientException exception, int failedAttempt) {
        long baseDelay = exception instanceof HttpClientErrorException.TooManyRequests
                ? RATE_LIMIT_RETRY_DELAY_MILLIS
                : TRANSIENT_RETRY_DELAY_MILLIS;
        return baseDelay * failedAttempt;
    }

    private void waitBeforeRetry(long retryDelayMillis) {
        try {
            Thread.sleep(retryDelayMillis);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("大模型请求重试等待被中断", e);
        }
    }

    private void requireResponseModel(JsonNode response, String expectedModel, String responseType) {
        JsonNode model = response.path("model");
        if (!model.isTextual() || !StringUtils.hasText(model.asText())) {
            throw new IllegalStateException(responseType + " 响应缺少 model");
        }
        if (!expectedModel.equalsIgnoreCase(model.asText().trim())) {
            throw new IllegalStateException(responseType + " 响应模型不符：expected="
                    + expectedModel + "，actual=" + model.asText().trim());
        }
    }

    /** DeepSeek 无官方 Embedding API 时使用的确定性本地字符 unigram/bigram 特征哈希。 */
    private List<Double> localEmbedding(String text) {
        String normalized = Normalizer.normalize(text == null ? "" : text, Normalizer.Form.NFKC)
                .toLowerCase(Locale.ROOT);
        double[] vector = new double[LOCAL_EMBEDDING_DIMENSIONS];
        int[] codePoints = normalized.codePoints().toArray();
        for (int i = 0; i < codePoints.length; i++) {
            addFeature(vector, codePoints[i]);
            if (i + 1 < codePoints.length) {
                addFeature(vector, 31 * codePoints[i] + codePoints[i + 1]);
            }
        }
        double norm = 0;
        for (double value : vector) {
            norm += value * value;
        }
        norm = Math.sqrt(norm);
        List<Double> result = new ArrayList<>(LOCAL_EMBEDDING_DIMENSIONS);
        for (double value : vector) {
            result.add(norm == 0 ? 0.0 : value / norm);
        }
        return result;
    }

    private void addFeature(double[] vector, int feature) {
        int hash = (FNV_OFFSET_BASIS ^ feature) * FNV_PRIME;
        int index = Math.floorMod(hash, vector.length);
        vector[index] += (hash & 0x80000000) == 0 ? 1.0 : -1.0;
    }

    private boolean isGlm() {
        return "glm".equals(provider);
    }

    private String requireProvider(String value) {
        String normalized = defaultIfBlank(value, "mock").toLowerCase(Locale.ROOT);
        if (!"glm".equals(normalized) && !"deepseek".equals(normalized)) {
            throw new IllegalArgumentException("OpenAI-compatible 客户端仅支持 glm 或 deepseek");
        }
        return normalized;
    }

    private int requireEmbeddingDimensions(int value) {
        if (value != 256 && value != 512 && value != 1024 && value != 2048) {
            throw new IllegalArgumentException("LLM_EMBEDDING_DIMENSIONS 仅支持 256/512/1024/2048");
        }
        return value;
    }

    private String defaultIfBlank(String value, String fallback) {
        return StringUtils.hasText(value) ? value.trim() : fallback;
    }

    private String requireText(String value, String environmentName) {
        if (!StringUtils.hasText(value)) {
            throw new IllegalStateException("启用真实大模型时必须设置 " + environmentName);
        }
        return value.trim();
    }

    private String stripTrailingSlash(String value) {
        return value.endsWith("/") ? value.substring(0, value.length() - 1) : value;
    }
}
