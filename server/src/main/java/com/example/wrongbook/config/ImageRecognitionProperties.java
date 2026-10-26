package com.example.wrongbook.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/** 图片错题识别旁路配置；默认开启，与文本分析模型配置相互独立。 */
@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "app.image-recognition")
public class ImageRecognitionProperties {

    private boolean enabled = true;
    private String baseUrl = "https://open.bigmodel.cn/api/paas/v4";
    private String apiKey;
    private String model = "glm-5.3-flash";
    private int maxImageBytes = 5 * 1024 * 1024;
}
