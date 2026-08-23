package com.example.wrongbook.service.impl;

import com.example.wrongbook.config.LlmProperties;
import com.example.wrongbook.service.LlmClient;
import com.fasterxml.jackson.databind.JsonNode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnExpression;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.client.RestClient;

import java.text.Normalizer;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/** 智谱 GLM 与 DeepSeek 共用的 OpenAI-compatible HTTP 客户端。 */
@Slf4j
@Component
@ConditionalOnExpression("'${app.llm.provider:mock}' == 'glm' or '${app.llm.provider:mock}' == 'deepseek'")
public class OpenAiCompatibleLlmClient implements LlmClient {

    static final String GLM_DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4";
    static final String GLM_DEFAULT_CHAT_MODEL = "glm-4.7-flash";
    static final String GLM_DEFAULT_EMBEDDING_MODEL = "embedding-3";
    static final String DEEPSEEK_DEFAULT_BASE_URL = "https://api.deepseek.com";
    static final String DEEPSEEK_DEFAULT_CHAT_MODEL = "deepseek-v4-flash";
    static final String LOCAL_EMBEDDING_MODEL = "local-char-ngram-256-v1";

    private static final int LOCAL_EMBEDDING_DIMENSIONS = 256;
    private static final int FNV_OFFSET_BASIS = 0x811c9dc5;
    private static final int FNV_PRIME = 0x01000193;

    private final RestClient restClient;
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
        String apiKey = requireText(properties.getApiKey(), "LLM_API_KEY");
        this.restClient = restClientBuilder
                .defaultHeader("Authorization", "Bearer " + apiKey)
                .defaultHeader("Content-Type", MediaType.APPLICATION_JSON_VALUE)
                .build();
        log.info("LLM provider={}，chatModel={}，embeddingModel={}",
                provider, chatModel, embeddingModelLabel());
    }

    @Override
    public String chat(String prompt) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("model", chatModel);
        body.put("messages", List.of(
                Map.of("role", "system", "content", "你是错题分析助手。严格按用户要求输出一个 JSON 对象，不要输出 Markdown。"),
                Map.of("role", "user", "content", prompt)));
        body.put("thinking", Map.of("type", "disabled"));
        body.put("response_format", Map.of("type", "json_object"));
        body.put("temperature", 0.2);
        body.put("stream", false);

        JsonNode response = post("/chat/completions", body);
        JsonNode content = response.path("choices").path(0).path("message").path("content");
        if (!content.isTextual() || !StringUtils.hasText(content.asText())) {
            throw new IllegalStateException("大模型响应缺少 choices[0].message.content");
        }
        return content.asText();
    }

    @Override
    public List<Double> embed(String text) {
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
        JsonNode embedding = response.path("data").path(0).path("embedding");
        if (!embedding.isArray() || embedding.isEmpty()) {
            throw new IllegalStateException("Embedding 响应缺少 data[0].embedding");
        }
        List<Double> vector = new ArrayList<>(embedding.size());
        embedding.forEach(value -> {
            if (!value.isNumber()) {
                throw new IllegalStateException("Embedding 响应包含非数值元素");
            }
            vector.add(value.asDouble());
        });
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
