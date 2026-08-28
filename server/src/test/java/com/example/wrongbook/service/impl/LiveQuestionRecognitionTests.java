package com.example.wrongbook.service.impl;

import com.example.wrongbook.config.ImageRecognitionProperties;
import com.example.wrongbook.service.QuestionRecognitionClient;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.web.client.RestClient;

import javax.imageio.ImageIO;
import java.awt.Color;
import java.awt.Font;
import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.util.Base64;
import java.util.List;
import java.util.concurrent.TimeUnit;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * GLM-5.3-Flash 单图识别手动验证入口。默认跳过，不访问数据库，也不创建 Question。
 */
@Tag("live-image-recognition")
@EnabledIfEnvironmentVariable(named = "RUN_LIVE_IMAGE_RECOGNITION_TESTS", matches = "(?i)true")
class LiveQuestionRecognitionTests {

    @Test
    @Timeout(value = 2, unit = TimeUnit.MINUTES)
    void recognizesOneBase64PngAsStrictJson() throws Exception {
        String apiKey = firstNonBlank(
                System.getenv("IMAGE_RECOGNITION_API_KEY"),
                System.getenv("LLM_API_KEY"));
        assertThat(apiKey)
                .as("IMAGE_RECOGNITION_API_KEY 或 LLM_API_KEY")
                .isNotBlank();

        ImageRecognitionProperties properties = new ImageRecognitionProperties();
        properties.setEnabled(true);
        properties.setApiKey(apiKey);
        properties.setBaseUrl(firstNonBlank(
                System.getenv("IMAGE_RECOGNITION_BASE_URL"), properties.getBaseUrl()));
        properties.setModel(firstNonBlank(
                System.getenv("IMAGE_RECOGNITION_MODEL"), properties.getModel()));
        GlmQuestionRecognitionClient client = new GlmQuestionRecognitionClient(
                RestClient.builder(), new ObjectMapper(), properties);

        QuestionRecognitionClient.Extraction result = client.recognize(
                createSingleQuestionPng(), List.of("数学", "物理", "英语"));

        assertThat(result.subjectName()).isEqualTo("数学");
        assertThat(result.stem()).containsIgnoringCase("x").contains("5").contains("6");
        assertThat(result.studentAnswer()).contains("3");
        assertThat(result.source()).containsIgnoringCase("Algebra");
    }

    private String createSingleQuestionPng() throws Exception {
        BufferedImage image = new BufferedImage(1200, 760, BufferedImage.TYPE_INT_RGB);
        Graphics2D graphics = image.createGraphics();
        try {
            graphics.setColor(Color.WHITE);
            graphics.fillRect(0, 0, image.getWidth(), image.getHeight());
            graphics.setColor(Color.BLACK);
            graphics.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 34));
            graphics.drawString("MATH - Single Question", 70, 90);
            graphics.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 36));
            graphics.drawString("Solve x^2 - 5x + 6 = 0.", 70, 210);
            graphics.setColor(new Color(150, 30, 30));
            graphics.drawString("Student answer: x = 3", 70, 370);
            graphics.setColor(Color.BLACK);
            graphics.drawString("Source: Algebra practice", 70, 520);
        } finally {
            graphics.dispose();
        }
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        ImageIO.write(image, "png", output);
        return "data:image/png;base64," + Base64.getEncoder().encodeToString(output.toByteArray());
    }

    private String firstNonBlank(String first, String fallback) {
        return first != null && !first.isBlank() ? first.trim() : fallback;
    }
}
