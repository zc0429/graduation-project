package com.example.wrongbook.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/** 大模型网关配置；敏感值由环境变量或未入库的 .env 注入。 */
@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "app.llm")
public class LlmProperties {

    private String provider = "mock";
    private String baseUrl;
    private String apiKey;
    private String chatModel;
    private String embeddingModel;
    private int embeddingDimensions = 1024;
}
